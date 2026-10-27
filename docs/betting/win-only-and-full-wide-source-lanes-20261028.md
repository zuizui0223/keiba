# Two different evidence lanes for source-constrained JRA next-market forecasts

**2026-10-28. Experimental Draft, nested on PR #28.** The first proposed new meeting is Saturday 2026-10-31 Kyoto; none of these new races has yet been observed, externally sealed or scored. The owner has not provided a licensed JRA-VAN feed, JV-Link subscription, WIN/WIDE source snapshots, official future full-card capture or current odds.

## Why a two-lane design is necessary

JRA-VAN's official [Data Lab. detailed schedule](https://jra-van.jp/dlb/ddata.html) distinguishes live "速報オッズ" from periodically saved "時系列オッズ". The JRA-VAN [official FAQ](https://jra-van.jp/dlb/sdv/faq.html), [TARGET manual](https://targetfaq.jra-van.jp/faq/detail?category=47&id=667&site=SVKNEGBV) and [developer community response, 2026-06-16](https://developer.jra-van.jp/t/topic/872) indicate that the **historical time-series odds cover WIN/PLACE/BRACKET/QUINELLA, not WIDE**. In contrast, full WIDE quotations can be obtained from a contemporaneous all-bet-type **real-time quote feed**, with legitimate access. Those live snapshots must be actually captured at the relevant time; unavailable historic WIDE cannot be reconstructed by assigning the WIDE of the final market, carrying forward a different race's pair prices, or using an arbitrary asynchronous site as if atomic with the WIN quote.

The same JRA-VAN docs explain that time-series odds are typically recorded at **5–10 minute intervals** and are not an exact market transaction tape; near-live "速報オッズ" updates follow a provider-specific refresh schedule. Closing vote-count reports (when available) are **not** historical pre-target total stake volumes. Do not assume a WIN quote's inverse equals actual true WIN probability or bettor count. Historical temporal snapshots obtained after a race can help *backtesting*, but cannot certify that a particular new prediction was computed BEFORE its market target.

### Predeclared data-availability routes

| Research lane | Minimum legitimate source inputs available BEFORE next target | Frozen modelling and outcomes | Missing-data rule |
|---|---|---|---|
| **A (primary full WIN + WIDE)** | Full-field WIN q0, later complete WIN qmid, complete \(\binom{n}{2}\) same displayed update minute WIDE pairs, final original card, source rights, source-and-reception clocks | Original PR22–PR28 **12 candidate** nonlocal horse ABM→WIDE horse-node→staged bettor model vs price-index q2 | If any complete WIDE pair/quote is unavailable, A is **HOLD**; never fabricate or reduce pair count |
| **B (secondary WIN-only)** | Two chronologically distinct, full-field authorized WIN quotes, final card, source/reception clocks | New **6 candidate** quote-index models sharing the **same nonlocal horse ABM and staged smooth bettor ABM**, but *without any WIDE node* | B may proceed despite missing historical WIDE, but must remain separately labeled; no claim about WIDE information |

Both use the SAME original 26 graded-race and separate 64 numbered-auxiliary-slot candidate registries, the SAME source update +15..20-minute next WIN target window and the SAME physical race ID. A race eligible for both lanes is **ONE race**, not two independent race results. The B protocol is fixed on 2026-10-28 before the first scheduled 2026-10-31 meeting; **do not retrofit earlier known 2026-10-12 Kyoto R8 as a prospective validation**.

The original PR22 A protocol and all 26/64 denominator commitments are unchanged. B is a separately reported data-availability sensitivity; it must not be used as a hindsight substitute for whichever lane fits actual q2 better.

## B's exact pre-target model universe

The script \`scripts/keiba_win_only_shadow_lane.py\` consumes the existing PR25 PRIVATE event chain and verified final-card **local assertion**. It chooses the **first full-field WIN source update, then the first chronologically distinct later complete WIN**, including their original publication and local reception clocks. It does not select an advantageous pair based on later observed outcomes. A version of the complete local source-chain head SHA, original complete card SHA, model source-file SHA list, physical distance, original complete field, seed, draws and all six forecast vectors are hashed together using exactly the existing canonical PR22 SHA convention.

- **WIN_mid_persistence**: qmid as next quoted price index.
- **WIN_log_momentum**: project the previous relative log-WIN support change to the **fixed +15 minute** horizon.
- **WIN_horse_ABM_smooth_info_round1**, **...round3**, **...round5**: PR17 horse first passage with front-neighbour nonlocal \(c=2\) m²/s, synthetic diffusion, Gumbel ability proxy from **qmid only**, then PR19 fixed smooth-feedback synthetic bettor ABM, receiving the simulated horse signal at the first, third, or no voting round.
- **WIN_horse_ABM_shifted_signal_placebo_round1**: cyclically reassign those simulated horse WIN signals to other official horse IDs before the same bettor ABM. This negative control can expose mechanical label alignment but is not a real randomized horse experiment.

In the SAME pre-target freeze, the model also runs the corresponding
12-second fixed-drift, no-Gumbel **product-marginal nonlocal PDE** diagnostic
from PR #17 with exactly the same forward K, physical crowd coefficient
`c=2`, diffusion `D=0.25` and qmid input used in the horse SDE. It
checks that every species density retains mass 1, and records the maximum
CDF discrepancy against interacting particle replicas. The PDE output is
a **numeric factorized closure audit**, not a second prediction of the
horse's real first-passage rank; this distinction remains in the
original SHA-bound payload. Finite correlated horses, different Brownian
samples, and PDE grid error still contribute to its discrepancy.

Each forecast is a full-field positive normalized **quoted-price** index. No actual finish positions, target q2 prices, real vote counts, wager stake amounts or ROI influence any model input. Each candidate keeps its exact horse-ID ordering.

All forecast routes are **hypothetical** physical and voting mechanisms. The qmid-only horse ABM is NOT an independent measurement of form: its initial "ability" is derived from the same observed market. No additional past performance or GPS value has been smuggled into it. With no real independent horse measurements, the original WIN-only market momentum/persistence benchmarks remain essential.

## B execution (local private source export, no scraping)

The operator first uses PR25's approved capture workflow to record valid full-field WIN source snapshots, preserving original publisher clock and local reception event. A provider-rights-reviewed genuine final-card record is required to connect race IDs and horse numbers to a fixed calendar slot.

Before the target window begins (separately frozen at +15..20 minutes):

    python scripts/keiba_win_only_shadow_lane.py freeze \
      --ledger private/captures/CONFIRMED_RACE_ID \
      --final-card private/CONFIRMED_RACE_ID_final_card.json \
      --private-output private/CONFIRMED_RACE_ID_WIN_only_frozen.json \
      --horse-draws 120 --seed 20261028

The PRIVATE output contains the six predictions and a canonical SHA. It stores original full source-chain head, declared card hash and all model code content SHAs. A changed card/race distance, modified source chain or changed software version must be detected when scoring. **This code has NO external PR23 SHA-comment verification or auto-submission implemented**, and must never label a local freeze as an externally authenticated prospective prediction. Extending PR23's narrowly typed full WIN/WIDE GitHub comment proof to this NEW schema would require a separate deliberately tested protocol; do not manually post an incompatible SHA claiming it passed that verifier.

Only AFTER the future full-field WIN quote is captured independently:

    python scripts/keiba_win_only_shadow_lane.py score \
      --ledger private/captures/CONFIRMED_RACE_ID \
      --final-card private/CONFIRMED_RACE_ID_final_card.json \
      --private-freeze private/CONFIRMED_RACE_ID_WIN_only_frozen.json \
      --private-output private/CONFIRMED_RACE_ID_WIN_only_local_score.json \
      --operator-confirms-complete-capture

The target is the **first fully complete WIN quote whose original publication time** lies within qmid source updated at +15..20 minutes, received only after model freeze. If no eligible source update appears, the missing target remains a **HOLD** in the declared WIN-only experimental lane. Missing-WIDE slots must *also* remain missing in lane A regardless of lane B success. Source completeness is only locally asserted; the later quote score remains TV/KL between relative displayed price indices, not horse winner log loss.

## Distinct final-card dates for next weekend

JRA's [official FAQ](https://jra.jp/faq/pop02/2_2.html) specifies a **special release for 天皇賞（秋）**: its horse-number-and-frame-equipped final card is normally published **Thursday after 14:00 JST**, 2026-10-29 in this case. Do not wait for the ordinary Saturday-race cards and treat these as the same source availability timeline.

For regular Saturday graded races, the usual release pattern is Thursday after 16:00 **without** horse/frame numbers, followed by the numbered list on Friday after 10:00 (or approximately 09:00 where the special exception applies). The 2026-10-31 京都ファンタジーS's pre-numbered Thursday entries should not be treated as the final field. The official [race page](https://own.jra.jp/keiba/race/098/syutsuba.html) reports release planned for Thursday 10/29, but that statement alone does not prove the full numbered official runner roster was already final.

For both races, every entry/quote must still be source-clock checked. The [official Oct31 programme](https://jra.jp/keiba/calendar2026/2026/10/1031.html) tentatively lists Kyoto 11R 15:45, and the [official Nov1 programme](https://jra.jp/keiba/calendar2026/2026/11/1101.html) lists Tokyo 11R 15:40. Either can change or be cancelled. These programme times are *planning context*, not frozen sourced JRA post-times suitable to forge a final card.

## Required source and effect boundaries

- No licensed DataLab/JV-Link account, license agreement or provider data is assumed connected; do not automate access absent authorization.
- A historical WIN 5–10-min series is not a same-source-minute, complete WIDE quote.
- Real-time WIN/WIDE pages or feeds may not have atomic update clocks. Preserve each original publisher/receiver timestamp and require same displayed minute for A.
- Both A and B target local WIN quote errors at a future time, NOT actual race results. Only external appropriately source-attested future trials may support forward prediction claims.
- All JRA-VAN official vote totals/closing reports, if used later, need independent timestamp availability review to avoid future information entering qmid.
- Never combine A+B scores by counting the same physical race twice, prefer **paired within-race analysis** where both actually exist.
- Source SHA and model content hash protect integrity, not honesty of self-reported receipt time or data-rights status. True external GitHub SHA timestamp evidence for B remains **HOLD** under this version.
- A, B, all parent Drafts, original sealed 菊花賞 M0–M2, v3.1 official ledger and main are not merged/changed.

**At protocol creation, genuine newly collected JRA source snapshots = 0; future independently GitHub timestamped WIN-only lane = 0; future verified next-price observations = 0.**


## 2026-10-28: independent typed WIN-only GitHub SHA verification

A **separate** SHA-only GitHub PR-comment verifier is now implemented in
[keiba_win_only_github_receipt.py](../../scripts/keiba_win_only_github_receipt.py).
This is NOT PR #23's WIN+WIDE verifier: the secondary WIN-only schema has a
different marker, a different six-candidate source model, and a different
public comment anchor.

| Research lane | Public comment anchor | Comment marker | Preconditions |
| --- | --- | --- | --- |
| A: full WIN/WIDE | Existing [PR #22](https://github.com/zuizui0223/keiba/pull/22) | KEIBA_SHA_ONLY_NEXT_MARKET_PR_COMMENT_V1 | 12/21-model complete WIN/WIDE freeze |
| B: WIN-only | Existing [PR #30](https://github.com/zuizui0223/keiba/pull/30) | KEIBA_SECONDARY_WIN_ONLY_NEXT_QUOTE_SHA_V1 | The six-model WIN-only freeze, source-card and code SHA manifest |

For the WIN-only secondary experiment, once a *genuine authorized future*
private freeze exists, the local operator may prepare the single public
SHA-only text WITHOUT POSTING it:

    python scripts/keiba_win_only_github_receipt.py prepare \
      --private-freeze private/RACE_WIN_only_frozen.json \
      --private-output private/RACE_WIN_only_comment_not_posted.json

The prepared SHA-only body must be deliberately posted ONCE by the repository
owner to **PR #30 before the predeclared next WIN target window starts**.
No model source, full horse card, original odds, actual stake stream or horse
prediction distribution is contained in the public body. The code does not
make GitHub writes or bet placements.

With an authenticated GitHub CLI, the operator can later validate the
GitHub-server comment creation time directly from the full paginated PR #30
issue-comment list and an independent GET of the single comment:

    python scripts/keiba_win_only_github_receipt.py verify-live \
      --private-freeze private/RACE_WIN_only_frozen.json \
      --private-output private/RACE_WIN_only_GitHub_SHA_receipt.json

It refuses owner mismatch, wrong PR, malformed/multiple same-race claims,
different SHA, edited timestamps, source receipt later than posted SHA,
comment posting after the +15min target window starts, incomplete GitHub API
pages, or changed model-code fingerprints. Offline fixture inspection NEVER
counts as server proof. Comments can be deleted or edited within a
one-second timestamp resolution, so the current GitHub list is not a
fully append-only certificate.

To bind the remote SHA timestamp to a *locally* saved subsequent price score
without falsely authenticating its completeness:

    python scripts/keiba_win_only_github_receipt.py verify-live \
      --private-freeze private/RACE_WIN_only_frozen.json \
      --private-local-score private/RACE_WIN_only_local_score.json \
      --private-output private/RACE_WIN_only_SHA_proved_q2_capture_local.json

Even if the user's future GitHub SHA were externally timestamped, only
SHA pre-existence would be proven. Source ownership, original quote
publisher clocks, all capture completeness, real stake amounts, win
probability calibration, bettor imitation and betting ROI remain unproven.

**As of implementation**, PR #30 has no new real WIN-only SHA comment; the
GitHub API runs in unit tests are explicit mocks and never count as real
market evidence.

## Same physical race, two lanes: a paired next-WIN evaluation

[keiba_dual_market_lane_audit.py](../../scripts/keiba_dual_market_lane_audit.py)
reopens the source-chained PRIVATE A and B freezes, recomputes each local
q2 score from the recorded later full-field WIN quote, and refuses
within-race comparisons unless all of these match exactly:

- official source-derived race ID and frozen horse-number identity universe;
- first and middle source-published WIN quote times, and the locked
  +15..20-minute target window;
- the **selected actual target WIN publisher update AND local receipt**;
- persistence and log-WIN-momentum benchmark TV and KL values.

After these prerequisites, compare original A's
\`mid_WIN_momentum_plus_WIDE_node_beta025\` error to secondary B's
\`WIN_log_momentum\` error. This is a **paired one-target
WIDE-information contrast**, not two independent race observations.

Example for one authorized privately recorded race:

    python scripts/keiba_dual_market_lane_audit.py compare \
      --ledger private/captures/CONFIRMED_RACE_ID \
      --final-card private/CONFIRMED_RACE_ID_final_card.json \
      --A-complete-WIDE-bundle private/RACE_full_WIDE_bundle.json \
      --B-win-only-freeze private/RACE_WIN_only_frozen.json \
      --private-output private/RACE_dual_lane_q2_comparison.json

If WIDE is unavailable, simply omit \`--A-complete-WIDE-bundle\`. The A
primary hypothesis stays \`HOLD_FULL_WIDE_NOT_PRETARGET_FROZEN\`, and B's
locally scored q2 is still one race, not a success for A. If neither source
exists, this script rejects the comparison instead of silently removing a
race from the original registered denominator.

The separately declared score files can be grouped and deduplicated by
official race ID and registered slot:

    python scripts/keiba_dual_market_lane_audit.py cohort \
      --reports private/raceA_dual_lane_q2_comparison.json \
                private/raceB_dual_lane_q2_comparison.json \
      --private-output private/all_registered_market_lanes_report.json

The cohort reports the number of A and B models locally scored, number of
races successfully scored in at least one lane, number of eligible exact
A/B pairs, and each lane's missingness, while explicitly guarding that
26+64 are *two candidate* registries, not 90 independent observed races.
Duplicate declared race IDs are rejected. All source quote capture and
external SHA proof validation limitations remain, so the result NEVER
promotes an unverified local score to a genuinely authenticated prospective
JRA sample.

[Dedicated cross-lane CI](https://github.com/zuizui0223/keiba/actions/runs/40532831691)
passed tests with synthetic sources for this exact paired-q2 and missing-WIDE
behavior. Real new forward races remain **0**.
