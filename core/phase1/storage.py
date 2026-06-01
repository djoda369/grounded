from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core.phase1.schema import IngestedDocument

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "phase1" / "gaia_phase1.db"


class ProjectNotFoundError(ValueError):
    """Raised when a project-scoped operation cannot find the requested project."""


class Phase1ProjectStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    brand TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_analyzed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS project_documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    text TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE (project_id, checksum)
                );

                CREATE TABLE IF NOT EXISTS project_analyses (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    input_checksum TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_current INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_project_analyses_current
                    ON project_analyses(project_id, is_current);

                CREATE TABLE IF NOT EXISTS project_ui_state (
                    project_id TEXT PRIMARY KEY,
                    profile_json TEXT,
                    gaps_json TEXT,
                    goals_json TEXT,
                    recommendation_json TEXT,
                    workshop_json TEXT,
                    job_to_be_done TEXT,
                    active_page TEXT,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                """
            )
            self._ensure_column(connection, "project_ui_state", "workshop_json", "TEXT")

    def create_project(self, name: str, company_name: str, brand: str | None = None) -> dict[str, Any]:
        name = name.strip()
        company_name = company_name.strip()
        if not name:
            raise ValueError("Project name is required.")
        if not company_name:
            raise ValueError("Company name is required.")

        now = utc_now()
        project = {
            "id": uuid.uuid4().hex,
            "name": name,
            "company_name": company_name,
            "brand": brand.strip() if isinstance(brand, str) and brand.strip() else None,
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "last_analyzed_at": None,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (id, name, company_name, brand, status, created_at, updated_at, last_analyzed_at)
                VALUES (:id, :name, :company_name, :brand, :status, :created_at, :updated_at, :last_analyzed_at)
                """,
                project,
            )
        return project

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, company_name, brand, status, created_at, updated_at, last_analyzed_at
                FROM projects
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, company_name, brand, status, created_at, updated_at, last_analyzed_at
                FROM projects
                WHERE id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            raise ProjectNotFoundError(f"Project {project_id} was not found.")
        return dict(row)

    def project_exists(self, project_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
        return row is not None

    def update_project(self, project_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        self._require_project(project_id)
        allowed = {"name", "company_name", "brand", "status"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return self.get_project(project_id)

        for required in ("name", "company_name"):
            if required in updates and not str(updates[required]).strip():
                raise ValueError(f"{required} is required.")
        clean_updates = {
            key: (str(value).strip() if value is not None else None)
            for key, value in updates.items()
        }
        clean_updates["updated_at"] = utc_now()

        assignments = ", ".join(f"{key} = :{key}" for key in clean_updates)
        clean_updates["id"] = project_id
        with self._connect() as connection:
            connection.execute(
                f"UPDATE projects SET {assignments} WHERE id = :id",
                clean_updates,
            )
        return self.get_project(project_id)

    def get_project_bundle(self, project_id: str) -> dict[str, Any]:
        return {
            "project": self.get_project(project_id),
            "documents": self.list_documents(project_id),
            "current_analysis": self.get_current_analysis(project_id),
            "ui_state": self.get_ui_state(project_id),
        }

    def list_documents(self, project_id: str, include_text: bool = False) -> list[dict[str, Any]]:
        self._require_project(project_id)
        columns = "id, project_id, source, kind, checksum, metadata_json, created_at"
        if include_text:
            columns = "id, project_id, source, kind, text, checksum, metadata_json, created_at"
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT {columns}
                FROM project_documents
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [document_row_to_dict(row) for row in rows]

    def add_documents(self, project_id: str, documents: Iterable[IngestedDocument]) -> list[dict[str, Any]]:
        self._require_project(project_id)
        now = utc_now()
        with self._connect() as connection:
            for document in documents:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO project_documents
                        (id, project_id, source, kind, text, checksum, metadata_json, created_at)
                    VALUES
                        (:id, :project_id, :source, :kind, :text, :checksum, :metadata_json, :created_at)
                    """,
                    {
                        "id": uuid.uuid4().hex,
                        "project_id": project_id,
                        "source": document.source,
                        "kind": document.kind,
                        "text": document.text,
                        "checksum": document.checksum,
                        "metadata_json": json_dumps(document.metadata),
                        "created_at": now,
                    },
                )
            connection.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (utc_now(), project_id))
        return self.list_documents(project_id)

    def delete_document(self, project_id: str, document_id: str) -> None:
        self._require_project(project_id)
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM project_documents WHERE project_id = ? AND id = ?",
                (project_id, document_id),
            )
            if cursor.rowcount == 0:
                raise ProjectNotFoundError(f"Document {document_id} was not found.")
            connection.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (utc_now(), project_id))

    def document_payloads(self, project_id: str) -> list[dict[str, str]]:
        documents = self.list_documents(project_id, include_text=True)
        return [
            {
                "source": str(document["source"]),
                "kind": str(document["kind"] or "txt"),
                "text": str(document["text"]),
            }
            for document in documents
            if str(document.get("text") or "").strip()
        ]

    def save_analysis(self, project_id: str, analysis: dict[str, Any], input_checksum: str) -> dict[str, Any]:
        self._require_project(project_id)
        now = utc_now()
        analysis_id = uuid.uuid4().hex
        with self._connect() as connection:
            connection.execute(
                "UPDATE project_analyses SET is_current = 0 WHERE project_id = ?",
                (project_id,),
            )
            connection.execute(
                """
                INSERT INTO project_analyses
                    (id, project_id, analysis_json, input_checksum, created_at, is_current)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (analysis_id, project_id, json_dumps(analysis), input_checksum, now),
            )
            connection.execute(
                "UPDATE projects SET updated_at = ?, last_analyzed_at = ? WHERE id = ?",
                (now, now, project_id),
            )
        saved = self.get_current_analysis(project_id)
        if saved is None:
            raise RuntimeError("Analysis was not saved.")
        return saved

    def get_current_analysis(self, project_id: str) -> dict[str, Any] | None:
        self._require_project(project_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, project_id, analysis_json, input_checksum, created_at, is_current
                FROM project_analyses
                WHERE project_id = ? AND is_current = 1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["analysis"] = json_loads(result.pop("analysis_json"))
        result["is_current"] = bool(result["is_current"])
        return result

    def get_project_assistant_context(self, project_id: str) -> dict[str, Any]:
        return {
            "project": self.get_project(project_id),
            "current_analysis": self.get_current_analysis(project_id),
            "documents": self.list_documents(project_id, include_text=True),
        }

    def save_ui_state(self, project_id: str, ui_state: dict[str, Any]) -> dict[str, Any]:
        self._require_project(project_id)
        current = self.get_ui_state(project_id) or {}
        next_state = {
            "profile": ui_state.get("profile", current.get("profile")),
            "gaps": ui_state.get("gaps", current.get("gaps")),
            "goals": ui_state.get("goals", current.get("goals")),
            "recommendation": ui_state.get("recommendation", current.get("recommendation")),
            "workshop": ui_state.get("workshop", current.get("workshop")),
            "job_to_be_done": ui_state.get("job_to_be_done", current.get("job_to_be_done")),
            "active_page": ui_state.get("active_page", current.get("active_page")),
        }
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO project_ui_state (
                    project_id, profile_json, gaps_json, goals_json, recommendation_json,
                    workshop_json, job_to_be_done, active_page, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    gaps_json = excluded.gaps_json,
                    goals_json = excluded.goals_json,
                    recommendation_json = excluded.recommendation_json,
                    workshop_json = excluded.workshop_json,
                    job_to_be_done = excluded.job_to_be_done,
                    active_page = excluded.active_page,
                    updated_at = excluded.updated_at
                """,
                (
                    project_id,
                    json_dumps_or_none(next_state["profile"]),
                    json_dumps_or_none(next_state["gaps"]),
                    json_dumps_or_none(next_state["goals"]),
                    json_dumps_or_none(next_state["recommendation"]),
                    json_dumps_or_none(next_state["workshop"]),
                    next_state["job_to_be_done"],
                    next_state["active_page"],
                    now,
                ),
            )
            connection.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id))
        return self.get_ui_state(project_id) or {}

    def get_ui_state(self, project_id: str) -> dict[str, Any] | None:
        self._require_project(project_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT profile_json, gaps_json, goals_json, recommendation_json,
                    workshop_json, job_to_be_done, active_page, updated_at
                FROM project_ui_state
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "profile": json_loads_or_none(row["profile_json"]),
            "gaps": json_loads_or_none(row["gaps_json"]),
            "goals": json_loads_or_none(row["goals_json"]),
            "recommendation": json_loads_or_none(row["recommendation_json"]),
            "workshop": json_loads_or_none(row["workshop_json"]),
            "job_to_be_done": row["job_to_be_done"],
            "active_page": row["active_page"],
            "updated_at": row["updated_at"],
        }

    def _require_project(self, project_id: str) -> None:
        if not self.project_exists(project_id):
            raise ProjectNotFoundError(f"Project {project_id} was not found.")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _ensure_column(self, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def input_checksum(documents: Iterable[dict[str, str]], context: str = "") -> str:
    digest = hashlib.sha256()
    for document in documents:
        digest.update(str(document.get("source") or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(document.get("kind") or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(document.get("text") or "").encode("utf-8"))
        digest.update(b"\0")
    digest.update(context.encode("utf-8"))
    return digest.hexdigest()


def default_db_path() -> Path:
    configured = os.getenv("GAIA_PHASE1_DB_PATH")
    return Path(configured) if configured else DEFAULT_DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_dumps_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return json_dumps(value)


def json_loads(value: str) -> Any:
    return json.loads(value)


def json_loads_or_none(value: str | None) -> Any:
    if value is None:
        return None
    return json_loads(value)


def document_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["metadata"] = json_loads_or_none(result.pop("metadata_json")) or {}
    return result
