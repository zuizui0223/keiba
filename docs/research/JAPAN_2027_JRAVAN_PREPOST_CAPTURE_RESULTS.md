# Private JRA-VAN pre/post SQLite capture → M0/M1/M2 forecast evidence

**As of 2026-11-18: SOURCE SOFTWARE READY, ALL TESTS FICTIONAL. STATUS HOLD_NO_LICENSED_JRA_LIVE_PRE_RACE_CAPTURE.** No user-licensed source DB has been obtained in this work. No real 2027 registered horse prediction or 2027 outcome has been scored.

## New chain

1. The source owner uses authorized JRA-VAN acquisition through their own permitted local importer (for example, a compatible jrvltsql SQLite database). **This repository never downloads JRA/JBIS horse records**.
2. Before a future JRA race, run [the private SQLite receipt capture](../../scripts/ecology_japan_jravan_asof_snapshot.py) in pre_race mode. It makes a SQLite online backup, verifies schema/completeness, records a local observed start/end time, and writes a public **aggregate-only receipt** with private backup SHA256. It rejects a copy completed at or after the declared start.
3. The [two-snapshot ID adapter](../../scripts/ecology_japan_jravan_snapshot_adapter.py) reads that fixed private backup, and **only if the source has all declared entrants** produces *private* entrant and parent CSVs in the [PR #51 model freeze](JAPAN_2027_POINT_IN_TIME_LEDGER.md) schema. H: blood IDs and B: breeding IDs remain separate. No result rank is allowed to have appeared in a claimed pre-race snapshot.
4. Use the PR #51 forecast freeze with a **genuinely trained and previously frozen** M1/M2 model, with an actual clock time before the race. It stores horse-specific M0/M1/M2 forecasts privately and emits a separate race-aggregate prediction-file SHA commitment. Publish/commit only aggregate receipt and aggregate forecast commitment **before the first race**, with externally verifiable Git commit timestamps. Neither source data nor private individual predictions go into public GitHub.
5. After the race, capture an immutable second SQLite backup in post_race mode **chained by the prior receipt SHA**. A pre/post adapter checks exactly the same race, entrants, rider/trainer, distance, track and race start, plus unique final ranks 1..N, before producing *private* result CSVs.
6. The existing PR #51 scorer matches the unchanged horse-level private forecast and final result CSVs by typed official ID and race key, verifies SHA commitment, and reports aggregate M0/M1/M2 race-rank RMSE. Small samples remain HOLD.

No source of **current real** JRA-NAR official records, trained model or odds is included. The chain can only be deployed after suitable authorized source data and signed/verifiable receipt-time provenance exist.

## Observed time versus genuine source published time

The actual source importer fields `NL_RA.MakeDate`, `NL_SE.MakeDate`, and `NL_SK.MakeDate` are date-only. They are **not** certified provider-time histories. This adapter conservatively defines local source-first-observed timestamps as the snapshot **finished** time plus one second, rather than inventing historical release times. It deliberately labels this as locally witnessed, not official JRA publication.

Important consequences:

- A pre-race source backup can support the narrow claim “these exact input bytes were held locally when the backup finished” **only if** its pre-race external timestamp and file integrity are later audited.
- A post-race complete-rank backup can support a later result-observed bound, **not** the date/hour when the JRA first published those results. Source corrections are versioned by the capture chain and cannot be silently backfilled into earlier snapshots.
- Even a perfect 2026–27 capture chain **cannot reconstruct which historic 2018–24 data revisions were available before those races**. Therefore the historical trainer [PR #52](JAPAN_2027_OFFICIAL_HISTORY_FIT_RESULTS.md) remains HOLD until a qualified historically timestamped source is obtained, or the study's historical scope is revised and prospectively fixed.
- A typed blood ID matched to a breeding ID is not an additive genetic effect, and a shared parent-history forecast may reflect stable/trainer/owner environment.
- A SHA256 file or local timestamp alone **cannot** prove the race had not begun. A pre-race independent public commitment and source clock/provenance audit are necessary.

## Actual CLI contract — private paths, examples only

All paths under /private are illustrative. Do not assume files already exist or that a JRA-VAN license permits copying raw tables.

The example source race uses six stable JRA fields (year, monthday, course JyoCD, Kaiji, Nichiji, RaceNum). It is a **fictional key and time**, not an actual scheduled race.

~~~bash
# Capture a permitted source state BEFORE the forecast race.
python scripts/ecology_japan_jravan_asof_snapshot.py capture \
  --authorized-local-db /private/source/jra_authorized.sqlite \
  --private-snapshot-out /private/captures/pre_001.sqlite \
  --public-receipt-out /private/captures/pre_001.aggregate.json \
  --phase pre_race --race-start-jst 2027-01-09T15:15:00+09:00

# Explicit source-approved source-track-code map: NEVER infer code meaning.
# This JSON lives only in the private input directory.
# /private/track_surface_approved.json (example: "11" maps to "turf")

python scripts/ecology_japan_jravan_snapshot_adapter.py pre \
  --pre-snapshot /private/captures/pre_001.sqlite \
  --pre-receipt /private/captures/pre_001.aggregate.json \
  --track-surface-map /private/track_surface_approved.json \
  --source-race-key 2027,109,05,1,1,1 \
  --private-entries-out /private/normalized/race_entries.csv \
  --private-parents-out /private/normalized/race_parents.csv \
  --public-summary-out /private/normalized/pre_source_qa.json

# In a separate step, use those private CSVs plus an authorized known-on
# historical results panel and a previously frozen genuine model to invoke
# the PR #51 'freeze' command, then timestamp its aggregate SHA in public Git
# BEFORE the first race. NEVER publish horse-level forecast output.

# After the scheduled start, capture a *separate* source state.
python scripts/ecology_japan_jravan_asof_snapshot.py capture \
  --authorized-local-db /private/source/jra_authorized.sqlite \
  --private-snapshot-out /private/captures/post_001.sqlite \
  --public-receipt-out /private/captures/post_001.aggregate.json \
  --phase post_race --race-start-jst 2027-01-09T15:15:00+09:00 \
  --previous-private-snapshot /private/captures/pre_001.sqlite \
  --previous-receipt /private/captures/pre_001.aggregate.json

python scripts/ecology_japan_jravan_snapshot_adapter.py post \
  --pre-snapshot /private/captures/pre_001.sqlite \
  --pre-receipt /private/captures/pre_001.aggregate.json \
  --post-snapshot /private/captures/post_001.sqlite \
  --post-receipt /private/captures/post_001.aggregate.json \
  --track-surface-map /private/track_surface_approved.json \
  --source-race-key 2027,109,05,1,1,1 \
  --private-results-out /private/normalized/race_final_results.csv \
  --public-summary-out /private/normalized/post_source_qa.json
~~~

No source-specific subscription token is sent to this repository. No provider API connection is created by either script. Local private snapshots and normalized private exports are created with 0600 file permissions and refused inside the checked-out Git tree. Snapshot names and source race IDs are never included in the aggregate public QA contents.

## Synthetic QA evidence

- [Private consistent SQLite capture and source revision chain CI](https://github.com/zuizui0223/keiba/actions/runs/44244453014): 22 capture/receipt tests + 9 independent SQLite-source-schema tests. Source bytes, exact race/parent join, source-change detection, three successive receipts, SHA tamper detection, pre/post time cutoffs and refusal to publish raw horse records are tested with **fictional** data.
- [Pre/post adapter to the real 2027 freeze/scorer SOFTWARE CI](https://github.com/zuizui0223/keiba/actions/runs/44245790368): 18 direct adapter tests + 22 capture/receipt tests. The new end-to-end software test feeds **three imaginary horses** through an artificial pre-race SQLite capture, typed M0/M1/M2 private forecast freeze, later post-race result capture, and separate scorer; its tiny score is correctly HOLD for insufficient support. No live JRA outcome or empirical forecast effectiveness is inferred.

**Distinct test families:** 22 snapshot/receipt + 9 underlying source schema + 18 pre/post adapter = **49 synthetic test cases** across the successful workflows, with snapshot tests run in both. These are NOT 49 registered horses or 49 real race starts. [Provenance and guardrails](../evidence/japan-2027-jravan-snapshot-chain-synthetic-qa-20261118.json).

## Research status

The actual 2022–24 historical tiny family-history improvement, the failure of the stale 2026 external-period model, and the 2026 post-hoc refreshed-own-history dominance remain unchanged. For a publishable new result, acquire the legal and independently timestamped JRA data and make genuine **out-of-sample** forecasts before 2027 races. An all-horse JRA+NAR pedigree A and individual-genome G analysis remain independent uncompleted projects.
