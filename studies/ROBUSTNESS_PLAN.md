# Imperfect evidence study plan

Recorded before the v0.2 robustness runner and its results were produced. This is a versioned development plan, not an independently registered study.

## Question

Which apparent benefits of retry and third-party screening survive when evidence can wrongly flag a benign interaction? Keep all results, including losses. Do not optimize grid points after seeing their outcomes.

## Fixed design

Retain the v0.1 baseline configuration and random sequence for its original event fields. Add independent false-positive draws from a separate deterministic random stream. A check has a true-positive probability (`evidence_accuracy`) and a false-positive probability. The old sensitivity variable and shared true-positive evidence draw remain unchanged; this is an incremental experiment, not a complete evidence model.

Two factorial panels, each using 20 paired seeds (0–19), 1,000 opportunities per run, 30 providers, and two sensitivities (0.6, 0.95):

- **Retry:** false-positive rate {0, .01, .05, .15, .30}; retry cost {.2, 1, 3, 5}; accident rate {.05, .25}; verification cost {.01, .6, 1.5}. No breaches, allegations, or externalities. Compare naive trust, always verify, verify-and-retry, and repair without exclusion. This isolates accidental failures and unnecessary rejection of repairable work.
- **Scope:** false-positive rate {0, .01, .05, .15, .30}; externality prevalence {0, .01, .05, .20, .35}; harm {1, 6, 12}; screening cost {.1, .6}. No accidents, breaches, or allegations. Compare naive trust and scope-only screening. This isolates the cost of unnecessary refusal and permits a closed-form oracle.

The design has 240 retry cells and 300 scope cells: 31,200 policy runs in total. These counts exclude baseline replication and tests.

## Evidence and metrics

A breach detector may reject a non-breach; a scope check may decline a harmless task; a retry diagnosis may misclassify a breach as an accident and waste its retry cost. Such a retry cannot fix a breach. True-positive and false-positive probabilities refer to different underlying truth classes, not independent decisions on the same label.

Separate metrics distinguish false verification rejections, false scope declines, and wasted retries. Preserve accounting conservation. No authority verification, cryptography, or real-world policy enforcement is implied.

Primary comparisons are paired differences in social net per opportunity: repair-without-exclusion minus naive trust; verify-and-retry minus always-verify; and scope-only minus naive trust. Report every cell, mean outcomes, and unadjusted 95% percentile bootstrap intervals over seeds (2,000 draws, seed 0). Treat these as descriptive Monte Carlo intervals, not confirmatory evidence across 540 comparisons. Do not report an overall win fraction as a probability over real environments.

## Analytic checks

In the scope panel, let s = benefit − production cost, p = harm prevalence, H = harm per completed harmful task, t = sensitivity, f = false-positive probability, and c = screening cost. Then:

```
E[scope − naive] = p*t*(H − s) − (1 − p)*f*s − c
```

This must agree with the simulation within sampling variation. A finite-tape oracle should match exactly, up to floating-point accumulation.

For always-verify versus verify-and-retry in the accident-only panel, a retry gives benefit B with probability r when an accident is diagnosed (sensitivity t), costs R if diagnosed, and costs diagnosis A for each failed attempted task. Verification falsely rejects a fraction f of all non-breaches. Expected incremental net is:

```
(1 − f)*accident_rate*(t*(r*B − R) − A)
```

These identities check the implementation and explain when interventions lose. They do not validate the realism of the model.

## Publication

Keep the v0.1 tag and baseline findings. Publish the complete v0.2 CSV, summary, source/input fingerprints, and these assumptions. Use deterministic tests, analytic controls, and CI. Credit related work without implying endorsement. Invite counterexamples through reusable contribution templates; do not promise future maintenance or send unsolicited outreach.
