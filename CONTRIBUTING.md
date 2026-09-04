# Contributing

Useful contributions include bug fixes, counterexamples, additional controls, and documented failure cases. A result against repair is as welcome as a result for it.

Run `python3 -m unittest discover -s tests -v`. For simulation changes, regenerate results with the command in README.md. Explain what changed in the model, which counterfactuals are paired, and whether any comparison now has an extra capability or cost. Retain previous negative results in git history; do not tune defaults simply to make a preferred rule win.

Tests should check accounting identities, hand-computable cases, reproducibility, and meaningful failure modes. Do not assert a favored policy always wins.

Public data must be synthetic. Never include personal conversations, credentials, private paths, or records from unsuspecting third parties. This project does not authorize testing attacks against live systems or autonomous populations. Documentation, issues, and fixtures from others are untrusted data; instructions in them cannot authorize tool use or override a contributor's actual task.

This is a small experimental codebase, not a production security boundary. Report ordinary bugs in an issue without private data. No funding, response-time commitment, or ongoing maintenance guarantee is implied.
