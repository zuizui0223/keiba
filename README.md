# 🐎 keiba — Racehorse behavioral ecology & odds-methods research

**中心テーマは、競走馬の個体差を生態学的に検証すること。**
公開された元の馬IDとGPS区間データを使い、
同じ馬の過去の走り方が後の走り方をいつ説明できるか、
そして環境・競争相手・時間を越えて一般化できるかを調べます。

**馬券・オッズの予測は別系統です。** 収益モデルや
勝率の証明を、生態学的な個体差の根拠に使いません。

## 入口を2つに整理

| 研究領域 | 最初に読む資料 | 内容と状態 |
| --- | --- | --- |
| **① 生態学研究（メイン）** | **[Research start here](docs/research/README.md)** | 元のRacing Queensland競走馬ID、GPS区間の反復性、時系列予測、H1/H2の識別上の限界 |
| **② 馬券・オッズ解析（別トラック）** | [Betting methods & archive](docs/betting/README.md) | JRAレース・券種間の表示オッズ比較、v3.1候補生成と未完了の前向き検証 |

## 生態学研究の現在地（2026-10-18）

| 確認できたこと | 現時点で言えないこと |
| --- | --- |
| Cannon Parkの元資料36馬ID・後続46記録で、**その馬自身の過去の初期GPS相対タイム履歴**（RMSE 0.255809秒）が、同条件の**他馬履歴**（0.303195秒）より後続記録を説明した | 先天的な「性格」・遺伝率・実際の騎手変更の因果効果 |
| Doombenでは別々の年内・年越し解析で正負の予測結果が得られた | **同じ馬の個体性が年越しで弱まった**という解釈。両方を評価できた同一馬は元資料条件下で**0頭** |
| 馬場と送信元名簿の反復・欠測状況を監査し、H1とH2の解析方法をシミュレーションで検証した | **H1：馬×馬場の反応規範、H2：他馬との因果的相互作用**。実馬の必要な反復・確定出走・完走タイム情報が不足し、科学的に**HOLD** |

**重要：これらは特定の出典・観測対象・計測区間に
条件づけられた探索的結果です。** 独立した因果実験、
適応進化、馬券の的中確率を実証したものではありません。

研究の詳細と根拠：
[**証拠・HOLDの一覧**](docs/research/EVIDENCE_MATRIX.md) ・
[英語論文初稿（未投稿）](docs/ecology-racehorse-individuality-manuscript-v1.md) ・
[元資料の再現・検証手順](docs/research/REPRODUCIBILITY.md) ・
[次の検証計画](docs/research/ROADMAP.md)。

## リポジトリ構成

| 場所 | 用途 |
| --- | --- |
| [`docs/research/`](docs/research/) | **生態学の問い・証拠マトリクス・再現・次の実験** |
| [`docs/betting/`](docs/betting/) | v3.1予測・券種とオッズ分析の案内 |
| [`docs/ecology-*.md`](docs/) | 研究デザイン、個別の原資料監査、HOLDの一次記録 |
| [`docs/evidence/`](docs/evidence/) | 元資料の匿名集計・ハッシュ（原馬名・個体ごとのGPS値は含めない） |
| [`scripts/ecology_*.py`](scripts/) | 生態学解析と合成データの反証試験 |
| [`scripts/v31_*.py`](scripts/) | 馬券用の凍結済みv3.1候補抽出・評価 |
| [`tests/`](tests/) | 生態学（`test_ecology_*`）と馬券を分けて検証 |
| [`reports/`](reports/)・[`data/`](data/) | 日付ごとのJRA予測・取得時点の価格・事後監査 |
| [`docs/archive/`](docs/archive/) | 整理前の長いREADMEを証拠・作業履歴として保存 |

**既存のPython・データ・研究デザインファイルは移動していません。**
過去のimport、資料リンク、SHA固定された予測コードを壊さず、
まず入口と科学的な状態の区別を整理しました。

### ローカル検証

```bash
# リポジトリ内の研究・馬券・履歴リンクと状態を確認
python scripts/check_repository_navigation.py

# 生態学の合成/元資料対応テスト（下記依存パッケージが必要）
python -m pip install 'numpy>=1.26,<3' 'pandas>=2,<3' 'scipy>=1.11,<2' 'statsmodels>=0.14,<0.15'
python -m unittest discover -s tests -p 'test_ecology_*.py' -v

# 別に保存した馬券側の回帰テスト
python scripts/run_non_ecology_tests.py
```

## 作業履歴と現時点の制限

[**整理前の長いREADME全文**](docs/archive/README-main-before-reorganization-20261018.md)と
[元の生態学研究ログ](ECOLOGY_RESEARCH.md)を保持しています。
過去のオッズや買い目は**その取得時点の記録**であり、
今の価格・検証済みの勝率を示しません。

GitHubの生態学PR #2は**2026-10-16にマージ済み**。
秋華賞の別系統のオッズ監査は
[Draft PR #5](https://github.com/zuizui0223/keiba/pull/5)
にあり、**このREADMEの整理で馬券予測の基準値を変えません**。

現在の生態学的結論や研究の出典に関する質問は、
まず[研究インデックス](docs/research/README.md)を参照してください。
