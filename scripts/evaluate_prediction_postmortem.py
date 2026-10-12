#!/usr/bin/env python3
"""Evaluate frozen pre-race marks and saved wide candidates against official results.

This is a post-race scoring utility. It does not fetch results, alter marks, or
make betting recommendations.
"""
import argparse
import json
from pathlib import Path

CORE_MARKS = {"◎", "○", "▲"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_race(race, result):
    positions = result["positions"]
    marks = {h["number"]: h.get("mark", "") for h in race["horses"]}
    candidate_set = {h["number"] for h in race["horses"] if h.get("mark")}
    core_set = {h["number"] for h in race["horses"] if h.get("mark") in CORE_MARKS}

    winner = positions[0]
    top2 = positions[:2]
    top3 = positions[:3]

    ticket_rows = []
    for ticket in race.get("tickets", []):
        if ticket.get("type") != "wide":
            continue
        pair = set(ticket["horses"])
        # If both horses are already confirmed in the known positions, the wide
        # is definitely a hit. For partial results, this is conservative and
        # never infers an unknown third-place horse.
        hit_confirmed = pair.issubset(set(positions))
        ticket_rows.append({
            "horses": sorted(ticket["horses"]),
            "priority": bool(ticket.get("priority", False)),
            "hit_confirmed": hit_confirmed,
        })

    return {
        "race": race["race"],
        "official_positions_available": positions,
        "complete_top3": bool(result.get("complete_top3", False)),
        "winner_mark": marks.get(winner, ""),
        "winner_in_core_marks": winner in core_set,
        "top2_both_in_core_marks": len(top2) == 2 and all(h in core_set for h in top2),
        "candidate_recall_available": {
            "hits": sum(h in candidate_set for h in positions),
            "denominator": len(positions),
        },
        "top3_candidate_recall": (
            sum(h in candidate_set for h in top3) / 3
            if result.get("complete_top3", False) and len(top3) == 3
            else None
        ),
        "saved_wide_candidates": ticket_rows,
        "any_saved_wide_hit_confirmed": any(t["hit_confirmed"] for t in ticket_rows),
        "any_priority_wide_hit_confirmed": any(
            t["priority"] and t["hit_confirmed"] for t in ticket_rows
        ),
        "source_url": result["source_url"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/2026-10-12")
    parser.add_argument(
        "--results", default="data/2026-10-12/official-results-partial.json"
    )
    parser.add_argument(
        "--output", default="reports/2026-10-12/prediction-evaluation.json"
    )
    args = parser.parse_args()

    result_data = load_json(args.results)
    rows = []
    for race_no, result in sorted(result_data["races"].items(), key=lambda x: int(x[0])):
        race = load_json(Path(args.data_dir) / f"kyoto_{int(race_no):02d}.json")
        rows.append(evaluate_race(race, result))

    summary = {
        "races_scored": len(rows),
        "winner_in_core_count": sum(r["winner_in_core_marks"] for r in rows),
        "winner_in_core_rate": (
            sum(r["winner_in_core_marks"] for r in rows) / len(rows) if rows else None
        ),
        "top2_both_in_core_count": sum(r["top2_both_in_core_marks"] for r in rows),
        "complete_top3_races": sum(r["complete_top3"] for r in rows),
        "complete_top3_all_candidates_count": sum(
            r["complete_top3"] and r["top3_candidate_recall"] == 1.0 for r in rows
        ),
        "any_saved_wide_hit_count": sum(r["any_saved_wide_hit_confirmed"] for r in rows),
        "rows": rows,
        "interpretation": (
            "Horse candidate extraction and ticket selection are scored separately. "
            "No post-result mark changes are allowed."
        ),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
