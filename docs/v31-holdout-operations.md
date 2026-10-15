# v3.1 prospective holdout operations

The v3.1 holdout is Kyoto-only and contains 20 eligible races.

Freeze manifest: `docs/v31-holdout-freeze.json`  
Ledger: `docs/v31-holdout-ledger.json`

The first eligible Kyoto race frozen after the manifest's `created_at_jst` is holdout #1. Every subsequent eligible Kyoto race is attempted in chronological order until 20 scored races are accumulated; a single race day may contribute multiple holdout entries.

## Directory convention

For holdout index `NNN`:

```
holdout/v31/NNN/
  race-input.json
  odds.json
  source-capture-meta.json
  freeze.json
  result-capture.json
  result.json
  score.json
```

`freeze.json` is immutable after post time. Results are always written to the separate `result.json` and `score.json`.

## Build race-input and odds from one captured JRA snapshot

Use `scripts/v31_prepare_snapshot.py` to turn one saved JRA card page plus the active runners' JRA profile pages into deterministic inputs.

The capture JSON has this shape:

```json
{
  "race": {
    "race_id": "YYYY-MM-DD-KYOTO-RR",
    "date": "YYYY-MM-DD",
    "venue": "京都",
    "race_number": 7,
    "age_scope": "3yo+",
    "scheduled_start_jst": "YYYY-MM-DDTHH:MM:SS+09:00",
    "target": {"surface": "ダ", "distance_m": 1800, "class_rank": 1}
  },
  "card": {
    "url": "official JRA race-card URL",
    "text": "captured UTF-8 page text"
  },
  "profiles": {
    "1": {"url": "official JRA horse URL", "text": "captured UTF-8 profile text"}
  }
}
```

Then:

```bash
python -B scripts/v31_prepare_snapshot.py \
  --capture holdout/v31/001/capture.json \
  --observed-at-jst YYYY-MM-DDTHH:MM:SS+09:00 \
  --output-dir holdout/v31/001
```

It writes `race-input.json`, `odds.json`, and `source-capture-meta.json`. Profile rows dated on or after the target date are removed automatically, so a profile fetched after results later exist cannot leak the target result into historical features. Cancelled/excluded horses are removed from the active runner set. The card-text and profile-text SHA-256 values are recorded in the metadata.

## race-input.json

Required top-level fields:

```json
{
  "race_id": "YYYY-MM-DD-KYOTO-RR",
  "date": "YYYY-MM-DD",
  "venue": "京都",
  "race_number": 7,
  "age_scope": "3yo+",
  "scheduled_start_jst": "YYYY-MM-DDTHH:MM:SS+09:00",
  "target": {
    "surface": "芝 or ダ",
    "distance_m": 1800,
    "class_rank": 1
  },
  "horses": []
}
```

Each horse uses the normalized pre-race schema accepted by `scripts/v31_candidate_channels.py`: age, career-start count, last-four starts and full history before the target race.

Target-race result fields such as `top3`, `winner`, `results` or `payouts` are forbidden.

## odds.json

```json
{
  "observed_at_jst": "YYYY-MM-DDTHH:MM:SS+09:00",
  "horses": [
    {"number": 1, "win_odds": 4.2}
  ]
}
```

The odds observation timestamp and the freeze timestamp must both be **15 to 25 minutes before the scheduled post time, inclusive**. The odds observation must not be later than the freeze timestamp. Horse numbers must exactly match the race input.

Do not reuse an earlier morning/noon snapshot for a later race, and do not substitute a later/final market if the fixed window was missed.

## Pre-result freeze

```bash
python -B scripts/v31_holdout.py freeze \
  --race-input holdout/v31/001/race-input.json \
  --odds holdout/v31/001/odds.json \
  --source-meta holdout/v31/001/source-capture-meta.json \
  --quality-map data/2026-10-12/v3-quality-tier-map.json \
  --manifest docs/v31-holdout-freeze.json \
  --classifier scripts/v31_candidate_channels.py \
  --observed-at-jst YYYY-MM-DDTHH:MM:SS+09:00 \
  --output holdout/v31/001/freeze.json
```

The wrapper refuses to freeze when:

- venue is not Kyoto;
- the race is maiden/newcomer class, obstacle/non-flat, or 2-year-old-only;
- post time has already arrived;
- the odds observation or freeze timestamp is outside the fixed 15-25 minute pre-post window;
- target-result fields are present;
- horse sets differ between history and odds;
- classifier Git blob SHA differs from the manifest;
- wrapper Git blob SHA differs from the manifest;
- source metadata does not report the frozen snapshot-preparer Git blob SHA;
- source metadata race ID, observation time, or active horse-number set does not match the generated inputs;
- an existing baseline quality tier has changed.

New quality-tier names may be appended only from an official source. Unknown tiers block Q1 for that race rather than being guessed.

## Record every eligible attempt

Before moving to the next eligible race, append exactly one event to `docs/v31-holdout-attempt-ledger.json`.

Valid freeze example:

```json
{
  "race_id": "YYYY-MM-DD-KYOTO-RR",
  "scheduled_start_jst": "YYYY-MM-DDTHH:MM:SS+09:00",
  "status": "FROZEN",
  "freeze_sha256": "<sha256 of freeze.json>"
}
```

Pre-result data failure example:

```json
{
  "race_id": "YYYY-MM-DD-KYOTO-RR",
  "scheduled_start_jst": "YYYY-MM-DDTHH:MM:SS+09:00",
  "status": "PRE_RESULT_DATA_FAILURE",
  "failure_reason": "missing_profile"
}
```

Register with:

```bash
python -B scripts/v31_attempt_ledger.py register \
  --ledger docs/v31-holdout-attempt-ledger.json \
  --event /tmp/v31-attempt-event.json \
  --output /tmp/v31-holdout-attempt-ledger.json
```

Review then replace the repository attempt ledger in a separate commit. Duplicate race IDs and chronological backfills are rejected.

## Post-result source capture and scoring

Do not type the top three manually.

Capture the official JRA result page text into `result-capture.json`:

```json
{
  "race_id": "YYYY-MM-DD-KYOTO-RR",
  "source_url": "https://www.jra.go.jp/JRADB/accessS.html?...",
  "observed_at_jst": "YYYY-MM-DDTHH:MM:SS+09:00",
  "text": "captured UTF-8 official JRA result page"
}
```

Generate the deterministic result file:

```bash
python -B scripts/v31_prepare_result.py \
  --capture holdout/v31/001/result-capture.json \
  --output holdout/v31/001/result.json
```

The result preparer rejects non-JRA result URLs, page date/race-number mismatches and incomplete or duplicate top-three rows. `result.json` stores the parsed top three plus the JRA URL, observation time and SHA-256 of the captured source text.

Then score:

```bash
python -B scripts/v31_holdout.py score \
  --freeze holdout/v31/001/freeze.json \
  --result holdout/v31/001/result.json \
  --output holdout/v31/001/score.json
```

Scoring calculates union and M-only top-three recall, winner recall, misses and non-M rescues without changing the pre-result freeze.

## Independent post-result reconciliation (required)

Before adding a scored race to the official score ledger, re-parse the raw official JRA capture and independently recompute the score arithmetic:

```bash
python -B scripts/v31_validate_postrace.py \
  --freeze holdout/v31/001/freeze.json \
  --result holdout/v31/001/result.json \
  --result-capture holdout/v31/001/result-capture.json \
  --score holdout/v31/001/score.json \
  --attempt-ledger docs/v31-holdout-attempt-ledger.json
```

The validator must print `"valid": true` and exit with status 0. It re-parses the JRA capture, requires it to reproduce `result.json` exactly, verifies result timing/source hashes, and checks freeze/result/attempt hashes plus membership and rescue arithmetic. Do not register a score if reconciliation fails.

A declared freeze timestamp alone does not independently prove that the prediction was made on time. Verify that the GitHub commit containing the freeze was published before the actual race start. If that cannot be independently established, record a data-integrity failure rather than backdating the freeze.

## Register in the 20-race ledger

```bash
python -B scripts/v31_holdout.py register \
  --ledger docs/v31-holdout-ledger.json \
  --freeze holdout/v31/001/freeze.json \
  --result holdout/v31/001/result.json \
  --result-capture holdout/v31/001/result-capture.json \
  --score holdout/v31/001/score.json \
  --attempt-ledger docs/v31-holdout-attempt-ledger.json \
  --output /tmp/v31-holdout-ledger.json
```

Review the generated ledger, then replace `docs/v31-holdout-ledger.json` in a separate commit.

The register command invokes the independent validator itself. It refuses registration if the raw JRA capture, deterministic result, immutable freeze, formal score or matching FROZEN attempt disagree.

The register command rejects duplicate race IDs, chronological backfilling and entries beyond the 20-race target.

## Formal evaluation after race 20

After exactly 20 scored eligible races, run:

```bash
python -B scripts/v31_evaluate_holdout.py \
  --ledger docs/v31-holdout-ledger.json \
  --attempt-ledger docs/v31-holdout-attempt-ledger.json \
  --contract docs/v31-holdout-decision-contract.json
```

The evaluator performs the preregistered one-sided exact stratified random-addition rescue test. It also checks the overall candidate-fraction ceiling.

Formal `PROMOTE` requires all three:

- exact one-sided p <= 0.05;
- overall candidate fraction <= 0.65;
- freeze success rate >= 0.80 through the 20th scored FROZEN race.

Before 20 scored races the evaluator returns `INCOMPLETE`; interim statistics cannot trigger promotion or threshold changes.

## No tuning during holdout

Do not modify M/C1/U/Q1/K1 thresholds or the class-aware rescue rule during the 20 eligible races.

A logic change creates v3.2 and starts a new holdout window. Misses are retained as residuals; they are not reasons to rewrite v3.1.
