# WIN-only未来q2の統合実験：元6候補＋連続・閾値・無情報5候補を同じレースで比較

**2026-10-31 事前に追加したB+ companion（開発）。本物のライセンス元WINや新規未来q2実測はまだ未取得。元の単勝専用PR #30の6候補の予測SHA・モデル・対象分母は変えない。**

## 元の馬ABM/PDE/市場鎖を置き換えない

既存 [PR #30](https://github.com/zuizui0223/keiba/pull/30) Lane Bは、原出馬表＋元全馬WIN2時点→取得チェーンSHA＋コードSHA→前方馬ABM/PDE検算→投票者ABM→6候補→固定15–20分後の最初の全馬WIN価格を評価する設計。これを過去の成績であとから置換してはいけない。

[PR #36](https://github.com/zuizui0223/keiba/pull/36) は過去の京都8R保存済みの**1件の次オッズ**を使った事後再生で、将来の再現性や閾値の存在を証明しない。新しく追加する keiba_win_only_regime_sidecar.py は**元PR30 freezeを必ず検算してから**、同じ1レース・同じq2に対し5モデルを追加する。元6モデルはそのまま**計11モデル**として保存し、同じ実raceの評価数は1件である。

## 新しいモデル5種

元全馬WIN価格の正規化逆数を q0, q1、原本source更新時計の差を h hoursとする。次の元PR30目標まで0.25hなので

v_i = (0.25/h) log(q1_i/q0_i), r = max_i |log(q1_i/q0_i)|/h

として、q2_i(alpha) ∝ q1_i exp(alpha v_i)。持続 (alpha=0) と全文logモメンタム (alpha=1) は**すでに元の6候補に存在するので重複させない**。

B+は、1. 連続価格ゲイン alpha=r/(r+0.10)、2. ハード価格ゲート alpha=1 if r>=0.10 else 0、を別候補として追加。0.10/log index per hourは元の探索的PR19由来の**仮定定数**であり市場の臨界値を観測したものではない。

残り3モデルは**元PR19の投票者ABMを改変せず使用**。投票者の固定・連続・ハード3法則それぞれで、同じ qmidと30人工seed、仮想初期3,000票、4ラウンド×250票、15分という仮想時計、**馬の新情報は最後まで到達しないarrival=5** という無情報の対照。ハード価格ゲインとハード投票者feedbackは**異なる方程式**。30seedは1レースの数値反復であって30独立市場ではない。

元6候補には qmid由来の馬能力prior→非局所馬ABM→PDE診断→情報到着1/3/なしの投票者ABM、馬IDずらし偽対照がある。**全て保全**する。ただし馬能力priorは市場由来であり、独立した実GPSではない。

## ソース・カード・SHA・ターゲットの完全対応

- B+ freezeは元6候補のオリジナルSHA、元source chain head SHA・件数、最終card SHA、全頭番号、最初の2つの**source publication＋reception時計**、未来目標窓を照合してから作る。
- 新モデル使用コード5ファイルのSHA・5候補のベクトル・30人工seedの3政策全予測・親SHAを、独立したcanonical B+ SHAに固定する。
- **親freezeの時刻より前・次WIN目標窓開始以後のB+ freezeを拒否**。未来ターゲットを前のモデルの説明変数に入れない。
- B+ scoreはまず**既存のPR30 score_win_onlyをそのまま実行**し、唯一最初の対象WIN q2を再取得。元持続／モメンタムTVとKLが親の実スコアに一致しなければ拒否。
- 次q2欠測はHOLD。都合の良い時点への変更、0誤差補完、競走ID変更、取得チェーン改変、モデルSHA不一致はHOLD。

## 実行（権利確認済みの非公開元ソースがある場合のみ）

未来q2を取得する前に、元PR30元6候補がすでに凍結されている同一レースで：

    python scripts/keiba_win_only_regime_sidecar.py freeze \
      --ledger private/captures/RACE \
      --final-card private/RACE_final_card.json \
      --original-win-only-freeze private/RACE_WIN_only_frozen.json \
      --private-output private/RACE_WIN_only_regime_Bplus.json

固定された+15〜20分の次q2窓が閉じ、対象オッズを実際に捕捉した後：

    python scripts/keiba_win_only_regime_sidecar.py score \
      --ledger private/captures/RACE \
      --final-card private/RACE_final_card.json \
      --original-win-only-freeze private/RACE_WIN_only_frozen.json \
      --sidecar-freeze private/RACE_WIN_only_regime_Bplus.json \
      --operator-confirms-complete-capture \
      --private-output private/RACE_WIN_only_regime_Bplus_local_score.json

**新しいB+ SHAを作っただけでは外部時刻認証でない。** 元PR30のGitHub SHA-only comment verifierは**元6候補だけ**に対応し、追加5候補を同じコメントから認証したことにしてはならない。B+の独立したGitHubサーバー時刻証明が実装・実行され、実際にq2以前に2つのSHAコメントが投稿・検証されるまでは**外部pretarget HOLD**。原データはprivate/に置き、元オッズや生投票データをPRに公開しない。

JRA-VAN認可元CSVや真の投票量は取得しておらず、今回の新規真正未来次オッズ評価は**0件**。JRAの馬勝率校正、賭け期待利益、社会的な相転移・臨界オッズはいずれも未確証。元26重賞/64補助枠の固定分母と菊花賞M0–M2およびv3.1 ledger、mainは変更なし。

## 再現（人工6頭の厳密な反証試験）

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests -p 'test_keiba_win_only_regime_sidecar.py' -v

専用CIでは、同一future sourceの最初適格なq2の採点、元6モデル不変、SHA/コード改変と時計逆行の拒否、無情報30seed、欠測HOLDを検査する。**合成例の成功は、実市場で新たな肯定的な結果を得たことを意味しない。**
