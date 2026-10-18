# Research roadmap: next **identifiable** biological question

**As of 2026-10-18.** This is a design priority plan,
not a statement that a physiological or evolutionary effect
was found. Science first; wagering prices and bet outcomes
do not constitute ecological evidence.

## The actual overarching question

> **When does an individual horse's past early-race behavioral signature
> predict its next observation, and what makes that predictability
> transportable across environment, opponents and time?**

Three parts must be kept distinct:

- **Observed horse-ID signature (what we have):** a same-source,
  selected repeated timing pattern with partial later-date
  predictive information.
- **Behavioral mechanism (what we do not have):** whether the
  horse responds differently to changing ground or competitors,
  after individual traits, race and training factors are addressed.
- **Transferability (also not yet identified):** whether the
  same exact trait follows the **same horse** across source
  periods under comparable measurement conditions.

## Priority 0 — fix measurement denominators and actual-rider attribution

**Empirical blocker:** `GetHorsesForRace` supplies assigned
Jockey/Trainer fields and HORSES ID; the two specific
documented SOAP operations do not supply certified final
starter, confirmed rider alteration, DNF or each runner's
complete finish time.

**Needed before analysis:** original results/scratchings
and altered-rider sources (with reuse rights), original
horse-ID history and verified finished/started denominator,
GPS-positive **and GPS-missing** confirmed starters,
age and training/trainer history, original source response
digests. Make a one-row-per-confirmed-start table and
auditable missingness flow.

**Deliverable:** reproducible source-ID linkage and
truth table of actual starters, assignments and
measurement inclusion across locked meeting dates.
**Gate:** no role-based *causal* claim without validation
of actual rider/participant states.
Source constraints:
[SOAP fields audit](../ecology-rq-official-soap-vs-final-starters-jockey-data-scope.md),
[missing role study](../ecology-rq-source-role-missingness-vs-early-gps.md).

## Priority 1 — same animal × same measurement × multiple years

**Key result to design around:** the two Doomben
predictive evaluation sets (within-2025 23 horse IDs,
year-forward 2025→2026 26 horse IDs) contain
**0 overlapping animal IDs** even before requiring
their common 150 m first section and exact distance.
The independently computed outcome-blind requirement
of 2+ observed 2025 dates and >=1 observed 2026
date at the same marker and distance also yielded
**0** eligible horses.

**Next sampling design:** fixed source, real shared
HORSES IDs, same first GPS marker, same official
distance and preferably original Class, with repeated
observations in both years. Do not expand until
a result becomes positive. Split earlier and later
observations by date, preserve missingness and
pre-register separate cohort-support and scoring rules.

**Decision:** Only after source availability supports
the SAME animal population across two horizons should
we compare its predictive errors across horizons.
Use horse- and date-clustered uncertainty;
distinguish overlap eligibility from
power/precision. Current 20-horse support
gates are pragmatic, **not a power calculation**.
[Zero-support report](../ecology-rq-doomben-matched-timescale-overlap-real-results.md).

## Priority 2 — H1: individual × ground reaction norms

**Central mechanism question:** Does the same horse's
absolute early-sectional pacing respond differently
to Good versus Soft/Heavy, holding measured first
marker/distance, race Class, jockey and individual
history as comparably as possible?

**Current original data:** 37 repeat source IDs
cross Good vs wet, but only 17 same marker
+ distance, only two also matching source Class,
and **zero strata with >=2 Good and >=2 wet
observations** for a repeated slope.

**Design:** at least two matched repeated exposures
in each ground state per horse/marker/distance/Class
where feasible; prefer additional continuous original
TrackRating and moisture/rain measurements, controlled
race/day components, changing-age/training history
and observational entry-selection modeling.
Primary model includes horse-specific ground slopes
only **after checking support and identifiability**.
Perform negative controls that preserve race-level
context and vary only labels/exposure history.

**Current verdict:** **HOLD; no real H1 random slopes
have been estimated.**
[Expanded H1 audit](../ecology-rq-real-h1-multigoing-expanded-audit.md).

## Priority 3 — H2: opponent response, not peer-mean arithmetic

**Central mechanism question:** Does changing competitor
composition/ability causally or predictively affect
the focal horse's **absolute** pacing/finish behavior?

**Current design risk:** subtracting the peers'
average GPS interval creates an apparent competitor
effect algebraically even if the focal's absolute
speed never changes. Changing rival composition
and field selection require genuine prior, not
postrace, rival descriptions.

**Minimum usable empirical data:** actual starters
and original runner IDs for each race, pre-race
rival histories, verified absolute individual
section/finish times, DNF and missing timing states,
ground and role covariates. Fit within-horse,
date-aware comparison and explicit noncompletion
submodel. Use *pre-race* rival predictors; avoid
incorporating the focal outcome into its own
competitive exposure.

**Current verdict:** **SIMULATION ONLY / EMPIRICAL HOLD**.
[H2 design on outcome selection](../ecology-h2-outcome-selection.md),
[absolute-speed synthetic falsification](../ecology-h2-absolute-stress-audit.md).

## Priority 4 — publications and independent replications

Before submission: external behavioral ecology literature check,
figure claim-to-source audit, source rights, CI and repeated
same-unit uncertainty, age/role validation, failure and
non-significant findings. Prioritize an *independent*
source or newly sampled same-source period, not a new
post-hoc split selected for a favorable trend.
Manuscript remains
[a draft](../ecology-racehorse-individuality-manuscript-v1.md).

Avoid claiming: genetically based personality, inherited
tempo, selection/adaptation, horse×ground/horse×competitor
causal effects, universal individual time decay,
or profitable wagering. Those are different estimands.

## Work queue (not yet executed)

| Priority | Concrete task | Gate/output |
| --- | --- | --- |
| P0 | Independently reconcile confirmed actual starters and rider changes | Valid first-party runner denominator and match logs |
| P1 | Search/lock source period with repeated *same horse* across years | >=20 **shared** exact marker/distance individuals before scores (heuristic gate) |
| P2 | Build fixed class/going per-horse exposure census | Count of repeated cross-going strata and measured missingness, then power/design audit |
| P3 | Validate pre-race rival exposures and complete outcome selection | Only then fit real opponent models |
| P4 | Update English manuscript claims and replication ledger without moving source versions | Traceable evidence-to-figure links and transparent limitations |

**Do not infer successful execution from items in this queue.**
