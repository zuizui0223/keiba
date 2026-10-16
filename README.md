# keiba

## 2026-10-17 京都：公式カードとの照合（事前準備、holdout未実施）

2026-10-15にJRA公式出馬表と59頭の公式プロフィールを照合した結果と過去履歴733行を、[木曜監査・訂正JSON](docs/v31-prep-2026-10-17-thursday-correction.json)と[過去履歴キャッシュ](docs/v31-prep-history-2026-10-17/)に保存しました。元の凍結 manifest・判定実装・試行台帳・スコア台帳は変更していません（attempt 0 / scored 0）。

**重要：** 京都8Rは「もみじステークス、2歳限定・芝1400m」であり、v3.1の `exclude_2yo_only` によりholdout対象外です。旧来の[10/17 v3.0-alpha暫定予定](configs/v3-next-test-20261017.json)には、8Rを3歳以上・ダート1400m、9Rをもみじステークスとする正式出馬表とは一致しない記載があります。この旧予定を正式レース条件として使わないでください。予測の凍結・馬番・取消・実オッズは、各対象レース発走前に**最新のJRA公式出馬表を新規取得・再照合**して初めて確定します。過去履歴キャッシュはfreeze・結果採点ではありません。


京都競馬の過去実績と中間オッズを、出典・時刻付きで比較するための分析リポジトリです。

## 2026年10月12日：11R結果照合・残差監査

11RスワンSの確定結果を、事前予測を改変せずに事後照合しています。

- [結果スナップショット](data/2026-10-12/r11-result-postrace.json)
- [予測→結果→説明済み残差→未説明残差の監査](reports/2026-10-12/r11-postrace-residual-audit.md)
- [発走前15:03時点の凍結分析](reports/2026-10-12/r11-focused-analysis-1503.md)
- [9R・10Rの結果スナップショット](data/2026-10-12/r9-result-postrace.json) / [10R](data/2026-10-12/r10-result-postrace.json)
- [9R・10Rの候補抽出・順位・券変換・状態残差の監査](reports/2026-10-12/r9-r10-postrace-residual-audit.md)
- [12Rで結果前に凍結したv2予測](reports/2026-10-12/v2-prerace-12r-1605.md)
- [12R公式結果スナップショット](data/2026-10-12/r12-result-postrace.json)
- [12R v2前向き検証：改善未確認と残差分析](reports/2026-10-12/r12-v2-forward-validation.md)
- [v3.0候補生成プロトコル（開発版・prospective検証には使用しない）](docs/v3-candidate-generation-protocol.md)
- [R7〜R12を使ったv3開発監査](reports/2026-10-12/v3-candidate-channel-development-audit.md)
- [v3開発指標JSON](reports/2026-10-12/v3-development-metrics.json)
- [83頭のv3.0完全機械判定](reports/2026-10-12/v3-mechanical-channel-audit.json)
- [v3.0結果照合（開発データのみ）](reports/2026-10-12/v3-mechanical-development-evaluation.json)
- [v3.0候補過多とv3.1縮約案](reports/2026-10-12/v3-mechanical-audit-and-v31-proposal.md)
- [83頭の全履歴正規化入力](data/2026-10-12/v3-normalized-prerace-history.json)
- [Q判定のquality tier map](data/2026-10-12/v3-quality-tier-map.json)
- [再現スクリプト](scripts/v3_candidate_channels.py) / [テスト](tests/test_v3_candidate_channels.py)
- [v3.1 holdout用プロトコル](docs/v31-candidate-generation-protocol.md)
- [v3.1 freeze manifest](docs/v31-holdout-freeze.json)
- [v3.1 score ledger（20レース、現在0/20）](docs/v31-holdout-ledger.json)
- [v3.1 eligible-attempt ledger（現在0件）](docs/v31-holdout-attempt-ledger.json) / [登録ツール](scripts/v31_attempt_ledger.py)
- [v3.1 formal decision contract（20レース時点のみ）](docs/v31-holdout-decision-contract.json)
- [v3.1 exact holdout evaluator](scripts/v31_evaluate_holdout.py) / [テスト](tests/test_v31_evaluate_holdout.py)
- [v3.1 residual audit protocol（formal decisionとは分離）](docs/v31-residual-audit-protocol.md)
- [v3.1 未説明残差の証拠ワークブック](scripts/v31_residual_workbook.py) / [運用手順](docs/v31-residual-workbook-usage.md) / [テスト](tests/test_v31_residual_workbook.py)
- [v3.1 holdout運用手順](docs/v31-holdout-operations.md)
- [v3.1自動運用スケジュール（10/15前処理→10/17 freeze→score/register）](docs/v31-automation-schedule.md)
- [次のholdout候補（10/17京都、#1候補はR7 13:15）](docs/v31-next-holdout-plan.md)
- [freeze / score / ledger wrapper](scripts/v31_holdout.py) / [テスト](tests/test_v31_holdout.py)
- [freeze契約の独立検証](scripts/v31_verify_freeze.py) / [integrityテスト](tests/test_v31_freeze_integrity.py)
- [JRA snapshot→race-input/odds前処理](scripts/v31_prepare_snapshot.py) / [テスト](tests/test_v31_prepare_snapshot.py)
- [独立した結果後の改変・SHA・計算照合](scripts/v31_validate_postrace.py) / [実分類器による全工程の通しテスト](tests/test_v31_pipeline_integration.py)
- [v3.1判定スクリプト](scripts/v31_candidate_channels.py) / [11テスト](tests/test_v31_candidate_channels.py)
- [v3.1機械判定（結果未使用）](reports/2026-10-12/v31-mechanical-channel-audit.json)
- [v3.1開発データ照合](reports/2026-10-12/v31-development-evaluation.json)
- [v3.1 vs 同候補数の市場人気順（副次評価プロトコル）](docs/v31-equal-market-shadow-protocol.md) / [比較スクリプト](scripts/v31_equal_market_shadow.py) / [テスト](tests/test_v31_equal_market_shadow.py)
- [R7〜R12の同候補数市場比較・再現用JSON](reports/2026-10-12/v31-equal-market-development.json)

開発データR7〜R12では、v3.1の候補49/83頭でTop3 18/18に対し、まったく同じ49頭を各レースの凍結時点の単勝人気順で選ぶだけでも17/18を捕捉しました。v3.1の市場順位に対する純増はR8⑦の1頭のみです。これはin-sampleの診断であり、未来への優位性を示しません。未来20レースでも同候補数の市場人気順を副次的に比較しますが、事前に固定した正式PROMOTE条件は変更しません。

事前フォーカスは9→1→13→14、確定上位は1→4→9→8。本線ワイド1–9は的中したが、評価は的中可否ではなく残差の種類で行います。4スズハロームは同距離履歴の未解消と上がり性能の特徴量欠落、8サンダーストラックは1600→1400の距離移植性、14ワイドラトゥールは市場順位11位に対し事前フォーカス4位だったモデル固有の過大評価として分離しました。

予測時の `kyoto_11.json` は事後に上書きしません。次回以降は、重要候補の履歴完全性、上がり3F、位置取りとの交互作用、距離移植性、当日状態を別に扱う方針です。

12Rでは、結果前16:05に凍結したv2 Top3 `16,1,14` に対し、確定上位は `10,12,9`。旧Top3もv2 Top3も実Top3 recall 0/3、広い候補集合も1/3で、v2の改善はこの1レースでは確認できませんでした。実Top3は7・11・8番人気で市場Top6も0/3だったため、v3では市場baselineだけでなく、昇級直前勝ち・少キャリアの上方不確実性・隣接短距離の改善を独立候補チャネルにします。

R7〜R12の開発データでは、凍結pre-race win oddsだけのMチャネルは22/83頭を候補にしてTop3 11/18（61.1%）、旧qualitative marksは38/83頭で15/18（83.3%）。全83頭のJRA全履歴を機械判定するとv3.0は18/18を拾う一方、候補が64/83頭（77.1%）まで膨らみました。v3.1はCを直近1走へ限定し、K/Qを強化、GII/GIではQ1∩K1のみを救済にして49/83頭（59.0%）まで縮約しました。R7〜R12での18/18は設計に使ったin-sample結果であり予測精度の証拠ではありません。v3.1は2026-10-13 22:20:51 JSTに、snapshot preparerのGit blob SHA計算バグ修正に加え、score ledger登録時の独立した結果後検証を必須化して再sealしました。科学的閾値や正式判定条件は変更していません。classifier・snapshot preparer・holdout wrapper・exact evaluator・attempt ledger契約に加え、独立した結果後照合ツールもSHA固定しています。**score ledger登録時には公式result・score・freeze・FROZEN attemptの四者照合が必須**で、改変scoreは登録を拒否します。holdout対象は**京都の平地・1勝クラス以上・2歳限定以外**に固定し、このseal後のeligible raceを時系列で全件attemptします。現在はscore ledger 0/20、attempt ledger 0件です。各eligible raceはfreeze成功ならFROZEN、事前データの技術的失敗ならPRE_RESULT_DATA_FAILUREとしてattempt ledgerに残し、成功したレースだけをscoreします。20/20到達時のPROMOTEには、同数ランダム追加に対する片側exact p≤0.05、全候補率≤0.65、20件目のFROZENまでのfreeze成功率≥0.80の**3条件すべて**が必要です。途中成績では正式判定しません。次の開催予定では10/17京都7R（13:15、3歳以上1勝クラス・ダ1800m）が最初の候補ですが、現行出馬表と時刻付きオッズを確認するまではfreezeしません。

## 2026年10月12日：8〜12Rの全8券種（主要候補を13:41〜13:42再確認）

**実績を加味した1点は11Rワイド9–14。価格比較では9R枠連4–7、10R枠連2–5を確認。**

- [各レースの買い方・京都と騎手の実績・100円単位の配分](reports/2026-10-12/remaining-guide.md)
- [主要候補の13:41〜13:42再確認記録](reports/2026-10-12/remaining-final-price-check.json)
- [30ページの取得オッズと時刻](data/2026-10-12/remaining-snapshots/)
- [844件の同条件比較・全結果をカバーする配分計算](reports/2026-10-12/remaining-market-analysis.json)
- [馬単を両順買う100円単位の比較](reports/2026-10-12/remaining-integer-comparisons.json)
- [馬と騎手の組み合わせ・騎手の京都コース成績](reports/2026-10-12/remaining-horse-jockey-evidence.json)

保存した中間価格での比較です。馬の選択は定性判断で、検証済み的中確率や市場全体の確実な利益を主張しません。全8券種を比較していますが、3連単と一部3連複は部分取得です。表の買い目は代替案であり、全点を同時購入する提案ではありません。

```bash
python -B scripts/analyze_remaining_markets.py
python -B scripts/compare_remaining_integer_stakes.py
```

前者はNumPy・SciPy、後者はPython標準ライブラリを使用します。

## 2026年10月12日：初回の7R以降の買い方案（12時台の保存値）

**1点なら11Rワイド9–14。複数なら10R 2–4、11R 9–14、12R 1–14を各100円、計300円。**

これは保存した京都実績、近走、クラス、休養、表示オッズを照合した定性判断です。学習済みモデルや検証済みの的中確率はありません。

- [絞った買い方・理由・収支](reports/2026-10-12/recommendations.md)
- [全95頭の実績比較と候補券の収支](reports/2026-10-12/report.md)
- [計算結果・入力SHA-256・根拠URL](reports/2026-10-12/analysis.json)
- [分析範囲と扱い方](docs/analysis-design.md)

全頭比較は6〜12Rを保存していますが、上記は12時台に作成した記録です。8R以降の追加分析は冒頭のremaining-guide.mdを参照してください。

## 再現

基本分析と券種間の価格比較はPython標準ライブラリのみを使用します。Python 3.12.14で確認しました。

## 7R：全8券種・京都実績・騎手との相性

- [具体的な買い方と判断根拠](reports/2026-10-12/r7-all-bets.md)
- [取得1,119券の中間オッズと更新時刻](data/2026-10-12/r7_markets.json)
- [同じ的中条件を買う価格比較](reports/2026-10-12/r7-price-comparison.json)
- [全3,360結果をカバーする配分計算](reports/2026-10-12/r7-coverage-lp.json)
- [馬と今回の騎手のコンビ履歴](reports/2026-10-12/r7-partnership-evidence.json)
- [騎手の京都ダート1,900m成績と集計期間](reports/2026-10-12/r7-jockey-evidence.json)

取得券の保存オッズを固定し、連続金額で全結果の最低払戻を最大化すると、購入額の88.28%でした。これは的中予測・期待利益の最適化ではありません。3連複と3連単は部分取得で、時刻も混在しています。100円単位の購入配分や実際の変動払戻を保証する計算ではありません。

```bash
python scripts/compare_r7_markets.py
python -B scripts/r7_coverage_lp.py
```

後者のみNumPyとSciPyが必要です。NumPy 2.3.5、SciPy 1.17.0で計算し、全結果の払戻と主問題・双対問題の差を検証しました。

## 8R：13:44更新の全券種比較

- [8Rの具体的な買い方・全11頭の見立て・騎手との相性](reports/2026-10-12/r8-all-bets.md)
- [全8券種838券・13:44更新値と公開HTMLのSHA256](data/2026-10-12/r8_markets_latest.json)
- [全990結果の払戻最適化・同一条件の券種比較・100円刻み配分](reports/2026-10-12/r8-coverage-latest.json)
- [馬と今回騎手の全履歴](reports/2026-10-12/r8-partnership-evidence.json)
- [騎手の京都芝2000m同期間集計](reports/2026-10-12/r8-jockey-evidence.json)

馬連5–11を個別の第一候補とし、3連複5–9–11を任意の追加候補にしています。価格監視で枠連1–8の包含優位と旧馬単配分の優位が消えた点を反映しました。オッズだけで正の期待値や的中確率は主張しません。後続レースの少点数案との重ね買いは前提にしません。

```bash
python -B scripts/r8_coverage_lp.py --input data/2026-10-12/r8_markets_latest.json --output reports/2026-10-12/r8-coverage-latest.json
```

前の価格は別snapshotに保存しています。13:44の8R入力は全市場が同じ表示更新時刻ですが、購入時にオッズが固定されるわけではありません。3連単は400/990通りの部分取得です。

### 基本分析の再現

```bash
python scripts/analyze.py --as-of 2026-10-12T12:44:35+09:00
python scripts/calculate_plans.py --as-of 2026-10-12T12:54:11+09:00
python -m unittest discover -s tests -v
```

入力は `data/2026-10-12/kyoto_06.json`〜`kyoto_12.json`、出力は `reports/2026-10-12/report.md` と `analysis.json` です。recommendations.mdはその計算結果を踏まえた定性判断の記録で、自動ランキングの出力ではありません。calculate_plans.pyは保存した追加オッズを反映して、1点・3点・4点案の収支を[plan-calculations.json](reports/2026-10-12/plan-calculations.json)に出力します。

別の時刻で候補の有効性とオッズの古さを計算する例：

```bash
python scripts/analyze.py --as-of 2026-10-12T13:20:00+09:00 --output reports/recheck-1320
```

この操作でオッズ自体は更新されません。入力ファイルの更新時刻と取得時刻を確認してください。全頭比較レポートでは9Rのワイドは11:53、10Rは12:31、11Rは12:24、12Rは12:36の保存値です。絞った買い方には追加取得した12Rの12:42更新値を反映し、[追加オッズ記録](reports/2026-10-12/odds-checkpoint.json)に残しています。

## 計算の意味

- 京都通算は当該レースの芝またはダートのみ。同距離成績は通算と区別します。
- 過去の3着以内率を今日の的中確率に置き換えません。未確認値や0戦を0%と表示しません。
- 必要的中率 `1 / オッズ下限` は1券の損益分岐点であり、推定的中率ではありません。
- 払戻の試算には中間オッズ下限を使用し、収支は選択した全券の購入総額を引きます。
- 同じ馬を軸にするワイドは独立した賭けではありません。通常の同着なしの3着以内を列挙し、同時的中の上限を計算します。
- 発走2分前から新規候補を除外します。実際の販売締切を保証するものではありません。
- 15分を超えるオッズは「要更新」と表示します。これは運用上の目安です。

## オッズ監視

依頼に基づくChatGPTの監視は、本日13:20、14:20、15:20、16:20 JSTの4回です。ワイド下限の20%以上の変化、軸馬の取消・除外、発走30分以内を通知条件にしています。

スクリプト自体はネットワーク取得や常駐監視を行いません。監視の実行間隔は1時間で、発走直前の取得を保証しません。実際の馬券購入は行っていません。
