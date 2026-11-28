# Observed single-market quote trajectories: aggregate and internal gaps can diverge

28 November 2026 JST. [Frozen protocol](MARKET_OBSERVED_WIN_TRAJECTORY_PROTOCOL_20261128.md) · [execution correction](MARKET_OBSERVED_WIN_TRAJECTORY_EXECUTION_AUDIT_20261128.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/46112860899) · [aggregate receipt](../evidence/market-observed-win-trajectory-20261128.json).

20 archived source blobs verified by Git SHA1. Same date and race IDs, complete horse-number sets, name matching where independently recorded, strictly prior source update and receipt relative to scheduled start. Primary chronology in receipt order; reject source-time regression. One raw-text extract retained as sensitivity only. Legacy R7 missing horse_count corrected using explicitly recorded expected_full_market_sizes.win and exact card/quote roster, before any analytical results.

| Race | Roster | Primary recorded source times (JST) | States |
|---|---:|---|---:|
| 6 | 12 | 12:30 | 1 |
| 7 | 16 | 12:29, 13:03 | 2 |
| 8 | 11 | 12:21, 13:26, 13:44 | 3 |
| 9 | 12 | 12:32, 13:26 | 2 |
| 10 | 10 | 12:18, 13:27 | 2 |
| 11 | 18 | 12:27, 13:26 | 2 |
| 12 | 16 | 12:36, 13:27 | 2 |

Seven races, six with multiple states, 14 states, seven adjacent intervals. One date. 614 dependent pair-interval rows. Exclude R8 13:22 record received after 13:26; Oct18 nine records lack upstream update clock; selected quote reports incomplete. R8 13:42 raw-text complete board is sensitivity only. No raw names or quotes in new aggregate. Source clocks are saved labels, not independently verified publisher times.

| Interval | Pairs | Point-value opposite | Truncation sensitivity resolved | Truncation opposite | Opposite aggregate grow/internal shrink | Opposite aggregate shrink/internal grow |
|---|---:|---:|---:|---:|---:|---:|
| R7 12:29–13:03 | 120 | 13 | 111 | 9 | 2 | 7 |
| R8 12:21–13:26 | 55 | 3 | 49 | 2 | 0 | 2 |
| R8 13:26–13:44 | 55 | 6 | 50 | 5 | 2 | 3 |
| R9 12:32–13:26 | 66 | 12 | 39 | 3 | 0 | 3 |
| R10 12:18–13:27 | 45 | 6 | 28 | 3 | 1 | 2 |
| R11 12:27–13:26 | 153 | 26 | 67 | 4 | 0 | 4 |
| R12 12:36–13:27 | 120 | 25 | 79 | 9 | 4 | 5 |

| Measurement sensitivity | Both directions resolved | Opposite directions |
|---|---:|---:|
| center | 609/614 | 91 |
| truncation | 423/614 | 35 |
| nearest | 423/614 | 35 |

Define normalized reciprocal displayed WIN quote proxy s; pair mass M=s_i+s_j; internal absolute balance r=abs(s_i−s_j)/M; aggregate absolute gap D=M r. Exact ΔD=mean(M)Δr+mean(r)ΔM. This identity is not an estimated behavioral mechanism. Point values show 91 opposite pairs among 609 resolved. Hypothetical quote-perturbation ranges [o,o+.1] and [max(1,o−.05),o+.05] each yield 35 opposite comparisons among 423 resolved, including 9 aggregate grow/internal shrink and 26 aggregate shrink/internal grow; all seven primary intervals contain at least one truncation-robust opposite case. Counts do not establish the same exact pair set across the two perturbation schemes. R8 extra raw-text source 13:42 gives 4 robust opposite comparisons on 13:26→13:42 and zero on 13:42→13:44; not pooled into primary. No significance test or independence claim from dependent pair rows. The conditional .8/odds floor-rounding simplex feasibility diagnostic contains unit sum at both ends of all primary intervals; this does NOT verify actual ticket shares or rounding rules, or identify stock. Neither total vote count nor externally timed information event appears in current data.

## Data acquisition gate

Official JRA-VAN DataLab description https://jra-van.jp/dlb/ddata.html documents time series odds every 5–10 minutes, body-weight publication about 60 minutes before post, and meeting changes. Staff clarification https://developer.jra-van.jp/t/topic/119 says per-ticket-type total votes are available in time-series odds, but intermediate per-selection ticket counts are not directly supplied by 0B20. Ordinary payout formula and WIN rate: https://www.jra.go.jp/faq/pop03/1_17.html?newwindow=true. Historical retrieval and true as-of publication not equivalent; see https://developer.jra-van.jp/t/topic/1158. Obtain authorized export with source records and license check, not raw public redistribution; no data acquisition claimed. Preregister stock and state model on future independent race/date blocks with publication windows and sham windows, compare normalized-quote bounds; no empirical causal inference or actual vote-flow reconstruction without additional validation. Keep PR125 theory and this observational signature separate. No betting recommendation, current prices, outcomes or prospective prediction. Main and frozen ledgers unchanged.

Artifact 15250676487, sha256:083ec207d4408a087c04b7052f428fa4a6ec001a45104e48a0860140c8ba6883; metadata and upload log match, ZIP not independently extracted.
