# Original Racing Queensland source snapshot drift: 548 to 543 horse/GPS joins

**Archive-to-archive provenance audit, 2026-10-14.**

This is a **data-version and reproducibility finding**, NOT an H1 ground
reaction norm, H2 competitor response, individual behavior change,
adaptation, heritability or betting result.

## Two original historical GitHub Actions artifacts compared

- Earlier [2026-10-13 Cannon Park 12-date calendar audit,
  run 38347984553](https://github.com/zuizui0223/keiba/actions/runs/38347984553).
  Original commit edabd5f4af01b0508df45ee8eadbaff859243da3;
  548 original numeric HORSES-ID × positive first-GPS candidate matches.
  Original artifact: rq-2026-calendar-12-meetings-aggregate-no-runner-records.
- Later [2026-10-14 original rider-switch / source-fingerprint audit,
  run 38501390778](https://github.com/zuizui0223/keiba/actions/runs/38501390778).
  Original commit 8e790d20dded66dee52859e12260b4790f3e6e7a;
  543 such source matches.
  Original artifact: original-rq-rider-switch-anonymous-aggregate.
- The independent [archive-to-archive reproduction run 38563462303](https://github.com/zuizui0223/keiba/actions/runs/38563462303)
  downloaded those exact previously generated anonymous artifacts,
  passed 7 fictional-source negative-control tests, and produced
  a fresh aggregate-only per-date comparison.

Both runs use the same 12 original 2026 Cannon Park meeting dates and
the previously fixed official race-number selection.

## Measured source observation change

| Original date | 2026-10-13 archive | 2026-10-14 archive | Delta |
| --- | ---: | ---: | ---: |
| 2026-02-16 | 42 | 41 | -1 |
| 2026-03-12 | 5 | 5 | 0 |
| 2026-03-26 | 35 | 34 | -1 |
| 2026-04-04 | 21 | 21 | 0 |
| 2026-04-09 | 51 | 50 | -1 |
| 2026-05-15 | 45 | 45 | 0 |
| 2026-05-29 | 51 | 51 | 0 |
| 2026-07-23 | 49 | 49 | 0 |
| 2026-08-22 | 67 | 67 | 0 |
| 2026-08-28 | 65 | 64 | -1 |
| 2026-08-29 | 64 | 64 | 0 |
| 2026-10-11 | 53 | 52 | -1 |
| **Total** | **548** | **543** | **-5** |

The following original, byte-derived SHA-256 checks **matched across
the older and newer original artifacts in all 12 of 12 dates**:

| Original upstream data component | Byte-identical original dates |
| --- | ---: |
| GetMeetingsForDate raw XML response | 12/12 |
| GetRacesForMeeting raw XML response | 12/12 |
| Official date-specific Sectionals CSV | 12/12 |

Therefore **changes to these three raw original data components do
not explain the difference of 5 candidate joins**.

### What remains unresolved

The earlier October 13 audit did NOT archive the original per-race
GetHorsesForRace raw XML response hashes. The later October 14 audit
DID preserve a combined raw HORSES-roster hash per date. In addition,
the GitHub source code changed between the two run commits.
Consequently we **cannot distinguish** a modification of original
horse-nomination response bytes from a difference in source parsers,
data matching code or other run configuration.

It would be scientifically incorrect to conclude that five horses
were removed from the biological population, scratched, experienced
environmental stress, or changed their performance. The source
difference is not a biological treatment effect.

Machine verdict:
**HOLD_SAME_ORIGINAL_3_SOURCES_DIFFERENT_JOIN_COUNTS_ROSTER_OR_CODE_UNRESOLVED**

## Permanent source fingerprint and current replay checks

The repository now retains the
[permanent anonymous 12-date raw-source hash file](evidence/rq-cannon-original-source-fingerprints-20261014.json)
from the October 14 **543-match** snapshot.
It freezes per original date:

- the original count of numeric HORSES-ID matched positive GPS intervals;
- exact GetMeetingsForDate, GetRacesForMeeting and original GPS CSV SHA-256;
- combined SHA-256 for all originally downloaded GetHorsesForRace
  XML responses, with numeric race IDs hashed as part of one digest
  rather than published in any output;
- the number of original race-roster XML responses.

This file was independently validated against the original
October 14 GitHub Actions aggregate in
[source-fingerprint replay run 38564794644](https://github.com/zuizui0223/keiba/actions/runs/38564794644).
Its 8 fictional-source validation tests independently verify
the original-source hash comparison, fail-closed missing dates,
digest integrity and absence of horse ID leakage.

**The permanent file is from the newer 543-row run only**:
it cannot restore the earlier 548-run horse roster or prove the
original horse-list endpoint was unchanged.

The new
[source roster snapshot replay script](../scripts/ecology_rq_horse_roster_snapshot_check.py)
re-fetches exactly the known source days and compares all four original
response types, returning HOLD rather than treating a failed request
as an absence of racehorses.

A first attempted 12-date re-fetch in
[run 38564794644](https://github.com/zuizui0223/keiba/actions/runs/38564794644)
could not reconcile any source dates, although the original archive
was correctly verified. No observed racehorse rows were inferred
as missing or zero from that failed fetch. The cause of the
one-time access failure is not independently proven.

After adding a **safe, name/ID-free validation-code
diagnostic**, the later fully independent
[run 38565084313](https://github.com/zuizui0223/keiba/actions/runs/38565084313)
successfully validated the permanent fingerprint manifest against
the archived genuine October 14 source JSON **and replayed all 12
original dates**.

| Exact re-fetched original component | Dates byte-identical to October 14 archive |
| --- | ---: |
| GetMeetingsForDate XML | **12/12** |
| GetRacesForMeeting XML | **12/12** |
| Original sectionals GPS CSV | **12/12** |
| GetHorsesForRace original XML combined roster SHA256 | **12/12** |
| Source-linked HORSES ID × first-positive-GPS candidate count | **12/12** |

The 543-row **October 14 source snapshot is now
independently replayable** with four original source
fingerprint components and the same matched-candidate
counts. This does NOT reconstruct the earlier October 13
HORSES XML and does NOT identify why that older run
reported five more joinable candidates. It also
does not verify final starter/finisher status or
biological environmental responses.

This source snapshot check is not a population-
representative repeatability model or a valid
replication of the conditional ICC at the same
data, fixed-source-code and model selection
conditions. Its value is **data provenance
and version-control reliability**.

## Reproduce without publishing original runner records

The exact historical workflow and code are:

- [Historical two-source snapshot diff workflow](../.github/workflows/ecology-rq-source-drift.yml).
- [Historical diff script](../scripts/ecology_rq_source_snapshot_drift.py).
- [Current original roster replay workflow](../.github/workflows/ecology-rq-original-source-roster-replay.yml).
- [Permanent source fingerprint file](evidence/rq-cannon-original-source-fingerprints-20261014.json).

The workflows only obtain previously published anonymous
aggregates or request a bounded number of original first-party
Racing Queensland endpoints. No horse name, individual HORSES ID,
licence number, raw GPS timing row or individual prediction is
stored in repository files or workflow artifacts.

Upstream attribution:
[Racing Queensland Open Data Web Services](https://www.racingqueensland.com.au/opendatawebservices)
and [original Thoroughbred sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).

## Consequence for research claims

The Cannon Park 0.432 source-conditional ICC and later
early-pace repeatability estimates are associated with
**identified source editions and matching-code revisions**.
They are not yet guaranteed to describe exactly the
same original animal-start roster across all re-fetches.
The 548-versus-543 source difference requires either
the missing earlier raw HORSES-roster edition or a
same-code/fully archived response replay to attribute
its cause. Neither is currently available.

Source version uncertainty must remain separate from
Gaussian model uncertainty and ecological/population
inference. Do not use the source-count discrepancy
to support or reject H1, H2, social plasticity,
evolved personality or heritability.
