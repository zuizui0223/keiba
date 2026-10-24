# 2027年1〜3月・平地重賞36競走の暫定名簿（結果前の別版）

作成日：2026-10-24。正式格付・開催日割の最終認可がまだ完了していない段階の**予定候補**。2026年分の既存SHA固定26競走を変更せず、2027年1〜3月を独立した provisional annex として追加した。

## 元の情報と法的・制度的な状態

JRAの [2027年度開催日割・重賞競走のお知らせ](https://www.jra.go.jp/news/202609/092805.html) は2026年9月28日に発表された。公式の [2027年度開催日割表（PDF）](https://www.jra.go.jp/keiba/program/2027/pdf/nittei.pdf) には1月4日からの開催、重賞名およびGⅠ〜GⅢの暫定格が掲載されている。JRAは農林水産大臣の認可後に正式確定すると明記している。根岸S・オーシャンSのGⅢからGⅡへの格付け申請は2027年1月に審査予定であり、本表では昇格済みのGⅡとは扱わない。

公式表はグラフィカルなため、日付と名称の手作業転記を複数資料で照合した。二次資料：
- https://joumeshi.jp/articles/jra-program-2027
- https://oyaji-sports.com/2026/09/29/jra-graded-race-calendar-2027/

この二資料の競走日付が一致しないものは、片方を正解と断定するのではなく、**候補日・代替日を別々に保存**し「正式日付未確定」とした。日付に食い違いがあるのは、フェアリーステークス（1/10または1/11）、フィリーズレビュー（3/6または3/7）、中山牝馬ステークス（3/8または3/13）、フラワーカップ（3/21または3/20）の4競走。

JRA公式PDFと各二次資料を完全に機械的に照合・署名したわけではない。この暫定ファイルを「JRA認証済み正式開催名簿」と呼ぶのは禁止する。

## 36競走の範囲

| 月 | 平地の暫定対象 | GⅠ | 留保 |
|---|---:|---:|---|
| 2027年1月 | 11競走 | 0 | フェアリーSの日付差、根岸SのGⅡ昇格申請 |
| 2027年2月 | 12競走 | 1（フェブラリーS） | オーシャンSのGⅡ昇格申請 |
| 2027年3月 | 13競走 | 1（高松宮記念） | フィリーズレビュー、中山牝馬S、フラワーCの日付差 |
| **暫定合計** | **36競走** | **2** | **正式認可未了** |

2月13日の小倉ジャンプSと3月13日の阪神スプリングジャンプは障害重賞（J-GⅢ/J-GⅡ）であり、平地GⅠ〜GⅢの対象に混ぜていない。開催場や競走番号の未確定部分を便宜的な識別子で捏造しない。

## 凍結するファイル

- [2027年1〜3月の暫定36競走](../data/research/jra-graded-2027jan-mar-provisional-calendar.json)
- [同じ36競走の結果非依存・全件状態台帳](../data/research/odds-prequential-2027jan-mar-provisional-registry.json)
- [2026年26件＋2027年暫定36件の照合器](../scripts/odds_multiyear_provisional_coverage.py)
- [否定的検証](../tests/test_odds_multiyear_provisional_coverage.py)

2027年の各行は結果未使用・予測未提出・正式認可待ちという状態。予測ハッシュが提出された、出走馬が確定した、結果が出た、格付けが認可された等の状態を現在の実証結果として記載しない。

2026年10〜12月の事前提出済み競走26件のカレンダーGit blob SHAは f458794971e184fb4cda5fdab84d1c56f277cc2f、状態台帳は9052dbb3590fd6a93bd6c6732d4e992929f77f0e、元の研究係数・採点規則v1は a0c3b180417ce061b72831fc649c5e5743a20935。**この3件の生ファイルが変更されていないことをプログラムがSHAで強制**する。

新たな2027年暫定ファイルも現在のGit blob SHAに固定した：

- 2027暫定カレンダー SHA = 15200e2429bc4c1c3b4388f11ffa2c4ba169369b
- 2027暫定状態台帳 SHA = 40ea5551472615f2faa61b0cb700b5862bb34305

正式日程・格付の審査結果で変更が必要なら、**この暫定ファイルを書き換えるのではなく別ファイルv2として改訂し、改訂理由と外部提出時刻を残す**。その後に正式な研究対象分母として確定する。

## 結果が無くても先にできる検証

2026年26候補＋2027年36候補＝62件というカレンダーの数は、プログラムで定めた最少60競走という「データ件数の受付条件」を見かけ上満たす。しかし、**予測確率を結果前に外部提出したことやJRA公式結果を前向き採点したことの証拠にはならない**。62件の予定競走が存在するという情報から、M1とM0の勝率予測誤差や閾値の正の結果を推測してはいけない。

- 2026年26件の登録後に競走が取消・延期・欠測になった場合も、最初の26件の分母は保持。
- 2027年36件は暫定候補なので、最終認可を得た別版との適切な照合が済むまで、確定分母とは見なさない。
- どのレースも、JRA公式結果の予測確率検証・モデルの事前封印・ROIの結果が存在したと偽って計上しない。
- M0/M1と係数+0.25、M2初期単勝10倍という探索候補、主要勝馬Log loss・副次Top3 Brierというルールv1は従前通り。新たな競走のリストを見て係数を最適化しない。

## 再現

~~~bash
python -m unittest discover -s tests -p 'test_odds_multiyear_provisional_coverage.py' -v

python scripts/odds_multiyear_provisional_coverage.py \
  --calendar-2026 data/research/jra-graded-flat-2026oct25-dec27-calendar.json \
  --registry-2026 data/research/odds-prequential-2026oct24-coverage-registry.json \
  --protocol docs/odds-prequential-graded-cohort-v1-20261024.json \
  --calendar-2027 data/research/jra-graded-2027jan-mar-provisional-calendar.json \
  --registry-2027 data/research/odds-prequential-2027jan-mar-provisional-registry.json \
  --output tmp/odds-multiyear-provisional-coverage.json
~~~

元のmain、正式v3.1 20レース台帳、および独立PR #9の実馬ABMには改変を加えていない。この研究成果はDraft PR #10に留める。
