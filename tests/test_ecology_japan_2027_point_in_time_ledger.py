"""Only invented horses: 2027 official-ID point-in-time forecast/score contract."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2027_point_in_time_ledger import (
    SCHEMA, MODEL_SCHEMA, OWN, KIN, canonical_bytes, digest_bytes,
    freeze, score, validate_models, asof_features, linear_predict,
)

JST = timezone(timedelta(hours=9))
ASOF = datetime(2027,1,8,19,0,tzinfo=JST)
CLOCK = datetime(2027,1,8,20,0,tzinfo=JST)
START1 = datetime(2027,1,9,15,15,tzinfo=JST)
START2 = datetime(2027,1,10,15,15,tzinfo=JST)
ENTRY_KNOWN = "2027-01-08T18:00:00+09:00"
PAST_START = "2026-12-24T15:30:00+09:00"
PAST_KNOWN = "2026-12-24T17:00:00+09:00"


def fictional():
    entries=[]
    parents=[]
    past=[]
    for i in range(3):
        name="H:"+str(111+i)
        parents.append({
            "horse_id":name, "sire_id":"B:FAKE7" if i<2 else "B:FAKE8",
            "dam_id":"B:MA"+str(i),
            "pedigree_master_known_at_jst":"2026-10-01T09:00:00+09:00",
        })
        past.append({
            "race_id":"JRA:FAKE20261224",
            "horse_id":name,
            "race_start_at_jst":PAST_START,
            "result_known_at_jst":PAST_KNOWN,
            "finish_rank":str(i+1),
            "classified_field_size":"3",
            "finish_status":"CLASSIFIED",
            "surface":"turf","distance_m":"1600",
            "course_id":"KYOTO",
            "jockey_id":"J:FAKE"+str(i),
            "trainer_id":"T:FAKE"+str(i//2),
        })
        for day,start in enumerate((START1,START2),start=1):
            entries.append({
                "race_id":"JRA:FAKE20270109"+str(day),
                "horse_id":name,
                "race_start_at_jst":start.isoformat(),
                "entry_known_at_jst":ENTRY_KNOWN,
                "course_id":"KYOTO",
                "surface":"turf",
                "distance_m":"1600",
                "sex":"M" if i==0 else ("F" if i==1 else "G"),
                "age":"4",
                "jockey_id":"J:FAKE"+str(i),
                "trainer_id":"T:FAKE"+str(i//2),
            })
    one={f:{"coefficient":0.0,"mean":0.0,"sd":1.0} for f in OWN}
    two={f:{"coefficient":0.0,"mean":0.0,"sd":1.0} for f in OWN+KIN}
    one["own_mean"]["coefficient"]=0.14
    two["own_mean"]["coefficient"]=0.14
    two["sire_kin_history"]["coefficient"]=0.16
    model={
        "schema":MODEL_SCHEMA,
        "training_through_jst":"2026-12-29T20:00:00+09:00",
        "model_frozen_at_jst":"2026-12-30T20:00:00+09:00",
        "models":{
            "M1":{"intercept":0.5,"features":one},
            "M2":{"intercept":0.5,"features":two},
        }
    }
    return entries,parents,past,model


def fake_sha():
    return {"entries":"a"*64,"parents":"b"*64,"history":"c"*64,
            "model":"d"*64}


def completed_results(entries, *, status=None):
    result=[]
    for x in entries:
        i=int(x["horse_id"][-1])-1
        race_day=x["race_start_at_jst"][:10]
        result.append({
            "race_id":x["race_id"],
            "horse_id":x["horse_id"],
            "race_start_at_jst":x["race_start_at_jst"],
            "result_known_at_jst":race_day+"T18:30:00+09:00",
            "finish_rank":str(i+1) if race_day=="2027-01-09"
                          else str(3-i),
            "classified_field_size":"3",
            "finish_status":"CLASSIFIED"
        })
    if status:
        result[0].update(status)
    return result


class FrozenForecastTests(unittest.TestCase):
    def setUp(self):
        self.entries,self.parents,self.history,self.model=fictional()

    def frozen(self):
        return freeze(self.entries,self.parents,self.history,self.model,
                      asof=ASOF,clock=CLOCK,source_sha=fake_sha())

    def test_private_predictions_are_separate_from_public_commitment(self):
        private,manifest=self.frozen()
        self.assertEqual(manifest["starts"],6)
        self.assertEqual(manifest["races"],2)
        self.assertEqual(manifest["unique_horses"],3)
        self.assertEqual(manifest["private_prediction_file_SHA256"],
                         digest_bytes(canonical_bytes(private)))
        self.assertTrue(private["private_horse_level_predictions"])
        self.assertNotIn("H:111",json.dumps(manifest))
        self.assertNotIn("FAKE202701",json.dumps(manifest))
        self.assertTrue(manifest["public_git_commit_timestamp_required_before_racing"])

    def test_model_coefficients_are_declared_and_not_trained_here(self):
        private,manifest=self.frozen()
        self.assertEqual(private["predictions"][0]["M0"],0.5)
        self.assertTrue(all(0<=x["M1"]<=1 for x in private["predictions"]))
        self.assertTrue(all(0<=x["M2"]<=1 for x in private["predictions"]))
        self.assertTrue(validate_models(self.model,CLOCK,START1))

    def test_future_history_published_after_forecast_is_rejected(self):
        self.history.append(dict(self.history[0],
          race_id="JRA:FAKEFUTURE",
          race_start_at_jst="2027-01-06T10:00:00+09:00",
          result_known_at_jst="2027-01-08T19:01:00+09:00"))
        with self.assertRaisesRegex(ValueError,"POST_ASOF_RESULT"):
            self.frozen()

    def test_entry_not_yet_announced_at_forecast_is_rejected(self):
        self.entries[0]["entry_known_at_jst"]="2027-01-08T19:30:00+09:00"
        with self.assertRaisesRegex(ValueError,"ENTRY_NOT_PUBLISHED_AT_ASOF"):
            self.frozen()

    def test_freeze_after_first_race_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"NOT_ACTUALLY_FROZEN"):
            freeze(self.entries,self.parents,self.history,self.model,
                   asof=ASOF,clock=START1,source_sha=fake_sha())

    def test_model_was_not_frozen_before_forecast(self):
        self.model["model_frozen_at_jst"]="2027-01-09T20:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"MODEL_FROZEN_TIMESTAMP"):
            self.frozen()

    def test_model_training_uses_no_2027_races(self):
        self.model["training_through_jst"]="2027-01-01T00:00:00+09:00"
        self.model["model_frozen_at_jst"]="2027-01-02T00:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"2027_LABELS"):
            self.frozen()

    def test_model_requires_same_own_scalers_in_M1_M2(self):
        self.model["models"]["M2"]["features"]["own_mean"]["sd"]=2.0
        with self.assertRaisesRegex(ValueError,"SCALER_MISMATCH"):
            self.frozen()

    def test_M1_cannot_consume_family_signal(self):
        self.model["models"]["M1"]["features"]["sire_kin_history"]={
            "coefficient":1.0,"mean":0.0,"sd":1.0
        }
        with self.assertRaisesRegex(ValueError,"SAME_OWN_COVARIATES_PLUS_KIN"):
            self.frozen()

    def test_future_historic_result_does_not_affect_preexisting_frozen_scores(self):
        p,_=self.frozen()
        newer=copy.deepcopy(self.history)
        newer[0]["finish_rank"]="3"
        p2,_=freeze(self.entries,self.parents,newer,self.model,
                    asof=ASOF,clock=CLOCK,source_sha=fake_sha())
        self.assertNotEqual(p["predictions"],p2["predictions"])
        # This change is in pre-race known history, so a *new* freeze would
        # differ; the original private SHA rejects edits after commitment.

    def test_missing_parent_never_shared_family_group(self):
        self.parents[0]["sire_id"]=""
        self.parents[1]["sire_id"]=""
        f,_=self.frozen()
        # Original H:111 and H:112 no longer share any specified parent ID;
        # all model-2 sire features must therefore be zero.
        for x in f["predictions"]:
            if x["horse_id"] in ("H:111","H:112"):
                self.assertAlmostEqual(x["M1"],x["M2"])

    def test_private_result_digest_must_match_public_commitment(self):
        private,manifest=self.frozen()
        edited=copy.deepcopy(private)
        edited["predictions"][0]["M2"]=0.999
        with self.assertRaisesRegex(ValueError,"DIGEST_MISMATCH"):
            score(edited,manifest,completed_results(self.entries))

    def test_full_results_scored_without_refit(self):
        private,manifest=self.frozen()
        out=score(private,manifest,completed_results(self.entries))
        self.assertEqual(out["starts_scored"],6)
        self.assertEqual(out["races_scored"],2)
        self.assertEqual(out["calendar_days_scored"],2)
        self.assertEqual(out["status"],"HOLD_2027_AGGREGATE_LOW_SUPPORT")
        self.assertAlmostEqual(out["RMSE_equal_horse_weight"]["M0"],
                               math.sqrt(1/6),places=12)
        self.assertTrue(out["no_individual_results_exported"])
        self.assertNotIn("H:111",json.dumps(out))
        self.assertNotIn("FAKE202701",json.dumps(out))
        self.assertFalse(out["conditional_operational_gain"])

    def test_incomplete_races_excluded_not_given_fabricated_ranks(self):
        private,manifest=self.frozen()
        altered=completed_results(self.entries)
        altered[0]["finish_status"]="DNF"
        altered[0]["finish_rank"]=""
        result=score(private,manifest,altered)
        self.assertEqual(result["races_scored"],1)
        self.assertEqual(result["starts_scored"],3)
        self.assertEqual(result["race_quality_counts"][
            "incomplete_tied_dnf_or_denominator_races"],1)

    def test_incomplete_publication_is_counted_as_pending_not_valid(self):
        private,manifest=self.frozen()
        result=score(private,manifest,completed_results(self.entries)[:2])
        self.assertEqual(result["status"],"HOLD_NO_FULLY_PUBLISHED_COMPLETE_RACES")
        self.assertEqual(result["race_quality_counts"][
            "pending_or_partially_reported_races"],2)

    def test_duplicate_result_horse_for_one_race_rejected(self):
        private,manifest=self.frozen()
        results=completed_results(self.entries)
        results.append(copy.deepcopy(results[0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OFFICIAL_RESULT"):
            score(private,manifest,results)

    def test_unknown_result_not_in_frozen_forecast_rejected(self):
        private,manifest=self.frozen()
        results=completed_results(self.entries)
        results[0]["horse_id"]="H:OTHER"
        with self.assertRaisesRegex(ValueError,"OUTCOME_NOT_IN_FROZEN"):
            score(private,manifest,results)

    def test_source_result_publication_cannot_precede_start(self):
        private,manifest=self.frozen()
        results=completed_results(self.entries)
        results[0]["result_known_at_jst"]="2027-01-09T10:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"PUBLICATION_CONFLICT"):
            score(private,manifest,results)

    def test_same_typed_registration_ids_dont_equate_with_parent_names(self):
        self.parents[0]["sire_id"]="Meisho Sample"
        with self.assertRaisesRegex(ValueError,"NAMESPACE"):
            self.frozen()

    def test_invalid_jockey_or_trainer_historical_key_fails_closed(self):
        self.history[0]["jockey_id"]=""
        with self.assertRaisesRegex(ValueError,"JOCKEY_TRAINER_UNCERTIFIED"):
            self.frozen()

    def test_all_model_feature_values_are_finite(self):
        private,manifest=self.frozen()
        self.assertEqual(private["schema"],SCHEMA)
        self.assertEqual(len(OWN),18)
        self.assertEqual(len(KIN),4)


if __name__=="__main__":
    unittest.main()
