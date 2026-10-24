# 独立導入できるSHA-onlyのオッズ予測ハッシュ受付

**2026-10-24：このブランチは予測モデルや競馬ソース資料を含まない、main向けの最小インフラPR。**

この小さい変更は、次の4項目だけをGitHub Actionsのworkflow_dispatchで受け取る。

- 公開可能な競走ID
- SHA256形式の封印済み予測内容ハッシュ
- タイムゾーン付き発走予定時刻
- タイムゾーン付き最終価格受信時刻（自己申告）

元のJRA/JRA-VAN・Yahoo!のオッズ表、馬ごとの予測確率、アカウント情報をGitHubへアップロードしない。

GitHub Actionsには独立した標準ライブラリだけの [受信処理](../scripts/odds_sha_only_receipt.py) を同梱し、repo/ref/event/run id/run attempt、ハッシュ長、race ID、時刻、発走10分前までの情報受信を検証して**予測ハッシュの受領票**を作る。runに紐づくv4 artifactに90日間保存する。実際の受付時刻はこのローカル受領票の生成時刻ではなく、第三者のGitHub APIから取得する run.created_at を使用する。

実際にSHAが発走前に提出されていたかを判断するには、[研究PR #10](https://github.com/zuizui0223/keiba/pull/10) の独立検証器が必要。GitHub REST API・workflow artifactを新規取得し、最初の同一競走の提出であること・SHAが元のローカル予測に一致すること・GitHubサーバの受付時刻が発走10分以上前であることを検証する。研究PRが未マージの間はその検証器も実用前であり、**この小PRの準備だけではまだ事前提出は存在しない**。

## 導入順序

1. 最小インフラPRのソースとGitHub Actions定義をレビューし、必要な場合にmainへマージ。
2. GitHubの仕様により、workflow_dispatchは当該workflowがデフォルトブランチに存在して初めて実行できる。マージせずにこの分析ブランチで「受領済み」とみなさない。
3. 研究者の安全なローカル環境で先に予測ファイルを作り、SHAと時刻だけをworkflowへ発走前に提出。実run ID・server-created-at・artifactsを保存。
4. 後日に独立の公式着順を取得してからハッシュを元予測ファイルと照合して事後採点する。複数提出の有利なものだけを選ばず、最初の試行を残す。

この受領ワークフローのみによって**競馬の勝率予測性能・オッズ閾値・投票者追随・馬券の収益性**が検証されるわけではない。v3.1の20レース正式holdoutには影響を与えない。

## テスト

~~~bash
python -m unittest discover -s tests -p 'test_odds_sha_only_receipt.py' -v
~~~

デフォルトブランチ以外からの受付、2回目のrun、タイムゾーン無しの日付、発走10分前より遅いソース、余計な市場価格列、無効なレースIDとSHAを拒否する。これは**完全に人工の受領データによるソフトウェア検証**であり、実競走の発走前に予測があったという証拠ではない。

GitHub仕様：[手動起動workflowはデフォルトブランチが必要](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)。
