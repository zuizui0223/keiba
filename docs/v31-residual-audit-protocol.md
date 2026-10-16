# v3.1 holdout residual-audit protocol

Status: descriptive diagnostic protocol. It does **not** alter the frozen v3.1 formal decision rule.

## Purpose

For every scored holdout race, inspect prediction errors without rewriting the pre-result freeze or using the audit to rescue the formal result.

The primary object is an **actual top-three horse absent from the frozen union**. False-positive burden may also be summarized, but it does not redefine a miss.

## Evidence order

Residual explanations must be checked in this order:

1. frozen pre-race input;
2. official pre-race source material that was available before post time;
3. target-race result and sectionals;
4. post-race comments only as supplementary context.

A later source cannot be silently inserted into the frozen input.

## Residual classes

### 1. data residual

Use when relevant information was publicly available before post time but was absent or incorrectly normalized in the frozen input.

Examples:

- missing prior start;
- wrong class/distance/surface parsing;
- missing official quality tier;
- missing course history that the frozen source already contained.

A data residual remains a formal miss. It may motivate a future version only after v3.1 holdout is finished.

### 2. representation residual

Use when the pre-race data were present and correct, but the frozen feature/channel system did not represent the relevant signal.

Examples:

- transferable performance across distances not captured by ±20%;
- sectional/pace ability present in source data but absent from M/C1/U/Q1/K1;
- growth pattern not represented by U.

This is a model-structure miss, not a data-integrity failure.

### 3. threshold residual

Use when the relevant signal is represented by a frozen channel but narrowly fails a preregistered cutoff.

Examples:

- 1.1-second latest margin versus C1 <=1.0;
- sixth career start versus U <=5;
- Kyoto repeated placings without the K1-required win component.

Do not change the threshold during holdout.

### 4. state / stochastic residual

Use only after data, representation and threshold explanations are not sufficient.

This covers target-day state, trip, pace realization, break, traffic, weather interaction, or residual competitive randomness that was not recoverable from the frozen pre-race evidence.

Do not assign a specific biological/racing cause unless the evidence identifies it.

## Market context

The frozen M channel is the only market baseline used in formal v3.1 evaluation.

Post-race final odds may be reported descriptively to distinguish a model-specific miss from a broader market surprise, but final odds never change the frozen M set or formal score.

## No hindsight rescue

Residual auditing cannot:

- add a missed horse to union;
- edit a freeze;
- remove an inconvenient scored race;
- change M/C1/U/Q1/K1;
- change alpha or the 0.65 candidate-fraction ceiling;
- alter the 20-race denominator.

## Per-miss record

For every union miss save:

- race_id and horse number/name;
- frozen M/C1/U/Q1/K1/rescue flags;
- frozen market rank/odds;
- uncertainty flags;
- relevant pre-race history;
- actual finish and race sectionals when available;
- residual class;
- evidence supporting that class;
- unresolved remainder;
- whether the same signal has appeared in an earlier holdout miss.

## Repeated residuals

A single residual is descriptive.

If the same representation or threshold residual recurs across independent holdout races, record the recurrence count but do not modify v3.1. Recurrent residuals become candidate changes for v3.2 only after the v3.1 20-race formal evaluation is sealed.

## Final aggregation

After race 20, report:

- counts by residual class;
- repeated residual motifs;
- which misses were market-shared versus model-specific;
- which signals would be candidates for v3.2;
- which residuals remain genuinely unexplained.

Residual analysis is secondary and descriptive. The formal PROMOTE / NO_PROMOTION decision remains governed only by `docs/v31-holdout-decision-contract.json`.
