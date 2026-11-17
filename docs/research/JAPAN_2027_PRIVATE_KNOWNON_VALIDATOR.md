# 2027 JRA official-ID pre-race known-on preflight — code and current status

**2026-11-17: implemented and synthetic-tested only. No licensed JRA-VAN/NAR live feed or 2027 observations have been obtained.** See design freeze [2027 official-ID protocol](JAPAN_2027_OFFICIAL_ID_ROLLING_FORECAST_PROTOCOL.md).

## New preflight validator

The private local CSV reader [ecology_japan_2027_official_knownon_preflight.py](../../scripts/ecology_japan_2027_official_knownon_preflight.py) accepts three explicitly supplied *authorized* private exports:

1. Entrant snapshots: race ID, horse ID, start and entry-known times, course, surface, distance, sex, age, jockey/trainer IDs.
2. Parent master: typed blood-ID horse, typed sire/dam IDs and pedigree-master known time.
3. Historical published results: prior race and horse, start and result-known time, classified rank, field size and finish status.

It checks the 2027-01-01 to 2027-06-30 target, one typed H: official blood-ID horse per race, explicit JST +09:00, entries before race starts, parent rows published before cutoff, distinct H: vs B: parent namespaces and historical result-known timestamps **strictly earlier** than target entry cutoff. It excludes same-time or later information, prevents missing-parent pseudo-families and excludes the focal horse from sibling/relative means. The code cannot authenticate JRA publication timing or provider permissions.

**Only aggregate output**: readiness counts, pretarget own/relative history support, counts of excluded delayed results and status HOLD_ACTUAL_2027_OFFICIAL_RESULTS_AND_FROZEN_MODEL. No names, IDs, source rows or predictions in outputs. This does not train a model or produce 2027 scores.

## Test coverage

The fictional-only [12 tests](../../tests/test_ecology_japan_2027_official_knownon_preflight.py) and [GitHub Actions workflow](../../.github/workflows/ecology-japan-2027-knownon-tests.yml) test delayed result exclusion, missing parents, typed ID namespaces, no name joins, post-cutoff pedigree appearance, self-parenting, duplicated runner/race, late entries, future-known outcomes, non-JST timestamps and preservation of the frozen 2027 target dates.

Passing them is necessary but insufficient for true licensed source completeness or a prospective genetic result.

## Authorized, PRIVATE use

Do not upload any raw JRA or NAR licensed records to GitHub. Run only on a local private computer with data-provider permission:

    python scripts/ecology_japan_2027_official_knownon_preflight.py \
      --entries /private/jra_2027_entered_horses.csv \
      --parents /private/authorized_parent_master.csv \
      --history /private/historical_result_known_on.csv \
      --out-aggregate /private/knownon_summary.json

Absent input is HOLD, not a null genetic effect. No automated online registry download exists in this repo. The JRA-vs-NAR and anonymous genomic-G ID joins still require independently approved source mappings.
