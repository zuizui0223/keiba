"""As-of exact-last-year and historical-stratum-start-depth nonkin counterfactual.

Select the PR73 actual same-parent peers first, then draw nonparent-sharing
peers from the SAME final history calendar year and SAME 1/2-4/5+ start-depth
bin. If any matching unit cannot be filled without replacement, record HOLD
for the full fixed cohort. Predictions and original identifiers stay private.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import numpy as np
import pandas as pd
import ecology_japan_balanced_parent_history as balanced
import ecology_japan_unrelated_peer_control as original
import ecology_japan_2022_24_family_feature_ablation as ablation

TAG="keiba-matched-nonkin-start-v1"
BIN_NAMES=("1","2-4","5+")


def _bin(n):
    if int(n)<1:
        raise ValueError("HOLD_INVALID_STRATUM_HISTORY_COUNT")
    return "1" if int(n)==1 else "2-4" if int(n)<=4 else "5+"


@dataclass(frozen=True)
class MatchedBlock:
    base: original.UnrelatedBlock
    history_last_year: np.ndarray
    history_start_bin: np.ndarray
    groups: dict


def prepare_temporal_match(history, target_context, source, *, cutoff_year):
    """Bind exact member recency/size to the already verified PR73 block."""
    anchor=original.prepare_unrelated_block(history,target_context,source,
                                           cutoff_year=cutoff_year)
    member=original._normalized(history,["horse","stratum"])
    member["day"]=balanced._days(history).to_numpy()
    grouped=member.groupby(["horse","stratum"],sort=True,observed=True).agg(
        last_day=("day","max"),starts=("day","size")).reset_index()
    if len(grouped)!=len(source.scores) or not np.array_equal(
            grouped[["horse","stratum"]].to_numpy(),
            np.column_stack([anchor.member_horse,
                             np.asarray([v for v in source.key_suffixes])])[:,:0]):
        # The actual identity/ordering guarantee comes from the validated
        # source key suffixes below, not any NumPy structured-dtype coercion.
        if len(grouped)!=len(source.scores):
            raise ValueError("HOLD_MATCH_HISTORY_MEMBER_PARITY")
    keys=[balanced._key_suffix(cutoff_year,r.stratum,r.horse)
          for r in grouped.itertuples()]
    if keys!=source.key_suffixes:
        raise ValueError("HOLD_MATCH_HISTORY_ORDER_PARITY")
    years=grouped.last_day.dt.year.to_numpy(np.int16)
    counts=grouped.starts.to_numpy(int)
    bins=np.array([_bin(v) for v in counts],dtype=object)
    groups=defaultdict(list)
    for i, (stratum, year, nbin) in enumerate(zip(
            grouped.stratum.to_numpy(),years,bins)):
        if anchor.member_sire[i] and anchor.member_dam[i]:
            groups[(stratum,int(year),nbin)].append(i)
    return MatchedBlock(anchor,years,bins,{k:np.asarray(v,dtype=np.intp)
                                          for k,v in groups.items()})


def _select_true(block, side, ranks):
    """Select the PR73 top-k peers excluding the focal, same hash priority."""
    base=block.base.source
    parent=base.pools[side]
    order=np.lexsort((ranks[parent.members],parent.groups))
    arranged=parent.members[order]
    out=[]
    for i,k in enumerate(base.request_k):
        if k==0:
            out.append(())
            continue
        g=int(parent.target_group[i])
        if g<=0:
            raise ValueError("HOLD_NO_RECORDED_TARGET_PARENT_GROUP")
        first=int(parent.offsets[g])
        # The extra slot is required iff the focal was among the top k.
        indices=arranged[first:first+int(k)+1]
        chosen=tuple(int(v) for v in indices if v!=base.focal[i])[:int(k)]
        if len(chosen)!=k:
            raise ValueError("HOLD_SELECTED_TRUE_PEER_NUMBER_MISMATCH")
        out.append(chosen)
    # Reproduce exact PR73 selected score, before using any nonkin information.
    raw=np.array([sum(base.scores[list(x)]) if x else 0. for x in out])
    old=balanced._selected_sums(base,parent,ranks)
    if not np.allclose(raw,old,atol=1e-12,rtol=0):
        raise ValueError("HOLD_TRUE_PEER_SELECTION_VS_PR73_LOSS_PARITY")
    return out


def _offset(seed, cutoff, stratum, focal, side, last_year, countbin, n):
    p=[TAG,int(seed),int(cutoff),str(stratum),str(focal),
       "sire" if side==0 else "dam",int(last_year),str(countbin)]
    digest=hashlib.sha256(json.dumps(p,ensure_ascii=False,
                     separators=(",",":")).encode("utf-8")).digest()
    return int.from_bytes(digest[:8],"big")%n


def sample_matched(block, *, seed, side):
    """Return features+support counts for one side; failure never imputes peers."""
    if not isinstance(block,MatchedBlock) or side not in (0,1):
        raise ValueError("HOLD_UNVERIFIED_MATCHED_BLOCK_OR_SIDE")
    source=block.base.source
    anchor=block.base
    prefix=balanced._prefix(seed)
    digests=np.fromiter((hashlib.sha256(prefix+v).digest()
                         for v in source.key_suffixes),
                         dtype="V32",count=len(source.scores))
    ranks=np.empty(len(digests),dtype=np.intp)
    order=np.argsort(digests,kind="stable")
    ranks[order]=np.arange(len(order))
    true=_select_true(block,side,ranks)
    ranked={cat:indices[np.argsort(ranks[indices],kind="stable")]
            for cat,indices in block.groups.items()}
    out=np.zeros(len(source.request_k),dtype=float)
    total_slots=0
    matched_slots=0
    unsupported_requests=0
    unsupported_slots=0
    support_by_bin=Counter()
    missing_by_bin=Counter()
    # Each unique horse × stratum is processed once, not once per start.
    for i, peers in enumerate(true):
        if not peers:
            continue
        target_sire=anchor.request_sire[i]
        target_dam=anchor.request_dam[i]
        focal=anchor.request_horse[i]
        stratum=anchor.request_stratum[i]
        demand=Counter((int(block.history_last_year[j]),block.history_start_bin[j])
                       for j in peers)
        total_slots+=len(peers)
        result=0.
        failed=False
        for (year,nbin),needed in demand.items():
            candidates=ranked.get((stratum,year,nbin),np.array([],dtype=np.intp))
            if len(candidates)==0:
                failed=True
                unsupported_slots+=needed
                missing_by_bin[nbin]+=needed
                continue
            good=((anchor.member_horse[candidates]!=focal) &
                  (anchor.member_sire[candidates]!=target_sire) &
                  (anchor.member_dam[candidates]!=target_dam))
            available=int(good.sum())
            if available<needed:
                failed=True
                unsupported_slots+=needed-available
                missing_by_bin[nbin]+=needed-available
                continue
            start=_offset(seed,block.base.cutoff,stratum,focal,side,year,nbin,len(candidates))
            selected=[]
            for j in range(len(candidates)):
                idx=candidates[(start+j)%len(candidates)]
                if (anchor.member_horse[idx]!=focal and
                    anchor.member_sire[idx]!=target_sire and
                    anchor.member_dam[idx]!=target_dam):
                    selected.append(idx)
                    if len(selected)==needed:
                        break
            if len(selected)!=needed:
                raise ValueError("HOLD_VALIDATED_MATCH_SUPPLY_NOT_USED")
            result+=float(source.scores[selected].sum())
            matched_slots+=needed
            support_by_bin[nbin]+=needed
        if failed:
            unsupported_requests+=1
        else:
            out[i]=result
    stats={"source_cutoff_year":int(block.base.cutoff),
           "side":"sire" if side==0 else "dam",
           "seed":int(seed),
           "unique_requests":len(source.request_k),
           "positive_k_requests":int((source.request_k>0).sum()),
           "requested_true_peer_slots":int(total_slots),
           "matched_peer_slots":int(matched_slots),
           "unsupported_request_groups":int(unsupported_requests),
           "minimum_missing_slots":int(unsupported_slots),
           "supported_selected_peer_bins":{v:int(support_by_bin[v]) for v in BIN_NAMES},
           "unmatched_selected_peer_bins":{v:int(missing_by_bin[v]) for v in BIN_NAMES},
           "no_replacement_outside_exact_calendar_year_and_start_bin":True,
           "historical_nonkin_candidates_both_parent_IDs_known":True,
           "observed_target_loss_unused_in_matching":True}
    if unsupported_requests:
        return None,{**stats,"status":"HOLD_EXACT_YEAR_AND_HISTORY_DEPTH_MATCHING_SUPPORT"}
    if matched_slots!=total_slots:
        raise ValueError("HOLD_EXACT_MATCH_ALLOCATION_ACCOUNTING")
    weights=5/(source.own_counts+5)
    per_start=weights*out[source.inverse]/(8+source.k)
    if not np.isfinite(per_start).all():
        raise ValueError("HOLD_NONFINITE_MATCHED_NONKIN_FEATURE")
    return per_start,{**stats,"status":"OK_EXACT_YEAR_DEPTH_MATCHED_NONKIN"}
