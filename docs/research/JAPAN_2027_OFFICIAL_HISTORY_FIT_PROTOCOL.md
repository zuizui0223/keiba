# JRA 2027 prospective model fit: licensed historical results only

**Status 2026-11-18:** PROTOCOL / SOFTWARE ONLY. No authorized official JRA-VAN data, complete historic blood-registration-ID result panel, fitted empirical model, or 2027 result has been obtained. All numeric tests are fictional.

## Gap after PR #51

The forecast freeze+score ledger supports supplied model coefficients but did not train them from consistent point-in-time source records. This branch adds a **separate, private, prior-2027 model fitter**. It uses the exact feature function and M1/M2 schemas from the frozen forecast ledger, rather than silently changing features during forecast time.

The training input is a licensed, official, source-stable horse-ID-linked set of THREE CSV tables: historical entrant snapshots (ENTRY_REQUIRED), typed parent records (PARENT_REQUIRED), and published per-horse historical result rows with race conditions, jockey and trainer IDs (HISTORICAL_INPUT). The same parent and horse namespaces must be used in future freeze. Must never infer IDs from names, owner prefix, Wikipedia, or unrelated DNA genotypes.

## Predeclared time split and estimator

- **Training races:** start in [2018-01-01, 2025-01-01) JST. To use a label, its actual publication timestamp must precede 2025-01-01 JST and the actual model creation time.
- **Chronological validation races:** start in [2025-01-01, 2027-01-01) JST, with labels and race entrants actually public before the model freeze. No 2027 race results may be included.
- **Feature cutoff per race:** historical entry_known_at_jst, strictly later than each contributing historical result_known_at_jst. The source must certify each known-on timestamp. Family-history features always exclude focal horse. Only classification-complete 1..N ranks from full race entry/result join are eligible; DNF, missing starts, tied ranks and incomplete race records are counted and omitted from train/validation, not imputed.
- Predeclared **ridge alpha=100.0**, intercept unpenalized; equal focal horse weights within the training set. Fixed feature transformation and *single common training scaler* for M1 and M2 own-history features, with sd=1 for constant columns. Do not tune alpha/features on 2025–26 validation results.
- Minimum training support: 100 starts, 30 horse IDs, 30 distinct racing days. Validation support: at least 50 starts, 20 horse IDs, 15 dates; report negative performance in validation rather than change features or split.
- M0 fixed 0.5, M1 own history/age/sex/course/jockey/trainer, M2 M1 plus 4 direct shared-parent other-horse previous-performance features. Scores equal-horse-weighted normalized-rank RMSE; operational claim only if M2 beats both M1 and M0, with no claim of additive-genetic causation.

## Anti-leakage and negative-control gates

1. Entrants, historical result publication timestamps and parent-master known-on timestamps must all be strictly before each historical race's prediction cutoff.
2. For every historical race there must be a complete entrant set and a full matched source result set. Race ID, horse ID, start, surface, distance and rank must align exactly. Unknown/dead-heat/withdrawn cases are excluded with counts. Never score a selected subset as an entire race.
3. The same documented relative may contribute only one normalized historic per-condition mean, regardless of repeat racing; missing parent IDs are not shared families.
4. Frozen model JSON must match the exact PR #51 schema and be validated by the same forecast-ledger parser. A source-data SHA and a model SHA audit are emitted as aggregate-only metadata. The actual fitted coefficients/pedigree rows stay private unless their source-license terms explicitly permit release.
5. Validation was already publicly available when this design was written. It is **historical model-building validation**, not a prospective study. The only proposed true future test remains 2027-01-01 through 2027-06-30, with pre-race Git commitment of model digest and private forecasts. A local timestamp or a GitHub file committed after the first start cannot be retroactively treated as a pre-race record.
6. No public CI workflow may automatically download JRA-VAN/JBIS/other licensed raw racing tables; CI tests use synthetic records only.

## Remaining external dependency

The real source license, the official stable horse/parent ID map and actual publication timestamps are absent. The numerical output for real JRA and NAR horse data, national complete kinship A, genomic G association, heritability, and profitable wagering all remain **HOLD**. This protocol and subsequent tests only establish a reproducible **method**.
