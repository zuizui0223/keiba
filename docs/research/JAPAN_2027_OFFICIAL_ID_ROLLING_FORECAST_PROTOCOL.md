# 2027 official-ID rolling family forecast: future-time validation protocol

**Design frozen 2026-11-17 JST, before any 2027 race. STATUS: HOLD_NO_LICENSED_OFFICIAL_PANEL.** This is a prospective *design*, not a claim that future data have been collected, or that access or redistribution permission exists.

## Motivation

The 2022–24 older-horse samples showed a small added predictive value of direct-sire/dam shared other-horse histories. However, a third-source 2026 check over 232 previously active horses and 480 starts did **not** robustly replicate that gain, and no fitted model beat a fixed 0.5 midpoint. Those 2026 forecasts relied entirely on old source-A histories through 2021, a 4+ year-old feature snapshot. Retuning to inspected 2026 results must **not** be called a fresh independent holdout.

## Future cohort and primary comparison

- **Target**: JRA flat-race starts dated 2027-01-01 through 2027-06-30 JST if a license-compliant, timestamped, stable-ID feed becomes available. This is a proposed data collection window, not a published race schedule.
- **Separate replication**: NAR only if its independently licensed stable horse identifiers and race outcomes are available and securely joined; no numeric ID equivalence across JRA/NAR.
- Freeze training and tuning on authorized outcomes and information-known timestamps strictly before 2027-01-01. For each target race, predictors use only records published **before that race's chosen prediction cutoff**, with history updated per race.
- Compare **M0** constant normalized-rank midpoint 0.5, **M1** pre-race own-horse form + age, sex, rest time, course, surface/distance, jockey/trainer, and **M2** the same M1 features + pre-race histories from *other* horses sharing sire or dam.
- **Primary metric**: equal-focal-horse-weighted normalized rank RMSE, on complete untied classified finishers with ranks 1..N. All models scored on identical rows. Record partial/cancelled/DNF results separately; do not silently impute finishing ranks.
- **Operational claim gate**: M2 must beat both M1 and M0, with positive family increment across the intended future period, and results reported by month, birth cohort, age and known-parent coverage. Horse and racing-day clustering reported as separate sensitivity intervals. Inference about heritability or betting profits remains out of scope.
- Negative tests fixed before evaluating 2027: at least 99 matched parent-pair permutations within birth cohort, circuit and parent-ID completeness if feasible, plus source-identity and lookahead tests. Recompute real and sham models on identical source-certified rows. A negative result stays negative.

## Authorized private table contract

### Entrant snapshots (one row per eligible horse/race, before start)
Required fields:
    race_id,horse_id,race_start_at_jst,entry_known_at_jst,course_id,surface,distance_m,sex,age,jockey_id,trainer_id

- Horse stable identifier is a typed official *blood registration* ID (e.g. H:XXXX), not name, prefix, owner, stable or event-hashed label.
- entry_known_at_jst must precede race_start_at_jst; any later edit to weather/going, weight, rider, class or venue is excluded until its own known-on timestamp permits it.
- Same race ID must have one date, surface, course, distance and start time; duplicate race+horse IDs are rejected.
- Source A/B/C name-event matching cannot substitute for this official identity source.

### Final result snapshots
Required fields:
    race_id,horse_id,race_start_at_jst,result_known_at_jst,finish_rank,classified_field_size,finish_status

- Only integer 1..N classified ranks are eligible for the primary response; other finish statuses are retained for coverage/selection diagnostics.
- result_known_at_jst must be >= race_start_at_jst. No prior result is a valid predictor for a later horse entry unless its publication time is **strictly before entry_known_at_jst**.
- Do not use 2027 labels, payouts, final odds or other hindsight fields to select model hyperparameters or horse identity.

### Private pedigree master (typed parent IDs)
Required fields:
    horse_id,sire_id,dam_id,pedigree_master_known_at_jst

- The file is created from authorized registry exports. JRA's *blood registration number* and *breeding registration number* are **different namespaces**; the existing ecology_jravan_blood_breeding_id_bridge.py explicitly maps them and preserves unresolved breeding references as B:XXXX rather than inventing same-namespace links.
- An unverified missing parent is UNKNOWN, not a shared phantom parent or a genetically unrelated founder.
- Disallow a parent record first known after the target race's entry cutoff, duplicate inconsistent parents, cycles or name-based merges.
- Exact pedigree A for authorized registered horses can be computed by the existing ecology_japan_registry_pedigree.py; matching genomic G requires consented identity-linked DNA data, not anonymous samples.

### Immutable provenance
A private source manifest records:
    source_provider,source_version_sha256,record_family,valid_from_jst,received_at_jst,reproduction_permission

JRA-VAN's RACE/RCOV master and per-horse race records can provide official stable IDs when used under an appropriate Data Lab contract. NAR requires separate source approval. No provider license is assumed to authorize publication of raw records.

## Fail-closed tests before scoring

1. All inputs used for a forecast have information-known timestamps earlier than that entrant's cutoff.
2. Original official horse IDs and typed pedigree-parent IDs agree across the joined master and race panels; name or same-prefix guesses are prohibited.
3. One horse's prior races cannot be counted as both its own-history feature and a same-family other-horse feature.
4. Class, course, age, jockey and trainer are valid only when source-certified at the pre-race cutoff.
5. Partial outcomes, nonfinishers, duplicate horse/race combinations and incomplete/full rank denominator conflicts are rejected or separately marked.
6. An actual 2027 prediction evaluation is only called independent after model coefficients, target period, thresholds and control scheme are frozen **before** viewing its results.

## Status

**Implemented previously**: private pedigree A recurrence and typed JRA blood/breeding ID bridge; source-separated 2022–24 and the negative 2026 archive test.

**Not yet obtained**: licensed time-stamped official 2027 entrants, outcomes, blood ID-to-parent master, full Japanese JRA+NAR registration coverage, source-certified 2027 prediction panels. They must remain HOLD until actually acquired and verified. Store only aggregate QA and prediction scores publicly; do not upload licensed horse-level information to GitHub.
