"""Fictional race results ONLY: time-aware JRA-2027 model coefficient trainer."""
from __future__ import annotations
from datetime import datetime,timedelta
from pathlib import Path
import json
import sys
import unittest
import copy

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2027_official_historical_train import (
    train, parse_licensed_panel, build_time_features, fit_ridge,
    required_support, cohort_scores, ALPHA, MIN_TRAIN, MIN_VAL,
    SPLIT_AT,
)
from ecology_japan_2027_point_in_time_ledger import (
    validate_models,OWN,KIN,linear_predict,JST_ZONE,
)

NOW=datetime(2026,11,18,11,30,tzinfo=JST_ZONE)
SOURCES={
    "historical_entries":"a"*64,
    "historical_results":"b"*64,
    "parent_master":"c"*64
}

def fictional_source():
    """40 train days 2023 and 20 2025 validation days, 42 horses.

    Future outcomes deliberately live in same historical result input; no
    code path may read them for previous training-race features.
    """
    parents=[]
    for i in range(42):
        parents.append({
            "horse_id":f"H:SYN{i:03d}",
            "sire_id":f"B:SYN_SIRE{i//6}",
            "dam_id":f"B:SYN_DAM{i}",
            "pedigree_master_known_at_jst":"2022-01-01T09:00:00+09:00",
        })
    entries=[]
    results=[]
    for era,year,month,n_days in (("train",2023,3,40),
                                  ("validation",2025,3,20)):
        base=datetime(year,month,1,15,15,tzinfo=JST_ZONE)
        for day in range(n_days):
            start=base+timedelta(days=day)
            entry_known=start-timedelta(days=1,hours=1)
            race=f"JRA:SYN{era}{day:04d}"
            course="TOKYO" if day%2 else "KYOTO"
            # 6 horses per race, 42 unique horses, repeat over days.
            members=[(day*6+j)%42 for j in range(6)]
            for j,i in enumerate(members):
                horse=f"H:SYN{i:03d}"
                horse_name_is_not_present=True
                entries.append({
                    "race_id":race,"horse_id":horse,
                    "race_start_at_jst":start.isoformat(),
                    "entry_known_at_jst":entry_known.isoformat(),
                    "course_id":course,
                    "surface":"turf" if day%2 else "dirt",
                    "distance_m":str(1600 if day%2 else 1800),
                    "sex":("M","F","G")[i%3],
                    "age":"5",
                    "jockey_id":f"J:SYN{i%9}",
                    "trainer_id":f"T:SYN{i//5}",
                })
                result= {
                    "race_id":race,"horse_id":horse,
                    "race_start_at_jst":start.isoformat(),
                    "result_known_at_jst":
                        (start+timedelta(hours=2)).isoformat(),
                    "finish_rank":str(1+((j+day)%6)),
                    "classified_field_size":"6",
                    "finish_status":"CLASSIFIED",
                    "surface":"turf" if day%2 else "dirt",
                    "distance_m":str(1600 if day%2 else 1800),
                    "course_id":course,
                    "jockey_id":f"J:SYN{i%9}",
                    "trainer_id":f"T:SYN{i//5}",
                }
                results.append(result)
    return entries,parents,results


class Pre2027TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries,cls.parents,cls.results=fictional_source()
        cls.model,cls.summary=train(
            cls.entries,cls.parents,cls.results,
            clock=NOW,source_sha=SOURCES
        )

    def test_fixed_jra_2027_ledger_model_contract(self):
        self.assertTrue(validate_models(
            self.model,NOW,datetime(2027,1,2,15,15,tzinfo=JST_ZONE)
        ))
        self.assertEqual(set(self.model["models"]),{"M1","M2"})
        self.assertEqual(len(self.model["models"]["M1"]["features"]),len(OWN))
        self.assertEqual(len(self.model["models"]["M2"]["features"]),len(OWN+KIN))
        self.assertEqual(self.summary["status"],
            "PRIVATE_OFFICIAL_ID_HISTORIC_M1_M2_MODEL_TRAINED_NOT_2027_PROSPECTIVE")
        self.assertTrue(self.summary["not_yet_2027_future_forecast"])

    def test_no_individual_identifiers_or_coefficients_in_public_summary(self):
        text=json.dumps(self.summary,ensure_ascii=False)
        self.assertNotIn("H:SYN",text)
        self.assertNotIn("B:SYN",text)
        self.assertNotIn("JRA:SYN",text)
        self.assertNotIn('"coefficient":',text)
        self.assertNotIn("private_horse_level_predictions",text)

    def test_public_model_digest_chains_to_private_coefficients(self):
        from ecology_japan_2027_point_in_time_ledger import (
            canonical_bytes,digest_bytes
        )
        self.assertEqual(
            self.summary["private_fitted_model_file_SHA256"],
            digest_bytes(canonical_bytes(self.model))
        )
        self.assertNotIn('"intercept":',json.dumps(self.summary))

    def test_historical_validation_one_way_uncertainty_is_source_scoped(self):
        v=self.summary["historical_scores"][
            "2025_2026_out_of_training_temporal_validation"]
        self.assertEqual(v["one_way_horse_cluster"]["bootstrap_draws"],399)
        self.assertEqual(v["one_way_race_day_cluster"]["bootstrap_draws"],399)
        self.assertEqual(v["one_way_race_day_cluster"]["cluster_count"],20)
        self.assertTrue(self.summary["methodology"][
            "one_way_validation_resampling_not_two_way_CI"])

    def test_validation_strata_use_pretarget_features_and_suppress_sparse(self):
        s=self.summary["pretarget_2025_2026_validation_strata"]
        self.assertEqual(s["status"],
           "PRETARGET_SOURCE_COVERAGE_CONDITIONAL_NOT_GENETIC_CAUSATION")
        groups=s["subgroups"]
        self.assertEqual(groups["no_documented_own_past"]["starts"]+
            groups["has_documented_own_past"]["starts"],120)
        self.assertEqual(groups["no_recorded_same_parent_peer"]["starts"]+
            groups["has_recorded_same_parent_peer"]["starts"],120)
        self.assertEqual(groups["both_parent_IDs_recorded"]["starts"]+
            groups["at_least_one_parent_ID_unrecorded"]["starts"],120)
        self.assertEqual(groups["no_documented_own_past"]["status"],
            "HOLD_SOURCE_COHORT_LOW_SUPPORT")
        self.assertIsNone(groups["no_documented_own_past"]["historical_scores"])
        self.assertTrue(s["no_documented_past_NOT_official_first_debut"])
        self.assertTrue(s["no_documented_family_peer_NOT_genetically_unrelated"])

    def test_validation_subgroups_include_no_source_family_without_imputation(self):
        parents=copy.deepcopy(self.parents)
        for p in parents:
            p["dam_id"]=""
            p["sire_id"]=""
        model,qa=train(self.entries,parents,self.results,
                       clock=NOW,source_sha=SOURCES)
        subs=qa["pretarget_2025_2026_validation_strata"]["subgroups"]
        self.assertEqual(subs["no_recorded_same_parent_peer"]["starts"],120)
        self.assertEqual(subs["has_recorded_same_parent_peer"]["starts"],0)
        self.assertEqual(subs["both_parent_IDs_recorded"]["starts"],0)
        self.assertIsNone(subs["has_recorded_same_parent_peer"]["historical_scores"])

    def test_temporal_split_and_pre2027_validation(self):
        t=self.summary["source_qa"]["training_support"]
        v=self.summary["source_qa"]["validation_support"]
        self.assertEqual(t["starts"],240)
        self.assertEqual(t["days"],40)
        self.assertEqual(v["starts"],120)
        self.assertEqual(v["days"],20)
        self.assertGreaterEqual(t["horses"],MIN_TRAIN[1])
        self.assertGreaterEqual(v["horses"],MIN_VAL[1])

    def test_same_own_feature_scalers_regardless_of_family(self):
        m=self.model["models"]
        for feature in OWN:
            self.assertEqual(
                m["M1"]["features"][feature]["mean"],
                m["M2"]["features"][feature]["mean"]
            )
            self.assertEqual(
                m["M1"]["features"][feature]["sd"],
                m["M2"]["features"][feature]["sd"]
            )

    def test_holdout_result_edits_do_not_retrain_model(self):
        modified=copy.deepcopy(self.results)
        # Swap validation ranks within one complete race. It must not affect
        # training features/coefs from 2023.
        x,y=240,241
        modified[x]["finish_rank"],modified[y]["finish_rank"] = (
            modified[y]["finish_rank"],modified[x]["finish_rank"]
        )
        alt,info=train(self.entries,self.parents,modified,
                       clock=NOW,source_sha=SOURCES)
        self.assertEqual(alt,self.model)

    def test_scoring_no_family_and_family_both_finite(self):
        score=self.summary["historical_scores"]
        for period,parts in score.items():
            for key in ("M0_midpoint","M1_own_context",
                        "M2_own_context_plus_family"):
                self.assertTrue(0<=parts[key]<1)
            self.assertAlmostEqual(parts["gain_M1_minus_M2"],
                parts["M1_own_context"]-parts["M2_own_context_plus_family"])

    def test_ridge_penalty_may_not_be_tuned_to_seen_validation(self):
        panel=parse_licensed_panel(self.entries,self.parents,self.results,
                                  clock=NOW)
        rows,_=build_time_features(panel)
        tr=[r for r in rows if r["start"]<SPLIT_AT]
        with self.assertRaisesRegex(ValueError,"UNFROZEN_RIDGE"):
            fit_ridge(tr,alpha=1.0)

    def test_later_known_parent_data_cannot_be_used(self):
        parent=copy.deepcopy(self.parents)
        parent[0]["pedigree_master_known_at_jst"]="2023-03-02T00:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"PEDIGREE_NOT_KNOWN"):
            train(self.entries,parent,self.results,clock=NOW,source_sha=SOURCES)

    def test_2027_future_race_result_cannot_be_input_to_fitter(self):
        result=copy.deepcopy(self.results)
        result[0]["result_known_at_jst"]="2027-01-09T16:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_PRE_RACE"):
            train(self.entries,self.parents,result,clock=NOW,source_sha=SOURCES)

    def test_results_cannot_be_published_before_race(self):
        results=copy.deepcopy(self.results)
        results[0]["result_known_at_jst"]="2023-03-01T14:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_PRE_RACE"):
            train(self.entries,self.parents,results,clock=NOW,source_sha=SOURCES)

    def test_conflicting_race_conditions_hold(self):
        results=copy.deepcopy(self.results)
        results[1]["surface"]="turf"
        with self.assertRaisesRegex(ValueError,"CONFLICTING_HISTORICAL_RACE"):
            train(self.entries,self.parents,results,clock=NOW,source_sha=SOURCES)

    def test_one_race_cannot_mix_different_entry_knownon_cutoffs(self):
        entries=copy.deepcopy(self.entries)
        # Entry for the second runner is not from the same certified
        # pre-race information snapshot as the first runner.
        e=entries[1]
        when=datetime.fromisoformat(e["entry_known_at_jst"])
        e["entry_known_at_jst"]=(when-timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(ValueError,
                "INCONSISTENT_ENTERED_RACE_CONDITIONS_OR_CUTOFF"):
            train(entries,self.parents,self.results,
                  clock=NOW,source_sha=SOURCES)

    def test_rider_replacement_after_entry_is_quarantined_whole_race(self):
        results=copy.deepcopy(self.results)
        results[0]["jockey_id"]="J:SYN_REPLACEMENT_AFTER_ENTRY"
        model,info=train(self.entries,self.parents,results,
                         clock=NOW,source_sha=SOURCES)
        self.assertEqual(info["source_qa"]["training_support"]["starts"],234)
        self.assertEqual(info["source_qa"]["training_target_races"][
            "changed_rider_or_trainer_after_entry"],1)

    def test_trainer_record_conflict_excludes_full_race(self):
        results=copy.deepcopy(self.results)
        results[0]["trainer_id"]="T:SYN_CHANGED_AFTER_ENTRY"
        model,info=train(self.entries,self.parents,results,
                         clock=NOW,source_sha=SOURCES)
        self.assertEqual(info["source_qa"]["training_support"]["starts"],234)
        self.assertEqual(info["source_qa"]["training_target_races"][
            "changed_rider_or_trainer_after_entry"],1)

    def test_duplicate_race_horse_hold(self):
        results=copy.deepcopy(self.results)
        results.append(copy.deepcopy(results[0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OFFICIAL_HISTORICAL"):
            train(self.entries,self.parents,results,clock=NOW,source_sha=SOURCES)

    def test_incomplete_finish_rank_quarantined_not_used_as_target(self):
        results=copy.deepcopy(self.results)
        results[0]["finish_status"]="DNF"
        results[0]["finish_rank"]=""
        model,info=train(self.entries,self.parents,results,
                         clock=NOW,source_sha=SOURCES)
        self.assertEqual(info["source_qa"]["training_support"]["starts"],234)
        self.assertEqual(info["source_qa"]["quarantined_historical_races"][
            "incomplete_tied_dnf_or_invalid_race"],1)

    def test_unmatched_training_runner_rejects_whole_race(self):
        entries=copy.deepcopy(self.entries)
        del entries[0]
        model,info=train(entries,self.parents,self.results,
                         clock=NOW,source_sha=SOURCES)
        self.assertEqual(info["source_qa"]["training_support"]["starts"],234)
        self.assertGreater(info["source_qa"]["training_target_races"][
            "incomplete_entry_result_or_DNF"],0)

    def test_histories_are_strictly_known_before_own_entry(self):
        panel=parse_licensed_panel(self.entries,self.parents,self.results,
                                  clock=NOW)
        rows,_=build_time_features(panel)
        first=next(r for r in rows if r["start"].year==2023)
        self.assertAlmostEqual(first["features"]["own_mean"],0.5)
        # History of target race is in the source file but never in own feature.
        self.assertEqual(first["features"]["log_own_count"],0.0)

    def test_privately_trained_coefficients_reach_2027_freeze_and_later_score(self):
        # End-to-end from synthetic historical official-ID panel to the very
        # same 2027 future forecast ledger, with zero actual JRA data.
        from ecology_japan_2027_point_in_time_ledger import (
            freeze,score,canonical_bytes,digest_bytes
        )
        forecast_start=datetime(2027,1,9,15,15,tzinfo=JST_ZONE)
        asof=datetime(2027,1,8,19,0,tzinfo=JST_ZONE)
        actual_freeze=datetime(2027,1,8,20,0,tzinfo=JST_ZONE)
        allowed=[]
        for i in range(3):
            horse=f"H:SYN{i:03d}"
            allowed.append({
                "race_id":"JRA:SYN20270109","horse_id":horse,
                "race_start_at_jst":forecast_start.isoformat(),
                "entry_known_at_jst":"2027-01-08T18:00:00+09:00",
                "course_id":"KYOTO","surface":"dirt",
                "distance_m":"1800","sex":("M","F","G")[i],
                "age":"6","jockey_id":f"J:SYN{i%9}",
                "trainer_id":f"T:SYN{i//5}",
            })
        from ecology_japan_2027_point_in_time_ledger import HISTORICAL_INPUT
        pr,commit=freeze(allowed,self.parents,self.results,self.model,
                         asof=asof,clock=actual_freeze,
                         source_sha={**SOURCES,
                           "model":digest_bytes(canonical_bytes(self.model))})
        self.assertEqual(commit["starts"],3)
        self.assertEqual(commit["input_SHA256"]["model"],
                         self.summary["private_fitted_model_file_SHA256"])
        self.assertNotIn("H:SYN",json.dumps(commit))
        after=[]
        for rank,horse in enumerate(("H:SYN000","H:SYN001","H:SYN002"),start=1):
            after.append({
                "race_id":"JRA:SYN20270109","horse_id":horse,
                "race_start_at_jst":forecast_start.isoformat(),
                "result_known_at_jst":"2027-01-09T17:00:00+09:00",
                "finish_rank":str(rank), "classified_field_size":"3",
                "finish_status":"CLASSIFIED",
            })
        scored=score(pr,commit,after)
        self.assertEqual(scored["status"],"HOLD_2027_AGGREGATE_LOW_SUPPORT")
        self.assertEqual(scored["starts_scored"],3)
        self.assertIn("gain_M1_minus_M2",scored)
        self.assertFalse(scored["conditional_operational_gain"])
        self.assertNotIn("H:SYN",json.dumps(scored))

    def test_no_2027_future_model_pretense_from_fake_data(self):
        self.assertFalse(self.summary["methodology"]["target_2027_outcomes_used"])
        self.assertFalse(self.summary["methodology"]["genetic_causality_estimated"])
        self.assertTrue(self.summary[
            "provider_rights_and_ID_authenticity_require_external_verification"])


if __name__=="__main__":
    unittest.main()
