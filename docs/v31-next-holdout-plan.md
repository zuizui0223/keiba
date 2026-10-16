# v3.1 prospective holdout: next eligible Kyoto races

Planning record only. **This file is not a pre-result freeze and does not count toward the 20-race ledger.**

Created after the v3.1 final manifest seal on 2026-10-13.

Official programme source:
https://www.jra.go.jp/keiba/calendar2026/2026/10/1017.html

JRA notes that the programme is scheduled information and that the current race card is normally published around Thursday 16:00; race order, distance, post time and other details can change.

## 2026-10-17 Kyoto programme

Under the frozen v3.1 eligibility rule (Kyoto, flat turf/dirt, 1-win class or higher, not 2yo-only):

| R | Scheduled post | Programme | Eligibility / fixed window |
|---|---|---|---|
| 1 | 09:55 | 2yo maiden dirt 1400 | no: below 1-win and 2yo |
| 2 | 10:25 | 2yo maiden turf 1200 | no |
| 3 | 10:55 | 2yo maiden turf 2000 | no |
| 4 | 11:25 | obstacle maiden | no: obstacle |
| 5 | 12:15 | 2yo newcomer turf 1800 | no |
| 6 | 12:45 | 2yo newcomer dirt 1800 | no |
| **7** | **13:15** | **3yo+ 1-win dirt 1800** | **eligible; 12:50-13:00, task 12:55** |
| **8** | **13:45** | **3yo+ 2-win dirt 1400, fillies** | **eligible; 13:20-13:30, task 13:25** |
| 9 | 14:15 | Momiji S, 2yo open, turf 1400 | no: 2yo-only |
| **10** | **14:50** | **Kiyotaki Tokubetsu, 3yo+ 2-win turf 2200** | **eligible; 14:25-14:35, task 14:30** |
| **11** | **15:30** | **Tourmaline S, 3yo+ 3-win dirt 1800, fillies** | **eligible; 15:05-15:15, task 15:10** |
| **12** | **16:15** | **3yo+ 1-win turf 1400** | **eligible; 15:50-16:00, task 15:55** |

## Chronological holdout rule

Every eligible race is attempted in chronological order. R7 becomes holdout #1 if it freezes validly; otherwise the next valid eligible race becomes #1. A valid R7 does not make R8/R10/R11/R12 optional: each later eligible race is still attempted in its own fixed window.

A race enters the holdout only if all of the following are true on race day:

1. the official current race card still matches an eligible Kyoto flat race at 1-win class or higher;
2. a complete normalized pre-race horse-history input is available;
3. a timestamped pre-race win-odds snapshot covers exactly the runners in the input;
4. both odds observation and freeze occur 15-25 minutes before scheduled post;
5. `scripts/v31_holdout.py freeze` succeeds inside that fixed window;
6. the resulting freeze is committed before the target result is observed.

If an eligible race is cancelled, changes to an ineligible condition, or cannot be frozen validly inside its fixed window, it does **not** enter the scored denominator and the technical reason is recorded. The next chronologically eligible race is still attempted. Failure of the prediction itself is never a reason to exclude a validly frozen race.

## Preparation checkpoint

After the official current race card is published, build the normalized input and verify quality-tier metadata. Do not use the scheduled programme page as a substitute for the current race card at freeze time.
