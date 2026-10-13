# v3.1 prospective holdout: next eligible Kyoto races

Planning record only. **This file is not a pre-result freeze and does not count toward the 20-race ledger.**

Created after the v3.1 final manifest seal on 2026-10-13.

Official programme source:
https://www.jra.go.jp/keiba/calendar2026/2026/10/1017.html

JRA notes that the programme is scheduled information and that the current race card is normally published around Thursday 16:00; race order, distance, post time and other details can change.

## 2026-10-17 Kyoto programme

Under the frozen v3.1 eligibility rule (Kyoto, flat turf/dirt, 1-win class or higher, not 2yo-only):

| R | Scheduled post | Programme | Eligibility |
|---|---|---|---|
| 1 | 09:55 | 2yo maiden dirt 1400 | no: below 1-win and 2yo |
| 2 | 10:25 | 2yo maiden turf 1200 | no |
| 3 | 10:55 | 2yo maiden turf 2000 | no |
| 4 | 11:25 | obstacle maiden | no: obstacle |
| 5 | 12:15 | 2yo newcomer turf 1800 | no |
| 6 | 12:45 | 2yo newcomer dirt 1800 | no |
| **7** | **13:15** | **3yo+ 1-win dirt 1800** | **eligible; first holdout candidate** |
| **8** | **13:45** | **3yo+ 2-win dirt 1400, fillies** | **eligible** |
| 9 | 14:15 | Momiji S, 2yo open, turf 1400 | no: 2yo-only |
| **10** | **14:50** | **Kiyotaki Tokubetsu, 3yo+ 2-win turf 2200** | **eligible** |
| **11** | **15:30** | **Tourmaline S, 3yo+ 3-win dirt 1800, fillies** | **eligible** |
| **12** | **16:15** | **3yo+ 1-win turf 1400** | **eligible** |

## Holdout #1 rule

R7 becomes holdout #1 only if all of the following are true on race day:

1. the official current race card still matches an eligible Kyoto flat race at 1-win class or higher;
2. a complete normalized pre-race horse-history input is available;
3. a timestamped pre-race win-odds snapshot covers exactly the runners in the input;
4. `scripts/v31_holdout.py freeze` succeeds before the scheduled post;
5. the resulting freeze is committed before the target result is observed.

If R7 is cancelled, changed to an ineligible condition, or cannot be frozen validly before post time, it does **not** enter the denominator. The next chronologically eligible race becomes the candidate. Failure of the prediction itself is never a reason to exclude a validly frozen race.

## Preparation checkpoint

After the official current race card is published, build the normalized input and verify quality-tier metadata. Do not use the scheduled programme page as a substitute for the current race card at freeze time.
