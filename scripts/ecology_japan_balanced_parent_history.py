"""Prepare cutoff-specific peer pools and draw equal historical counts on each side."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import numpy as np
import pandas as pd

import ecology_japan_2022_24_family_feature_ablation as ablation


PARENTS = ("sire_id", "dam_id")
COUNTS = ("sire_relative_count", "dam_relative_count")
KEYS = ["horse", "stratum"]
TAG = "keiba-equal-peer-v1"


def _integer(value):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
        raise ValueError("HOLD_INVALID_DRAW_OR_CUTOFF")
    return int(value)


def _json_bytes(values):
    return json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _key_suffix(cutoff, stratum, horse):
    return _json_bytes([cutoff, stratum, horse])[1:]


def _prefix(seed):
    return _json_bytes([TAG, _integer(seed)])[:-1] + b","


def peer_priority(seed, cutoff_year, stratum, horse) -> bytes:
    """Return the protocol SHA-256 digest for normalized historical identifiers."""
    ids = ablation.clean_id(pd.Series([stratum, horse], dtype=object))
    if ids.eq("").any():
        raise ValueError("HOLD_MISSING_PEER_IDENTIFIER")
    key = _prefix(seed) + _key_suffix(_integer(cutoff_year), ids.iloc[0], ids.iloc[1])
    return hashlib.sha256(key).digest()


@dataclass(frozen=True)
class _Pool:
    members: np.ndarray       # Historical horse/stratum row numbers with a recorded parent
    groups: np.ndarray        # Group per member, numbered from 1; 0 means missing
    offsets: np.ndarray       # Group starts in the sorted member array
    target_group: np.ndarray  # Group requested by each distinct target horse/stratum
    counts: np.ndarray        # Eligible members per request after excluding the focal


@dataclass(frozen=True)
class _Block:
    counts: pd.DataFrame
    k: np.ndarray
    own_counts: np.ndarray
    pools: tuple
    scores: np.ndarray
    key_suffixes: list
    focal: np.ndarray
    request_k: np.ndarray
    inverse: np.ndarray


def _identifiers(values):
    # Normalize distinct strings just once even for years of repeated starts.
    codes, unique = pd.factorize(values, use_na_sentinel=False)
    return ablation.clean_id(pd.Series(unique, dtype=object)).to_numpy()[codes]


def _days(frame):
    if pd.api.types.infer_dtype(frame.day, skipna=True) not in ("string", "datetime64", "datetime", "date"):
        raise ValueError("HOLD_INVALID_PEER_DATE")
    days = pd.to_datetime(frame.day, format="mixed", errors="coerce")
    if days.isna().any() or days.dt.tz is not None:
        raise ValueError("HOLD_INVALID_PEER_DATE")
    if "year" in frame and not np.array_equal(days.dt.year.to_numpy(), pd.to_numeric(frame.year, errors="coerce")):
        raise ValueError("HOLD_CONFLICTING_PEER_YEAR")
    return days


def _pool(members, requests, parent, focal):
    known = np.flatnonzero(members[parent].ne(""))
    group_cols = [parent, "stratum"]
    keys = pd.MultiIndex.from_frame(members.iloc[known][group_cols])
    groups = keys.unique()
    codes = groups.get_indexer(keys)
    codes = codes + 1
    target_group = groups.get_indexer(pd.MultiIndex.from_frame(requests[group_cols])) + 1
    sizes = np.bincount(codes, minlength=len(groups)+1)
    offsets = np.cumsum(sizes) - sizes
    # A focal in this stratum belongs to its recorded parent pool by the mapping gate.
    counts = sizes[target_group] - ((focal >= 0) & (target_group > 0))
    return _Pool(known, codes, offsets, target_group, counts)


def prepare_peer_block(history, target_context, *, cutoff_year):
    """Cache fixed pools and membership for the context rows in their supplied order."""
    cutoff_year = _integer(cutoff_year)
    required = {*KEYS, *PARENTS, "day", "y"}
    if (not isinstance(history, pd.DataFrame) or not isinstance(target_context, pd.DataFrame)
            or history.empty or target_context.empty or not history.columns.is_unique
            or not target_context.columns.is_unique or not required.issubset(history)
            or set(target_context.columns) != set(ablation.CONTEXT)):
        raise ValueError("HOLD_INVALID_PEER_HISTORY_OR_TARGET_CONTEXT")
    cutoff = pd.Timestamp(year=cutoff_year, month=1, day=1)
    past_day, target_day = _days(history), _days(target_context)
    if past_day.max() >= cutoff or target_day.min() < cutoff:
        raise ValueError("HOLD_INVALID_PEER_HISTORY_CUTOFF")
    distance = ablation._vector(target_context.distance, len(target_context))
    if (distance <= 0).any() or (_identifiers(target_context.surface) == "").any():
        raise ValueError("HOLD_INVALID_PEER_TARGET_CONTEXT")
    y = ablation._vector(history.y, len(history), bounded=True)
    cols = [*KEYS, *PARENTS]
    h, t = [pd.DataFrame({c: _identifiers(frame[c]) for c in cols})
            for frame in (history, target_context)]
    if h[KEYS].eq("").any().any() or t[KEYS].eq("").any().any():
        raise ValueError("HOLD_MISSING_PEER_IDENTIFIER")
    if "race" in history:
        races = pd.DataFrame({"race": _identifiers(history.race), "horse": h.horse, "day": past_day.to_numpy()})
        if (races.race.eq("").any() or races.duplicated(["horse", "race"]).any()
                or races[["race", "day"]].drop_duplicates().race.duplicated().any()):
            raise ValueError("HOLD_CONFLICTING_PEER_RACE_RECORD")
    family = ["horse", *PARENTS]
    parents = pd.concat([h[family].drop_duplicates(), t[family].drop_duplicates()]).drop_duplicates()
    if parents.horse.duplicated().any():
        raise ValueError("HOLD_CONFLICTING_PEER_PARENT_MAPPING")

    # Canonical order also makes the score reduction independent of input permutation.
    h["y"] = y
    h["day"] = past_day.to_numpy()
    h = h.sort_values(["horse", "stratum", "day", "y"])
    members = h.groupby(KEYS, sort=True).agg(score=("y", "mean"), starts=("y", "size")).reset_index()
    members["score"] -= .5
    members = members.join(parents.set_index("horse"), on="horse")
    requests = t.drop_duplicates(KEYS).reset_index(drop=True)
    request_keys = pd.MultiIndex.from_frame(requests[KEYS])
    inverse = request_keys.get_indexer(pd.MultiIndex.from_frame(t[KEYS]))
    focal = pd.MultiIndex.from_frame(members[KEYS]).get_indexer(request_keys)
    own = members.groupby("horse").starts.sum().reindex(t.horse, fill_value=0).to_numpy()
    pools = tuple(_pool(members, requests, parent, focal) for parent in PARENTS)
    counts = pd.DataFrame({name: pool.counts[inverse] for name, pool in zip(COUNTS, pools)})
    request_k = np.minimum(pools[0].counts, pools[1].counts)
    suffixes = [_key_suffix(cutoff_year, stratum, horse)
                for horse, stratum in members[KEYS].itertuples(index=False, name=None)]
    return _Block(counts, request_k[inverse], own, pools, members.score.to_numpy(), suffixes,
                  focal, request_k, inverse)


def _selected_sums(block, pool, ranks):
    k = block.request_k
    selected = np.zeros(len(k))
    active = k > 0
    if not active.any():
        return selected
    order = np.lexsort((ranks[pool.members], pool.groups))
    members = pool.members[order]
    groups = pool.groups[order]
    scores = block.scores[members]
    # Prefix sums start afresh in every parent/stratum to avoid cancellation across pools.
    prefix = pd.Series(scores).groupby(groups, sort=False).cumsum().to_numpy()
    rank_in_pool = np.full(len(ranks), -1, dtype=np.intp)
    rank_in_pool[members] = np.arange(len(members)) - pool.offsets[groups]
    focal = block.focal[active]
    local_rank = rank_in_pool[focal]
    skip_focal = (focal >= 0) & (local_rank >= 0) & (local_rank < k[active])
    last = pool.offsets[pool.target_group[active]] + k[active] - 1 + skip_focal
    selected[active] = prefix[last] - np.where(skip_focal, block.scores[focal], 0.)
    return selected


def balanced_performance(block, *, seed):
    """Use one shared priority per horse/stratum and one top-k lookup per side."""
    prefix = _prefix(seed)
    # V32 compares the entire digest bytewise, including embedded and trailing NULs.
    digests = np.fromiter((hashlib.sha256(prefix + suffix).digest() for suffix in block.key_suffixes),
                          dtype="V32", count=len(block.scores))
    # Members are in (horse, stratum) order, so stable sorting resolves ties by horse ID.
    order = np.argsort(digests, kind="stable")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(len(order))
    shrink = 5 / (block.own_counts + 5)
    return pd.DataFrame({name: shrink * _selected_sums(block, pool, ranks)[block.inverse] / (8 + block.k)
                         for name, pool in zip(ablation.PERFORMANCE, block.pools)})


def replace_performance(base_features, performance):
    """Copy the base and replace the two performance columns in positional order."""
    for frame in (base_features, performance):
        if (not isinstance(frame, pd.DataFrame) or frame.empty or not frame.columns.is_unique
                or not isinstance(frame.index, pd.RangeIndex)
                or not frame.index.equals(pd.RangeIndex(len(frame)))
                or not np.isfinite(frame.to_numpy(dtype=float)).all()):
            raise ValueError("HOLD_INVALID_OR_MISALIGNED_FEATURE_FRAME")
    if (not set(ablation.PERFORMANCE).issubset(base_features)
            or list(performance) != list(ablation.PERFORMANCE)
            or not performance.index.equals(base_features.index)):
        raise ValueError("HOLD_INVALID_OR_MISALIGNED_PERFORMANCE")
    result = base_features.copy()
    for column in ablation.PERFORMANCE:
        result[column] = performance[column].to_numpy(copy=True)
    return result
