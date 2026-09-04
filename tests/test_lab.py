import unittest
from dataclasses import replace
from pathlib import Path
import tempfile
from lab import Config, Event, POLICIES, make_tape, simulate, tape_digest, paired_interval, run_suite

class LabTests(unittest.TestCase):
    def c(self, n=1, **kw):
        return Config(opportunities=n, providers=1, **kw)
    def e(self, **kw):
        return replace(Event(0, 'none', False, False, False, .5, 0., 0.), **kw)
    def p(self, name):
        return next(p for p in POLICIES if p.name == name)
    def test_benign_closed_form(self):
        c = self.c(10)
        tape = (self.e(),) * 10
        a = simulate(c, tape, self.p('naive_trust'))
        b = simulate(c, tape, self.p('always_verify'))
        self.assertEqual(a['social_net'], 40)
        self.assertAlmostEqual(a['social_net'] - b['social_net'], 10*c.verification_cost)
    def test_accounting_conservation(self):
        c = Config(opportunities=500)
        for p in POLICIES:
            m = simulate(c, make_tape(c, 8), p)
            self.assertAlmostEqual(m['social_net'], m['gross_benefit']-m['production_cost']-m['coordination_cost']-m['third_party_harm'])
            self.assertEqual(m['attempted'], m['completed']+m['failures'])
            self.assertEqual(c.opportunities, m['attempted']+m['prevented_breaches']+m['exclusions']+m['scope_declines'])
    def test_verification_does_not_create_output(self):
        m = simulate(self.c(), (self.e(failure='breach'),), self.p('always_verify'))
        self.assertEqual(m['completed'], 0)
        self.assertEqual(m['production_cost'], 0)
        self.assertEqual(m['prevented_breaches'], 1)
        self.assertEqual(m['social_net'], -.6)
    def test_repair_is_paid_and_can_fail(self):
        c = self.c(repair_success=0)
        tape = (self.e(failure='accident'),)
        a = simulate(c, tape, self.p('repair'))
        b = simulate(replace(c, repair_success=1), tape, self.p('repair'))
        self.assertEqual(a['completed'], 0)
        self.assertEqual(a['repair_cost'], c.repair_cost)
        self.assertEqual(b['completed'], 1)
        self.assertAlmostEqual(b['social_net']-a['social_net'], c.benefit)
    def test_no_repair_of_breach(self):
        m = simulate(self.c(evidence_accuracy=0), (self.e(failure='breach'),), self.p('repair'))
        self.assertEqual(m['repairs'], 0)
        self.assertEqual(m['repair_cost'], 0)
        self.assertEqual(m['completed'], 0)
    def test_false_accusation_and_appeal(self):
        tape = (self.e(allegation=True),)
        a = simulate(self.c(), tape, self.p('repair'))
        b = simulate(self.c(), tape, self.p('repair_no_appeal'))
        self.assertEqual(a['completed'], 1)
        self.assertEqual(a['appeals'], 1)
        self.assertEqual(b['false_exclusions'], 1)
    def test_exclusion_expires(self):
        tape = (self.e(failure='breach'),)+(self.e(),)*4
        m = simulate(self.c(5), tape, self.p('repair'))
        self.assertEqual(m['exclusions'], 3)
        self.assertEqual(m['completed'], 1)
    def test_reset_erases_exclusion(self):
        tape = (self.e(failure='breach'), self.e(reset=True))
        m = simulate(self.c(2), tape, self.p('repair'))
        self.assertEqual(m['exclusions'], 0)
        self.assertEqual(m['verifications'], 2)
        self.assertEqual(m['completed'], 1)
    def test_scope_accounts_for_nonparticipants(self):
        c = self.c(harm=12)
        tape = (self.e(externality=True),)
        a = simulate(c, tape, self.p('naive_trust'))
        b = simulate(c, tape, self.p('repair_with_scope'))
        self.assertEqual(a['participant_net'], 4)
        self.assertEqual(a['social_net'], -8)
        self.assertEqual(b['third_party_harm'], 0)
        self.assertEqual(b['social_net'], -c.scope_cost)
    def test_replay_and_policy_order(self):
        c = Config(opportunities=200)
        tape = make_tape(c, 7)
        digest = tape_digest(tape)
        a = {p.name: simulate(c, tape, p) for p in POLICIES}
        b = {p.name: simulate(c, tape, p) for p in reversed(POLICIES)}
        self.assertEqual(a, b)
        self.assertEqual(digest, tape_digest(tape))
        self.assertEqual(tape, make_tape(c, 7))
        self.assertNotEqual(tape, make_tape(c, 8))
    def test_zero_cost_benign_equivalence(self):
        c = self.c(20, verification_cost=0, commitment_cost=0, scope_cost=0)
        self.assertEqual({simulate(c, (self.e(),)*20, p)['social_net'] for p in POLICIES}, {80})
    def test_provider_relabeling(self):
        c = Config(providers=5, opportunities=500)
        tape = make_tape(c, 1)
        other = tuple(replace(e, provider=4-e.provider) for e in tape)
        for p in POLICIES:
            self.assertEqual(simulate(c, tape, p), simulate(c, other, p))
    def test_bootstrap(self):
        self.assertEqual(paired_interval([2.]*5), (2,2,2))
        self.assertEqual(paired_interval([1,2,3]), paired_interval([1,2,3]))
        with self.assertRaises(ValueError):
            paired_interval([1])
    def test_homogeneous_control(self):
        a = Config(opportunities=200, unreliable_fraction=0, unreliable_multiplier=1)
        b = replace(a, unreliable_fraction=1)
        self.assertEqual(make_tape(a, 4), make_tape(b, 4))
    def test_no_exclusion_control(self):
        tape = (self.e(failure='breach'), self.e())
        m = simulate(self.c(2), tape, self.p('repair_no_exclusion'))
        self.assertEqual(m['exclusions'], 0)
        self.assertEqual(m['completed'], 1)
    def test_scope_detection_can_miss(self):
        m = simulate(self.c(evidence_accuracy=0), (self.e(externality=True),), self.p('scope_only'))
        self.assertEqual(m['scope_declines'], 0)
        self.assertEqual(m['third_party_harm'], 6)
    def test_retry_without_reputation(self):
        m = simulate(self.c(), (self.e(failure='accident'),), self.p('verify_and_retry'))
        self.assertEqual(m['repairs'], 1)
        self.assertEqual(m['completed'], 1)
        self.assertEqual(m['exclusions'], 0)
    def test_invalid_config(self):
        for kw in ({'providers':0}, {'opportunities':-1}, {'evidence_accuracy':1.1}, {'verification_cost':-1}, {'repair_cost':float('nan')}, {'shock_start':.8,'shock_end':.2}, {'accident_rate':.9}):
            with self.assertRaises(ValueError):
                Config(**kw)
    def test_suite_artifacts_reproduce(self):
        with tempfile.TemporaryDirectory() as root:
            a,b = Path(root)/'a', Path(root)/'b'
            run_suite(a,2,10)
            run_suite(b,2,10)
            for f in ('runs.csv','manifest.json','REPORT.md'):
                self.assertEqual((a/f).read_bytes(), (b/f).read_bytes())

if __name__ == '__main__':
    unittest.main()
