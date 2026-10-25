# GitHub PR comment SHA receipt for next-market forecasts

**2026-10-25 — nested Draft after PR #22. No real future market has been sealed.**

The earlier default-branch SHA workflow is NOT deployed on main. GitHub workflow_dispatch does not work merely because its workflow appears in an unmerged Draft PR. This additional protocol uses a **single user-authorized GitHub issue-type comment** on the existing PR #22, with only a SHA256 commitment and nonsensitive race/time identifiers. No private quote table, winner forecast, horse history or protected source is posted.

## One integrated model and the independent timestamp

PR #22 already freezes all 12/21 candidate next-price distributions using the same PR #17 nonlocal horse ABM, PR #19 smooth-staged bettor ABM and full same-updated-minute WIDE price residuals. This add-on does not modify any model coefficient. It only lets an independently retrieved GitHub server-created comment timestamp give partial evidence that the **whole private candidate distribution hash was made public before its next market target**.

The required clock order is:

    last source received <= locally frozen forecast <= GitHub comment created
        < START of next WIN target price window <= END of target window
        < horse post - 10 minutes

Requiring a SHA commitment before **the next targeted market quote** is much stricter than merely posting it before the race starts. If a GitHub comment appears after the planned next-price quote but before the horses race, that is not a valid next-market prediction.

## Operational procedure for a NEW, authorized, FUTURE race

First, create a private full-field WIN/WIDE freeze using the method in PR #22. The feature JSON must be an authorized local export, not a historical replay or synthetic demonstration. Record the fixed target horizon and source clocks before the next price observation. Private raw source and prediction files belong only under the gitignored private/ directory.

Second, create a safe comment body locally WITHOUT posting it:

    python scripts/keiba_nextprice_pr_comment_attestation.py prepare \
      --freeze private/next_market_freeze.json \
      --output private/SHA_ONLY_COMMENT_TO_POST.json

This emits a JSON object with a field named body_to_post_once_in_PR22_comment. That text consists of the fixed schema marker and canonical JSON with race ID, the 64-character SHA digest, last local source-receipt time, local freeze timestamp, first and last permissible future quote update times, scheduled post, and number of prediction models. It includes NO quoted odds, no horse names or full model distributions.

Third, **explicitly post the body ONCE, as repository owner**, in the conversation of https://github.com/zuizui0223/keiba/pull/22 . Do this only if the actual next target update has not yet occurred. Do not amend the comment or post a second variant for the same race. The preparation command never submits anything automatically.

Fourth, the independent proof verifier (requires installed authenticated GitHub CLI) retrieves the complete paginated PR #22 issue-comment list AND its individual comment record directly from GitHub REST:

    python scripts/keiba_nextprice_pr_comment_attestation.py verify-live \
      --freeze private/next_market_freeze.json \
      --output private/independent_SHA_timestamp_proof.json

Its rules reject late SHA posts, edited timestamps, extra comment fields, incorrect race ID, wrong owner, wrong PR, mismatching SHA, and multiple comment attempts for one race. It fails closed if GitHub is unavailable or history pagination is incomplete. An offline fixture checker is provided but ALWAYS has a HOLD status: simulated GitHub JSON cannot prove remote time.

Finally, and only after independently saving the future market quote in its originally locked time window, use PR #22's score command. The live proof and the LOCAL market-score report can be linked by:

    python scripts/keiba_nextprice_pr_comment_attestation.py verify-live \
      --freeze private/next_market_freeze.json \
      --score private/next_market_score.json \
      --output private/SHA_proved_target_capture_still_local.json

This rejects different races, different frozen digests and price updates before the SHA commitment. Even when GitHub's timestamp is independently retrieved, the target capture stream is only locally declared complete. It cannot be called an externally authenticated total market capture or a calibrated race prediction.

## Security and scientific boundaries

This process is designed as a partial alternative to the undeployed default-branch workflow. It **does not** merge anything to main or alter the presealed 菊花賞 M0/M1/M2 SHA, earlier Draft PRs or formal v3.1 results.

GitHub issue comments are mutable and deletable. The program rejects comments with updated_at differing from created_at, but edits occurring within one GitHub timestamp second may not be detectable and deleted prior attempts cannot be reconstructed. Consequently the current visible comment record is not mathematically append-only proof.

The GitHub server-created timestamp proves only that a specific SHA text is publicly visible as of that time under the limits of the record; it does not authenticate provider price facts, full source receipt times, the true existence/completeness of a private next-quote stream, bettor transaction amounts or honest scientific model preregistration. No actual upcoming new race was posted during the development of this protocol; the PR #22 comment thread was empty when checked.

An externally server-dated SHA alone cannot establish real horse social interactions, actual voter imitation, phase transition or positive expected bet profits.

## Verification

    python -m pip install 'numpy>=1.26,<3'
    python -m unittest discover -s tests \
      -p 'test_keiba_nextprice_pr_comment_attestation.py' -v

Synthetic tests cover post-target and pre-freeze comments, comment editing, duplicate SHA attempts, other authors and PR URLs, tampered digests, false self-declared evidence, full-field market probability preservation and API unavailability. Tests should never claim a real new prospective observation.

**Current real proof status: HOLD; no new future race sealed.**
