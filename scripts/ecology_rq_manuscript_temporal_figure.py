#!/usr/bin/env python3
"""Validate and plot ONLY frozen anonymous aggregate manuscript evidence.

No network, no original HORSES IDs, rider/trainer IDs, source XML or
individual timings. Does not infer a causal year effect from two
different venues/source cohorts. Supports SVG figure for research Draft PR.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"docs"/"evidence"/"rq-racehorse-temporal-generalization-20261015.json"
PALETTE={"zero":"#929DAA","own":"#31485A","other_horses_context":"#B7AEA2"}
LIMIT=0.45


def checked_evidence(path:Path=EVIDENCE)->dict:
    z=json.loads(path.read_text(encoding="utf-8"))
    if z["scientific_status"]!="POST_HOC_SOURCE_CONDITIONAL_OBSERVATIONAL_CONTRAST_NOT_CAUSAL":
        raise ValueError("HOLD_MANUSCRIPT_EVIDENCE_NOT_EXPLORATORY")
    a=z["within_year_cannon"]
    b=z["year_forward_doomben"]
    assert a["original_racecourse"]=="Cannon Park"
    assert b["original_racecourse"]=="Doomben"
    if not (a["scored_distinct_original_horses"]==36
            and a["scored_future_rows"]==46
            and b["scored_distinct_original_horses"]==26
            and b["scored_future_rows"]==27):
        raise ValueError("HOLD_MANUSCRIPT_SOURCE_POPULATION_MISMATCH")
    if b["original_dates_successful"]+len(b["original_dates_HOLD"])!=b["original_dates_locked_total"]:
        raise ValueError("HOLD_CROSS_YEAR_SOURCE_DATE_DENOMINATOR_INCONSISTENT")
    if a["source_original_dates_successful"]!=12:
        raise ValueError("HOLD_CANNON_SOURCE_DATE_INCOMPLETE")
    if not (z["limitations"]["cannon_old_horse_roster_digest_missing"]
            and z["limitations"]["doomben_original_date_coverage_incomplete"]
            and not z["limitations"]["measured_actual_starter_or_final_jockey"]
            and not z["limitations"]["h1_ground_reaction_norm_fitted"]
            and not z["limitations"]["h2_competitor_causal_effect_estimated"]):
        raise ValueError("HOLD_UNSUPPORTED_ECOLOGICAL_CAUSAL_CLAIM")
    for label,cohort in (("Cannon",a),("Doomben",b)):
        err=cohort["rmse_seconds"]
        if set(err)!={"zero","own","other_horses_context"}:
            raise ValueError("HOLD_MANUSCRIPT_RMSE_ENDPOINT_MISSING")
        if not all(math.isfinite(float(val)) and 0<float(val)<LIMIT for val in err.values()):
            raise ValueError("HOLD_MANUSCRIPT_RMSE_INVALID")
        expected=err["other_horses_context"]-err["own"]
        if abs(expected-cohort["other_minus_own_rmse_seconds"])>1e-12:
            raise ValueError("HOLD_MANUSCRIPT_GAIN_DOES_NOT_MATCH_SAME_ROW_RMSE")
    if not (a["other_minus_own_rmse_seconds"]>0
            and b["other_minus_own_rmse_seconds"]<0):
        raise ValueError("HOLD_STUDY_CONTEXTS_DO_NOT_SHOW_REPORTED_SIGN_CONTRAST")
    for key,total in (("year_forward_leave_one_horse",26),
                      ("year_forward_leave_one_future_date",10)):
        influence=b[key]
        if (influence["attempted"]!=total
            or influence["supported"]!=total
            or influence["own_better_count"]+influence["other_better_count"]!=total):
            raise ValueError("HOLD_INFLUENCE_COUNTS_NOT_RECONCILED")
        if not (influence["other_minus_own_min_seconds"] < 0
                < influence["other_minus_own_max_seconds"]):
            raise ValueError("HOLD_INFLUENCE_SIGN_REVERSAL_NOT_RETAINED")
    strict=b["strict_original_race_class_support"]
    if any(x["status"]!="HOLD" or x["horse_ids"]>=20 for x in strict.values()):
        raise ValueError("HOLD_CLASS_OR_200M_UNSUPPORTED_RESULT")
    return z


def svg_figure(evidence:dict)->str:
    """Two separated source cohort panels, same RMSE axis, not paired years."""
    panels=[
        (evidence["within_year_cannon"],"A  Within 2026",
         "Cannon Park | newly documented rider ID subset"),
        (evidence["year_forward_doomben"],"B  2025 → 2026",
         "Doomben | fixed 2025 history to held-out 2026"),
    ]
    out=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="725" viewBox="0 0 1200 725" role="img" aria-labelledby="title desc">',
        '<title id="title">Individual history predictive value differs between two source cohorts</title>',
        '<desc id="desc">RMSE of zero history, focal horse history and other-horse source context history, compared within—not between—Cannon Park and Doomben observational cohorts. Lower RMSE is better. These are not causal year effects.</desc>',
        '<rect width="1200" height="725" fill="#FFFFFF"/>',
        '<text x="44" y="46" font-family="Arial,sans-serif" font-size="24" font-weight="bold" fill="#202A32">Does individual history improve later early-GPS timing predictions?</text>',
        '<text x="44" y="75" font-family="Arial,sans-serif" font-size="15" fill="#58636C">Horse-equal-weighted RMSE (seconds); lower = better; each panel compares the same future observations</text>',
    ]
    colors=(("zero","No individual profile"),("own","Focal horse history"),
            ("other_horses_context","Other horses, same context"))
    for index,(data,heading,subtitle) in enumerate(panels):
        left=44+index*580
        top=115
        width=550
        plot_top=197
        plot_bottom=529
        base=plot_bottom-plot_top
        out.extend([
            f'<rect x="{left}" y="{top}" width="{width}" height="495" rx="10" fill="#FAFBFC" stroke="#D8DCE1"/>',
            f'<text x="{left+22}" y="{top+38}" font-family="Arial,sans-serif" font-size="21" font-weight="bold" fill="#28343D">{escape(heading)}</text>',
            f'<text x="{left+22}" y="{top+62}" font-family="Arial,sans-serif" font-size="14" fill="#58636C">{escape(subtitle)}</text>',
        ])
        for tick in (0.0,0.1,0.2,0.3,0.4):
            y=plot_bottom-tick/LIMIT*base
            out.append(f'<line x1="{left+50}" y1="{y:.1f}" x2="{left+527}" y2="{y:.1f}" stroke="#E0E5E9"/>')
            out.append(f'<text x="{left+42}" y="{y+5:.1f}" font-family="Arial,sans-serif" font-size="12" fill="#626D78" text-anchor="end">{tick:.1f}</text>')
        bars=data["rmse_seconds"]
        for bar_index,(key,caption) in enumerate(colors):
            center=left+132+bar_index*144
            value=bars[key]
            height=value/LIMIT*base
            y=plot_bottom-height
            out.append(f'<rect x="{center-31}" y="{y:.2f}" width="62" height="{height:.2f}" fill="{PALETTE[key]}"/>')
            out.append(f'<text x="{center}" y="{y-9:.2f}" text-anchor="middle" font-size="15" font-weight="bold" font-family="Arial,sans-serif" fill="#202A32">{value:.3f}</text>')
            words={"zero":["No horse","history"],"own":["Own horse","history"],"other_horses_context":["Other horses","history"]}[key]
            for subindex,word in enumerate(words):
                out.append(f'<text x="{center}" y="{plot_bottom+23+subindex*17}" text-anchor="middle" font-size="12" font-family="Arial,sans-serif" fill="#374550">{escape(word)}</text>')
        n=data["scored_distinct_original_horses"]
        nrows=data["scored_future_rows"]
        advantage=data["other_minus_own_rmse_seconds"]
        arrow="Own better" if advantage>0 else "Own worse"
        sign="+" if advantage>0 else "−"
        out.append(f'<text x="{left+24}" y="594" font-family="Arial,sans-serif" font-size="14" font-weight="bold" fill="#374550">{escape(arrow)} vs other: {sign}{abs(advantage):.3f} s  |  {n} horses, {nrows} later records</text>')
    out += [
        '<text x="44" y="640" font-family="Arial,sans-serif" font-size="14" font-weight="bold" fill="#26313A">Interpretation boundary</text>',
        '<text x="44" y="662" font-family="Arial,sans-serif" font-size="13" fill="#58636C">Different venues, years, animal populations, source Class and historical update rules; panels do NOT estimate temporal decay.</text>',
        '<text x="44" y="680" font-family="Arial,sans-serif" font-size="13" fill="#58636C">Doomben source had 38/42 locked dates available and only six Class-matched 150m year-shared horses (HOLD).</text>',
        '<text x="44" y="702" font-family="Arial,sans-serif" font-size="11" fill="#58636C">Source: Racing Queensland; archive runs 38563275612 and 38678720302. Aggregate-only; no original animal-level data.</text>',
        '</svg>',
    ]
    return "\n".join(out)+"\n"


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,default=EVIDENCE)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    z=checked_evidence(args.evidence)
    figure=svg_figure(z)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(figure,encoding="utf-8")
    print(json.dumps({
        "status":"AGGREGATE_ONLY_FIGURE_SUCCESS_NOT_CAUSAL_COMPARISON",
        "cannon_horses":z["within_year_cannon"]["scored_distinct_original_horses"],
        "doomben_horses":z["year_forward_doomben"]["scored_distinct_original_horses"],
        "not_a_test_of_year_effect":True,
    }))


if __name__=="__main__":
    main()
