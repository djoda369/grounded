import json
import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.phase1 import Phase1Analyzer
from core.phase1.assistant import GroundedAssistant
from core.phase1.ingestion import ReportIngestionPipeline, normalize_text
from backend.api import analyze_payload

STRUCTURED_KEYS = {
    "contract_version",
    "company_name",
    "documents",
    "company_bbp",
    "competitors",
    "culture",
    "consumer",
    "category",
    "sustainability",
    "iag",
    "recommendation",
    "five_c",
    "sustainability_goals",
    "assistant_system_prompt",
}


class Phase1EngineTest(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict("os.environ", {"GAIA_LLM_EXTRACTION": "disabled"})
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_ingestion_normalizes_and_dedupes_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.txt"
            duplicate = Path(directory) / "duplicate.txt"
            text = "Company purpose and nutrition commitment.\n\n\nReduce emissions by 30% by 2030."
            path.write_text(text, encoding="utf-8")
            duplicate.write_text(text, encoding="utf-8")

            documents = ReportIngestionPipeline().ingest_paths([path, duplicate])

        self.assertEqual(len(documents), 1)
        self.assertIn("Reduce emissions", documents[0].text)
        self.assertEqual(documents[0].kind, "txt")

    def test_json_ingestion_extracts_nested_strings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(
                json.dumps({"goals": [{"title": "Reduce carbon emissions by 20% by 2030"}]}),
                encoding="utf-8",
            )

            documents = ReportIngestionPipeline().ingest_paths([path])

        self.assertEqual(len(documents), 1)
        self.assertIn("Reduce carbon emissions", documents[0].text)

    def test_pdf_ingestion_extracts_scope_text_without_optional_dependency(self):
        path = Path(__file__).resolve().parents[1] / "Grounded-Development-Technical-Scope-of-Work.pdf"

        documents = ReportIngestionPipeline().ingest_paths([path])

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].kind, "pdf")
        self.assertIn("Phase 1 Deliverables", documents[0].text)

    def test_phase1_analysis_returns_stable_5c_iag_and_assistant_prompt(self):
        source = normalize_text(
            """
            Yoplait believes childhood nutrition is a critical window for calcium and vitamin D fortification.
            Parents compare yogurt brands at shelf and need transparent labels before purchase.
            Competitor brands focus on broad wellness and market positioning rather than child bone health.
            Culture is shifting toward trust, simplicity, and proof in children's dairy.
            The category need state is fortified yogurt that supports child bone health.
            The sustainability commitment is to reduce carbon emissions by 30% by 2030 and improve packaging circularity.
            """
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "yoplait_report.txt"
            path.write_text(source, encoding="utf-8")

            analysis = Phase1Analyzer().analyze_paths([path], "Yoplait UK")

        self.assertEqual(set(analysis.five_c), {"company", "competition", "culture", "consumer", "category"})
        self.assertGreaterEqual(analysis.five_c["category"].confidence, 60)
        self.assertGreaterEqual(len(analysis.sustainability_goals), 1)
        self.assertIn("summary", analysis.iag)
        self.assertIn("Grounded's 5C methodology", analysis.assistant_system_prompt)

    def test_assistant_offline_answer_uses_evidence(self):
        source = "Parents need nutrition proof. The sustainability goal is to reduce emissions by 2030."
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.txt"
            path.write_text(source, encoding="utf-8")

            analysis = Phase1Analyzer().analyze_paths([path], "Yoplait UK")
            answer = GroundedAssistant().deterministic_answer(analysis, "What is the gap?")

        self.assertIn("Yoplait UK", answer)
        self.assertIn("5C and IAG", answer)

    def test_phase1_api_payload_accepts_inline_text(self):
        result = analyze_payload(
            {
                "company_name": "Yoplait UK",
                "text": "Parents need transparent nutrition proof. The goal is to reduce packaging waste by 2030.",
            }
        )

        self.assertEqual(result["company_name"], "Yoplait UK")
        self.assertIn("company", result["five_c"])
        self.assertIn("summary", result["iag"])

    def test_phase1_api_payload_returns_structured_contract_with_legacy_fields(self):
        result = analyze_payload(
            {
                "company_name": "Acme Foods",
                "text": (
                    "Acme Foods believes healthy snacks need transparent proof. "
                    "Competitors include Danone UK and Arla Foods. "
                    "Parents need clear nutrition labels at purchase. "
                    "Culture is shifting toward trust and simple claims. "
                    "The category need state is fortified snack nutrition. "
                    "The sustainability goal is to reduce packaging waste by 30% by 2030."
                ),
            }
        )

        self.assertTrue(STRUCTURED_KEYS.issubset(result.keys()))
        self.assertEqual(result["contract_version"], "phase1.structured.v1")
        self.assertEqual(result["company_bbp"]["market"], "Acme Foods")
        self.assertGreaterEqual(len(result["competitors"]), 1)
        self.assertIn("goals", result["sustainability"])
        self.assertIn("nextSteps", result["iag"]["summary"])
        self.assertIn("five_c", result)
        self.assertIn("sustainability_goals", result)
        self.assertIn("assistant_system_prompt", result)

    def test_empty_evidence_returns_low_confidence_structured_objects(self):
        result = analyze_payload({"company_name": "Acme Foods", "text": ""})

        self.assertTrue(STRUCTURED_KEYS.issubset(result.keys()))
        self.assertLessEqual(result["company_bbp"]["confidence"], 45)
        self.assertEqual(result["competitors"][0]["name"], "Competitive whitespace")
        self.assertLessEqual(result["competitors"][0]["confidence"], 45)
        self.assertIn("No named competitors", result["competitors"][0]["evidence"][0]["summary"])
        self.assertLessEqual(result["sustainability"]["goals"][0]["confidence"], 45)
        self.assertTrue(result["culture"]["drivers"])
        self.assertTrue(result["consumer"]["stages"])
        self.assertTrue(result["category"]["need_states"])

    def test_phase1_api_payload_accepts_base64_upload(self):
        encoded = base64.b64encode(
            b"Parents need nutrition evidence. The goal is to reduce carbon emissions by 2030."
        ).decode("ascii")

        result = analyze_payload(
            {
                "company_name": "Yoplait UK",
                "documents": [{"source": "note.txt", "kind": "txt", "data_base64": encoded}],
            }
        )

        self.assertEqual(result["documents"][0]["kind"], "txt")
        self.assertIn("summary", result["iag"])


if __name__ == "__main__":
    unittest.main()
