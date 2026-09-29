import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RequestedSiteContentTests(unittest.TestCase):
    def test_publication_pages_load_shared_adapter_before_sheet_service(self):
        for path in ROOT.rglob("*.html"):
            if "_site" in path.parts:
                continue
            source = path.read_text(encoding="utf-8")
            if "/imsi/js/SheetServices.js" not in source:
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("/imsi/js/publication-data.js", source)
                self.assertLess(
                    source.index("/imsi/js/publication-data.js"),
                    source.index("/imsi/js/SheetServices.js"),
                )

    def test_publication_archive_has_result_count_and_shared_actions(self):
        source = (ROOT / "publication" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="pub-result-count"', source)
        self.assertIn('aria-live="polite"', source)
        self.assertIn("Publications.actions", source)
        self.assertNotIn("'Paper_Link', 'Paper Link', 'paper_link', 'Column_5'", source)

    def test_advisor_profiles_link_to_official_hospital_pages(self):
        pa_hong = (ROOT / "authors/advisors/pa-hong/index.html").read_text(encoding="utf-8")
        won_jae = (ROOT / "authors/advisors/won-jae-lee/index.html").read_text(encoding="utf-8")
        self.assertIn("https://smc.skku.edu/doctor/main/main.do?mId=1&amp;medDrSeq=274", pa_hong)
        self.assertIn("https://smc.skku.edu/doctor/main/main.do?mId=1&amp;medDrSeq=286", won_jae)
        self.assertIn("Official hospital profile", pa_hong)
        self.assertIn("Official hospital profile", won_jae)

    def test_local_news_is_merged_with_sheet_news(self):
        service = (ROOT / "js" / "SheetServices.js").read_text(encoding="utf-8")
        self.assertIn("/imsi/data/news-local.json", service)
        self.assertRegex(service, r"async function getNews\(\)[\s\S]+newsPromise")

        records = json.loads((ROOT / "data" / "news-local.json").read_text(encoding="utf-8"))
        by_id = {row["News_ID"]: row for row in records}
        self.assertEqual({"NEWS_005", "NEWS_006", "NEWS_007", "NEWS_008"}, set(by_id))
        self.assertEqual("2026-09-28", by_id["NEWS_005"]["Date"])
        self.assertEqual("2026-10-01", by_id["NEWS_006"]["Date"])
        self.assertIn("NeurIPS 2026", by_id["NEWS_005"]["Title"])
        self.assertIn("2027년 1월", by_id["NEWS_006"]["Title"])

    def test_niscis_and_internship_document_news_have_downloadable_attachments(self):
        records = json.loads((ROOT / "data" / "news-local.json").read_text(encoding="utf-8"))
        by_id = {row["News_ID"]: row for row in records}

        niscis = by_id["NEWS_007"]
        self.assertEqual("2026-10-02", niscis["Date"])
        self.assertEqual("차세대반도체 혁신융합학회(NISCIS) 개최 안내", niscis["Title"])
        self.assertIn("2026년 10월 23일(금) 18:00", niscis["Content"])
        self.assertIn("2026년 11월 19일(목)", niscis["Content"])
        self.assertIn("광주 김대중컨벤션센터", niscis["Content"])
        self.assertIn("구두 발표: 09:45–11:00", niscis["Content"])
        self.assertIn("포스터 발표: 11:10–12:00", niscis["Content"])
        self.assertIn("발표 시간은 10분", niscis["Content"])
        self.assertIn("교통비·숙박비·일비·식비", niscis["Content"])
        self.assertIn("마이크로디그리", niscis["Content"])
        self.assertNotIn("식비, 일비, 개인 경비", niscis["Content"])
        self.assertIn("https://www.disu.ac.kr/community/notice", niscis["Content"])
        self.assertIn("export=download&id=1Tcc6k6ihFjLMeqrqmbc9JN5J3eIENp--", niscis["Content"])
        self.assertIn("153DXOSVmakAMNEQSDJW3O2KI95zYM-XR/export?format=docx", niscis["Content"])

        confirmation = by_id["NEWS_008"]
        self.assertEqual("2026-10-05", confirmation["Date"])
        self.assertEqual("2026학년도 차세대반도체 인턴십 근무확인서 발급 안내", confirmation["Title"])
        self.assertIn("1학기·하계·2학기·동계", confirmation["Content"])
        self.assertIn("export=download&id=1sjyScTF0As04PabNxT66LrrexFZAEk23", confirmation["Content"])

        for news_id in ("NEWS-007", "NEWS-008"):
            page = ROOT / "news" / news_id / "index.html"
            self.assertTrue(page.is_file(), news_id)

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
        self.assertNotIn("Nam-Joon Kim†", neurips)
        self.assertIn("1nDVguFzOGEUAD3mXIiqLD5wUfmn01ipk", neurips)
        self.assertIn("1WR75Het4xBgIfQZe_TeRUDbAVgiTyYD3", neurips)
        for route in [
            "/imsi/authors/undergraduate_interns/eunseob-choi/",
            "/imsi/authors/research_assistants/kyeonghun-kim/",
            "/imsi/authors/investigators/hyukjae-lee/",
            "/imsi/authors/investigators/nam-joon-kim/",
        ]:
            self.assertIn(route, neurips)

        self.assertIn("2026년 12월 4일", interview)
        self.assertIn("참석 확정자에게 별도 안내", interview)
        self.assertIn("70편 이상", interview)
        self.assertIn("MICCAI", interview)
        self.assertIn("ISBI", interview)
        self.assertIn("http://capp.snu.ac.kr/imsi/", interview)
        for activity in [
            "2026년 10월 28–30일",
            "2026년 11월 18–19일",
            "2026년 11월 27–28일",
            "2027년 3월 12–18일",
        ]:
            self.assertIn(activity, interview)
        for institution in [
            "KBS",
            "NVIDIA Korea",
            "NVIDIA Singapore",
            "NVIDIA San Jose",
            "Google",
            "Salesforce",
            "Uber",
            "Microsoft",
            "Stanford University",
            "UC Berkeley",
            "Samsung Medical Center",
        ]:
            self.assertIn(institution, interview)
        for achievement in [
            "MICCAI Workshop 논문 2편",
            "ISBI 구두 발표 논문 3편",
            "NeurIPS 2026 채택 논문 2편",
            "CVPR 논문 1편",
            "IEEE MedAI 논문 1편",
            "AICAS 논문 4편",
            "APCCAS 논문 4편",
            "GTC 포스터 5편",
            "AAAI Workshop 논문 1편",
        ]:
            self.assertIn(achievement, interview)
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
                "Minjun Yoo",
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

    def test_minjun_profile_has_canonical_route_projects_and_verified_media(self):
        profile_path = ROOT / "authors" / "undergraduate_interns" / "minjun-yoo" / "index.html"
        self.assertTrue(profile_path.exists())
        profile = profile_path.read_text(encoding="utf-8")
        required = [
            "Minjun Yoo",
            "yoodison@snu.ac.kr",
            "Mathematics Education",
            "March 2023",
            "March 2028",
            "Geuneulro",
            "https://www.instagram.com/geuneulro/",
            "https://play.google.com/store/apps/details?id=com.unmet.ttubeok",
            "https://apps.apple.com/kr/app/",
            "3bfa4fa76c2f81c49cfde2e17bfc43dd",
            "youquizontheblock",
            "news.sbs.co.kr",
            "KBS",
        ]
        for text in required:
            self.assertIn(text, profile)

        mapping = json.loads((ROOT / "data" / "author-profiles.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "/imsi/authors/undergraduate_interns/minjun-yoo/",
            mapping["Minjun Yoo"],
        )

        portrait = ROOT / "authors" / "undergraduate_interns" / "minjun-yoo" / "avatar.png"
        with portrait.open("rb") as image:
            self.assertEqual(b"\x89PNG\r\n\x1a\n", image.read(8))

    def test_research_profiles_have_highlights_orcid_and_service_sections(self):
        eunseob = (ROOT / "authors" / "undergraduate_interns" / "eunseob-choi" / "index.html").read_text(encoding="utf-8")
        kyeonghun = (ROOT / "authors" / "research_assistants" / "kyeonghun-kim" / "index.html").read_text(encoding="utf-8")
        youngung = (ROOT / "authors" / "research_assistants" / "youngung-han" / "index.html").read_text(encoding="utf-8")

        for profile in [eunseob, kyeonghun]:
            self.assertIn("Two NeurIPS 2026 Papers Accepted", profile)
            self.assertIn("/imsi/news/NEWS-005/", profile)

        self.assertIn("https://orcid.org/0009-0002-9405-8424", kyeonghun)
        self.assertIn("https://orcid.org/0009-0008-0596-8367", youngung)

        required_kyeonghun = [
            "3D-LLDM",
            "first author",
            "ISBI 2026",
            "Stanford",
            "NVIDIA",
            "Samsung Medical Center",
            "Google",
            "Salesforce",
            "Uber",
            "Microsoft",
            "NeurIPS 2026: 2",
            "MICCAI Workshops: 2",
            "AAAI Workshop: 1",
            "ISBI oral papers: 3",
            "IEEE MedAI: 1",
            "AICAS oral papers: 3",
            "APCCAS papers: 4",
            "GTC posters: 3",
            "AACL-IJCNLP: 1",
            "10-3010471-0000",
            "Teaching Experience",
            "SK Telecom",
            "OUTTA",
            "HUN Company",
            "Kyobo Life",
            "Busan Metropolitan City",
            "Kookmin University",
            "Volunteering",
            "Korean Red Cross Blood Services",
            "https://www.redcross.or.kr/main/main.do",
            "NAVER Happy Bean",
            "https://www.navercorp.com/en/main",
            "October 8, 2020",
            "August 21, 2021",
            "data-fancybox=\"blood-donation-awards\"",
            "blood-donation-silver.png",
            "blood-donation-gold.png",
        ]
        for text in required_kyeonghun:
            self.assertIn(text, kyeonghun)

        for filename in ["blood-donation-silver.png", "blood-donation-gold.png"]:
            image_path = ROOT / "authors" / "research_assistants" / "kyeonghun-kim" / filename
            with image_path.open("rb") as image:
                self.assertEqual(b"\x89PNG\r\n\x1a\n", image.read(8))

    def test_kyeonghun_profile_uses_shared_normalized_publication_renderer(self):
        profile = (ROOT / "authors/research_assistants/kyeonghun-kim/index.html").read_text(encoding="utf-8")
        self.assertIn('data-author-publications="Kyeonghun Kim"', profile)
        self.assertIn('/imsi/js/author-publications.js', profile)
        self.assertNotIn("renderKyeonghunPublications", profile)
        self.assertNotIn("['Authors', 'Column_4']", profile)


if __name__ == "__main__":
    unittest.main()
