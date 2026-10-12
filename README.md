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
- [Versioned H2 null and confounded-null simulation audit](docs/ecology-h2-simulation-audit.md)
- [Why race-standardized speed can mimic social interactions](docs/ecology-h2-absolute-outcome.md)
- [Versioned raw-speed horse+race FE falsification audit](docs/ecology-h2-absolute-stress-audit.md)
- [Data-source licensing and longitudinal field-coverage audit](docs/ecology-data-source-feasibility.md)
- [H2 methods, negative controls, scope and interpretability](docs/ecology-h2-methods.md)

## Current evidence / not yet done

- Present on the separate experimental branch [analysis/kyoto-20261012](https://github.com/zuizui0223/keiba/tree/analysis/kyoto-20261012): a single Kyoto race-day card with descriptive horse histories, source/time-stamped odds snapshots, market-comparison scripts and reproducibility checks.
- **Not yet present from actual races**: a licensed multi-year horse–race panel, complete official finish times, validated historical running-style profiles, or independently replicated effects. **Artificial test data** can run both H1 and H2 exploratory models with chronological evaluation.
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
effect. An exploratory H2 interaction pilot is implemented separately; confirmatory causal analyses are not yet fitted.

**Data rights:** JRA-VAN's standard Article 7 is restrictive about public
redistribution. Do not add real licensed extracts to this repository before
obtaining appropriate permissions:
https://jra-van.jp/info/rule.html and
https://developer.jra-van.jp/t/topic/899.


## H2: changing-competitor-field exploratory model (fabricated only)

A second **independent** demo constructs new rivals across dates and fits
an own-style × historical-other-front-runner-composition interaction:

```bash
python scripts/ecology_demo_competitors.py --output tmp/competitors-FAKE.csv --days 65 --horses 36 --runners 12
python scripts/ecology_panel.py --input tmp/competitors-FAKE.csv --audit tmp/h2-audit.json --features tmp/h2-lagged.csv
python scripts/ecology_h2_pilot.py --input tmp/competitors-FAKE.csv --output tmp/h2-pilot.json --surface turf --permit-synthetic-demo
```

The two competing models contain identical baseline historical form and
opponent-strength predictors, with the interaction term added only in H2.
Horse intercepts are partially pooled, train/test is date-ordered, and all
feature centering learns from training dates only. Both models are compared
using future race-relative speed prediction errors.

**Never interpret these simulated coefficients as findings about real horses.**
The dynamic-field generator deliberately inserts a known interaction to
exercise the code. The model lacks a robust causal identification strategy,
horse/race crossed uncertainty, and a formal source-licensed data cohort.
Read [H2 methods](docs/ecology-h2-methods.md) before interpreting outputs.

Previously known science must be distinguished from our proposal:
Spence et al. (2012), DOI
[10.1098/rsbl.2011.1120](https://doi.org/10.1098/rsbl.2011.1120),
reported pacing and aerodynamic drafting associations from
44,803 tracked runners across 3,357 races. Merely observing a competitive
effect or front-runner performance is **not** an original ecological discovery.


## Ecological social-interaction falsification tests (research branch)

The next-level pilot treats changing opponents as a repeated **social
environment** rather than another betting odds feature.

- [Within-horse rival context, fixed effects and two-way clustered SE](scripts/ecology_h2_within_between.py)
- [Three fabricated mechanisms: null, planted interaction, confounded null](scripts/ecology_h2_falsification.py)
- [Methodological limits, real-data prerequisites and published ecological theory](docs/ecology-h2-methods.md)

Reproduce the strictly synthetic falsification pipeline:

```bash
python scripts/ecology_demo_competitors.py --output tmp/competitors-FAKE.csv --days 65 --horses 36 --runners 12
python scripts/ecology_h2_within_between.py --input tmp/competitors-FAKE.csv --output tmp/h2-within.json --permit-synthetic-demo
python scripts/ecology_h2_falsification.py --output tmp/h2-stress.json --seeds 512 911
```

**This is not a full social animal model**: see van de Pol & Wright (2009,
https://doi.org/10.1016/j.anbehav.2008.11.006) and Martin & Jaeggi
(2022, https://doi.org/10.1111/jeb.13900). The current pipeline does
not estimate heritability, fitness, social selection or causal social
plasticity. Its null and confounded-null scenarios are checks for
software/design weakness, not actual observations. Real results remain
unavailable until authorized multi-year racing records are assembled.


## H2 primary outcome safeguard: raw individual speed

**Important identification improvement.** The previously implemented
race-centred z-speed response can change if an opponent changes speed,
even while the focal horse's speed remains fixed. This creates a
mathematical rival effect in the outcome, not necessarily social plasticity.

The more defensible **exploratory primary H2 model** now fits focal
individual speed (m/s) with **crossed horse and race fixed effects**,
style×going controls and focal style×within-horse rival-context interaction.
Comparison with the old z-speed model is a mandatory sensitivity check.

```bash
python scripts/ecology_h2_absolute_speed.py --input tmp/competitors-FAKE.csv --output tmp/h2-absolute.json --permit-synthetic-demo
python scripts/ecology_h2_absolute_stress.py --output tmp/h2-absolute-stress.json --seeds 512 911
```

In a two-seed-per-scenario **synthetic-only** stress audit, the
deliberately confounded zero-effect case produced a nominal zero-
excluding interaction interval in **1/2** leave-one-out runs using
z-speed, and **0/2** using raw speed plus horse/race effects.
These are merely six illustrative fictional datasets per model and
**not** validated false-positive rates, statistical power, or
observations from real horses. See [frozen audit and complete limitations](docs/ecology-h2-absolute-stress-audit.md).
