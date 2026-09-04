"""Verify saved outputs; optionally rerun both complete studies in a temporary directory."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_runs(path, expected):
    seen=set()
    with path.open() as f:
        for row in csv.DictReader(f):
            key=(row.get('scenario',row.get('cell')),row['seed'],row['policy'])
            if key in seen:
                raise ValueError('duplicate run in '+path.name)
            seen.add(key)
            for name in ('social_net','participant_net','gross_benefit','production_cost','coordination_cost','third_party_harm'):
                if not math.isfinite(float(row[name])):
                    raise ValueError('nonfinite metric')
            expected_net=float(row['gross_benefit'])-float(row['production_cost'])-float(row['coordination_cost'])-float(row['third_party_harm'])
            if not math.isclose(float(row['social_net']),expected_net,rel_tol=1e-10,abs_tol=1e-8):
                raise ValueError('social-net accounting mismatch')
            if int(row['attempted'])!=int(row['completed'])+int(row['failures']):
                raise ValueError('outcome accounting mismatch')
    if len(seen)!=expected:
        raise ValueError('unexpected number of runs')


def verify(root, rerun=False):
    root=Path(root)
    b=root/'results'
    r=b/'robustness'
    base=json.loads((b/'manifest.json').read_text())
    robust=json.loads((r/'manifest.json').read_text())
    if base['source_sha256']!=digest(root/'lab.py'):
        raise ValueError('baseline source fingerprint differs')
    expected_sources={'lab.py','robustness.py','studies/ROBUSTNESS_PLAN.md'}
    if set(robust['sources'])!=expected_sources:
        raise ValueError('unexpected source manifest entries')
    for name,sha in robust['sources'].items():
        if sha!=digest(root/name):
            raise ValueError('robustness source fingerprint differs: '+name)
    if set(robust['artifacts'])!={'runs.csv','summary.csv'}:
        raise ValueError('unexpected artifact manifest entries')
    for name,sha in robust['artifacts'].items():
        if sha!=digest(r/name):
            raise ValueError('robustness artifact fingerprint differs: '+name)
    check_runs(b/'runs.csv',len(base['scenarios'])*len(base['seeds'])*len(base['policies']))
    check_runs(r/'runs.csv',robust['run_count'])
    if rerun:
        from lab import run_suite
        from robustness import run
        # This helper reproduces the checked-in full/default study, not arbitrary manifests.
        if base['seeds']!=list(range(40)) or robust['seeds']!=list(range(20)) or robust['quick']:
            raise ValueError('rerun expects the published full-study configuration')
        with tempfile.TemporaryDirectory() as temp:
            a,c=Path(temp)/'baseline',Path(temp)/'robustness'
            run_suite(a,40,2000)
            run(c,20,1000)
            for original,reproduced,names in ((b,a,('runs.csv','REPORT.md')),
                    (r,c,('runs.csv','summary.csv','REPORT.md'))):
                for name in names:
                    if digest(original/name)!=digest(reproduced/name):
                        raise ValueError('reproduction differs: '+name)
        print('Both full studies reproduce exactly (data and reports; runtime metadata may differ).')
    print('Source fingerprints, robustness artifact hashes, run counts, and accounting checks passed.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rerun',action='store_true')
    args=p.parse_args()
    try:
        verify(Path(__file__).parent,args.rerun)
    except (ValueError,KeyError,FileNotFoundError) as e:
        p.exit(1,f'Verification failed: {e}\n')


if __name__=='__main__':
    main()
