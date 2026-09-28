import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicationSchemaTests(unittest.TestCase):
    def test_normalizes_a_to_t_schema_and_actions(self):
        source = (ROOT / "js" / "publication-data.js").read_text(encoding="utf-8")
        for header in (
            "Pub_ID", "Year", "Title", "Venue_Name", "Authors", "Spacer",
            "Project_Link", "GDrive_Link", "arXiv_Link", "Paper_Link",
            "Venue_Link", "Code", "Model", "Poster_Link", "Slides_link",
            "Cite", "In Google Scholar", "Cited at Least Once", "Notes", "Remarks",
        ):
            self.assertIn(header, source)
        for label in ("Project", "GDrive", "arXiv", "Paper", "Venue", "Code", "Model", "Poster", "Slides", "Cite"):
            self.assertIn(f"label: '{label}'", source)

    def test_omits_empty_actions_and_filters_personal_token_only(self):
        source = (ROOT / "js" / "publication-data.js").read_text(encoding="utf-8")
        self.assertIn(".filter(action => action.url)", source)
        self.assertIn("\\bPERSONAL\\b", source)
        self.assertIn("isLabPublication", source)

    def test_sheet_service_normalizes_and_filters_publications(self):
        source = (ROOT / "js" / "SheetServices.js").read_text(encoding="utf-8")
        self.assertIn("Publications.normalize", source)
        self.assertIn("Publications.isLabPublication", source)


if __name__ == "__main__":
    unittest.main()
