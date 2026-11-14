# Japan Meisho study: *bloodlines, naming and ownership are distinct networks*

Date: **2026-11-14**.
Status: **11 manually verified public JBIS profile facts; no real future-performance prediction yet**.

## Core ecological question

Is repeatable early-race pace prediction attributable to **an individual horse's own historical behavior**, **documented pedigree-linked relatives' prior behavior**, or **non-genetic assortative organization around owners, trainers, breeders and named racing stables**? The Meisho prefix is an unusually useful *case study*, but not a biological clade.

Crucial: **メイショウ is a naming/ownership convention, not an inherited genetic family.** The founding owner 松本好雄 and relatives, including 松本好隆, use the prefix; a record may retain the prefix even if the listed owner changes. Owner name labels are not canonical owner IDs and may change across time.

## Real public registry demonstration

The curated, **nonrepresentative** sample in
docs/evidence/japan-meisho-manual-profile-snapshot-20261114.json
contains **11 selected registered horses**, of which **9 have メイショウ in the name and 2 do not**. The 11 have **11 distinct reported sire names** and **4 distinct currently displayed owners**. These counts are selection artefacts of the example sample, **not population estimates**.

Verified maternal half-sibling links (different published sire names and same registered dam ID):

| Registered pair | Documented common dam | Minimal A from only linked maternal path | Prefix / currently displayed owner |
| --- | --- | ---: | --- |
| メイショウタバル × メイショウメイスイ | メイショウツバクロ (JBIS 0001121214) | 0.25 | Same prefix; different currently displayed owners (松本好隆 vs 鈴木雅俊) |
| メイショウハリオ × テーオーロイヤル | メイショウオウヒ (JBIS 0001096629) | 0.25 | Different prefix; different currently displayed owners (松本好隆 vs 小笹公也) |
| メイショウツバクロ × メイショウカンパク | ダンシングハピネス (JBIS 0000613233) | 0.25 | Same prefix and same currently displayed owner (松本好雄) |

Additionally, メイショウカンパク and メイショウタバル have a **documented two-generation maternal path** with truncated-pedigree A=0.125: the mother of the latter (メイショウツバクロ) is the maternal half-sibling of the former. This path is a genuine source-audited biological relationship; the *numerical* A assumes unlinked ancestors are unrelated founders. **Do not mistake this for whole-pedigree or genomic A.**

Across all 11 deliberately selected profiles, the software finds **3 documented different-sire same-dam pairs**, of which **1 crosses the naming prefix and 2 cross currently displayed owner labels**, plus **13 pairs with at least one known maternal path** (including direct mothers and indirect two-generation connections). **The remaining pairs are UNKNOWN, not proven unrelated**; a missing sire ID is not a negative genetic finding.

Primary individually audited JBIS pages:
- https://www.jbis.or.jp/horse/0001335651/ — メイショウタバル, sire ゴールドシップ, dam メイショウツバクロ
- https://www.jbis.or.jp/horse/0001267813/ — メイショウメイスイ, sire ノヴェリスト, dam メイショウツバクロ
- https://www.jbis.or.jp/horse/0001121214/ — メイショウツバクロ, dam ダンシングハピネス
- https://www.jbis.or.jp/horse/0001046777/ — メイショウカンパク, dam ダンシングハピネス
- https://www.jbis.or.jp/horse/0000613233/ — ダンシングハピネス
- https://www.jbis.or.jp/horse/0001234732/ — メイショウハリオ, sire パイロ, dam メイショウオウヒ
- https://www.jbis.or.jp/horse/0001266566/ — テーオーロイヤル, sire リオンディーズ, dam メイショウオウヒ
- https://www.jbis.or.jp/horse/0001096629/ — メイショウオウヒ
- https://www.jbis.or.jp/horse/0000760084/ — メイショウサムソン, sire オペラハウス
- https://www.jbis.or.jp/horse/0000310442/ — メイショウドトウ, sire Bigstone
- https://www.jbis.or.jp/horse/0001123893/ — メイショウマンボ, sire スズカマンボ

No automated JBIS scraping, live-performance harvesting, bulk duplication or commercial data transfer was performed. Current owner/trainer display may reflect later transfers; **never retrospectively assign those current labels to an earlier race**.

Executed first-party check:
https://github.com/zuizui0223/keiba/actions/runs/43579722814 .
The action tests stable IDs, original source URL pairs, canonical maternal references, partial A, and absence of unsupported unrelatedness claims.

## Falsifiable hierarchy: same future targets

The new offline scorer scripts/ecology_japan_meisho_forward.py implements five frozen, out-of-time models:

- **M0**: training-only venue × first-GPS-marker × official-distance × going × class baseline + focal horse's prior first-sectional absolute time, with fixed shrinkage.
- **M_name**: M0 + earlier other horses with the same exact メイショウ naming prefix (only for a Meisho-named focal). It is a naming/organizational association, not kin.
- **M_owner**: M0 + earlier other horses appearing under the same documented **as-of owner ID**. Never use current 2026 profile owner as if it was the past owner.
- **M_kin**: M0 + earlier documented relatives' times weighted by source-verified pedigree numerator A (threshold 0.125), one historical mean per other horse.
- **M_owner_plus_kin**: M0 + owner + kin, with their two incremental weights tuned **only on earlier inner validation dates**. This is an observational interaction of information channels, NOT a fitted causal decomposition.

All channels are scored on **the identical held-out, exact-context-supportable target horse-race rows**, and explicitly report true first-observed horses, Meisho-named targets and Meisho-named cold starts. Weight candidates: {0,0.25,0.5,1}; both inner/outer splits are by whole race date. Missing actual GPS data, owner history or pedigree coverage must not be treated as zero observed effects.

### Required private/authorized CSVs

The observations file has all original pedigree-forecaster columns plus **horse_name, owner_id, owner_known_on** (historical owner source timestamp/datestamp strictly earlier than the recorded race date). The pedigree file remains **horse_id, sire_id, dam_id, known_on**; those IDs must link to the *same* canonical horse IDs used in observations. There is **no automatic matching** between JRA-VAN IDs and JBIS profile URLs; formal audited ID crosswalk required.

Example commands (only after license and identity gates):

~~~bash
python scripts/ecology_japan_meisho_audit.py \
  --profiles docs/evidence/japan-meisho-manual-profile-snapshot-20261114.json \
  --output tmp/japan-meisho-profile-audit.json

python scripts/ecology_japan_meisho_forward.py \
  --observations /private/licensed-japan-early-GPS.csv \
  --pedigree /private/verified-japan-parent-ids.csv \
  --output /private/japan-meisho-prefix-owner-kin-future.json
~~~

## What was tested, and what remains untested

- **REAL:** A minimal maternal-line graph and named/owner grouping disagreement on a hand-selected set of *public pedigree metadata*. Not an effect size on real racing performance.
- **SYNTHETIC:** Name-only/owner-only/kin-only/joint forecasts, chronological information leakage, unknown cross-owner or cross-trainer contexts, 3 false-positive mechanisms. Software QA is not biological evidence.
- **HOLD:** Japan-wide Meisho race-history panel, original 2026 owner/rider changes and final-starter denominator, parentage join across two primary registries, actual early GPS outcome coverage, genuine time-forward forecasting, sire/dam variance components, pedigree-vs-shared environmental separation, ABM/PDE/odds integration.

Relevant JRA-VAN Data Lab official published data catalogue: https://jra-van.jp/dlb/ddata.html ; it lists racehorse, owner, breeder, trainer, breeding and offspring data products, but the catalogue is **not proof that this runtime already possesses or may republish them**. Data rights, as-of snapshot and entity-key mapping must be validated first.

**Proposed scientific angle:** In a managed competitive population, genetic relatedness and human organizational networks can overlap but do not coincide. Test whether historical phenotype transfer is explained by **genetic relatives**, **shared ownership/management**, or **individual-specific persistence**; then consider more complex opponent-kin assortative competition (H2) only with official actual-starter and absolute section data. No breeding adaptation, selection or wagering profit is established by these lineage examples.
