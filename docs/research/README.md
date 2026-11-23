# 🐎 生態学研究 / Research start here

> **Status: exploratory observational research; manuscript draft, not submitted.**
> This is the **primary scientific entrypoint** of `keiba`. Horse-race
> predictions, odds and wagering are a separate technical track:
> [betting-methods index](../betting/README.md).

## 2026-11-23 · 券種別市場を個体ノードとペアの情報構造として解析（研究主線）

**[ワイド市場の9レース実測グラフ分解](TICKET_MARKET_INFORMATION_GRAPH_ECOLOGY_20261123.md)**：単勝由来のワイド同時上位3着確率との対数価格比を「馬ノード評価成分＋ペア残差」に分解した。重み付き当てはめ \(R^2\) は10/12京都5Rで**0.686**、10/18の3場4Rで**0.779**。各ペアを1つずつ隠して、同一レース内の残るペアから予測した \(R^2\) も**0.505／0.656**。ただし個体の先天的能力や遺伝価ではなく、**市場における馬単位の価格成分**である。

残差のペア固有成分をさらに足しても、正確な1→2→3着の負対数確率は両日とも平均悪化（追加損失 +0.0178／+0.0040）。これは買い目や利益の評価ではなく、**多層の集合判断が個体成分としてどの程度圧縮できるか**という観測的な情報生態学の問い。まだ**2日・9R・中間オッズ横断面**しかなく、見かけのノード構造が単勝強度の非線形市場補正で説明されないかを反証する必要がある。個体反復・血縁A・ゲノムG・市場情報を同じ個体IDで連結できていない。生物間相互作用、社会学習、遺伝因果は**HOLD**。

[9競走の匿名実測証拠](../evidence/ticket-market-node-dyad-empirical-20261123.json) · [再計算CIとグラフ解析コード](https://github.com/zuizui0223/keiba/actions/runs/45083421066) · [結果前の本人・親族情報精度研究](INFORMATION_PRECISION_HIERARCHY_ECOLOGY_20261118.md)。

**追加の反証検定（2026-11-23）**：馬ノードの価格乖離構造を、単勝人気の**全馬共通の単調非線形価格補正**で説明できるかを、βのみ31条件とβ・曲率γの93条件で比較した。ペアを1組ずつ除外すると共通補正のR²はそれぞれ**0.134／0.125**と**0.164／0.150**、馬ノードの**0.505／0.656**に及ばず、2パラメータ補正後にもノード成分が残った（9/9レース）。ただしγが9レース中7レースで負側の探索境界に達しており、*任意*の価格形成補正を否定したわけではない。生物学的個体性、A/G遺伝構造や集団模倣の証拠でもない。[研究解釈と2種の負の対照](TICKET_MARKET_INFORMATION_GRAPH_ECOLOGY_20261123.md) · [1パラメータの実測台帳](../evidence/ticket-market-temperature-null-20261123.json) · [2パラメータの実測台帳](../evidence/ticket-market-curvature-null-20261123.json)。

**より柔軟な市場補正で再点検（2026-11-23）**：全馬に共通する単勝人気の**1〜4次の滑らかな価格関数**でもペア除外予測を実施。4次まで許すと同一競走内 \(R^2\) は京都5Rで**0.310**、別日3場4Rで**0.230**まで改善するが、馬ノードの**0.505／0.656**には平均で及ばなかった。ただし馬ノードが全レースで勝つわけではなく**9レース中8レース**、京都9Rでは共通の3/4次価格関数が僅かに上回る。**共有された市場価格関数と、馬インデックス別の残差構造を区別した探索的結果**であり、反復する生物学的個体性・社会学習・遺伝的因果を示さない。[本文に全モデルと例外](TICKET_MARKET_INFORMATION_GRAPH_ECOLOGY_20261123.md) · [4次までの実測証拠](../evidence/ticket-market-smooth-null-20261123.json)。

**追加の独立した反証（2026-11-23）**：[市場ノードの60/40ペアブロック検証](TICKET_MARKET_INFORMATION_GRAPH_ECOLOGY_20261123.md#3d-ワイドの40を隠すブロック外挿馬単位の構造はどこまで頑健か)では、未使用40%のワイドペアに対するノードR²は京都5Rで**0.367**、別日4Rで**0.590**（固定ridgeを入れると**0.428／0.613**）。共通4次価格関数は**0.248／0.181**で、馬ノードは**8/9レース**で優位。ただし馬番はレース固有であり、異なる競走で同一馬が反復する個体差ではない。[証拠](../evidence/ticket-market-edge-block-heldout-20261123.json)。

**理論上の識別限界と観測的反例**：単勝オッズが全て異なるなら、馬別の価格係数を任意に柔軟な人気関数でも補間できる。これに対して単勝表示オッズが**同一**の馬2組（10/18東京11R・新潟11R）を自然な対照とすると、第三馬とのワイド表示価格は**19/19で違い**、そのうち**18/19で表示価格範囲が非重複**だった。標準PLと表示丸め±0.05を条件付きで許しても18/19が区間外。配信時刻のずれ・未表示値・異なる市場価格形成で説明される可能性は残り、これは遺伝的・反復個体差の証拠ではない。[同じ資料の出典と限界](../evidence/ticket-market-odds-tie-identification-20261123.json)。

## Integrated November 2026 Japan / genotype / market research

Read the **[integrated evidence and future paper program](INTEGRATED_KINSHIP_GENOME_INFORMATION_MARKET_20261118.md)** first for a source-separated evaluation of measured positive, negative and not-yet-tested claims: selected Japanese parent-history forecasts in 2019–2026, partial Wikipedia numerator A, 370 anonymous Japanese Thoroughbred SNP samples and genomic G, nine observed odds snapshots and human-voter ABM on **synthetic** later ballots. The source data are not a combined pedigree × genome × market same-horse panel. In particular, the first 2026 external-period family signal did **not** transfer robustly, and the refreshed own-history results are explicitly post-hoc.

**New explicit information-precision hypotheses:** [own-history vs family-history posterior precision and a correlated-context falsification](INFORMATION_PRECISION_HIERARCHY_ECOLOGY_20261118.md), with [regenerable real aggregate signs plus analytic-only toy audit](../evidence/information-precision-hierarchy-audit-20261118.json). The toy parameters are not estimates of additive genetic covariance, and the cross-section market source contains no market-odds time trajectory. A future biological vs human-market information test requires separate real race-ID and known-on time series.

Original Australian early-GPS animal-individuality studies below are **a separate measured phenotype**; do not silently pool their first-150m GPS elapsed seconds with Japanese normalized finishing ranks.

## 2026-11-22 · 年代と履歴量まで一致する非親族の支持域監査（PR #75）

[厳格な実資料照合](JAPAN_2022_24_TIME_DEPTH_MATCHED_NONKIN_RESULTS.md)では、PR73で選んだ真親族の各他馬と同じ**最終記録年・同条件歴史出走数（1／2–4／5+）**の非親族を探した。PR70–73の再計算・SHA照合に成功し、**32seed×5履歴cutoff×父母2側＝320の照合組合せ中319組が完全一致、2021年学習用の父方・5走以上だけ1seedで1枠不足**。全26,464,320の選択馬×抽出枠のうち不足は1枠。ただし重複したモデル抽出枠であって独立馬数ではなく、**学習入力の1件不足がRidge係数を変え得る**ため、新しい全標本の親族−非親族MSE差と8比較CIは**HOLD**（計算・補完なし）。**親族効果ゼロとは言っていない**。[実測前に固定した仕様](JAPAN_2022_24_TIME_DEPTH_MATCHED_NONKIN_PROTOCOL.md) · [匿名の支持域台帳](../evidence/japan-2022-24-time-depth-matched-nonkin-20261122.json) · [実資料Actions #45010304245](https://github.com/zuizui0223/keiba/actions/runs/45010304245)。

## 2026-11-22 · 親族 vs 同数の非親族を使った負の対照（PR #74）

元の**244,147出走・12,887頭・35,333競走**を維持し、PR73で固定した各側の過去馬数kを使って、**記録上どちらの親も共有しない過去馬**を同じ芝/ダート・距離帯から32回抽出して一つの非親族モデルNを毎回再学習した。通期で真の同数父方MSがNを上回るMSE点推定は**+1.57×10⁻⁶**、真の同数母方MDは**+33.97×10⁻⁶**。8比較Bonferroni区間はそれぞれ**[−22.32,+25.46]**、**[−58.49,+126.44]**で、**全8区間が0を含んだ**。2024年母方だけ父群・母群の**点別**区間は正だが、補正後は0を含み、**同年N/MS/MDは全てM0より悪い**。

非親族Nと本人＋父母頭数MCの通期RMSEは**0.312392706/0.312393483**で近かった。これは共有する記録上の直接の親を除いた、出走年や厩舎まで一致しない**不完全な非親族対照**であり、血縁度A/G、遺伝率、母性効果、馬自身の情報利用を識別しない。古い2022–24結果の**事後的な**比較である。[全8区間と絶対性能](JAPAN_2022_24_UNRELATED_PEER_PLACEBO_RESULTS.md)・[結果前に固定した仕様](JAPAN_2022_24_UNRELATED_PEER_PLACEBO_PROTOCOL.md)・[SHA固定の匿名全集計](../evidence/japan-2022-24-unrelated-peer-placebo-20261122.json)・[再現来歴](../evidence/japan-2022-24-unrelated-peer-placebo-provenance-20261122.json)。

## 2026-11-22 · 父母の他馬履歴数をそろえる感度分析（PR #73）

同じ **244,147出走・12,887頭・35,333競走**の全行を残し、本人を除く同父・同母の過去馬数を両側とも `k=min(s,d)` にした。元の父母双方の頭数特徴と本人・条件情報を保持し、固定32抽出で父方のみ・母方のみを計64回再学習した。抽出ごとの二乗誤差を平均するため、予測のアンサンブルとは異なる。

通期の父方優位Fは **+82.39 → B −32.40 ×10⁻⁶ MSE**へ符号が変わり、変化C=F−Bは **+114.79**。馬×暦日の8比較Bonferroni区間はB **[−124.25,+59.45]**、C **[−8.41,+237.99]**（同じ単位）。**通期・年別の主比較8区間は全て0を含む。** 母方優位の確定や、元の差の何%が履歴量で生じたかという因果分解にはならない。

評価区間は固定した32組の抽出・学習を条件とし、BとCの抽出MCSEは通期 **3.926**、2024年 **11.030 ×10⁻⁶ MSE**。区間のゼロ付近の境界を、無限回抽出でも確定した符号と読めない。等頭数でも他馬の独立性・精度・環境は揃わず、遺伝的寄与も識別しない。**2024年の均等頭数2モデルはともに中間順位M0より悪い。** ローカルとActionsの960数値項目は最大差1.14×10⁻¹³で再現した。[実測結果](JAPAN_2022_24_EQUAL_PEER_INFORMATION_RESULTS.md)・[手順](JAPAN_2022_24_EQUAL_PEER_INFORMATION_PROTOCOL.md)・[匿名集計](../evidence/japan-2022-24-equal-peer-information-20261122.json)・[再現来歴](../evidence/japan-2022-24-equal-peer-information-provenance-20261122.json)。

## 2026-11-22 · Comparing sire-side and dam-side performance histories

On the same **244,147 starts, 12,887 horses and 35,333 races**, all four models in the parent comparison retained both historical peer counts. Adding sire-side performance after dam-side performance reduced pooled horse-equal MSE by **103.28 × 10⁻⁶**. Adding dam-side performance after sire-side performance reduced it by **20.89 × 10⁻⁶**. The direct advantage for sire-only over dam-only performance was **82.39 × 10⁻⁶ MSE**, with a 12-comparison Bonferroni 95% interval of **[−78.43, +243.21] × 10⁻⁶**. All 12 adjusted intervals included zero. The direct comparison included zero under every interval method in each period. In 2024 the constant midpoint had lower error than all six fitted models.

Both parents were recorded for every evaluated horse. Within the same surface and 400 m distance band, the horse-equal mean count of distinct historical peers was **317.193 sharing the sire** and **2.805 sharing the dam**. Starts with peers on both sides accounted for **82.315% of evaluation weight** after giving each horse equal total weight. This retrospective comparison measures predictive performance under unequal coverage. [Results](JAPAN_2022_24_PARENT_PERFORMANCE_CHANNELS_RESULTS.md) · [protocol](JAPAN_2022_24_PARENT_PERFORMANCE_CHANNELS_PROTOCOL.md) · [anonymous aggregates](../evidence/japan-2022-24-parent-performance-channels-20261122.json).

## 2026-11-21: Recorded-sire distribution — positive in 215 of 383 groups, selected joint deletion remains influential

The [fixed-prediction concentration analysis](JAPAN_2022_24_SIRE_SIGNAL_CONCENTRATION_RESULTS.md) reproduces PR70 on the same **244,147 starts / 12,887 horses**. P-after-C improvement is positive in **215 of 383 recorded sire groups** and negative in 168. Every single-group deletion retains a positive horse-equal mean; the minimum jointly deleted set that makes a nonempty remainder nonpositive is **11 groups / 1,567 horses (12.16%)**, chosen by observed contribution. This is an outcome-selected sensitivity diagnostic without refitting, not a deployable family-selection rule or a minimum number of horses.

Pooled horse-equal gain is **+0.000140910**, sire-equal **+0.000246870**; both whole-sire pointwise 95% intervals and their difference's interval cross zero. **Only 2024 sire-equal gain has a wholly positive pointwise interval** among the four periods × three estimands. That changes the target weighting and does not undo the known 2024 horse-equal loss of all learned models against M0; sire-equal M2 versus M0 was not assessed. Group size counts evaluated horses, and P includes both paternal and maternal histories. [Protocol](JAPAN_2022_24_SIRE_SIGNAL_CONCENTRATION_PROTOCOL.md) · [full anonymous aggregates](../evidence/japan-2022-24-sire-signal-concentration-20261121.json).

## 2026-11-21: Actual family-feature ablation — larger performance-block point estimate, family-cluster uncertainty remains

The [new four-model analysis](JAPAN_2022_24_FAMILY_FEATURE_ABLATION_RESULTS.md) keeps the same **244,147 starts, 12,887 horses and 35,333 strict races**, original 2018–21 training blocks and ridge penalty 100. Horse-equal RMSE is **0.312429448** for M1, **0.312393483** after adding explicit log peer counts C, **0.312194516** after adding shrunk peer performance P, and **0.312167869** for full M2. The order-averaged allocation of M1→M2 MSE improvement is **+0.000143827 to P** and **+0.000019555 to C**. These are refitted-model loss allocations; P itself already contains own- and peer-count shrinkage.

**No robust positive conditional effect is established:** both the eight-comparison-adjusted horse×calendar-day intervals and the 999 whole-sire-cluster pointwise intervals cross zero for every pooled/yearly conditional contrast. The pooled P-after-C point is **+0.000140910**, sire interval **[−0.000033325, +0.000292310]**. In **2024 all four learned models lose to midpoint M0**. This retrospective analysis separates implemented feature blocks, not genetic effects, animal information use or biological fitness. [Protocol](JAPAN_2022_24_FAMILY_FEATURE_ABLATION_PROTOCOL.md) · [full anonymous aggregates](../evidence/japan-2022-24-family-feature-ablation-20261121.json).

## 2026-11-21: Make future sample selection immutable before racing — software-only SHA+GitHub original commit chain

A new [immutable 2027 eligible-race universe protocol](JAPAN_2027_IMMUTABLE_UNIVERSE_PLEDGE_PROTOCOL.md) fixes the previously unsealed **private eligible-race CSV bytes** by SHA256, binds them to the existing pre-race horse-level forecast SHA, public prediction manifest SHA and the source/forecast pledge bundle SHA, then publishes **only hashes, aggregate target counts, missed forecast counts and first declared start** in a content-addressed NEW GitHub file. A dedicated real **push-only** workflow requires a first-time original GitHub server `created_at` before the earliest declared start and rejects edits/re-runs. Post-race **two independent original-commit checks** (universe and original model/source bundle) reopen exact Git Blob SHA/bytes and completed first-run SUCCESS before the existing [frozen-denominator missing-rank auditor](JAPAN_2027_FROZEN_UNIVERSE_RANK_BOUNDS_RESULTS.md) may score.

This is a **future integrity/selection safeguard, not current JRA data or a scientific forecast result**. [Actual GitHub Actions synthetic run #44903130236](https://github.com/zuizui0223/keiba/actions/runs/44903130236) passed **20 new fictional tests, 14 earlier denominator tests, 24 frozen forecast tests and 36 GitHub bundle tests (94 fictional in total)**. **Zero real official 2027 forecast pledges, zero independently verified complete official eligible-race universe, and zero licensed individual race results.** GitHub's existence timestamp proves an opaque pledge was present, **not** JRA provider publication time, source authenticity or biological fitness. The implementation intentionally remains **HOLD** for those questions. [Recorded software result](JAPAN_2027_IMMUTABLE_UNIVERSE_PLEDGE_RESULTS.md) · [anonymous test provenance](../evidence/japan-2027-immutable-universe-pledge-20261121.json).

## 2026-11-21: 2027 preregistered forecast denominator and unresolved-rank bounds — SOFTWARE ONLY

The prospective 2027 [frozen-race-universe and complete-rank permutation bounds protocol](JAPAN_2027_FROZEN_UNIVERSE_RANK_BOUNDS_PROTOCOL.md) now guards against cherry-picking only races with final results. It checks a *separately supplied, forecast-cutoff-known* list of intended races (a private, not independently certified official schedule), counts races with missing forecasts and preserves **all frozen forecast starts and original horse-equal weights**, even where results were never received. Missing race outcomes receive exact **M1−M2 and M0−M2 feasible MSE loss bounds conditional on every unresolved race having a complete 1..N ranking**; cancellations/DNF/undefined normalized-rank targets force **HOLD**, not fictional negative labels. All-complete bounds must equal the existing frozen scorer's horse-equal RMSE squared difference.

**Science status: 14 new fictional-race falsification tests plus the existing 24 frozen-score and 36 GitHub-push tests, 0 real 2027 JRA forecasts, 0 licensed registry source or externally certified complete race universe.** The bounds are *mathematical worst-case rank assignments*, not 95% confidence intervals or evidence for an adaptive/genetic family effect. External GitHub pre-race original-commit attestation remains a separate gate; source race-list possession alone cannot prove JRA completeness. [Implementation](../../scripts/ecology_japan_2027_denominator_rank_bounds.py) · [synthetic QA/results](JAPAN_2027_FROZEN_UNIVERSE_RANK_BOUNDS_RESULTS.md) · [fictional tests](../../tests/test_ecology_japan_2027_denominator_rank_bounds.py).

## 2026-11-21: Frozen information gate's apparently strong exposure gap is history composition, not adaptive information use

The [actual-source 2022 MG switch-exposure audit](JAPAN_2022_INFORMATION_SWITCH_EXPOSURE_RESULTS.md) reproduces the same **12,755 horses and 120,381 starts**. For future-2024 recorded versus unrecorded animals, the horse-equal fraction of starts where **the model MG** chose its own-history M1 (rather than always-family M2) was **35.49% versus 52.06%**, a sire-bootstrap nonzero difference **−16.56 percentage points**. But the gate explicitly selects M1 in **100% of animals with 16+ pre-2022 own records**, and in fewer than 1% of starts within each lower-history bin. Standardizing to the same four pre-2022 own-history-bin mix changes the exposure gap to **+0.033 percentage points**, sire-bootstrap 95% interval **[−0.088, +0.153] points**, crossing zero. Almost the full unadjusted M1-switch exposure disparity is therefore a **deterministic algorithmic gate × cohort prior-history mix** rather than evidence of horse learning or a new behavioral strategy.

An exact algebraic decomposition of the previously observed 2024 group difference in 2022 **MG-vs-M2 MSE (−0.00013014)** gives frequency component **−0.00003203** (recorded-sire interval negative) and conditional M1-switch loss component **−0.00009811** (recorded-sire interval crosses zero). The conditional-group difference and the un-gated, frozen 2018–21 **M1-vs-M2** group comparison also lack robust sire-cluster support. Among the **8,659 horses also observed in 2023**, the history-standardized gate exposure gap is ~zero and the MG group difference remains uncertain. These are post-hoc model arithmetic and observational comparisons, not genetic effects, lifetime survival, mortality, fitness or prospectively verified prediction. The prior [2022 opportunity-standardized cluster audit](JAPAN_2022_OPPORTUNITY_CLUSTER_RESULTS.md) also showed zero-crossing intervals.

[Source audit and uncertainty](../evidence/japan-2022-switch-exposure-20261121.json) · [Python analysis](../../scripts/ecology_japan_2022_gate_exposure_selection.py) · [post-result history-bin adjustment protocol](JAPAN_2022_INFORMATION_SWITCH_EXPOSURE_PROTOCOL.md).

## 2026-11-21: 2022 source-observation opportunity adjustment removes robust cohort-gap support

**Important further qualification to the prior retrospective negative 2022 cohort-contrast:** The [actual-source six-specification 2022 observation-opportunity audit](JAPAN_2022_OPPORTUNITY_CLUSTER_RESULTS.md) fixed the same **12,755 horses, 120,381 starts, 381 recorded sire groups, original 2018–21 M1/M2 and 2022-selected MG**. Once pre-2022 own-history count was standardized jointly with the horse's **last 2022 recorded half-year** or **number of 2022 recorded starts**, the 2024-present-vs-absent MSE advantage point estimates shrank to approximately **−0.0000774/−0.0000769**. In the subset of 8,659 horses also recorded in 2023, the available joint-history-plus-starts estimate was **−0.0000752**. Across **all three available estimands**, horse×calendar-day 95%, whole-sire-cluster 999-draw 95%, and six-contrast Bonferroni 95% sensitivity intervals **all cross zero**. Three more granular pre-specified combinations are **HOLD for sparse group support (4/2/7 unsupported cells)**.

Thus **the direction of source-observation bias is visible, but its claimed residual strength is not robust after 2022 observation-opportunity standardization and clustered uncertainty**. This does not demonstrate absence of an effect or that the recorded race count caused the difference. The 2022 final recorded half-year and full-year number of starts are post-event proxies **not known before 2022's races**; conditioning on them may itself select horses. The frozen MG was chosen after looking at 2022 results, and source record nonappearance does not mean biological death, retirement or failed reproduction. [SHA-pinned anonymous evidence](../evidence/japan-2022-opportunity-cluster-20261121.json) · [Python source](../../scripts/ecology_japan_2022_opportunity_cluster_inference.py) · [retrospective protocol](JAPAN_2022_OPPORTUNITY_CLUSTER_PROTOCOL.md).

## 2026-11-21: Actual-source 2023/2024 observation paths and eligibility-bias audit

**The old 2024 source-record contrast should not be described as confirmed retention or dropout.** The new [2022→2023→2024 pathway audit](JAPAN_2022_24_OBSERVATION_PATHS_RESULTS.md) keeps the same **12,755 2022 horse candidates and frozen 2018–21 M1/M2 plus 2022 MG**. Its four strict-evaluation future-source states were: **both 2023/24 = 5,102**, **2023 only = 3,557**, **2024 only = 61**, **neither = 4,035**. Their 2022 MG-minus-M2 MSE gains differ (respectively −0.00002901, +0.00004726, −0.00006760, +0.00014776). The original 2024-present-vs-absent difference **−0.00013014** splits arithmetically into 2023-status composition **−0.00005223** and within-2023-status difference **−0.00007791**. These are not causal pathway percentages.

**Critical qualification:** among the 8,659 2022 animals also observed in 2023, the 2024-present-vs-absent 2022 gain difference shrank to **−0.00007627** (2021-history-adjusted **−0.00007403**), and **both horse×day and sire-cluster sensitivity intervals cross zero**. Adjustment for recorded 2022 starts and/or last observed half-year yielded smaller descriptive point estimates, with several crossed strata held for sparse support. Only **23 of 7,592** horses absent from the strict 2024 evaluation had a broader validated source-B race-history entry; **7,569** had none in that *still-filtered* eligible source. Neither category proves that a horse did not race, retired or died.

For true observational survival, transfers and breeding follow-up the [official registration/UM and NAR source contract](JAPAN_REGISTRY_OBSERVATION_STATE_BRIDGE.md) is **not yet filled with actual linked individuals**. Preserve the original negative 2024 benchmark against midpoint M0. [Source SHA-pinned anonymous evidence](../evidence/japan-2022-24-observation-paths-20261121.json) · [Python implementation](../../scripts/ecology_japan_2022_24_observation_paths.py) · [frozen post-hoc design](JAPAN_2022_24_OBSERVATION_PATHS_PROTOCOL.md).

## 2026-11-21: Actual 2022 later-observed cohort bias survives separate history, date and sire sensitivity

The [source-locked 2022 future-observation audit](JAPAN_2022_OBSERVATION_SELECTION_CLUSTER_RESULTS.md) re-evaluated the **same 12,755 observed horses and 120,381 starts from 2022**: 5,163 horse candidates had a further source record in 2024, while 7,592 did not. The 2022 MG-versus-always-M2 horse-equal MSE difference was **−0.000130139** between those groups; controlling for four pre-2022 own-history count bins using the **full 2022 population's composition** gave **−0.000126286**. Both retrospective differences had **negative horse×2022 calendar-day intervals, negative 2-estimand Bonferroni sensitivity intervals and negative recorded-sire-cluster bootstrap intervals**. The sire-cluster intervals' upper bounds are near zero, so a single large paternal group's influence was assessed *after viewing the results*: **381 of 381 sire leave-one-out values were negative** for both estimands. The largest recorded sire group contained 311 horses.

This is **descriptive informative observation** in a selected secondary-source cohort, not a biological survival rate, retirement observation, adaptive selection, genomic effect, causal herd behavior or an independent future test. The 2022-selected gate was itself chosen after examining 2022 outcomes. The 2024 absence/presence classification is retrospective, and official studbook IDs and full observation reasons remain unavailable. The [anonymous actual-source evidence](../evidence/japan-2022-observation-selection-cluster-20261121.json), [code](../../scripts/ecology_japan_2022_observation_selection_dependence.py) and [protocol including post-result LOSO disclosure](JAPAN_2022_OBSERVATION_SELECTION_CLUSTER_PROTOCOL.md) preserve positive and negative results. **Do not conflate this 12,755-horse cross-cohort comparison with the separate 4,636-horse three-year within-horse trend, which failed sire/multiplicity robustness.**

## 2026-11-21: Dependence audit downgrades robustness of temporal kin-information shift

**Correction to the preceding post-hoc three-year result:** The [actual-source horse × race-day, sire-family and 3-comparison audit](JAPAN_2022_24_DEPENDENCE_SENSITIVITY_RESULTS.md) reproduced the **same 4,636 animals, 5,895 animal×context cells and frozen 2022 model**. The 2023→2024 MG-vs-always-M2 MSE difference remains **−0.000120824**. Its horse×calendar-day normal 95% sensitivity interval was negative (**[−0.000223736, −0.000017911]**), but the three-comparison Bonferroni interval **[−0.000246525, +0.000004878]** and recorded-sire-cluster interval (**280 groups; [−0.000265776, +0.000007552]**) **both cross zero**. Thus the prior horse-only significant direction **does not support robust or universal temporal decay**.

This is an observational correlation correction, not evidence that genetics, heritability, breeding fitness or real odds-market behavior caused an effect. The **2022 future-2024-observation selection contrast is a separate estimand**; its dedicated horse×calendar-day and sire checks are reported in the newer [observation-selection study](JAPAN_2022_OBSERVATION_SELECTION_CLUSTER_RESULTS.md), and remain retrospective and non-causal. Preserve the 2024 loss of MG and M2 against midpoint M0. [Anonymous source-verified result](../evidence/japan-2022-24-dependence-sensitivity-20261121.json) · [reproducible code](../../scripts/ecology_japan_2022_24_dependency_sensitivity.py).

## 2026-11-21: Balanced three-year horse-context and observed-participation selection (real, post-hoc)

The [actual-source 2022–24 balanced three-year audit](JAPAN_2022_24_BALANCED_THREE_YEAR_SELECTION_RESULTS.md) holds **4,636 observed horses and 5,895 horse × turf/dirt/400-m band cells** constant throughout 2022, 2023 and 2024, with each horse's 2022 context weights unchanged. The 2022-selected individual/kin gate (MG) relative to always-family M2 deteriorated **2023→2024 (horse-equal MSE difference change −0.000120824, 399 horse-bootstrap 95% sensitivity interval [−0.000214007, −0.000024614])**. However 2022→2023 and 2022→2024 sensitivity intervals span zero: do not infer a universal monotonic decay.

**Selective observation is a separate and stronger descriptive finding.** In 2022, horses also recorded in 2024 (5,163) already had MG−M2 loss differences **−0.000130139** lower than 2022 horses without 2024 source records (7,592), 95% horse-only sensitivity interval **[−0.000217021, −0.000035517]**. Only about **24.5%** of that *arithmetic group difference* is accounted for by composition of four pre-2022 own-history bins; the rest is within-bin differences. Neither figure identifies survival, retirement, biological selection, additive genetic effects, age-related behavioral change, market dynamics or causal mechanisms. The first year's MG advantage and 2024 loss against M0 are both preserved. These years were inspected before this analysis; **no new prospective claim**.

Code, protocol, synthetic falsifications, source SHA and anonymous aggregate: [Python](../../scripts/ecology_japan_2022_24_balanced_three_year.py) · [protocol](JAPAN_2022_24_BALANCED_THREE_YEAR_SELECTION_PROTOCOL.md) · [evidence](../evidence/japan-2022-24-balanced-three-year-selection-20261121.json) · [successful actual-data workflow](https://github.com/zuizui0223/keiba/actions/runs/44762798731).

## Real 2022–24 family-information moderation (post-hoc)

The [source-locked 244,147-start descriptive stratification](JAPAN_2022_2024_KIN_INFORMATION_MODERATORS_RESULTS.md) explores how the **incremental prediction value** of recorded same-parent other-horse history changes with the focal horse's own qualifying historical observations. Positive pooled differences decline across 0–3, 4–7, 8–15, 16+ own-start bins, but **2024 reverses the low-vs-high ordering** and the relative-history-age gradient is not monotone. These are earlier-inspected historical results, not a fresh source evaluation, genetic heritability, a complete pedigree matrix A, genomic G joined by registered ID, or evidence of market herding. [Aggregate-only evidence with positive/negative strata](../evidence/japan-2022-24-posthoc-kin-information-moderators-20261118.json).

## 2022-selected family-information rule: historical 2023–24 transfer failure

The [real-source calendar-forward diagnostic](JAPAN_2022_KIN_GATE_2023_24_TRANSFER_RESULTS.md) selected a conditional family-history-use rule using 2022 results alone, then evaluated it unchanged on 2023 and 2024. The selected rule was best among 14 candidates in 2022 but **did not outperform always-family M2 in either later year** and lost to the fixed midpoint in 2024. This demonstrates instability of a decision rule in previously inspected historical source data; **not** an untouched future holdout, a pedigree A/genomic G causal effect or observed human-market information transmission. [Aggregate-only negative evidence](../evidence/japan-2022-trained-kin-gate-2023-24-transfer-20261118.json).

**Why the 2022-selected family-information gate fails over years:** the [locked real 244,147-start cohort decomposition](JAPAN_2022_24_GATE_FAILURE_DECOMPOSITION_RESULTS.md) separates changing focal-own-history-bin composition from differences within those bins (2022→24 descriptive MSE-accounting 5.7% vs 94.3%), and separately examines which horses appear in the later year (42.3% of signed degradation) vs changes in race-year forecast errors among the same 5,163 horse-ID candidates (57.6%). These are exact algebraic descriptive shares, **not causal selection or genetic effects**; the paired-horse single-way bootstrap interval includes zero. [Source-hash-locked aggregate](../evidence/japan-2022-24-gate-shift-composition-paired-20261118.json).

## Central ecological question

**Under which observational conditions does an individual horse's previous
early-race timing carry information about its later timing — and when
is that information not transferable?**

The research starts from the same numeric original `HORSES ID` across
published Racing Queensland race rosters and first-positive GPS sectionals.
The current response is a measured **first-sectional timing**, or its
**race-relative** form (focal timing minus the other GPS-timed horses'
mean). This is **not** a complete starter/finisher time, a pre-race speed
forecast, an innate temperament measure or a genetic phenotype.

### Read in this order

1. [**Evidence and HOLD matrix**](EVIDENCE_MATRIX.md) — one table separating
   measured results, source failures, synthetic tests, and untested claims.
2. [**Paper draft v1**](../ecology-racehorse-individuality-manuscript-v1.md)
   — English Abstract/Methods/Results/Discussion. **Not submitted**.
3. [**Critical same-horse temporal comparison audit**](../ecology-rq-doomben-matched-timescale-overlap-real-results.md)
   — two signed source-conditional prediction results cannot estimate
   within-horse aging: **0 shared eligible horses**.
4. [**Data and reproducibility guide**](REPRODUCIBILITY.md) —
   how source version, missingness, identity and unit tests are checked.
5. [**Priority next experiments**](ROADMAP.md) — what would actually
   resolve H1 horse×ground and H2 horse×competitor effects.
6. [**Long-form development notebook**](../../ECOLOGY_RESEARCH.md) —
   the original ~66 KB merged research narrative, retained as a
   historical lab record rather than a short statement of established facts.

## What empirical observations currently support

| Empirical track | What is observed | What it does **not** establish |
| --- | --- | --- |
| Cannon Park, repeated official horse identities | A model-conditional, race-adjusted first-GPS horse-ID ICC was positive (~0.430 in the later pinned source snapshot); dates, races and GPS-positive selection matter | Innate/heritably stable behavioral personality |
| Cannon Park, chronological same-horse history | **36 source horse IDs / 46 later observations**: own earlier race-relative timing RMSE **0.255809 s**, other-horse matched-context history **0.303195 s** | Independently validated prediction; verified rider-switch cause; a commercial betting model |
| Doomben, within-2025 history | In two consistent 38/42-date original re-fetches, **23 IDs / 24 scored later rows**: own **0.211065 s**, other **0.240692 s**; other date-availability snapshots fell below the source gate | Population-level source stability or an annual personality trajectory |
| Doomben, 2025 histories to 2026 | **26 IDs / 27 later observations**: own **0.386131 s**, other **0.368906 s** (own does worse in this source-conditioned cohort) | Loss of individuality due to aging or elapsed time |
| Doomben, **same animals** across the two evaluation horizons | **0 shared eligible horse IDs** at the same first-GPS 150 m marker and official race distance; the date-and-ID-only audit independently agrees | A meaningful within-animal difference between within-year and year-forward predictability |

For **all numerical claims**, refer to
[the evidence matrix](EVIDENCE_MATRIX.md) and their named source documents.
Do not compare `RMSE` between the Cannon and Doomben groups as if they
measured the same animals or a randomized difference in time horizon.

## The more ambitious hypotheses are on scientific HOLD

**H1 — heterogeneous ground reaction norms.** Some original animals appear
on Good and Soft/Heavy tracks, but repeated **same horse × exact marker ×
distance × Class × ground** support is insufficient for defensible
individual-by-going slopes. The expanded source screen found **0**
same-context horse strata with at least two Good and two wet observations.
See [original H1 source support](../ecology-rq-real-h1-multigoing-expanded-audit.md).

**H2 — rival-dependent early pacing.** The repo has mathematical
negative controls and two-part/absolute-speed prototypes on
**fabricated data**, but not a source-complete verified actual-starter,
actual finish-time and competitor-composition outcome table.
Race-relative GPS peer means mechanically change when the observed
other horses change. See [H2 outcome selection](../ecology-h2-outcome-selection.md)
and [synthetic absolute-speed stress audit](../ecology-h2-absolute-stress-audit.md).

**Cross-racecourse trait replication — HOLD.** Cannon and Eagle Farm
positive pooled horse-ID ICCs use different first-section marker
distributions and have **no jointly estimable identical-marker
ICC subgroup**. [Source audit](../ecology-rq-eagle-farm-real-icc-cross-site-audit.md).

## New, not-yet-empirical extension: pedigree-based future prediction

[**Pedigree forward protocol and offline scorer**](PEDIGREE_FORWARD.md) tests
whether relatives' earlier absolute first-GPS timing provides incremental
future predictive information beyond a horse's own history. The as-of
pedigree coefficients, cold-start split and synthetic regression tests
are implemented; a [**simulation-only trainer-confounding falsification**](PEDIGREE_FALSIFICATION.md) demonstrates why predictive gains are not heritability; **no validated original HORSES-ID × sire/dam crosswalk exists**
for the current real cohort, so its kinship predictive effect remains
**HOLD / UNTESTED**. This is not heritability or a horse-racing odds model.

## Japan case study — Meisho name is not a pedigree

[**Japan Meisho study / real JBIS maternal-kin evidence**](JAPAN_MEISHO_DESIGN.md)
adds 11 hand-verified public JBIS profiles (9 named メイショウ), three
different-sire shared-dam pairs, and 13 pairs linked through documented
maternal paths (including parents). This is **real identity evidence,
not actual timing prediction**. The separate strictly time-forward
**synthetic** scorer compares a common name prefix, documented pre-race
owner IDs, known kin, and combined owner+kin on the SAME future targets.
The real Japanese name/owner/kin predictive improvement remains **HOLD**:
original race-level GPS, pre-race owner versions, stable JRA/JBIS crosswalk
and licensed longitudinal outcomes are not yet joined.

## Meisho naming-group matched null: real-source negative/control evidence

[**Meisho name group versus 999 coverage-matched real horse sets**](JAPAN_MEISHO_MATCHED_CONTROLS.md): in a **new 5,879-article Wikipedia source version** (different SHA from the earlier frozen 5,878-article study), 38 named Meisho horses had 703 within-group pairs and mean partial pedigree A **0.01328**, vs **0.01134** for decade/country/parent-link-coverage-matched control sets. This is **not compelling evidence of a systematically special high-kinship clan**; among the same control sets the frequency of A>=0.125 pairs was actually lower for Meisho (10 vs mean 22.77). The source cohort is selected, dam IDs sparse, and no breeding causal or racing-performance prediction is justified. [Reproducible aggregate result](../evidence/japan-meisho-coverage-matched-kinship-20261114.json).

## Nationwide pedigree computation: source gate still OPEN

[**Japan JRA/NAR full-registry kinship method**](JAPAN_NATIONAL_PEDIGREE_SCALING.md)
adds exact pedigree numerator A, partial inbreeding F, per-horse shared
parent/full-sib/half-sib counts, a bounded Wikidata CC0 check, and sparse
pair-query output. It was **actually run** on 11 manually checked real
profiles (all 55 pairs, 13 nonzero documented maternal paths) and 12
Wikidata Japan-origin QIDs (all 66 pairs, 2 nonzero documented paths;
deeper ancestors HTTP 429). **Neither is the complete JRA+NAR register.**
No complete national pedigree export was obtained; a countrywide genetic
matrix, inbreeding distribution or speed prediction must NOT be claimed.

## Large real public-data pedigree benchmark (2026-11-14)

The source-conditional [Japan national scaling report](JAPAN_NATIONAL_PEDIGREE_SCALING.md)
now also includes an **actual large-source subset**: 5,878 Japanese-language
Wikipedia racehorse article IDs with **17,272,503 exact partial-pedigree A
pair calculations** (5,327,594 with a documented positive ancestral path).
Among 3,411 entries explicitly labelled Japanese-born, 5,815,755 pairs
were scored (2,555,223 positive documented paths). The mother link is
available for only 642/5,878 article IDs, so a positive A does not
establish close kin, and missing paths cannot be treated as non-kin.
The 38 メイショウ-prefixed Wikipedia articles form **703 within-prefix
pairs (311 with documented paths)**, not a Japanese ownership or breeding
census. [Frozen source SHA, both reruns, denominators and bins](../evidence/japan-wikipedia-actual-kinship-20261114.json).
**New real-data source-information contrast:** removing the 642 documented
maternal page links from the SAME 5,878-horse source removes **2,049,634**
of the previously documented positive A paths (**38.5%**), and reduces
A for **4,912,213** same-target pairs. Among Japan-born-infobox
articles the missing-path count is **879,783**, and among 38 Meisho-name
articles **34**. This quantifies pedigree-source sensitivity, **not**
a maternal genetic variance or predictive racing effect.
[Fixed-SHA paired source-ablation evidence](../evidence/japan-wikipedia-maternal-ablation-20261114.json)
and [protocol](JAPAN_PEDIGREE_MATERNAL_SOURCE_SENSITIVITY.md).

A separate exact Japanese Wikipedia page → Wikidata QID cross-check on
**200 selected real articles** (all 38 Meisho titles included) found
**12 candidate new mother QID links** absent from the article baseline;
none was silently merged into the main pedigree.
[Secondary parent audit](../evidence/japan-wikimedia-200-parent-qid-audit-20261114.json).

**JRA+NAR population-complete A and prediction effects remain HOLD.**

## Practical directory map (preserves working imports)

| Source family | Location |
| --- | --- |
| Original Racing Queensland data-read scripts | [`scripts/ecology_rq_*`](../../scripts/) |
| Ecological hypothesis simulations | [`scripts/ecology_h1_*`, `ecology_h2_*`](../../scripts/) |
| Ecology synthetic + source-aware QA | [`tests/test_ecology_*`](../../tests/) |
| Fixed calendar/design/source protocols | [`docs/ecology-*.md`](../) |
| Anonymized source/evidence JSON | [`docs/evidence/`](../evidence/) |
| Manuscript and two aggregate-only figure generators | [paper](../ecology-racehorse-individuality-manuscript-v1.md), [figure code](../../scripts/ecology_rq_manuscript_temporal_figure.py) |
| GitHub Actions original-source/QA jobs | [`.github/workflows/ecology-*.yml`](../../.github/workflows/) |

**Why not move the Python files now?** Many existing imports, tests,
workflows and frozen provenance links assume the current
`scripts/`, `tests/`, and `docs/` locations. This cleanup adds
stable navigation and scientific-status contracts **without breaking
those paths**. Physical code relocation should be a separate
test-validated refactor, not mixed with scientific reanalysis.

The original protocol and historical study logs remain accessible.
All source dates, zero-support groups, missing provenance, absent
verified starters and omitted licensing checks must remain visible.
