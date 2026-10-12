"""Synthetic Kaggle-shaped race and run files: compatibility only, no rights claims."""
import csv
from datetime import date,timedelta
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_hk_preflight import preflight,load_csv,RACE_COLUMNS,RUN_COLUMNS


def make_kaggle_shaped(path:Path,n_races=12):
    races=[]; runs=[]
    for j in range(n_races):
        rid=f"OBFUSCATED-RACE-{j:03}"
        d=date(2000,1,1)+timedelta(days=j)
        races.append({
            "race_id":rid,"date":d.isoformat(),"venue":"ST",
            "surface":"0","distance":"1600",
            "going":"GOOD" if j%2==0 else "YIELDING",
            "race_class":"3",
        })
        # Changing rivals; animal-1 enters every date, rest rotate.
        ids=["horse_1"] + [f"horse_{((j+k)%6)+2}"
                             for k in range(3)]
        for rank,h in enumerate(ids,1):
            runs.append({
                "race_id":rid,"horse_id":h,"result":str(rank),
                "finish_time":str(100+rank+j/10),
                "position_sec1":str(rank),"jockey_id":f"jockey_{rank}"
            })
    def write(name,records,columns):
        f=path/name
        with f.open("w",encoding="utf-8",newline="") as fd:
            w=csv.DictWriter(fd,fieldnames=columns)
            w.writeheader();w.writerows(records)
        return f
    return write("races.csv",races,sorted(RACE_COLUMNS)),\
           write("runs.csv",runs,sorted(RUN_COLUMNS))


class HKPreflightTests(unittest.TestCase):
    def test_longitudinal_ids_exist_but_timeline_and_rights_remain_hold(self):
        with tempfile.TemporaryDirectory() as temp:
            races,runs=make_kaggle_shaped(Path(temp))
            report=preflight(races,runs)
        c=report["counts"]
        self.assertEqual(report["status"],"HOLD_SOURCE_RIGHTS_AND_OBSCURED_DATES")
        self.assertEqual(c["race_rows"],12)
        self.assertEqual(c["valid_matched_horse_starts"],48)
        self.assertEqual(c["unique_horses_in_matched_runs"],7)
        self.assertGreater(c["horses_with_4plus_starts_and_2plus_distinct_opponent_sets"],0)
        self.assertGreater(c["horse_start_rows_with_3plus_prior_early_positions"],0)
        self.assertFalse(report["real_race_dates_verified"])
        self.assertFalse(report["upstream_source_rights_verified"])
        self.assertFalse(report["generated_model_panel"])
        self.assertTrue(report["no_automatic_going_ordinal_map"])
        self.assertEqual(report["raw_going_label_race_counts"]["YIELDING"],6)

    def test_stratified_going_overlap_not_inferred_from_confounding_classes(self):
        with tempfile.TemporaryDirectory() as temp:
            races,runs=make_kaggle_shaped(Path(temp))
            with races.open(encoding="utf-8",newline="") as fd:
                rec=list(csv.DictReader(fd))
            # Every "GOOD" race is class 3; every "YIELDING" is class 4.
            # The horses see both conditions *globally*, but never within
            # the same class and therefore have no estimable within-stratum
            # going comparison.
            for row in rec:
                row["race_class"]="3" if row["going"]=="GOOD" else "4"
            with races.open("w",encoding="utf-8",newline="") as fd:
                writer=csv.DictWriter(fd,fieldnames=sorted(RACE_COLUMNS))
                writer.writeheader();writer.writerows(rec)
            report=preflight(races,runs)
        counts=report["counts"]
        self.assertGreater(counts["horses_with_2plus_distinct_raw_going_labels"],0)
        self.assertEqual(
            counts["horses_with_environment_overlap_within_same_venue_surface_distance_class"],0)
        self.assertNotIn(
            "horse_by_stratum_both_environment_and_rival_overlap",
            counts["stratified_support"])

    def test_same_obscured_date_starts_are_flagged_not_assumed_ordered(self):
        with tempfile.TemporaryDirectory() as temp:
            races,runs=make_kaggle_shaped(Path(temp))
            with races.open(encoding="utf-8",newline="") as fd:
                rec=list(csv.DictReader(fd))
            rec[1]["date"]=rec[0]["date"]
            with races.open("w",encoding="utf-8",newline="") as fd:
                writer=csv.DictWriter(fd,fieldnames=sorted(RACE_COLUMNS))
                writer.writeheader();writer.writerows(rec)
            report=preflight(races,runs)
        self.assertGreater(report["counts"]["horse_races_sharing_same_obscured_date"],0)
        self.assertFalse(report["real_race_dates_verified"])
        self.assertFalse(report["race_start_time_known"])

    def test_missing_finish_times_not_zero_imputed(self):
        with tempfile.TemporaryDirectory() as temp:
            races,runs=make_kaggle_shaped(Path(temp))
            with runs.open(encoding="utf-8",newline="") as fd:
                records=list(csv.DictReader(fd))
            records[0]["finish_time"]=""
            records[2]["finish_time"]="DNF"
            with runs.open("w",encoding="utf-8",newline="") as fd:
                writer=csv.DictWriter(fd,fieldnames=sorted(RUN_COLUMNS))
                writer.writeheader();writer.writerows(records)
            report=preflight(races,runs)
        self.assertEqual(report["counts"]["run_rows_with_unavailable_finish_time"],2)
        self.assertEqual(report["counts"]["timed_run_rows"],46)

    def test_orphan_run_reported_but_not_mistaken_as_matched_race(self):
        with tempfile.TemporaryDirectory() as temp:
            races,runs=make_kaggle_shaped(Path(temp))
            with runs.open(encoding="utf-8",newline="") as fd:
                records=list(csv.DictReader(fd))
            records.append({**records[0],
                            "race_id":"not_in_races",
                            "horse_id":"orphan_horse"})
            with runs.open("w",encoding="utf-8",newline="") as fd:
                writer=csv.DictWriter(fd,fieldnames=sorted(RUN_COLUMNS))
                writer.writeheader();writer.writerows(records)
            report=preflight(races,runs)
        self.assertEqual(report["counts"]["unmatched_run_rows"],1)
        self.assertEqual(report["counts"]["valid_matched_horse_starts"],48)

    def test_duplicate_runner_key_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            races,runs=make_kaggle_shaped(Path(temp))
            with runs.open(encoding="utf-8",newline="") as fd:
                records=list(csv.DictReader(fd))
            records.append(records[0].copy())
            with runs.open("w",encoding="utf-8",newline="") as fd:
                writer=csv.DictWriter(fd,fieldnames=sorted(RUN_COLUMNS))
                writer.writeheader();writer.writerows(records)
            with self.assertRaisesRegex(ValueError,"duplicate horse_id"):
                preflight(races,runs)


if __name__=="__main__":
    unittest.main()
