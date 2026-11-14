# Japan JRA + NAR national pedigree relatedness: all-horse computation gate

**Update: 2026-11-14. STATUS: ONLY TWO SMALL REAL SUBSETS COMPUTED. NOT ALL JAPANESE HORSES.**

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
