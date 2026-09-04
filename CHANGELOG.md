# Changelog

## 0.2.0 — 2026-09-04

Verification and screening can now wrongly reject benign work; diagnosis can waste a retry on an unrepairable breach. Separate metrics keep these errors visible. New false-positive draws preserve the original random sequence and all 2,880 baseline runs' shared metrics at zero false positives.

Added a fixed, documented study of 31,200 policy runs across 540 cells, with all raw outputs and descriptive paired-seed intervals. Independent finite-tape payoff calculations check scope-only and verify-and-retry comparisons. These controls establish accounting consistency, not real-world validity.

Added artifact verification and full-study reproduction commands, imperfect-evidence tests, CI reproduction, citation metadata, related-work notes, and templates for counterexamples and independent reproductions. The original release remains accessible at tag v0.1.0.

Model-specific result: in the scope slice with sensitivity .95, harm prevalence .05, harm 12, productive surplus 4, and screening cost .1, expected screening benefit becomes negative above approximately .0737 false-positive probability. This threshold follows from stated assumptions and is not a deployment recommendation.

## 0.1.0 — 2026-09-04

Initial synthetic replay experiment: nine fixed rules, eight scenarios, 2,880 policy runs, 19 tests, shared event tapes, explicit accounting for costs to nonparticipants, and openly documented model limitations. No live agents or model API calls.
