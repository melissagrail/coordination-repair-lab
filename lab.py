"""Coordination Repair Lab: synthetic event replay, standard library only."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

VERSION = '0.2.0'


@dataclass(frozen=True)
class Config:
    providers: int = 30
    opportunities: int = 2000
    benefit: float = 5.0
    production_cost: float = 1.0
    verification_cost: float = 0.6
    commitment_cost: float = 0.05
    appeal_cost: float = 0.3
    repair_cost: float = 1.0
    scope_cost: float = 0.1
    harm: float = 6.0
    accident_rate: float = 0.05
    breach_rate: float = 0.05
    unreliable_fraction: float = 0.2
    unreliable_multiplier: float = 5.0
    allegation_rate: float = 0.02
    externality_rate: float = 0.03
    identity_reset_rate: float = 0.0
    evidence_accuracy: float = 0.95
    false_positive_rate: float = 0.0
    repair_success: float = 0.8
    audit_rate: float = 0.1
    successes_to_trust: int = 3
    exclusion_length: int = 3
    shock_start: float = 0.4
    shock_end: float = 0.6
    shock_breach_rate: float = 0.3

    def __post_init__(self):
        for name in ('providers', 'opportunities', 'successes_to_trust', 'exclusion_length'):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f'{name} must be a positive integer')
        for name, value in asdict(self).items():
            if name.endswith('_rate') or name in ('evidence_accuracy', 'repair_success', 'shock_start', 'shock_end', 'unreliable_fraction'):
                if not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f'{name} must be in [0, 1]')
            elif isinstance(value, (int, float)) and (not math.isfinite(value) or value < 0):
                raise ValueError(f'{name} must be finite and nonnegative')
        if self.accident_rate + max(self.breach_rate, self.shock_breach_rate) > 1:
            raise ValueError('accident and breach probabilities must sum to at most 1')
        if self.shock_start > self.shock_end:
            raise ValueError('shock_start must not exceed shock_end')


@dataclass(frozen=True)
class Event:
    provider: int
    failure: str  # none, accident, breach; hidden from decision rules
    allegation: bool  # false allegation, independent of actual task outcome
    externality: bool
    reset: bool
    audit_draw: float
    evidence_draw: float
    repair_draw: float
    verification_false_draw: float = 0.5
    scope_false_draw: float = 0.5
    diagnosis_false_draw: float = 0.5

    def __post_init__(self):
        if type(self.provider) is not int or self.provider < 0:
            raise ValueError('event provider must be a nonnegative integer')
        if self.failure not in ('none', 'accident', 'breach'):
            raise ValueError('invalid event failure')
        for name in ('allegation', 'externality', 'reset'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be boolean')
        for name in ('audit_draw', 'evidence_draw', 'repair_draw', 'verification_false_draw',
                     'scope_false_draw', 'diagnosis_false_draw'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'{name} must be finite and in [0, 1]')


@dataclass(frozen=True)
class Policy:
    name: str
    verify_all: bool = False
    reputation: bool = False
    repair: bool = False
    appeal: bool = False
    scope: bool = False
    commitments: bool = False
    exclude: bool = True


POLICIES = (
    Policy('always_verify', verify_all=True),
    Policy('naive_trust'),
    Policy('reputation_only', reputation=True),
    Policy('repair', reputation=True, repair=True, appeal=True, commitments=True),
    Policy('repair_no_exclusion', reputation=True, repair=True, appeal=True, commitments=True, exclude=False),
    Policy('verify_and_retry', verify_all=True, repair=True),
    Policy('scope_only', scope=True),
    Policy('repair_no_appeal', reputation=True, repair=True, commitments=True),
    Policy('repair_with_scope', reputation=True, repair=True, appeal=True, scope=True, commitments=True),
)


@dataclass
class State:
    successes: int = 0
    excluded_for: int = 0


def make_tape(config: Config, seed: int) -> tuple[Event, ...]:
    """Pre-sample every exogenous event before any policy runs."""
    rng = random.Random(seed)
    false_rng = random.Random(f'false-positives-v1:{seed}')
    multipliers = [config.unreliable_multiplier if rng.random() < config.unreliable_fraction else 1.0
                   for _ in range(config.providers)]
    events = []
    for t in range(config.opportunities):
        provider = rng.randrange(config.providers)
        shock = config.shock_start <= t / config.opportunities < config.shock_end
        breach = config.shock_breach_rate if shock else config.breach_rate
        breach = min(1.0 - config.accident_rate, breach * multipliers[provider])
        u = rng.random()
        failure = 'accident' if u < config.accident_rate else ('breach' if u < config.accident_rate + breach else 'none')
        events.append(Event(provider, failure, rng.random() < config.allegation_rate,
                            rng.random() < config.externality_rate,
                            rng.random() < config.identity_reset_rate,
                            rng.random(), rng.random(), rng.random(),
                            false_rng.random(), false_rng.random(), false_rng.random()))
    return tuple(events)


def tape_digest(tape: tuple[Event, ...]) -> str:
    encoded = json.dumps([asdict(e) for e in tape], sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def simulate(config: Config, tape: tuple[Event, ...], policy: Policy) -> dict:
    if len(tape) != config.opportunities:
        raise ValueError('tape length must match opportunities')
    states = [State() for _ in range(config.providers)]
    m = dict(completed=0, attempted=0, failures=0, prevented_breaches=0,
             exclusions=0, false_exclusions=0, scope_declines=0, repairs=0,
             appeals=0, verifications=0, resets=0, false_rejections=0,
             false_scope_declines=0, wasted_retries=0, gross_benefit=0.0,
             production_cost=0.0, verification_cost=0.0, commitment_cost=0.0,
             appeal_cost=0.0, repair_cost=0.0, scope_cost=0.0, third_party_harm=0.0)
    for e in tape:
        if not 0 <= e.provider < config.providers:
            raise ValueError('event provider outside population')
        if e.failure not in ('none', 'accident', 'breach'):
            raise ValueError('invalid event failure')
        if e.reset:
            states[e.provider] = State()
            m['resets'] += 1
        s = states[e.provider]
        accurate = e.evidence_draw < config.evidence_accuracy
        # Allegations are not authority. Appeal acquires evidence at a cost.
        if policy.reputation and policy.exclude and e.allegation:
            cleared = False
            if policy.appeal:
                m['appeals'] += 1
                m['appeal_cost'] += config.appeal_cost
                cleared = accurate
            if not cleared:
                s.excluded_for = config.exclusion_length
                s.successes = 0
        if policy.reputation and policy.exclude and s.excluded_for:
            m['exclusions'] += 1
            if e.failure == 'none':
                m['false_exclusions'] += 1
            s.excluded_for -= 1
            continue
        if policy.scope:
            m['scope_cost'] += config.scope_cost
            flagged = accurate if e.externality else e.scope_false_draw < config.false_positive_rate
            if flagged:
                m['scope_declines'] += 1
                if not e.externality:
                    m['false_scope_declines'] += 1
                continue
        verify = policy.verify_all or (policy.reputation and
                 (s.successes < config.successes_to_trust or e.audit_draw < config.audit_rate))
        if verify:
            m['verifications'] += 1
            m['verification_cost'] += config.verification_cost
        if policy.commitments:
            m['commitment_cost'] += config.commitment_cost
        # A paid check can also wrongly reject a non-breach.
        flagged = accurate if e.failure == 'breach' else e.verification_false_draw < config.false_positive_rate
        if verify and flagged:
            if e.failure == 'breach':
                m['prevented_breaches'] += 1
            else:
                m['false_rejections'] += 1
            if policy.reputation:
                s.successes = 0
                if policy.exclude:
                    s.excluded_for = config.exclusion_length
            continue
        m['attempted'] += 1
        m['production_cost'] += config.production_cost
        completed = e.failure == 'none'
        if not completed and policy.repair:
            # A false accident diagnosis wastes retry resources on an unrepairable breach.
            m['appeal_cost'] += config.appeal_cost
            m['appeals'] += 1
            diagnosed = accurate if e.failure == 'accident' else e.diagnosis_false_draw < config.false_positive_rate
            if diagnosed:
                m['repair_cost'] += config.repair_cost
                if e.failure == 'breach':
                    m['wasted_retries'] += 1
                completed = e.failure == 'accident' and e.repair_draw < config.repair_success
                if completed:
                    m['repairs'] += 1
        if completed:
            m['completed'] += 1
            m['gross_benefit'] += config.benefit
            if e.externality:
                m['third_party_harm'] += config.harm
            s.successes += 1
        else:
            m['failures'] += 1
            s.successes = 0
            if policy.reputation and policy.exclude:
                s.excluded_for = config.exclusion_length
    m['coordination_cost'] = sum(m[k] for k in ('verification_cost', 'commitment_cost', 'appeal_cost', 'repair_cost', 'scope_cost'))
    m['participant_net'] = m['gross_benefit'] - m['production_cost'] - m['coordination_cost']
    m['social_net'] = m['participant_net'] - m['third_party_harm']
    m['social_net_per_opportunity'] = m['social_net'] / config.opportunities
    m['completion_rate'] = m['completed'] / config.opportunities
    # Opportunity gap is descriptive and is NOT subtracted again from social net.
    m['unrealized_benefit'] = (config.opportunities - m['completed']) * config.benefit
    return m


def scenarios(base: Config) -> dict[str, Config]:
    return {
        'benign': replace(base, accident_rate=0, breach_rate=0, shock_breach_rate=0, allegation_rate=0, externality_rate=0),
        'mixed_shock': base,
        'uniform_reliability': replace(base, unreliable_fraction=0),
        'accidental_failures': replace(base, accident_rate=0.25, breach_rate=0, shock_breach_rate=0, allegation_rate=0, externality_rate=0),
        'cheap_verification': replace(base, verification_cost=0.01, breach_rate=0.3, shock_breach_rate=0.6),
        'poor_evidence': replace(base, evidence_accuracy=0.25, repair_success=0.25),
        'identity_churn': replace(base, identity_reset_rate=0.3),
        'third_party_costs': replace(base, externality_rate=0.35, harm=12),
    }


def paired_interval(values: list[float], seed: int = 0, draws: int = 2000) -> tuple[float, float, float]:
    """Percentile bootstrap over independent paired seed differences, not interactions."""
    if len(values) < 2 or draws < 1:
        raise ValueError('need at least two seeds and one bootstrap draw')
    rng = random.Random(seed)
    n = len(values)
    boot = sorted(statistics.fmean(rng.choices(values, k=n)) for _ in range(draws))
    return statistics.fmean(values), boot[int(0.025 * (draws - 1))], boot[int(0.975 * (draws - 1))]


def run_suite(out: Path, seeds: int, opportunities: int) -> None:
    if seeds < 2:
        raise ValueError('at least two seeds required')
    configs = scenarios(Config(opportunities=opportunities))
    rows, hashes = [], {}
    for scenario, config in configs.items():
        hashes[scenario] = {}
        for seed in range(seeds):
            tape = make_tape(config, seed)
            hashes[scenario][str(seed)] = tape_digest(tape)
            for policy in POLICIES:
                rows.append(dict(scenario=scenario, seed=seed, policy=policy.name, **simulate(config, tape, policy)))
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'runs.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = dict(version=VERSION, python_version=sys.version.split()[0], seeds=list(range(seeds)), scenarios={k: asdict(v) for k, v in configs.items()},
                    policies=[asdict(p) for p in POLICIES], tape_sha256=hashes,
                    bootstrap=dict(unit='paired seed', draws=2000, seed=0, interval='95% percentile; unadjusted'),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    report = ['# Coordination Repair Lab — measured results', '',
              f'{len(rows):,} runs; {seeds} paired seeds per scenario; {opportunities:,} opportunities per run.', '',
              '**Synthetic sensitivity study, not evidence of agent alignment or equilibrium selection.**', '',
              'These are arbitrary model units, not dollars, tokens, or empirical welfare estimates. Larger social net is better.', '',
              '## Mean social net per opportunity', '',
              '| Scenario | ' + ' | '.join(p.name for p in POLICIES) + ' |',
              '|---|' + '---:|' * len(POLICIES)]
    for scenario in configs:
        report.append('| ' + scenario + ' | ' + ' | '.join(f"{statistics.fmean(r['social_net_per_opportunity'] for r in rows if r['scenario'] == scenario and r['policy'] == p.name):.3f}" for p in POLICIES) + ' |')
    report += ['', '## Paired differences: repair minus always_verify', '',
               '95% percentile bootstrap intervals over seeds; no multiple-comparison correction. These quantify Monte Carlo variation under fixed assumptions, not model uncertainty.', '',
               '| Scenario | Mean difference | Lower | Upper |', '|---|---:|---:|---:|']
    for scenario in configs:
        lookup = {(r['seed'], r['policy']): r['social_net_per_opportunity'] for r in rows if r['scenario'] == scenario}
        mean, low, high = paired_interval([lookup[s, 'repair'] - lookup[s, 'always_verify'] for s in range(seeds)])
        report.append(f'| {scenario} | {mean:.3f} | {low:.3f} | {high:.3f} |')
    report += ['', '## Interpretation limits', '',
               '- Provider breach propensities persist within a run; the uniform_reliability control removes heterogeneity. Identity resets erase public history but preserve latent propensity.',
               '- Policies are fixed rules. No language models, strategic learning, voluntary institutional choice, or conscious populations are instantiated.',
               '- Failure events are exogenous. An adaptive attacker may react to policy; this replay cannot measure that.',
               '- This baseline sets false_positive_rate to zero. The separate robustness study varies false positives; see studies/ROBUSTNESS_PLAN.md.',
               '- Commitments currently add cost only. Their independent benefit is unmodeled, so this is not a test of commitment semantics.',
               '- Reputation uses provider identity and bounded exclusion. There is no authenticated identity, decentralization, insolvency, restitution transfer, or enforcement model.',
               '- Parameter regimes are illustrative stress cases, not a representative sample of future environments.',
               '- Read MODEL.md before treating any ranking as a design recommendation.', '']
    (out / 'REPORT.md').write_text('\n'.join(report))
    print(f'Wrote {len(rows)} runs and reproducibility manifest to {out}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results'))
    parser.add_argument('--seeds', type=int, default=40)
    parser.add_argument('--opportunities', type=int, default=2000)
    args = parser.parse_args()
    try:
        run_suite(args.out, args.seeds, args.opportunities)
    except ValueError as e:
        parser.error(str(e))


if __name__ == '__main__':
    main()
