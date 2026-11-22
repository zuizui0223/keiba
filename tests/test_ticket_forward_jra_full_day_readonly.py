"""Synthetic JRA 24-race discovery and strict numbered-table oracle tests."""
import json
from pathlib import Path
import unittest

from scripts.ticket_forward_jra_full_day_readonly import (
    audit_day, card_key, discover_day_links, numbered_card_rows
)
from scripts.ticket_forward_program_preflight import audit_preliminary_program

STAGE=Path(__file__).resolve().parents[1]/"docs/evidence/ticket-forward-20261123-program-staging.json"


def make_url(venue,n):
    code,prefix = ("03","pw01dde01") if venue=="福島" else ("05","sw01ddd01")
    return f"https://www.jra.go.jp/JRADB/accessD.html?CNAME={prefix}{code}2026{code}06{n:02d}20261123/AA"


def make_table(venue,n,show_horses=True):
    heading=f"<h1>出馬表2026年11月23日 3回{venue}6日</h1>"
    rows=["<tr><th>枠</th><th>馬番</th><th>馬名</th></tr>"]
    if show_horses:
        for horse in range(1,n+1):
            rows.append(f"<tr><td>{min(8,horse)}</td><td>{horse}</td><td>horse</td></tr>")
    return heading+"<table>"+"".join(rows)+"</table>"


def synthetic_reader(stage, *, miss=None, mismatch_tokyo=True):
    counts={(r["venue"],r["race_number"]):r["third_party_displayed_runner_count"]
            for r in stage["races"]}
    links="".join(f'<a href="{make_url(v,i)}">R</a>'
                  for v in ("福島","東京") for i in range(1,13))
    def get(url):
        key=card_key(url)
        if key is None:
            raise ValueError("invalid_JRA_card")
        n=counts[key]
        if key==("東京",1) and mismatch_tokyo:
            n=13  # intentionally exposes third-party 14-vs-13 discrepancy
        page=make_table(key[0],n,show_horses=(key!=miss))
        if key[1]==1:
            page+=links
        raw=page.encode()
        return page,raw,url
    return get


class JraFullDayReadOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage=json.loads(STAGE.read_text())

    def test_url_key_is_official_and_requires_exact_date_meeting(self):
        self.assertEqual(card_key(make_url("福島",1)),("福島",1))
        self.assertEqual(card_key(make_url("東京",12)),("東京",12))
        with self.assertRaises(ValueError):
            card_key("https://not-jra.example/JRADB/accessD.html?CNAME=...")

    def test_table_requires_complete_contiguous_number_column(self):
        good,numbers=numbered_card_rows(make_table("東京",13))
        self.assertEqual(good,13)
        self.assertEqual(numbers[0]["html_row_count"],14)
        missing=make_table("東京",13).replace("<td>7</td><td>7</td>","<td>7</td><td>19</td>")
        num,_=numbered_card_rows(missing)
        self.assertIsNone(num)

    def test_all_24_urls_discovered_from_official_anchor_html(self):
        source=synthetic_reader(self.stage)
        a=make_url("福島",1);b=make_url("東京",1)
        mapping=discover_day_links([(a,source(a)[0]),(b,source(b)[0])])
        self.assertEqual(len(mapping),24)
        self.assertEqual(set(mapping),{(r["venue"],r["race_number"]) for r in self.stage["races"]})

    def test_full_audit_returns_disagreement_and_stays_unsealed(self):
        audit=audit_day(synthetic_reader(self.stage),self.stage)
        self.assertEqual(audit["expected_cards"],24)
        self.assertEqual(audit["number_sequence_card_count"],24)
        self.assertEqual(audit["preliminary_count_disagreement_count"],1)
        self.assertEqual(audit["preliminary_count_disagreements"][0]["race_id"],
                         "2026-11-23-TOKYO-01")
        self.assertEqual(audit["preliminary_count_disagreements"][0]["official_number_rows"],13)
        self.assertEqual(audit["preliminary_count_disagreements"][0]["third_party_preliminary_count"],14)
        self.assertFalse(audit["official_program_day_git_server_seal"])
        self.assertFalse(audit["actual_runner_scratch_status_verified"])
        self.assertEqual(audit["future_prospective_forecasts"],0)

    def test_one_unparseable_card_yields_hold_not_imputation(self):
        audit=audit_day(synthetic_reader(self.stage,miss=("福島",4)),self.stage)
        self.assertEqual(audit["number_sequence_card_count"],23)
        self.assertEqual(audit["status"],"HOLD_INCOMPLETE_OFFICIAL_CARD_ROSTER_PARSE")
        missing=next(r for r in audit["races"] if r["race_id"]=="2026-11-23-FUKUSHIMA-04")
        self.assertEqual(missing["parse_status"],"HOLD_NO_UNIQUE_NUMBER_SEQUENCE")
        self.assertIsNone(missing["strict_numbered_horse_rows"])


if __name__=="__main__":
    unittest.main()
