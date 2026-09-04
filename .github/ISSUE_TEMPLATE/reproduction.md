---
name: Independent reproduction
about: Report agreement or disagreement with a tagged release
labels: ''
---

## Version and environment

Release or commit, Python version, operating-system family, and command. Omit user names and private filesystem paths.

## Outcome

Did `python3 verify_results.py --rerun` pass? If not, which artifact or check differed?

## Differences

Describe changes in configuration, source, or dependencies. Attach only small, synthetic reproducing examples.

## Interpretation

Reproducing output is a software check, not validation that the model describes real agents. Explain any additional conclusions separately.
