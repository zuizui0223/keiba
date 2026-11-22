"""Source-as-of same-k unrelated peer placebo for the PR73 parent-history comparison.

No target outcomes, future results, or horse/parent identities leave the runner.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import numpy as np
import pandas as pd

import ecology_japan_2022_24_family_feature_ablation as ablation
import ecology_japan_balanced_parent_history as balanced


START_TAG = "keiba-unrelated-start-v1"


@dataclass(frozen=True)
class UnrelatedBlock:
    source: balanced._Block
    cutoff: int
    candidate_indices: tuple
    request_group: np.ndarray
    member_horse: np.ndarray
    member_sire: np.ndarray
    member_dam: np.ndarray
    request_horse: np.ndarray
    request_sire: np.ndarray
    request_dam: np.ndarray
    request_stratum: np.ndarray


def _normalized(frame, cols):
    return pd.DataFrame({col: balanced._identifiers(frame[col]) for col in cols})


def prepare_unrelated_block(history, targets, source, *, cutoff_year):
    """Tie candidate IDs to a validated historical feature block.

    The original block has already checked dates, family IDs and cutoff
    ordering and owns the observed history score and original k values.
    """
    if not isinstance(source, balanced._Block):
        raise ValueError("HOLD_UNVERIFIED_EQUAL_PEER_BLOCK")
    cutoff = balanced._integer(cutoff_year)
    if (not isinstance(history, pd.DataFrame) or not isinstance(targets, pd.DataFrame)
            or not set(ablation.CONTEXT).issubset(targets)):
        raise ValueError("HOLD_INVALID_UNRELATED_CONTEXT")
    cols = ["horse", "stratum", "sire_id", "dam_id"]
    if not set(cols).issubset(history):
        raise ValueError("HOLD_INVALID_UNRELATED_HISTORY")
    h = _normalized(history, cols).drop_duplicates().sort_values(cols[:2]).reset_index(drop=True)
    t = _normalized(targets, cols).drop_duplicates(cols[:2]).reset_index(drop=True)
    if (len(h) != len(source.scores) or len(t) != len(source.request_k)
            or len(source.key_suffixes) != len(h)):
        raise ValueError("HOLD_UNRELATED_HISTORY_MEMBERSHIP_MISMATCH")
    keys = [balanced._key_suffix(cutoff, r.stratum, r.horse) for r in h.itertuples()]
    if keys != source.key_suffixes:
        raise ValueError("HOLD_UNRELATED_HISTORY_ORDER_MISMATCH")
    if not np.array_equal(t.loc[:, cols[:2]].to_numpy(),
                          _normalized(targets, cols).drop_duplicates(cols[:2]).loc[:, cols[:2]].to_numpy()):
        raise ValueError("HOLD_UNRELATED_REQUEST_ORDER_MISMATCH")
    # No horse with unrecorded sire OR dam can be certified as unrelated.
    eligible = h.sire_id.ne("") & h.dam_id.ne("")
    codes, strata = pd.factorize(h.stratum, sort=True)
    sets = tuple(np.flatnonzero(eligible.to_numpy() & (codes == i)) for i in range(len(strata)))
    req_group = strata.get_indexer(t.stratum)
    if np.any((source.request_k > 0) & (req_group < 0)):
        raise ValueError("HOLD_UNRELATED_MISSING_HISTORICAL_STRATUM")
    if np.any((source.request_k > 0) & (t.sire_id.eq("") | t.dam_id.eq(""))):
        raise ValueError("HOLD_UNRELATED_MISSING_TARGET_PARENT")
    return UnrelatedBlock(source, cutoff, sets, req_group,
                          h.horse.to_numpy(), h.sire_id.to_numpy(), h.dam_id.to_numpy(),
                          t.horse.to_numpy(), t.sire_id.to_numpy(), t.dam_id.to_numpy(),
                          t.stratum.to_numpy())


def _offset(seed, cutoff, stratum, focal, n):
    payload = json.dumps([START_TAG, int(seed), int(cutoff), str(stratum), str(focal)],
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % n


def unrelated_performance(block, *, seed):
    """Same-k, same-stratum peer performance from neither-parent-sharing horses.

    Only the start offset, not the global candidate priority, depends on the focal
    horse. The candidate ranking is shared across all targets for each cutoff.
    """
    if not isinstance(block, UnrelatedBlock):
        raise ValueError("HOLD_UNVERIFIED_UNRELATED_BLOCK")
    base = block.source
    prefix = balanced._prefix(seed)
    digests = np.fromiter((hashlib.sha256(prefix + s).digest() for s in base.key_suffixes),
                          dtype="V32", count=len(base.scores))
    ranked = tuple(idx[np.argsort(digests[idx], kind="stable")] for idx in block.candidate_indices)
    result = np.zeros(len(base.request_k), dtype=float)
    for i, k in enumerate(base.request_k):
        if k == 0:
            continue
        g = block.request_group[i]
        if g < 0:
            raise ValueError("HOLD_NO_UNRELATED_STRATUM")
        population = ranked[g]
        n = len(population)
        if k > n:
            raise ValueError("HOLD_TOO_FEW_UNRELATED_PEERS")
        start = _offset(seed, block.cutoff, block.request_stratum[i], block.request_horse[i], n)
        count = 0
        total = 0.
        for j in range(n):
            idx = population[(start + j) % n]
            if (block.member_horse[idx] == block.request_horse[i]
                    or block.member_sire[idx] == block.request_sire[i]
                    or block.member_dam[idx] == block.request_dam[i]):
                continue
            count += 1
            total += base.scores[idx]
            if count == k:
                break
        if count < k:
            raise ValueError("HOLD_TOO_FEW_UNRELATED_PEERS")
        result[i] = total
    shrink = 5. / (base.own_counts + 5.)
    values = shrink * result[base.inverse] / (8. + base.k)
    if not np.isfinite(values).all():
        raise ValueError("HOLD_NONFINITE_UNRELATED_PERFORMANCE")
    # The same false-kin covariate can be fitted in the MS OR MD slot.
    return pd.DataFrame({col: values for col in ablation.PERFORMANCE})
