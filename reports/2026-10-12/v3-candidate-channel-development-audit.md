# v3.0 candidate-channel development audit: Kyoto R7-R12

This is a **development / retrospective** audit. v3.0 was designed after seeing these race outcomes. Therefore this file is not evidence of prospective predictive performance.

The prospective protocol is frozen separately in `docs/v3-candidate-generation-protocol.md`.

## Baselines from frozen pre-race data

Across Kyoto R7-R12 there were 83 starters and 18 top-three finishing slots.

### M-only baseline

Using the frozen pre-race win odds in `kyoto_07.json` through `kyoto_12.json`, channel M selects the top quarter of each field, minimum 3 and maximum 5, including cutoff ties.

| R | Field | M candidates | Actual top3 | M hits |
|---|---:|---|---|---|
| 7 | 16 | 11,2,15,12 | 2,15,9 | 2,15 |
| 8 | 11 | 9,5,11 | 9,1,7 | 9 |
| 9 | 12 | 12,10,4 | 4,3,12 | 4,12 |
| 10 | 10 | 5,2,9 | 5,2,9 | 5,2,9 |
| 11 | 18 | 9,1,18,15,13 | 1,4,9 | 1,9 |
| 12 | 16 | 3,16,8,9 | 10,12,9 | 9 |

M-only:
- candidates: **22 / 83 = 26.5% of starters**
- top-three hits: **11 / 18 = 61.1%**

This is the correct baseline for the claim “use the market as a baseline”, not a claim that the market alone is sufficient.

### Old qualitative marks

The original frozen marks selected:

- R7: 2,5,7,9,12,15
- R8: 1,3,5,7,9,11
- R9: 3,4,5,7,10,12
- R10: 2,4,5,7,9,10
- R11: 1,6,9,10,13,14,17,18
- R12: 1,3,6,9,14,16

Across all six races:
- candidates: **38 / 83 = 45.8%**
- top-three hits: **15 / 18 = 83.3%**

So the old qualitative process added substantial recall over M-only, but still missed:

- R11 #4 スズハローム
- R12 #10 ビービーシナジー
- R12 #12 ベラジオリン

Those three misses are the direct development targets for v3.0.

## Would the frozen v3.0 channel definitions rescue the old misses?

Yes, on this development sample.

### R11 #4 スズハローム — Q / K

Pre-race information available before the result included:

- recent Listed win at Kyoto 1600m;
- recent GIII win at 1600m;
- prior Kyoto 1400m win;
- prior GII 1400m third.

For a 1400m target, 1600m is within the ±20% distance band.

Therefore:
- **Q quality-transfer channel: yes**
- **K course/adjacent-distance specialist: yes**

This addresses the earlier failure caused by exact-distance emphasis and incomplete `kyoto_distance_record`.

### R12 #10 ビービーシナジー — U

Before R12:
- age 3;
- only 3 career starts;
- most recent start was a win;
- that win was on dirt 1200m, exactly the target distance.

Therefore:
- **U young class-riser / sparse-career growth: yes**

This is the canonical reason U exists.

### R12 #12 ベラジオリン — C

Before R12, the full pre-race history included:

- latest start: 1-win class, dirt 1000m, 4th;
- previous relevant runs: 1-win dirt 1200m 7th and 5th;
- target: 1-win dirt 1200m.

Dirt 1000m lies within ±20% of 1200m, and latest finish was 4th.

Therefore:
- **C recent same-class / adjacent-distance form: yes**

This addresses the earlier summarization error where one Kyoto 1200m seventh was given more weight than the sequence of recent short-distance class form.

## Top-three channel map on the development races

This table only asks whether each actual top-three horse had at least one v3 channel using pre-race information. It does not measure false positives.

| R | Finish | Horse | Development-time v3 channel(s) |
|---|---:|---|---|
| 7 | 1 | 2 アレンスター | M, K |
| 7 | 2 | 15 ジーティーアメリカ | M, C |
| 7 | 3 | 9 エイユーファイヤー | C, K |
| 8 | 1 | 9 レゼルフォート | M, U |
| 8 | 2 | 1 エレガンシア | C |
| 8 | 3 | 7 レーヌマロン | K |
| 9 | 1 | 4 ソルチェリア | M, C, K |
| 9 | 2 | 3 クロノスバレット | C |
| 9 | 3 | 12 テイエムサンレーヴ | M, K |
| 10 | 1 | 5 アクセス | M, U |
| 10 | 2 | 2 カムアップローゼス | M, C |
| 10 | 3 | 9 ミリタリータトゥー | M |
| 11 | 1 | 1 ダイヤモンドノット | M / quality-distance evidence |
| 11 | 2 | 4 スズハローム | Q, K |
| 11 | 3 | 9 オフトレイル | M, K, Q |
| 12 | 1 | 10 ビービーシナジー | U |
| 12 | 2 | 12 ベラジオリン | C |
| 12 | 3 | 9 トゥインクルアップ | M, C |

Under the v3.0 definitions, all 18 observed top-three horses have at least one plausible channel on this **development** set.

That is useful as a design sanity check, but it is exactly the kind of result that can be produced by post-hoc rule design. It must not be reported as “100% prediction accuracy”.

## What is not yet known

The full v3 candidate-set fraction has **not** been computed for all 83 horses because the existing frozen JSON does not normalize last-three class/distance histories for every horse. Many records are compressed into free-text notes or `null` same-distance fields.

Therefore we do not yet know whether v3 obtains this retrospective recall with:

- 35% of the field,
- 50%,
- 70%,
- or nearly every horse.

That coverage cost is critical.

The next implementation task is to normalize the last-three pre-race starts for every horse and compute M/C/U/Q/K membership mechanically.

## Why v3.0 ranking is intentionally not fitted now

R10 would push ranking toward market order.  
R12 would push it away from market order.  
R11 would push toward quality-transfer and closing ability.

Fitting weights to these six races would simply encode the outcomes we have already seen.

So v3.0 freezes candidate generation first and leaves ranking largely market-baseline until prospective data accumulates.

## Holdout success criteria

For the next 20 races, do not change channel thresholds.

A useful v3 result would require both:

- top-three recall higher than M-only;
- broad-set fraction materially below 100%.

Report both numbers every time.

A channel is especially valuable when it produces a **unique rescue**: a top-three horse absent from M but present in that channel.

The three development examples motivating this are:

- Q/K → R11 #4
- U → R12 #10
- C → R12 #12

## Development conclusion

The current evidence supports the following narrow claim:

> The previous system already had strong broad-candidate recall (15/18 top-three slots) but failed on three horses whose pre-race histories represent three distinct information types: adjacent-distance quality, lightly raced class-rise growth, and recent same-class adjacent-sprint form.

v3.0 encodes those information types explicitly and is now frozen for future holdout testing.
