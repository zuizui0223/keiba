import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from v31_prepare_result import prepare


RESULT_TEXT = """\
# レース結果2026年10月18日（日曜）4回京都7日 7レース

発走時刻：**13時25分**

## 3歳以上1勝クラス

| 着順 | 枠 | 馬 番 | 馬名 | 性齢 | 負担 重量 | 騎手名 | タイム |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 |  | 4 | デルタ | 牡3 | 57.0 | 田口 貫太 | 1:52.0 |
| 2 |  | 1 | アルファ | 牡4 | 57.0 | 武 豊 | 1:52.1 |
| 3 |  | 2 | ベータ | 牝4 | 56.0 | 西村 淳也 | 1:52.3 |
| 4 |  | 3 | ガンマ | 牡5 | 58.0 | 幸 英明 | 1:52.5 |
"""


class PrepareOfficialResultTests(unittest.TestCase):
    def capture(self):
        return {
            "race_id": "2026-10-18-KYOTO-07",
            "source_url": "https://www.jra.go.jp/JRADB/accessS.html?CNAME=example",
            "observed_at_jst": "2026-10-18T13:35:00+09:00",
            "text": RESULT_TEXT,
        }

    def test_parses_official_jra_top3_and_provenance(self):
        result = prepare(self.capture())
        self.assertEqual(result["race_id"], "2026-10-18-KYOTO-07")
        self.assertEqual(result["top3"], [4, 1, 2])
        self.assertEqual(result["source"]["provider"], "JRA")
        self.assertEqual(result["source"]["url"], self.capture()["source_url"])
        self.assertEqual(
            result["source"]["text_sha256"],
            hashlib.sha256(RESULT_TEXT.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(result["source"]["observed_at_jst"], "2026-10-18T13:35:00+09:00")

    def test_rejects_non_jra_source(self):
        capture = self.capture()
        capture["source_url"] = "https://example.com/result"
        with self.assertRaisesRegex(ValueError, "non_jra_result_source"):
            prepare(capture)

    def test_rejects_race_number_mismatch(self):
        capture = self.capture()
        capture["race_id"] = "2026-10-18-KYOTO-08"
        with self.assertRaisesRegex(ValueError, "result_page_race_mismatch"):
            prepare(capture)

    def test_rejects_date_mismatch(self):
        capture = self.capture()
        capture["race_id"] = "2026-10-17-KYOTO-07"
        with self.assertRaisesRegex(ValueError, "result_page_race_mismatch"):
            prepare(capture)

    def test_rejects_missing_top3_row(self):
        capture = self.capture()
        capture["text"] = RESULT_TEXT.replace(
            "| 3 |  | 2 | ベータ | 牝4 | 56.0 | 西村 淳也 | 1:52.3 |\n", ""
        )
        with self.assertRaisesRegex(ValueError, "result_top3_incomplete"):
            prepare(capture)

    def test_rejects_naive_observed_time(self):
        capture = self.capture()
        capture["observed_at_jst"] = "2026-10-18T13:35:00"
        with self.assertRaisesRegex(ValueError, "naive_datetime:observed_at_jst"):
            prepare(capture)


if __name__ == "__main__":
    unittest.main()
