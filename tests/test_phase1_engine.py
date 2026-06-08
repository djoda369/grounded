import json
import base64
import tempfile
import unittest
from pathlib import Path

from core.phase1 import Phase1Analyzer
from core.phase1.assistant import GroundedAssistant
from core.phase1.ingestion import ReportIngestionPipeline, normalize_text
from backend.api import analyze_payload
from backend.api import onboard_payload, suggest_competitors_payload
from core.phase1.source_collector import (
    FetchResult,
    collect_sources,
    extract_html,
    validate_public_website_url,
)


def fake_fetcher(pages):
    def fetch(url: str) -> FetchResult:
        if url not in pages:
            return FetchResult(url=url, status=404, content_type="text/html", body="")
        return FetchResult(url=url, status=200, content_type="text/html", body=pages[url])

    return fetch


class Phase1EngineTest(unittest.TestCase):
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

    def test_url_validation_requires_public_http_url(self):
        self.assertEqual(validate_public_website_url("example.com"), "https://example.com")
        with self.assertRaises(ValueError):
            validate_public_website_url("ftp://example.com")
        with self.assertRaises(ValueError):
            validate_public_website_url("http://127.0.0.1:8787")
        with self.assertRaises(ValueError):
            validate_public_website_url("http://localhost")

    def test_html_text_extraction_returns_title_text_and_links(self):
        extracted = extract_html(
            """
            <html><head><title>Acme Purpose</title><style>.x{}</style></head>
            <body><h1>Purpose</h1><p>Acme makes low-waste dairy for families.</p>
            <a href="/about">About us</a><script>ignore()</script></body></html>
            """
        )

        self.assertEqual(extracted["title"], "Acme Purpose")
        self.assertIn("low-waste dairy", extracted["text"])
        self.assertEqual(extracted["links"][0], ("/about", "About us"))

    def test_source_collection_crawls_same_domain_with_limits_and_dedupes(self):
        long_copy = " ".join(["Acme dairy purpose sustainability competitors include Danone and Muller."] * 20)
        pages = {
            "https://acme.test/": f"""
                <title>Acme Dairy</title><p>{long_copy}</p>
                <a href="/about">About</a>
                <a href="/about#team">Duplicate about</a>
                <a href="/products">Products</a>
                <a href="/careers">Careers</a>
            """,
            "https://acme.test/about": f"<title>About Acme</title><p>{long_copy}</p>",
            "https://acme.test/products": f"<title>Acme Products</title><p>{long_copy}</p>",
            "https://acme.test/careers": f"<title>Acme Careers</title><p>{long_copy}</p>",
        }

        ledger = collect_sources(
            "https://acme.test/",
            {"maxSources": 3, "enabledSourceTypes": {"website": True}},
            fetcher=fake_fetcher(pages),
        )

        ok_urls = [entry["url"] for entry in ledger if entry["status"] == "ok"]
        self.assertEqual(len(ok_urls), 3)
        self.assertIn("https://acme.test/about", ok_urls)
        self.assertEqual(len(ok_urls), len(set(ok_urls)))

    def test_source_collection_records_skipped_sources(self):
        long_copy = " ".join(["Acme sustainability purpose."] * 20)
        ledger = collect_sources(
            "https://acme.test/",
            {
                "maxSources": 3,
                "enabledSourceTypes": {
                    "website": True,
                    "search": True,
                    "reviews": True,
                    "reddit": True,
                },
            },
            fetcher=fake_fetcher({"https://acme.test/": f"<title>Acme</title><p>{long_copy}</p>"}),
        )

        skipped = [entry for entry in ledger if entry["status"] == "skipped"]
        self.assertGreaterEqual(len(skipped), 3)
        self.assertTrue(all(entry.get("error") for entry in skipped))

    def test_source_collection_applies_limit_across_social_links(self):
        long_copy = " ".join(["Acme sustainability purpose and products."] * 20)
        pages = {
            "https://acme.test/": f"""
                <title>Acme</title><p>{long_copy}</p>
                <a href="/about">About</a>
                <a href="/products">Products</a>
                <a href="https://www.youtube.com/acme">YouTube</a>
            """,
            "https://acme.test/about": f"<title>About</title><p>{long_copy}</p>",
            "https://acme.test/products": f"<title>Products</title><p>{long_copy}</p>",
            "https://www.youtube.com/acme": f"<title>Acme YouTube</title><p>{long_copy}</p>",
        }

        ledger = collect_sources(
            "https://acme.test/",
            {
                "maxSources": 3,
                "enabledSourceTypes": {
                    "website": True,
                    "social_links": True,
                },
            },
            fetcher=fake_fetcher(pages),
        )

        self.assertEqual(
            len([entry for entry in ledger if entry["status"] == "ok"]),
            3,
        )

    def test_onboarding_api_payload_collects_sources_and_runs_analysis(self):
        long_copy = " ".join(
            [
                "Acme believes in family nutrition and low waste dairy.",
                "Competitors include Danone and Muller.",
                "The sustainability goal is to reduce emissions by 2030.",
            ]
            * 15
        )

        original_collect = __import__("backend.api", fromlist=["collect_sources"]).collect_sources
        try:
            import backend.api as api

            api.collect_sources = lambda *args, **kwargs: [
                {
                    "url": "https://acme.test/",
                    "type": "website",
                    "title": "Acme Dairy",
                    "fetched_at": "2026-01-01T00:00:00+00:00",
                    "status": "ok",
                    "excerpt": long_copy,
                    "error": "",
                }
            ]
            result = onboard_payload({"website_url": "https://acme.test/", "source_settings": {"maxSources": 3}})
        finally:
            api.collect_sources = original_collect

        self.assertEqual(result["profile"]["market"], "Acme Dairy")
        self.assertEqual(result["source_ledger"][0]["status"], "ok")
        self.assertIn("summary", result["analysis"]["iag"])

    def test_competitor_suggestion_parses_source_names(self):
        result = suggest_competitors_payload(
            {
                "website_url": "https://acme.test/",
                "profile": {"brand": "Acme", "market": "Acme Dairy"},
                "source_ledger": [
                    {
                        "url": "https://acme.test/",
                        "status": "ok",
                        "excerpt": "Acme competes alongside Danone, Muller Group, and Arla Foods in dairy.",
                    }
                ],
            }
        )

        names = [item["name"] for item in result["suggestions"]]
        self.assertIn("Danone", names)
        self.assertTrue(all(item["selected"] is False for item in result["suggestions"]))


if __name__ == "__main__":
    unittest.main()
