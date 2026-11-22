# ticket-forward-v1 — 券種間情報増分の前向き評価プロトコル

**定義日：2026-11-22。状態：実馬の未来予測0件。** 2026年10月12日と18日の結果を見た後に作成したため、当該2日間の再演は前向き実測には数えない。既存v3.1 holdoutとは完全に独立。

関連ファイル：

- [パラメータとコードSHA固定](ticket-forward-v1-manifest.json)
- [予測の凍結と結果採点](../../scripts/ticket_forward_freeze.py)
- [対象レース分母と全欠測記録](../../scripts/ticket_forward_universe.py)
- [過去9Rの探索結果](WIDE_PAIR_INFORMATION_TRANSFER_RESULTS.md)

## 仮説と固定比較

M0＝全出走馬の単勝逆オッズを強度とするPlackett–Luce（PL）上位3着順位分布。M3-wide＝全組合せワイドの幾何中点逆数を和3へ正規化し、PLの同時3着内ペア確率との対数残差を各上位3着順序へ **alpha 0.5** で追加、再正規化した一貫した分布。

主指標は、実際の1着→2着→3着に与えた**負の対数確率**の差「M3-wide−M0」。負が改善。副指標は8券種ごとの全可能買い目Brierスコア。アルファの再選択、都合のよい券種だけの選択は禁止。ワイドの真の票数・控除率を推定するモデルではない。今回は本人履歴・血縁・騎手の増分を主検定に混ぜない。

## レース分母：結果で選ばない

JRA中央平地（芝・ダート）、事前出走予定9〜18頭。2026年11月23日以降、GitHubでプロトコルが発走前に封印された開催日から、各日のJRA**公式の全レース予定**を当日の最初の発走前に保存する。開催日ごとに発走予定時刻→競馬場→レース番号→IDの順で並べ、適格な最初の10レースを固定。合計30**挑戦**まで続ける（異なる3開催日以上）。欠測レースを結果確認後に入れ替えない。

2026年11月23日は東京・福島、28日は東京・京都で開催予定というJRA公式日程がある。ただしこの概要だけで具体的なレース数・頭数を確定してはいけない。当日の出馬表の実データに基づく分母が必要。

予定表JSONは schema_version, schedule_date, source_url, source_text_sha256, captured_at_jst, races を持つ。各レース行は race_id, venue, race_number, date, scheduled_start_jst, surface, declared_runner_count, status を持つ。全レースを含むことと元資料の真正性は独立確認が必要。前日または当日最初の対象レース前にGitHubサーバー時刻で予定表・選択結果を封印する。予定表を後で作った場合は正式な分母として扱えない。

初期の空台帳を生成する：

    python scripts/ticket_forward_universe.py init --manifest docs/betting/ticket-forward-v1-manifest.json --output /tmp/ticket-forward-ledger.json

予定表から日別の対象候補を先に決定する：

    python scripts/ticket_forward_universe.py plan-day --schedule /private/jra-schedule.json --manifest docs/betting/ticket-forward-v1-manifest.json --output /tmp/day-plan.json

    python scripts/ticket_forward_universe.py register-day --ledger /tmp/ticket-forward-ledger.json --day-plan /tmp/day-plan.json --manifest docs/betting/ticket-forward-v1-manifest.json --output /tmp/ledger-next.json

欠測がある場合でも、対象レースはHOLDとして登録する。状態は HOLD_NO_WIN_WIDE_SNAPSHOT, HOLD_INCOMPLETE_MARKET, HOLD_STALE_QUOTE, HOLD_INVALID_ROSTER, HOLD_MISSING_SERVER_RECEIPT、提出した場合は SUBMITTED_FOR_GITHUB_PROOF。イベントは順序固定で二重登録不可。

## 日別の完全な分母・サーバー封印（追加監査）

[2026-11-23の実際のJRA予定から作った暫定10レース](JRA_2026-11-23_PROGRAM_PREFLIGHT.md) は、公式出馬表の全馬・当日全レースが同一時点で照合済みではないため、正式ホールドアウト台帳には入れない。

正式な日別スケジュールは、**2または3競馬場について各1R〜12Rの全24〜36行**を必須とし、出走予定の各レースには正の頭数が必要。1レース・1競馬場だけを都合よく掲載したファイル、8頭以下の取消・障害レースを不当に隠したファイル、頭数未確認の0頭レースは不正として拒否する。JRA公式当日番組自体に例外のある日は無理に対象選択を続けずHOLDし、別の事前仕様を検討する。

日別プランの根拠になる**3つのバイト列**（公式スケジュール原文、24/36行に転記したJSON、当日選択プランJSON）について、[予定表サーバー証明コード](../../scripts/ticket_forward_day_proof.py)を追加した。

- 解析上の確認：原文SHA256、予定表JSONのハッシュ、対象選択プランJSONを元のコードで再計算し、最初の10レースが改変されていないか検査する。
- GitHubサーバー上の確認：予定表の最初の発走**以前**に開始された成功runのコミットに、同じ3バイト列が共存したことを、GitHub APIで実バイト・Git blob SHA1を照合する。
- 科学的限界：元公式ページからの転記が正しいか／全24または36行を本当に原資料から拾ったかは**別途独立監査**が必要。サーバー記録は公式データの真正性までは証明しない。

必要な配置：

    holdout/ticket-forward-v1/YYYY-MM-DD/day-schedule.json
    holdout/ticket-forward-v1/YYYY-MM-DD/day-schedule-source.txt
    holdout/ticket-forward-v1/YYYY-MM-DD/day-plan.json

発走前に3ファイルがコミットされた後、成功したActions run IDを添えて確認する。

    python scripts/ticket_forward_day_proof.py \
      --schedule holdout/ticket-forward-v1/YYYY-MM-DD/day-schedule.json \
      --source-page holdout/ticket-forward-v1/YYYY-MM-DD/day-schedule-source.txt \
      --day-plan holdout/ticket-forward-v1/YYYY-MM-DD/day-plan.json \
      --manifest docs/betting/ticket-forward-v1-manifest.json \
      --github-run-id RUN_ID \
      --github-plan-path holdout/ticket-forward-v1/YYYY-MM-DD/day-plan.json \
      --output /tmp/day-server-proof.json

run IDがない場合は**DAY_EVIDENCE_CONSISTENT_BUT_NOT_SERVER_ATTESTED**と表示し、正式な前向き日別分母に昇格させない。サーバー検査が成功して初めて**DAY_PLAN_SERVER_SEALED_PRE_FIRST_RACE**になる。

## 予測時点の情報ゲート

単勝全頭、ワイド全n(n−1)/2組合せ、馬番号・枠・予定発走時刻が一致すること。オッズソースは許可されたJRA公式URLまたは記録可能な仲介URL。単勝とワイドのページに**出典上の更新時刻が表示されている**必要がある（推定した時刻を代入しない）。

- 予測時刻：発走15〜25分前
- 更新時刻の古さ：予測時点から10分以内
- ページの取得時刻：予測時点から5分以内
- 単勝／ワイドの取得時刻差：最大90秒
- 元ページの実バイトSHA256と予測入力の対応が一致すること
- 結果・着順・払戻・最終オッズを予測入力に混ぜた場合は拒否

各レースについて、下記4ファイルを結果が出る前に一つのGitHubコミットへ保存する。

    holdout/ticket-forward-v1/RACE_ID/
      capture.json
      win-source.txt
      wide-source.txt
      forecast.json

capture.json は schema_version=1, race, markets の3要素を持つ。raceには race_id, date, venue, race_number, scheduled_start_jst, horses を含み、horsesは全頭のnumberとframe。markets.winとmarkets.wideの各市場には source_url, observed_at_jst, updated_at_jst, updated_time_basis="source_visible", raw_page_sha256, quotes の6要素を含む。各quoteは selection（馬番号配列）、odds_low、odds_high。単勝low=high。元ページの全文（再配布可能な範囲）はそれぞれwin-source.txtとwide-source.txtに保存し、その実バイトSHA256を用いる。

    python scripts/ticket_forward_freeze.py freeze \
      --capture holdout/ticket-forward-v1/RACE_ID/capture.json \
      --win-source-page holdout/ticket-forward-v1/RACE_ID/win-source.txt \
      --wide-source-page holdout/ticket-forward-v1/RACE_ID/wide-source.txt \
      --manifest docs/betting/ticket-forward-v1-manifest.json \
      --as-of-jst "YYYY-MM-DDTHH:MM:SS+09:00" \
      --output holdout/ticket-forward-v1/RACE_ID/forecast.json

予測には全nP3順序についてM0とM3-wideの確率を保存する。数値自体の整合性、モデルGit blob SHA1、captureと元資料のSHA256を固定。単にファイルを作っただけでは前向き評価として認めない。

## GitHubサーバーによる前向き証明

予測ファイルと同じコミットにcapture・単勝原ページ・ワイド原ページの**4ファイル**が揃い、当該コミットを含むGitHub Actions runが発走前に**GitHubサーバーで開始**されている必要がある。結果確認後のスコア時に、成功runのIDとその当時のforecast.jsonのパスを指定すると、GitHub APIから server-created timestamp、git head SHA、forecastと3つの元資料ファイルの**実バイト**を検証する。実行時刻が予測時刻より古い、発走後、コミットの内容が異なる、ファイルが欠ける場合は拒否する。

ただしこの照合で証明できるのはファイルが発走前に存在したことまで。**元ページがJRA等の出典に実際に対応すること、表示された引用更新時刻が正しいことは別途監査**する。利用規約上公開できない元HTMLは無断で再配布せず、私的原資料と公開ハッシュ・記録を分け、証明の限界を明記する。

## レース終了後に別ファイルで採点

JRA公式の上位3着、結果ページ、結果を見た時刻と元ページSHA256を別のresult.jsonに記録（同着や取消など、この版が扱えない事象はHOLD）。**手入力した3つの馬番号だけでは採点を確定させない。** JRA公式結果ページの見出し（日付・競馬場・レース番号）と1〜3着の3行が確認できる元テキストを別途保存し、検証器がページから上位3着を独立に取り出してresult.jsonと一致することを必須とする。ページ形式を認識できない場合は無理に類推せずHOLD。

    python scripts/ticket_forward_result_capture.py \
      --race-id RACE_ID \
      --official-url 'https://www.jra.go.jp/JRADB/accessS.html?SOURCE_ID' \
      --source-text holdout/ticket-forward-v1/RACE_ID/result-source.txt \
      --observed-at-jst 'YYYY-MM-DDTHH:MM:SS+09:00' \
      --output holdout/ticket-forward-v1/RACE_ID/result.json

    python scripts/ticket_forward_freeze.py score \
      --forecast holdout/ticket-forward-v1/RACE_ID/forecast.json \
      --result holdout/ticket-forward-v1/RACE_ID/result.json \
      --result-source-text holdout/ticket-forward-v1/RACE_ID/result-source.txt \
      --manifest docs/betting/ticket-forward-v1-manifest.json \
      --github-run-id 123456789 \
      --github-committed-path holdout/ticket-forward-v1/RACE_ID/forecast.json \
      --output holdout/ticket-forward-v1/RACE_ID/score.json

source-textの実バイトSHA256・レース日付・競馬場・レース番号・着順3行が一致しなければ採点自体を拒否する。ただしこの検査も元ページの取得元の真正性までは証明しない。

GitHub証明がなければ採点しても SCORED_BUT_PROSPECTIVE_STATUS_UNVERIFIED。証明が成功した場合のみ SCORED_PROSPECTIVE_SERVER_SEALED。予測に結果を混ぜての再計算はしない。

**まだ未来の実レース出走表・単勝/ワイド全組合せの時点付きスナップショットを取得していないので、前向き評価0件。** 実施には今後の取得が必要。30挑戦は初期パイロットであり、誤差が小さくてもこの段階で収益性・遺伝因果・市場の完全効率性を主張できない。新しい購入・自動投票機能はない。
