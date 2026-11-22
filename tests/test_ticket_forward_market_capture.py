"""Live Yahoo 16 horse + 120 wide pair extraction oracle; no actual wagers."""
import json
import math
from pathlib import Path
import unittest

from scripts.ticket_forward_market_capture import parse_win, parse_wide, parse_sources, _allowed_same_resource, CARD_URL, TARGETS
from scripts.ticket_forward_freeze import REPO_ROOT, freeze_forecast, canonical


def example_win(updated="2026/11/23 09:23 更新", n=16):
    head="<tr><th>枠番</th><th>馬番</th><th>馬名</th><th>単勝</th><th>複勝</th></tr>"
    rows=[
        f"<tr><td>{(i+1)//2}</td><td>{i}</td><td>synthetic{i}</td>"
        f"<td>{2.0+i:.1f}</td><td>1.2 - 1.4</td></tr>"
        for i in range(1,n+1)
    ]
    return (f"<html><body><h1>2026年11月23日 福島1R</h1>"
            f"<table>{head}{''.join(rows)}</table><p>{updated}</p></body></html>").encode()


def example_wide(updated="2026/11/23 09:23 更新", n=16):
    tables=[]
    for i in range(1,n):
        rows=[
            f"<tr><td>{j}</td><td>{i+j+1.0:.1f} - {i+j+2.0:.1f}</td></tr>"
            for j in range(i+1,n+1)
        ]
        tables.append(f"<table><tr><th>{i}</th></tr>{''.join(rows)}</table>")
    return (f"<html><h1>2026年11月23日 福島1R</h1>"
            f"{''.join(tables)}<footer>{updated}</footer></html>").encode()


def example_jra(n=16):
    header="<tr><th>枠</th><th>馬番</th><th>馬名</th></tr>"
    rows=[
        f"<tr><td>{(i+1)//2}</td><td>{i}</td><td>horse{i}</td></tr>"
        for i in range(1,n+1)
    ]
    return (f"<html><h1>出馬表 2026年11月23日 福島1R</h1>"
            f"<table>{header}{''.join(rows)}</table></html>").encode()


class YahooFullMarketCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(
            (REPO_ROOT/"docs/betting/ticket-forward-v1-manifest.json").read_text(encoding="utf-8")
        )

    def test_strict_16_win_and_120_wide_pair_completion(self):
        frames,win,winup=parse_win(example_win())
        wide,wideup=parse_wide(example_wide(),16)
        self.assertEqual(len(win),16)
        self.assertEqual(len(wide),120)
        self.assertEqual(frames[1],1)
        self.assertEqual(frames[16],8)
        self.assertEqual(winup,"2026-11-23T09:23:00+09:00")
        self.assertEqual(wideup,"2026-11-23T09:23:00+09:00")
        self.assertEqual(wide[0]["selection"],[1,2])
        self.assertEqual(wide[-1]["selection"],[15,16])
        self.assertAlmostEqual(wide[0]["odds_low"],4.0)

    def test_real_freezer_accepts_only_synthetic_timely_complete_market(self):
        w,u,card=example_win(),example_wide(),example_jra()
        capture,diag=parse_sources(
            win_raw=w,wide_raw=u,card_raw=card,
            observed_win_jst="2026-11-23T09:24:05+09:00",
            observed_wide_jst="2026-11-23T09:24:15+09:00",
            manifest=self.manifest,
        )
        self.assertEqual(len(capture["race"]["horses"]),16)
        self.assertEqual(len(capture["markets"]["wide"]["quotes"]),120)
        self.assertFalse(diag["active_scratch_status_independently_verified"])
        f=freeze_forecast(
            capture,self.manifest,"2026-11-23T09:25:00+09:00",
            capture_raw=canonical(capture),
            source_pages={"win":w,"wide":u},
        )
        self.assertEqual(f["status"],"PRE_RACE_CANDIDATE_UNATTESTED")
        self.assertEqual(len(f["ordered_top3_probs"]),16*15*14)
        self.assertAlmostEqual(sum(row[3] for row in f["ordered_top3_probs"]),1,places=10)
        self.assertAlmostEqual(sum(row[4] for row in f["ordered_top3_probs"]),1,places=10)
        self.assertNotIn("result",capture)
        with self.assertRaisesRegex(ValueError,"market_receipt_stale"):
            freeze_forecast(
                capture,self.manifest,"2026-11-23T09:30:00+09:00",
                capture_raw=canonical(capture),
                source_pages={"win":w,"wide":u},
            )

    def test_missing_16th_or_wide_price_not_imputed(self):
        with self.assertRaisesRegex(ValueError,"JRA_card_number_rows_disagree"):
            parse_sources(
                win_raw=example_win(n=15),wide_raw=example_wide(n=15),
                card_raw=example_jra(n=16),
                observed_win_jst="2026-11-23T09:24:05+09:00",
                observed_wide_jst="2026-11-23T09:24:15+09:00",
                manifest=self.manifest,
            )
        incomplete=example_wide().replace(
            b"<tr><td>16</td><td>32.0 - 33.0</td></tr>",b"",1)
        with self.assertRaises(ValueError):
            parse_wide(incomplete,16)
        censored=example_win().replace(b"<td>3.0</td>",b"<td>999.9</td>",1)
        with self.assertRaisesRegex(ValueError,"censored_win_price"):
            parse_win(censored)

    def test_official_card_redirect_percent_encoding_is_not_new_resource(self):
        self.assertTrue(_allowed_same_resource(CARD_URL,CARD_URL.replace("%2F","/")))
        self.assertTrue(_allowed_same_resource(TARGETS["wide"],TARGETS["wide"]))
        self.assertFalse(_allowed_same_resource(CARD_URL,CARD_URL.replace("20261123","20261122")))
        self.assertFalse(_allowed_same_resource(
            TARGETS["wide"],"https://evil.example/keiba/race/odds/wide/2603030601?ninki=0"
        ))

    def test_cp932_official_card_decoding_is_accepted(self):
        source=example_jra().decode("utf-8").encode("cp932")
        capture,detail=parse_sources(
            win_raw=example_win(),wide_raw=example_wide(),card_raw=source,
            observed_win_jst="2026-11-23T09:24:05+09:00",
            observed_wide_jst="2026-11-23T09:24:15+09:00",
            manifest=self.manifest,
        )
        self.assertEqual(detail["JRA_numbered_rows"],16)
        self.assertEqual(len(capture["markets"]["wide"]["quotes"]),120)

    def test_jra_card_count_and_quote_time_must_match(self):
        with self.assertRaisesRegex(ValueError,"JRA_card_number_rows_disagree"):
            parse_sources(
                win_raw=example_win(),wide_raw=example_wide(),
                card_raw=example_jra(n=15),
                observed_win_jst="2026-11-23T09:24:05+09:00",
                observed_wide_jst="2026-11-23T09:24:15+09:00",
                manifest=self.manifest,
            )
        with self.assertRaisesRegex(ValueError,"market_observations_not_synchronous"):
            parse_sources(
                win_raw=example_win(),wide_raw=example_wide(),
                card_raw=example_jra(),
                observed_win_jst="2026-11-23T09:24:00+09:00",
                observed_wide_jst="2026-11-23T09:26:00+09:00",
                manifest=self.manifest,
            )


if __name__=="__main__":
    unittest.main()
