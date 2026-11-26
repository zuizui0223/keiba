# Monthly joint common ability: equal-cutoff gain in general first meetings, strict one-start HOLD

26 November 2026. [Frozen protocol](JAPAN_PERIODIC_JOINT_ABILITY_PROTOCOL_20261126.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45788791473) · [aggregate receipt](../evidence/japan-periodic-joint-ability-20261126.json).

All 36 monthly fits and original PR107 calibration/score/denominator parity gates passed. All monthly slopes selected as 2 from 2019, with daily slopes fixed from PR107. Matched pairs connected at month start only.

| Year | Group | Matched/daily-connected | Frozen naive | Frozen online | Joint batch | Actual daily online | Daily surface |
|---|---|---:|---:|---:|---:|---:|---:|
| 2020 | first_both_one_start_one_win | 197/291 | 0.248457355 | 0.248771581 | 0.248663415 | 0.248776634 | 0.249279322 |
| 2020 | first_both_one_win | 39487/41617 | 0.229863319 | 0.224949841 | 0.225810130 | 0.223064092 | 0.222870039 |
| 2020 | first_meeting | 207271/224065 | 0.220308398 | 0.218154701 | 0.216840732 | 0.215241154 | 0.212750739 |
| 2021 | first_both_one_start_one_win | 184/280 | 0.250551239 | 0.250523138 | 0.249858883 | 0.250516585 | 0.247386238 |
| 2021 | first_both_one_win | 42491/44446 | 0.230126494 | 0.226206100 | 0.227032023 | 0.223501621 | 0.222504308 |
| 2021 | first_meeting | 208453/223211 | 0.219595163 | 0.218524012 | 0.216358295 | 0.215603544 | 0.212838055 |

| Year | Group | Joint vs frozen online gain (conditional 97.5%) | Joint vs daily online gain (conditional 97.5%) | Mean abs batch gap | Mean formal lower SD bound |
|---|---|---|---|---:|---:|
| 2020 | first_both_one_start_one_win | 0.000108165 [-0.001674407, 0.002146081] | 0.000113218 [-0.001674606, 0.002160202] | 0.017862485 | 1.280248745 |
| 2020 | first_both_one_win | -0.000860289 [-0.002791533, 0.001233671] | -0.002746038 [-0.004937307, -0.000371770] | 0.352297875 | 0.882312044 |
| 2020 | first_meeting | 0.001313970 [0.000691570, 0.001949570] | -0.001599577 [-0.002786469, -0.000425301] | 0.365208299 | 0.948151081 |
| 2021 | first_both_one_start_one_win | 0.000664255 [-0.001748359, 0.003300673] | 0.000657702 [-0.001749902, 0.003291659] | 0.018023893 | 1.278471807 |
| 2021 | first_both_one_win | -0.000825923 [-0.002895365, 0.001165016] | -0.003530401 [-0.005903427, -0.001494247] | 0.339459685 | 0.881891306 |
| 2021 | first_meeting | 0.002165717 [0.001604329, 0.002709079] | -0.000754751 [-0.001620837, 0.000025539] | 0.364379469 | 0.952026186 |

Primary 2021 strict both exactly one prior recorded start and win: 184 pairs/37 days, gain vs same-cutoff online +0.000664255 and vs actual daily online +0.000657702, both conditional intervals include zero. 2020 strict likewise uncertain. General first meetings: joint vs equal-cutoff online gains positive in both years with intervals excluding zero; actual daily model better in point estimate, with adverse 2020 interval and uncertain 2021 interval. Broader one-win groups: joint vs equal-cutoff online negative point gains with intervals spanning zero; joint vs actual daily online worse in both years with adverse conditional intervals. Do not claim full-network refit is universally better or isolate pure indirect information; objective, penalty, exact recency and update timing differ. Strict score gaps are tiny relative to formal inverse-Hessian SD lower bounds; none exceed 1.96 times that bound. These are curvature diagnostics of a penalized composite likelihood, not calibrated uncertainty or biological variability. Coverage loss is material for strict winners. Conditional day resampling ignores shared horse, graph and fit dependence. Source already inspected; no absolute speed, causal genetics, prospective inference, official career completeness or wagering claim. Next: assess whether earlier recorded-parent group scores provide incremental information on the same daily rating scale, controlling own-history and parent observation counts. No raw export or main merge.

Provenance: source head 45d8013e8cccdcc74137d0ee89a68b763c177992; artifact 15102136211; sha256:0974f14565cac75f9439634316ed0e1917810bf98af849a73bc2f37b39e1a139; metadata and upload-log parity, ZIP bytes not independently extracted.
