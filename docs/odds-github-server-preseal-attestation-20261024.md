# SHAだけをGitHub側へ事前提出するWIN/WIDE予測の外部時刻証明

**2026-10-24 — 実装済み・本番未稼働。実競馬での事前コミットメントはまだ0件。**

## 解決する問題

従来のローカル予測封印は、予測のSHA256が一致するかどうかを検証できた。しかし、そのハッシュを自分で発走後に作成した可能性は排除できない。

今回の新しい [外部受付検証器](../scripts/odds_github_attestation.py) と [GitHub Actionsワークフロー](../.github/workflows/odds-shadow-attest.yml) は、封印した予測のハッシュだけをGitHubのworkflow_dispatchへ提出し、GitHub REST APIが記録したrun.created_atで受付時刻を確認する。発走予定の**10分以上前**に受付が記録された場合だけ、ハッシュの事前存在が裏付けられる。

これは**ハッシュの事前存在の証拠**であって、元オッズの真偽、予測が校正された本当の勝率か、投票者の模倣、馬券利益、正式v3.1 holdoutを保証するものではない。

## 公開するのは4つの文字列のみ

GitHubへ送信するworkflow_dispatch inputsは次の4つ。

- race_id — 公開可能な競走ID
- seal_sha256 — ローカルで封印した予測payloadの64文字ハッシュ
- scheduled_post_jst — 予定発走時刻とタイムゾーン
- last_source_received_jst — 事前情報の最終受信時刻の自己申告

**元の全頭単勝、全ワイド価格、確率表、ライセンス付きデータはアップロードしない。** 予測本体は研究者のローカル環境に残す。

## 事前提出から採点まで

### 発走前

許諾確認済みのローカル市場データで、係数を価格更新前に固定してからシャドー予測を作る。

~~~bash
python scripts/odds_shadow_freeze_score.py freeze \
  --source private/authorized_snapshot.json \
  --output private/freeze.json

python scripts/odds_github_attestation.py dispatch \
  --freeze private/freeze.json \
  --output private/dispatch.json
~~~

次に、GitHub Actionsの「SHA-only shadow odds prediction preseal」を実行し、dispatch.jsonのinputsに記録された4項目を正確に入力する。GitHub CLIの場合はgh workflow run odds-shadow-attest.yml --ref main と、4つの -f name=value 引数を使う。

**実運用の重要な制限**：GitHubのworkflow_dispatchは該当ワークフローがデフォルトブランチに存在する必要がある。2026-10-24現在、本実装はDraft PR #10の分析ブランチにしかないため、**mainに導入するまでは実行不能**。詳細：[GitHub公式ドキュメント](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)。

実際に起動されればGitHub Actionsはrun ID付きのSHAだけのcommitment.jsonを生成し、v4 artifactとして保存する（保持期間は90日）。同じレースへの複数の申請はGitHub run一覧に残るため、最初の受付より遅い提出を選ぶことを拒否する。

### レース後

公式結果を独立に記録したら、ローカル封印ファイルとGitHubの実run IDを照合する。

~~~bash
python scripts/odds_github_attestation.py verify-live \
  --freeze private/freeze.json \
  --repo zuizui0223/keiba \
  --run-id ACTUAL_RUN_ID \
  --result private/official_top3.json \
  --output private/proof-and-score.json
~~~

verify-liveはGitHub CLIを使ってrunメタデータ、当該アーティファクト、当該workflowの他のrun一覧を**GitHubサーバから新規取得する**。ローカルの日時文字列だけを入れた偽の記録では成功しない。

検査条件は、対象リポジトリとワークフロー、main上の手動実行・一回目の成功、提出された競走ID・ハッシュ・予定発走時刻、run.created_atがローカル封印後かつ発走10分以上前、他に先行する同一レースの試行が無いこと、最後に封印した元ファイルがSHAと一致すること。

公式結果の採点は元のローカル封印の単勝Log loss（主要）、Top3 Brier（副次）、三連複Log loss（探索）とし、**v3.1の既存20レース台帳には一切追加しない**。

## 本当に証明できる範囲

- GitHubのrun.created_atは第三者サーバの受付時刻の証拠となる。
- 予測ファイルのSHA256照合は予測内容の差し替え検出となる。
- しかし提供元オッズの正しい掲載・取得時刻、ライセンス、実際のJRA結果の原本、モデル係数の妥当性は別途監査する。
- GitHub Actionsのrun一覧が欠けた場合、以前の失敗した提出が確認された場合、アーティファクトが90日で消失した場合はHOLD。偽のローカル受付記録で代替しない。
- 同じ競走への多数の提出から有利なものを選ばない。失敗した提出も研究の試行として記録する。
- これらの証拠を用意しても、それだけで単勝や複勝の予測優位、正の投資収益は成立しない。

## 合成動作確認

~~~bash
python -m unittest discover -s tests -p 'test_odds_github_attestation.py' -v
python scripts/odds_github_attestation.py demo \
  --output tmp/synthetic-offline-GitHub-proof.json
~~~

上記のdemoは架空2030年のGitHub情報を与えるため、**必ずHOLD_OFFLINE_RECEIPT_IS_NOT_INDEPENDENT_GITHUB_EVIDENCE**を返す。ハッシュ破損、別レースへの置換、発走後の提出、異なるworkflow、2回目のrun、先に失敗した同一レースへの提出、GitHub APIへの接続失敗などをテストする。

## 実証上の現在地

この研究では既に京都5レースの実市場で単勝・ワイドの非同調と、券種別に異なる事後的な着順スコアを確認した。しかし全て同一開催日の結果を後から採点したもので、独立の前向き成績ではない。

**次の実証に必要なのは**、ワークフローを安全にデフォルトブランチへ導入し、実競走前にモデル係数とハッシュを外部受付させ、未来の別開催日で結果を採点すること。その後、競走ごと・開催日ごとに単勝PL基準と階層モデルを比較する。実オッズ閾値や追随因果効果については引き続きHOLD。
