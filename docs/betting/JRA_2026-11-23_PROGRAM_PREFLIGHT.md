# JRA 2026-11-23 pre-race calendar preflight (not a frozen cohort)

**Checked 2026-11-22 JST. Status: PRELIMINARY_PROGRAM_ONLY / NO SERVER-SEALED OFFICIAL FULL CARD / NO BETTING FORECASTS.**

This is a *provisional* list of the earliest ten potentially eligible JRA races for tomorrow's prospective odds experiment. It is not the full verified day-plan JSON and MUST NOT be used to report any genuine forward success. Full official racecards, exact active runner counts, scratches, contemporaneous price updates, official raw page bytes and GitHub pre-first-race receipts are still needed.

The [JRA published program for 23 November 2026](https://jra.jp/keiba/calendar2026/2026/11/1123.html) specifies Tokyo 5th meeting day 6 and Fukushima 3rd meeting day 6, 12 races per venue. [JRA official racecard example](https://app.jra.jp/JRADB/accessD.html?CNAME=sw01ddd0103202603060220261123%2F68) confirms posted participants and race information; the published program explicitly warns that race/post time and other details can change.

Preliminary participant counts have been cross-checked with accessible third-party racecards ([Tokyo counts](https://umadan.jp/races/jra/2026-11-23), [Fukushima 1/5/6](https://keiba.love/20261123/fukushima.html), [Fukushima 3](https://race.netkeiba.com/race/shutuba.html?race_id=202603030603)) and official individual racecards where seen. These counts are not substitutes for a complete same-time JRA day roster.

| Provisional selection order | Race | Planned post JST | Expected runners (unfrozen) | Venue/class |
| ---: | --- | --- | ---: | --- |
| 1 | Fukushima 1R | 09:45 | 16 | 2yo maiden, dirt |
| 2 | Tokyo 1R | 10:00 | 14 | 2yo maiden, dirt |
| 3 | Fukushima 2R | 10:15 | 15 | 3yo+ 1 win, dirt |
| 4 | Tokyo 2R | 10:30 | 17 | 2yo maiden, turf |
| 5 | Fukushima 3R | 10:45 | 15 | 3yo+ 1 win, dirt |
| 6 | Tokyo 3R | 11:00 | 11 | 2yo maiden, turf |
| — | Fukushima 4R | 11:15 | not used | **Obstacle race: excluded a priori** |
| 7 | Tokyo 4R | 11:30 | 15 | 2yo maiden, dirt |
| 8 | Fukushima 5R | 12:05 | 16 | 2yo newcomer, turf |
| 9 | Tokyo 5R | 12:20 | 14 | 2yo newcomer, turf |
| 10 | Fukushima 6R | 12:35 | 16 | 2yo maiden, turf |

## 2026-11-22 夜：JRA公式出馬表24件を読み取った追加監査

[24公式出馬表のURL・取得元SHA256・連番馬番行数の匿名メタデータ](../evidence/ticket-forward-20261123-jra-card-numbered-rows-20261122.json)を保存した。GitHub Actionsは[JRA公式の福島/東京1Rのナビゲーション](https://github.com/zuizui0223/keiba/actions/runs/45029846692)から両場の**全24レースURL**を発見し、[各ページを1回ずつ読み取った実行記録](https://github.com/zuizui0223/keiba/actions/runs/45030215026)で全24レースのHTMLテーブルから連続する馬番列を抽出した。**元HTML全文は公開していない**。

- 福島1〜12R：今回抽出した馬番行数は暫定頭数とすべて一致（ただし4Rは障害なので券種別実験から除外）。
- 東京1R：**公式表13行、暫定サイト14頭**。
- 東京4R：**公式表14行、暫定サイト15頭**。
- 東京6R：**公式表13行、暫定サイト14頭**。
- 他の東京9レースは一致。差の原因を出走取消と決めつけない。馬番行数がそのまま発走時の実出走頭数とは限らない。

[専用の突き合わせコード](../../scripts/ticket_forward_jra_reconcile.py)は、この公式24ページの読み取り数を使って仮の先頭10レースを改めて計算し、暫定頭数との不一致を全件記録する。**暫定先頭10レースの組合せ自体は変わらない**が、東京1R/4Rの候補頭数を第三者の値と同一視してはいけない。

**制約はそのまま：** ①出走取消等を反映した最終の実出走馬集合、②同一時点・公式24出馬表原資料との確実な内容照合、③最初の発走9:45より前のGitHubでの「日別対象分母」サーバー封印、④15〜25分前の真正な単勝・ワイド更新時刻と全価格、が揃っていない。現状は将来モデルの予測0件・独立評価0件。翌朝の評価で条件を満たせない場合は**HOLD**とし、後から日時・出走馬を埋めない。

## 2026-11-22 23:11 JST：候補選択をGitHubサーバー時刻で事前記録

[JRA公式24レースの馬番行数・URL・ソースSHA](../evidence/ticket-forward-20261123-jra-card-numbered-rows-20261122.json)から、**公式の馬番連続表で9〜18行を満たす平地レースの最初の10件**を再選択した。

- [10候補の事前選択JSON](../evidence/ticket-forward-20261123-prestart-intent.json)は、元の24レースプログラム、24公式表メタデータ、固定したコード・マニフェストのGit blob SHAを参照する。
- [サーバー時刻の検証記録](../evidence/ticket-forward-20261123-intent-receipt.json)：GitHub Actions [run #45031414549](https://github.com/zuizui0223/keiba/actions/runs/45031414549) は **2026-11-22 14:11 UTC（23:11 JST）**に開始、成功。実行コミット \`9fb8e2a617d89a6b5c11869fd4c51d5f5013f7a5\` に対象の候補ファイル（Git blob \`4d3fde7d6269b86472b409719077aca556dc4ac1\`）が存在したことを照合済み。
- **これは候補選択の事前記録に限る**。元の公式HTML24件、最新取消、全単勝・全ワイドの出典更新時刻、3ファイルの正式day-plan封印がまだないため、正式なholdout day-planではない。前向き予測・採点は0件。
- 2026-11-23の朝の公式出馬表に変更があっても、古い候補ファイルを黙って書き換えてはいけない。実際の結果より前に新しい公式データを保存して資格判定を更新し、変更点とHOLDを独立に記録する。

**Protection against hindsight:** The code cannot yet register this table as the first prospectively eligible day. The universe script now refuses incomplete meeting lists: it requires full **1R–12R for each of exactly 2 or 3 venues**, a declared positive runner count for every active race, and a result-free schedule source. The first-day plan must then be sealed **before 09:45 JST** by GitHub server receipt, together with the *actual* raw official day source and parsed schedule; independent source-page completeness review remains necessary. If that deadline, roster validation or receipt is missed, do not backfill from this preliminary table.

**Crucially, a provisional table created the night before is not yet a scientifically valid freeze.** A missing source should generate a transparent HOLD; it should never be replaced with estimated odds or later results.

Underlying tested code:
- [Full-day denominator](../../scripts/ticket_forward_universe.py)
- [Raw official day + GitHub server proof](../../scripts/ticket_forward_day_proof.py)
- [Pre-race odds freeze](../../scripts/ticket_forward_freeze.py)
- [Independent prospective contract](TICKET_FORWARD_V1_PROTOCOL.md)

No wagering or investment return claim.
