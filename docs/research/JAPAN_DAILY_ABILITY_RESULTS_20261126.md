# Day-updated common ability: improvements on one-win horses, strict one-start HOLD

26 November 2026. [Frozen protocol](JAPAN_DAILY_ABILITY_PROTOCOL_20261126.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45780051832) · [aggregate log receipt](../evidence/japan-daily-ability-20261126.json).

Source parity passed; 550,062 classified JRA starts /62,199 horses across 2010–2021. Ratings updated after entire calendar day. 2019 slope 2 for all three models. Two predeclared 2021 contrasts supported: daily network vs naive among connected first meetings of one-recorded-win horses, and surface model vs daily network among all connected first meetings. Separate daily and annual fits/denominators prevent interpreting their score difference as an isolated update-frequency effect.

| Year | Group | Pairs | Naive Brier | Daily global | Daily surface | Global gain (conditional 97.5%) | Surface gain (conditional 97.5%) |
|---|---|---:|---:|---:|---:|---|---|
| 2020 | all_connected | 258677 | 0.218275826 | 0.215839439 | 0.213378483 | 0.002436387 [0.001886129, 0.002931957] | 0.002460955 [0.002005304, 0.002934393] |
| 2020 | first_meeting | 224065 | 0.218046547 | 0.215617605 | 0.213018155 | 0.002428941 [0.001887670, 0.002959163] | 0.002599450 [0.002073820, 0.003106173] |
| 2020 | first_both_one_win | 41617 | 0.228234568 | 0.222901991 | 0.222501100 | 0.005332577 [0.003042543, 0.007184595] | 0.000400891 [-0.001074145, 0.001740922] |
| 2020 | first_both_one_start_one_win | 291 | 0.249317035 | 0.249497493 | 0.249924519 | -0.000180458 [-0.000556157, 0.000095022] | -0.000427026 [-0.002896035, 0.002080038] |
| 2020 | first_naive_tie | 29 | 0.250000000 | 0.249731626 | 0.245077344 | 0.000268374 (HOLD support) | 0.004654282 (HOLD support) |
| 2021 | all_connected | 257284 | 0.216951460 | 0.215530105 | 0.212749672 | 0.001421356 [0.000900249, 0.001897691] | 0.002780433 [0.002382081, 0.003163432] |
| 2021 | first_meeting | 223211 | 0.217062983 | 0.215729196 | 0.212867359 | 0.001333787 [0.000813178, 0.001845491] | 0.002861837 [0.002414772, 0.003311931] |
| 2021 | first_both_one_win | 44446 | 0.227777814 | 0.223228242 | 0.222233662 | 0.004549572 [0.002634581, 0.006613113] | 0.000994580 [-0.000230122, 0.002290429] |
| 2021 | first_both_one_start_one_win | 280 | 0.251013043 | 0.250903927 | 0.248576468 | 0.000109117 [-0.000262558, 0.000387937] | 0.002327459 [-0.000099031, 0.005213851] |
| 2021 | first_naive_tie | 17 | 0.250000000 | 0.250598652 | 0.244838056 | -0.000598652 (HOLD support) | 0.005760596 (HOLD support) |

2021 primary one-win daily gain 0.004549572 [0.002634581,0.006613113], accuracy 0.620310 to 0.633841; surface increment on this subgroup uncertain. Primary all-first surface increment 0.002861837 [0.002414772,0.003311931], also positive in 2020. Strict first both exactly one recorded start and win: coverage 291/330 (2020), 280/301 (2021), vs annual model 24/330 and 18/301. Neither strict daily-network vs naive nor surface vs global interval excludes zero in either year. No proof of useful ability differentiation after one start. Online updates do not transfer a later opponent's new evidence back to the inactive focal horse. The next distinct test adds prior-opponent post-encounter rating innovations, strictly pre-day, to the fixed daily score and separately checks an alternative-opponent control. Classified finishers only, not complete official career wins or entry list. Conditional day intervals omit repeated horse and graph-fit dependence; no genetic, physiological, causal or prospective claim. No raw export or main merge.

Provenance: head 6c38cb57fc593faedecb86f60262d42fe5ffddf5; artifact 15098181496; sha256:745c840a921f0e5e482138299507ae4373f01d8de432740abf2f26e2b1c3946f; metadata and upload-log parity only, not independent ZIP extraction.
