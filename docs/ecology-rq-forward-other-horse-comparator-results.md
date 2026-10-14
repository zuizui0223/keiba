# Can other horses' histories explain the focal horse's early GPS persistence?

**2026-10-14; original-source RQ Cannon Park data, post-hoc exploratory comparison.**
The new alternative-history source/decision contract was
[committed before inspecting this specific alternative-control outcome](ecology-rq-forward-alternative-history-lock.md).
However, *positive horse ID ICCs, cross-declared-jockey consistency
and past-horse vs zero-baseline time-ordered improvement were already
known*. This is **not a preregistered or independent biological
confirmation**, and no inferential p-value/CI or causal effect is claimed.

## Biological question

Past source-linked HORSES-ID-specific race-relative first-GPS
sectional time improves error for later source records with a
Jockey/@Id not previously documented for that horse in the
same original measurement context. But could this improvement
come only from stable **official distance/first GPS marker,
source-documented trainer or source-documented jockey** rather
than any additional horse-ID-associated information?

The comparison uses the **same future observations** for every
model being compared within each row of the table below.
All profiles use *strictly earlier original meeting dates*,
the same fixed n/(n+2) historical-mean shrinkage, and the
same original HORSES-ID/GPS join, with NO prediction trained on
today's or a later record.

The focal horse's historical profile uses only its own earlier
positive race-relative GPS observations in the same original
official distance and first measured GPS marker context.

The source-control profiles use only observations from
**OTHER official HORSES IDs**, excluding the focal horse:
(a) same distance and first marker, (b) same source
trainer licence and same context, or (c) same present
source jockey licence and same context. Trainer/jockey
values are **original nomination/roster data**, not
verified actual post-race assignments.

The race-relative outcome for horse i in source race r is

    original first-GPS section time(i,r)
        - mean(other GPS-positive horses' first-GPS sections in that race)

The target depends on the **observed postrace GPS field**;
therefore this is an out-of-time *descriptive persistence
check*, not a pre-race forecast, absolute pace model,
winning probability, wagering edge or fitness measure.

## Real source analysis

[Full 12/12 previously locked 2026 Cannon Park dates; first
official source re-run](https://github.com/zuizui0223/keiba/actions/runs/38563048063),
and [post-correction independently re-executed 12/12 source
run](https://github.com/zuizui0223/keiba/actions/runs/38563275612)
produced the same aggregate results. The latter additionally
passed [full 221-test ecology QA](https://github.com/zuizui0223/keiba/actions/runs/38563275573).
A test expecting the stricter Class-novelty cohort to be a
mathematical subset of the broad cohort was corrected before
the final QA; changing the Class key changes the source-rider
novelty history and can change eligibility in either direction.

Both original-source runs used **543** official original
HORSES-ID-linked GPS-positive candidate records;
**519** original timed rows were retained in races with
at least four positive GPS peers; 378 timed rows had a
valid source Jockey/@Id. The older 548-source-candidate
version remains a separate historical source snapshot
with missing old roster-XML digests, so its change mechanism
cannot be proved from this analysis.

### Primary: matched distance and first GPS marker (no Class restriction)

| Earlier source predictor matched on SAME future rows | Distinct HORSES IDs | Later source rows | Future dates | Equal-HORSES-ID weighted RMSE: focal horse profile | RMSE: historical OTHER-horse predictor | Earlier OTHER-horse RMSE minus focal horse RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Any other source horse under the identical marker and race distance | **36** | **46** | 11 | **0.255809 s** | **0.303195 s** | **+0.047386 s** |
| Other horse with the SAME documented trainer and measurement context | **23** | **31** | 9 | **0.223217 s** | **0.293963 s** | **+0.070745 s** |
| Other horse with the SAME currently documented jockey and measurement context | **32** | **39** | 10 | **0.246934 s** | **0.301783 s** | **+0.054849 s** |

For the **first row only**, the zero-profile benchmark on
those exact 46 future records had RMSE **0.297676 s**
(vs focal horse history 0.255809 s). The source/context
history benchmark was **0.303195 s**.
Thus historical focal HORSES-ID early-GPS timing carries
additional predictive information versus a simple
context-only history in these matched original observations.
The **0.047386 s advantage** of horse-specific over
other-horse history is about **15.6% of that other-horse
benchmark's RMSE**.

The trainer and rider rows are **separate selected subsets**:
they do NOT establish that the difference in the three
advantages is an effect of trainer or jockey assignment,
or that model coefficients can be partitioned into genetic
horse/rider/trainer variance components.

The source-rights and all missingness restrictions from
the original first-party
[Racing Queensland official open data](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
remain in force.

### Extra original race Class matching

| Same-Class comparator | IDs | Later rows | Status | Focal RMSE | Other-horse RMSE |
| --- | ---: | ---: | --- | ---: | ---: |
| Other horses with the same official distance, first GPS marker **and Class** | **20** | **22** | Exploratory boundary support | **0.320113 s** | **0.386706 s** |
| Same-Class and same source-documented trainer, other horses only | 9 | 11 | **HOLD** (below support gates) | Not reported | Not reported |
| Same-Class and same current source-documented jockey, other horses only | 13 | 15 | **HOLD** (below support gates) | Not reported | Not reported |

The source Class-matched comparison sits **exactly** on
the predeclared 20-HORSES-ID/20-context minimum.
More importantly, because "not previously documented
jockey" is evaluated *within the exact matching context*,
introducing Class creates a redefined, **not necessarily
nested** future evaluation cohort. Class and non-Class
differences must not be interpreted as an effect of Class
or the robustness of the *same exact observed future rows*.

The model reports numerical results only if there are
>=20 separate HORSES IDs, >=20 later records, >=6
future dates, and >=20 horse-by-context strata. Otherwise
it emits HOLD and does not turn absence of source support
into an artificial zero prediction gain.

## Software checks and reproducibility

- Original-source code:
  scripts/ecology_rq_forward_alternative_history.py
- In-memory integration:
  scripts/ecology_rq_rider_switch_consistency.py
- Fictional source-only counterexamples:
  tests/test_ecology_rq_forward_alternative_history.py
- Official aggregate-only workflow:
  .github/workflows/ecology-rq-rider-switch.yml
- Synthetic checks include source-only stable **trainer**
  effects (the trainer-peer profile correctly wins in that
  fictional scenario), stable planted animal effects,
  exact prior date ordering, same-day/late-source
  non-leakage, no focal horse in other-horse profiles,
  source jockey/trainer missingness and no fabricated
  ID-specific artifacts.

No original horse names, original numeric HORSES IDs,
original jockey/trainer licence identifiers, per-horse GPS
records/predictions or original XML payloads are published.
The artifact holds only aggregate source counts, model errors,
source SHA256 summaries and explicit HOLD status.

## Scientific interpretation boundary

**Qualified finding:** within this selected Cannon Park
official-source cohort, a horse's earlier relative initial
GPS timing predicts its later relative initial GPS timing
more accurately than the earlier source/context average
of different HORSES IDs; related matched declared-rider and
declared-trainer peer baselines also perform less well
on their **own, smaller paired eligibility sets**.

**Not resolved:** horse-intrinsic physiological/behavioral
personality, age, genetics, heritability, selective entries,
training regimes, actual postrace jockey or trainer,
GPS dropout, source edition drift, full official starters
or fitness. This does not identify H1 environment-specific
within-horse reaction slopes nor H2 response to competitor
composition. Because race-relative timing is mechanically
affected by the current peer field, it also does not
prove a social interaction effect or a pre-race absolute
horse speed prediction.

To separate individual biology from trainer/rider assignment,
the priority remains a properly rights-cleared, prospectively
fixed and starter/rider/results-verified longitudinal
cohort with adequate source replication. Do not tune
the benchmark after inspecting this favorable selected
result, and do not merge it into the betting-analysis PR.
