# Official Thoroughbred Weight/Jockey/Trainer adjustment to early-sectional ICC

**2026-10-13, REAL original Racing Queensland horses, EXPLORATORY
Gaussian mixed model and source-data-completeness audit.**

**Interpretation decision:** The horse random-intercept component
remains nonzero in a conditional model adjusting for observed riding
weight, declared jockey licence ID and trainer licence ID. **This
is not evidence for innate horse personality, heritability, selection,
ground-reaction slopes (H1), social competition (H2), or a causal effect
of jockey/trainer.** Source selective entry and incomplete rider
coverage are substantial.

Official source: [Racing Queensland Open Data Services
Protocol, §4.15](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).
The genuine \`GetHorsesForRace\` XML defines:
- \`Horse/@Id\`: original internal HORSES animal ID;
- \`Weight\`: declared riding weight (numerical, interpreted as kg);
- \`Jockey/@Id\` and \`Trainer/@Id\`: original **licensee**
  identifiers, which are not horse IDs and are not inferred from names.
The API does **not** supply a reliably verified biological age, a
guaranteed *actual post-race rider*, confirmed starter/finisher status,
or individual certified full-distance finishing time. No such fields
are guessed from the unofficial GPS timing string.

The original contemporaneous first positive GPS interval is from
[Racing Queensland Thoroughbred Sectionals and Position
Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).
The same original twelve 2026 Cannon Park meeting dates and conservative
official identity linking remain in the
[source calendar](ecology-rq-2026-calendar-cohort-lock.md).
No horse/rider/trainer identity, source raw XML or individual GPS
record is included in this PR or the aggregate CI artifacts.

## Missing source data: a major obstacle

The [original ICC](ecology-rq-real-horse-race-adjusted-icc.md)
used 523 first-GPS horse×race rows with >=4 valid timed
horses in 74 fields and reported a race-conditional Gaussian
ICC of **0.431738**.

The source-nuisance-data screen operates on **548**
initial original HORSES-ID / positive GPS observations
(before applying the new complete-covariate field minimum):

| Filtering stage | Original source rows |
| --- | ---: |
| All original ID × positive first GPS observations | **548** |
| After source Weight, Jockey licence and Trainer licence all available | **337** |
| After requiring >=4 **complete-source-covariate** GPS horses in the same race | **279** |
| Original records excluded from the final covariate-model sample | **269** |

The sequential source reasons included **148** original records
without a valid numeric jockey licence and **63** lacking
the corresponding trainer licence among the remaining records;
the measured weight was within the specified validity
interval for all these original source rows. These counts
depend on the source-gating order and should **not**
be treated as proven independent missingness causes.

The resulting 279 observations come from **54 races,
11 distinct source dates, 164 original HORSES IDs**,
and 71 HORSES IDs with >=2 timed positive GPS records.
This is **not the same animal population** as the
523-row original ICC. Directly comparing 0.431738
against the 279-record models would be invalid.

The new research code also prints **source retention by
original meeting date and race-level Good/Soft/Heavy**.
Such differential coverage can be informative missingness
related to the question. No MAR/MNAR assumption is
silently accepted; complete-case ICCs are explicitly
conditional on which fields and animals remain.

## SAME 279 horse×race observations, nested nuisance models

Model outcome = the **original absolute time in seconds
of the first positive GPS section**, *not*
full-race finish speed, rank or a relative-to-rivals
postrace score.

Race intercepts are treated as unrestricted fixed
effects (one per original event). Original numeric
HORSES ID has an exchangeable Gaussian
random intercept. Source covariates are held as
fixed nuisance terms for the same retained 279 rows.

| Nuisance fixed-effect specification | Conditional horse ICC point estimate |
| --- | ---: |
| Race intercepts only + random HORSES ID | **0.503005** |
| Plus within-race registered riding weight | **0.509202** |
| Plus common original jockey licence categories | **0.513500** |
| Plus common original trainer licence categories | **0.487447** |

The final minus same-source-sample baseline difference
is **−0.015558** on the ICC scale, not a valid causal
contribution or uncertainty interval.

Other source supports in the 279-row cohort:

| Data dimension | Count |
| --- | ---: |
| Original numeric jockey licences | 20 |
| Original numeric trainer licences | 41 |
| Jockey licences shared by >=2 distinct HORSES IDs | 19 |
| Trainer licences shared by >=2 distinct HORSES IDs | 23 |
| Individual HORSES IDs with 2+ different registered jockey licences | **45** |
| Individual HORSES IDs with 2+ different registered trainer licences | **1** |
| Original jockey licence categories with >=4 observed records | 15 |
| Original trainer licence categories with >=4 observed records | 18 |

**Crucial confounding:** For almost every recorded horse,
the trainer's source licence is stable. A trainer fixed
effect and a horse random intercept can remain highly
entangled because horses are nonrandomly allocated to
trainers and many trainers have only one observed horse.
The code estimates conditional variance under a
specific model; it **does not identify what is biologically
intrinsic to the horse**.

Sparse jockey/trainer IDs with <4 positive records are
held in an omitted source category (not asserted to
have zero true effect). If a whole nuisance category
is unidentifiable, the model returns **HOLD** instead
of fitting arbitrary dummy coefficients.

## Estimation and reproducibility

[\`scripts/ecology_rq_covariate_icc.py\`](../scripts/ecology_rq_covariate_icc.py)
parses the documented nested \`Jockey/@Id\`,
\`Trainer/@Id\` and numeric \`Weight\` fields only.
Unknown/zero licence IDs are excluded, without
guessing them from \`FullName\`.

For each original race, the same Helmert
orthonormal contrasts remove the unrestricted
race mean. Next, a full SVD removes the column
space of observed nuisance covariate predictors
from the reduced outcome and HORSES-ID incidence
matrix. The remaining error contrasts yield a
restricted Gaussian variance-component likelihood:

~~~text
first_GPS_sec_ir = alpha_race
                 + beta_weight * Weight_ir
                 + gamma_jockey[licensed_jockey_ir]
                 + delta_trainer[licensed_trainer_ir]
                 + b_HORSES[original_id_i]
                 + e_ir

conditional_ICC = Var(b_HORSES) / (Var(b_HORSES) + Var(e))
~~~

The four rows above use the **same source-matched
horse×race observations**, which is the proper
way to compare their descriptive point estimates.
The number of restricted contrasts decreases as
fixed nuisance terms are added (225 initially,
224 weight, 209 weight+jockey, 191 in the
complete fixed-effects nuisance model).

Different restricted profile objective values
between the models are **not directly comparable
as a likelihood-ratio test**, because each model
has a different fixed-effect contrast space.
No formal p-values or valid confidence intervals
have been calculated. The assumptions of
Gaussian iid conditional errors and homoscedastic
GPS noise remain unverified.

Synthetic tests in
[\`tests/test_ecology_rq_covariate_icc.py\`](../tests/test_ecology_rq_covariate_icc.py)
exercise: real-schema nested role IDs, invalid
weight and zero licence sentinels, source attrition,
identical modeling cohorts, race-common offset
invariance, planted fake weight association,
empty/single-ID HOLDs, and protection against
publishing licensee IDs and source horse names.

### Reproduce

~~~bash
python -m unittest discover -s tests -p 'test_ecology_rq_covariate_icc.py' -v

# No horse rows/IDs/jockey or trainer IDs are written:
python scripts/ecology_rq_2026_calendar_overlap.py \
  --output tmp/rq-original-2026-adjusted-horse-ICC-aggregates.json
~~~

Independent first original-source run:
[GitHub Actions #38366370065](https://github.com/zuizui0223/keiba/actions/runs/38366370065)
(12 source dates, above numerical results).
The [standard research test workflow](https://github.com/zuizui0223/keiba/actions)
also checks the wholly fictional design and
source-rights/identity HOLD safeguards.

## Genuine follow-up hypothesis, not yet supported

Can the original HORSES-ID repeatability observed
in early-section performance be separated from
stable rider/trainer allocations, horse age,
carried/riding weight, recent fitness and source
measurement selection **in another independently
defined racecourse/date cohort**?

The current answer is **UNRESOLVED**.
A fully identified scientific analysis needs
the actual final riding horse/jockey pairing
(not merely nomination lists), validated
individual age or date of birth, race rest time,
trainer continuity, all confirmed starters,
and systematically observed GPS timing or
official individual finish records. Source
outcome missingness by date/going/race class
must be handled rather than assumed ignorable.

Nakagawa & Schielzeth (2010), [doi:
10.1111/j.1469-185X.2010.00141.x](https://doi.org/10.1111/j.1469-185X.2010.00141.x)
is an appropriate reference for adjusted
repeatability and its estimand limitations.
**No H1 ground random slope or H2 opponent
social-context model was fitted to these
original sources.**
