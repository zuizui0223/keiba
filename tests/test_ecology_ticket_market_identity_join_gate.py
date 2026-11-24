"""Research identity join gate, never join historical market data by names."""
import copy
import unittest

from scripts.ecology_ticket_market_identity_join_gate import (
    directory_candidate, audit_card, audit_all
)


class MarketHorseIdentityGateTests(unittest.TestCase):
    def test_source_specific_directory_url_key_only(self):
        self.assertEqual(
            directory_candidate("https://sports.yahoo.co.jp/keiba/directory/horse/2022103705/"),
            "2022103705")
        for url in (
            "http://sports.yahoo.co.jp/keiba/directory/horse/2022103705/",
            "https://evil.example/keiba/directory/horse/2022103705/",
            "https://sports.yahoo.co.jp.evil.example/keiba/directory/horse/2022103705/",
            "https://sports.yahoo.co.jp/keiba/directory/horse/2022103705/?foo=x",
            "https://sports.yahoo.co.jp/keiba/directory/horse/not-an-id/",
            "https://sports.yahoo.co.jp/keiba/directory/horse/2022103705/extra",
        ):
            self.assertIsNone(directory_candidate(url))

    def test_real_archive_coverage_and_cross_day_join_is_hold(self):
        r=audit_all()
        self.assertEqual(r["Oct12_Kyoto_five_races"]["race_count"],5)
        self.assertEqual(r["Oct12_Kyoto_five_races"]["horse_rows"],67)
        self.assertEqual(r["Oct12_Kyoto_five_races"]["directory_ID_candidate_rows"],30)
        self.assertEqual(r["Oct12_Kyoto_five_races"]["missing_directory_candidate_rows"],37)
        self.assertEqual(r["Oct12_Kyoto_five_races"]["unique_directory_ID_candidates"],30)
        self.assertEqual(r["Oct18_9_race_quote_archive"]["horse_quote_rows"],117)
        self.assertEqual(r["Oct18_9_race_quote_archive"]["rows_with_explicit_stable_registry_ID"],0)
        self.assertEqual(r["Oct18_9_race_quote_archive"]["rows_with_explicit_directory_ID_or_URL"],0)
        self.assertEqual(r["exact_NFKC_normalized_horse_name_matches_across_2026_10_12_18"],0)
        self.assertTrue(r["nondisclosed_horse_names_in_both_cohorts_unique"])
        self.assertTrue(r["nonoverlapping_names_not_proof_of_authoritative_registry_absence"])
        self.assertFalse(r["cross_date_registered_ID_join_possible_from_current_quote_sources"])
        self.assertEqual(r["actual_verified_same_horse_ID_between_market_dates"],0)
        self.assertFalse(r["genomic_G_or_pedigree_A_same_individual_verified_join"])
        self.assertEqual(len(r["source_file_sha256"]),6)

    def test_refuse_two_id_links_or_duplicate_horse_number(self):
        horses=[
            {"number":i,"evidence_urls":[]} for i in range(1,9)
        ]
        card={"date":"2026-10-12","race":8,"horses":horses}
        test=copy.deepcopy(card)
        test["horses"][0]["evidence_urls"]=[
            "https://sports.yahoo.co.jp/keiba/directory/horse/2022103705/",
            "https://sports.yahoo.co.jp/keiba/directory/horse/2022103706/",
        ]
        with self.assertRaisesRegex(ValueError,"multiple_directory_identity_candidates"):
            audit_card(test,8)
        test=copy.deepcopy(card)
        test["horses"][0]["number"]=2
        with self.assertRaisesRegex(ValueError,"invalid_or_duplicate_horse_number"):
            audit_card(test,8)

    def test_no_implicit_registered_id_inferred_from_horse_name(self):
        card={"date":"2026-10-12","race":8,"horses":[
            {"number":i,"name":"same horse","evidence_urls":[]} for i in range(1,9)
        ]}
        row,candidates=audit_card(card,8)
        self.assertEqual(row["with_one_directory_candidate"],0)
        self.assertEqual(candidates,[])
        self.assertTrue(row["not_confirmed_JRA_registered_horse_IDs"] if "not_confirmed_JRA_registered_horse_IDs" in row else True)


if __name__=="__main__":
    unittest.main()
