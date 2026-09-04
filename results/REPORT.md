# Coordination Repair Lab — measured results

2,880 runs; 40 paired seeds per scenario; 2,000 opportunities per run.

**Synthetic sensitivity study, not evidence of agent alignment or equilibrium selection.**

These are arbitrary model units, not dollars, tokens, or empirical welfare estimates. Larger social net is better.

## Mean social net per opportunity

| Scenario | always_verify | naive_trust | reputation_only | repair | repair_no_exclusion | verify_and_retry | scope_only | repair_no_appeal | repair_with_scope |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| benign | 3.400 | 4.000 | 3.916 | 3.866 | 3.866 | 3.400 | 3.900 | 3.866 | 3.766 |
| mixed_shock | 2.353 | 2.801 | 1.737 | 2.058 | 2.683 | 2.472 | 2.753 | 1.943 | 2.042 |
| uniform_reliability | 2.582 | 3.086 | 1.975 | 2.353 | 2.962 | 2.702 | 3.039 | 2.219 | 2.336 |
| accidental_failures | 2.140 | 2.740 | 1.359 | 2.709 | 3.169 | 2.789 | 2.640 | 2.709 | 2.623 |
| cheap_verification | 1.719 | 1.276 | 0.769 | 0.859 | 1.711 | 1.832 | 1.218 | 0.829 | 0.844 |
| poor_evidence | 2.241 | 2.801 | 1.701 | 1.679 | 2.417 | 2.193 | 2.715 | 1.655 | 1.628 |
| identity_churn | 2.353 | 2.801 | 1.919 | 2.149 | 2.511 | 2.472 | 2.753 | 2.070 | 2.130 |
| third_party_costs | -0.827 | -0.379 | -0.367 | -0.465 | -0.657 | -0.868 | 1.695 | -0.442 | 1.325 |

## Paired differences: repair minus always_verify

95% percentile bootstrap intervals over seeds; no multiple-comparison correction. These quantify Monte Carlo variation under fixed assumptions, not model uncertainty.

| Scenario | Mean difference | Lower | Upper |
|---|---:|---:|---:|
| benign | 0.466 | 0.465 | 0.467 |
| mixed_shock | -0.296 | -0.314 | -0.277 |
| uniform_reliability | -0.230 | -0.244 | -0.215 |
| accidental_failures | 0.568 | 0.549 | 0.587 |
| cheap_verification | -0.859 | -0.886 | -0.831 |
| poor_evidence | -0.562 | -0.577 | -0.548 |
| identity_churn | -0.204 | -0.216 | -0.191 |
| third_party_costs | 0.362 | 0.341 | 0.381 |

## Interpretation limits

- Provider breach propensities persist within a run; the uniform_reliability control removes heterogeneity. Identity resets erase public history but preserve latent propensity.
- Policies are fixed rules. No language models, strategic learning, voluntary institutional choice, or conscious populations are instantiated.
- Failure events are exogenous. An adaptive attacker may react to policy; this replay cannot measure that.
- Scope checks have known false negatives but no false positives; repair diagnoses have false negatives but no false positives. Both assumptions favor the corresponding interventions.
- Commitments currently add cost only. Their independent benefit is unmodeled, so this is not a test of commitment semantics.
- Reputation uses provider identity and bounded exclusion. There is no authenticated identity, decentralization, insolvency, restitution transfer, or enforcement model.
- Parameter regimes are illustrative stress cases, not a representative sample of future environments.
- Read MODEL.md before treating any ranking as a design recommendation.
