# v3.1 holdout — pre-first-race reseal integrity receipt

確認日：2026-10-13 22:23 JST。対象：`zuizui0223/keiba` / `analysis/kyoto-20261012`。

## 結果

**再封印後の凍結ファイル15/15一致、品質tier baseline一致、両ledger参照SHA一致。正式ホールドアウトは0/20。**

- 新manifest Git blob：`783000b048daeec5206625685ed29da41a26a3bf`
- manifest再封印日時：`2026-10-13T22:20:51+09:00`
- 15項目の実ファイルSHAをGitHubから再取得し、`frozen_blobs` と直接照合：差異0
- `data/2026-10-12/v3-quality-tier-map.json` は凍結基準SHAと一致
- `docs/v31-holdout-attempt-ledger.json` の `manifest_blob_sha` は新manifestと一致、eligible attempts 0
- `docs/v31-holdout-ledger.json` の `manifest_blob_sha` も一致、scored races 0

## 22時台の不一致と是正

初回点検時の旧manifestでは15/15一致したが、並行ブランチ更新によりその後4/15が不一致となった。

変更4件：
1. `scripts/v31_holdout.py`：ledger登録時の独立事後検証を必須化（`--result`, `--attempt-ledger`）。
2. `tests/test_v31_holdout.py`：新登録契約への対応。
3. `docs/v31-holdout-operations.md`：新しい必須入力と拒否条件を文書化。
4. `tests/test_v31_pipeline_integration.py`：改変されたscoreをledgerへ受け入れないテストを追加。

いずれも**採点入力の整合性を強制する技術的変更**であり、分類器 `scripts/v31_candidate_channels.py`、候補条件、オッズ窓、対象基準、片側検定のalpha 0.05、候補率上限0.65、freeze成功率下限0.80は不変だった。

初回holdout未実施のため、manifestの `integrity_correction_2` に是正理由を記録した再封印が実施され、両ledger SHAも更新された。本記録はその**最終状態を独立に再照合した**もの。既存の凍結ファイルをこの監査自体では変更していない。

## 注意する科学的境界

- 2026-10-12の派生v3データ83/83の構造PASSは、実データ原資料83頭全件の真実性認証ではない
- 2026-10-12のv3.1候補49/83・Top3 18/18は**既知結果を用いて設計した開発成績**で、予測力の独立検証ではない
- 2026-10-17の予定番組は現行出馬表ではなく、発走15〜25分前の独立freezeが必要
- 事前freezeに失敗したeligible raceは `PRE_RESULT_DATA_FAILURE` としてattempt ledgerに残す。結果を見てから補填しない
- 正式結論は凍結された20レースの条件でのみ判定。途中のスコアでv3.1を改善済みと呼ばない

## 次の固定運用

2026-10-15 17:00準備、2026-10-17は京都R7 12:55／R8 13:25／R10 14:30／R11 15:10／R12 15:55に事前freezeを試行、16:50以降に結果検証・採点、17:20にfail-safe監査。これらの自動タスクは既に設定済みであり、重複作成しない。

旧状態の点検：[v31-preflight-readiness-2217.md](v31-preflight-readiness-2217.md)。新状態のmanifestとledgerは `docs/` 直下を参照。

本監査はGitHub上の現在blob SHAとledger JSONを直接照合したもので、リポ全体のPythonテストを再実行したものではない。
