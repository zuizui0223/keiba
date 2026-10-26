"""Synthetic-only source identity, repetition, biology->market and stability tests.

Original RQ horses/identifiers/timing remain outside the repository.
A passing test does not establish real JRA herd behaviour or a critical price.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import math
import sys
import unittest
try:
    import numpy as np
except ModuleNotFoundError as error:
    if error.name != "numpy":
        raise
    np = None

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
if np is not None:
    from keiba_individual_trait_to_market_cascade import (
    repeatable_traits,objective_horse_prior,initial_market_proxy,
    layered_vote_market,theoretical_gain,deterministic_market_step,
    local_market_gain,premarket_context_log_scores,run_coupled_repeatability_trial,
)


HORSES=["H1","H2","H3","H4","H5","H6"]
SOURCE_SYSTEM="SYNTHETIC_SAME_STABLE_HORSE_IDS_NO_RQ_JRA_MAPPING"


def make_target():
    return {
        "source_system":SOURCE_SYSTEM,"horse_ids":HORSES.copy(),
        "asof_jst":"2026-10-26T09:30:00+09:00",
        "initial_market_published_at_jst":"2026-10-26T08:45:00+09:00",
        "initial_market_received_at_jst":"2026-10-26T09:00:00+09:00",
        "first_marker_m":150,"distance_m":1000,"race_class":"C",
    }


def make_source():
    # Stable within-horse trait, varying per-race conditions and measurement
    # noise, created synthetically. No actual horse identity or outcome.
    traits=[-.44,-.31,-.15,.14,.31,.46]
    records=[]
    for day in range(1,7):
        for i,horse in enumerate(HORSES):
            t=9.0+0.11*day+traits[i]+.037*((day+2*i)%4-1.5)
            records.append({
                "source_system":SOURCE_SYSTEM,
                "horse_id":horse,
                "race_id":f"TOY-R{day}",
                "race_day":f"2026-10-0{day}T10:00:00+09:00",
                "received_at":f"2026-10-0{day}T12:00:00+09:00",
                "first_marker_m":150,
                "distance_m":1000,"race_class":"C",
                "first_section_seconds":t,
            })
    return {
        "schema":"KEIBA_SAME_HORSE_GPS_REPEATABILITY_HISTORY_V1",
        "source_system":SOURCE_SYSTEM,
        "rights_checked_locally":True,
        "authenticated_publisher_clock":True,
        "records":records,
    }


@unittest.skipIf(np is None, "Optional numpy required; dedicated CI installs it")
class RepeatableIndividualToMarketsTests(unittest.TestCase):
    def test_estimates_identity_specific_repeated_traits(self):
        x=repeatable_traits(make_source(),make_target())
        self.assertEqual(x["repeated_source_horses"],6)
        self.assertEqual(x["source_races"],6)
        self.assertEqual(x["distinct_source_days"],6)
        self.assertGreater(x["horse_effect_variance_seconds_squared"],0)
        self.assertGreater(x["residual_variance_seconds_squared"],0)
        self.assertGreater(x["source_conditional_approx_icc"],0.5)
        p=x["posterior"]
        self.assertLess(p["H1"]["mean_relative_seconds"],0)
        self.assertGreater(p["H6"]["mean_relative_seconds"],0)
        self.assertEqual(p["H1"]["n_historical_dates"],6)
        self.assertGreater(p["H1"]["variance_seconds_squared"],0)
        obj=objective_horse_prior(x)
        self.assertAlmostEqual(float(obj.sum()),1.,places=12)
        self.assertGreater(obj[0],obj[-1])

    def test_source_identity_marker_class_date_are_strict(self):
        for mode in ("new_target","cross_source","cross_record_source",
                     "market_quote_time_reversed","early_market_quote",
                     "marker","race_class","late_receive","late_race",
                     "missing_one_peer","duplicate","future_target_label",
                     "no_source_rights"):
            source,target=make_source(),make_target()
            if mode=="market_quote_time_reversed":
                target["initial_market_published_at_jst"]="2026-10-26T09:15:00+09:00"
                target["initial_market_received_at_jst"]="2026-10-26T09:00:00+09:00"
            if mode=="early_market_quote":
                target["initial_market_published_at_jst"]="2026-09-30T08:30:00+09:00"
                target["initial_market_received_at_jst"]="2026-09-30T08:50:00+09:00"
            if mode=="new_target":target["source_system"]="UNRELATED_JRA"
            if mode=="cross_source":source["source_system"]="UNRELATED_JRA"
            if mode=="cross_record_source":source["records"][0]["source_system"]="UNRELATED_JRA"
            if mode=="marker":source["records"][0]["first_marker_m"]=200
            if mode=="race_class":source["records"][0]["race_class"]="OTHER"
            if mode=="late_receive":source["records"][0]["received_at"]="2026-10-27T12:00:00+09:00"
            if mode=="late_race":source["records"][0]["race_day"]="2026-10-27T10:00:00+09:00"
            if mode=="missing_one_peer":source["records"]=[r for r in source["records"]
                                                       if not (r["race_id"]=="TOY-R1" and r["horse_id"] in ("H1","H2","H3"))]
            if mode=="duplicate":source["records"].append(source["records"][0].copy())
            if mode=="future_target_label":source["winner"]="H1"
            if mode=="no_source_rights":source["rights_checked_locally"]=False
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                repeatable_traits(source,target)

    def test_observed_market_is_not_objective_horse_prior(self):
        trait=repeatable_traits(make_source(),make_target())
        p=objective_horse_prior(trait)
        a=initial_market_proxy(dict(zip(HORSES,[10.,7.,4.,3.,2.,1.5])),HORSES)
        b=initial_market_proxy(dict(zip(HORSES,[1.5,2.,3.,4.,7.,10.])),HORSES)
        self.assertGreater(p[0],p[-1])
        self.assertGreater(a[-1],a[0])
        self.assertGreater(b[0],b[-1])
        self.assertTrue(np.array_equal(p,objective_horse_prior(trait)))
        self.assertFalse(np.array_equal(a,b))

    def test_fundamental_and_social_information_are_different_channels(self):
        q0=initial_market_proxy(dict(zip(HORSES,[2.,3.,4.,5.,6.,7.])),HORSES)
        objective=initial_market_proxy(dict(zip(HORSES,[10.,9.,8.,7.,6.,5.])),HORSES)
        signalA=initial_market_proxy(dict(zip(HORSES,[2.,10.,10.,10.,10.,10.])),HORSES)
        signalB=initial_market_proxy(dict(zip(HORSES,[10.,10.,10.,10.,10.,2.])),HORSES)
        a=layered_vote_market(q0,objective,signalA,release_step=3,seed=51)
        b=layered_vote_market(q0,objective,signalB,release_step=3,seed=51)
        for step in (0,1,2):
            np.testing.assert_array_equal(a["path"][step],b["path"][step])
        self.assertFalse(np.array_equal(a["final"],b["final"]))
        c=layered_vote_market(q0,objective,signalA,release_step=5,seed=51)
        d=layered_vote_market(q0,objective,signalB,release_step=5,seed=51)
        for x,y in zip(c["path"],d["path"]):
            np.testing.assert_array_equal(x,y)
        self.assertEqual(c["rounds"][-1]["horse_information_visible"],False)
        self.assertEqual(sum(r["new_votes"] for r in c["rounds"]),1000)

    def test_self_reference_is_not_an_absolute_price_cutoff(self):
        a=theoretical_gain(herding_fraction=.5,gamma=1,new_vote_fraction=.2)
        b=theoretical_gain(herding_fraction=.5,gamma=2,new_vote_fraction=.2)
        c=theoretical_gain(herding_fraction=.5,gamma=3,new_vote_fraction=.2)
        self.assertAlmostEqual(a["linear_gain"],.9)
        self.assertAlmostEqual(b["linear_gain"],1.)
        self.assertAlmostEqual(c["linear_gain"],1.1)
        self.assertEqual([a["regime"],b["regime"],c["regime"]],
                         ["damping","neutral","amplifying"])
        self.assertEqual(b["neutral_social_exponent"],2.)
        self.assertIsNone(b["critical_absolute_win_odds"])
        self.assertTrue(c["not_observed_JRA_phase_transition"])
        with self.assertRaises(ValueError):
            theoretical_gain(herding_fraction=1.2,gamma=1,new_vote_fraction=.2)

    def test_coupled_real_modules_receive_same_synthetic_trait_prior(self):
        market=dict(zip(HORSES,[2.1,3.2,4.3,5.1,7.,10.]))
        out=run_coupled_repeatability_trial(
            make_source(),make_target(),observed_first_odds=market,
            horse_draws=45,seed=2501,info_release_round=1)
        self.assertTrue(out["information_never_market_identical"])
        self.assertTrue(out["not_empirically_calibrated"])
        self.assertEqual(len(out["independent_horse_objective_prior"]),6)
        self.assertAlmostEqual(out["observed_early_market_proxy"].sum(),1)
        self.assertAlmostEqual(out["physical_nonlocal_horse_model"]["crowded_win_signal"].sum(),1)
        self.assertTrue(np.isfinite(out["market_crowding_effect_TV_points"]))
        self.assertGreaterEqual(out["market_crowding_effect_TV_points"],0)

        revised=dict(zip(HORSES,[10.,9.,7.,5.1,3.2,2.1]))
        different=run_coupled_repeatability_trial(
            make_source(),make_target(),observed_first_odds=revised,
            horse_draws=45,seed=2501,info_release_round=1)
        np.testing.assert_array_equal(
            out["independent_horse_objective_prior"],
            different["independent_horse_objective_prior"])
        np.testing.assert_array_equal(
            out["physical_nonlocal_horse_model"]["crowded_win_signal"],
            different["physical_nonlocal_horse_model"]["crowded_win_signal"])
        self.assertFalse(np.array_equal(
            out["observed_early_market_proxy"],
            different["observed_early_market_proxy"]))

    def test_same_kernel_agent_pde_receives_objective_prior(self):
        out=run_coupled_repeatability_trial(
            make_source(),make_target(),
            observed_first_odds=dict(zip(HORSES,[2.1,3.2,4.3,5.1,7.,10.])),
            horse_draws=40,seed=12,info_release_round=5,pde_particles=100)
        self.assertIn("matching_kernel_agent_PDE",out)
        # PDE and physical law are numerical demonstrations, not real GPS fits.
        self.assertEqual(out["physical_nonlocal_horse_model"]
                         ["source_physical_constants_hypothetical"]["kernel_radius_m"],8.)
        self.assertTrue(out["information_never_market_identical"])


    def test_local_gain_jacobian_matches_analytic_uniform_threshold(self):
        # f_herd = 1/2 => the source-free uniform fixed point is neutral
        # at gamma=2, NOT when any particular displayed odds hits 10.
        q=np.ones(6)/6
        for gamma,expected in ((1.,.9),(2.,1.),(3.,1.1)):
            with self.subTest(gamma=gamma):
                out=local_market_gain(q,q,q,gamma=gamma,
                                      new_vote_fraction=.2)
                analytic=theoretical_gain(
                    herding_fraction=.5,gamma=gamma,
                    new_vote_fraction=.2)["linear_gain"]
                self.assertTrue(out["is_evaluated_at_equilibrium"])
                self.assertTrue(out["gain_is_an_instability_test"])
                self.assertAlmostEqual(
                    out["local_simplex_spectral_gain"],analytic,places=7)
                self.assertAlmostEqual(analytic,expected)
        nonuniform=unit = np.asarray([.35,.25,.20,.10,.07,.03])
        out=local_market_gain(q,nonuniform,q,gamma=1.3)
        self.assertFalse(out["is_evaluated_at_equilibrium"])
        self.assertFalse(out["gain_is_an_instability_test"])
        self.assertIsNone(out["model_critical_absolute_odds"])


    def test_pre_market_objective_weather_going_jockey_source_gate(self):
        target=make_target()
        receipt={
            "schema":"KEIBA_PUBLISHED_OBJECTIVE_CONTEXT_V1",
            "rights_checked_locally":True,
            "target_source_system":SOURCE_SYSTEM,
            "feature_names":["track","going","weather","jockey","distance"],
            "feature_model_frozen_at_jst":"2026-09-28T12:00:00+09:00",
            "source_published_at_jst":"2026-10-20T12:00:00+09:00",
            "source_received_at_jst":"2026-10-20T12:15:00+09:00",
            "objective_log_score_by_horse_id":{h:(i-2.5)*.03 for i,h in enumerate(HORSES)}
        }
        scores=premarket_context_log_scores(receipt,target)
        self.assertEqual(set(scores),set(HORSES))
        a=run_coupled_repeatability_trial(
            make_source(),target,
            observed_first_odds=dict(zip(HORSES,[2.,3.,4.,5.,6.,7.])),
            premarket_context_receipt=receipt,horse_draws=40,seed=77)
        b=run_coupled_repeatability_trial(
            make_source(),target,
            observed_first_odds=dict(zip(HORSES,[2.,3.,4.,5.,6.,7.])),
            horse_draws=40,seed=77)
        self.assertTrue(a["premarket_context_used"])
        self.assertFalse(b["premarket_context_used"])
        self.assertFalse(np.array_equal(a["independent_horse_objective_prior"],
                                        b["independent_horse_objective_prior"]))
        self.assertEqual(a["premarket_context_proof"],
                         "LOCAL_ONLY_EXTERNAL_ATTESTATION_HOLD")
        for mode in ("late_source","late_model_freeze","odds_leak","missing_horse","bad_feature"):
            modified=deepcopy(receipt)
            if mode=="late_source":
                modified["source_received_at_jst"]="2026-10-26T08:46:00+09:00"
            if mode=="late_model_freeze":
                modified["feature_model_frozen_at_jst"]="2026-10-26T08:50:00+09:00"
            if mode=="odds_leak":modified["market_q0"]={h:1/6 for h in HORSES}
            if mode=="missing_horse":
                modified["objective_log_score_by_horse_id"].pop("H6")
            if mode=="bad_feature":modified["feature_names"].append("current_odds")
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                premarket_context_log_scores(modified,target)



    def test_already_conditioned_physical_signal_is_not_multiplied_by_objective_twice(self):
        # The physical ABM already used objective evidence. Giving its
        # exact same probability vector as the public "new" signal must
        # NOT cause a change. The old obj*signal code violates this.
        obj=initial_market_proxy(dict(zip(HORSES,[2.,3.,4.,6.,8.,12.])),HORSES)
        q0=initial_market_proxy(dict(zip(HORSES,[9.,7.,5.,4.,3.,2.])),HORSES)
        all_informed={"fundamental":0.,"herding":0.,"informed":1.}
        immediate=layered_vote_market(
            q0,obj,obj,voter_shares=all_informed,release_step=1,seed=1234)
        never=layered_vote_market(
            q0,obj,obj,voter_shares=all_informed,release_step=5,seed=1234)
        for early,late in zip(immediate["path"],never["path"]):
            np.testing.assert_array_equal(early,late)
        expected=deterministic_market_step(
            q0,obj,obj,voter_shares=all_informed,new_vote_fraction=.2)
        np.testing.assert_allclose(expected,.8*q0+.2*obj,atol=1e-14)
        self.assertAlmostEqual(float(expected.sum()),1.,places=12)


    def test_time_layered_objective_then_social_influence_is_a_scenario_not_observed(self):
        ids=HORSES
        q0=initial_market_proxy(dict(zip(ids,[2.,3.,4.,5.,6.,7.])),ids)
        objective=initial_market_proxy(dict(zip(ids,[7.,6.,5.,4.,3.,2.])),ids)
        schedule=[
            {"fundamental":.60,"herding":.20,"informed":.20},
            {"fundamental":.45,"herding":.35,"informed":.20},
            {"fundamental":.25,"herding":.50,"informed":.25},
            {"fundamental":.15,"herding":.60,"informed":.25},
        ]
        a=layered_vote_market(
            q0,objective,objective,gamma=2.,release_step=5,
            voter_shares_by_round=schedule,seed=71)
        self.assertTrue(a["social_mix_is_time_varying"])
        gains=[round(r["uniform_null_local_gain"],6) for r in a["rounds"]]
        self.assertLess(gains[0],1)
        self.assertLess(gains[1],1)
        self.assertAlmostEqual(gains[2],1.,places=6)
        self.assertGreater(gains[3],1)
        self.assertEqual([r["new_votes"] for r in a["rounds"]],[250]*4)
        # This equilibrium result does NOT imply the current nonuniform
        # market actually changes phase at one fixed quoted price.
        self.assertNotEqual(schedule[0]["herding"],schedule[-1]["herding"])
        const={"fundamental":.25,"herding":.5,"informed":.25}
        base=layered_vote_market(q0,objective,objective,seed=71)
        same=layered_vote_market(q0,objective,objective,
                                 voter_shares_by_round=[const]*4,seed=71)
        for x,y in zip(base["path"],same["path"]):
            np.testing.assert_array_equal(x,y)

        for bad in ([schedule[0]]*3,
                    [dict(schedule[0],herding=-.01)]*4):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                layered_vote_market(q0,objective,objective,
                                     voter_shares_by_round=bad)
        with self.assertRaises(ValueError):
            layered_vote_market(q0,objective,objective,
                 voter_shares=schedule[0],voter_shares_by_round=schedule)


if __name__ == "__main__":
    unittest.main()
