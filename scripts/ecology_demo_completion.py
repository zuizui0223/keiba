#!/usr/bin/env python3
"""Generate an explicitly FAKE race panel with nonfinishers for H2 two-part QA.

Never uses actual animals, venues, official records, or downloadable data.
Completion status is ARTIFICIALLY censored for a subset of races.
"""
import argparse
import csv
from pathlib import Path

from ecology_demo_competitors import fabricate_competition
from ecology_h2_outcome_loss_stress import inject_nonfinishing
from ecology_panel import REQUIRED


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--days",type=int,default=100)
    p.add_argument("--horses",type=int,default=48)
    p.add_argument("--runners",type=int,default=12)
    p.add_argument("--seed",type=int,default=512)
    p.add_argument("--loss",choices=("random","speed_dependent"),default="random")
    args=p.parse_args()
    rows=fabricate_competition(args.days,args.horses,args.runners,args.seed,
                                interaction=-0.9)
    rows=inject_nonfinishing(rows,args.loss,seed=args.seed+31)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=list(REQUIRED)+["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)
    censored=sum(r["finish_status"]=="did_not_finish" for r in rows)
    print(f"FABRICATED ONLY; {len(rows)} invented starters and {censored} "
          f"artificial DNF statuses; {args.output}")


if __name__=="__main__":
    main()
