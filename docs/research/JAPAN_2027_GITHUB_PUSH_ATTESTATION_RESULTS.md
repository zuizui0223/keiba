# JRA 2027: server-timestamped GitHub pre-race aggregate forecast commitments

**2026-11-18 STATUS: SOFTWARE AND SYNTHETIC CI VERIFIED; NO ACTUAL 2027 RACE BUNDLE.** This is not a JRA source-publication certification, a data license, an empirically fitted M1/M2 model, or a real 2027 forecast.

[Source-and-forecast pledge bundler](../../scripts/ecology_japan_2027_github_push_attestation.py) and a separate [push-only GitHub Actions validator](../../.github/workflows/ecology-japan-2027-immutable-push-attestation.yml) connect the PR #53 locally frozen pre-race SQLite receipt, its normalized private entrant+parent file SHA256, and PR #51 private M0/M1/M2 forecast digest.

## Validated software result

[GitHub Actions #44250171941](https://github.com/zuizui0223/keiba/actions/runs/44250171941) completed with **29 fictional-source/test-race SHA and chronology tests**, plus **4 production push-workflow security tests**, all successful. No actual JRA records, real 2027 start, real pre-race bundle or prediction were used. The real server-side push gate has **not run for an actual race**. Source and proof status are preserved in the [aggregate QA evidence](../evidence/japan-2027-github-server-attestation-synthetic-qa-20261118.json).

Covered tests: hashed source/adapter/forecast file linkage, automatic anonymous content-addressed filename, one complete race per source capture, source-first-observed bound, pre-race forecast time ordering, immutable original private source and model opening, failed SHA mismatch, duplicate JSON key rejection, rejecting simulated late Github runs, forged Git SHA, wrong repository and non-push events. The production workflow additionally refuses an edited/replaced commitment, non-opaque filename, non-content-matching filename, fake test clock and an unauthenticated push event.

## Data/provenance chain

1. Capture one permitted local JRA-VAN SQLite snapshot before the actual race, using the PR #53 read-only and atomic backup. Store the private original outside Git; a public source receipt exposes only timestamps, SHA and aggregate QA.
2. Convert the exact pre-race snapshot with PR #53 adapter to private entrants and parent CSVs. Its aggregate-only QA contains hashes of the precise files. Blood-registration H: and breeding-registration B: IDs remain distinct, and the source may not already include final race ranks.
3. Use a legitimately pre-2027-fitted private M1/M2 model and PR #51 freeze command to prepare exact private predictions and an aggregate-only public commitment (source entry, parent, history, model and private prediction hashes).
4. Create ONE public bundle from these three aggregate manifests. The new bundler accepts only a strict whitelist of source/forecast metadata (no raw horse or race IDs, original rows, owner/stable names or individual predictions). The filename is a SHA-derived 32-hex opaque content address. Declared race-start timestamp and aggregate number of starters **are public** and can reveal which event was studied.
5. Commit this new bundle to docs/commitments/2027/<32hex>.json; push to GitHub before the real start. The separate production workflow triggers **only for push** (not pull-request/manual replay), verifies the exact pushed SHA, the before→after Git file additions (not edits), and checks GitHub REST run.created_at against the race start and the local forecast-frozen time. Git author/committer timestamps, JV-Data MakeDate and the user's computer clock cannot be substituted for the server's creation time.
6. After the race, retrieve the **original pre-race commit SHA** and locally open/verify original private snapshot, source aggregate files, private normalized entrants/parents/history/model and private individual predictions against that immutable public bundle. Then separately score actual, complete later-published results via PR #51. Private originals and outcomes NEVER need to be uploaded to GitHub.

Passing the server-created-at check is evidence only that an **aggregate pledge existed on GitHub before its declared race time**. Source authenticity, actual legal JRA access, official race-start verification and the local machine's claimed first receipt of data remain independent requirements. A public SHA alone is not proof of external source publication.

## Local CLI, once legitimate inputs exist

Paths below are illustrative. There are NO actual licensed source files or genuine fitted coefficients in this project.

~~~bash
python scripts/ecology_japan_2027_github_push_attestation.py bundle \
  --pre-source-receipt /private/receipts/pre.aggregate.json \
  --pre-adapter-summary /private/normalized/pre.aggregate.json \
  --forecast-public-commitment /private/predictions/frozen.aggregate.json \
  --commit-directory docs/commitments/2027

# Commit ONLY the printed new opaque aggregate bundle before race start.
git add docs/commitments/2027/<opaque-32hex>.json
git commit -m 'research: preregister JRA forecast-source aggregate'
git push origin <branch-with-the-push-workflow>
~~~

A push workflow created by the GitHub server before the race is necessary. The actual output must be SUCCESS. If it is too late, an existing pledge was rewritten, the event was a manual action, or source hashes differ, the production check fails. Do not use an older development CI success to claim a real 2027 pledge occurred.

After the racing results are available:

~~~bash
python scripts/ecology_japan_2027_github_push_attestation.py open-private \
  --bundle /private/immutable_bundle_from_original_commit.json \
  --pre-source-receipt /private/receipts/pre.aggregate.json \
  --pre-adapter-summary /private/normalized/pre.aggregate.json \
  --forecast-public-commitment /private/predictions/frozen.aggregate.json \
  --private-forecast /private/predictions/by_horse.json \
  --private-source-snapshot /private/source/pre.sqlite \
  --private-entries /private/normalized/entries.csv \
  --private-parents /private/normalized/parents.csv \
  --private-history /private/known_at/history.csv \
  --private-model /private/models/m1_m2_coefficients.json \
  --result-aggregate /private/qa/opened_source_and_forecast_hashes.json
~~~

This private SHA-opening does **not** revalidate the GitHub server timestamp; that is a separate prerequisite and is recorded in the GitHub Actions successful PUSH run. Nor does it score real outcomes; the existing PR #51 scorer handles that separately.

## Why this is not yet a genetic result

There are no licensed official JRA 2027 entry/result records or public prospective race forecasts to evaluate. Past partial 2026 year evaluations were inspected and post-hoc; they cannot substitute for a new 2027 holdout. The future source may still lack comprehensive NAR coverage, a full pedigree A, identified DNA genotypes G or source-certified historic event publication times. Improved predictions from recorded same-parent horses cannot by themselves distinguish genetic effects from breeding-farm, stable, rider, owner and selection environment.

[Pre-race attestation protocol](JAPAN_2027_GITHUB_PUSH_ATTESTATION_PROTOCOL.md) | [machine-readable synthetic evidence](../evidence/japan-2027-github-server-attestation-synthetic-qa-20261118.json).
