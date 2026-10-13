import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from v31_prepare_snapshot import prepare

CARD = """\
|  | 1 | アルファ  **4.2**(2番人気)  500kg(+4)  owner | 牡3/鹿  57.0kg  武 豊 | 2026年9月1日  阪神  1勝クラス  2着  12頭1番2番人気  武 豊  57.0kg  1800ダ  1:52.0  良  496kg  3F 37.0  ベータ(0.2) | 2026年7月1日  京都  未勝利  1着  10頭1番1番人気  武 豊  57.0kg  1800ダ  1:53.0  良  492kg  3F 37.5  ガンマ(0.1) |  |  |
|  | 2 | ベータ  **8.0**(5番人気)  470kg(-2)  owner | 牝4/栗  56.0kg  西村 淳也 | 2026年8月2日  中京  1勝クラス  4着  14頭2番4番人気  西村 淳也  56.0kg  1900ダ  2:01.0  良  472kg  3F 38.0  デルタ(0.6) |  |  |  |
|  | 3 | スクラッチ  **20.0**(8番人気)  480kg(0) owner | 牡5/鹿 58.0kg 騎手 | 取消 |  |  |  |
"""

PROFILE1 = """\
| 2026年10月17日 | 京都 | 3歳上1勝クラス | ダ1800 | 良 | 12 | 2 | 1 | 武 豊 | 57 | 500 | 1:51.0 | 105 | (ベータ) |
| 2026年9月1日 | 阪神 | 3歳上1勝クラス | ダ1800 | 良 | 12 | 2 | 2 | 武 豊 | 57 | 496 | 1:52.0 |  | ベータ |
| 2026年7月1日 | 京都 | 3歳未勝利 | ダ1800 | 良 | 10 | 1 | 1 | 武 豊 | 57 | 492 | 1:53.0 |  | (ガンマ) |
"""

PROFILE2 = """\
| 2026年8月2日 | 中京 | 3歳上1勝クラス | ダ1900 | 良 | 14 | 4 | 4 | 西村 淳也 | 56 | 472 | 2:01.0 |  | デルタ |
| 2026年5月1日 | 京都 | 4歳上1勝クラス | ダ1800 | 良 | 10 | 6 | 6 | 西村 淳也 | 56 | 474 | 1:54.0 |  | エコー |
"""


class PrepareSnapshotTests(unittest.TestCase):
    def fixture(self):
        return {
            "race": {
                "race_id": "2026-10-17-KYOTO-07",
                "date": "2026-10-17",
                "venue": "京都",
                "race_number": 7,
                "age_scope": "3yo+",
                "scheduled_start_jst": "2026-10-17T13:15:00+09:00",
                "target": {"surface": "ダ", "distance_m": 1800, "class_rank": 1},
            },
            "card": {"url": "https://jra/card", "text": CARD},
            "profiles": {
                "1": {"url": "https://jra/horse1", "text": PROFILE1},
                "2": {"url": "https://jra/horse2", "text": PROFILE2},
                "3": {"url": "https://jra/horse3", "text": "unused"},
            },
        }

    def test_builds_race_input_odds_and_meta(self):
        race, odds, meta = prepare(self.fixture(), "2026-10-17T12:55:00+09:00")
        self.assertEqual([h["number"] for h in race["horses"]], [1, 2])
        self.assertEqual([h["career_starts_before_target"] for h in race["horses"]], [2, 2])
        self.assertEqual(
            odds["horses"],
            [{"number": 1, "win_odds": 4.2}, {"number": 2, "win_odds": 8.0}],
        )
        self.assertEqual(meta["scratched_or_excluded_numbers"], [3])
        self.assertFalse(meta["uses_target_race_results"])

    def test_filters_target_date_result_from_profile(self):
        race, _, _ = prepare(self.fixture(), "2026-10-17T12:55:00+09:00")
        self.assertEqual(
            [x["date"] for x in race["horses"][0]["full_history_before_target"]],
            ["2026-09-01", "2026-07-01"],
        )

    def test_parses_latest_start_race_name_class_and_margin(self):
        race, _, _ = prepare(self.fixture(), "2026-10-17T12:55:00+09:00")
        latest = race["horses"][0]["last4"][0]
        self.assertEqual(latest["race_name"], "1勝クラス")
        self.assertEqual(latest["class_rank"], 1)
        self.assertEqual(latest["margin_sec"], 0.2)

    def test_missing_profile_for_active_horse_fails(self):
        capture = self.fixture()
        del capture["profiles"]["2"]
        with self.assertRaisesRegex(ValueError, "missing_profile:2"):
            prepare(capture, "2026-10-17T12:55:00+09:00")

    def test_missing_current_odds_fails(self):
        capture = self.fixture()
        capture["card"]["text"] = capture["card"]["text"].replace(
            "ベータ  **8.0**", "ベータ  **--**"
        )
        with self.assertRaisesRegex(ValueError, "missing_current_win_odds:2"):
            prepare(capture, "2026-10-17T12:55:00+09:00")

    def test_post_time_snapshot_fails(self):
        with self.assertRaisesRegex(ValueError, "snapshot_not_prerace"):
            prepare(self.fixture(), "2026-10-17T13:15:00+09:00")

    def test_non_kyoto_fails(self):
        capture = self.fixture()
        capture["race"]["venue"] = "東京"
        with self.assertRaisesRegex(ValueError, "ineligible_venue"):
            prepare(capture, "2026-10-17T12:55:00+09:00")


if __name__ == "__main__":
    unittest.main()
