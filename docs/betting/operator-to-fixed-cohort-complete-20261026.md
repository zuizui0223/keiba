# Private WIN/WIDE → horse ABM → staged bettors → SHA → fixed 26/64 cohort

**2026-10-26. Draft PR #26 (nested on PR #25).** This is an INTEGRATION of the already written mathematical and source-audit tools, NOT new actual JRA data, an unattended data acquisition job, a calibrated horse predictor or independently attested market forecast.

## Why this is a research advance

By PR #25 we had (1) a locally chained source log, (2) the PR #22 physical/nonlocal horse ABM to PR #19 smooth/voter ABM full WIN/WIDE 12-model source-locked forecast, (3) PR #23 GitHub comment SHA proof, and (4) PR #24 immutable 26 graded / 64 auxiliary race *candidate* registries. They still required manually transcribing the race and SHA to several separate programs. A race could therefore be accidentally lost in a denominator, retrospectively relabeled, or have its provenance disconnected from the model that was scored.

This PR's \`scripts/keiba_operator_cohort_bundle.py\` connects these **existing components** without replacing them. The only output is a PRIVATE bundle bound to a single registered race, including original source chain head, horse→bettor model predictions/locked metadata, a safe public SHA-comment TEXT TO POST ONCE (authorized sources only, never auto-posted), and a fixed-denominator receipt.

The source chain is verified again when the operator uses the model against the *later* WIN price. It requires that the entire source-event prefix present at freeze still exists and has the identical SHA head. New snapshots may be appended after the freeze, but cannot retroactively change the physical/voter input. It does not claim that a local hash chain is an external immutable record.

## The two intentionally separate race denominators

1. **Original SHA-locked 26 graded races, 20 dates:** The 2026-10-25 Kyoto 菊花賞 is an existing, different outcome-prediction preseal, not a new next-market q(t) target. Hence 25 future graded next-WIN candidate races remain in the preregistered denominator. Here the bundle emits precisely the \`KEIBA_PRIVATE_FIXED_SLOTS_CAPTURE_METADATA_V1\` receipt required by PR #24. The core 26 slots and their missing market windows are preserved even when no data exist.
2. **Independent auxiliary 64 number-slots on eight dates:** The first eight future dates fixed by PR #24, same selected venue, R05–R12. For auxiliary-only slots the bundle **does not fake a grade registration**; it preserves a separate 64-slot denominator and can report local price scoring only within that scope. A possible graded race also appearing as an R11 auxiliary slot is **one physical event**, not two independent experiments.

No official race ID, final horse-number list, provider rights or full WIN/WIDE source data is inferred from a provisional schedule. The source operator must supply a rights-reviewed, final-card receipt and the JRA official source update clocks. A race that is cancelled, changed, inaccessible, missing one WIDE pair, or missing a frozen next-WIN market update stays a **HOLD**, never replaced after the result is known.

## CLI: two steps, both PRIVATE

After using PR #25's \`keiba_operator_winwide_capture.py append\` command to record rights-reviewed full-field WIN and WIDE quotes in private/:

\`\`\`sh
python scripts/keiba_operator_cohort_bundle.py prepare \
  --private-ledger private/captures/YOUR_CONFIRMED_RACE_ID \
  --confirmed-card private/YOUR_CONFIRMED_RACE_ID_final_card.json \
  --private-output private/YOUR_CONFIRMED_RACE_ID_next_market_bundle.json \
  --horse-draws 120 --seed 20261026
\`\`\`

This uses the **earliest** full WIN + middle WIN/WIDE (with matching published source-update minute), PR #17 ahead-neighbour first-passage SDE c=2 and PR #19 smooth staged bettor q(t). It fixes exactly 12 market models, including directly quoted market, time-momentum and WIDE-node controls, aligned physical/WIDE and intentionally rotated wrong-horse WIDE negative controls, at voter release rounds 1/3/5. The horse physical signal is never allowed to look at future q2 or actual winner.

If source provenance is truly marked \`authorized_private_local_export\` with operator-confirmed rights, the bundle holds a **SAFE SHA-ONLY** GitHub PR #22 comment body computed using PR #23, but it does **NOT** publish it. The authorized operator must deliberately post once before the frozen next-WIN target window begins and then separately run PR #23's \`verify-live\` to confirm its GitHub server timestamp. If the data are merely synthetic or past replay, the safe public comment field is null.

After independently obtaining the future full WIN price snapshots in the same private ledger, and only when the *predeclared target window has already closed*:

\`\`\`sh
python scripts/keiba_operator_cohort_bundle.py score \
  --private-ledger private/captures/YOUR_CONFIRMED_RACE_ID \
  --private-bundle private/YOUR_CONFIRMED_RACE_ID_next_market_bundle.json \
  --private-output private/YOUR_CONFIRMED_RACE_ID_next_market_score.json \
  --operator-confirms-complete-capture
\`\`\`

Scoring checks that the SHA chain prefix is identical, the frozen race/provider/official card/horizon remain unchanged, local clocks are ordered, the late full-field WIN target is selected from the fixed +15-to-+20 minute interval, and all fixed model candidates are reported. **An absent quote must remain HOLD.** If no later WIN exists at all, a final missing-window claim is allowed only once the scheduled post time has passed. A missing quote cannot be substituted by a later one. An early score before the target window ends fails closed.

The \`--operator-confirms-complete-capture\` flag is a LOCAL declaration. It cannot authenticate provider updates or unobserved omitted snapshots. Neither the final score nor its cohort audit counts as independent prospective performance without a verified external SHA source/target receipt. Later market TV and KL are **relative quoted payout-price shape**, not calibrated WIN probability, human bettor transaction count, market criticality or ROI.

## Data-quality tests and live proof boundary

The new unit-test suite uses only an **artificial 6-horse / 15-WIDE-pair source stream** and an intentionally synthetic "authorized" flag in its isolated fixture; it NEVER posts anything to the public PR #22. It tests:

- correct frozen 12-model universe and a source SHA-only public message, not private price disclosure;
- changed future WIN target cannot mutate the earlier sealed forecast SHA;
- local hash-chain edits or a different private frozen metadata SHA are rejected;
- target window cannot be selected after inspecting q2; final missing-window status cannot appear before race post;
- original grade-26 and auxiliary-64 labels remain separate, and 2026 菊花賞 is never eligible as a new next-price event;
- disabled source rights, synthetic replay status and unverified external GitHub timestamps cannot become registered prospective outcomes;
- no new source observations or prospective trials are fabricated by tests.

Importantly, the *original* mathematical limitation remains: all horse SDE/crowding strengths, marginal PDE closure and bettor feedback coefficients are hypothetical. The published upstream six-race and Kyoto8 result replays are not newly independent validation samples. The true current state is **ZERO new authorized real next-WIN captures, ZERO remotely before-next-quote SHA commitments, ZERO independently validated next-WIN prices.**

## Preservation and future empirical priority

The true empirical next step is source-authorized full-field WIN twice plus same-update-minute WIDE all-pairs and a verified **final** starter card on multiple upcoming JRA dates. Under the fixed same-provider reception clock, freeze the price model before q2, post a SHA-only message deliberately, then collect the first eligible full WIN quote within +15..20 minutes. Keep every missing source and missing next quote in the full 26/64 denominator.

Public repository changes are **code, tests and documentation only**. All protected raw data, original horse histories, per-horse forecasts and staking information stay in \`private/\` (gitignored). \`main\`, the 2026 菊花賞 externally sealed M0/M1/M2 SHA and formal v3.1 20-race ledger are unchanged. Draft dependency PRs remain unmerged.

The priority is **independent as-of market reproducibility before fitting any "herd" threshold or claiming a betting edge**.
