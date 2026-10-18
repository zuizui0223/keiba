# Evidence matrix — what the horse ecology repo actually knows

**Updated 2026-10-18.** Read this before interpreting any figure,
paper paragraph, workflow success, or historical top-level README.
**All animal findings here are retrospective observational,
selected on original-source availability**, not preregistered
independent horse experiments.

## Decision vocabulary

| Label | What it permits |
| --- | --- |
| **OBSERVED / SOURCE-CONDITIONAL** | A numeric result for the stated fixed original-source snapshot and measurement/selection gate only |
| **OBSERVED / NONTRANSFER** | A source-specific result unfavorable to a transfer hypothesis; not proof a biological trait vanished |
| **HOLD / NONIDENTIFIABLE** | Cannot estimate the proposed ecological mechanism or comparison with current matching individuals/measurements |
| **HOLD / SOURCE COVERAGE** | An upstream date, original roster, matched horse or endpoint is missing or inconsistent; **not** a zero biological outcome |
| **SIMULATION ONLY** | Software behavior on artificial horse/competitor data; **not** a real-animal result |
| **UNTESTED** | A planned causal, population, genetic or evolutionary claim without an empirical result |

Never use `CI pass` (a GitHub Action process exit code) as a substitute
for scientific `OBSERVED` versus `HOLD` in the saved artifact.

## Empirical findings and their denominators

| ID / status | Source, measurement and sample | What was actually seen | Limitation and source audit |
| --- | --- | --- | --- |
| **R1 — OBSERVED / SOURCE-CONDITIONAL** | Cannon Park 2026, original numeric HORSES ID; race-fixed **absolute** first positive GPS segment (>=4 timed peers/race) | Race-fixed horse-ID Gaussian ICC **0.430147** in a later source snapshot; an earlier run with different joins found **0.431738** | Different snapshots/screening: don't silently pool sample sizes. The later fitted-Gaussian 299-simulation estimator quantiles **0.313683–0.528432** are **not an empirically validated 95% population CI**. [Source conditional audit](../ecology-rq-real-icc-source-conditional-sampling.md), [earlier ICC audit](../ecology-rq-real-horse-race-adjusted-icc.md) |
| **R2 — OBSERVED / SOURCE-CONDITIONAL** | Cannon Park, 12/12 preselected dates; 36 source HORSES IDs, **46 later rows**, 11 later dates, same first GPS marker and official race distance | Equal-horse-weighted RMSE: past **own** horse **0.255809 s** vs **other** horses with same measurement context **0.303195 s**; no horse profile **0.297676 s** | This is retrospectively scored later **race-relative** first GPS time (postrace peer set); rider licence not previously documented within context is **not verified actual jockey switch**. [Real source results](../ecology-rq-forward-other-horse-comparator-results.md), [forward analysis](../ecology-rq-rider-change-forward-validation-results.md) |
| **R3 — OBSERVED / SOURCE-CONDITIONAL** | Cannon Park, 36 HORSES IDs with different *documented* source Jockey/@Id in 72 dated same-horse/marker/distance pairs | Positive mean centered pair product **+0.063583 seconds²**, still positive in **12/12** leave-one-date and **36/36** leave-one-horse screens | Not a causal jockey-change response, not an independent 36-horse confirmation; rider assignment and GPS missingness remain. [Original source influence audit](../ecology-rq-real-rider-switch-persistence-audit.md) |
| **R4 — OBSERVED / SOURCE-CONDITIONAL; SOURCE COVERAGE FRAGILE** | Doomben 2025, same venue/year, 150 m first GPS marker, same distance, **23 IDs / 24 scored later rows** in two identical **38/42** original date-source reruns | Past own horse RMSE **0.211065 s** versus earlier other-horse context history **0.240692 s** | Earlier separate original requests fetched different dates: one had **21/21** scored, another **17/18 → HOLD**; source-date coverage determines support. Independent reruns using the **same source snapshot** are not independent populations. [Original rerun audit](../ecology-rq-doomben-within-year-source-replay-results.md) |
| **R5 — OBSERVED / NONTRANSFER** | Doomben **2025 training records → 2026 observed records**, 150 m and same original race distance; **26 IDs / 27 scored later rows** | Own 2025 profile RMSE **0.386131 s** vs other-horse 2025 profile **0.368906 s**; own not advantageous **in this scored group** | Leave-one-out can reverse sign for **1/26 horses** and **1/10 future source dates**. Not a within-animal age effect or universal negative result. [Official year-forward results](../ecology-rq-doomben-2025-to-2026-year-forward-results.md) |
| **R6 — HOLD / NONIDENTIFIABLE** | Doomben exact 150 m, original distance; across **38/42** locked available dates, scoring groups R4 23 IDs and R5 26 IDs | **0 shared eligible HORSES IDs** between within-2025 and 2025→2026 prediction evaluations; independent *outcome-blind* original ID/date incidence also found **0 IDs** with >=2 dates in 2025 + >=1 in 2026 in the same exact marker/distance context | The **difference R4−R5 is not a within-horse time-horizon effect**. This is **lack of common measurement support**, not animals disappearing. Original data across all markers still had **977 IDs, 228 repeated across dates**. [Independently reproduced source overlap](../ecology-rq-doomben-matched-timescale-overlap-real-results.md), [pinned anonymous counts](../evidence/rq-doomben-identical-horse-timescale-overlap-20261015.json) |
| **R7 — HOLD / NONIDENTIFIABLE** | Cannon versus Eagle Farm independent source cohorts: pooled race-fixed ICC **0.430147 / 0.453332** in later model-conditional source snapshots | Both numbers positive but **no identical first-GPS marker has an estimable ICC in BOTH tracks** | Not independent same-trait biological replication; different GPS marker distributions, individuals and field contexts. [Matched marker gate](../ecology-rq-eagle-farm-real-icc-cross-site-audit.md) |
| **R8 — HOLD / NONIDENTIFIABLE: H1** | Expanded original Cannon Good/Soft/Heavy source screen: **37** HORSES IDs seen in Good and wet; only **17** same marker+distance, only **2** also same source Class | **0** original animal/context strata observed >=2 times Good AND >=2 times wet | Cannot fit reliable horse-by-ground reaction norm, explain variance by ground, or assert ground adaptation. [Expanded H1 feasibility](../ecology-rq-real-h1-multigoing-expanded-audit.md) |
| **R9 — SIMULATION ONLY; H2 EMPIRICALLY HOLD** | Synthetic rival composition, absolute speed, nonfinishing/telemetry selection, within-between negative controls | Method tests avoid some mechanically created rival effects when outcome is focal absolute speed instead of same-race relative difference | Genuine complete confirmed starters, real original field identities, final rider, **absolute full-race finish time**, and nonfinish denominator are not linked. [H2 selection](../ecology-h2-outcome-selection.md), [synthetic stress](../ecology-h2-absolute-stress-audit.md) |
| **R10 — HOLD / SOURCE PROVENANCE** | Different original Cannon historical runs | Older **548** versus newer **543** original numeric-HORSES ID / positive GPS candidate joins; five original dates differ by one | Meeting/race/GPS bytes archived as equal; **older per-race horse-roster response hashes absent**, so horse-roster revisions vs parser/join changes unresolved. Don't silently claim identical source editions. [Source drift audit](../ecology-rq-cannon-original-source-drift-20261014.md) |
| **R11 — HOLD / MEASUREMENT/METADATA** | Original RQ `GetHorsesForRace`, `GetHorseDetailsInRace`, positive GPS source | Source numeric `Jockey/@Id`, `Trainer/@Id` are assigned/recorded labels, **not independently verified final actual riders or starters**. The first positive GPS sectional is not the certified full-race finish time | Racing Queensland may offer separate results/scratchings/alteration datasets, but those are **not integrated in this empirical panel**. [Official SOAP schema scope](../ecology-rq-official-soap-vs-final-starters-jockey-data-scope.md) |

## Claim ledger / no silent promotion

| Biological claim | Current status | Required to upgrade |
| --- | --- | --- |
| An original horse ID carries out-of-time predictive information *in the measured Cannon cohort* | **Supported only as R2 source-conditional association** | Independent prospective source-fixed cohort and complete measurement/selection audit |
| Horse-ID repeatability is intrinsic, genetic, inherited temperament | **UNTESTED** | Validated repeated behavioral phenotype, pedigree/genomic or experimental design, training and rider confounding control |
| A jockey replacement *causes* stable or altered pacing | **UNTESTED** | Actual independently verified final jockey, same-horse repeated switches, role/horse selection adjustment |
| Individual response slopes to Good/Soft/Heavy (H1) | **HOLD** | Repeated same marker/distance/Class/horse at multiple ground levels |
| Rivals' identities/strategies *cause* focal pacing changes (H2) | **HOLD** | Verified actual starters, pre-race opponent exposure, absolute focal outcome, missingness framework |
| Horse personality predictability *decreases with a calendar year* | **HOLD — R6 has ZERO shared animals** | Common animal×measurement cohort scored at both horizons |
| The same trait repeats across different racecourses | **HOLD — unmatched GPS first markers** | A sufficient source-supported common marker with repeated same animals where biologically comparable |
| A positive racehorse ICC means better wagers or positive betting expected value | **UNTESTED and a category error** | Separate calibrated ticket-event probabilities and genuine out-of-sample financial validation; **not an ecology claim** |

## Why these distinctions matter

**Do not interchange outcomes.** An *absolute* focal first-sectional
time with race fixed effects (R1) and a focal time **minus observed GPS
peer mean** (R2–R6) are different targets. The latter changes
mathematically if observed peers change, even if the focal horse's
absolute timing does not.

**Do not interchange populations.** A Doomben horse's 2025 within-year
evaluation and another horse's year-forward 2025→2026 evaluation cannot
be treated as the same animal followed longitudinally.

**Do not interchange uncertainty types.** A leave-one-date range,
source re-fetch reproducibility, Gaussian parametric
model-dependent quantile range and population confidence interval
are not equivalent. None of these audits estimates a causal
`horse × ground`, `horse × rival`, genetic, or fitness effect.

**Next action:** [ROADMAP.md](ROADMAP.md).
