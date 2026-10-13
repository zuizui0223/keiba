# Feasibility audit: obtaining legal longitudinal animal race performance data

Review date: **2026-10-12**. No external archive has been ingested
into this repo. Links below are **candidates**, not permissions.

## Data decision: choose a rights-cleared horse×race source before fitting

The actual H1/H2 research model requires repeat starts for stable
`horse_id`, race date, track/going, distance, individual performance,
historical early-running position, and all rivals per race, with
terms allowing the intended research and publication. Mere download
access does **not** imply redistribution or commercial permission.

| Candidate | What seems available | Rights/compatibility check | Current decision |
| --- | --- | --- | --- |
| [Racing Queensland official thoroughbred open data](https://www.racingqueensland.com.au/about/reports-and-data/open-data) | Official public thoroughbred meeting/race information with race results, sectionals/position maps listed in its data catalogue, and SOAP web services such as GetHorsesForRace and GetHorseDetailsInRace | Racing Queensland states public website/web-service information is free for use without copyright restriction, with accuracy and commercial-use caveats. **Not yet verified:** whether these methods expose a stable horse ID and individual elapsed time per historical start, full actual starter rosters, and programmatic chronology at useful depth | **PRIORITY EQUINE SOURCE—FIELD-LEVEL VERIFICATION PENDING** |
| [Australian Racing Open Data (PandaVision) Queensland greyhound GPS](https://github.com/brucem1967/au-racing-open-data) | Verified pinned ODC-BY file: 25,679 greyhound 50m sectionals and early positions. Dog names recur, track/date/box observed. [Frozen real-data benchmark](ecology-real-greyhound-method-benchmark.md) | Attribution explicitly provided; Racing Queensland public open-data permissions corroborated. **Species is greyhound, not horse**; no stable biological ID guarantee, no certified complete race fields, and no track going or official full-distance horse outcomes | **REAL CROSS-SPECIES METHODS PILOT ONLY—NO HORSE H1/H2** |
| [Existing 2026-10-12 Kyoto analysis branch](https://github.com/zuizui0223/keiba/tree/analysis/kyoto-20261012) | 7 races, 95 starters, historical aggregate course counts, odds snapshots; not full individual starts across environments | No longitudinal horse×race exposure panel; race snapshots not enough | **H1/H2 HOLD** |
| [Kaggle Hong Kong Horse Racing](https://www.kaggle.com/datasets/gdaley/hkracing) | `races.csv` plus `runs.csv`: stable horse and race IDs, ground conditions, distance, individual finishing time and first-sectional position, with repeated starts across races. Publisher describes dates as deliberately obscured | Dataset page claims **CC0**, but original HKJC/source-chain rights and obligations have not been independently verified. Obscured dates also prevent official-season/clock verification. Run our new **aggregate-only** `scripts/ecology_hk_preflight.py` on locally and lawfully obtained files; it refuses to promote this to the empirical H1/H2 pipeline | **TOP COMPATIBILITY CANDIDATE—PROVENANCE/TIMELINE HOLD** |
| [Kaggle JRA日本中央競馬会 dataset](https://www.kaggle.com/datasets/takamotoki/jra-horse-racing-dataset) and [usage README](https://github.com/evanfadhil/japan_horse_racing_analysis) | 4 CSV categories described: race results, corner passage order, laptimes, odds (scraped from netkeiba; older historical archive) | Source/CSV reuse terms and any netkeiba redistribution rights **not verified**; an MIT license for analysis code does not license the underlying source dataset | **CANDIDATE—RIGHTS HOLD** |
| [HK/SG historical racing archive](https://github.com/eprochasson/horserace_data) | Hong Kong/Singapore `performances`, `races`, `horses`, `sectional_times` CSV.gz; some historical record tables do not join 1:1 and may lack dates/races for earlier years | README says scraped from HKJC/SGTC, root has **no LICENSE file** (reviewed GitHub contents). Public GitHub alone does not establish permission to reproduce original results or provide a rights-cleared derived dataset | **CANDIDATE—RIGHTS HOLD** |
| [Huggy French race sample](https://huggingface.co/datasets/huggy-engine/horse-racing-database-fr) | Sample explicitly lists CC BY 4.0, `courses.csv` (~931 races) and `rapports.csv`; parent vendor advertises larger multi-year commercial collection | Current freely listed files are race-level and payouts, **not** the complete horse×race performance panel/positions needed for H2; attribution and source-chain checks remain necessary | **NOT SUFFICIENT FOR H1/H2** |
| [HKJC Guru historical results export](https://data.hkjc.guru/data/hkjc/hkjc_race_results) | Rich horse-level profiles and sectional times, paid archive | Site explicitly states redistribution of raw exports is not permitted. Evaluate research usage terms separately before payment, do not add proprietary exports to public GitHub | **RIGHTS / ACCESS HOLD** |
| [TrapStats greyhound CC BY sample](https://trapstats.co.uk/en/data) / [Zenodo CC BY greyhound research data](https://zenodo.org/records/19842376) | Runner×race records with track, going, finish, sometimes sectional/bend positions; a potentially relevant *other species* methodological comparison | Species is greyhound, not Thoroughbred; cannot be used as direct evidence about racehorses. Underlying source rights and full-file scope should be checked | **OPTIONAL CROSS-SPECIES METHODS, NOT HORSE EVIDENCE** |

## Minimum rights checklist before any authorized raw data enters pipeline

1. Confirm whether research use is allowed and whether derived
   coefficient tables/figures can be published; obtain written permission
   if raw results are contractually restricted.
2. Record original publisher, source URL, archived version/DOI, date of
   access, original license or written approval, and restrictions on
   redistribution and machine-learning analysis.
3. Use race date/time and official record version for provenance. Verify
   each derived pre-race variable was knowable before the target start.
4. Confirm individual identity across different courses and years,
   correct status of scratches/disqualifications/dead heats, and handling
   of same-time/tied finishing ranks.
5. Quantify how many horses have repeated starts under varying going
   **and** changing rival contexts. Small selected subsets can bias
   interaction estimates.
6. Keep source bulk files local/private if redistribution prohibited;
   publish only code, synthetic tests, permitted derived metrics and
   attribution.

## Recommendation

**First** seek permission or independently rights-clear a complete
longitudinal equine dataset with early-race sectional/position information;
the existing Kaggle JRA archive and HK/SG performance+sectionals are
worth screening, but have unresolved upstream conditions.

**Do not** treat a public scraper, a code repository's permissive license
or a free commercial preview as an explicit dataset license.

Until then, a substantial, reproducible **ecological research code base**
exists, but zero real-race H1/H2 biological claims are justified.


## New offline HK screen: turn a promising dataset into measurable readiness

The 2019 public Kaggle listing for
[Horse Racing in HK](https://www.kaggle.com/datasets/gdaley/hkracing)
describes `races.csv` / `runs.csv`, including `horse_id`,
`race_id`, `position_sec1`, `finish_time`, `going`, `distance`,
and stable horse-level metadata. The uploader marks the page **CC0**,
but this is not independent verification of the original provider's
rights to redistribute the records. Race dates have deliberately
been changed; they must not be re-labelled as official calendar time.

The following offline-only command screens schema compatibility,
joining, repeated individual starts, changing opponent sets, first
section measurement availability and missing finish times. It does
**not** scrape, download, reproduce individual rows, guess dates or
run the ecological model.

```bash
python scripts/ecology_hk_preflight.py \
  --races /private/hk/races.csv \
  --runs /private/hk/runs.csv \
  --audit tmp/hk-compatibility.json
```

Output will explicitly say `HOLD_SOURCE_RIGHTS_AND_OBSCURED_DATES`.
The full rights/timeline gate must be cleared independently before
any source data are published or analysis is represented as a
dated historical test. The local input files must remain outside
GitHub. A separate source-to-Japan-going mapping is scientifically
unresolved and will not be guessed automatically.

**Most promising path now:** source/rights review followed by this
preflight, then a carefully versioned data harmonization step.
No factual dataset has yet been ingested into the repo.


## 2026-10-13 preflight revision: conditional overlap rather than mere size

[scripts/ecology_hk_preflight.py](../scripts/ecology_hk_preflight.py)
now distinguishes:

- Horse repeated starts globally, including varying raw going labels.
- Within-horse repeated starts under **2+ observations in each of two
  different ground labels**, while holding venue, surface, exact
  distance and race class constant.
- Distinct opponent sets within the same race stratum, with at least
  4 starts (a necessary support screen, not identification).
- Starts recorded on the same **obscured** calendar date which cannot
  be ordered without verified race clock information.

An artificial counterexample in the CI tests assigns all GOOD
races to one class and all YIELDING races to another. The preflight
correctly refuses to count this as same-stratum environmental
replication, despite global within-horse variation.

The Kaggle dataset's reported 1997–2005 period and obscured date
labels must not be treated as an authoritative racing calendar. This
preflight has **not** been run against the actual Kaggle CSVs.
Upstream rights remain unverified, so no record-level data were copied
into the public repository.


## Verified cross-species methodological proof, 2026-10-13

A real racing-animal GPS dataset has now been processed, *without
claiming that it contains horses*. Frozen data revision and the
first 50m repeated-exposure summary:
[Queensland greyhound analysis](ecology-real-greyhound-method-benchmark.md).
The raw data are not mirrored or committed in this repository; the
source states **ODC-BY 1.0**. [Racing Queensland's public open data
page](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
is additional upstream rights context, but its explicit access,
accuracy and commercial terms continue to apply.

### Focused next-equine acquisition priority

**Official Racing Queensland (thoroughbred)** is the highest-value
access route to inspect: the operator's official open-data catalogue
lists race results, position maps and sectionals, with SOAP interfaces
for dates, races and horses (see
[Meetings.asmx](https://www.racingqueensland.com.au/OpenDataWebServices/Meetings.asmx)).
No individual result payload has yet been checked or ingested.
Before calling it an H1/H2 data source, verify in a *small,
documented sample*: stable horse identity; real local dates; actual
starter versus non-starter; horse-specific elapsed times and
first-sectional positions; track going, distance, class and venue;
enough historical depth to see the same horses under distinct
environments and rival rosters.

If these are absent in public SOAP fields, a manual export from
explicitly open race/sectional CSV or PDF may be required, and must
pass the same provenance and anti-leakage checks. The project must
not synthesize missing horse IDs or longitudinal start records.

**Species boundary:** the licensed greyhound test provides a
pragmatic *methods* calibration, but not an empirical test of
Thoroughbred individual reaction norms or social plasticity.
