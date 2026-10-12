# keiba — ecological individuality & competitive context

**研究の中心：競走馬の個体差・環境反応規範・競争相手の構成が、相対的な競走成績をどう変えるか。**

This repository is being developed as a reproducible observational research program at the intersection of **individual ecology, phenotypic plasticity, competitive interactions and equine performance science**. The ecological hypotheses are currently **proposed, not empirically supported**.

## Research questions

1. **Individual reaction norms:** do horses differ in how their performances change with ground condition, after controlling for course, distance, age, class and jockey?
2. **Biotic context:** does a horse's historically measured running-style profile interact with the pre-race composition of opponents?
3. **Specialization** (exploratory): is environmental performance specialization associated with a robustness trade-off, after correcting for selective race entry?

Read:
- [Ecological research design: hypotheses, alternatives, models, falsification criteria](docs/ecology-research-plan.md)
- [Longitudinal horse–race panel specification and leakage checks](docs/ecology-panel-schema.md)
- [Actual Kyoto 2026-10-12 archive: explicit H1/H2 data-gap audit](docs/ecology-archive-gap-audit.md)

## Current evidence / not yet done

- Present on the separate experimental branch [analysis/kyoto-20261012](https://github.com/zuizui0223/keiba/tree/analysis/kyoto-20261012): a single Kyoto race-day card with descriptive horse histories, source/time-stamped odds snapshots, market-comparison scripts and reproducibility checks.
- **Not yet present on this research branch**: multi-year horse–race panel, official finish-time outcome table, pre-race opponent-behavior history, fitted random-slope models, or out-of-time validation.
- One-day win/place/third summaries cannot establish reaction norms, adaptive specialization, animal personality, natural selection, competition causality, or expected wagering returns.

## Research vs decision support

Ecological outputs will focus on conditional performance curves, horse-level slope variation, opponent-context interactions and uncertainty, with temporal validation and explicit competing explanations.

Historical odds/ticket analysis and betting decision support belong to the [separate Kyoto draft PR](https://github.com/zuizui0223/keiba/pull/1). They will not count as ecological evidence. No bet placing or financial return claims are made here.

## Literature anchors

- Dingemanse et al. 2010, behavioural reaction norms: https://doi.org/10.1016/j.tree.2009.07.013
- van de Pol 2012, random-regression design: https://doi.org/10.1111/j.2041-210X.2011.00160.x
- Maeda et al. 2012, track conditions and times: https://doi.org/10.1016/j.jevs.2012.02.012
- Oda et al. 2024, Japanese Thoroughbred performance and mixed models: https://doi.org/10.1111/jbg.12822

Already-published mixed-model and track-condition studies mean this is **not** a novelty claim. The proposed competition × individual-environment interaction and robust longitudinal validation require literature review and independent verification.


## Reproduce the research pipeline (fabricated data only)

The executable prototype requires Python 3.12+, NumPy, pandas, SciPy and statsmodels.
It is **not** a confirmed ecological model and has **no connection to betting**.

```bash
python -m pip install 'numpy>=1.26,<3' 'pandas>=2,<3' 'scipy>=1.11,<2' 'statsmodels>=0.14,<0.15'
python scripts/ecology_demo_data.py --output tmp/fabricated.csv
python scripts/ecology_panel.py --input tmp/fabricated.csv --audit tmp/audit.json --features tmp/lagged.csv
python scripts/ecology_h1_pilot.py --input tmp/fabricated.csv --surface turf --permit-synthetic-demo --output tmp/h1-synthetic.json
python -m unittest discover -s tests -p 'test_ecology_*.py' -v
```

The artificial rows carry `source_license=synthetic`, and fitting is refused without
`--permit-synthetic-demo`; that flag refuses any non-synthetic rows. A successfully
fitted model on invented data is an **implementation smoke test**, not a research result.

For authorized real records, first prepare one CSV row per historical horse×race
start according to the [schema](docs/ecology-panel-schema.md), then run
`ecology_panel.py`. The full cross-going repeated exposure and rights gates must
pass before `ecology_h1_pilot.py` will run without demo mode.

Current H1 pilot uses *race-centred z-speed*, estimated after complete finish-time
rosters are available, a horse random intercept, and optionally a horse random
**within-individual ground-response slope**. Horse exposure means are estimated from
training dates only; train/test races are chronologically separated. It omits
several confounder adjustments (jockey, age, class changes, selective race entry),
cannot establish physiological plasticity, and reports no validated ecological
effect. H2 and confirmatory causal analyses are not yet fitted.

**Data rights:** JRA-VAN's standard Article 7 is restrictive about public
redistribution. Do not add real licensed extracts to this repository before
obtaining appropriate permissions:
https://jra-van.jp/info/rule.html and
https://developer.jra-van.jp/t/topic/899.
