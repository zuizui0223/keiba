# Racing Queensland実GPS 12開催日の独立REML再検証（2026-10-26）

**観測データ：Racing Queensland、Cannon Parkの元の固定12開催日・レース1〜8。回顧的・ソース版に依存。** 元の馬ID・馬名・GPS区間時間・騎手ID等は公開コミットせず、GitHub Actions runner内で解析し匿名集計だけを残す。

## 実データの肯定的結果と母数

[1回目実データ計算](https://github.com/zuizui0223/keiba/actions/runs/40288058032)・[別の独立したソース再取得](https://github.com/zuizui0223/keiba/actions/runs/40288342917)・[開催日除外感度](https://github.com/zuizui0223/keiba/actions/runs/40289136170)。

| 指標 | 数値 |
|---|---:|
| 元の固定12開催日の取得成功 | **12/12** |
| 公式HORSES ID × 初期GPS候補行 | **526** |
| 4頭以上で初GPSが観測された区間行・レース | **503行・74競走** |
| 異なる公式HORSES ID | **262** |
| 2日以上GPS測定されている馬ID | **134** |
| race-fixed独立Helmertコントラスト次元 | **429** |
| 既存main SciPy REMLの同一データICC | **0.434811151749** |
| 新NumPy REMLの同一データICC | **0.434811154870** |
| 数理実装間ICCの絶対差 | **約3.12×10⁻⁹** |
| 馬間分散 | **0.0414849814 秒²** |
| 条件付き絶対初区間時間残差分散 | **0.0539242116 秒²** |
| 第2回の独立ソース再取得からのICC | **0.434811174679** |
| 1日除外で12回再推定 | **12/12実行可能** |
| 日付除外時のICC最小～最大 | **0.391841～0.505077** |

同じ原公式GPSデータを2つの独立した数値アルゴリズムに入力すると、分散成分とICCが数値的に一致した。これは実測に基づく**方法論的な肯定的結果**であり、複数日で馬の個体IDに関連する変動が存在することへの探索的観測支持でもある。ただし再取得2回は新しい独立馬コホートではない。日付削除幅は推定の感度であり95%信頼区間ではない。

## 10月14日の元source版とは完全一致しない

元の[10月14日の12日永久source fingerprint](https://github.com/zuizui0223/keiba/blob/main/docs/evidence/rq-cannon-original-source-fingerprints-20261014.json)では元HORSES ID×GPS候補は543行、今回の再取得は526行（純差−17）。全12日のGetMeetingsForDate XML、GetRacesForMeeting XML、初GPS CSVの原SHAは一致する一方、**9/12日**のGetHorsesForRace原馬名簿の結合SHA、**7/12日**の正GPS候補行数が異なる。**全項目一致は3/12日だけ**。馬の死亡や個体行動の変化を意味せず、ソース名簿の版違いにより適格な母数が変更された。

元のsource版でのICC約0.430147を完全再現したとは主張しない。最新のICC約0.434811は今回の元馬名簿版に条件づく別の回顧的観測値。原版12/12完全一致の科学ゲートは**HOLD**なので、GitHub Actionsの判定も意図的に失敗となる。これは実測REML計算や数理実装のエラーとは異なる。

## 実測12日を1日ずつ削除して再計算した結果

全12回のsource開催日除外でREMLが数値的に推定可能で、ICCが0.391841から0.505077となった。一つのsource日だけに依存していた結果ではない。ただし元GPS欠測・class・距離マーカーの混在、出走選択、騎手・調教の交絡などは未解決で、先天的なpersonalityや行動生態学的な適応は同定していない。全て回顧的、選ばれたsourceデータに限る。

## 実装・境界

[匿名集計実装](../../scripts/keiba_rq_real_source_reml_replay.py)は、既存の元12日source collectorと、生態学mainのrace-fixed REMLをSHA固定取得し、最新のPR #26の数理式と同じレース・馬ID・absolute first-GPS区間に適用する。[HOLDを担保する人工テスト](../../tests/test_keiba_rq_real_source_reml_replay.py)は元コホート日付1個の欠測、馬名簿/SHA改変、数学的一致、漏洩防止を検査する。

元の初期市場オッズを読んでいないので**Racing Queensland馬とJRA別馬番を同一視しない**。当時の出走直前に今日再取得したGPSが利用できたと偽らない。馬ABM/PDE・投票者ABMの係数の実馬への校正、リアルな社会的追随、臨界オッズ、馬券の正の期待値はすべてHOLD。

**今回の科学的結論：** 実測Racing Queensland GPSの同一馬IDに条件付きの反復性が見られ、異なるREML実装と全source日除外感度でもモデル上の個体間成分が残る。元source版の更新と異なる距離マーカーによる非比較性は、定量的に明記して今後の実測研究を進める。
