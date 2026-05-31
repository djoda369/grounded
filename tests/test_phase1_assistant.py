import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from backend.api import Phase1APIHandler, add_project_documents_payload, analyze_project_payload
from core.phase1 import Phase1Analyzer
from core.phase1.contract import StructuredPhase1ContractBuilder
from core.phase1.storage import Phase1ProjectStore


class Phase1AssistantEndpointTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "gaia_phase1.db"
        self.store = Phase1ProjectStore(self.db_path)
        self.analyzer = Phase1Analyzer()
        self.env_patch = patch.dict(os.environ, {"OPENAI_API_KEY": ""})
        self.env_patch.start()

        handler = type(
            "TestPhase1APIHandler",
            (Phase1APIHandler,),
            {
                "store": self.store,
                "analyzer": self.analyzer,
                "contract_builder": StructuredPhase1ContractBuilder(),
            },
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_assistant_endpoint_returns_400_without_message(self):
        status, body = self.post_json("/api/phase1/assistant", {"project_id": "missing-message"})

        self.assertEqual(status, 400)
        self.assertIn("message", body["error"])

    def test_assistant_endpoint_returns_400_without_project_id(self):
        status, body = self.post_json("/api/phase1/assistant", {"message": "What is the biggest IAG risk?"})

        self.assertEqual(status, 400)
        self.assertIn("project_id", body["error"])

    def test_assistant_endpoint_returns_404_for_unknown_project(self):
        status, body = self.post_json(
            "/api/phase1/assistant",
            {"project_id": "unknown-project", "message": "What is the biggest IAG risk?"},
        )

        self.assertEqual(status, 404)
        self.assertIn("was not found", body["error"])

    def test_assistant_endpoint_returns_400_without_current_analysis(self):
        project = self.store.create_project("Yoplait UK", "Yoplait UK")

        status, body = self.post_json(
            "/api/phase1/assistant",
            {"project_id": project["id"], "message": "What is the biggest IAG risk?"},
        )

        self.assertEqual(status, 400)
        self.assertIn("current Phase 1 analysis", body["error"])

    def test_assistant_endpoint_returns_grounded_fallback_answer(self):
        project = self.store.create_project("Yoplait UK", "Yoplait UK")
        add_project_documents_payload(
            project["id"],
            {
                "documents": [
                    {
                        "source": "report.txt",
                        "kind": "txt",
                        "text": (
                            "Yoplait parents need transparent nutrition proof at shelf. "
                            "Culture is shifting toward trust, simplicity, and proof in children's dairy. "
                            "The sustainability goal is to reduce packaging waste by 30% by 2030."
                        ),
                    }
                ]
            },
            self.store,
            self.analyzer,
        )
        analyze_project_payload(project["id"], {}, self.store, self.analyzer)

        status, body = self.post_json(
            "/api/phase1/assistant",
            {
                "project_id": project["id"],
                "message": "What is the biggest IAG risk?",
                "history": [{"role": "user", "content": "Use the saved evidence only."}],
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(set(body), {"answer", "sources", "confidence", "grounding_status", "suggested_followups"})
        self.assertIn("5C and IAG", body["answer"])
        self.assertGreaterEqual(body["confidence"], 35)
        self.assertEqual(body["grounding_status"], "grounded")
        self.assertTrue(body["sources"])
        self.assertTrue(all({"source", "excerpt", "module"}.issubset(source) for source in body["sources"]))

    def post_json(self, path: str, payload: dict):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
