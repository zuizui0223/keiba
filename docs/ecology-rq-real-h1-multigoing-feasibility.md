# First original Thoroughbred Good–Soft–Heavy within-horse design audit

**Frozen real-source feasibility result:** 2026-10-13.
**Conclusion: partial individual-environment overlap has been proven,
but H1 individual reaction-norm variance and H2 competitive-context
effects remain UNIDENTIFIABLE under the strict repeated-stratum gate.**

Independent CI result:
[38346277581](https://github.com/zuizui0223/keiba/actions/runs/38346277581).
Read-only replication:
[`scripts/ecology_rq_multigoing_h1_preflight.py`](../scripts/ecology_rq_multigoing_h1_preflight.py).

## Official sources, locked design and permissions

Data publisher: Racing Queensland, via its official
[open-data program](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
and
[Thoroughbred Sectionals and Position Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).
Source uses official `GetMeetingsForDate`,
`GetRacesForMeeting` and `GetHorsesForRace` with
the original numeric `HORSES` internal horse ID.

Exactly five Cannon Park meetings were selected and exactly
race numbers **1, 2, 3 and 8** requested on each date.
This was selected to check source *identifiability*, not to
maximize evidence for a wet-track effect or claim a
representative racehorse population.

| Original meeting | Public meeting ground description | Original SOAP race-level ground class | Official ID×positive first-section rows |
| --- | --- | --- | ---: |
| 2026-05-15 | Heavy 9 | Heavy | 21 |
| 2026-05-29 | Soft 5 | Soft | 24 |
| 2026-08-22 | Soft 6 | Soft | 33 |
| 2026-08-29 | Good | Good | 33 |
| 2026-10-11 | Good | Good | 32 |
| **Total** | 3 distinct ground classes | All metadata agreed | **143** |

Every requested one of the **20** race numbers had a
numeric original-source `Race Id` in this selected subset.
The archive contains source SHA-256 for each official
meeting/race response and original GPS CSV in the attached
aggregate-only CI artifact. No original horse names, original
numeric horse IDs or runner-level times are published by the
research scripts.

**Important:** the SOAP class is categorical (`Good`, `Soft`,
`Heavy`); no assumption of equal spacing between
Good 4, Soft 5, Soft 6 and Heavy 9 is made. The meeting web
rating and individual race metadata represent different
levels of measurement and were checked for class agreement.

## Genuine within-source HORSES identity overlap

| Audit step | Available |
| --- | ---: |
| Unique official numeric IDs after strict same-day name/ID ambiguity exclusion | 107 |
| Official IDs recurring on 2+ distinct dates | 26 |
| Recurring IDs observed on Good and Soft/Heavy dates | **20** |
| Good–Soft recurring IDs | 15 |
| Good–Heavy recurring IDs | 8 |
| Good/non-Good contrasts with same race distance and same first-section marker | **10** IDs |
| Same distance, first-section marker **and race class** | **1** ID |
| Same matched class/distance/marker with at least **2 Good and 2 non-Good starts** | **0** strata |

The Good–Soft and Good–Heavy counts overlap: a horse ID can be
listed in both. There are more than 20 potential simple
cross-ground source records, but that does *not* identify
individual random slopes with class and route controls.
Class and distance confounding drastically reduce
the usable matched-context sample.

## Cautionary descriptive sign check (NOT a ground effect)

For 10 IDs with at least one first-section measurement under
Good and non-Good conditions **at the same recorded first distance
marker and same race distance**, the *non-Good minus Good*
initial segment time averaged **−0.2885 s** across horse-specific
strata; 8 differences were negative, 2 positive.

This is **NOT evidence that horses run faster on softer/heavier
tracks**. It is an undercontrolled opportunistic descriptive
contrast, susceptible to class, weather, recent condition,
race tactics, starter selection, track preparation, jockey,
measurement differences, and unequal number of attempts.
When race class was also matched, only **one** candidate ID
remained (contrast −0.48 s, one comparison). Even that one
animal has insufficient within-stratum independent
replication to estimate a reliable reaction norm.

Consequently **no confidence interval, p-value,
reaction-norm variance, positive effect claim, or
adaptive/evolutionary interpretation** is warranted.

## What the code actually did

- Read **only** five bounded genuine Cannon Park meeting dates
  and four specified race numbers on each date through the
  original first-party SOAP endpoint; no broad site scraping.
- Retained `HORSES` official ID in memory, enforcing same-day
  one-race-per-ID and one GPS race per same-day name.
- Matched names **only within the original date/race number**;
  rejected duplicates, absent GPS, source-zero/invalid section
  values, and unknown race metadata.
- Required the first-section numeric marker, signal and
  duration to be positive; used *first recorded interval time
  in seconds* rather than pretending the header clock time
  was an individual finish time.
- Grouped verified source IDs by actual ground and exact
  source-record distance, marker and class, and counted
  repeated conditions. No individual outcome/horse records
  were written or published.
- Ran fictional examples in
  `tests/test_ecology_rq_multigoing_h1_preflight.py`:
  a class-confounded ground comparison fails the strict
  gate, same-day duplicate names cannot be promoted to
  repeated biological IDs, and ordinal ground spacing
  is not assumed.

## Scientific decision and research design next

**H1 status: HOLD** — repeatedly observed IDs can be
linked to different ground conditions (20 horses), but the
strict 2+ Good and 2+ wet within same class/distance/first
marker requirement is met by **zero** horse strata in this
particular selected sample. The engineering gate is
not a formal sample-size/power calculation.

**H2 status: HOLD** — neither complete confirmed starter
rosters nor official early positions and true
horse-specific finish outcomes are validated. The
first-section duration cannot be treated as an animal's
confirmed full-distance performance or evidence for a
competitive effect.

**Next empirical expansion should be predeclared:**
expand source dates and class/distance matching, check
how many horse IDs cross varying grounds after
stratification, then perform a simulation-based power/
identifiability study using the real exposure distribution.
The exploratory 10-ID contrast in this memo must not be
retroactively treated as a preregistered primary
hypothesis test after selecting a larger sample.

All tests and downloads used publicly available,
official Racing Queensland data and preserved the
original publisher attribution. Review the
source's open-data terms before redistribution;
the repository contains source links and aggregates
but no raw racehorse records.
