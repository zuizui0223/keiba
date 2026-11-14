# Japanese Thoroughbred: maternal-source sensitivity and second-source audit

2026-11-14 — This is a source-quality and identifiability analysis, **not a heritability estimate or nationwide JRA/NAR pedigree census**.

## Baseline

The licensed 2026-11-14 Japanese Wikipedia horse-infobox snapshot contains 5,878 horse article IDs and 17,272,503 computed pairs. Among all article records, 4,304 have unambiguous linked father pages (73.2%) and only 642 have linked mother pages (10.9%). The latter is a major source-coverage defect; a numerical pedigree A of zero means only that no path was found in the **truncated documented pedigree**.

Original input SHA256: e4e25ba13754d8dc60a6160126b30c97641edea043c51be1c1120509d15c1a57.
Original Actions source: https://github.com/zuizui0223/keiba/actions/runs/43583807454 .

## Paired same-horse-pair evidence experiment

Script: scripts/ecology_japan_wikipedia_parent_ablation.py .

From the SAME original input and SAME actual horse identities, compute pairwise partial numerator A on three graphs: (1) all directly documented parents, (2) sire-page links only, (3) dam-page links only. Report how many positives are lost when documented maternal edges are removed, positive A changes and A-threshold crossings, plus birth-decade missingness. Compare three fixed cohorts: 5,878 Japanese-language articles, 3,411 explicitly Japan-born article entries, and the 38 Meisho-name entries. A full graph must never have less known-path A than its sire-only or dam-only deletion. This is an information-ablation exercise — it does **NOT** identify a paternal or maternal biological variance component, genetic selection, or inherited pacing.

## Secondary-parent ID coverage check

Script: scripts/ecology_japan_wikimedia_parent_crosscheck.py .

Bounded to at most 200 **targeted** Wikipedia horse articles, prioritizing 38 Meisho-name pages followed by deterministic sampled articles with unlinked mothers. Exact Japanese Wikipedia page-title -> wikibase_item QID -> direct Wikidata P22/P25 claims; no name matching or transliteration. Count source-consistent additional sire/dam IDs, overlaps and conflicts. A missing/ambiguous/rate-limited Wikidata response is HOLD, not biological absence, and these secondary-source records are NOT an independent official studbook verification. No raw horse identities or records are republished in the aggregated output. The 200-target sampling is not representative.

## National external benchmark

A 2024 published Japanese Thoroughbred study (doi:10.1294/jes.35.57) reported five-generation pedigree analysis of 346,744 Japanese-bred horses born from 1978, showing inbreeding increases partly linked to Sunday Silence and Northern Dancer lines. That published number is **not** a dataset retrieved or reanalyzed in this repository. It cannot be combined with the Wikipedia sample denominators; ancestry depth and selection differ.

## Required future population inference

Only an authorized fixed-version JRA+NAR actual-starter roster with canonical blood/breeding pedigree IDs, multi-generation parent data (including foreign founders) and independent source-rights review can support nationwide A/F. Predictive genetic behavior additionally needs verified historical early GPS or race outcome panels plus environmental, trainer, breeder, age and horse-history covariates with no lookahead.

## Credits

Japanese Wikipedia racehorse infobox source: CC BY-SA. Upstream original fetcher: https://github.com/Sheep-Meadow-Road-Games/open-horse-data. Credited as required: **Sheep Meadow Road Games / Horse Racing Manager** at https://store.steampowered.com/app/2740170/Horse_Racing_Manager/ . No licensed JBIS/JRA-VAN bulk datasets are republished.
