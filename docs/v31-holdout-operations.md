# v3.1 prospective holdout operations

The v3.1 holdout is Kyoto-only and contains 20 eligible races.

Freeze manifest: `docs/v31-holdout-freeze.json`  
Ledger: `docs/v31-holdout-ledger.json`

The first eligible Kyoto race frozen after the manifest's `created_at_jst` is holdout #1.

## Directory convention

For holdout index `NNN`:

```
holdout/v31/NNN/
  race-input.json
  odds.json
  freeze.json
  result.json
  score.json
```

`freeze.json` is immutable after post time. Results are always written to the separate `result.json` and `score.json`.

## race-input.json

Required top-level fields:

```json
{
  "race_id": "YYYY-MM-DD-KYOTO-RR",
  "date": "YYYY-MM-DD",
  "venue": "京都",
  "race_number": 7,
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

The observation timestamp must be before post time and no later than the freeze timestamp. Horse numbers must exactly match the race input.

## Pre-result freeze

```bash
python -B scripts/v31_holdout.py freeze \
  --race-input holdout/v31/001/race-input.json \
  --odds holdout/v31/001/odds.json \
  --quality-map data/2026-10-12/v3-quality-tier-map.json \
  --manifest docs/v31-holdout-freeze.json \
  --classifier scripts/v31_candidate_channels.py \
  --observed-at-jst YYYY-MM-DDTHH:MM:SS+09:00 \
  --output holdout/v31/001/freeze.json
```

The wrapper refuses to freeze when:

- venue is not Kyoto;
- post time has already arrived;
- target-result fields are present;
- horse sets differ between history and odds;
- classifier Git blob SHA differs from the manifest;
- wrapper Git blob SHA differs from the manifest;
- an existing baseline quality tier has changed.

New quality-tier names may be appended only from an official source. Unknown tiers block Q1 for that race rather than being guessed.

## Post-result scoring

Store only the observed top three in the minimal result file:

```json
{
  "race_id": "YYYY-MM-DD-KYOTO-RR",
  "top3": [10, 12, 9]
}
```

Then:

```bash
python -B scripts/v31_holdout.py score \
  --freeze holdout/v31/001/freeze.json \
  --result holdout/v31/001/result.json \
  --output holdout/v31/001/score.json
```

This calculates union and M-only top-three recall, winner recall, misses and non-M rescues without changing the pre-result freeze.

## Register in the 20-race ledger

```bash
python -B scripts/v31_holdout.py register \
  --ledger docs/v31-holdout-ledger.json \
  --freeze holdout/v31/001/freeze.json \
  --score holdout/v31/001/score.json \
  --output /tmp/v31-holdout-ledger.json
```

Review the generated ledger, then replace `docs/v31-holdout-ledger.json` in a separate commit.

The register command rejects duplicate race IDs, chronological backfilling and entries beyond the 20-race target.

## No tuning during holdout

Do not modify M/C1/U/Q1/K1 thresholds or the class-aware rescue rule during the 20 eligible races.

A logic change creates v3.2 and starts a new holdout window. Misses are retained as residuals; they are not reasons to rewrite v3.1.
