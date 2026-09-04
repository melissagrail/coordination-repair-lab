# Imperfect evidence: robustness results

31,200 policy runs across 540 parameter cells; 20 paired seeds and 1,000 opportunities per run.

**Synthetic model, not real agent behavior.** The cells form a chosen factorial grid, not a representative distribution of environments.

Complete cell results: [summary.csv](summary.csv). Every policy run: [runs.csv](runs.csv). Inputs, source fingerprints, and parameters: [manifest.json](manifest.json).

## Analytic controls

Every finite-tape scope and verify-and-retry contrast agrees with an independent payoff calculation to within 1e-9 units per opportunity.

The population formulas explain why the rankings change:

```text
scope − naive = p*t*(H − s) − (1 − p)*f*s − screening_cost
verify_and_retry − always_verify = (1 − f)*a*(t*(r*B − retry_cost) − diagnosis_cost)
```

Here s is benefit minus production cost, p is harmful-task prevalence, t sensitivity, f false-positive probability, H third-party harm, a accident probability, r retry success probability, and B benefit.

## Predefined grid: positive and negative mean differences

Counts below describe grid cells only. They are not win probabilities for real environments; no significance claim is made.

| Comparison | Positive mean | Negative mean | Zero mean |
|---|---:|---:|---:|
| repair_no_exclusion − naive_trust | 52 | 188 | 0 |
| verify_and_retry − always_verify | 180 | 60 | 0 |
| scope_only − naive_trust | 56 | 244 | 0 |

## Illustrative slice: when screening becomes over-refusal

Sensitivity .95, harm prevalence .05, harm 12, screening cost .1. All rows of this slice are shown; the entire grid remains available above.

| False-positive rate | Mean scope − naive | 95% lower | 95% upper | Analytic expectation |
|---|---:|---:|---:|---:|
| 0.00 | 0.2884 | 0.2732 | 0.3044 | 0.2800 |
| 0.01 | 0.2546 | 0.2378 | 0.2720 | 0.2420 |
| 0.05 | 0.1108 | 0.0962 | 0.1262 | 0.0900 |
| 0.15 | -0.2650 | -0.2842 | -0.2446 | -0.2900 |
| 0.30 | -0.8318 | -0.8566 | -0.8066 | -0.8600 |

## Limits

- Bootstrap intervals are unadjusted across many comparisons and quantify Monte Carlo variation only.
- The retry panel has no intentional breaches. It tests recovery from execution failure, not incentives or resistance to exploitation.
- The scope panel assumes known costs in one common unit. It does not establish consent, fairness, or how to discover affected parties.
- False-positive draws are independent across channels; true-positive evidence is still shared within an opportunity.
- False allegations can fail to clear; truthful allegations and a full appeal confusion matrix are not modeled.
- Reputation, screening, and retry rules remain fixed. No strategic learning or live agent deployment occurred.
- The study plan was committed before running this study, but was not independently preregistered.
