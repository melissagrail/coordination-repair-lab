"""Run the pre-specified imperfect-evidence study (standard library only)."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, replace
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import statistics
import sys

from lab import Config, POLICIES, VERSION, make_tape, paired_interval, simulate, tape_digest

GENERATOR_FIELDS = ('providers', 'opportunities', 'accident_rate', 'breach_rate',
                    'unreliable_fraction', 'unreliable_multiplier', 'allegation_rate',
                    'externality_rate', 'identity_reset_rate', 'shock_start', 'shock_end',
                    'shock_breach_rate')


def cells(opportunities=1000):
    base = Config(opportunities=opportunities, breach_rate=0, shock_breach_rate=0,
                  allegation_rate=0, externality_rate=0)
    rates = (0, .01, .05, .15, .30)
    sensitivities = (.6, .95)
    for i, (f, t, r, a, v) in enumerate(itertools.product(rates, sensitivities, (.2, 1, 3, 5), (.05, .25), (.01, .6, 1.5))):
        yield 'retry', f'retry-{i:03d}', replace(base, false_positive_rate=f, evidence_accuracy=t,
                repair_cost=r, accident_rate=a, verification_cost=v)
    for i, (f, t, p, h, s) in enumerate(itertools.product(rates, sensitivities, (0, .01, .05, .20, .35), (1, 6, 12), (.1, .6))):
        yield 'scope', f'scope-{i:03d}', replace(base, false_positive_rate=f, evidence_accuracy=t,
                accident_rate=0, externality_rate=p, harm=h, scope_cost=s)


def scope_expected_delta(c):
    surplus = c.benefit - c.production_cost
    return (c.externality_rate*c.evidence_accuracy*(c.harm-surplus)
            - (1-c.externality_rate)*c.false_positive_rate*surplus - c.scope_cost)


def retry_expected_delta(c):
    return ((1-c.false_positive_rate)*c.accident_rate*
            (c.evidence_accuracy*(c.repair_success*c.benefit-c.repair_cost)-c.appeal_cost))


def scope_tape_delta(c, tape):
    """Independent finite-tape oracle, no policy simulator calls."""
    surplus = c.benefit - c.production_cost
    return statistics.fmean(
        (c.harm-surplus if e.externality else -surplus)
        * (e.evidence_draw < c.evidence_accuracy if e.externality
           else e.scope_false_draw < c.false_positive_rate) - c.scope_cost
        for e in tape)


def retry_tape_delta(c, tape):
    """Incremental retry payoff when both comparators verify every opportunity."""
    deltas = []
    for e in tape:
        delta = 0.0
        if e.failure == 'accident' and e.verification_false_draw >= c.false_positive_rate:
            delta -= c.appeal_cost
            if e.evidence_draw < c.evidence_accuracy:
                delta -= c.repair_cost
                if e.repair_draw < c.repair_success:
                    delta += c.benefit
        deltas.append(delta)
    return statistics.fmean(deltas)


def run(out, seeds=20, opportunities=1000, quick=False):
    if type(seeds) is not int or seeds < 2:
        raise ValueError('at least two integer seeds required')
    all_cells = list(cells(opportunities))
    if quick:
        # Both panels, both signs of the scope control, a retry-cost contrast.
        all_cells = [all_cells[i] for i in (0, 47, 240, 299, 539)]
    chosen = {p.name: p for p in POLICIES}
    comparisons = {'retry': (('repair_no_exclusion', 'naive_trust'), ('verify_and_retry', 'always_verify')),
                   'scope': (('scope_only', 'naive_trust'),)}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    input_hashes = {}

    @lru_cache(maxsize=None)
    def cached_tape(generator_json, seed):
        c = Config(**json.loads(generator_json))
        tape = make_tape(c, seed)
        tape_id = hashlib.sha256((generator_json + ':' + str(seed)).encode()).hexdigest()
        input_hashes[tape_id] = dict(seed=seed, generator=json.loads(generator_json), sha256=tape_digest(tape))
        return tape_id, tape

    summaries = []
    row_count = 0
    with (out/'runs.csv').open('w', newline='') as f:
        writer = None
        for panel, cell_id, c in all_cells:
            results = {}
            names = sorted({name for pair in comparisons[panel] for name in pair})
            generator_json = json.dumps({k: getattr(c, k) for k in GENERATOR_FIELDS}, sort_keys=True)
            max_oracle_error = 0.0
            for seed in range(seeds):
                tape_id, tape = cached_tape(generator_json, seed)
                for name in names:
                    m = simulate(c, tape, chosen[name])
                    results[seed, name] = m['social_net_per_opportunity']
                    row = dict(panel=panel, cell=cell_id, seed=seed, policy=name, tape_id=tape_id, **m)
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    row_count += 1
                left, right = comparisons[panel][-1]
                oracle = scope_tape_delta(c, tape) if panel == 'scope' else retry_tape_delta(c, tape)
                error = abs(results[seed,left]-results[seed,right]-oracle)
                if error > 1e-9:
                    raise AssertionError('finite-tape oracle mismatch')
                max_oracle_error = max(max_oracle_error, error)
            for left, right in comparisons[panel]:
                deltas = [results[s,left]-results[s,right] for s in range(seeds)]
                mean, low, high = paired_interval(deltas)
                analytic = (scope_expected_delta(c) if panel == 'scope' else
                            retry_expected_delta(c) if left == 'verify_and_retry' else None)
                summaries.append(dict(panel=panel, cell=cell_id, left=left, right=right,
                    **asdict(c), mean_delta=mean, ci_low=low, ci_high=high,
                    analytic_delta=analytic,
                    monte_carlo_error=None if analytic is None else mean-analytic,
                    max_tape_oracle_error=None if analytic is None else max_oracle_error))
    with (out/'summary.csv').open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(summaries[0])); w.writeheader(); w.writerows(summaries)
    root = Path(__file__).parent
    manifest = dict(version=VERSION, python_version=sys.version.split()[0], quick=quick,
                    seeds=list(range(seeds)), run_count=row_count,
                    cells={cid: dict(panel=panel, config=asdict(c)) for panel,cid,c in all_cells},
                    policies={name:asdict(chosen[name]) for panel in comparisons for pair in comparisons[panel] for name in pair},
                    inputs=input_hashes,
                    sources={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                             for name in ('lab.py','robustness.py','studies/ROBUSTNESS_PLAN.md')},
                    artifacts={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ('runs.csv','summary.csv')},
                    intervals='2000 paired-seed bootstrap draws; seed=0; 95% percentile; unadjusted; descriptive only')
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    report = ['# Imperfect evidence: robustness results', '',
              f'{row_count:,} policy runs across {len(all_cells)} parameter cells; {seeds} paired seeds and {opportunities:,} opportunities per run.', '',
              '**Synthetic model, not real agent behavior.** The cells form a chosen factorial grid, not a representative distribution of environments.', '',
              'Complete cell results: [summary.csv](summary.csv). Every policy run: [runs.csv](runs.csv). Inputs, source fingerprints, and parameters: [manifest.json](manifest.json).', '',
              '## Analytic controls', '',
              'Every finite-tape scope and verify-and-retry contrast agrees with an independent payoff calculation to within 1e-9 units per opportunity.', '',
              'The population formulas explain why the rankings change:', '',
              '```text',
              'scope − naive = p*t*(H − s) − (1 − p)*f*s − screening_cost',
              'verify_and_retry − always_verify = (1 − f)*a*(t*(r*B − retry_cost) − diagnosis_cost)',
              '```', '',
              'Here s is benefit minus production cost, p is harmful-task prevalence, t sensitivity, f false-positive probability, H third-party harm, a accident probability, r retry success probability, and B benefit.', '',
              '## Predefined grid: positive and negative mean differences', '',
              'Counts below describe grid cells only. They are not win probabilities for real environments; no significance claim is made.', '',
              '| Comparison | Positive mean | Negative mean | Zero mean |', '|---|---:|---:|---:|']
    for panel,pairs in comparisons.items():
        for left,right in pairs:
            vals=[s['mean_delta'] for s in summaries if s['panel']==panel and s['left']==left]
            report.append(f'| {left} − {right} | {sum(x>0 for x in vals)} | {sum(x<0 for x in vals)} | {sum(x==0 for x in vals)} |')
    report += ['', '## Illustrative slice: when screening becomes over-refusal', '',
               'Sensitivity .95, harm prevalence .05, harm 12, screening cost .1. All rows of this slice are shown; the entire grid remains available above.', '',
               '| False-positive rate | Mean scope − naive | 95% lower | 95% upper | Analytic expectation |', '|---|---:|---:|---:|---:|']
    for s in summaries:
        if s['panel']=='scope' and (s['evidence_accuracy'],s['externality_rate'],s['harm'],s['scope_cost'])==(.95,.05,12,.1):
            report.append(f"| {s['false_positive_rate']:.2f} | {s['mean_delta']:.4f} | {s['ci_low']:.4f} | {s['ci_high']:.4f} | {s['analytic_delta']:.4f} |")
    report += ['', '## Limits', '',
               '- Bootstrap intervals are unadjusted across many comparisons and quantify Monte Carlo variation only.',
               '- The retry panel has no intentional breaches. It tests recovery from execution failure, not incentives or resistance to exploitation.',
               '- The scope panel assumes known costs in one common unit. It does not establish consent, fairness, or how to discover affected parties.',
               '- False-positive draws are independent across channels; true-positive evidence is still shared within an opportunity.',
               '- False allegations can fail to clear; truthful allegations and a full appeal confusion matrix are not modeled.',
               '- Reputation, screening, and retry rules remain fixed. No strategic learning or live agent deployment occurred.',
               '- The study plan was committed before running this study, but was not independently preregistered.', '']
    (out/'REPORT.md').write_text('\n'.join(report))
    print(f'Wrote {row_count:,} policy runs across {len(all_cells)} cells to {out}')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('results/robustness'))
    p.add_argument('--seeds',type=int,default=20)
    p.add_argument('--opportunities',type=int,default=1000)
    p.add_argument('--quick',action='store_true',help='five-cell smoke test; not the published full study')
    args=p.parse_args()
    try:
        run(args.out,args.seeds,args.opportunities,args.quick)
    except ValueError as e:
        p.error(str(e))


if __name__=='__main__':
    main()
