#!/usr/bin/env python3
"""Synthetic local market freeze integrity, result isolation and as-of clocks."""
from copy import deepcopy
import json
from pathlib import Path
import math
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from odds_shadow_freeze_score import (
    SOURCE_SCHEMA, FREEZE_SCHEMA, OFFICIAL_SCHEMA,
    STATUS_SHADOW, SCORING_STATUS,
    build_freeze, score_sealed, verify_seal, synthetic_demo,
    _seal, _canonical, _validate_snapshot,
)


class ShadowMarketFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.observed = synthetic_demo()
        cls.frozen = build_freeze(cls.source)
        cls.scored = score_sealed(cls.frozen, cls.observed)

    def test_local_freeze_has_no_actual_podium_or_raw_odds(self):
        doc=self.frozen
        payload=verify_seal(doc)
        self.assertEqual(payload["schema"],FREEZE_SCHEMA)
        self.assertEqual(payload["status"],STATUS_SHADOW)
        self.assertEqual(payload["source_provenance"],"synthetic")
        self.assertEqual(payload["horse_count"],8)
        self.assertTrue(payload["no_actual_result_loaded"])
        self.assertTrue(payload["v31_frozen_holdout_untouched"])
        self.assertTrue(payload["all_price_features_available_before_freeze"])
        self.assertEqual(
            payload["confidence_attestation"],
            "LOCAL_TIME_AND_SHA_ONLY_NOT_TRUSTED_REMOTE_PROOF")
        self.assertNotIn("odds_by_horse_number",str(payload))
        self.assertNotIn("synthetic_top3",str(payload))
        self.assertNotIn("top3_horse_numbers",str(payload))
        self.assertNotIn("actual_top3",str(payload))

    def test_seal_is_deterministic_and_catches_modified_probability(self):
        self.assertEqual(self.frozen,build_freeze(self.source))
        self.assertEqual(len(self.frozen["seal_sha256_of_canonical_payload"]),64)
        modified=deepcopy(self.frozen)
        modified["payload"]["predicted_probabilities"]["win_PL_baseline"][
            "win"][0]["p"]+=.002
        with self.assertRaisesRegex(ValueError,"HOLD_FREEZE_DIGEST"):
            verify_seal(modified)
        with self.assertRaisesRegex(ValueError,"HOLD_FREEZE_DIGEST"):
            score_sealed(modified,self.observed)

    def test_real_score_is_never_formally_prospective_without_external_proof(self):
        x=self.scored
        self.assertEqual(x["status"],SCORING_STATUS)
        self.assertEqual(set(x["frozen_models_scores"]),{
            "win_PL_baseline","predeclared_hierarchy"})
        self.assertEqual(set(x["preselected_hierarchy_minus_PL_lower_is_better"]),{
            "win_categorical_log_loss","top3_binary_brier_mean_horse",
            "trio_categorical_log_loss"})
        self.assertEqual(
            x["formal_prospective_status"],
            "HOLD_INDEPENDENT_REMOTE_PRESTART_TIMESTAMP_ATTESTATION_NOT_VERIFIED")
        self.assertTrue(x["cannot_append_to_frozen_v31_formal_ledger"])
        self.assertTrue(x["unverified_local_clock_not_external_evidence"])
        self.assertEqual(x["actual_top3_horse_numbers"],[2,5,1])

    def test_joint_win_top3_trio_marginals_exact(self):
        d=self.frozen["payload"]["predicted_probabilities"]
        self.assertEqual(len(d),2)
        for pred in d.values():
            win={v["n"]:v["p"] for v in pred["win"]}
            place={v["n"]:v["p"] for v in pred["top3"]}
            trio={tuple(v["numbers"]):v["p"] for v in pred["trio"]}
            self.assertEqual(len(win),8)
            self.assertEqual(len(trio),56)
            self.assertAlmostEqual(sum(win.values()),1,places=10)
            self.assertAlmostEqual(sum(place.values()),3,places=10)
            self.assertAlmostEqual(sum(trio.values()),1,places=10)
            for n in win:
                self.assertLessEqual(win[n],place[n])
                self.assertAlmostEqual(
                    place[n],sum(v for k,v in trio.items() if n in k),places=10)
        self.assertTrue(all(math.isfinite(v) for v in
                            self.scored["preselected_hierarchy_minus_PL_lower_is_better"].values()))

    def test_postrace_actual_results_change_scores_never_frozen_probs(self):
        freeze=deepcopy(self.frozen)
        other=deepcopy(self.observed)
        other["top3_horse_numbers"]=[8,2,6]
        x=score_sealed(freeze,other)
        self.assertEqual(freeze,self.frozen)
        self.assertNotEqual(
            self.scored["frozen_models_scores"]["win_PL_baseline"][
                "win_categorical_log_loss"],
            x["frozen_models_scores"]["win_PL_baseline"][
                "win_categorical_log_loss"])
        self.assertEqual(
            self.scored["freeze_payload_sha256"],
            x["freeze_payload_sha256"])

    def test_future_official_result_verified_at_must_be_after_start(self):
        fake=deepcopy(self.observed)
        fake["independently_verified_at_jst"]="2030-01-01T13:59:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_PRESTART"):
            score_sealed(self.frozen,fake)
        fake=deepcopy(self.observed)
        fake["independently_verified_at_jst"]="2030-01-01T15:00"
        with self.assertRaisesRegex(ValueError,"HOLD_NAIVE_CLOCK"):
            score_sealed(self.frozen,fake)

    def test_models_must_have_been_locked_before_price_was_published(self):
        source=deepcopy(self.source)
        source["coefficient_lock_at_jst"]="2030-01-01T13:30:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EARLY_ENOUGH"):
            build_freeze(source)
        source=deepcopy(self.source)
        source["prediction_recorded_at_jst"]="2030-01-01T13:55:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EARLY_ENOUGH"):
            build_freeze(source)
        source=deepcopy(self.source)
        source["trained_last_official_result_verified_at_jst"]=(
            "2030-01-01T13:00:00+09:00")
        with self.assertRaisesRegex(ValueError,"HOLD_TRAINING_RESULT_KNOWN_AFTER"):
            build_freeze(source)

    def test_source_page_updates_have_to_be_aligned(self):
        altered=deepcopy(self.source)
        altered["wide"]["source_updated_at_jst"]="2030-01-01T13:28:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EARLY_ENOUGH"):
            build_freeze(altered)
        altered=deepcopy(self.source)
        altered["win"]["received_at_jst"]="2030-01-01T13:28:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_MARKET_PUBLISHED_AFTER_RECEIPT"):
            build_freeze(altered)

    def test_raw_source_rights_self_attestation_not_legal_proof(self):
        altered=deepcopy(self.source)
        altered["provenance"]="authorized_local_normalized_market"
        with self.assertRaisesRegex(ValueError,"HOLD_LOCAL_RESEARCH_RIGHTS"):
            build_freeze(altered)
        altered["operator_confirmed_research_rights"]=True
        a=build_freeze(altered)
        self.assertEqual(a["payload"]["source_provenance"],
                         "authorized_local_normalized_market")
        self.assertIn("LOCAL_",a["payload"]["confidence_attestation"])
        altered["raw_provider_rows_redistributable"]=True
        with self.assertRaisesRegex(ValueError,"HOLD_PUBLIC_RAW_ODDS"):
            build_freeze(altered)

    def test_bad_source_roster_and_pairs_fails_closed(self):
        s=deepcopy(self.source)
        s["wide"]["pairs"].pop()
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_ALL_PAIRS"):
            build_freeze(s)
        s=deepcopy(self.source)
        s["win"]["odds_by_horse_number"]["1"]=.8
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_WIN_QUOTE"):
            build_freeze(s)
        s=deepcopy(self.source)
        s["models"][0]["beta_horse"]=1
        with self.assertRaisesRegex(ValueError,"HOLD_BASELINE_MUST"):
            build_freeze(s)

    def test_wrong_official_race_real_synthetic_mix_and_invalid_podium(self):
        s=deepcopy(self.observed)
        s["race_id"]="ANOTHER-RACE"
        with self.assertRaisesRegex(ValueError,"HOLD_WRONG_OFFICIAL_RACE"):
            score_sealed(self.frozen,s)
        s=deepcopy(self.observed)
        s["top3_horse_numbers"]=[2,2,3]
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_OFFICIAL_PODIUM"):
            score_sealed(self.frozen,s)
        s=deepcopy(self.observed)
        s["top3_horse_numbers"]=[2,3,42]
        with self.assertRaisesRegex(ValueError,"HOLD_PROBABILITY_RUNNER_ROSTER"):
            score_sealed(self.frozen,s)
        s=deepcopy(self.observed)
        s["provenance"]="authorized_local_normalized_market"
        s["source_type"]="JRA_official"
        s["official_results_url"]="https://www.jra.go.jp/JRADB/accessS.html"
        with self.assertRaisesRegex(ValueError,"HOLD_REAL_AND_SYNTHETIC"):
            score_sealed(self.frozen,s)

    def test_unmodified_precommitted_payload_roundtrips_local_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"freeze.json"
            p.write_text(
                json.dumps(self.frozen,ensure_ascii=False,indent=2)+"\n",
                encoding="utf-8")
            v=json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(verify_seal(v),self.frozen["payload"])
            self.assertEqual(score_sealed(v,self.observed),self.scored)
            self.assertEqual(_seal(self.frozen["payload"]),
                             self.frozen["seal_sha256_of_canonical_payload"])


if __name__=="__main__":
    unittest.main()
