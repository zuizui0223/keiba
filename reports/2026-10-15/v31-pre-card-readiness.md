# v3.1 Kyoto holdout pre-card readiness — 2026-10-15

Status: **operational preflight only**. No prospective race has been frozen or scored yet.

## Frozen state

- Branch: `analysis/kyoto-20261012`
- Freeze manifest blob SHA: `af6e9bc7cda9f92efb65838a34999f0f97fcad52`
- Manifest seal time: 2026-10-15 12:47:15 JST
- Score ledger: 0 / 20
- Eligible-attempt ledger: 0 attempts
- Scientific/candidate rules unchanged by this readiness check.

The latest reseal only added audit provenance fields to future score-ledger entries: SHA-256 values for the deterministic result, raw official result capture, score and attempt ledger, plus the official result URL.

## Verification

Current head after reseal:

- PR #1 remains draft/open.
- Workflow `v3.1 holdout tests`: success.
- Focused holdout tests: 17 / 17 passed.
- Full repository suite: 152 / 152 passed.
- Frozen-contract verification step: success.

The real synthetic end-to-end pipeline test covers:

`official-style JRA pre-race capture -> frozen classifier -> pre-result freeze -> FROZEN attempt -> official JRA result capture -> deterministic result -> score -> mandatory post-race reconciliation -> score ledger -> incomplete formal evaluator`.

## Official 2026-10-17 Kyoto programme

JRA scheduled programme:
https://www.jra.go.jp/keiba/calendar2026/2026/10/1017.html

Under the frozen v3.1 eligibility rule, the scheduled candidates remain:

| Race | Scheduled post | Programme | Frozen eligibility |
|---|---:|---|---|
| R7 | 13:15 | 3yo+ 1-win, dirt 1800m | eligible |
| R8 | 13:45 | 3yo+ 2-win, dirt 1400m, fillies | eligible |
| R9 | 14:15 | Momiji S, 2yo open, turf 1400m | **excluded: 2yo-only** |
| R10 | 14:50 | Kiyotaki Tokubetsu, 3yo+ 2-win, turf 2200m | eligible |
| R11 | 15:30 | Tourmaline S, 3yo+ 3-win, dirt 1800m, fillies | eligible |
| R12 | 16:15 | 3yo+ 1-win, turf 1400m | eligible |

JRA explicitly notes that this programme is scheduled information and that the current race card is normally published around Thursday 16:00. Therefore none of the above is treated as final until the current JRA race cards are re-read.

## Automation readiness

- 2026-10-15 17:00 JST: one-time source-capture preparation.
- Every Thursday 17:30 JST: recurring Kyoto holdout planner while scored ledger <20.
- 2026-10-17: independent exact freeze tasks at 12:55, 13:25, 14:30, 15:10 and 15:55 for the scheduled eligible races.
- Post-race scoring and fail-safe audit are scheduled after the final eligible race.

Each race-day task must revalidate:

- current official JRA race identity/conditions;
- active runners after scratches/exclusions;
- JRA-only card/profile provenance;
- frozen snapshot-preparer/classifier/wrapper SHAs;
- frozen quality baseline;
- market observation and freeze timestamps inside the 15–25 minute window;
- exactly one chronological attempt-ledger record.

## Holdout start condition

No current race counts yet.

The holdout begins only when the first post-seal eligible Kyoto race receives a valid pre-result freeze and a matching `FROZEN` attempt before post time. An eligible race that cannot be frozen for a pre-result data/technical reason must instead enter the attempt ledger as `PRE_RESULT_DATA_FAILURE`.

No result-driven backfill or threshold change is allowed.

## Publication-stage check added on 2026-10-15

**Source:** JRA official race-card publication FAQ: https://jra.jp/faq/pop02/2_2.html

A Thursday release after 16:00 normally **does not have horse/frame numbers**; numbers are normally assigned after 10:00 Friday. Thus today's 17:00 task is limited to card/profiles/horse-ID caching as actually available, not number-keyed finalized inputs or live odds. A separate **Friday 2026-10-16 around 13:00 JST** check is now scheduled to reconcile official horse IDs and newly published horse numbers for the Saturday eligible races. Saturday race-day tasks retain their fixed 15–25-minute actual-odds window and must independently recheck scratches.

**Read-only integrity spot check (2026-10-15):** all 19 listed `frozen_blobs` and the baseline quality-tier-map blob were compared to the current GitHub branch: **20 of 20 exact Git blob SHA matches, 0 mismatches**. Manifest Git blob: `af6e9bc7cda9f92efb65838a34999f0f97fcad52`. This spot check does not replace running the full frozen verifier in the future execution environment.

**Ledger count remains 0/20**; no prospective freeze or scored result was created in this readiness step. No automatic wagering or paid browsing was performed.
