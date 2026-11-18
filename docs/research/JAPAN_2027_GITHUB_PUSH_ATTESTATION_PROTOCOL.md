# 2027 GitHub-server-time pre-race commitment: input and scientific gates

**Design frozen 2026-11-18 JST, before any 2027 results.** This is a SOFTWARE AND TESTS proposal, **not** a real pre-race commitment, not JRA publication-time certification and not legal permission to obtain/reproduce source records.

## Why this addition is necessary

PR #53 implemented two private local JRA-VAN SQLite snapshots and PR #51 froze each horse's pre-race forecasts. But their local timestamp fields are **self-reported by the capturing computer**, and the private horse-level prediction digest is not independently timestamped merely because it exists on local disk. To make an interpretable future test, a **public aggregate-only commit must demonstrably exist on GitHub's server before the first race starts**.

This work introduces an **atomic per-race public commitment bundle** tying the source snapshot receipt, the source-normalization SHA and the M0/M1/M2 forecast commitment together, then validates its checked-out Git SHA against GitHub Actions **server-side `created_at`**, not against the Git commit's user-editable author/committer timestamp. The external timestamp proves only that **the SHA-committed aggregate bundle existed on GitHub before the event**, conditional on verified GitHub API results. It does **not** prove that local snapshots/forecasts were actually collected at their claimed time without independent licensing/clock review and opening the committed digests against private inputs later.

## Per-race bundle contract

Input consists only of three manifest-like aggregate JSON files already created in private processing:

1. `pre_snapshot_receipt.json` from PR #53: `JRA_LOCAL_SQLITE_ASOF_RECEIPT_V1`, phase `pre_race`; includes `private_snapshot_sha256`, `capture_started_utc`, `capture_finished_utc`, `target_race_start_jst`, `local_clock_injected_for_synthetic_test`.
2. `pre_normalization_summary.json` from the pre-race adapter: `JRA_2027_PRIVATE_PRE_POST_SNAPSHOT_CSV_ADAPTER_V1`; includes `source_pre_receipt_SHA256`, `source_pre_private_snapshot_SHA256`, `private_normalized_CSV_SHA256.entries` and `.parents`, `first_observed_entry_known_at_jst`, `earliest_target_start_at_jst`, `declared_source_entrant_count`.
3. `private_forecast_public_commitment.json` from PR #51: `JRA_2027_H1_PREDICTION_COMMITMENT_V1`; includes `input_SHA256.entries/parents/history/model`, `private_prediction_file_SHA256`, `asof_at_jst`, `frozen_at_utc`, `earliest_target_start_at_jst`, `races`, `starts`, `unique_horses`.

The bundler hashes **the exact bytes** of each original JSON file and embeds a **whitelist of aggregate fields**. It neither reads nor outputs horse/race IDs, source tables, pedigree rows, individual predictions, odds, model coefficients or local sensitive filesystem paths. It refuses user-provided extra fields in the bundle that could leak such values. For this release, an atomic bundle covers **exactly one complete race**; require `races==1`, `starts==unique_horses==declared_source_entrant_count` and identical earliest start timestamps. Multiple races require multiple separate pre-race bundles, not one partial source receipt falsely covering a whole day.

**Chronology invariants (strict):** `source_capture_started <= source_capture_finished < (first_observed_entry_known_at = finished+1s) <= forecast_asof <= forecast_frozen <= GitHub_run_created_at < race_start`. If any source/adapter/forecast hash differs, or an individual source capture is marked synthetic for a purported live bundle, the real attestation must fail.

The source receipt's declared phase, local checksum flags, track code map digest, forecast model digest, and original source SHA are expected. An input that looks like a JSON race record instead of one of these bounded aggregate manifests is rejected. **No bundled public artifact is created automatically**, and no actual 2027 data currently exist.

## GitHub server attestation

A dedicated `push` workflow accepts only changed files under `docs/commitments/2027/*.json` (no pull_request, no manual retroactive rerun). It uses a fixed GitHub REST host and `GITHUB_RUN_ID`, `GITHUB_SHA`, `GITHUB_REPOSITORY`, `GITHUB_EVENT_NAME=push`. The validator reads the server-created workflow `created_at`, checks `head_sha==checked-out GITHUB_SHA`, repository and event `push`, then verifies the exact bundle bytes at that SHA, the chronology, source/forecast SHA links and the presence of no sensitive fields. The GH run created timestamp must predate the earliest declared source race start. **Never accept Git commit author date, `MakeDate`, local clock, a passed-in timestamp, or later `workflow_dispatch` as the external proof.**

The planned workflow handles **new files only**. Modified previously committed bundles are disallowed by checking Git's changed file status for the pushing commit; if the exact intended file was already present in earlier revisions, treat it as rewritten/invalid. Each bundle is intended to be immutable. A later race result must never enter the public pre-race bundle or change that commit. GitHub repository settings, branch protections and true source authorization still need separate external review.

## Post-race audit

Post-race, the original immutable Git bundle is retrieved **by its exact pre-race commit SHA**. The private source pre receipt, adapter summary and private forecast public commitment must recompute to the three frozen SHA256 values embedded in the bundle; the private forecast itself must match the committed `private_prediction_file_SHA256`. Only then are true later results scored with PR #51. This is separate from the GitHub event-time test and requires the user's private files; CI never loads them.

## Limitations and scientific status

- A successfully posted aggregate bundle would provide evidence of the time of **public GitHub commitment**, conditional on trusted GH server API and source file hash openings; it **does not independently prove JRA's per-record publication time**, licensing, or that the declared target time is accurate. A maliciously backdated race start in the manifest would still need official race schedule cross-validation from the authorized feed.
- Local SQLite backups are not immutable external data publication logs; their claimed capture timestamps are local observations. Backups and original provider record versions must remain available for external audit.
- The 2018–24 historical JRA source release history cannot be reconstructed by capturing a database today. Consequently the originally planned historical trainer still requires proper historical known-on inputs.
- Observing a M2 family-history prediction improvement in 2027 would not establish causal heredity, nationwide JRA+NAR pedigree A, matched genomic G or an odds-market wagering edge.
- CI synthetic tests use **only fictional future races and fake horse source IDs**. No real 2027 source data, predictions or model coefficients are committed by this change.
