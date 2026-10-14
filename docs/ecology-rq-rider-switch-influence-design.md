# Post-hoc influence and source-readiness design for documented-rider early-pace persistence

**Design frozen on 2026-10-14, AFTER the positive 36-horse observational rider-switch result and BEFORE running these influence checks on live source records.** The original 2026 Cannon Park 12 dates and positive-GPS measurement definitions are NOT changed. This is a robustness/descriptive diagnostic, not a preregistration or independent biological replication.

## Scientific falsification

The original descriptive result (36 official HORSES IDs, 72 cross-date changed-Jockey/@Id pairs, +0.063583 sec² equal-stratum mean pair product) might be disproportionately carried by a few meeting dates, a few repeatedly observed HORSES IDs, or incomplete official rider/horse metadata. We test whether dropping one original meeting or one original animal reverses the direction, or makes the originally documented data-support gate fail. **Neither robustness nor statistical significance is guaranteed.**

## Fixed eligibility and outputs

Re-use source_timed_panel, pair_records, summarize_pairs exactly as already defined by the primary rider-switch script. Each pair links the same numerical original HORSES ID on two different dates, with matching first-GPS marker and official race distance and different documented Jockey/@Id. Peers with missing jockey values STILL contribute to the original first-GPS race-relative target.

* Leave-one-original-meeting-date-out: remove every pair touching that date, retain all other original race-relative outcomes unchanged. Re-evaluate the support gate (>=20 different official HORSES IDs, >=20 strata, >=6 represented source dates, >=6 distinct meeting-date pair types), without reselecting dates. Return **one source-date keyed aggregate row** with support count, pair count, status, and, only if identifiable, mean pair product. If any deletion fails the gate, the across-all-days stability verdict is HOLD. The 12 deletion values are **not a 95% CI or an independent validation set**.
* Leave-one-original-HORSES-ID-out: for every distinct contributor to the main changed-rider statistic, delete **only pair records for that ID**, leaving every other original race-relative timing value/peer average unchanged (avoids changing the definition of other horses' outcomes). Re-evaluate the same support gate. Report **only aggregated min/max, count of supported/unsupported re-fits, negative/zero/positive refit counts**, and maximum absolute deviation from the originally observed aggregate mean. Never serialize the removed original HORSES ID, its dates, row-level contribution, or pseudo-identifiers. If any animal deletion causes HOLD, the overall stability interpretation is HOLD.
* Source completeness: report meeting-date and race-ground aggregate source positive-GPS counts and documented numeric Jockey/@Id coverage, distinguishing observed and missing roles. This is not a GPS-missingness model, a random sample, a true starter count, or rider final-identity verification.
* Source errors: record safe **HTTP status-code categories** when available (e.g. 429, 403, 502/503) and sanitized error class, but NEVER error URLs, horse IDs, source XML or raw rider times. If any of the original 12 dates is unavailable, top-level empirical result remains HOLD, regardless of any partial numeric positive signal. A green unit-test/CI process is not equivalent to complete source replication.

## Interpretation and bounds

All sensitivity calculations here are **post-hoc and within the same observed-source cohort**. A positive all-deletions signal would make one-day/one-horse dominance less plausible under these measurements. It would NOT establish heritability, personality, adaptation, a causal change-of-rider effect, source stability over time, verified actual jockey switches, horse-by-going random slopes (H1), opponent social effects (H2) or generalization across tracks.

Source: Racing Queensland official race/horse SOAP and positive initial GPS sectionals, data-rights and previous locked-date documentation as in the PR. Only anonymized aggregate output may enter public CI artifacts and the repository. Work remains in Draft PR #2; main and betting PR are not altered.
