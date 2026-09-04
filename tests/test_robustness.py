import csv
from dataclasses import replace
import itertools
import json
from pathlib import Path
import tempfile
import unittest

from lab import Config, Event, POLICIES, make_tape, simulate
from robustness import (cells, run, scope_expected_delta, scope_tape_delta,
                        retry_expected_delta, retry_tape_delta)

P = {p.name:p for p in POLICIES}

class EvidenceTests(unittest.TestCase):
    def e(self, **kw):
        return replace(Event(0,'none',False,False,False,.5,.5,.5,.5,.5,.5),**kw)
    def c(self, n=1, **kw):
        return Config(providers=1,opportunities=n,**kw)
    def test_false_verification_rejects_good_work(self):
        c=self.c(false_positive_rate=1)
        m=simulate(c,(self.e(),),P['always_verify'])
        self.assertEqual(m['completed'],0)
        self.assertEqual(m['false_rejections'],1)
        self.assertEqual(m['prevented_breaches'],0)
        self.assertEqual(m['social_net'],-c.verification_cost)
    def test_false_scope_flag_costs_benefit(self):
        c=self.c(false_positive_rate=1)
        m=simulate(c,(self.e(),),P['scope_only'])
        self.assertEqual(m['scope_declines'],1)
        self.assertEqual(m['false_scope_declines'],1)
        self.assertEqual(m['third_party_harm'],0)
        self.assertEqual(m['social_net'],-c.scope_cost)
    def test_false_diagnosis_spends_without_repairing_breach(self):
        c=self.c(false_positive_rate=1,evidence_accuracy=0)
        m=simulate(c,(self.e(failure='breach'),),P['verify_and_retry'])
        self.assertEqual(m['wasted_retries'],1)
        self.assertEqual(m['repairs'],0)
        self.assertEqual(m['completed'],0)
        self.assertEqual(m['repair_cost'],c.repair_cost)
    def test_rejection_sanction_is_bounded(self):
        c=self.c(5,false_positive_rate=1)
        m=simulate(c,(self.e(),)*5,P['repair'])
        self.assertEqual(m['false_rejections'],2)
        self.assertEqual(m['exclusions'],3)
    def test_false_draw_does_not_replace_true_detection(self):
        c=self.c(false_positive_rate=1,evidence_accuracy=0)
        m=simulate(c,(self.e(failure='breach'),),P['always_verify'])
        self.assertEqual(m['false_rejections'],0)
        self.assertEqual(m['prevented_breaches'],0)
        self.assertEqual(m['failures'],1)
    def test_conservation_with_imperfect_evidence(self):
        for rate in (0,.05,.3,1):
            c=Config(opportunities=300,false_positive_rate=rate)
            tape=make_tape(c,2)
            for p in POLICIES:
                m=simulate(c,tape,p)
                self.assertEqual(c.opportunities,m['attempted']+m['prevented_breaches']+m['false_rejections']+m['exclusions']+m['scope_declines'])
                self.assertEqual(m['attempted'],m['completed']+m['failures'])
                self.assertLessEqual(m['false_scope_declines'],m['scope_declines'])
                self.assertAlmostEqual(m['social_net'],m['gross_benefit']-m['production_cost']-m['coordination_cost']-m['third_party_harm'])
    def test_probability_changes_preserve_tape(self):
        c=Config(opportunities=40)
        self.assertEqual(make_tape(c,2),make_tape(replace(c,false_positive_rate=.5,repair_cost=9,evidence_accuracy=.2),2))
    def test_event_validation(self):
        for kw in ({'provider':-1},{'provider':True},{'failure':'anything'},{'reset':'false'},
                   {'audit_draw':float('nan')},{'scope_false_draw':1.1},{'diagnosis_false_draw':-1}):
            with self.assertRaises(ValueError):
                self.e(**kw)
    def test_full_factorial_counts(self):
        design=list(cells())
        self.assertEqual(len(design),540)
        self.assertEqual(sum(p=='retry' for p,_,_ in design),240)
        self.assertEqual(len({name for _,name,_ in design}),540)
    def test_scope_analytic_boundary(self):
        c=self.c(externality_rate=.05,harm=12,evidence_accuracy=.95,scope_cost=.1)
        self.assertAlmostEqual(scope_expected_delta(c),.28)
        self.assertAlmostEqual(scope_expected_delta(replace(c,false_positive_rate=.15)),-.29)
    def test_retry_analytic_cost_boundary(self):
        c=self.c(accident_rate=.25,evidence_accuracy=.95,repair_cost=1,false_positive_rate=.05)
        self.assertGreater(retry_expected_delta(c),0)
        self.assertLess(retry_expected_delta(replace(c,repair_cost=5)),0)
    def test_scope_finite_tape_oracle(self):
        for rate,t in itertools.product((0,.1,1),(0,.6,1)):
            c=Config(opportunities=300,accident_rate=0,breach_rate=0,shock_breach_rate=0,
                     externality_rate=.3,false_positive_rate=rate,evidence_accuracy=t)
            tape=make_tape(c,5)
            actual=simulate(c,tape,P['scope_only'])['social_net_per_opportunity']-simulate(c,tape,P['naive_trust'])['social_net_per_opportunity']
            self.assertAlmostEqual(actual,scope_tape_delta(c,tape),places=10)
    def test_retry_finite_tape_oracle(self):
        for rate,t in itertools.product((0,.1,1),(0,.6,1)):
            c=Config(opportunities=300,accident_rate=.25,breach_rate=0,shock_breach_rate=0,
                     externality_rate=0,false_positive_rate=rate,evidence_accuracy=t)
            tape=make_tape(c,5)
            actual=simulate(c,tape,P['verify_and_retry'])['social_net_per_opportunity']-simulate(c,tape,P['always_verify'])['social_net_per_opportunity']
            self.assertAlmostEqual(actual,retry_tape_delta(c,tape),places=10)
    def test_quick_suite_is_reproducible_and_marked(self):
        with tempfile.TemporaryDirectory() as root:
            a,b=Path(root)/'a',Path(root)/'b'
            run(a,seeds=2,opportunities=10,quick=True)
            run(b,seeds=2,opportunities=10,quick=True)
            for filename in ('runs.csv','summary.csv','manifest.json','REPORT.md'):
                self.assertEqual((a/filename).read_bytes(),(b/filename).read_bytes())
            manifest=json.loads((a/'manifest.json').read_text())
            self.assertTrue(manifest['quick'])
            self.assertEqual(manifest['run_count'],28)
            with (a/'runs.csv').open() as f:
                self.assertEqual(len(list(csv.DictReader(f))),28)

if __name__=='__main__':
    unittest.main()
