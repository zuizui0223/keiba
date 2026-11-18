# 2027 GitHub pre-race pledge: first real server-API integration rehearsal

**November 18, 2026 — Real GitHub API connectivity SUCCESS; ALL SOURCE HORSES, RACES AND PREDICTIONS SYNTHETIC.** No actual 2027 forecast, licensed JRA-VAN record, registered racing horse, betting evaluation or prospective family effect exists in this report.

## Actual external evidence

- [Successful real GitHub Actions push run #44255047320](https://github.com/zuizui0223/keiba/actions/runs/44255047320) — GitHub's API reported `created_at=2026-11-18T06:56:27Z` (15:56:27 JST), `event=push`, `run_attempt=1`, repository `zuizui0223/keiba`, `head_sha=e1ef76be45b939555fff107d4e1249e0ece6329b`, staging workflow `.github/workflows/ecology-japan-2027-server-rehearsal.yml`, completed SUCCESS.
- In this same run, the code contacted the *real* `api.github.com` Actions run endpoint and its source contents endpoint with an exact immutable commit SHA. The returned source code bytes matched the checked-out file and the returned Git blob SHA matched an independent SHA-1 calculation. Only the rehearsal source code was fetched, **not a JRA-VAN dataset**.
- The staged fictional source manifest explicitly carried `synthetic_test_only=True` and `local_clock_injected_for_synthetic_test=True`; the **production** pledge validator correctly rejected it. The script only passed with an explicitly synthetic rehearsal mode and a distinct, allowlisted staging workflow path.
- The successful run executed **36 source/bundle/server-time synthetic unit tests** plus **4 production workflow source-contract tests**, all passing. Source/API evidence is pinned in [the inspectable JSON](../evidence/japan-2027-github-real-server-rehearsal-20261118.json).

## Repaired failure modes

The production code now rejects `run_attempt > 1`: GitHub Actions reruns retain the *original* run's `created_at`, so without this gate a failed before-race run rerun after the race could be misrepresented as a new successful before-race attestation. A genuine pledge must originate from the exact expected production workflow path, not an unrelated push workflow. Only a staging-only synthetic flag permits the staging path.

A separate [original-commit verifier](../../scripts/ecology_japan_2027_github_push_attestation.py) now has a `verify-original` command intended to be used *after a real race*. Its input is the exact previously committed anonymous bundle, immutable 40-character Git SHA, and the real successful production run ID. It verifies the historical GitHub REST contents response by that immutable SHA, original file bytes, Git blob SHA, `run_attempt=1`, expected production workflow path, successful completed run and actual GitHub server creation time before the declared race. A mismatch produces HOLD. This verifier was tested with injected fictional REST responses, **not on an actual JRA prediction**.

The initial rehearsal [run #44254467784](https://github.com/zuizui0223/keiba/actions/runs/44254467784) failed correctly because the fictional UTC and JST capture-finished timestamps did not agree. The inconsistent synthetic timestamps were fixed before the successful real-API integration runs. This negative gate remains part of the protocol.

## Remaining missing evidence

1. A **permitted, independently identifiable** real JRA-VAN blood-ID and pedigree master, real pre-race entrant/receipt snapshots and true source licensing.
2. A genuine pre-2027 M1/M2 model with a fully audited historical known-at record. No artificial MakeDate-to-publication-time assignment.
3. The first **actual** pre-race public pledge in `docs/commitments/2027/<opaque-sha>.json` on a branch with the real production workflow; a server-created push run SUCCESS before the **officially checked** JRA start.
4. The corresponding private source bytes, freeze files and post-race actual full results; an immutable GitHub SHA opening and a source-based score M0 versus M1 versus M2.

Thus this completed task strengthens the audit trail for a future prospective prediction, **not the evidence for a new family-history forecast or genetic inheritance**. Existing observations remain: 2022–24 parent-history gains were tiny and sample conditional; a stale 2026 external period did not transfer robustly; refreshing the own horse's history in the already inspected 2026 sample was much more valuable than refreshing relatives, but the latter analysis was post-hoc. Full Japan JRA+NAR pedigree A and horse-linked DNA G remain HOLD.

## Implementation

- [Real server staging runner](../../scripts/ecology_japan_2027_github_server_rehearsal.py) and [staging-only workflow](../../.github/workflows/ecology-japan-2027-server-rehearsal.yml).
- [Production attestor, source/forecast bundler and exact original GitHub SHA verifier](../../scripts/ecology_japan_2027_github_push_attestation.py).
- [Prior production push-only workflow](../../.github/workflows/ecology-japan-2027-immutable-push-attestation.yml) and [fixed protocol](JAPAN_2027_GITHUB_PUSH_ATTESTATION_PROTOCOL.md).

No original horse race results, registered animal IDs, betting data, genomic information or private model coefficients were uploaded.
