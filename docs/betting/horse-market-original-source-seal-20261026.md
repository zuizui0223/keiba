# PR #28 — one SHA commits the original market capture chain, final JRA card and linked horse→voter forecast

**2026-10-26. Draft, depends on [PR #27](https://github.com/zuizui0223/keiba/pull/27). No real new upcoming race or GitHub SHA comment has yet been captured.**

## Scientific and audit problem

PR #17–#19 connect a forward-neighbour nonlocal horse ABM, a factorized horse-position PDE, staged bettor information, smooth market feedback and coherent rank-derived WIN/WIDE combinations. PR #22 freezes a fixed family of predicted *next WIN-quote index* distributions. PR #23 can attest the **SHA's GitHub server posting time** by explicitly fetching its PR comment, and PR #24–#27 integrate full WIN/WIDE source observations and 26 graded / 64 auxiliary candidate-denominator tracking.

**A previously unaddressed integrity gap:** The PR #27 local bundle stored the *original per-snapshot SHA chain head* and *source-card record* **beside** the SHA-locked PR #22 model, rather than **inside** that committed model payload. The SHA thus bound only normalized WIN/WIDE feature rows and forecast vectors. A source-original card or entire source chain could later be relabeled or rewritten while leaving an otherwise valid previously generated model-SHA unchanged.

A GitHub pretarget comment containing such a SHA proves only the existence of that model payload, **not the original source-chain head or final-card claim**. In studies distinguishing actual information availability from post-hoc knowledge, that gap matters even when the numerical forecast predictions themselves stay fixed.

## Changes: same source, same horse physical input, same digest

\`keiba_operator_cohort_bundle.prepare_bundle\` now adds one typed, strict source-binding object **inside** the PR #22 SHA256-covered frozen forecast payload:

- SHA-256 of the entire declared **final JRA card** (race ID, source card URL, card publishing/acquisition times, final full field, venue/slot, announced post, surface/distance and operator rights claim);
- the original private full WIN/WIDE source event **chain-head SHA-256** at freeze time;
- the exact length of the source-event chain before freeze;
- the **physical horse model's original race distance** actually passed to the nonlocal first-passage agents;
- the frozen full-field **horse-number identity list**.

The code recomputes the SHA using exactly the existing canonical \`_seal\` operation before preparing a **SHA-only GitHub comment body**. No original odds, WIDE pair prices, full card, identifiable horse rows or original URL is posted as plaintext to a public GitHub comment; they are covered cryptographically by the digest.

It also verifies that the underlying PR #22 normalized feature blob SHA matches the model's original \`source_sha256_local_only\`, and that the declared full-field horse numbers in the final card match the frozen predicted field. During later scoring, the bundle cannot silently change the source card, registered slot, declared physical distance, initial source prefix length/head, public comment preparation text, or alleged external verification status.

**Threat model limits:** An operator can still falsify a *local* source's rights, receipt time or final-card declaration before freezing it; SHA does not prove those claims true. A local hash chain alone is not tamper-proof against complete rewrite or deletion. However, if its head was bound *before the target* to a GitHub-posted SHA (once such a real comment has been posted), later reconstructing a completely new local chain would no longer match the frozen digest. The current unmerged Draft does not claim any remote post exists.

The change applies to the **operator bundle route**. Other standalone PR #22 freeze formats remain usable for historical replays but do NOT automatically inherit this original-source binding. Source assertions must never be upgraded from local to authenticated without a verified pretarget remote comment and trusted source capture.

## Correct information clock for non-atomic WIN/WIDE sources

The PR #27 refinement retained WIN and WIDE original publication **seconds** but treats them as same price-index signal if their displayed update **minute** agrees. This avoids falsely interpreting two source pages as an atomic multi-market transaction; it does not rewrite publication timestamps. A separate data-quality bug was also removed: additional WIN quotes recorded **after the selected middle quote but already received before freeze** are not later market-target observations. They are excluded from the subsequent received WIN stream, rather than being mistakenly treated as "time-travel" after the frozen forecast.

The next market still uses the **first** complete WIN update in the predeclared +15-to-+20-minute source-update interval, not a favorable update chosen after viewing q2. Missing targets remain a HOLD. Official finishing order and payout are never inputs to the next-quote forecast.

## Cross-denominator physical-race deduplication

A future Kyoto R11 Fantasy Stakes can simultaneously appear as \`2026-10-31|京都|ファンタジーS\` in the original 26-grade source universe AND as \`2026-10-31|京都|R11\` among the 64 auxiliary trial slots. The underlying physical race is still ONE event.

The new \`audit_distinct_private_bundles()\` and its private-only CLI operation fail closed if:

- the same declared final race ID appears twice across grade / auxiliary candidates, even if different locally SHA-frozen model payloads are supplied;
- two different declared race IDs are assigned to the same pre-registered slot;
- any private bundle has an unbound or changed model SHA, source chain prefix, final JRA card, prepared safe GitHub comment body or source scope.

The output keeps the **26 original grade slots and 64 separate numbered auxiliary slots** as separate candidate denominators and never calls their sum 90 independently observed races. It reports *operator-declared* distinct race IDs separately from fully externally authenticated prospective trials, which remain zero.

Private-only read-only example:

    python scripts/keiba_operator_cohort_bundle.py audit \
      --private-bundles private/raceA_bundle.json private/raceB_bundle.json \
      --private-output private/unique_market_trial_source_audit.json

## Adversarial automated tests and reproducibility

Tests use synthetic six-horse WIN / fifteen WIDE-pair records, **not newly collected JRA observations**. New cases check:

1. complete initial local source-chain and final-card SHA inside the outer freeze SHA, with the source details absent from public SHA-only comment text;
2. physical horse distance, registered grade/auxiliary slot, horse list and source URL changes fail after freeze;
3. two physically identical JRA race IDs under grade/auxiliary slots **cannot count twice**;
4. public SHA comment text modification or a bundle falsely claiming independent remote attestation is rejected;
5. replaying the entire local source chain with *new internally consistent SHA files* passes its local chain checks, but does **not** match the already committed original source head;
6. a full WIN quote received before model freeze, but after the selected middle source update, is not mistaken for an additional future target.

The older PR #22 Kyoto8 three-quote historical replay, original PR #23 GitHub issue-comment gates and PR #25 operator receipt QA also run as regression controls. All original predictive and economic limitations still apply: no directly measured bettor ballots/stakes, no real JRA GPS calibration of the nonlocal horse physical law, no true information-herding threshold, no calibrated future winning probability, no proven bet EV.

## Execution

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests \
      -p 'test_keiba_operator_cohort_bundle.py' -v
    python -m unittest discover -s tests \
      -p 'test_keiba_operator_winwide_capture.py' -v

The synthetic CI must not commit, upload or print real private per-horse odds/horse histories. The source chain is explicitly LOCAL, its license assertions SELF-REPORTED, and the SHA-only GitHub comment remains a separate, deliberate act on an actual **upcoming** race before the predicted next price target. No comment is posted by the software.

**Status: software integrity hardening, not additional empirical proof. New genuinely remote-time-verified race trials = 0.** Original Kikuka M0–M2 preseal and formal v3.1 remain untouched, as does \`main\`.
