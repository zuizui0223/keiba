# Next phase: a private, reusable multi-race WIN/WIDE → physical horse → bettor → next-price shadow pipeline

**2026-10-25 | nested Draft after [PR #21](https://github.com/zuizui0223/keiba/pull/21).**

**Important:** The original three-point Kyoto 8R on 2026-10-12 is already a known historical market. This module replays it strictly as an **engineering test**. It does **not** create an authentic pre-2026-10-12 SHA commitment. On current main neither \`.github/workflows/odds-shadow-attest.yml\` nor its \`odds_sha_only_receipt.py\` receiver is installed: both are in unmerged Draft branches. Therefore future private shadow forecasts may be hashed LOCALLY with this script, but **cannot yet be called GitHub-server-presealed**. Do not present source publication/receipt clocks or personal local timestamps as independent proof.

## One scientifically coherent project, not isolated bets/model variants

The directed path carried forward from Draft PR #9–#21 is

\[
\text{historical horse state}
\longrightarrow \text{horse ABM (common nonlocal }K,c,D\text{ with PDE)}
\longrightarrow \text{as-of information signal}
\longrightarrow \text{PR19 informed voters and cumulative pool}
\longrightarrow q^{\mathrm{synthetic}}(t)
\longrightarrow \text{coherent market/rank event probabilities}.
\]

In parallel the **same source WIN/WIDE price panel** provides a fixed, simpler autoregressive market benchmark. The first saved WIN quote and next WIN quote are relative prices, **not calibrated winning probabilities or observed vote shares**. True horse GPS coefficients, JRA vote count/ticket amount, bookmaker stake turnover, horse ability and bettor social influence are still not fitted. The factorized 1D position PDE is a toy closure; not a real observed horse-group density.

The NEW pipeline adds an actual repeatable experiment protocol rather than another one-off analysis.

## Required phases and data firewall

### 1. Source capture (PRIVATE, rights reviewed)

Keep all source files under \`private/\`, now gitignored. The first private JSON input must use \`KEIBA_PRIVATE_TWO_WIN_ONE_FULL_WIDE_FEATURE_V1\` and **contain no next-price target or official race result**.

It includes:
- fixed race ID, scheduled local post, actual distance in metres, one named quote provider, self-declared local research rights review;
- externally predetermined horizon in minutes 5–90 (e.g. 15 or 18) and tolerance 0–15 min (e.g. 5), fixed before the future quote arrives;
- \`model_coefficient_lock_at_jst\` at/before first displayed quote update and a local freeze creation time;
- two complete WIN quote snapshots (each distinct provider publication/update time AND local reception time, full horse-number→decimal-payout-odds map);
- a complete middle WIDE quote grid, \(\binom{n}{2}\) pairs, from the **same displayed update minute** as middle WIN (separate source pages and separate receipt clocks; not claimed atomic transaction times);
- optional separately transmitted, source-rights-reviewed **past-horse history bytes** + a SHA-matching independent history receipt. The existing \`keiba_independent_horse_asof_preflight.verify_offline_source\` checks each historical race precedes target, official horse names/IDs align and the history was self-reported received BEFORE the first WIN quote. If missing or received later, history-based physical predictions are omitted rather than reverse-engineered from later quotes. This receipt is still LOCAL and cannot authenticate its own timestamp.

For instance, the structural shape (short excerpt with omitted horses/pairs; *not a runnable full-field source*) is:

\`\`\`json
{
  "schema": "KEIBA_PRIVATE_TWO_WIN_ONE_FULL_WIDE_FEATURE_V1",
  "provenance": "authorized_private_local_export",
  "operator_confirmed_research_rights": true,
  "race_id": "FUTURE_RACE_ID",
  "scheduled_post_jst": "2026-11-01T15:00:00+09:00",
  "race_distance_m": 2000,
  "provider": "YOUR_AUTHORIZED_SINGLE_QUOTE_PROVIDER",
  "model_coefficient_lock_at_jst": "2026-11-01T09:00:00+09:00",
  "local_forecast_created_at_jst": "2026-11-01T13:06:00+09:00",
  "horizon_minutes": 15,
  "target_window_minutes": 5,
  "first_win": {
    "market": "win", "provider": "YOUR_AUTHORIZED_SINGLE_QUOTE_PROVIDER",
    "source_clock_verified": true,
    "source_updated_at_jst": "2026-11-01T12:00:00+09:00",
    "received_at_jst": "2026-11-01T12:01:00+09:00",
    "odds_by_horse_number": {"1": 4.2, "2": 8.8}
  },
  "middle_win": {
    "market": "win", "provider": "YOUR_AUTHORIZED_SINGLE_QUOTE_PROVIDER",
    "source_clock_verified": true,
    "source_updated_at_jst": "2026-11-01T13:05:00+09:00",
    "received_at_jst": "2026-11-01T13:05:30+09:00",
    "odds_by_horse_number": {"1": 3.9, "2": 9.0}
  },
  "middle_wide": {
    "market": "wide", "provider": "YOUR_AUTHORIZED_SINGLE_QUOTE_PROVIDER",
    "source_clock_verified": true,
    "source_updated_at_jst": "2026-11-01T13:05:00+09:00",
    "received_at_jst": "2026-11-01T13:05:40+09:00",
    "pairs": [{"selection": [1, 2], "odds_low": 3.1, "odds_high": 3.8}]
  }
}
\`\`\`

The example deliberately lists only two horses and one pair for readability. A real file must supply EVERY current runner (5–30) and every valid WIDE pair; otherwise the script rejects it. The declared times **cannot** verify themselves.

### 2. Frozen candidate calculation (NO LATER WIN QUOTE OPENED)

\`\`\`sh
python -m pip install 'numpy>=1.26,<3'

python scripts/keiba_private_multirace_winwide_shadow.py freeze \
  --source private/your_authorized_earlier_win_and_middle_wide.json \
  --output private/next_market_freeze.json \
  --horse-draws 120 --seed 20261025
\`\`\`

With a separate eligible horse history, also provide \`--history-source private/horse_history.json --history-receipt private/history_receipt.json\`.

The freeze uses **exactly the existing PR17 ahead-neighbour horse first-passage ABM**, the **PR19 smooth-staged bettor ABM** and the **PR21 same-WIDE-node signal tilt** (fixed beta 0.25) with common comparison seeds. It produces:

- **3 market-only price baselines:** (1) latest WIN qmid carried forward, (2) time-scaled previous log support momentum, (3) momentum plus same-source-minute WIDE node beta 0.25;
- **9 physical qmid→voter alternatives:** one PR17 physical horse signal under crowd c=2, with (A) no WIDE, (B) aligned WIDE node, (C) cyclically wrong-horse WIDE placebo, crossed with PR18 information release at voting round 1/3/never (5);
- if historical past-horse input is externally eligible by the *declared* local source clocks, another **9 analogous horse-history alternatives**, with independently sourced physical initial information and the same voter market qmid.

Hence a complete freeze contains **12 or 21** candidate price-index distributions, all indexed by official horse number, summing to one. There is no winner payout, false independence assumption for overlapping WIDE pairs, or direct momentum-to-real-physical-speed inference. The candidate count may not be changed after the freeze by selecting the best scorer.

All candidates and metadata are stored in a canonical JSON payload, with a SHA-256 digest in \`seal_sha256_of_canonical_payload\`. The returned \`SHA_only_existing_dispatch_inputs_NOT_SENT\` contains exactly race ID, digest, scheduled post and last input reception. **It has NOT been submitted to GitHub.** It is safe to share only after the receiver is properly deployed on the default branch and only if user/source rights permit the metadata. Never push private quotes, individual horse histories or the full private forecast to a public GitHub PR.

The feature contract rejects: extra fields (including accidental current winner or later odds); 5-or-fewer/incomplete horse numbers; nonpositive payout odds; incomplete/duplicated WIDE pairs; cross-provider WIN/WIDE; a different WIDE displayed source update minute; source clock time-travel; forecast generation after the selected next-quote minimum; any target time too close to post; optional history with incorrect name/ID or receipt after first WIN.

### 3. Holdout target capture is a SEPARATE private file

The SECOND local JSON file has schema \`KEIBA_PRIVATE_LATER_WIN_RECEIPT_STREAM_V1\` and is read ONLY when scoring. It contains a chronologically ordered *capture stream* of full WIN quotes, each with provider update and local receipt. It must be from the same race, provider and complete field. The script selects the FIRST **declared** complete full-field WIN update in the source-time window

\[
[t_{\mathrm{mid\ WIN\ update}} + H,\quad t_{\mathrm{mid\ WIN\ update}}+H+W]
\]

where \(H\) and \(W\) were frozen in advance, and every received quote must still be before post minus ten minutes. If there is **no quote** in this locked interval, the race is explicitly \`HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW\`. You must not substitute the next convenient later quote or a new horizon after seeing it.

\`\`\`sh
python scripts/keiba_private_multirace_winwide_shadow.py score \
  --freeze private/next_market_freeze.json \
  --target-series private/independently_saved_later_win_stream.json \
  --output private/next_market_score.json
\`\`\`

The scored target is *only the future displayed WIN **price-index shape***. Predeclared primary is full-field TV distance (percentage points), secondary full-field KL divergence. These are not calibrated horse-win log losses, and they do not measure ticket returns or true vote shares. A locally complete capture stream is self-declared: **the code cannot prove no eligible quote was omitted**. The result always retains \`external_preseal_authenticated=false\`, \`capture_stream_independently_complete=false\`, \`not_a_prospective_scored_forecast=true\`.

### 4. Aggregate ALL private race-level reports; no model selection on one winner

\`\`\`sh
python scripts/keiba_private_multirace_winwide_shadow.py cohort \
  --scores private/race1_score.json private/race2_score.json \
  --output private/multirace_aggregate.json
\`\`\`

The model compares paired TV/KL errors and includes both **equal-real-race** and **equal-meeting-date** mean differences from the untouched \`mid_WIN_persistence\` baseline, with identical race IDs and post-time labels. It refuses duplicate scored target identities. Missing/unavailable predeclared windows remain explicit HOLDs, never selectively dropped from the submitted file count. The earlier draft \`60 independent races across >=8 dates\` remains only a **development cohort guard**, *not* proof of adequate power or of prospective authentication. Even if it passes, this pipeline's local reports alone can NEVER be promoted to externally verified results.

An independently server-dated GitHub **default-branch** SHA receiver is still necessary for future genuinely pre-committed evidence. The existing \`odds-shadow-attest.yml\` and \`odds_sha_only_receipt.py\` are **currently missing from main** (Draft branch only). Installing them would require a separate reviewed merge and user authorization; this PR DOES NOT merge to main or promise real automated captures. Even a server timestamp proves only a SHA existed before a race, not that all WIN/WIDE sources were actually public or complete or that an authorized market dataset is scientifically valid.

## One real historical integration test, not one new predictive success

The new [R8 source replay](../../scripts/keiba_private_forward_r8_replay.py) feeds **12:21 full WIN**, **13:26 full WIN + all 55 WIDE**, then freezes 12 models **without opening** the hash-locked 13:44 source file. Only then does it open 13:44 full WIN, with its separately locked provider reception time, and compare price-index predictions. Its \`local_forecast_created_at\` is an **explicitly fictional reconstruction clock** (13:28) inserted solely for an old-replay software test; this new software did NOT exist before that date.

| Later real 13:44 quote-index TV distance | Source-locked new generic pipeline |
|---|---:|
| qmid persistence | 9.656363 pp |
| qmid WIN momentum | 8.180965 pp |
| qmid momentum + WIDE node beta .25 | **7.104114 pp** |
| PR17 qmid horse signal → PR19 smooth informed voter, release round 1 | 11.265058 pp |
| Same linked physical social model + correctly assigned WIDE node | 10.790058 pp |

These match the earlier R8 one-off PR #21 computations and show both implementation compatibility AND continued negative evidence for an uncalibrated physical market upgrade. Neither source identity nor real-life bettor simulation coefficients were learned from the result.

\`\`\`sh
python -m unittest discover -s tests \
  -p 'test_keiba_private_multirace_winwide_shadow.py' -v

python scripts/keiba_private_forward_r8_replay.py \
  --horse-draws 120 \
  --output tmp/private-multirace-r8-engineering-replay.json
\`\`\`

The dedicated CI publishes only **aggregate replay scores**, not raw licensed WIN/WIDE rows, private freezes or futures. See [CI](https://github.com/zuizui0223/keiba/actions/runs/40197181305) (first new-code execution).

**Scientific HOLD:** until independent genuine before-target source receipt/server commitments and authorized next-market full-field snapshots are collected across multiple new dates, the project cannot claim that WIDE information, horse social movement, a betting-market phase transition or a "best bet" is independently forecastable.
