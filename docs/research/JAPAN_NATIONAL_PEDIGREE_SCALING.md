# Japan JRA + NAR national pedigree relatedness: all-horse computation gate

**Update: 2026-11-14. REAL large source-conditional Wikipedia pedigree subset computed (5,878 articles; all 17,272,503 unordered pairs). STILL NOT the complete JRA+NAR racehorse population.**

## Population and source rights

Target population is *all real Japan-registered racehorses* (JRA/NAR, including retired horses and imported entries) within an explicitly fixed registry snapshot and observation period. A separate genealogy table must contain all required parents (including foreign ancestors) so unknown ancestral relationships are not inadvertently erased. An ancestor does **not** automatically become a target Japanese racehorse.

- JBIS states that its searchable system contains **about 1.17 million light-breed horses**, a figure including racehorses, sires, broodmares, foals and horses outside Japan, not an independently verified count of Japanese JRA+NAR racehorse registrants. https://jbba.jp/data/site/ .
- JBIS offers extensive public individual pedigree pages but explicitly restricts bulk reproduction, modification and third-party distribution without permission: https://www.jbis.or.jp/help/use/ . Do NOT crawl 1.17 million profile pages or mirror the records.
- JRA-VAN Data Lab (https://jra-van.jp/dlb/ddata.html) publishes the **specification and availability** of horse, breeding and progeny record types, not freely reusable raw nationwide pedigree exports. JRA records alone do not establish a complete NAR register or long-lived foreign ancestor identity. An authorized, locally exported and independently joined registry is needed.
- Wikidata CC0 can support a *small* transparent secondary-data pilot but **not national completeness**. Wikimedia offers horse mother/father relations via structured P25/P22 and CC0 source terms (https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service).

## Exactly what was computed on REAL horse identity facts

### A. Curated actual Meisho-related horses

The previously independently checked 11-profile JBIS demonstration (docs/evidence/japan-meisho-manual-profile-snapshot-20261114.json) was converted into 11 canonical IDs and the 6 independently linked **maternal** parent IDs. **No canonical father IDs are present**. This is not all horses sharing the Meisho prefix.

- **11 real horses; every 55 unique pair i<j was queried** with the exact additive numerator recurrence.
- **13 of 55 pairs have a nonzero path through documented mothers.** Other 42 pairs have **NO DOCUMENTED PATH**, not known actual zero genetic relatedness.
- **3 same-dam pairs**, but no formal full vs maternal-half status from canonical sire IDs; published sire *labels* are different and the manual study documented them, but the strict computation deliberately does not promote name labels into pedigree parent IDs.
- Examples: Meisho Tabaru vs Meisho Meisui **partial A=0.25**; Meisho Tabaru vs Meisho Kanpaku **partial A=0.125**; Tabaru vs its mother Meisho Tsubakuro **A=0.5**. The actual whole-pedigree A may be greater.
- Partial F is zero in this sample only because none of the six recorded mothers has two verified parent IDs in this local graph. **This is NOT evidence that the horses are biologically outbred.**
- Source-conditional independent GitHub test and execution: https://github.com/zuizui0223/keiba/actions/runs/43582382093 .

### B. Wikidata CC0, *reported* Japan country-of-origin

A bounded original WDQS (P31/P279* Horse, P495 Japan, optional P22/P25) query **returned 12 Wikidata QID horse records**. **All 66 unordered pairs** were calculated using only the parent relations in these 12 source items, with absent ancestors as computational founders.

- 12/12 had a recorded sire QID, 3/12 had a recorded dam QID; **2 shared-sire pairs** had documented **partial A>=0.125** (both 0.25 under the observed one-parent link).
- The request to resolve 13 distinct ancestral QIDs returned **HTTP 429**, so the deeper pedigree could not be reconstructed. Parent paths not observed remain unknown. No prediction or additive-genetic heritability estimate was made.
- This P495 Japan metadata filter is extremely incomplete for national horses, and **not interchangeable with JBIS IDs** or the curated 11 horses. No attempted total 23 *unique* horses is asserted: overlapping identities across independent registries have NOT been checked.
- Actual source check: https://github.com/zuizui0223/keiba/actions/runs/43582522592 (GitHub Actions aggregate logs). The attempted query is bounded and does not bulk crawl JBIS.

These are **numbers of partial documented genealogical relationships**, not a genetic association with speed or race performance.

## C. Large publicly licensed Japanese Wikipedia horse article sample — newly measured

A separate GitHub Actions run directly downloaded the CC BY-SA Japanese Wikipedia {{競走馬}} article infoboxes (using the license-attributed third-party fetcher) and computed **all pairwise exact partial A values for the observed article cohort**, not a random-pair extrapolation. **No JRA/JBIS/NAR bulk profile data were harvested.**

**Fixed original-source SHA256**: e4e25ba13754d8dc60a6160126b30c97641edea043c51be1c1120509d15c1a57.
**Original successful computation**: https://github.com/zuizui0223/keiba/actions/runs/43583807454 .
**Reconciled aggregate evidence**: [docs/evidence/japan-wikipedia-actual-kinship-20261114.json](../evidence/japan-wikipedia-actual-kinship-20261114.json).

| Metric | All Japanese-language horse articles | Subset with infobox country explicitly Japan |
| --- | ---: | ---: |
| Real source article identities | **5,878** | **3,411** |
| All distinct i<j A pairs computed | **17,272,503** | **5,815,755** |
| Nonzero A in the truncated documented pedigree | **5,327,594** | **2,555,223** |
| A>=0.125 (including more strongly related pairs) | **201,794** | **163,107** |
| Documented father page link in the target | **4,304** | **2,822** |
| Documented mother page link in the target | **642** | **472** |
| Full-sib pairs with both parent page IDs | **86** | **68** |
| Maternal half-sibs with fully distinguishable father pages | **165** | **131** |

Real source association is verified here; biological whole-pedigree coefficients and national coverage are **NOT** verified. The 5,878 pages include horses from outside Japan, and the 3,411 with Japan in the infobox country field exclude imported horses that raced in Japan. Both are article-selected populations, so reporting either as "all Japanese racehorses" would be false. Parents were linked only by exact unambiguous Wikipedia article-title hyperlinks; absent links were not guessed from labels. Zero A is **no path in the recorded pedigree**, not genetic unrelatedness.

**Major quality limitation:** 73.2% had an unambiguous father link, but only 10.9% had an unambiguous mother link in the all-article source. Strong paternal coverage and missing mothers make the observed A distribution and any derived inbreeding F highly sensitive to source completeness. The counted positive pairs can include extremely weak common-ancestor paths, so A>0 is not the same as being close kin. The predeclared partial A bins are saved in the evidence file.

**Meisho target:** 38 racehorse article titles start with メイショウ; the first version's all-pair pass counted 311 positive documented pedigree paths among within-prefix pairs and 82,634 between a Meisho-prefix article and another named horse article, but these are **Wikipedia-selected** naming groups, not the population of all Meisho-owned or named horses. No owner/management-causal or racing-performance effect is established.

**Attribution:** Uses the external extractor from [Sheep Meadow Road Games open-horse-data](https://github.com/Sheep-Meadow-Road-Games/open-horse-data). As required by its LICENSE, credit **Sheep Meadow Road Games / Horse Racing Manager**, https://store.steampowered.com/app/2740170/Horse_Racing_Manager/ . Japanese Wikipedia source: CC BY-SA; do not relicense or mirror its raw records without complying with those terms. Only non-personal aggregate counts and source SHA are committed here.

### Why the licensed official registry is still needed

An official complete source can resolve dam lines, foreign ancestors, non-notable runners, exported Japanese horses, ownership histories and same-name ambiguity with genuine stable identifiers. The official TARGET CSV data dictionary has **血統登録番号**, **繁殖登録番号**, **父繁殖登録番号** and **母繁殖登録番号**, which are **not interchangeable identifier namespaces**. The new private adapter \`scripts/ecology_jravan_blood_breeding_id_bridge.py\` performs typed crosswalks and explicitly refuses name-only/ID-collision joins; no licensed bulk export is present in this PR.

## Full-registry implementation

scripts/ecology_japan_registry_pedigree.py accepts an **authorized local CSV** with mandatory columns:

    horse_id,sire_id,dam_id

Optionally include horse_name. Use ONE independently established canonical ID system; blanks represent unknown parents; parent IDs not found as rows are treated as *unresolved founder placeholders*, not eliminated. Duplicate IDs, self-parenting, sire=dam and pedigree cycles fail closed.

For the complete Japanese racehorse *target* subset, also provide:

    horse_id

in a separate target ID CSV. The comprehensive genealogy can additionally contain ancestors of those targets, but it must NOT infer the horses' JRA/NAR/foreign cohort membership from their names.

Supported outputs:

1. Per-target pedigree inbreeding coefficient F from documented ancestry, verified sire/dam coverage, numbers of target full-sibs, confirmed paternal/maternal half-sibs, and same-sire or same-dam other targets.
2. Aggregated sibling-pair counts without materializing all O(N^2) pairs. A full-sib requires BOTH parents documented; a half-sib requires the other parent's verified ID to differ.
3. On-demand exact numerator A(i,j) with the recursion A(i,i)=1+A(sire(i),dam(i))/2 and A(i,j)=[A(sire(i),j)+A(dam(i),j)]/2 after ordering younger-to-older, and normalized r(i,j)=A(i,j)/sqrt[A(i,i) A(j,j)]. The unknown founder assumption is explicit.

Example on authorized LOCAL/private source:

~~~bash
python scripts/ecology_japan_registry_pedigree.py \
  --pedigree /private/japan_and_foreign_pedigree.csv \
  --target-ids /private/jra_nar_registered_horse_ids.csv \
  --summary /private/japan_kinship_coverage_summary.json \
  --per-horse /private/japan_all_registered_horses_partial_F_siblings.csv

# A distinct, independently enumerated set of requested pairs
python scripts/ecology_japan_registry_pedigree.py \
  --pedigree /private/japan_and_foreign_pedigree.csv \
  --target-ids /private/jra_nar_registered_horse_ids.csv \
  --summary /private/selected_pair_summary.json \
  --pairs /private/focal_pair_requests.csv \
  --pair-output /private/selected_kinship_A_r.csv
~~~

The pair-requests file needs columns horse_id_1,horse_id_2. Results from this command are private by default. Do NOT check licensed raw or output files into public GitHub.

For N=1,170,000 (a hypothetical computational ceiling, **NOT the true JRA/NAR target count**), a full double-precision symmetric N-by-N matrix requires **~10.95 TB**, or **~5.48 TB** for one triangular half without labels/indices. Pair counts from shared parents are O(N) counting. On-demand requested A is far more practical. The prototype's CI checks 3,000 artificially related horses, validates 4.5 million shared-parent pairs **without enumerating them**, and tests 11 real horses; million-horse performance has **NOT** been measured and must not be promised.

## Current decision

- **Real calculation performed** on two narrow identity cohorts with positive documented kin paths.
- **Not performed:** all Japanese racehorses, all JRA/NAR pedigrees, countrywide F distribution, countrywide full-sib or mean kinship, or full N×N relationship matrix.
- **Reason:** the complete licensed and canonical ID-linked source tables are not accessible in this execution environment; there is no permission to bypass publisher restrictions by wholesale profile scraping.
- **Next concrete data gate:** one rights-cleared, as-of fixed genealogy + target registry export; exact ID crosswalk audit; report missing sire/dam/ancestor coverage by cohort and birth year before any biological interpretation.
