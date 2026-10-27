# Bringing genuine licensed WIN and WIDE snapshots into the linked horse–bettor model

**2026-10-28 — Draft PR #31, nested on PR #30. No genuine new future JRA observation has been collected in this repository.**

## New evidence about the data source

The [JRA-VAN listing of Jv Odds Visualizer](https://jra-van.jp/dlb/sft/lib/jv_odds_visualizer.html) and [author's manual](https://keiba.ryuzee.com/jv-odds-visualizer/manual/09-export.html) confirm that the program can monitor all eight bet types and save during-meeting snapshots including WIDE if the operator has a licensed Windows Data Lab/JV-Link setup. Its documented export format is UTF-8 with BOM/CRLF, a 17-field race information first line, blank second line, tab name third line and column headings fourth line, followed by table rows. The exporter can save CSV and Excel, and the selected tab/time matters.

**Critical limitation:** The manual confirms the envelope, NOT the exact wide popular-ranking column names of every version. This adapter supports an explicit pair-list contract and FAILS CLOSED on unknown headers, matrix tabs, unclear numbers, missing WIDE pairs or unknown time selections. An actual user-supplied rights-reviewed CSV is required to prove compatibility. Do not say that this PR directly connects to a Data Lab account.

## No hidden race results or invented as-of source times

The operator must have a genuine FINAL-card private JSON matching the existing KEIBA_OPERATOR_OFFICIAL_FINAL_CARD_RECEIPT_V1 contract, and must provide the exact JRA-VAN provider identity, HTTPS source provenance and selected source-update time with timezone offset. The first 17 CSV race header values are checked against the declared race number, date, venue, distance, planned post and runner count. The 16-digit exporter race code is retained as a vendor source identity, NOT assumed equal to the JRA official race ID.

The **単複 one-time table** must have 馬番 and 単勝 columns for every final-card horse. Column 着順 and 払戻 may appear but cannot contain any after-race value. The **ワイド pair-list tab** must contain ワイド in the tab name and a 組 column identifying each unordered pair. It must have either genuine low/high columns (such as 下限 and 上限) or a genuinely exported price RANGE field such as 3.4～4.1. The adapter does not invent a low/high value from an unknown single odds number. It requires exactly n(n−1)/2 distinct complete WIDE pairs; all other cases HOLD.

The private optional audit report records TWO distinct local checksums:
(1) SHA-256 of the original CSV bytes, including its actual BOM/CRLF;
(2) SHA-256 of the normalized capture-source object. These permit local
reprocessing audits when the operator retains the actual CSV. **The
original vendor CSV byte digest is NOT currently part of the downstream
PR22/PR30 publicly committed model SHA** (those source chains bind the
normalized captured market rows instead). This provenance limitation is
explicitly recorded rather than claiming end-to-end raw-source sealing.

A previous PR #31 iteration stored the original CSV SHA only in a separate audit report, outside the published prediction commitment. This child PR now binds that original-byte digest to the normalized captured quote **inside** the event head (and therefore the PR28/PR30 forecast SHA), with an explicit append-time exact reparse. The original CSV file is still only locally available and must be retained for a later raw-source audit; no live JRA-VAN license or actual real export has been verified.

The first-row CSV race header does **NOT** itself attest the selected odds observation minute. Therefore the explicit selected quote time provided to the adapter is only an operator declaration. After conversion, the pre-existing capture append action stamps its own local receipt clock. Neither of these is independent evidence of when market values were publicly available; for future validation publish the forecast SHA ONLY before the target next-WIN market window and verify the independent GitHub server timestamp. The source and future target capture completeness remain separate, unproved obligations.

## Local-private integration (no remote fetch, no wagers)

First, with licensed access, export a selected single-time WIN or WIDE table from Jv Odds Visualizer to the gitignored private/ directory. The following are placeholders, NOT verified future quote times or URLs. Convert a WIN one-time CSV by running:

    python scripts/keiba_jv_visualizer_export_adapter.py \
      --csv private/RAW_RACE_EARLY_単複.csv \
      --final-card private/REAL_CONFIRMED_RACE_final_card.json \
      --market win \
      --source-updated-at-jst 2026-10-31T14:05:00+09:00 \
      --provider MY_RIGHTS_REVIEWED_JRA_VAN_EXPORT \
      --source-url https://YOUR-LEGITIMATE-JRA-VAN-SOURCE.example \
      --private-output private/NORMALIZED_RACE_EARLY_WIN.json

Repeat with a later full WIN quote and its ACTUAL selected time. For the paired WIDE tab, after inspecting the real header and actual source clock, run:

    python scripts/keiba_jv_visualizer_export_adapter.py \
      --csv private/RAW_RACE_MIDDLE_WIDE.csv \
      --final-card private/REAL_CONFIRMED_RACE_final_card.json \
      --market wide \
      --source-updated-at-jst 2026-10-31T14:40:00+09:00 \
      --provider MY_RIGHTS_REVIEWED_JRA_VAN_EXPORT \
      --source-url https://YOUR-LEGITIMATE-JRA-VAN-SOURCE.example \
      --wide-range-col オッズ \
      --private-output private/NORMALIZED_RACE_MIDDLE_WIDE.json

If the real export has TWO numeric lower and upper fields, specify both the actual header names using --wide-low-col and --wide-high-col instead of a single range. A different update minute than the source's middle WIN update cannot be treated as atomic paired market information.

Append each *normalized* source to the previously implemented PRIVATE source chain:

    python scripts/keiba_operator_winwide_capture.py append \
      --raw-source private/NORMALIZED_RACE_EARLY_WIN.json \
      --original-vendor-csv private/RAW_RACE_EARLY_単複.csv \
      --confirmed-card private/REAL_CONFIRMED_RACE_final_card.json \
      --private-ledger private/captures/REAL_CONFIRMED_RACE_ID

**The original CSV and the already normalized source MUST be supplied together at append time.** The program recalculates the raw CSV byte SHA, re-parses the actual horse/pair quotes and checks the normalized source is exactly identical to the original file and confirmed final card. It refuses a fabricated CSV hash without the original bytes, changed odds under a valid hash, changed row mappings or mismatched final cards. The append clock is still only a LOCAL receipt clock.

The SHA of the original CSV bytes is included in the captured source object's typed `original_vendor_export` field; PR25's local capture-event hash chain includes that field; both the PR28 full-WIDE freeze and the PR30 WIN-only freeze commit that source-chain head within the full prediction SHA. **Thus the original CSV's byte digest is now transitively part of the public forecast commitment — the CSV file bytes themselves remain PRIVATE, and SHA does not prove the source clock or the source's truthfulness.**

This is when the operator's local **reception** time is stamped. Repeat for qmid WIN and WIDE only if both really exist. Then use the existing PR28/PR30 private model freeze and the two typed SHA comment verifiers.

- **Research lane A:** requires two complete WIN snapshots and all WIDE pairs from the same source update minute; forecasts 12 full-field market candidates with nonlocal horse ABM, crosspool horse-node information and staged bettor ABM. Unknown or missing WIDE remains explicitly missing.
- **Research lane B:** requires two complete WIN snapshots and no WIDE; forecasts six candidates with the same nonlocal horse ABM/PDE and staged bettors, and cannot fill missing A data.
- Both use the same registered 26 graded and separate 64 auxiliary candidate denominators. One physical race is one independent market interval, even if both lanes forecast and score the same future q2.

Do not use a postrace CSV with recorded 着順 or 払戻 as a pretarget market feature. The original q2 target must be captured **AFTER the model freeze** in its predeclared +15 to +20 minute source-update window, separately from the q0/qmid source generation.

## Validation and scientific status

New tests use an expressly synthetic six-horse / 15-WIDE-pair Jv Odds Visualizer CSV mimic, including the documented 17-column race metadata, BOM and CRLF. They cover full-field horse identity, source race header, one-time WIN tab, complete WIDE pair list, vendor display range parsing, postrace winner/payoff leakage, no future source time, ambiguous price column and actual preexisting linked horse–bettor freeze functions. **These unit tests do not establish the actual column format of a genuine vendor export; actual sample data must be inspected before calling the converter production-ready.**

No Data Lab/JV-Link license, automated JRA scraper, public odds source, independently authenticated live data, genuine new prospective q2 scoring, GPS horse physical calibration, proven vote count, real information cascade or positive betting expectation has been obtained in this task. Original Kikuka M0–M2 preseal, formal v3.1 and main remain unchanged. This PR is Draft until a rights-reviewed real CSV can be checked.
