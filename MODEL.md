# Model v0.2 (v0.1 baseline preserved)

## Scope

This is a finite-horizon event-replay sensitivity study. A provider is an integer index plus two public counters, with no cognition, goals, personal narrative, or social experience. An opportunity is a possible task. A single aggregate requester stands in for demand; all participant payoffs are pooled. There is no agent learning or endogenous institution formation.

The implementation is `lab.py`; configuration is `Config`. Defaults are assumptions, not empirical estimates. The exact suite configuration is saved in `results/manifest.json`.

## Exogenous events

For each seed, a local pseudorandom generator first assigns each provider either multiplier 1 or multiplier 5 (probability 0.2 for the latter by default). Providers are sampled uniformly with replacement for 2,000 opportunities.

At opportunity t, the base breach probability is 0.05, rising to 0.3 during the interval [0.4T, 0.6T). Multiply by the provider's fixed multiplier and cap at 1 minus the accident probability. Accidents and breaches are mutually exclusive. A single draw chooses accident, breach, or no failure. An accident represents unsuccessful execution; a breach represents an invalid commitment detectable before execution with sufficient evidence. Neither denotes an instantiated attacker.

Other independent draws generate a false allegation, a harmful externality flag, an identity reset, and latent audit, evidence, and retry outcomes. A reset erases public history and sanctions but retains the provider's underlying propensity. This approximates cheap identity replacement, not an identity protocol or a full Sybil attack.

A single true-positive evidence draw is deliberately shared across checks within each opportunity. Checks are therefore correlated. Its threshold is `evidence_accuracy`; despite the name, it models **sensitivity**, not a calibrated classifier's overall accuracy. The baseline keeps false positives at zero. The v0.2 robustness study varies a separate `false_positive_rate`. Audits detect true breaches, diagnoses identify true accidents, appeals clear false allegations, and scope checks detect true externalities when that draw is below the threshold. On a missed true positive they detect nothing. A separate pseudorandom stream supplies independent false-positive draws for verification, scope screening, and diagnosis. Those checks may wrongly classify a non-breach, a harmless task, or an unrepairable breach respectively. The false-positive parameter does not alter allegation appeals: all allegations here remain false, and evidence can fail to clear them. This incomplete appeal model must remain visible.

The tuple of frozen event records is generated before any policy runs. Policies cannot inspect future records, hidden provider multipliers, or hidden outcomes to choose whether to verify. Diagnosis and screening use hidden labels only through the modeled evidence mechanism.

## Decision and accounting order

1. Apply any identity reset.
2. For rules with exclusion, process the false allegation. An appeal pays for evidence; a successful appeal leaves prior sanctions unchanged. An uncleared allegation resets the good-history counter and starts exclusion, including this opportunity.
3. If excluded, decline and decrement the counter. Exclusion after an outcome lasts the next three opportunities for that provider, not three global time steps. Repeated allegations can extend exclusion.
4. If the rule screens scope, pay the scope cost and decline a flagged task. A harmless task can be wrongly flagged and is counted as a false scope decline.
5. Verify if the rule checks all tasks, or if the reputation counter is below three successful deliveries, or with audit probability 0.1. Pay the verification cost. Pay any commitment cost.
6. A flagged breach is rejected before production. A false positive can also reject a non-breach; record it as a false rejection, not a prevented breach. This produces no output. Rules with exclusion also reset history and exclude the provider for its next three opportunities.
7. Otherwise pay production cost 1. A normal task succeeds. A failed task under a retry rule incurs diagnosis cost 0.3; an evidenced accident incurs retry cost 1 and succeeds with probability 0.8. A false diagnosis may incur a wasted retry on a breach, which still cannot be repaired. Failed diagnosis and failed retries still cost resources.
8. A completed task yields benefit 5 and increments good history. If it has an externality, subtract third-party harm, even after a successful repair. Remaining failures reset good history and, for exclusion rules, start bounded exclusion.

A `repair_no_exclusion` record retains verification history but ignores allegations and never excludes. `repair_no_appeal` removes only allegation appeals, not paid diagnosis after execution failure. `verify_and_retry` controls for retry being useful without reputation. `scope_only` controls for externality screening being useful without the repair package.

## Metrics

Let B be gross realized benefit, P production costs, V verification, C commitments, A diagnosis/appeal, R retries, S scope screening, and H third-party harm:

```
coordination_cost = V + C + A + R + S
participant_net  = B - P - coordination_cost
social_net       = participant_net - H
reported score   = social_net / number_of_opportunities
```

All costs are resource consumption, not monetary transfers. Restitution is **not implemented**. There are no endowments, borrowing limits, or insolvency. Negative social net is allowed.

`false_exclusions` counts excluded opportunities whose underlying task would have succeeded, including exclusions following genuine prior breaches. It is a counterfactual productive-opportunity metric, not a count of innocent people punished. `unrealized_benefit` is an ideal gross-benefit gap, not a feasible oracle welfare estimate; it is never subtracted again from net value. No recovery-time or catastrophe metric is claimed.

## Inference and reproducibility

For each scenario, policies share provider assignments and all exogenous events. Comparisons are paired by seed. The report resamples the vector of per-seed differences 2,000 times, taking the 2.5th and 97.5th percentile order statistics. Intervals are unadjusted for multiple comparisons. A run's events are not independent observations.

The source hash, event hashes, parameter values, and Python version provide a reproducibility record. Tape hashes establish identical inputs, not scientific validity or signatures of authority. To extend the simulator, keep exogenous randomness independent of the policy's number of draws. Changing the tape generator creates a new experiment and should be reported as such.

## Imperfect-evidence extension

The design in [studies/ROBUSTNESS_PLAN.md](studies/ROBUSTNESS_PLAN.md) was committed before its implementation and execution; it was not independently registered. `robustness.py` runs a fixed grid and checks two contrasts against independently written finite-tape payoff calculations. Every cell's parameters, raw policy outcomes, and paired intervals are published.

`false_rejections` counts verification refusals of non-breaches, including accidental tasks that might have been repairable. `false_scope_declines` is a subset of scope declines. `wasted_retries` counts paid attempts to retry a misdiagnosed breach. None should be relabeled as successfully prevented harm.

The new random stream leaves all original v0.1 fields unchanged. At false-positive rate zero, every metric shared with the 2,880 original baseline runs was checked for exact equality. Event hashes and source hashes change because records now include the new draws and the implementation has changed; the v0.1 tag preserves the original artifact.

`verify_results.py` checks source fingerprints, saved robustness data hashes, counts, and accounting. With `--rerun`, it regenerates both full studies in a temporary directory and compares data and reports exactly. Fingerprints detect accidental mismatch, not malicious modification of both data and manifest; they are not cryptographic attestations of correctness.

## Important non-results

- Fixed rules and exogenous failures cannot establish strategic stability, incentive compatibility, voluntary adoption, moral truth, or advanced-agent alignment.
- The model has bounded unit production losses; it omits theft of accumulated assets, leaked secrets, tail catastrophes, and an adaptive attacker. Naive trust may therefore look much better than in a high-stakes environment.
- The aggregate requester hides distributional inequality and asymmetric power. A social-net number is not proof that every affected party benefits or consents.
- Externalities are modeled as a known nonnegative loss on completion; there is no uncertainty in loss magnitudes beyond detection/classification, delayed harm, affected-party discovery, or disagreement over valuation.
- Policies use a common public history and trustworthy evidence channel. Authenticity, collusion, false evidence, decentralization, and appeal abuse are not solved.
- Three-success trust and three-opportunity exclusion thresholds are unoptimized modeling choices. Policy families have not received equal tuning budgets.
- A finite stress suite is not a representative distribution over possible worlds. Intervals do not capture these structural limitations.
