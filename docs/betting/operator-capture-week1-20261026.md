# First authorized source ingestion: 2026-10-31 / 2026-11-01 week-1 readiness

**2026-10-26 · Nested Draft on PR #24. Not a new race outcome or realized next-market observation.**

PR #17–#21 now form a directed causal-model **hypothesis**: horse positional interaction → horse winner-signal sensitivity → bettor information release time → cumulative synthetic WIN price → coherent rank-derived WIDE/trio outcomes. PR #22 freezes exactly those fixed candidate models before an intended next full-field WIN quote, PR #23 allows independent GitHub comment timestamp verification of a SHA, and PR #24 locks two distinct source denominators: 26 graded races/20 dates and 64 proposed auxiliary R05–R12 slots/8 dates.

The most pressing blockage was still that **no actual newly upcoming authorized WIN/WIDE snapshot enters this pipeline automatically**, and users could not record two full-field source updates without writing a bespoke JSON file manually. This branch creates a private operator-driven normalization and chained provenance stream, and an official **preliminary** racing programme checklist for the first 16 proposed race numbers. No licensed dataset, external provider credential, or bookmaker API is bundled.

## Observed JRA preliminary programme, not confirmed racecards

Official programme: https://jra.jp/keiba/calendar2026/2026/10/1031.html (Kyoto, 10/31) and https://jra.jp/keiba/calendar2026/2026/11/1101.html (Tokyo, 11/1). JRA cautions that runner entries, race conditions, post times, racing order and cancellations can change and the actual cards should be checked when published, generally Thursday around 16:00. Those webpages are an official **schedule, not an actual WIN/WIDE feed or final card**.

| 2026 JST | Venue | Proposed R05–R12 local post times from published programme |
| --- | --- | --- |
| Saturday 10/31 | Kyoto | 12:25, 12:55, 13:25, 14:00, 14:35, 15:10, 15:45, 16:25 |
| Sunday 11/1 | Tokyo | 12:20, 12:50, 13:20, 13:50, 14:25, 15:00, 15:40, 16:25 |

The 10/31 Kyoto R11 is the KBS Fantasy Stakes (GⅢ, planned turf 1400m, 15:45); the 11/1 Tokyo R11 is the Tenno Sho Autumn (GⅠ, planned turf 2000m, 15:40). **These two races also exist in the original 26-grade registry**; they must not become 2× independent real observations merely because their provisional race numbers appear in the 64-slot auxiliary registry.

The new \`scripts/keiba_week1_licensed_capture_plan.py\` derives for each of these sixteen planned slots **attempted operator visits** at 100 minutes before post and 65 minutes before post. For example:
- Fantasy Stakes: try first complete WIN at 14:05 and try second WIN + complete WIDE at 14:40;
- Tenno Sho Autumn: try first complete WIN at 14:00 and second WIN + complete WIDE at 14:35.

These are **observation attempts only**. The provider may not publish a source update at the planned moment. A correctly frozen future target is always [actual source update minute of the middle WIN] + **15 to 20 minutes**, with no substitution after a missing full quote. Only quotes obtained before the target begin can influence the horse ABM→bettor ABM; information from later cannot be injected into an earlier simulated voter round.

Reproduce the public provisional operator timetable, containing **no private odds**:

    python scripts/keiba_week1_licensed_capture_plan.py \
      --as-of 2026-10-26T01:14:00+09:00 \
      --output tmp/week1-capture-planned-only.json

This plan does NOT run in the background, schedule fetches, access a provider, record a final starter list, or certify any actual JRA post time.

## How to ingest rights-authorized normalized market data, locally only

Only the operator who actually has lawful access to an authorized export can save original WIN and WIDE source snapshots. Do not scrape unapproved bookmaker/JRA data or publicly commit raw odds. This code never connects to JRA websites; \`source_url\` is recorded as provenance only. It also never places bets.

For each complete source, prepare a **PRIVATE** input with the exact fixed fields below. Example values are synthetic and do NOT refer to real Fantasy Stakes runners:

\`\`\`json
{
  "schema": "KEIBA_OPERATOR_AUTHORIZED_SNAPSHOT_V1",
  "race_id": "SOME_CONFIRMED_OFFICIAL_RACE_ID",
  "provider": "YOUR_AUTHORIZED_SOURCE",
  "market": "win",
  "source_updated_at_jst": "2026-10-31T14:05:00+09:00",
  "source_url": "https://your-authorized-provider.example/full-win",
  "source_clock_declared_verified": true,
  "rights_reviewed_by_operator": true,
  "provenance": "authorized_private_local_export",
  "odds_by_horse_number": {"1": 4.5, "2": 6.8, "3": 10.1, "4": 13.2, "5": 18.4}
}
\`\`\`

This example with five horses is illustrative only. The actual final horse-number set must be the **complete confirmed** official card, not a speculative nomination list. All odds must be finite, >1.0, without duplicate or noncanonical horse IDs. A WIDE input uses the same common metadata with \`market="wide"\` and a \`pairs\` list instead of \`odds_by_horse_number\`, each row containing the unordered integer \`selection: [i,j]\` and finite \`1<odds_low<=odds_high\`. **All** \(n(n-1)/2\) pairs are mandatory (55 for 11 horses). WIDE providers may carry separate publication/update clocks; the match is by the recorded source update **minute** only and is **not proof of simultaneous final stake settlement**.

Record a source as soon as it is obtained (the CLI generates the actual local machine time rather than accepting a retrospective time argument):

    python scripts/keiba_operator_winwide_capture.py append \
      --raw-source private/this_source_WIN_or_WIDE.json \
      --private-ledger private/captures/THIS_RACE_ID

Each append creates a *new* numbered private JSON event file, with SHA-256 over its content and SHA-256 of the preceding event; the software refuses duplicate publication timestamps for the same source/market and checks timestamp monotonicity. Files use exclusive-create mode, not overwrite. The audit detects ordinary post-capture content edits or chain gaps. **A local hash chain is NOT tamper-proof against rewriting the whole directory, unobserved deletions, manipulated computer time, or external changes at the source.** PR #23's GitHub receipt remains essential.

## A confirmed-card gate BEFORE actual horse and voter modeling

After JRA publishes the final official runner list, create a separate private card receipt with schema \`KEIBA_OPERATOR_OFFICIAL_FINAL_CARD_RECEIPT_V1\`, exact original registered slot ID, the final **source-based** official race ID, source/provider, official horse numbers, scheduled post and distance, final-card publication/receipt timestamps and an authorized source URL. \`declared_final_entrant_list\` must be true, but remains an **operator claim** rather than an independent proof of official JRA identity. It must match the fixed 26-grade slot or fixed 64 auxiliary slot; the original 菊花賞 slot is never eligible for this next-quote research.

Once the first complete WIN and first *later*, source-update-aligned WIN+WIDE pair-grid have both been recorded, freeze the fixed model immediately:

    python scripts/keiba_operator_winwide_capture.py freeze \
      --private-ledger private/captures/THIS_RACE_ID \
      --confirmed-card private/THIS_RACE_ID_final_card.json \
      --private-output private/THIS_RACE_ID_frozen.json \
      --horse-draws 120 --seed 20261026

This calls the **unchanged PR #17 horse first-passage dynamics**, PR #19 smooth/delayed voter model, PR #21 WIDE-node tilt, and PR #22 source-locked 12-candidate next-price forecast. Its fixed coefficients, race horizon (+15-minute lower bound and +20-minute upper bound), and unmodified market-only competitors are all present in the frozen SHA. Missing WIN, missing one WIDE pair, different horse IDs, cross-provider clocks, late source arrival, a freeze after the first target update, or any extra winner/return fields cause an immediate HOLD.

The CLI can only write under a gitignored \`private/\` directory and refuses overwriting an existing freeze. The data source rights assertion remains local. An optional independent past-horse profile can be added only through PR #22's separate rights-reviewed history receipt gate — **not** by pretending current market prices or postrace normalization are past biological ability observations.

The **additional manual next step**, before the next quote arrives, is preparing the SHA-only manifest via PR #23 and making the deliberate user-authorized **GitHub PR #22 comment**. This capture tool does **not** post comments or remote SHA commitments automatically.

## Later market scoring must remain separate

Continue appending subsequent full WIN source updates. Once the predeclared future quote update has been received, and **only if the operator has saved a locally complete actual capture stream**, use:

    python scripts/keiba_operator_winwide_capture.py score \
      --private-ledger private/captures/THIS_RACE_ID \
      --private-freeze private/THIS_RACE_ID_frozen.json \
      --private-output private/THIS_RACE_ID_score.json \
      --operator-confirms-complete-capture

The result preserves \`external_preseal_authenticated=false\` and \`capture_stream_independently_complete=false\`, regardless of the number of saved snapshots. GitHub SHA verification is separately handled by PR #23, and the 26/64 cohort denominators and missing slots by PR #24. The output is a full-field **next-quote price-index** TV/KL, **not** winner-probability log loss, true tote vote share, participant copying, an estimated herd coefficient, a market phase transition or positive bet expected return. No official podium enters this routine.

## Actual CI outcome, not simulated market evidence

[Dedicated Actions test](https://github.com/zuizui0223/keiba/actions/runs/40211721126) passed a strictly synthetic 6-horse mock feed:

- 10:00 first full-field WIN, 11:00 second full-field WIN and complete 15-pair WIDE, 11:03 mock local SHA freeze, later 11:17 full WIN target;
- output 12 coherent frozen PR22 next-market model candidates, then a separate local-only TV/KL market score;
- invalid extra winner/payout fields, incomplete WIDE pair grids, duplicate publication times, mixed providers, after-target freeze, altered local SHA-chain files, non-final card, and post-hoc selection of a different source minute are rejected;
- tentative first two upcoming meeting dates produce **16 proposed slots**, 2 pre-existing grade overlaps, **0 actually collected future odds**, 0 remote SHA commitments and 0 verified new market outcomes.

The numerical model is still **uncalibrated** for real horse GPS movement and actual bettors. The point of this new module is to make it possible for the *next* lawful real data capture to enter an experimentally controlled, externally pre-target SHA protocol. Do not upgrade a successful synthetic CLI run to genuine data collection or future betting skill.
