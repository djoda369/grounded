import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.api import add_project_documents_payload, analyze_payload, analyze_project_payload
from core.phase1 import Phase1Analyzer
from core.phase1.storage import Phase1ProjectStore

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


class Phase1ProjectStorageTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "gaia_phase1.db"
        self.store = Phase1ProjectStore(self.db_path)
        self.analyzer = Phase1Analyzer()
        self.env_patch = patch.dict("os.environ", {"GAIA_LLM_EXTRACTION": "disabled"})
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_creates_lists_and_loads_project_bundle(self):
        project = self.store.create_project("Yoplait UK", "Yoplait UK", "Yoplait")

        projects = self.store.list_projects()
        bundle = self.store.get_project_bundle(project["id"])

        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "Yoplait UK")
        self.assertEqual(bundle["project"]["company_name"], "Yoplait UK")
        self.assertEqual(bundle["documents"], [])
        self.assertIsNone(bundle["current_analysis"])

    def test_stores_and_dedupes_documents_by_checksum(self):
        project = self.store.create_project("Yoplait UK", "Yoplait UK")
        payload = {
            "documents": [
                {
                    "source": "note-a.txt",
                    "kind": "txt",
                    "text": "Parents need transparent nutrition proof. Reduce emissions by 2030.",
                },
                {
                    "source": "note-b.txt",
                    "kind": "txt",
                    "text": "Parents need transparent nutrition proof. Reduce emissions by 2030.",
                },
            ]
        }

        first = add_project_documents_payload(project["id"], payload, self.store, self.analyzer)
        second = add_project_documents_payload(project["id"], payload, self.store, self.analyzer)

        self.assertEqual(len(first["documents"]), 1)
        self.assertEqual(len(second["documents"]), 1)
        self.assertNotIn("text", second["documents"][0])
        self.assertEqual(second["documents"][0]["source"], "note-a.txt")

    def test_runs_stored_project_analysis_and_marks_one_current(self):
        project = self.store.create_project("Yoplait UK", "Yoplait UK")
        add_project_documents_payload(
            project["id"],
            {
                "documents": [
                    {
                        "source": "report.txt",
                        "kind": "txt",
                        "text": (
                            "Yoplait parents need nutrition proof at shelf. "
                            "The sustainability goal is to reduce packaging waste by 2030."
                        ),
                    }
                ]
            },
            self.store,
            self.analyzer,
        )

        first = analyze_project_payload(project["id"], {}, self.store, self.analyzer)
        second = analyze_project_payload(
            project["id"],
            {"context": "Add calcium and vitamin D claims to the activation evidence."},
            self.store,
            self.analyzer,
        )
        current = self.store.get_current_analysis(project["id"])

        with sqlite3.connect(self.db_path) as connection:
            current_count = connection.execute(
                "SELECT COUNT(*) FROM project_analyses WHERE project_id = ? AND is_current = 1",
                (project["id"],),
            ).fetchone()[0]

        self.assertNotEqual(first["analysis_id"], second["analysis_id"])
        self.assertEqual(current["id"], second["analysis_id"])
        self.assertEqual(current_count, 1)
        self.assertIn("summary", second["analysis"]["iag"])
        self.assertEqual(second["analysis"]["contract_version"], "phase1.structured.v1")
        self.assertTrue(STRUCTURED_KEYS.issubset(second["analysis"].keys()))
        self.assertTrue(STRUCTURED_KEYS.issubset(current["analysis"].keys()))

    def test_saves_and_reloads_ui_state_json(self):
        project = self.store.create_project("Yoplait UK", "Yoplait UK")
        self.store.save_ui_state(
            project["id"],
            {
                "profile": {"market": "Yoplait UK"},
                "gaps": {"summary": {"confidence": 88}},
                "goals": [{"id": "goal-1", "title": "Nutrition proof"}],
                "recommendation": {"title": "IAG Sprint"},
                "workshop": {"consumer": [{"stage": "Evaluation", "selected": True}]},
                "job_to_be_done": "Prove child nutrition impact.",
                "active_page": "fiveC",
            },
        )

        reloaded = Phase1ProjectStore(self.db_path).get_ui_state(project["id"])

        self.assertEqual(reloaded["profile"]["market"], "Yoplait UK")
        self.assertEqual(reloaded["gaps"]["summary"]["confidence"], 88)
        self.assertEqual(reloaded["goals"][0]["id"], "goal-1")
        self.assertEqual(reloaded["workshop"]["consumer"][0]["stage"], "Evaluation")
        self.assertEqual(reloaded["active_page"], "fiveC")

    def test_legacy_analyze_payload_still_works(self):
        result = analyze_payload(
            {
                "company_name": "Yoplait UK",
                "text": "Parents need nutrition proof. The goal is to reduce carbon by 2030.",
            },
            self.analyzer,
        )

        self.assertEqual(result["company_name"], "Yoplait UK")
        self.assertIn("company", result["five_c"])


if __name__ == "__main__":
    unittest.main()
