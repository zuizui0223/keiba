# Pre-race authorized JRA-VAN SQLite snapshot receipt: capture and audit contract

**Fixed protocol 2026-11-18 JST, before any 2027 results.** The aim is to record what a permitted local client **possessed** by a known clock time, not reconstruct historical source publication from the JV-Data MakeDate field. This is an experimental acquisition/evidence workflow, **not** a JRA-VAN downloader, legally sufficient provenance proof, or a retrospective license.

## Why

PR #52 added official typed blood-ID and breeding-ID source readiness QA for the jrvltsql NL_RA/NL_SE/NL_UM/NL_SK/NL_HN tables, with no genuine authorized source data available. A static historical database cannot establish when a particular record was actually accessible to an analyst; its MakeDate is a record date, not verified event-specific publication or receipt time.

Capture **unaltered, read-only, consistency-preserving SQLite backups** before and after future racing events, with recorded local capture start/end timestamps, snapshot SHA256 and a public *aggregate-only* digest commitment. A pre-race snapshot and a public Git commit **before first start** are jointly necessary for externally auditable temporal availability, but the local machine clock, manifest and source user assertion by themselves are not trusted third-party attestations.

## Commands and permissible roles

- capture pre_race: require a specified race start in explicit JST +09:00 and a locally measured **finished** capture time strictly earlier than it. This proves only a backup completed before a declared start according to the local clock. It **does not** certify that the source's records are accurate, current, permitted for reuse, or available in real-time through a provider.
- capture post_race: require a start time strictly earlier than the locally observed capture beginning. A later result may still not yet have been officially published; count source updates, don't infer result status from timestamps alone.
- capture master: no target start time; suitable for tracking pedigree/registration master changes, not a race forecast.
- verify: independently recompute the private snapshot SHA and manifest linkage to detect corruption or changed source bytes.
- Optional previous private snapshot plus its prior public manifest: verify both prior digests, check chronological ordering, then count added / changed / removed rows for five explicit NL_* tables by their composite primary keys. For confidentiality, counts only; no individual row keys, horse IDs or names ever enter the public manifest.
- A deleted or changed record is an observed local snapshot revision, **not** automatically a source correction; racing-result revision must be investigated with provider metadata and rights.

## Input/output restrictions

- Input: an **already licensed, already populated local SQLite** database. The tool never downloads official horse files or opens a web browser.
- Private output: a consistent SQLite backup *outside the Git working tree*, file mode 0600; use an atomic temporary-file transition, never overwrite existing snapshots.
- Public output: JSON with observation window in UTC/JST, source/snapshot SHA256 and byte count, record counts / QA only, optional SHA-linked predecessor and row-change counts. The public manifest MUST NOT contain table rows, horse names/IDs, jockey, owner or odds.
- Historical 2018–2024 snapshots were not recorded at the time. You may capture the current database today, but doing so does not retroactively certify what was available to a real 2018 race forecaster.
- If a source can be updated during backup, a consistent SQLite online backup is necessary; if a concurrent update is detected by the same connection's data version, hold rather than claim a closed pre-race snapshot.
- No private source data or credentials in any public GitHub Actions workflow. CI uses tiny fictional SQLite files only.

## Consequence for actual M1/M2 forecasting

This capture ledger is **one prerequisite**, not yet an adapter from every NL_* raw record into the trainer. A future adapter must derive race-level entrant_known_at, result_known_at, and parent master known_at from a **verifiable first-captured snapshot** or authorized provider event-time log, with the correct changes/delays. Never set these to MakeDate, race day, or the time a retrospective database was downloaded. Use them only if the exact version of each required input was present in the corresponding pre-race snapshot and the snapshot was committed before that target start.

Predictions need complete entrants and an audited typed KettoNum / HansyokuNum bridge. NAR remains a different data source and identifier namespace. Without actual licensed per-race snapshots and independent timestamp attestation, 2027 result predictions, population kinship A, genomic G and genetic heritability remain HOLD.
