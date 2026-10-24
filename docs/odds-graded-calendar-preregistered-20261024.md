# 2026年平地重賞の前向き評価：対象26競走を結果前に固定

**2026-10-24／GitHubサーバへ事前提出済み。これはレース対象の登録であり、競走結果の予測有効性の証明ではない。**

## 結果を見て対象を選ばないための競走分母

[JRA公式2026年重賞レース一覧](https://jra.jp/datafile/seiseki/replay/2026/jyusyo.html)に基づき、10月25日〜12月27日の平地GⅠ・GⅡ・GⅢ **26競走／20競走日**を、結果前に以下のファイルへ登録した。

- [公式2026年対象名簿](../data/research/jra-graded-flat-2026oct25-dec27-calendar.json)：日付・場・競走名・格の全26件。障害のJ-GⅠ/GⅡ/GⅢとJRA以外の競走は対象外。将来の競走番号や発走時刻は未確定のものを捏造せず、菊花賞のみ公式確認済み。
- [全26競走の状態台帳](../data/research/odds-prequential-2026oct24-coverage-registry.json)：菊花賞のみ予測SHAを別途提出済み、残り25競走は未予測のまま明記。
- [市場基準M0と経路M1の事前ルールv1](odds-prequential-graded-cohort-v1-20261024.json)：予測係数と主要評価指標。

これら3つのファイルのSHAと**26競走の一覧そのもの**を、[GitHub PR #10の事前登録コメント](https://github.com/zuizui0223/keiba/pull/10#issuecomment-6382991405) に投稿した。GitHub APIのサーバ記録は2026-10-24T10:15:53Z、すなわち**2026年10月24日19:15:53 JST**。作成時刻と更新時刻は一致し、翌日菊花賞の15:40発走より前だった。以後このコメントは編集しない。

| 事前提出したファイル | Git blob SHA-1 |
|---|---|
| 26競走の名簿 | f458794971e184fb4cda5fdab84d1c56f277cc2f |
| 26競走の状態台帳 | 9052dbb3590fd6a93bd6c6732d4e992929f77f0e |
| 係数と主要評価ルールv1 | a0c3b180417ce061b72831fc649c5e5743a20935 |

菊花賞の予測内容自体は別に、[先行するコメントID 6381798252](https://github.com/zuizui0223/keiba/pull/10#issuecomment-6381798252)でSHAを提出済み。**競走分母の提出と、個々のレースの予測を提出したことは別々の証拠**。

## 「欠測」も分母から消さない

[対象競走の監査器](../scripts/odds_graded_calendar_coverage.py)は、全26競走に必ず1つの状態行を要求する。公式予定の対象競走が1つでも台帳から消えた、対象外競走が事後追加された、同じ競走が二重登録された、結果を見てから除外を作った場合はHOLDで処理を拒否する。

予測時点での情報不足、2時点の全頭単勝欠損、元ソース時刻の不整合、取消・延期、中止、発走前SHA未提出、結果確認待ちも独立の状態で残す。未実施のupcoming状態が競走日後にも解決されなければ、**HOLD_OVERDUE_CALENDAR_SLOTS_WITHOUT_EXPLICIT_POSTRACE_DISPOSITION**となり、古い台帳を都合よく完了したものと見なせない。

[外部GitHubコメントの照合器](../scripts/odds_graded_calendar_comment_proof.py)は、SHAの一致だけでなく、26競走の名前と日付をそれぞれコメント原文に照合する。偽のローカルコメントJSONは常にHOLD、GitHubサーバから新規取得したAPI結果だけが外部証拠として認められる。

## 事前固定の予測とスコア

M0は最新単勝の逆数正規化によるPL順位確率。M1は初期と最新の相対単勝支持の変化を固定係数+0.25で補正する。M2は早期表示単勝10倍以上の馬だけ同じ補正を入れた探索用モデル。係数と初期10倍の境界は実測から校正された最適値ではなく、**レースの結果で後から改変しない仮定**である。

**主要指標**は勝馬Log lossのM1−M0、副次はTop3 Brier、探索は三連複Log lossと10倍境界。各競走の事前SHAを第三者時刻で検証し、別途JRA公式結果の原本確認ができた時点だけ採点する。未提出や欠測を結果で後から選んで除外しない。

**現時点の前向き結果採点は0件**。対象26は未来の予定競走数であって、予測改善の統計的標本数ではない。ルールにある60レース・8開催日もソフトウェアの最低条件であり、有意性や検出力を保証しない。

## 2027年1〜3月はまだ対象名簿に含まれていない

研究期間v1の末日は2027年3月31日だが、この名簿はJRA公式2026年度の10月25日〜12月27日の対象だけを固定したもの。**全研究期間の分母が26で確定したとは主張しない。** 2027年分の公式番組を確認できた時点で、競走結果より前に別の名簿・別のSHA事前提出記録を作り、元の2026年分を差し替えない。

## 再現手順

~~~bash
python -m unittest discover -s tests -p 'test_odds_graded_calendar_coverage.py' -v
python -m unittest discover -s tests -p 'test_odds_graded_calendar_comment_proof.py' -v

python scripts/odds_graded_calendar_coverage.py \
  --calendar data/research/jra-graded-flat-2026oct25-dec27-calendar.json \
  --registry data/research/odds-prequential-2026oct24-coverage-registry.json \
  --output tmp/odds-graded-calendar-coverage.json

# GitHub CLIによる本当の独立API取得が可能な環境のみ：
python scripts/odds_graded_calendar_comment_proof.py \
  --calendar data/research/jra-graded-flat-2026oct25-dec27-calendar.json \
  --registry data/research/odds-prequential-2026oct24-coverage-registry.json \
  --protocol docs/odds-prequential-graded-cohort-v1-20261024.json \
  --output tmp/odds-graded-calendar-external-proof.json
~~~

上記は対象分母の監査であり、勝率や複勝率の未来予測精度の立証ではない。本線main、正式v3.1の20レース台帳、別PR #9の実馬ABMには変更を加えない。
