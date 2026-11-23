#!/usr/bin/env python3
"""Within-race identifiability check for horse-indexed market price deviations.

Observed 9 archived complete win+wide price graphs, NOT multi-date horse IDs.
A single shared arbitrary function f(win quote) can interpolate any fitted
horse-node offsets on a finite set of UNIQUE win quotes. Thus horse-node fit
alone cannot identify an individual trait, however large leave-one-pair-out R2.

Identical *displayed* win odds create an exact internal falsification:
if horses i and j have equal quoted win strengths, a shared f(win odds) must
give the same node score; for every other horse k, coherent PL wide
marginals are invariant under swapping i/j. Any nonzero
  d(i,j;k)=log(q_ik/pPL_ik)-log(q_jk/pPL_jk)
cannot be explained by an IDENTICAL-quoted-price-only function.
This is an observational market price distinction, not biological identity,
and is sensitive to rounded/hidden win quotes, quote ranges and timing.

No JRA horse registry IDs, pedigree A, genomic G, actual repeated market
snapshots, voters, future outcomes or betting recommendations are used.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
import math
from pathlib import Path

try:
    from scripts.ecology_ticket_information_graph import graph_inputs, decompose_edges
    from scripts.ticket_type_models import predict_tickets
    from scripts.ticket_type_historical_audit import (
        SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from scripts.ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_information_graph import graph_inputs, decompose_edges
    from ticket_type_models import predict_tickets
    from ticket_type_historical_audit import (
        SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )

STATUS = "OBSERVED_DISPLAY_WIN_QUOTE_TIE_FALSIFICATION_NOT_BIOLOGICAL_IDENTIFICATION"
EQUAL_PRICE_QUANTIZATION = 0.1
TOL = 1e-9


def original_display_odds(strength: dict[int,float])->dict[int,float]:
    """Report only one-decimal JRA-style displayed prices; never invent ties."""
    output={}
    for i,v in strength.items():
        if not (type(i) is int and isinstance(v,(int,float)) and
                not isinstance(v,bool) and math.isfinite(v) and v>0):
            raise ValueError("missing_valid_strength")
        candidate=1./v
        shown=round(candidate,1)
        if abs(candidate-shown)>1e-7 or not 1<=shown<=999.9:
            raise ValueError("non_tenth_decimal_display_quote_cannot_infer_ties")
        output[i]=shown
    return output


def analyze_tied_quotes(race_id:str,date:str,strength:dict[int,float],
                        frames:dict[int,int],wide_quotes:list[dict])->dict:
    quoted=original_display_odds(strength)
    deviations,weights,base=graph_inputs(strength,frames,wide_quotes)
    if set(quoted)!=set(strength):
        raise ValueError("win_quote_coverage_lost")
    fitted=decompose_edges(deviations,weights)
    quote_ranges={}
    for quote in wide_quotes:
        pair=tuple(sorted(quote["selection"]))
        if pair in quote_ranges:
            raise ValueError("duplicate_quote_interval")
        low,high=quote["odds_low"],quote["odds_high"]
        if not (math.isfinite(low) and math.isfinite(high) and 1<=low<=high):
            raise ValueError("invalid_quote_interval")
        quote_ranges[pair]=(low,high)
    if set(quote_ranges)!=set(deviations):
        raise ValueError("incomplete_quote_intervals")
    groups={}
    for number,odds in quoted.items():
        groups.setdefault(odds,[]).append(number)
    tied=[tuple(sorted(group)) for group in groups.values() if len(group)>=2]
    tied.sort()
    comparisons=[]
    for group in tied:
        for i,j in combinations(group,2):
            differences=[]
            interval_disjoint=0
            rounding_PL_incompatible=0
            observed = quoted[i]
            lower=max(1.0, observed-0.05)
            upper=observed+0.05
            # Two win-odds rounding extremes provide the PL pair ratio
            # bounds for every third horse. All other win odds are held at
            # their displayed values: conditional, not universal, bounds.
            conditional_pl_extremes=[]
            for odds_i,odds_j in ((lower,upper),(upper,lower)):
                src=dict(strength)
                src[i]=1./odds_i
                src[j]=1./odds_j
                conditional_pl_extremes.append(predict_tickets(src,frames)["wide"])
            for k in sorted(quoted):
                if k in (i,j):
                    continue
                e1=tuple(sorted((i,k)))
                e2=tuple(sorted((j,k)))
                # Exact symmetry under exchange of tied winning strengths;
                # cannot be due to any global normalization of wide prices.
                baseline_delta=math.log(base["wide"][e1]/base["wide"][e2])
                if abs(baseline_delta)>1e-10:
                    raise ValueError("JRA_quote_tie_but_PL_marginal_asymmetric")
                d=deviations[e1]-deviations[e2]
                if not math.isfinite(d):
                    raise ValueError("invalid_opponent_matched_pair_difference")
                differences.append(d)
                lo_i,hi_i=quote_ranges[e1]
                lo_j,hi_j=quote_ranges[e2]
                if hi_i < lo_j or hi_j < lo_i:
                    interval_disjoint += 1
                # Wide price interval implies the support-ratio interval
                # [lo_j/hi_i, hi_j/lo_i], invariant to quote normalization.
                qmin, qmax=lo_j/hi_i,hi_j/lo_i
                pl_ratios=[
                    p[e1]/p[e2] for p in conditional_pl_extremes
                ]
                rmin,rmax=min(pl_ratios),max(pl_ratios)
                if qmax < rmin-1e-12 or qmin > rmax+1e-12:
                    rounding_PL_incompatible += 1
            comparisons.append({
                "two_horses_share_same_display_win_odds":True,
                "same_display_price":quoted[i],
                "other_horses_compared":len(differences),
                "mean_abs_wide_logprice_contrast":
                    math.fsum(abs(x) for x in differences)/len(differences),
                "max_abs_wide_logprice_contrast":max(abs(x) for x in differences),
                "opponent_comparisons_nonzero":sum(abs(d)>TOL for d in differences),
                "opponent_wide_price_ranges_nonoverlapping": interval_disjoint,
                "opponent_price_ranges_outside_conditional_PL_win_rounding_bound":
                    rounding_PL_incompatible,
                "fitted_horse_node_offset_difference_abs":
                    abs(fitted["node_effect"][i]-fitted["node_effect"][j]),
                "not_a_biological_trait":True
            })
    all_opponent_count=sum(r["other_horses_compared"] for r in comparisons)
    nonzero_count=sum(r["opponent_comparisons_nonzero"] for r in comparisons)
    interval_count=sum(r["opponent_wide_price_ranges_nonoverlapping"] for r in comparisons)
    rounding_count=sum(
        r["opponent_price_ranges_outside_conditional_PL_win_rounding_bound"]
        for r in comparisons
    )
    return {
        "race_id":race_id,"date":date,
        "runners":len(strength),
        "unique_display_win_quote_levels":len(groups),
        "tied_win_quote_groups":len(tied),
        "tied_horse_pair_count":len(comparisons),
        "same_win_quote_opponent_pair_comparisons":all_opponent_count,
        "same_win_quote_opponent_price_difference_count":nonzero_count,
        "opponent_wide_price_range_nonoverlap_count":interval_count,
        "opponent_outside_conditional_PL_win_rounding_bound_count":rounding_count,
        "same_win_quote_opponent_differences_are_all_exactly_zero":
            nonzero_count==0 if all_opponent_count else None,
        "mean_abs_matched_logprice_contrast_across_tied_pairs":
            (math.fsum(r["mean_abs_wide_logprice_contrast"]
                       for r in comparisons)/len(comparisons)) if comparisons else None,
        "maximum_abs_matched_logprice_contrast":
            max((r["max_abs_wide_logprice_contrast"] for r in comparisons),default=None),
        "max_fitted_node_difference_between_equal_quote_horses":
            max((r["fitted_horse_node_offset_difference_abs"] for r in comparisons),default=None),
        "tied_pair_summary_without_individual_horse_numbers":comparisons,
        "distinct_win_odds_can_always_support_arbitrary_finite_function_interpolation":
            len(groups)==len(strength),
        "exact_quote_ties_may_reflect_display_rounding":True,
        "stable_registry_horse_IDs_available_for_this_test":False,
    }


def run_analysis()->dict:
    hashes={}
    races=[]
    for number in TARGET_RACES:
        x=market_race(number,hashes)
        races.append(analyze_tied_quotes(
            x["race_id"],SOURCE_DATE,
            {i:1./odds for i,odds in x["win_odds"].items()},
            x["frames"],x["markets"]["wide"],
        ))
    other=read_json(SAVED_SNAPSHOT_PATH,hashes)
    eligible,coverage=eligible_four_market_only(other)
    for row in eligible:
        races.append(analyze_tied_quotes(
            row["race_id"],SECOND_DATE,row["strengths"],
            row["frames"],row["wide_quotes"],
        ))
    if len(races)!=9:
        raise ValueError("incomplete_two_day_archive")
    by_date={}
    for date in (SOURCE_DATE,SECOND_DATE):
        sub=[r for r in races if r["date"]==date]
        by_date[date]={
            "race_count":len(sub),
            "races_with_equal_display_win_odds":sum(r["tied_horse_pair_count"]>0 for r in sub),
            "races_with_tie_opponent_price_contrast":sum(
                r["same_win_quote_opponent_price_difference_count"]>0 for r in sub),
            "total_equal_odds_horse_pairs":sum(r["tied_horse_pair_count"] for r in sub),
            "total_opponent_matched_comparisons":sum(
                r["same_win_quote_opponent_pair_comparisons"] for r in sub),
            "total_nonzero_opponent_matched_price_contrasts":sum(
                r["same_win_quote_opponent_price_difference_count"] for r in sub),
            "total_nonoverlapping_wide_quote_ranges":sum(
                r["opponent_wide_price_range_nonoverlap_count"] for r in sub),
            "total_opponent_ranges_outside_conditional_PL_win_rounding_bounds":sum(
                r["opponent_outside_conditional_PL_win_rounding_bound_count"] for r in sub),
        }
    return {
        "schema_version":1,"status":STATUS,
        "scope":"the same 9 races and 2 dates, same cross sections as prior horse-node market analysis",
        "identification_theorem":"For N distinct win-quote values, an unrestricted f(log win odds) can interpolate ANY set of N fitted node coefficients; cross-sectional horse identity effects are not identifiable without function restrictions or time/ID replication.",
        "tie_null":"For two equal-display-win-odd horses, all other-opponent wide price deviations must match under any identical-quote-only function with symmetric PL baseline.",
        "display_quote_resolution":EQUAL_PRICE_QUANTIZATION,
        "source_quoted_odds_are_not_latent_exact_probabilities":True,
        "rounding_sensitivity_is_conditional_on_fixed_other_win_prices_and_P_L_model":True,
        "wide_price_quote_ranges_robustly_separated_when_nonoverlapping":True,
        "no_registered_horse_identity_repeatability_tested":True,
        "no_independent_time_series_or_outcome_validation":True,
        "no_inference_about_heritability_or_actual_voter_behavior":True,
        "not_any_win_price_only_model_rejected_except_at_exact_ties":True,
        "by_date":by_date,"races":races,
        "input_file_sha256":dict(sorted(hashes.items())),
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    try:
        data=run_analysis()
    except (ValueError,KeyError,TypeError,OSError) as exc:
        p.error(str(exc))
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(raw,encoding="utf-8")
    else:
        print(raw,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
