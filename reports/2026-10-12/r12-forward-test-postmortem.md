# Kyoto 12R forward-test postmortem

## Frozen predictions

Old top 3, frozen before the result:
1. 14 ビスケットアソート
2. 1 ダイヤモンド
3. 6 メリフルアス

v2 top 3, frozen at 16:05 JST:
1. 16 カネコメファミリー
2. 1 ダイヤモンド
3. 14 ビスケットアソート

v2 broad candidate set:
16, 1, 14, 3, 9, 6

## Official result

JRA official:
1. 10 ビービーシナジー
2. 12 ベラジオリン
3. 9 トゥインクルアップ

Final popularity:
- 10: 7th favorite
- 12: 11th favorite
- 9: 8th favorite

Official result URL:
https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0108202604051220261012%2F4D

## Score

| Metric | Old | v2 |
|---|---:|---:|
| Winner rank | not ranked | not ranked |
| Exact unordered Top 2 | no | no |
| Top-3 recall | 0/3 | 0/3 |

The broader v2 candidate set caught only 9, for 1/3 recall.

**v2 did not improve the forward test.** It had been designed after observing 7-11R, so the 12R failure is evidence against treating the same-day retrospective improvements as validated.

## Root causes

### 1. Winner 10 was excluded because class rise was treated too negatively

The frozen repository note for 10 said:
- Kyoto dirt 1200m untried;
- previous start: Chukyo dirt 1200m maiden win;
- first start after promotion.

JRA history confirms 10 was a lightly raced 3-year-old and had won its immediately preceding start over the same 1200m dirt distance. The system treated "first start in class" mainly as risk and did not represent upward developmental trajectory.

**Fix direction:** class rise is not a negative by itself. For 3-year-olds and lightly raced horses, recent same-distance wins need an explicit upside feature; ideally compare speed/pace-adjusted performance rather than class labels alone.

### 2. Horse 12 exposed an input-completeness defect

The frozen repository note for 12 only emphasized:
- 2026-05-09 Kyoto 1-win dirt 1200m: 7th, 0.8 sec behind.

But a later public history shows:
- 2026-07-04 Kokura 1-win dirt 1000m: 4th, 0.6 sec behind.

That newer same-class run was missing from the pre-race notes. Therefore the ranking was based on an incomplete recent-history summary.

**Fix direction:** before ranking, require a structured latest-N-runs table for every runner with date, class, surface, distance, placing, margin and source. If recency coverage is incomplete, mark DATA_HOLD rather than silently treating missing runs as no evidence.

### 3. Layoff uncertainty was still converted into a rank penalty

9 トゥインクルアップ was retained in the broad set but ranked only fifth in v2 because of roughly a one-year layoff. It finished third.

The policy text said layoffs should widen uncertainty rather than automatically lower expected performance, but the actual frozen ranking still effectively demoted 9 for the layoff.

**Fix direction:** separate predictive mean from uncertainty. A layoff should widen intervals/confidence unless empirical backtests show a systematic mean effect.

### 4. Candidate set was too narrow for an upset race

The final top three were the 7th, 11th and 8th favorites. Market top choices also did not contain the winner/runner-up, so this was a difficult race rather than a model-only miss.

That is not an excuse: a system that is uncertain should **abstain or widen the candidate set**, not output a confident top three.

**Fix direction:** make candidate-set size adaptive to uncertainty and add explicit "upside" candidates (recent winner/class riser, lightly raced improver, recent same-class close finish). Evaluate recall at fixed k as well as coverage efficiency so that simply selecting many horses is not rewarded.

## Statistical interpretation

The earlier 7-11R observations were used to design v2. Therefore those races are training/diagnostic data, not evidence that v2 works.

12R was the first genuinely forward-frozen test and v2 failed. With one forward test, the correct conclusion is:

**There is currently no evidence that v2 improves predictive accuracy over the old system.**

The next version must be frozen before a new race day and evaluated across multiple independent races before claiming improvement.
