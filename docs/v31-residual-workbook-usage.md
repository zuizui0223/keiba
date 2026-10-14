# v3.1: post-race residual evidence workbook

This is an **optional descriptive companion** to the frozen holdout workflow. It does not affect the v3.1 candidate set, the formal score, the 20-race denominator, or the PROMOTE/NO_PROMOTION contract.

The official JRA finishing order must be checked independently by the operator before the minimal `result.json` is accepted. The workbook does **not** independently authenticate the official result website, and explicitly records that limitation.

## One workbook per scored race

Only after a valid pre-race freeze, official result verification, score calculation and FROZEN attempt registration, run:

```bash
python -B scripts/v31_residual_workbook.py \
  --freeze holdout/v31/001/freeze.json \
  --result holdout/v31/001/result.json \
  --score holdout/v31/001/score.json \
  --attempt-ledger docs/v31-holdout-attempt-ledger.json \
  --race-input holdout/v31/001/race-input.json \
  --source-meta holdout/v31/001/source-capture-meta.json \
  --output holdout/v31/001/residual-workbook.json
```

Before writing the workbook, the tool calls the independent v3.1 post-race validator and verifies that the saved pre-race history and source metadata still match the SHA-256 hashes embedded in `freeze.json`. Modified scores or altered histories are rejected.

## What it records

Each *actual top-three horse missing from the frozen union* gets a row with:

- finish position, **frozen pre-race** win odds and market rank;
- frozen M/C1/U/Q1/K1/rescue/union flags and uncertainty flags;
- frozen Kyoto-course counts and the exact prior history contained in `race-input.json`;
- an initially unreviewed explanation field and placeholders for independent post-race evidence;
- SHA-256 provenance for freeze, result, score, race-input and source metadata.

The workbook also records the number of union candidates that **did not finish in the top three**. This is candidate-set breadth, not necessarily evidence that individual horses were poor predictions.

## Explanation protocol

Every unexplained row starts with `classification = UNREVIEWED`. A reviewer may later classify it as DATA, REPRESENTATION, THRESHOLD, STATE_STOCHASTIC or UNRESOLVED only after checking the evidence in `docs/v31-residual-audit-protocol.md`.

In particular:

- An unexpected result is **not** evidence by itself for poor fitness, a trip problem, pace or randomness.
- A pre-race source missing from the freeze is a possible DATA residual, but must be documented rather than silently inserted.
- A narrow cutoff miss can be described as a THRESHOLD residual without changing the cutoff.
- If none of the evidence discriminates among explanations, keep the cause **UNRESOLVED**.

No review may edit the original freeze, official result record, score or attempt ledger. Any later reviewed version of the workbook should be preserved as a **separate versioned artifact**, with the initial unreviewed workbook retained.

## Example: no missed top-three horse

Even a race with zero union misses produces a workbook showing `union_miss_count = 0` and `non_top3_union_candidates`. This avoids reporting only failures and dropping candidate-breadth information.

## Automated scoring

The 2026-10-17 scoring workflow should generate a workbook for each scored FROZEN race after independent result verification. If workbook generation fails, preserve the valid formal score and report the descriptive audit failure separately. Do **not** retroactively change the freeze or formal score.

## Verification

```bash
python -m unittest tests.test_v31_residual_workbook -v
python -m unittest discover -s tests -v
```

This tool is intentionally **not** listed among the frozen v3.1 scientific classifier/decision-contract blobs: it is an evidence-presentation aid introduced before the first real holdout, not a source of candidate membership or formal test statistics.
