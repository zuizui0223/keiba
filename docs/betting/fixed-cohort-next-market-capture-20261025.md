# Fixed 26-race JRA next-market observation campaign — before any new source acquisition

**2026-10-25 / Draft after [PR #23](https://github.com/zuizui0223/keiba/pull/23).** This is a DATA COLLECTION DENOMINATOR, not a live odds feed or a betting forecast. It does not modify \`main\`, the previously sealed 菊花賞 M0/M1/M2, the original v3.1 20-race ledger or parent Draft PRs. The single known 2026 Kyoto8 next-quote test is a historical engineering replay and is not a newly prospective observation.

## What was already predeclared independently of this implementation

The repository already contains two immutable SHA-locked source files:

| File | Git blob SHA |
| --- | --- |
| \`data/research/jra-graded-flat-2026oct25-dec27-calendar.json\` | \`f458794971e184fb4cda5fdab84d1c56f277cc2f\` |
| \`data/research/odds-prequential-2026oct24-coverage-registry.json\` | \`9052dbb3590fd6a93bd6c6732d4e992929f77f0e\` |

The files enumerate exactly **26 JRA flat G1/G2/G3 races on 20 calendar dates**, from 2026-10-25 through 2026-12-27. Their recorded origin is a 2026-10-24 JRA calendar review, but the calendar file explicitly says it is **not an externally signed official calendar** and does not know all race IDs or post times.

The first slot (2026-10-25 京都 菊花賞) has a previous **separate outcome-prediction SHA** labeled \`preseal_sha_submitted_unverified\`. This is NOT an outcome score, is NOT a source-received WIN/WIDE price trajectory, and cannot count as a new next-market prediction. At 2026-10-25 22:04 JST, that first race is in the past. Exactly **25** races remain in the future, including:

- **2026-10-31 京都 ファンタジーS** — registered grade G3, official race ID and actual post time **missing** in the source-locked registry.
- **2026-11-01 東京 天皇賞（秋）** — registered grade G1, official race ID and actual post time **missing** in the source-locked registry.
- Remaining 23 future registered slots through 2026-12-27.

**No source-authorized new live WIN/WIDE acquisition, real next-price target, or server-verified next-market SHA is available in the repository. Current genuinely sealed new race count = 0.** Do not fill missing race IDs, post times or odds from guesses, from later results or from a neighboring race.

## A universal next-market trial, not cherry-picked races

The independent event is a **race / one predeclared next-market interval**, not an individual horse, a WIN pair, a WIDE pair, synthetic ABM trajectories or repetitions of the same target. Every one of the 26 fixed slots stays in the denominator; 25 are eligible for future observation, and the old Kikuka is carried as a **different previously submitted outcome-protocol** slot, never new next-market evidence.

Before the first future registered event, globally fix these NEXT-WIN price source-update target parameters:

| Fixed variable | Locked setting |
| --- | --- |
| Prediction origin | Second complete source-updated WIN quote, with first WIN quote and same-minute all-pair WIDE already captured |
| Relative target horizon | **+15 minutes after the middle WIN source-update clock** |
| Window | **Next 5 minutes** beyond +15, inclusive; select the FIRST complete source-updated WIN quote in this window |
| Missed quote target | **HOLD_TARGET_NOT_OBSERVED**; do not replace with a later convenient update |
| Minimum time to post | Original source and local market receipts, model freeze and target receipt must precede post by the original PR #22 safety buffer |
| Candidate model set | The **exact unchanged 12 or 21** PR #22 candidates; none can be dropped/replaced after their results are seen |
| Market benchmark | \`mid_WIN_persistence\`; compare separately with WIN momentum, WIN+WIDE and the PR17 physical→PR19 informed voter alternatives |
| Primary score | Full-field next **relative displayed WIN price-index TV distance**, percentage points |
| Secondary score | Full-field next price-index KL divergence |
| Source assumptions | authorized local export of complete WIN and WIDE from the same named provider/update minute, different source-received clocks explicitly preserved |
| Horse input | PR17 nonlocal crowding is hypothetical; independently authorized past-record input if locally source-clock eligible, otherwise market-derived physical prior only |
| Independent proof | Exact private model SHA and GitHub server-created comment **before next target window** using PR #23; until then LOCAL/HOLD |

**15+5 minutes is a design choice, not empirically fitted to price predictability.** It may cause eligible snapshots to be missing; those missingness patterns must be reported, not eliminated by retrospective horizon changes. The event's official post time must be source-verified separately before a local freeze is built; no such upcoming post time is supplied in the existing calendar. The user must access licensed market sources lawfully; this code is NOT a JRA-VAN or proprietary downloader.

## New fixed denominator executable

\`scripts/keiba_fixed_denominator_market_campaign.py\` checks both files against their actual **Git object content SHA** each time. If a future person edits one file, removes a race, adds a preferred race, changes the original Kikuka state, or quietly collapses a source date, the program rejects it.

Use without any licensed data:

    python scripts/keiba_fixed_denominator_market_campaign.py \
      --as-of '2026-10-25T22:04:00+09:00' \
      --output tmp/registered-market-capture-readiness.json

The result returns 26 registered rows/20 dates, 25 future slots, 25 entries missing verified official IDs/posts, zero local scores and zero externally proven next-market forecasts. It publishes only **public event-name/date and gate status**, not horse IDs, private quote data, target price series or forecasts.

### Later: private per-slot capture metadata (safe locally, NOT third-party proof)

When legitimately acquired in an authorized local source environment, the operator MAY add a private metadata JSON under gitignored \`private/\`:

    {
      "schema": "KEIBA_PRIVATE_FIXED_SLOTS_CAPTURE_METADATA_V1",
      "entries": [
        {
          "slot_id": "2026-10-31|京都|ファンタジーS",
          "official_race_id": "SOURCE_VERIFIED_REAL_ID",
          "scheduled_post_jst": "USE_SOURCE_VERIFIED_OFFSET_CLOCK",
          "racecard_source_url": "https://AUTHORIZED_SOURCE",
          "racecard_received_at_jst": "USE_ACTUAL_RECEIPT_OFFSET_CLOCK",
          "quote_provider_name": "AUTHORIZED_QUOTE_PROVIDER",
          "source_rights_checked_locally": true,
          "capture_stage": "metadata_only",
          "local_frozen_model_sha256": null,
          "target_horizon_minutes": 15,
          "target_window_minutes": 5
        }
      ]
    }

The strings labeled USE... and SOURCE_VERIFIED... above are **placeholders, not live-source facts**. They must be replaced with authentic permitted source records before the command is run. The program demands closed fields, full source-card metadata when any such field is supplied, HTTPS provenance, exactly matching original calendar date, nonduplicate race identities and true/false local source-rights review.

Allowed failure/attempt states (not success claims):
- \`metadata_only\`
- \`missing_full_WIN\`
- \`missing_full_WIDE\`
- \`WIN_WIDE_source_clock_mismatch\`
- \`local_SHA_frozen\`
- \`next_quote_window_missing\`
- \`next_quote_local_scored\`

The latter three require a declared local frozen SHA, complete card metadata and local rights review; they still do NOT prove real market data existed or was authorized. Claims of scoring are only counted from separately supplied PR #22 score files that match exact race ID, scheduled post, 64-character local digest and the original complete 12/21 model-name universe. Future-price receipt after the requested \`--as-of\` is **rejected**, and "missing target" may not be declared before the race is over.

To inspect those PRIVATE local artifacts:

    python scripts/keiba_fixed_denominator_market_campaign.py \
      --receipts private/capture_metadata.json \
      --scores private/race1_next_market_score.json private/race2_next_market_score.json \
      --output private/complete_centre_campaign_report.json

**This parser does not independently re-fetch official card data, private source receipts or GitHub timestamps.** Its output will NEVER automatically promote a claimed private status to authenticated prospective evidence, even if dozens of local scores exist. A SHA-only GitHub PR #22 comment proof remains a distinct PR #23 live verification step, and even that only verifies the SHA's server creation time, not actual data-source truth or complete quote capture.

The scoring metrics are *price-index matching*, not actual WIN/Top3/payout outcome scores. The physical HORSE and social BETTOR models remain connected through the prior PR17–PR22 pipeline; this registrar only prevents their evaluation universe from being selectively changed.

## Minimal statistical integrity requirements

- Report **all 26 registered slots** and separately the 25 candidate future next-market slots; do not silently treat the old Kikuka outcome-protocol commitment as a successful future WIN-price experiment.
- Count missing card/post, missing WIN, missing WIDE, unmatched provider/update minute, local-only SHA, missing exact target and locally scored event as **separate capture stages**. Do not classify unsupported server-proof strings in a local file as evidence.
- When multiple eligible local market scores exist, report both equal-real-race and equal-meeting-date paired differences in next WIN TV vs the persistence baseline. There are **20 total dates** in the predeclared 26-slot schedule but the remaining 25 races span 19 future dates; no assumption of independence for multiple same-day races, horse entrants or WIDE pairs.
- The older PR #10 recommendation of a **60-race / 8-date development gate cannot be achieved by this 26-event registry**. Even if 25 future quotes were independently collected, wider new registered cohorts would be needed for strong external validation and statistical power. The code explicitly reports this guard as false, not as implied forward skill.
- New future racing outcome/calibration, genuine JRA tote flow, market critical point, physical horse crowding parameters, bettor herding and positive expected return remain **HOLD**.

## Near-term operations

The next calendar slots are 10/31 ファンタジーS and 11/01 天皇賞（秋）, both without independently supplied local card/post times. A valid operator must first obtain an authorized full race card and original local clock receipt, then prepare the actual WIN/WIDE capture and SHA. There is **no user-authorized public source collector or auto-refresh task running here**. No future race has been captured, SHA-posted or scored by creating this Draft code.

Run unit tests or GitHub Actions without any external/licensed source:

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests \
      -p 'test_keiba_fixed_denominator_market_campaign.py' -v

**This work turns the old one-race replay into a fixed-denominator reproducible data-collection study design. It does not convert the archive into new prospective experiments.**
