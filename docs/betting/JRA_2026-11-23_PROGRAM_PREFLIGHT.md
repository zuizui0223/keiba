# JRA 2026-11-23 pre-race calendar preflight (not a frozen cohort)

**Checked 2026-11-22 JST. Status: PRELIMINARY_PROGRAM_ONLY / NO SERVER-SEALED OFFICIAL FULL CARD / NO BETTING FORECASTS.**

This is a *provisional* list of the earliest ten potentially eligible JRA races for tomorrow's prospective odds experiment. It is not the full verified day-plan JSON and MUST NOT be used to report any genuine forward success. Full official racecards, exact active runner counts, scratches, contemporaneous price updates, official raw page bytes and GitHub pre-first-race receipts are still needed.

The [JRA published program for 23 November 2026](https://jra.jp/keiba/calendar2026/2026/11/1123.html) specifies Tokyo 5th meeting day 6 and Fukushima 3rd meeting day 6, 12 races per venue. [JRA official racecard example](https://app.jra.jp/JRADB/accessD.html?CNAME=sw01ddd0103202603060220261123%2F68) confirms posted participants and race information; the published program explicitly warns that race/post time and other details can change.

Preliminary participant counts have been cross-checked with accessible third-party racecards ([Tokyo counts](https://umadan.jp/races/jra/2026-11-23), [Fukushima 1/5/6](https://keiba.love/20261123/fukushima.html), [Fukushima 3](https://race.netkeiba.com/race/shutuba.html?race_id=202603030603)) and official individual racecards where seen. These counts are not substitutes for a complete same-time JRA day roster.

| Provisional selection order | Race | Planned post JST | Expected runners (unfrozen) | Venue/class |
| ---: | --- | --- | ---: | --- |
| 1 | Fukushima 1R | 09:45 | 16 | 2yo maiden, dirt |
| 2 | Tokyo 1R | 10:00 | 14 | 2yo maiden, dirt |
| 3 | Fukushima 2R | 10:15 | 15 | 3yo+ 1 win, dirt |
| 4 | Tokyo 2R | 10:30 | 17 | 2yo maiden, turf |
| 5 | Fukushima 3R | 10:45 | 15 | 3yo+ 1 win, dirt |
| 6 | Tokyo 3R | 11:00 | 11 | 2yo maiden, turf |
| — | Fukushima 4R | 11:15 | not used | **Obstacle race: excluded a priori** |
| 7 | Tokyo 4R | 11:30 | 15 | 2yo maiden, dirt |
| 8 | Fukushima 5R | 12:05 | 16 | 2yo newcomer, turf |
| 9 | Tokyo 5R | 12:20 | 14 | 2yo newcomer, turf |
| 10 | Fukushima 6R | 12:35 | 16 | 2yo maiden, turf |

**Protection against hindsight:** The code cannot yet register this table as the first prospectively eligible day. The universe script now refuses incomplete meeting lists: it requires full **1R–12R for each of exactly 2 or 3 venues**, a declared positive runner count for every active race, and a result-free schedule source. The first-day plan must then be sealed **before 09:45 JST** by GitHub server receipt, together with the *actual* raw official day source and parsed schedule; independent source-page completeness review remains necessary. If that deadline, roster validation or receipt is missed, do not backfill from this preliminary table.

**Crucially, a provisional table created the night before is not yet a scientifically valid freeze.** A missing source should generate a transparent HOLD; it should never be replaced with estimated odds or later results.

Underlying tested code:
- [Full-day denominator](../../scripts/ticket_forward_universe.py)
- [Raw official day + GitHub server proof](../../scripts/ticket_forward_day_proof.py)
- [Pre-race odds freeze](../../scripts/ticket_forward_freeze.py)
- [Independent prospective contract](TICKET_FORWARD_V1_PROTOCOL.md)

No wagering or investment return claim.
