import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RequestedSiteContentTests(unittest.TestCase):
    def test_local_news_is_merged_with_sheet_news(self):
        service = (ROOT / "js" / "SheetServices.js").read_text(encoding="utf-8")
        self.assertIn("/imsi/data/news-local.json", service)
        self.assertRegex(service, r"async function getNews\(\)[\s\S]+newsPromise")

        records = json.loads((ROOT / "data" / "news-local.json").read_text(encoding="utf-8"))
        by_id = {row["News_ID"]: row for row in records}
        self.assertEqual({"NEWS_005", "NEWS_006"}, set(by_id))
        self.assertEqual("2026-09-28", by_id["NEWS_005"]["Date"])
        self.assertEqual("2026-10-01", by_id["NEWS_006"]["Date"])
        self.assertIn("NeurIPS 2026", by_id["NEWS_005"]["Title"])
        self.assertIn("2027년 1월", by_id["NEWS_006"]["Title"])

    def test_news_detail_pages_have_required_content_and_no_access_codes(self):
        neurips = (ROOT / "news" / "NEWS-005" / "index.html").read_text(encoding="utf-8")
        interview = (ROOT / "news" / "NEWS-006" / "index.html").read_text(encoding="utf-8")
        records = json.loads((ROOT / "data" / "news-local.json").read_text(encoding="utf-8"))
        by_id = {row["News_ID"]: row for row in records}
        neurips += by_id["NEWS_005"]["Content"]
        interview += by_id["NEWS_006"]["Content"]

        self.assertIn("Auditing Correlated Failures in Frozen-Feature", neurips)
        self.assertIn("Auditing Capsule Vision 2024", neurips)
        self.assertIn("Eunseob Choi", neurips)
        self.assertIn("Nam-Joon Kim", neurips)
        self.assertIn("1nDVguFzOGEUAD3mXIiqLD5wUfmn01ipk", neurips)
        self.assertIn("1WR75Het4xBgIfQZe_TeRUDbAVgiTyYD3", neurips)

        self.assertIn("2026년 12월 4일", interview)
        self.assertIn("참석 확정자에게 별도 안내", interview)
        self.assertIn("70편 이상", interview)
        self.assertIn("MICCAI", interview)
        self.assertIn("ISBI", interview)
        self.assertNotIn("입구비번", interview)
        self.assertNotIn("2층입구비번", interview)
        self.assertEqual(1, interview.count("출입 비밀번호는 참석 확정자에게 별도 안내"))
        self.assertIsNone(re.search(r"\b\d{4,6}\*", interview))

    def test_undergraduate_interns_have_exact_requested_order(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        section = home.split("Undergraduate Interns", 1)[1].split("Advisors", 1)[0]
        names = re.findall(r"<h2><a[^>]*>([^<]+)</a></h2>", section)
        self.assertEqual(
            [
                "Eunseob Choi",
                "Yului Jeong",
                "Hyunsu Go",
                "Jooyoung Bae",
                "Anna Jung",
                "Giseong Hwang",
            ],
            names,
        )
        self.assertNotIn("Hyeonseok Jung", section)

    def test_yului_profile_has_new_portrait_and_verified_activity_links(self):
        profile = (ROOT / "authors" / "undergraduate_interns" / "yului-jeong" / "index.html").read_text(encoding="utf-8")
        required = [
            "2025 Startup Item Competition",
            "Excellence Award",
            "GCSC 2026",
            "Global Track Silver Award",
            "도서관을 벗어난 대학생의 무모한 도전기",
            "https://www.snunews.com/news/articleView.html?idxno=34431",
            "AICAS 2026",
            "Ha Long Bay",
            "APCCAS 2026",
            "scheduled",
            "Fukuoka",
            "Hamsters",
            "Malatang",
            "Pink",
        ]
        for text in required:
            self.assertIn(text, profile)
        self.assertRegex(profile, r"\bshe\b")

        portrait = ROOT / "authors" / "undergraduate_interns" / "yului-jeong" / "avatar.png"
        with portrait.open("rb") as image:
            self.assertEqual(b"\x89PNG\r\n\x1a\n", image.read(8))
            length = struct.unpack(">I", image.read(4))[0]
            self.assertEqual(13, length)
            self.assertEqual(b"IHDR", image.read(4))
            width, height = struct.unpack(">II", image.read(8))
        self.assertEqual((512, 512), (width, height))


if __name__ == "__main__":
    unittest.main()
