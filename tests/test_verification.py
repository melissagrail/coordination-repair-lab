import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from verify_results import check_runs, verify


class ArtifactTests(unittest.TestCase):
    def fixture(self, root):
        (root/'results/robustness').mkdir(parents=True)
        (root/'studies').mkdir()
        sources={}
        for name in ('lab.py','robustness.py','studies/ROBUSTNESS_PLAN.md'):
            (root/name).write_text('synthetic source fixture\n')
            sources[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
        row=dict(scenario='fixture',seed=0,policy='fixture',social_net=2,
                 participant_net=3,gross_benefit=5,production_cost=1,coordination_cost=1,
                 third_party_harm=1,attempted=1,completed=1,failures=0)
        for folder in (root/'results',root/'results/robustness'):
            with (folder/'runs.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow(row)
        (root/'results/robustness/summary.csv').write_text('synthetic summary\n')
        base=dict(source_sha256=sources['lab.py'],scenarios={'fixture':{}},seeds=[0],policies=[{}])
        robust=dict(sources=sources,run_count=1,artifacts={name:hashlib.sha256((root/'results/robustness'/name).read_bytes()).hexdigest() for name in ('runs.csv','summary.csv')})
        (root/'results/manifest.json').write_text(json.dumps(base))
        (root/'results/robustness/manifest.json').write_text(json.dumps(robust))
    def test_matching_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root);verify(root)
    def test_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root);(root/'lab.py').write_text('changed\n')
            with self.assertRaisesRegex(ValueError,'source fingerprint'):
                verify(root)
    def test_changed_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root);(root/'results/robustness/summary.csv').write_text('changed\n')
            with self.assertRaisesRegex(ValueError,'artifact fingerprint'):
                verify(root)
    def test_nonfinite_metric_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root);p=root/'results/runs.csv'
            with p.open() as f:
                rows=list(csv.DictReader(f))
            rows[0]['social_net']='nan'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            with self.assertRaisesRegex(ValueError,'nonfinite'):
                check_runs(p,1)


if __name__=='__main__':
    unittest.main()
