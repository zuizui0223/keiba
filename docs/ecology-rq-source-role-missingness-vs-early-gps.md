# Real Thoroughbred source-metadata missingness vs observed early GPS time

**Real-data source-quality audit, 2026-10-13.**
**NOT** a test of complete race outcomes, missing true finishing times,
ground reaction norms (H1), biological social effects (H2), or MCAR.

Original independently rerun data:
[GitHub Actions #38403358393](https://github.com/zuizui0223/keiba/actions/runs/38403358393).
Program:
[\`scripts/ecology_rq_role_missingness_audit.py\`](../scripts/ecology_rq_role_missingness_audit.py).
The test suite uses **fictional** identities in
[\`tests/test_ecology_rq_role_missingness_audit.py\`](../tests/test_ecology_rq_role_missingness_audit.py).

Original publisher:
[Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
and [original Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).
Official source identity = internal \`HORSES\` numeric identifier,
exact within-race name linked to **positive** early-GPS
interval duration. The original public \`GetHorsesForRace\`
response may have \`Weight\`, \`Jockey/@Id\`,
\`Trainer/@Id\` or may be missing these items.

**Restricted population:** source horses with a positive GPS
initial segment already recorded. The audit does not
observe horses without GPS and does not know which
nominees officially started or completed the distance.

## Question and exact within-race contrast

A prior [same-source-sample adjusted
ICC](ecology-rq-real-horse-weight-jockey-trainer-adjusted-icc.md)
lost **269/548 = 49.1%** of its original candidate
records after requiring complete role metadata
and >=4 such horses within a race.

Question: *Among horses with a recorded first GPS
interval, do records with complete public
weight/jockey/trainer licence fields have
systematically different initial sectional
times than records with ≥1 missing field
**in the very same official race**?*

For each race with >=4 positive GPS horses and
at least one horse in each metadata group:

~~~text
D_r = mean(first_section_sec | all role fields documented, race r)
      - mean(first_section_sec | ≥1 role field missing, race r)

D = mean_races(D_r)
~~~

A **negative** value means documentation-complete
horses had a slightly shorter observed initial
interval. Race differences remove the event-wide
ground/distance/class/weather timing mean.
This does **not** account for individual ability,
weight/age, trainer allocations, GPS selection
or final confirmed starter status.

Permute only the **record-documentation-completeness
labels** 499 times inside each original race,
preserving the recorded sectional durations,
field size and original number of complete and
incomplete records. This is an observational
algorithmic reference, **not** a valid randomized
experiment or confirmatory p value.

## Actual source results

| Input/subset | Verified count |
| --- | ---: |
| Original source GPS-positive internal HORSES-ID rows | 548 |
| Original races represented | 84 |
| Races with >=4 positive GPS horses | 74 |
| Positive-GPS horse rows in these races | 523 |
| Documentation complete / incomplete among these 523 | 324 / 199 |
| Races with **both** documentation groups | **68** |
| Individual observed GPS times in those 68 mixed-source races | **491** |
| Complete / incomplete in mixed races | **297 / 194** |
| Meeting dates with mixed documentation races | **11** |

**Equal-race weighted documentation-complete
minus incomplete initial sectional contrast:
−0.0235497 seconds**.

A second, harmonic-group-size weighted
summary was **−0.0268476 seconds**.
Exactly **34 of 68** races had positive
group differences and **34** negative.

With 499 race-stratified documentation-label
reassignments, the null reference mean was
approximately **0.00000155 seconds**.
Its **5th/50th/95th** percentiles were
**−0.049776, −0.0006975, +0.049056 seconds**.
The two-sided absolute-label-shuffle reference
fraction was **0.416**. This is **not**
a calibrated biological or missing-data p-value.

### By original race-level ground (still exploratory)

| Original TrackRating | Mixed-source races | Complete minus incomplete mean first-section time |
| --- | ---: | ---: |
| Good | 22 | **−0.079391 s** |
| Soft | 27 | **−0.014241 s** |
| Heavy | 19 | **+0.027880 s** |

The ground-specific signs differ; they are
**post-hoc subgroup descriptions** from
only the races containing both metadata
groups. They are not evidence that track
going causes a documentation effect.
Ground-group means also reflect different
horses and race conditions.

Delete one original meeting date at a time
from the 68 mixed-source races:
**−0.044073 to −0.000577 seconds**
over 11 re-fits. All 11 descriptive
means remained negative, but this
is **not a 95% confidence interval**
or a prospective independent confirmation.

## Interpretation: what this does and DOES NOT justify

This negative-control-like selection audit
found **no prominent global, race-controlled
first-GPS timing separation** attributable to
completeness of the public recorded
Weight/Jockey/Trainer metadata under the
simple race-stratified descriptive test.
That is useful additional evidence
about a **measured** selection component.

It does **not** establish that records are
MCAR/MAR, nor that the missing outcome times
of horses without GPS resemble times of
horses with GPS. It cannot validate
inclusion of final starters, or prove that
full ICC on 523 rows and adjusted ICC on
279 rows should match.

The much more severe problem remains:
**49.1% of initial eligible source
records are lost in the fully adjusted
same-row model**, and the retention
fraction differs by actual ground:
Good 47.8%, Soft 56.9%, Heavy 45.9%.
One source date (2026-04-04) disappears
from the adjusted source cohort altogether.
These changes in the distribution of
race environments and horse/trainer
links can bias population generalization
even if the group means of observed GPS
times are similar.

Missing-data context:
Dumelle et al. (2025), *Missing data
in ecology: Syntheses, clarifications,
and considerations*, Ecological Monographs,
https://doi.org/10.1002/ecm.70037.
The paper distinguishes MCAR/MAR/MNAR
assumptions and complete-case, weighting,
imputation and sensitivity methods. We
have **not** applied a validated inverse-
probability or MNAR correction here.

## Required next inference gates

- Independently confirm actual starters,
  finishing status, animal-specific finish
  or sectional outcomes and final race
  jockey/trainer/weight assignment
  from an authoritative official results source.
- Measure official source role-field
  completeness, unobserved GPS timing
  and race participation **separately**.
- Validate a missingness/selection
  model with overlap and positivity
  before claiming any inverse-probability
  estimate identifies the all-starter
  animal population.
- For the fitted source-complete ICC,
  delete one original meeting date
  at a time (same underlying rows for
  adjusted vs unadjusted), inspect
  variance component stability, and
  calibrate uncertainty under realistic
  small-cluster dependence. Report
  **HOLD** where model support is
  too weak.
- Continue to keep the separate
  H1 ground reaction-norm slope and
  H2 social context hypotheses on
  research HOLD. Neither is tested
  by observed first-GPS completeness.

~~~bash
# No original animal data are written
python -m unittest discover -s tests -p 'test_ecology_rq_role_missingness_audit.py' -v
python scripts/ecology_rq_2026_calendar_overlap.py \
  --output tmp/rq-documentation-selection-2026-aggregates.json
~~~

**Nothing in this source-completeness audit establishes
genetic heritability, adaptation, a causal training
mechanism, or a gambling-market advantage.**
