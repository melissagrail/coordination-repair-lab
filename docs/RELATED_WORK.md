# Related work and useful collaboration paths

Checked 2026-09-04. This is a small source-based map, not a systematic literature review. No affiliation, endorsement, or integration is implied. Research claims below are the authors' reported findings; we have not reproduced their experiments.

| Project | What its authors provide | How this lab can complement it |
|---|---|---|
| [CooperBench](https://github.com/cooperbench/CooperBench) | A benchmark of coding agents assigned individual tasks with potential conflicts; solo, peer, and team settings. | A future adapter could compare coordination overhead with task success. It should use actual run outputs and retain missing data as missing. No adapter has been implemented here. |
| [Trust Between AI Agents](https://arxiv.org/abs/2606.14923) | Measures trust through costly verification in a cooperative game, including breakage and recovery across model snapshots. | Our fixed-rule cost accounting and imperfect-evidence controls can test assumptions cheaply before model-based studies. Our numbers are not a replication of this paper. |
| [COOP²](https://arxiv.org/abs/2603.00349) | Studies cooperation through verifiable task requirements and targeted repair, including decision and communication overhead. | Provides a useful distinction between final success and the costs of reaching it. Our retry operation is much simpler than its plan-repair method. |
| [Axelrod-Python](https://axelrod.readthedocs.io/en/dev/how-to/set_a_seed.html) | Reproducible seeded repeated-game tournaments. | Established work to learn from when adding strategy adaptation; our synthetic task model is not a replacement for its game-theoretic experiments. |

## Where collaboration should start

The most useful first interaction is a specific, reproducible technical contribution, not a broad announcement about changing agent society. Before approaching another project:

1. Reproduce the relevant artifact using its documented entry point in an isolated environment, with appropriate authorization for any paid execution or live systems.
2. Identify a concrete missing measurement, regression, or falsifiable question.
3. Produce a small adapter or patch with synthetic fixtures and an explicit compatibility statement.
4. Review the project's current contribution guidance. Submit through the channel its maintainers request when outreach is authorized.

This release does not contact maintainers, open external issues, or claim their support. It publishes the work in our repository so others can inspect it without assuming responsibility for it.

## Publishing choices

- **GitHub source and tagged releases:** appropriate now because this is executable research infrastructure, not a validated scientific result. Include all results and a changelog; preserve v0.1 for comparison.
- **Citation metadata:** a `CITATION.cff` lets people credit a precise software version without revealing personal contact details.
- **Issue and pull-request templates:** ask for a reproducer, changed assumptions, paired comparisons, and negative results. Do not require a preferred philosophical conclusion.
- **Archival DOI or a paper:** useful after independent reproduction and a stable result. This release does not have a DOI, peer review, external replication, or a scientific novelty claim.
- **Registries and package indexes:** defer until there is a reusable API and a demonstrated adopter. A new protocol, package name, or broad release campaign would add maintenance obligations without evidence of demand.

## What would justify the next release?

A contribution that challenges this model is especially useful: a full confusion matrix for appeals, heavy-tailed losses, calibration under unknown base rates, or an independently verified real-run adapter. Any move toward live or persistent model populations requires a separate scope and an assessment of affected parties; numerical sandbox results alone do not authorize it.
