# Reproducing the ecological research without mixing in betting analyses

**Current source of truth:** source-scoped result pages and
[evidence matrix](EVIDENCE_MATRIX.md), not the old
[long development notebook](../../ECOLOGY_RESEARCH.md).
The English [manuscript draft](../ecology-racehorse-individuality-manuscript-v1.md)
has not been submitted or peer reviewed.

## 1. Two distinct data categories

**Empirical source audit:**
[original Racing Queensland Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and the [original RQ SOAP open-data protocol](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).
The original runner records can change on re-fetch and
some historical source dates fail HTTP requests.
The included sample is **positive first GPS telemetry rows linked to
source numeric HORSES IDs**, not all verified actual starters.
We publish code, aggregate results, date-level source digests and
HOLD codes. Do not publish individual names, HORSES IDs, individual
section times, unverified jockey licence IDs or inferred finish records.

**Simulated method checks:** `scripts/ecology_demo_*.py` and
`scripts/ecology_h1_*.py`, `scripts/ecology_h2_*.py`
generate or test **fictitious horses and rival fields only**.
The success of a synthetic H1/H2 test is **not** evidence of
an observed environmental or competitor effect.

## 2. Standard checks

Run all commands **from the repository root**, preferably
in Python 3.12 (the ecology GitHub Actions uses this version).
The pre-existing ecological CI installs:

```bash
python -m pip install 'numpy>=1.26,<3' 'pandas>=2,<3' 'scipy>=1.11,<2' 'statsmodels>=0.14,<0.15'
python -m unittest discover -s tests -p 'test_ecology_*.py' -v
```

Run the unrelated betting regression tests separately:

```bash
python scripts/run_non_ecology_tests.py
```

Run repository navigation verification (Python standard library only):

```bash
python scripts/check_repository_navigation.py
python -m unittest discover -s tests -p 'test_repository_navigation.py' -v
```

GitHub workflows also run the
[ecology-only suite](../../.github/workflows/ecology-tests.yml),
[betting/v3.1 suite](../../.github/workflows/tests.yml),
and source-specific ecological audit actions in
[`.github/workflows/`](../../.github/workflows/).
A GitHub Action being **green means the code ran**;
inspect each anonymous result artifact's `status` to know
whether the corresponding biological comparison was
numerically supported or **scientifically HOLD**.

## 3. Source result reproduction and version boundaries

1. Begin from a declared source-cohort lock in
   [`docs/ecology-*.md`](../) (meeting dates, race numbers,
   marker, distance and comparison gates). Do not choose a
   new calendar after seeing an appealing outcome.
2. Use the original RQ-specific
   [source join/parser scripts](../../scripts/) and their paired
   `tests/test_ecology_rq_*.py`. For example:
   [horse race-fixed ICC](../../scripts/ecology_rq_race_fixed_icc.py),
   [rider historical prediction](../../scripts/ecology_rq_rider_forward_check.py),
   [Doomben horizon incidence](../../scripts/ecology_rq_doomben_matched_timescale_overlap.py).
3. Save original **meeting XML, race XML, GPS CSV and original
   HORSES-roster response hashes** per successful meeting date.
   Never state two source editions are identical unless the
   compared source fingerprint/record-denominator matches.
4. **Treat HTTP errors, zero-GPS, missing rider and absent true
   starter/finisher status separately.** A missing observation
   is not a measured zero and need not be a DNF.
5. If the pre-declared number of repeated source animals,
   dates, original marker/distance/Class contexts, or measurement
   source records fails, emit `HOLD`, not a noisy effect estimate.
6. Keep *both* favorable and unfavorable runs, including source
   reruns that switch a borderline test to HOLD. The 2025 Doomben
   first-marker source audit illustrates why:
   [source-availability audit](../ecology-rq-doomben-within-year-source-replay-results.md).
7. **Distinguish conditional observation from mechanism.** A
   numerical ICC or an earlier-horse RMSE advantage is not a
   variance component from genetics, stable innate personality,
   ground slope H1, actual-rider causality or social interaction H2.

### Four pinned aggregate evidence files

- [Cannon original source fingerprints](../evidence/rq-cannon-original-source-fingerprints-20261014.json)
- [Horse history forecasts and disjoint 2025/26 cohorts](../evidence/rq-racehorse-temporal-generalization-20261015.json)
- [Doomben exact animal-level context availability, aggregate only](../evidence/rq-doomben-identical-horse-timescale-overlap-20261015.json)
- [Doomben same-year source availability replays](../evidence/rq-doomben-same-year-rerun-availability-20261015.json)

These are **previously audited snapshots**; they do
not authorize exporting source-runner records or
substituting a later JRA betting-price quote for
a genuine RQ GPS response.

## 4. Figures and manuscript

- [Figure 1 code, two source-cohort RMSE panels](../../scripts/ecology_rq_manuscript_temporal_figure.py)
- [Figure 2 code, zero common eligible animal IDs](../../scripts/ecology_rq_manuscript_source_overlap_figure.py)
- [Corresponding figure tests](../../tests/test_ecology_rq_manuscript_temporal_figure.py),
  [source-overlap figure tests](../../tests/test_ecology_rq_manuscript_source_overlap_figure.py)
- [Full draft](../ecology-racehorse-individuality-manuscript-v1.md)

Figure 1 deliberately shows two **different animal samples**.
Figure 2 shows why those samples cannot identify
within-individual temporal change. Neither figure estimates
a causal elapsed-time effect or a reliable cross-horse-course
reaction norm.

## 5. Decisions reserved for future studies

For **H1**, require repeated confirmed horses in multiple going
conditions with stable distance, exact section marker and Class;
a minimum engineering support count is **not** a power analysis.
For **H2**, obtain actual competitor identities and
verified starters/individual finish times with an explicit
missing-outcome model, or collect direct telemetry of
focal–rival encounters under measured exposure.
See the [research next-study roadmap](ROADMAP.md).

Data rights and original RQ SOAP scope:
[official source fields](../ecology-rq-official-soap-vs-final-starters-jockey-data-scope.md).
