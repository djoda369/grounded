import os
import unittest
from unittest.mock import patch

from backend.api import analyze_payload
from core.phase1.llm_extraction import Phase1LLMExtractor


class FakeLLMClient:
    model = "fake-model"

    def __init__(self, response=None, error=None, has_key=True):
        self.response = response or {}
        self.error = error
        self.has_key = has_key

    def has_api_key(self):
        return self.has_key

    def json_chat(self, messages):
        if self.error:
            raise self.error
        return self.response


class Phase1LLMExtractionTest(unittest.TestCase):
    def test_without_key_uses_deterministic_metadata(self):
        extractor = Phase1LLMExtractor(FakeLLMClient(has_key=False))

        result = analyze_payload(
            {
                "company_name": "Yoplait UK",
                "text": "Parents need nutrition proof. The goal is to reduce packaging by 2030.",
            },
            llm_extractor=extractor,
        )

        self.assertEqual(result["analysis_mode"], "deterministic")
        self.assertEqual(result["llm_extraction_status"], "skipped_no_key")
        self.assertIn("executive_summary", result)

    def test_valid_llm_json_enriches_contract(self):
        extractor = Phase1LLMExtractor(
            FakeLLMClient(
                response={
                    "company_bbp": {
                        "belief": "LLM belief grounded in provided evidence.",
                        "evidence": [
                            {
                                "title": "Evidence 1",
                                "summary": "Parents need nutrition proof.",
                                "facts": ["Source evidence exists."],
                                "sources": ["inline:1"],
                                "signals": ["Evidence score: 80%"],
                                "implications": ["Use in BBP."],
                            }
                        ],
                    },
                    "recommendation": {
                        "title": "LLM Activation Sprint",
                        "outcomes": ["Name action, proof point, and measurable outcome."],
                    },
                    "executive_summary": "LLM executive summary.",
                }
            )
        )

        result = analyze_payload(
            {
                "company_name": "Yoplait UK",
                "text": "Parents need nutrition proof. The goal is to reduce packaging by 2030.",
            },
            llm_extractor=extractor,
        )

        self.assertEqual(result["analysis_mode"], "llm_enriched")
        self.assertEqual(result["llm_extraction_status"], "success")
        self.assertEqual(result["company_bbp"]["belief"], "LLM belief grounded in provided evidence.")
        self.assertEqual(result["recommendation"]["title"], "LLM Activation Sprint")
        self.assertEqual(result["executive_summary"], "LLM executive summary.")

    def test_invalid_llm_call_falls_back_without_crashing(self):
        extractor = Phase1LLMExtractor(FakeLLMClient(error=RuntimeError("bad json")))

        result = analyze_payload(
            {
                "company_name": "Yoplait UK",
                "text": "Parents need nutrition proof. The goal is to reduce packaging by 2030.",
            },
            llm_extractor=extractor,
        )

        self.assertEqual(result["analysis_mode"], "deterministic")
        self.assertEqual(result["llm_extraction_status"], "error_fallback")
        self.assertIn("llm_error", result)

    def test_disabled_env_skips_llm_even_when_client_has_key(self):
        with patch.dict(os.environ, {"GAIA_LLM_EXTRACTION": "disabled"}):
            extractor = Phase1LLMExtractor(FakeLLMClient(response={"executive_summary": "Should not be used"}))
            result = analyze_payload(
                {
                    "company_name": "Yoplait UK",
                    "text": "Parents need nutrition proof. The goal is to reduce packaging by 2030.",
                },
                llm_extractor=extractor,
            )

        self.assertEqual(result["llm_extraction_status"], "skipped_disabled")
        self.assertNotEqual(result["executive_summary"], "Should not be used")


if __name__ == "__main__":
    unittest.main()
