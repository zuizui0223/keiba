# 2027 official registration-ID prediction ledger: implementation and evidence gates

**Status: SOFTWARE AND SYNTHETIC TESTS ONLY; HOLD_NO_LICENSED_2027_JRA_INPUT_OR_TRAINED_MODEL.**
This is a step toward the [frozen 2027 official-ID rolling research protocol](JAPAN_2027_OFFICIAL_ID_ROLLING_FORECAST_PROTOCOL.md), **not** a 2027 racing result or a claim that a JRA-VAN Data Lab. license has been obtained.

## Why this implements a scientifically important missing part

In selected old racers, source-C 2026 retrospective analysis revealed large predictive improvements from adding *recent focal-horse performance* versus small/uncertain increments from matching other horses sharing a recorded sire/dam. These repeated post-hoc 2026 comparisons cannot establish independent future transfer. The next test must commit **before** racing to an exact set of predictions made from historically known information, and then score those same predictions **after** complete race results appear.

Previous private source-readiness code confirmed timestamp/ID schemas but did **not** produce a pre-result commitment or separate later score. The new file [point-in-time ledger](../../scripts/ecology_japan_2027_point_in_time_ledger.py) performs those two stages as distinct commands.

## Input contract — privately supplied licensed data only

* Target entrant snapshots (same required fields as the private known-on validator): race_id (JRA namespace), horse_id (typed H: blood-registration namespace), race_start_at_jst, entry_known_at_jst, course_id, surface (turf/dirt), distance_m, sex (M/F/G/U), age, jockey_id, trainer_id.
* Parent master: horse_id, sire_id, dam_id (typed H:/B: or blank), pedigree_master_known_at_jst. Do **not** equate JRA blood-registration and breeding-registration namespaces without a verified typed bridge. Blank parent IDs must never create artificial kin groups.
* Historical published outcomes: race_id, horse_id, race_start_at_jst, result_known_at_jst, finish_rank, classified_field_size, finish_status, **surface, distance_m, course_id, jockey_id, trainer_id**. The extra fields are necessary to compute known-at-time course, jockey and trainer baselines without assuming old-source numeric IDs are interchangeable.
* Separately **trained and frozen** coefficient model JSON with schema JRA_2027_H1_FROZEN_LINEAR_MODEL_V1, training_through_jst, model_frozen_at_jst and two models M1 and M2. Each has an intercept and every required feature's coefficient, mean and strictly-positive sd. No model coefficients (fake or real) are bundled as if they were empirically trained. The 2027 source is required to contain **authorized actual published timing metadata**, not merely inferred race dates or static websites.

All imported time fields require explicit JST +09:00 offset. The CLI uses its **actual local current clock** at forecast creation, which must be after the selected information as-of time but before the first race start. An as-of timestamp typed by hand is not proof that a prediction existed by that date.

**M0** is the fixed normalized rank midpoint 0.5; **M1** uses own prior performance (mean, count, surface/distance context, last three, recency), current age/sex, surface/distance, and source-certified **course/jockey/trainer historical outcome summaries**; **M2** uses exactly the same own/control features plus pre-race same-sire/dam *other-horse* context summaries and peer counts. These family means exclude the focal horse and weight each relative once per surface–distance context. The regression coefficients are not estimated from the target outcome.

The normalization target is (finishing rank − 1)/(classified field size − 1) in source-certified complete ranked races, not a race-winning probability; the bounded outputs 0..1 must not be interpreted as calibrated betting odds.

## Privacy-separated two-step workflow

### Stage 1. Freeze, before the first start

Run on an authorized **private** machine with the permitted actual data files:

    python scripts/ecology_japan_2027_point_in_time_ledger.py freeze \
      --entries /private/next_races_jra_entries.csv \
      --parents /private/authorized_parent_master.csv \
      --history /private/official_prior_result_known_on.csv \
      --frozen-model /private/fitted_pre2027_model.json \
      --asof-at-jst 2027-01-08T19:00:00+09:00 \
      --private-forecast /private/forecasts-20270109.json \
      --public-commitment /private/forecast-20270109-aggregate-commitment.json

The private prediction JSON has one row per target race and horse with M0/M1/M2 forecasts and exact race starts. It **must never be uploaded publicly**. The separate public commitment includes only overall race/horse/start counts, as-of and actual generated timestamps, file/version SHA256, and a SHA256 digest of the private prediction bytes. It does not contain horse or race IDs or individual predictions.

For public, independently inspected temporal provenance, commit the **aggregate commitment** to a public Git repository *before* any race begins, and preserve the commit SHA/timestamp. A local digest or self-reported timestamp alone is **NOT independent proof of pre-race existence**; the command cannot sign or attest this by itself. JRA data rights and model training provenance still require separate review. Do not include provider-sensitive source files, proprietary trained coefficient content if licensing prohibits redistribution, or IDs in GitHub.

Stage 1 **rejects** target races outside 2027-01-01 to 2027-06-30, less than two or more than 30 frozen entrants, incomplete source-known race metadata, any model trained on 2027 outcomes or frozen after prediction, any entered horse/pedigree master published after cutoff, results published at or after the freeze as-of time, conflicting/duplicated race IDs or parent namespaces, invalid classified historical ranks and any source file with missing requisite fields.

### Stage 2. Score, only after official complete outcomes

    python scripts/ecology_japan_2027_point_in_time_ledger.py score \
      --private-forecast /private/forecasts-20270109.json \
      --public-commitment /private/forecast-20270109-aggregate-commitment.json \
      --later-results /private/authorized_complete_results_2027.csv \
      --aggregate-out /private/forecast-20270109-score.json

This independently verifies the original private forecast digest and manifest SHA, exact race and registered-horse IDs, result timestamps **after the scheduled race and after the original freeze**, and full 1..N ranked completeness **matching the frozen entrant list**. Duplicate, foreign, partial, tied, DNF, conflicting-field or not-yet-published results are rejected or counted as pending/ineligible **without inventing finishing ranks**. Every model scores on exactly the same valid starts.

The aggregate reports per-horse-equal RMSE for M0/M1/M2, M1−M2 and M0−M2 gains, monthly support counts and one-way horse/date bootstrap sensitivity where group counts permit. It also reports **separately pre-race-defined strata** for horses with zero vs at least one **recorded classified prior result** and horses with/without **documented same-parent other-horse history**. It suppresses subgroup RMSE when sample support is too small. A horse without historical entries is **not certified as an official debutant**: that status depends on licensed lifetime record completeness. With fewer than 100 classified starts, 30 distinct horses or 30 race days, it reports HOLD_2027_AGGREGATE_LOW_SUPPORT rather than promotion to a general claim. Even if M2 beats M1 and M0 on an authorized panel, the score is **PROVISIONAL** until a separate earlier public-commitment timestamp, licensed source completeness and independent model-training provenance are verified.

## Threat model and limitations

1. Individual names, blood IDs, horse-level predictions and result rows can **never appear in the aggregate JSON**; the private forecast file must be stored outside the working Git repo.
2. An unchanged SHA only detects modification relative to a given commitment. This code does **not** verify an authentic pre-race signed Git commit, an unforgeable OS clock or the data provider's legal rights.
3. Race entrants and their timestamps must have been genuinely published by the source, not backfilled after outcomes. The gate requires their claimed known-at times, but cannot verify authenticity without provider records.
4. Complete 1..N ranks across the frozen entrant list exclude DNF/scratches from the primary score; coverage and selection bias need reporting.
5. Even a future forecast effect from relatives **cannot identify additive genetics**, breeding management, owner, stable, trainer or selection. Pedigree A and anonymous genomic G are **not linked**.
6. This script does not download JRA-VAN or NAR data, and it does not train a real 2027 M1/M2 model. Only the original 2026 study has real outcomes.

## Validation

[Unit tests](../../tests/test_ecology_japan_2027_point_in_time_ledger.py) use fictional typed IDs and **simulated dates** to demonstrate that future outcomes, model mutation, incomplete ranks and duplicate results cannot silently contaminate predictions. The dedicated CI workflow does **not** download any third-party race data or claim prospective outcomes. The latest [successful synthetic run #44013284488](https://github.com/zuizui0223/keiba/actions/runs/44013284488) passed **24** new freeze/score tests and **12** prior source-known-on tests; [immutable aggregate QA provenance](../evidence/japan-2027-point-in-time-ledger-synthetic-qa-20261117.json).

Related implementation: [typed JRA blood/breeding ID bridge](../../scripts/ecology_jravan_blood_breeding_id_bridge.py) and [2027 private known-on source preflight](JAPAN_2027_PRIVATE_KNOWNON_VALIDATOR.md).
