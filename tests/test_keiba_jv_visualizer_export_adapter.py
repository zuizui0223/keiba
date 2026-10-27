#!/usr/bin/env python3
"""Official four-line CSV envelope, synthetic tab layouts and strict as-of."""
from __future__ import annotations

from itertools import combinations
import copy
import csv
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
if np is not None:
    import keiba_jv_visualizer_export_adapter as a
    import keiba_operator_winwide_capture as op
    import keiba_win_only_shadow_lane as B
    import keiba_operator_cohort_bundle as A
    from test_keiba_operator_winwide_capture import card,DATE


def csv_sample(*, market="win",scale=1.,tab=None,postrace=False,
               partial=False,range_column=True,realistic_jra_code=True,
               race_no=11):
    header=[
        "20261031010811"+f"{race_no:02d}" if realistic_jra_code else "XXX",
        "2026/10/31","土","京都",str(race_no),"15:45","",
        "ファンタジーS","2歳牝馬","芝","1400","",
        "","", "6","","",
    ]
    if market=="win":
        title=tab or "単複"
        columns=["枠","馬番","馬名","単勝","人気","着順","払戻"]
        body=[
            [str(i//2+1),str(i),f"SYN_HORSE_{i}",
             str(float((2+2*i)*(scale if i%2 else 1./scale))),
             str(i),str(i) if postrace and i==1 else "",
             "100" if postrace and i==1 else ""]
            for i in range(1,7)]
    else:
        title=tab or "ワイド人気順"
        columns=(["順","組","オッズ","払戻"] if range_column
                 else ["順","組","下限","上限","払戻"])
        body=[]
        for k,(i,j) in enumerate(combinations(range(1,7),2),1):
            lo=float(2+i+j)
            hi=float(lo+0.7)
            if range_column:
                body.append([str(k),f"{i}-{j}",f"{lo}～{hi}",
                             "400" if postrace and k==1 else ""])
            else:
                body.append([str(k),f"{i}-{j}",str(lo),str(hi),
                             "400" if postrace and k==1 else ""])
        if partial:
            body.pop()
    buf=io.StringIO(newline="")
    writer=csv.writer(buf,lineterminator="\r\n")
    writer.writerow(header)
    writer.writerow([])
    writer.writerow([title])
    writer.writerow(columns)
    writer.writerows(body)
    return ("\ufeff"+buf.getvalue()).encode("utf-8")


@unittest.skipIf(np is None,"NumPy only required for linked horse/voter test")
class VisualizerCSVEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.card=card()
        self.provider=self.card["provider"]
        self.url="https://example.org/testing-export-source"
        self.upd=DATE+"T11:00:00+09:00"

    def import_win(self,data=None,t=None):
        return a.adapt_one_export(
            data if data is not None else csv_sample(),
            self.card,market="win",
            source_updated_at_jst=t or self.upd,
            provider=self.provider,source_url=self.url)

    def import_wide(self,data=None):
        return a.adapt_one_export(
            data if data is not None else csv_sample(market="wide"),
            self.card,market="wide",source_updated_at_jst=self.upd,
            provider=self.provider,source_url=self.url)

    def test_documented_csv_header_and_one_time_WIN_normalizes_full_field(self):
        result,audit=self.import_win()
        self.assertEqual(audit["full_win_n"],6)
        self.assertEqual(audit["full_wide_n_pairs"],0)
        self.assertEqual(result["market"],"win")
        self.assertEqual(result["race_id"],self.card["race_id"])
        self.assertEqual(set(result["odds_by_horse_number"]),
                         {str(i) for i in range(1,7)})
        self.assertEqual(audit["JvOddsVisualizer_16digit_race_code"],
                         "2026103101081111")
        self.assertTrue(audit[
            "operator_provided_source_update_clock_NOT_from_csv_header"])
        self.assertFalse(audit["source_clock_and_reception_independently_attested"])
        from hashlib import sha256
        self.assertEqual(
            audit["original_vendor_export_bytes_SHA256_local_only"],
            sha256(csv_sample()).hexdigest())
        self.assertEqual(
            audit["normalized_private_snapshot_SHA256_local_only"],
            sha256(op._dump(result).encode("utf-8")).hexdigest())
        self.assertTrue(audit[
            "raw_vendor_export_byte_digest_in_normalized_capture_and_later_chain"])
        self.assertTrue(audit["append_requires_original_csv_and_final_card_reparse"])
        self.assertEqual(result["original_vendor_export"]["raw_csv_sha256"],
                         audit["original_vendor_export_bytes_SHA256_local_only"])

    def test_WIDE_range_as_pair_list_full_edges_not_matrix(self):
        win,_=self.import_win()
        wide,audit=self.import_wide()
        self.assertEqual(wide["market"],"wide")
        self.assertEqual(len(wide["pairs"]),15)
        self.assertEqual(audit["full_wide_n_pairs"],15)
        self.assertEqual(wide["pairs"][0]["selection"],[1,2])
        self.assertGreaterEqual(wide["pairs"][0]["odds_high"],
                                wide["pairs"][0]["odds_low"])
        text=csv_sample(market="wide",range_column=False)
        wide2,_=self.import_wide(text)
        self.assertEqual(
            [x["odds_low"] for x in wide["pairs"]],
            [x["odds_low"] for x in wide2["pairs"]])

    def test_postrace_WIN_or_WIDE_finish_or_payout_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"POSTRACE_FINISH_OR_PAYOUT"):
            self.import_win(csv_sample(postrace=True))
        with self.assertRaisesRegex(ValueError,"POSTRACE_FINISH_OR_PAYOUT"):
            self.import_wide(csv_sample(market="wide",postrace=True))

    def test_pair_missing_or_wrong_tab_halts_A_without_imputing_WIDE(self):
        with self.assertRaisesRegex(ValueError,"NOT_ALL_PAIRS"):
            self.import_wide(csv_sample(market="wide",partial=True))
        with self.assertRaisesRegex(ValueError,"ONLY_ONE_TIME_WIN_TAB"):
            self.import_win(csv_sample(tab="単勝推移"))
        with self.assertRaisesRegex(ValueError,"WIDE_PAIR_LIST_REQUIRED_NOT_MATRIX"):
            self.import_wide(csv_sample(market="wide").replace(
                "順,組,オッズ,払戻".encode(),
                "順,馬番,オッズ,払戻".encode()))
        with self.assertRaisesRegex(ValueError,"NOT_A_WIDE_PAIR_LIST_TAB"):
            self.import_wide(csv_sample(market="wide",tab="馬連人気順"))

    def test_starter_card_venue_post_date_distance_and_runners_must_agree(self):
        for key,value in (
            ("scheduled_post_jst",DATE+"T15:40:00+09:00"),
            ("race_distance_m",2000),
            ("horse_numbers",[1,2,3,4,5,7]),
            ("slot_id","2026-10-31|東京|R11"),
        ):
            c=copy.deepcopy(self.card)
            c[key]=value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    a.adapt_one_export(csv_sample(),c,market="win",
                        source_updated_at_jst=self.upd,
                        provider=self.provider,source_url=self.url)
        with self.assertRaisesRegex(ValueError,"SOURCE_RACE_NOT_CONFIRMED_CARD"):
            self.import_win(csv_sample(race_no=10))

    def test_no_late_or_naive_operator_fabricated_source_clock(self):
        with self.assertRaises(ValueError):
            self.import_win(t=DATE+"T15:40:00+09:00")
        with self.assertRaises(ValueError):
            self.import_win(t=DATE+"T11:00:00")
        with self.assertRaises(ValueError):
            self.import_win(t="2026-11-01T11:00:00+09:00")
        with self.assertRaisesRegex(ValueError,"PROVIDER_DIFFERENT"):
            a.adapt_one_export(csv_sample(),self.card,market="win",
                source_updated_at_jst=self.upd,
                provider="WRONG_PROVIDER",source_url=self.url)

    def test_vendor_layout_ambiguity_or_unverified_columns_are_not_guessed(self):
        blob=csv_sample(market="wide")
        with self.assertRaisesRegex(ValueError,"USER_DECLARED_WIDE_COLUMN_ABSENT"):
            a.adapt_one_export(blob,self.card,market="wide",
                 source_updated_at_jst=self.upd,provider=self.provider,
                 source_url=self.url,range_col="NOT_A_REAL_COLUMN")
        with self.assertRaisesRegex(ValueError,"AMBIGUOUS_WIDE"):
            a.adapt_one_export(blob,self.card,market="wide",
                 source_updated_at_jst=self.upd,provider=self.provider,
                 source_url=self.url,range_col="オッズ",low_col="オッズ")
        with self.assertRaisesRegex(ValueError,"EXPECTED_RACE_HEADER"):
            self.import_win(b"nonsense,header\n")

    def test_friday_presale_quote_can_have_different_date_from_saturday_race(self):
        # The exported first-row date is the RACE date, not necessarily the
        # selected pre-sale WIN odds published date. Only publication and
        # local append receipt are distinct, operator-declared clocks.
        src,check=self.import_win(t="2026-10-30T17:00:00+09:00")
        self.assertEqual(src["source_updated_at_jst"],
                         "2026-10-30T17:00:00+09:00")
        self.assertEqual(check["full_win_n"],6)
        with self.assertRaisesRegex(ValueError,"QUOTE_TIME_NOT_BEFORE_POST"):
            self.import_win(t="2026-10-27T12:00:00+09:00")

    def test_real_csv_must_be_UTF8_and_bom_handled_safely(self):
        with self.assertRaisesRegex(ValueError,"NOT_UTF8"):
            self.import_win(csv_sample().replace(b"\xe9\xa6\xac",b"\xff"))
        no_bom=csv_sample().decode("utf-8-sig").encode("utf-8")
        src,_=self.import_win(no_bom)
        self.assertEqual(len(src["odds_by_horse_number"]),6)

    def test_exported_WIN_and_WIDE_snapshots_feed_actual_existing_models(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"private"/"jv_visualizer"
            original_first=csv_sample(scale=1)
            original_mid=csv_sample(scale=1.10)
            original_wide=csv_sample(market="wide")
            first,_=self.import_win(original_first,
                 t=DATE+"T10:00:00+09:00")
            mid,_=self.import_win(original_mid)
            wide,_=self.import_wide(original_wide)
            op.append_capture(folder,first,
                              captured_at_jst=DATE+"T10:02:00+09:00",
                              original_vendor_bytes=original_first,
                              confirmed_final_card=self.card)
            op.append_capture(folder,mid,
                              captured_at_jst=DATE+"T11:01:00+09:00",
                              original_vendor_bytes=original_mid,
                              confirmed_final_card=self.card)
            op.append_capture(folder,wide,
                              captured_at_jst=DATE+"T11:02:00+09:00",
                              original_vendor_bytes=original_wide,
                              confirmed_final_card=self.card)
            laneB=B.prepare_win_only(
                folder,self.card,horse_draws=40,
                frozen_at_jst=DATE+"T11:03:00+09:00",seed=8)
            laneA=A.prepare_bundle(
                folder,self.card,horse_draws=40,
                frozen_at_jst=DATE+"T11:03:00+09:00",seed=8)
            self.assertEqual(len(laneB["payload"]["fixed_next_quote_model_indices"]),6)
            self.assertEqual(len(laneA["freeze"]["payload"]["candidate_predictions"]),12)
            self.assertFalse(laneB["payload"]["full_WIDE_grid_used_as_signal"])
            self.assertEqual(laneA["registered_cohort"]["primary_scope"],
                             "FROZEN_GRADED_26_PRIMARY")
            self.assertFalse(laneA["external_GitHub_comment_created_at_verified"])
            chain=op._read_ledger(folder)
            from hashlib import sha256
            self.assertEqual(chain[0]["captured_source"]["original_vendor_export"][
                "raw_csv_sha256"],sha256(original_first).hexdigest())
            self.assertEqual(chain[1]["captured_source"]["original_vendor_export"][
                "raw_csv_sha256"],sha256(original_mid).hexdigest())
            self.assertEqual(chain[2]["captured_source"]["original_vendor_export"][
                "raw_csv_sha256"],sha256(original_wide).hexdigest())
            # Thus the outer PR22 SHA covers original CSV byte digests
            # transitively through the committed local source-chain HEAD.
            binding=laneA["freeze"]["payload"][
                "operator_source_card_chain_binding"]
            self.assertEqual(
                binding["private_capture_chain_prefix_sha256"],
                chain[-1]["event_sha256"])
            self.assertEqual(
                laneB["payload"]["original_local_capture_chain_prefix_SHA256"],
                chain[-1]["event_sha256"])

    def test_original_bytes_required_not_merely_unverified_vendor_hash(self):
        original=csv_sample()
        normalized,_=self.import_win(original)
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"private"/"captures"
            with self.assertRaisesRegex(
                    ValueError,"ORIGINAL_VENDOR_BYTES_AND_FINAL_CARD_REQUIRED"):
                op.append_capture(folder,normalized,
                                  captured_at_jst=DATE+"T11:01:00+09:00")
            self.assertEqual(len(op._read_ledger(folder)),0)
            with self.assertRaisesRegex(
                    ValueError,"ORIGINAL_VENDOR_CSV_BYTES_DIGEST_MISMATCH"):
                op.append_capture(folder,normalized,
                                  captured_at_jst=DATE+"T11:01:00+09:00",
                                  original_vendor_bytes=csv_sample(scale=1.3),
                                  confirmed_final_card=self.card)
            self.assertEqual(len(op._read_ledger(folder)),0)

    def test_correct_original_CSV_cannot_certify_changed_normalized_prices(self):
        original=csv_sample()
        normalized,_=self.import_win(original)
        changed=copy.deepcopy(normalized)
        changed["odds_by_horse_number"]["1"]=987.0
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"private"/"captures"
            with self.assertRaisesRegex(
                    ValueError,"ORIGINAL_CSV_NOT_SAME_NORMALIZED_HORSE_QUOTES"):
                op.append_capture(folder,changed,
                                  captured_at_jst=DATE+"T11:01:00+09:00",
                                  original_vendor_bytes=original,
                                  confirmed_final_card=self.card)
            self.assertEqual(len(op._read_ledger(folder)),0)

    def test_wrong_original_CSV_mapping_or_card_cannot_enter_receipt_chain(self):
        original=csv_sample(market="wide")
        normalized,_=self.import_wide(original)
        altered=copy.deepcopy(normalized)
        altered["original_vendor_export"]["wide_range_col"]="下限"
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"private"/"captures"
            with self.assertRaises(ValueError):
                op.append_capture(folder,altered,
                                  captured_at_jst=DATE+"T11:01:00+09:00",
                                  original_vendor_bytes=original,
                                  confirmed_final_card=self.card)
            altered=copy.deepcopy(self.card)
            altered["race_distance_m"]=1800
            with self.assertRaisesRegex(ValueError,"SOURCE_RACE_NOT_CONFIRMED_CARD"):
                op.append_capture(folder,normalized,
                                  captured_at_jst=DATE+"T11:01:00+09:00",
                                  original_vendor_bytes=original,
                                  confirmed_final_card=altered)
            self.assertEqual(len(op._read_ledger(folder)),0)

    def test_vendor_binding_cannot_be_silently_removed_by_extra_field(self):
        original=csv_sample()
        normalized,_=self.import_win(original)
        corrupted=copy.deepcopy(normalized)
        corrupted["original_vendor_export"]["raw_csv_sha256"]="bad"
        with self.assertRaisesRegex(
                ValueError,"INVALID_OR_UNLINKED_VENDOR_CSV_BYTES_DIGEST"):
            op._verify_capture_payload(corrupted)
        corrupted=copy.deepcopy(normalized)
        corrupted["unverified_future_winner"]=1
        with self.assertRaisesRegex(ValueError,"EXTRA_FUTURE_FIELDS"):
            op._verify_capture_payload(corrupted)

    def test_historical_license_and_vanishing_noncanonical_pair_rejected(self):
        raw=csv_sample(market="wide")
        bad=raw.replace(b"1-2",b"1-8",1)
        with self.assertRaisesRegex(ValueError,"WIDE_PAIR_SELECTION_INVALID"):
            self.import_wide(bad)


if __name__=="__main__":
    unittest.main()
