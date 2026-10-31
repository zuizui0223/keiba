# 2026年天皇賞（秋）：前日ニュース→翌日市場の事前固定試験（公開情報レーンC）

**2026-10-31事前作成。翌日11月1日の全頭単勝オッズはまだ取得していない。PR30/37の馬ABM・PDE・投票者ABM11モデルとは独立した別レーン。**

## 既知の元記事から確実に固定できること

[netkeiba 2026-10-31 17:42掲載](https://news.netkeiba.com/?no=347359&pid=news_view)の全17頭単勝は、[ウマニティ18:00掲載表](https://umanity.jp/racedata/race_newsdet.php?nid=11881172)と完全一致する。**2つの記事は別の市場更新という証拠ではない**。既存PR35の編集媒体申告値canonical SHAは **3b8fc4798664a090963d5e8221029643cf9205934ba7fe7db0cc37a8d1f6e37b**。本レーンは17:42記事の報道値1点だけを使用し、記事時刻をJRA原市場の実時刻に昇格させない。

4つの価格指数モデルを事前固定：
- M0持続：全17頭の単勝表示オッズ逆数を17頭で正規化
- 固定10%均等化：0.9*M0+0.1/17
- log support power 0.9：M0^0.9を再正規化
- log support power 1.1：M0^1.1を再正規化

3つの追加モデルは**恣意的な帰無・感度**であり、真の投票者率・市場の臨界点・馬の独立能力や勝率ではない。⑦マスカレードボール→①クロワデュノールの人気首位と上位2頭集合{1,7}を固定して、未来の同じ登録競走の価格順位と照合する。

全17頭の価格・4分布・依存コード実バイトSHA256・元報道値SHA・source URL・日時・競走ID・翌日の対象窓をcanonical SHA256に固定する。公開記事由来のsourceを、認可されたJRA-VAN原本だとは称しない。

## 将来のtargetを後から選ばないための固定条件

- 登録競走枠：2026-11-01|東京|天皇賞（秋）、東京11R芝2000m、予定発走15:40 JST、17馬番全件。予定時刻や確定出馬表の変更があれば本試験はHOLD。
- 未来元市場提供者：**JRA-VAN Data Lab** と厳密に指定。権利確認済み手元の元CSV・official-card・source updated時刻・ローカル受信のチェーンが実在する場合だけ。
- 時刻窓：**2026-11-01 14:45:00〜15:05:00 JST（両端含む）**。その範囲にソース更新時計がある**最初の**全17頭単勝の完全な更新を使用する。
- 受信期限：15:15 JST。ソース更新より受信が前、17頭欠損、異なる馬番・レース・provider・権利・出馬表・重複した更新はHOLD。
- 窓閉鎖前に採点しない。15:40の予定発走前に「もう未来の元価格は取得不可能」という最終欠測判定も出さない。適格な更新がなければ**HOLD_TARGET_MISSING**として残し、後から都合のよい他時刻に変更しない。

公開newsの初期価格と合法な提供者の未来価格は異なる媒体を跨ぐので、採点されても「同一provider市場の15分先予測」とは別の実験である。未来source自体の完全性・真正性は操作者宣言＋ローカルSHAだけでは第三者に保証されない。

## GitHubのSHA-onlyコメントで予測の存在時刻を証明

専用のPR41用マーカー **KEIBA_PUBLIC_NEWS_F0_TO_FIXED_NEXTWIN_SHA_V1** を新設。これは元のPR30・PR37の本当の11モデルSHAとは異なり、使用できない他レーンの実証件数を増やさない。

    python scripts/keiba_tenno_public_pretarget_future_shadow.py freeze \
      --output tmp/tenno-public-news-frozen.json

    python scripts/keiba_tenno_public_pretarget_remote_receipt.py prepare \
      --frozen tmp/tenno-public-news-frozen.json \
      --output tmp/tenno-public-news-SHA-comment-not-posted.json

prepareコマンドはPRへ**投稿しない**。許可を得た所有者が公開SHAのみを既存[PR41](https://github.com/zuizui0223/keiba/pull/41)へ**対象窓の開始より前**に一度投稿し、時刻証明コードがGitHubのコメント一覧と個別詳細の両方をREST GETして、本文SHA完全一致、同レーン重複なし、正しい所有者、編集なし、記事17:42以降かつ翌日14:45より前を検証する。

    python scripts/keiba_tenno_public_pretarget_remote_receipt.py verify-live \
      --frozen tmp/tenno-public-news-frozen.json \
      --output tmp/tenno-public-news-remote-proof.json

これは**SHAがGitHubサーバー上でtarget以前に存在したこと**の限定的な証明。元JRAの真の更新・受信時刻、合法なsource権利、未来targetの捕捉完全性、実投票量、馬GPS、レース結果を証明しない。

## targetが合法に捕捉できた場合の別工程

既存PR25のprivate取得チェーンと元cardを実際に用意した場合のみ：

    python scripts/keiba_tenno_public_pretarget_future_shadow.py score-local \
      --frozen tmp/tenno-public-news-frozen.json \
      --ledger private/captures/REAL_TENNO11 \
      --final-card private/REAL_TENNO11_verified_final_card.json \
      --operator-confirms-full-capture \
      --output private/tenno-public-news-local-score.json

4モデルを**同一の最初の適格なq2だけ**に対して市場表示指数のTV/KLで採点し、上位2頭の順位と集合も確認する。着順・払戻・馬券EV・個別投票は使用しない。正式PR30/37の11候補や元菊花賞M0–M2・v3.1 ledger・mainは変更しない。

**実際の権利確認済み元全頭WIN原本、将来q2、元のPR30/37の本物の2件のpretarget GitHub SHA登録は現在各0件。** このPRは新しい公開記事由来の事前予測を凍結する試験であり、真正な市場ダイナミクスの検証や勝率校正を達成したとみなさない。
