# Authorized data acquisition gate for environmental allocation research

2026-11-25 JST. **HOLD_NO_AUTHORIZED_OFFICIAL_PANEL.** Public source documentation and terms checked; no account purchased, no provider contacted, no data access or research/publication permission obtained. The six CI runs on PR94 revision `8eb3f3cc7a0652e6347cacd8fe5d6610231aaafd` succeeded: [fictional source-to-fit audit](https://github.com/zuizui0223/keiba/actions/runs/45559674822), [PR audit](https://github.com/zuizui0223/keiba/actions/runs/45559682859), [tests](https://github.com/zuizui0223/keiba/actions/runs/45559682829), [navigation](https://github.com/zuizui0223/keiba/actions/runs/45559682820), [holdout regression](https://github.com/zuizui0223/keiba/actions/runs/45559682700), [ecology QA](https://github.com/zuizui0223/keiba/actions/runs/45559682752). They establish software behavior only.

## Source assessment

| Provider | Documented capability | Gate |
|---|---|---|
| JRA-VAN Data Lab | [Data specification and update schedule](https://jra-van.jp/dlb/ddata.html): new horse master records, breeding horses and progeny updates. [RACE/RCOV official FAQ](https://support.jra-van.jp/jravan/detail?category=16&id=226&site=SVKNEGBV) documents horse registration ID and race-level historical lookup. [Service](https://jravan.jp/dlb/) lists JPY 2,090/month including tax, via JV-Link. | [Terms art.7 and JV-Link restrictions](https://jravan.jp/info/rule.html): ordinary use restricted; approval for academic analysis, collaborator access and publishing aggregate effects is not established. [2026-11-20 staff response](https://developer.jra-van.jp/t/topic/1434) explicitly reiterates secondary-use restrictions. [Posting guide](https://jra-van.jp/info/post_guide.html) distinguishes limited permitted posts from JV-Link data. Do not purchase merely assuming academic publication rights. Ask support for permitted academic route. |
| JBIS / Japan Bloodstock Information System | [JBBA description](https://jbba.jp/data/site/) lists ~1.17 million light-breed horses of multiple types, ~770,000 races; [data coverage](https://www.jbis.or.jp/help/data/) describes 1984+ born horse information and single-start outcomes, central race results from 1986; [search](https://www.jbis.or.jp/help/horse/search/) supports active registration categories. | [Terms art.8/12](https://www.jbis.or.jp/terms/) and [secondary-use help](https://www.jbis.or.jp/help/use/) restrict unapproved copying/modification and automated access. Request written permission and a provider-supplied research export via [official contact](https://www.jbis.or.jp/support/); no scraping. Coverage of all eligible 2027 horses, historical snapshots and timestamp evidence not established. |
| Existing HF source B | [Pinned database documentation](https://huggingface.co/datasets/KBlueLeaf/jp-racing-horse/blob/main/db.py): horse table has hid, born, name, info, races; info described generically, not certified pedigree IDs. [Dataset card](https://huggingface.co/datasets/KBlueLeaf/jp-racing-horse) Apache-2.0 label; upstream rights not independently verified. PR93 194/2,839 strict horses have A parent anchor; 0/664 first-record 2025 horses anchored. | No certified new-entrant parent bridge. Do not infer parent identities from names, free text, numeric overlap, unknown fields or target outcomes. No new empirical analysis in this audit. |
| Earlier Wikipedia/Wikidata subset | [National pedigree scaling](JAPAN_NATIONAL_PEDIGREE_SCALING.md) partial documented genealogies. | Not a complete active-registrant universe, not native registry ID bridge, not substitute for 2027 full cohort. |

Provider claims of database coverage are not independently verified national census counts. Ordinary subscription is not a research-use license. No legal determination; obtain written provider guidance for this exact use. The underlying rights of prior public archives and permission to publish derived aggregates should also be documented before manuscript submission.

## Minimum requested research export (not obtained)

1. Full pre-window JRA registered/eligible horse universe, with stable blood-registration ID, registration status and observation date; all registered eligible horses including unraced/unknown pedigree. Distinguish registered from genuinely eligible; outside-universe new registrations later reported separately.
2. Separate stable breeding/parent ID namespace, typed sire and dam keys, authenticated breeding-to-blood crosswalk where available, missing/conflict/unresolved state and original master observation or version date; never equate breeding and blood registration numbers.
3. 2010–2026 candidate race census: stable race IDs, actual start date/time, JRA/NAR, flat/surface/distance, declared entry count, all entrants (including withdrawal/nonclassification states), official results and source-available timestamp or archived observation evidence. 2018 donor start, 2019–24 calibration, 2025–26 validation planned; real availability may HOLD rather than change after observing target outcomes.
4. 2027 Jan1–Mar27 follow-up of all candidate races, all entries and finalized outcomes with revisions and actual capture times. Distinguish no observed start from verified unraced. No betting prices, bets, personal owner/jockey data, or sensitive account information required for primary endpoint.
5. Written data-use rights and attribution, permitted private storage, derived aggregate publication and code/reproducibility conditions, collaborators if any, retention/deletion terms, fees and extraction process. Ask for archived point-in-time evidence separately: a current static snapshot does not prove historical availability.

## Draft inquiry (NOT SENT; user may edit and send)

件名：競走馬の血統・競走成績データの非営利学術研究利用について

ご担当者様

競走馬の血縁関係と個体の競走経験が、芝・ダート等の環境利用に関する予測情報にどのように関係するかを、生態学・統計学の観点から研究しております。馬券購入や予想情報の販売を目的とするものではありません。

学術研究のため、個体を安定して識別できる血統登録番号、父母の登録番号、登録状態、競走ごとの馬場・距離・出走および確定成績について、研究用データ提供または利用許諾の制度があるか伺いたく存じます。対象期間は2010年以降、特に2025〜2027年の新規登録馬を含む資料を希望しております。可能であれば、登録情報や競走成績の取得・更新時点が確認できる過去時点の資料についてもご教示ください。

個別の馬名・登録番号・元データは公表せず、許諾された範囲内で管理し、統計的な集計結果、図表、解析方法を学会発表・学術論文に用いることを想定しております。このような非営利学術研究、共同研究者との必要最小限の共有、および集計結果の公表に関する許諾条件、申請方法、提供可能項目、費用、必要な契約をご案内いただけますでしょうか。

利用規約の範囲を超える自動取得や再配布は行いません。ご検討のほど、よろしくお願いいたします。

## Stop/go

The next empirical step needs actual authorized data with enough known parents and coverage of new registrants plus auditable time-of-availability. Until then preserve 2025 primary uncertainty, do not fabricate new-entrant scores, and do not turn synthetic CI into empirical evidence. Keep licensed raw source outside public GitHub, and only share outputs under the provider's written permissions. If permission is declined, use genuinely licensed alternative research data or restrict the manuscript to the existing sources and their documented limitations. A mock original-push replay is not external attestation.
