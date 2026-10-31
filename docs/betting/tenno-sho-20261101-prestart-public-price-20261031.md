# 天皇賞（秋）2026 — 10/31 17:00 public-quote prestart research preview

**Status: PUBLIC-SOURCE-REPORTED, EXPLORATORY MARKET-M0 / NOT A PR22/PR30 PROSPECTIVE SOURCE RECEIPT.**

### Scope and exact documented source

The official [JRA 2026-11-01 Tokyo 11R entry list](https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202604111120261101%2FA6) confirms **17 entries**, Tokyo turf left-handed 2000m and **15:40 JST scheduled post**. The official race is **第174回**; editorial material may incorrectly label it 第173回. This script keys exclusively on official horse numbers 1–17, not any fabricated horse IDs.

The 17 single-WIN prices are taken from the separate, [public October 31 **17:00** quoted *前日単勝* table](https://keiba-times.com/tennosho-aki-2026-zenjitsu-odds/), which distinguishes actual quoted prices from its own earlier *編集部の予想オッズ*. The price pairs \`(horse no., quoted single WIN price)\` were manually transcribed before this proposed race; NO proprietary Data Lab snapshots, local original-export bytes, independent source-receipt proof, per-bet stake totals, or current synchronized WIDE panel were available. Source time **reported by the publisher** is NOT authenticated model-local first receipt. Numbers are price observations as described by the article, not true probabilities or a claim of current odds after 17:00.

[2026 JRA pre-rating publication](https://www.jra.go.jp/datafile/ranking/g1/2026/akiten.html) supplies an *optional*, current-year best race performance descriptor: #1 122, #7 122, #17 118, #11 117, #3 104, etc. #10 lacks a listed current-year pre-rating in that table. Numerical sensitivity uses a fixed NEUTRAL **assumption of 115** for #10 but NEVER reports that number as an observed JRA rating. Highest-race performance ratings are not 2000m running speeds, a field-standardized direct ability estimate or the result of the target race.

JRA [horse background](https://www.jra.go.jp/keiba/g1/akiten/horse.html) identifies #7 as 2025 Akiten winner / 2025 Japan Cup close second and notes his previous overseas King George seventh, #1 as 2026 Osaka Cup and Tenno Spring winner/Takarazuka second, #17 as 2024 Derby winner and 2026 Osaka/Takarazuka third, #3 as successful on good going but two poorer performances in soft conditions, and #11 as Kinko Sho/Sapporo Kinen winner. [JRA track bulletin, 10/31](https://www.jra.go.jp/keiba/baba/) has Tokyo turf **良** and B course, but 11/1 actual day-going and body weights are NOT yet available.

### Exact market-index math (the main answer)

For all **17** published WIN prices \(o_i\), let

\[
q_i^{M0}=\frac{1/o_i}{\sum_{j=1}^{17}1/o_j}.
\]

The sum of the raw reciprocals is approximately **1.2699**, so the unnormalized \(1/o_i\) are NOT win probabilities. The normalized vector is a **relative public market-support index**, not the true probability a horse wins. Ranking/each ticket event from the same exact Plackett–Luce ordered top-three law is *coherent as mathematical probabilities*, but its particular ordering assumptions are not empirically verified against this future race.

| Horse | Earlier published single-WIN payout | Relative market M0 win index | PL-based Top3 index |
| --- | ---: | ---: | ---: |
| **7 マスカレードボール** | 2.4 | **32.81%** | **79.07%** |
| **1 クロワデュノール** | 2.5 | **31.50%** | **77.87%** |
| 3 レガレイラ | 9.8 | 8.04% | 31.09% |
| 17 ダノンデサイル | 11.4 | 6.91% | 27.11% |
| 11 シェイクユアハート | 11.9 | 6.62% | 26.06% |
| 6 セイウンハーデス | 27.2 | 2.90% | 11.90% |

The same ranking law implies indicative event indices: 馬連1–7 **30.5%**, ワイド1–7 **60.2%** (both top 3), 三連複1–3–7 **14.0%**, 1–7–17 **11.9%** and 1–7–11 **11.3%**. These are not observed market-pool odds. There is **no licensed same-time pair/trio price** available in this research protocol, hence **no auditable ticket EV, no edge or stake optimization**. Separately published JRA or sports-site WIDE values do NOT create an atomic same-time market snapshot against the 17:00 single-WIN source from another provider.

### Prestart sensitivity, NOT a trained horse ability model

The source-coded Python experiment runs:

1. Existing \`odds_coherent_hierarchy_rank_bridge.joint_rank_probability\` with \(\beta_{\mathrm{horse}}=\beta_{\mathrm{pair}}=0\). There is **no measured WIDE residual**, no future market update, no slot-time threshold.
2. Existing \`keiba_nonlocal_horse_pde_bettor_bridge.finish_pair\` at 2000m with hypothetical physical \(c=2\) m²/s and matched paired Brownian/Gumbel draws for interacting versus uncrowded horses. Two declared initializations: qM0 alone; alternatively a very rough **rating-only toy** prior \(h_i\propto\exp[(r_i-115)/10]\) with missing #10 imputed neutral **only in simulation**. The latter was never trained to future horse results or market returns.
3. Existing \`pde_density_and_agent_check\` tests marginal probability mass/convergence under the same synthetic \(K,D,c\) law, **not a validation of actual GPS horse trajectories**, and not identical to a fully correlated physical joint-rank PDE.
4. Existing \`keiba_endogenous_threshold_null_bridge.voter_path\` routes the hypothetical horse signal through **one connected market ABM**, at declared rounds 1, 3 or never (5), with fixed 15-minute artificial pseudo-vote duration. No actual future q2 was observed. The no-signal condition is a negative control, not evidence of real bettors. This duration is NOT derived from observed quote timestamps and is a *what-if assumption*, NOT a real market forecast.

No target finishing positions or race payouts are loaded. If the simulated model seems to outperform a price-only forecast, that **cannot** be claimed here: there is still one publicly reported 17:00 quote rather than two controlled as-of WIN snapshots, no simultaneous full WIDE, no calibrated ability/market social coefficients and no out-of-sample official labels.

### Decision note (not an expected-return recommendation)

- **Main win/head-to-head**: 7 マスカレードボール versus 1 クロワデュノール. Source-only qM0 narrowly favors 7; race-form context and expected good Tokyo B-course also support both. 7's recent overseas seventh and 1's potentially tighter inner race position must be monitored, not called known effects.
- **Practical insurance for high-class placings**: 17 ダノンデサイル (consistent G1 thirds, but outside draw), 3 レガレイラ (going-dependent results), 11 シェイクユアハート (recent G2 victories). Outsiders 6 セイウンハーデス / 9 ホウオウビスケッツ can affect pace and surprise in the top three.
- **Illustrative ticket shortlist**, all subject to actual contemporaneous bet-type payout checks (NOT automatically recommended for purchase):
  * Single WIN alternatives: 7 or 1, never pretend a double purchase necessarily creates positive expectation.
  * Unordered quinella: 1–7 as central, 7–17 / 1–17 as high-risk backups.
  * Both-top3 WIDE: 1–7 for concentration, 7–17 / 1–17 / 7–11 for dispersed combinations.
  * Unordered three: 1–3–7 / 1–7–17 / 1–7–11; strongly dependent on both central favorites placing.
  * Ordered: 7→1→17 and 1→7→17 only as very conditional outcome narratives.
  
**Do not sell those as guaranteed best odds, calibrated win rates, real value bets or audited profit calculations**. If the published single-WIN odds or actual track change before the race, current claims must be re-evaluated from the new source using a separate source-and-local-receipt/commit record.

### Reproduce

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests \
      -p 'test_keiba_tenno_20261101_public_market_shadow.py' -v
    python scripts/keiba_tenno_20261101_public_market_shadow.py \
      --horse-draws 120 --seeds 3 \
      --output tmp/tenno-20261101-public-prestart-shadow.json

All artifacts generated by GitHub Actions are **prestart exploratory artifacts**, not PR22/PR30 authenticated quote-capture certificates. This branch is nested on the existing Draft PR #32. It does not modify \`main\`, the old 2026 菊花賞 preseal or the formal v3.1 ledger. **True prospective source-verified next-market trials remain 0 until legitimate capture/receipt and separate q2.**
