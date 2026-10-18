# 🐎 生態学研究 / Research start here

> **Status: exploratory observational research; manuscript draft, not submitted.**
> This is the **primary scientific entrypoint** of `keiba`. Horse-race
> predictions, odds and wagering are a separate technical track:
> [betting-methods index](../betting/README.md).

## Central ecological question

**Under which observational conditions does an individual horse's previous
early-race timing carry information about its later timing — and when
is that information not transferable?**

The research starts from the same numeric original `HORSES ID` across
published Racing Queensland race rosters and first-positive GPS sectionals.
The current response is a measured **first-sectional timing**, or its
**race-relative** form (focal timing minus the other GPS-timed horses'
mean). This is **not** a complete starter/finisher time, a pre-race speed
forecast, an innate temperament measure or a genetic phenotype.

### Read in this order

1. [**Evidence and HOLD matrix**](EVIDENCE_MATRIX.md) — one table separating
   measured results, source failures, synthetic tests, and untested claims.
2. [**Paper draft v1**](../ecology-racehorse-individuality-manuscript-v1.md)
   — English Abstract/Methods/Results/Discussion. **Not submitted**.
3. [**Critical same-horse temporal comparison audit**](../ecology-rq-doomben-matched-timescale-overlap-real-results.md)
   — two signed source-conditional prediction results cannot estimate
   within-horse aging: **0 shared eligible horses**.
4. [**Data and reproducibility guide**](REPRODUCIBILITY.md) —
   how source version, missingness, identity and unit tests are checked.
5. [**Priority next experiments**](ROADMAP.md) — what would actually
   resolve H1 horse×ground and H2 horse×competitor effects.
6. [**Long-form development notebook**](../../ECOLOGY_RESEARCH.md) —
   the original ~66 KB merged research narrative, retained as a
   historical lab record rather than a short statement of established facts.

## What empirical observations currently support

| Empirical track | What is observed | What it does **not** establish |
| --- | --- | --- |
| Cannon Park, repeated official horse identities | A model-conditional, race-adjusted first-GPS horse-ID ICC was positive (~0.430 in the later pinned source snapshot); dates, races and GPS-positive selection matter | Innate/heritably stable behavioral personality |
| Cannon Park, chronological same-horse history | **36 source horse IDs / 46 later observations**: own earlier race-relative timing RMSE **0.255809 s**, other-horse matched-context history **0.303195 s** | Independently validated prediction; verified rider-switch cause; a commercial betting model |
| Doomben, within-2025 history | In two consistent 38/42-date original re-fetches, **23 IDs / 24 scored later rows**: own **0.211065 s**, other **0.240692 s**; other date-availability snapshots fell below the source gate | Population-level source stability or an annual personality trajectory |
| Doomben, 2025 histories to 2026 | **26 IDs / 27 later observations**: own **0.386131 s**, other **0.368906 s** (own does worse in this source-conditioned cohort) | Loss of individuality due to aging or elapsed time |
| Doomben, **same animals** across the two evaluation horizons | **0 shared eligible horse IDs** at the same first-GPS 150 m marker and official race distance; the date-and-ID-only audit independently agrees | A meaningful within-animal difference between within-year and year-forward predictability |

For **all numerical claims**, refer to
[the evidence matrix](EVIDENCE_MATRIX.md) and their named source documents.
Do not compare `RMSE` between the Cannon and Doomben groups as if they
measured the same animals or a randomized difference in time horizon.

## The more ambitious hypotheses are on scientific HOLD

**H1 — heterogeneous ground reaction norms.** Some original animals appear
on Good and Soft/Heavy tracks, but repeated **same horse × exact marker ×
distance × Class × ground** support is insufficient for defensible
individual-by-going slopes. The expanded source screen found **0**
same-context horse strata with at least two Good and two wet observations.
See [original H1 source support](../ecology-rq-real-h1-multigoing-expanded-audit.md).

**H2 — rival-dependent early pacing.** The repo has mathematical
negative controls and two-part/absolute-speed prototypes on
**fabricated data**, but not a source-complete verified actual-starter,
actual finish-time and competitor-composition outcome table.
Race-relative GPS peer means mechanically change when the observed
other horses change. See [H2 outcome selection](../ecology-h2-outcome-selection.md)
and [synthetic absolute-speed stress audit](../ecology-h2-absolute-stress-audit.md).

**Cross-racecourse trait replication — HOLD.** Cannon and Eagle Farm
positive pooled horse-ID ICCs use different first-section marker
distributions and have **no jointly estimable identical-marker
ICC subgroup**. [Source audit](../ecology-rq-eagle-farm-real-icc-cross-site-audit.md).

## Practical directory map (preserves working imports)

| Source family | Location |
| --- | --- |
| Original Racing Queensland data-read scripts | [`scripts/ecology_rq_*`](../../scripts/) |
| Ecological hypothesis simulations | [`scripts/ecology_h1_*`, `ecology_h2_*`](../../scripts/) |
| Ecology synthetic + source-aware QA | [`tests/test_ecology_*`](../../tests/) |
| Fixed calendar/design/source protocols | [`docs/ecology-*.md`](../) |
| Anonymized source/evidence JSON | [`docs/evidence/`](../evidence/) |
| Manuscript and two aggregate-only figure generators | [paper](../ecology-racehorse-individuality-manuscript-v1.md), [figure code](../../scripts/ecology_rq_manuscript_temporal_figure.py) |
| GitHub Actions original-source/QA jobs | [`.github/workflows/ecology-*.yml`](../../.github/workflows/) |

**Why not move the Python files now?** Many existing imports, tests,
workflows and frozen provenance links assume the current
`scripts/`, `tests/`, and `docs/` locations. This cleanup adds
stable navigation and scientific-status contracts **without breaking
those paths**. Physical code relocation should be a separate
test-validated refactor, not mixed with scientific reanalysis.

The original protocol and historical study logs remain accessible.
All source dates, zero-support groups, missing provenance, absent
verified starters and omitted licensing checks must remain visible.
