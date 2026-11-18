# 2027 JRA authorized SQLite intake: real jrvltsql schema, read-only data readiness

**Status: program implemented, nine fictional SQLite tests passed. Real JRA-VAN Data Lab. export NOT obtained, source-license and known-on timestamps NOT verified.** This is not a new race prediction or an estimate of heritability.

## Why this matters

The 2027 M1/M2 trainer needs one officially stable blood-registration ID system across historical race results and pedigree. The earlier 2010–21 and 2022–26 studies used selected name+race-event anchors from separate public histories, which do not establish complete JRA/NAR racehorse coverage or genetic causality. The public JRA-VAN help describes a concrete **RACE + RCOV** route to each runner's official blood-registration number and historical racing record:
https://support.jra-van.jp/jravan/detail?category=16&id=226&site=SVKNEGBV

A public, independently maintained Python importing tool, [miyamamoto/jrvltsql](https://github.com/miyamamoto/jrvltsql), can save licensed JRA-VAN records into local SQLite tables. Its open-source program is **NOT permission to download or redistribute any underlying JRA data**, nor does it cover the complete NAR population.

The repository [schema.py](https://github.com/miyamamoto/jrvltsql/blob/master/src/database/schema.py) confirms these source fields:

| Source table | Explicit fields | Role |
|---|---|---|
| NL_SE | KettoNum, Year, MonthDay, JyoCD, Kaiji, Nichiji, RaceNum, KakuteiJyuni, NyusenJyuni, IJyoCD, KisyuCode, ChokyosiCode, SexCD, Barei | Official horse-race result ID, final rank and horse/rider/trainer conditions |
| NL_RA | Matching six-part race key, TrackCD, Kyori, HassoTime, SyussoTosu, NyusenTosu | Race and documented declared starter counts |
| NL_UM | KettoNum, MakeDate, BirthDate, SexCD | Official horse blood-registration master |
| NL_SK | KettoNum, FNum, MNum | Parent **breeding-registration** numbers tied to child **blood-registration** number |
| NL_HN | HansyokuNum, KettoNum | Optional verified breeding-ID-to-horse blood-ID translation for registered breeding animals |

This **does not** mean that NL_SK or NL_HN has every JRA parent record, foreign ancestor or every local registered runner. NL_UM's multi-generation textual fields must not be substituted for validated direct parent IDs by assuming a slot number.

## New source readiness command

Use [scripts/ecology_japan_jrvltsql_sqlite_qa.py](../../scripts/ecology_japan_jrvltsql_sqlite_qa.py) on an **already authorized, locally generated** private SQLite export:

    python scripts/ecology_japan_jrvltsql_sqlite_qa.py \
      --authorized-local-db /private/JRA_VAN_authorized.sqlite \
      --aggregate-only-out /private/JRA_source_QA_aggregate.json

The Python process opens SQLite with read-only mode and sets PRAGMA query_only=ON. It never changes the original file. Only SQL counts and the entire local DB SHA256 are exported, **not horse names/IDs, original races, individual pedigree paths, money, odds or model predictions**.

QA includes:
- Presence of the five source tables and required actual columns, with HOLD on absent or empty structures.
- How many NL_SE records are joined by stable KettoNum to NL_UM and NL_SK — counts only, never by horse name.
- How many NL_SK rows document either/both typed breeding parent IDs FNum/MNum, and how many could be uniquely mapped through NL_HN.HansyokuNum to a registered horse blood ID. Unmatched parent identifiers remain in the **B:** namespace; never equate B: to H: just because the digits match.
- Races for which all available NL_SE KakuteiJyuni values form complete consecutive 1..N ranked finishers, matching NL_RA.SyussoTosu. Ties, DNF, rank gaps and incomplete starter lists are counted as nonqualifying, not repaired with guessed finishes.
- Potentially ambiguous blood-to-breeding reversals that cannot be silently promoted into pedigree relationships.
- The critical **HOLD** that neither MakeDate nor date of racing certifies the actual input-available timestamp of the particular historical entry, rider change, result or pedigree update. The schema does not provide a verifiable per-event result_known_at_jst or entry_known_at_jst field.

Passing this audit is only **schema/coverage readiness**, not permission, birth-registry completeness, identity accuracy certification, a prediction at race time, or a genetic result.

## Temporal provenance blocker

The Data Lab. official [data timing schedule](https://jra-van.jp/dlb/ddata.html) describes normal release slots and rapid data classes, but such a schedule is not a per-row immutable publication/receipt log. A later historical SQLite snapshot can contain corrected values and cannot prove which values were known before a past race.

A separately timestamped, audited import event log for each future data update is needed. At a minimum keep on the authorized private machine:
- Provider record family and version, actual *receipt* timestamp at JST with a trusted clock,
- Source capture digest, stable record/race ID and revision/replacement flags,
- Original unchanged pre-race snapshot and exact parent master version,
- Separately captured post-start results with their actual receive times.

Such **receipt times are upper bounds** on what the system actually possessed, not authoritative proof of JRA publication times. Historical 2018–24 race release times absent from existing snapshots must be marked unknown, never fabricated from MakeDate. Consequently the new official trainer remains **HOLD** until a qualified data source can supply or independently attest the required as-of history. No unrestricted bulk copying or web crawling is permitted.

## Tests and source integrity

[Synthetic-only CI run #44237531926](https://github.com/zuizui0223/keiba/actions/runs/44237531926) succeeded: nine tests use small temporary local SQLite tables with the real **column names**, fictional IDs and one correctly classified plus one tied-rank race. Tests cover complete vs tied ranks, NL_SE-to-UM/SK IDs, parent namespace mapping via HN, schema/column absence, empty source, no SQL file modification, prevention of false known-on attestation and no individual IDs in aggregate output.

Code passes **no actual source records**, and no 2027 forecasting, true multi-generation A matrix or anonymous genomic G connection has occurred.

JRA-VAN Data Lab. requires the appropriate user contract and key. NAR source records and registration namespace require separate approval. A national all-horse relatedness claim is therefore **not permitted** on this adapter.
