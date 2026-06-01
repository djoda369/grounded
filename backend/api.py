from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.phase1 import Phase1Analyzer
from core.phase1.contract import StructuredPhase1ContractBuilder
from core.phase1.llm_extraction import Phase1LLMExtractor
from core.phase1.schema import IngestedDocument
from core.phase1.storage import Phase1ProjectStore, ProjectNotFoundError, input_checksum

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DIST_DIR = ROOT_DIR / "dist"


class Phase1APIHandler(BaseHTTPRequestHandler):
    analyzer = Phase1Analyzer()
    contract_builder = StructuredPhase1ContractBuilder()
    llm_extractor = Phase1LLMExtractor()
    store = Phase1ProjectStore()

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        parts = self._path_parts()
        if parts == ["api", "health"]:
            self._send_json({"ok": True, "service": "gaia-phase1"})
            return

        try:
            if parts == ["api", "phase1", "projects"]:
                self._send_json({"projects": self.store.list_projects()})
                return

            if len(parts) == 4 and parts[:3] == ["api", "phase1", "projects"]:
                self._send_json(self.store.get_project_bundle(parts[3]))
                return
        except ProjectNotFoundError as exc:
            self._send_json({"error": str(exc)}, status=404)
            return
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        if self._send_static_asset():
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parts = self._path_parts()
        try:
            if parts == ["api", "phase1", "analyze"]:
                payload = self._read_json()
                result = analyze_payload(payload, self.analyzer, self.contract_builder, self.llm_extractor)
                self._send_json(result)
                return

            if parts == ["api", "phase1", "assistant"]:
                payload = self._read_json()
                self._send_json(assistant_payload(payload, self.store, self.analyzer.assistant))
                return

            if parts == ["api", "phase1", "projects"]:
                payload = self._read_json()
                self._send_json(create_project_payload(payload, self.store), status=201)
                return

            if len(parts) == 5 and parts[:3] == ["api", "phase1", "projects"] and parts[4] == "documents":
                payload = self._read_json()
                self._send_json(add_project_documents_payload(parts[3], payload, self.store, self.analyzer))
                return

            if len(parts) == 5 and parts[:3] == ["api", "phase1", "projects"] and parts[4] == "analyze":
                payload = self._read_json(required=False)
                self._send_json(
                    analyze_project_payload(
                        parts[3],
                        payload,
                        self.store,
                        self.analyzer,
                        self.contract_builder,
                        self.llm_extractor,
                    )
                )
                return
        except ProjectNotFoundError as exc:
            self._send_json({"error": str(exc)}, status=404)
            return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
            return
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_PATCH(self) -> None:
        parts = self._path_parts()
        try:
            if len(parts) == 4 and parts[:3] == ["api", "phase1", "projects"]:
                payload = self._read_json()
                self._send_json(update_project_payload(parts[3], payload, self.store))
                return
        except ProjectNotFoundError as exc:
            self._send_json({"error": str(exc)}, status=404)
            return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
            return
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_DELETE(self) -> None:
        parts = self._path_parts()
        try:
            if len(parts) == 6 and parts[:3] == ["api", "phase1", "projects"] and parts[4] == "documents":
                self.store.delete_document(parts[3], parts[5])
                self._send_json({"ok": True, "documents": self.store.list_documents(parts[3])})
                return
        except ProjectNotFoundError as exc:
            self._send_json({"error": str(exc)}, status=404)
            return
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _path_parts(self) -> list[str]:
        return [part for part in urlsplit(self.path).path.strip("/").split("/") if part]

    def _read_json(self, required: bool = True) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            if required:
                raise ValueError("Request body is required.")
            return {}
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_static_asset(self) -> bool:
        if not DIST_DIR.exists():
            return False
        raw_path = urlsplit(self.path).path
        relative = raw_path.lstrip("/") or "index.html"
        target = (DIST_DIR / relative).resolve()
        if not str(target).startswith(str(DIST_DIR.resolve())):
            self._send_json({"error": "Not found"}, status=404)
            return True
        if not target.exists() or not target.is_file():
            target = DIST_DIR / "index.html"
        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True


def analyze_payload(
    payload: dict[str, Any],
    analyzer: Phase1Analyzer | None = None,
    contract_builder: StructuredPhase1ContractBuilder | None = None,
    llm_extractor: Phase1LLMExtractor | None = None,
) -> dict[str, Any]:
    company_name = str(payload.get("company_name") or payload.get("brand") or "Yoplait UK")
    analyzer = analyzer or Phase1Analyzer()

    paths = payload.get("paths")
    documents = payload.get("documents")
    text = payload.get("text")

    selected_inputs = sum(value is not None for value in (paths, documents, text))
    if selected_inputs != 1:
        raise ValueError("Provide exactly one of: paths, documents, or text.")

    if paths is not None:
        if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
            raise ValueError("paths must be a list of file paths.")
        analysis = analyzer.analyze_paths(paths, company_name)
    elif documents is not None:
        analysis = analyze_documents_payload(documents, company_name, analyzer)
    else:
        if not isinstance(text, str):
            raise ValueError("text must be a string.")
        analysis = analyzer.analyze_texts([text], company_name)

    workshop_state = payload.get("workshop_state") if isinstance(payload.get("workshop_state"), dict) else None
    return structured_analysis_payload(analysis, contract_builder, llm_extractor, workshop_state)


def analyze_documents_payload(
    documents: Any,
    company_name: str,
    analyzer: Phase1Analyzer,
):
    return analyzer.analyze_documents(normalize_documents_payload(documents, analyzer), company_name)


def create_project_payload(payload: dict[str, Any], store: Phase1ProjectStore) -> dict[str, Any]:
    return store.create_project(
        name=str(payload.get("name") or ""),
        company_name=str(payload.get("company_name") or payload.get("name") or ""),
        brand=str(payload["brand"]) if payload.get("brand") is not None else None,
    )


def update_project_payload(
    project_id: str,
    payload: dict[str, Any],
    store: Phase1ProjectStore,
) -> dict[str, Any]:
    fields = {
        key: payload[key]
        for key in ("name", "company_name", "brand", "status")
        if key in payload
    }
    if fields:
        store.update_project(project_id, fields)
    if "ui_state" in payload:
        ui_state = payload["ui_state"]
        if not isinstance(ui_state, dict):
            raise ValueError("ui_state must be a JSON object.")
        store.save_ui_state(project_id, ui_state)
    if not fields and "ui_state" not in payload:
        raise ValueError("Provide project metadata fields or ui_state.")
    return store.get_project_bundle(project_id)


def add_project_documents_payload(
    project_id: str,
    payload: dict[str, Any],
    store: Phase1ProjectStore,
    analyzer: Phase1Analyzer,
) -> dict[str, Any]:
    store.get_project(project_id)
    documents = normalize_documents_payload(payload.get("documents"), analyzer)
    if not documents:
        raise ValueError("No document text could be normalized from the payload.")
    return {"documents": store.add_documents(project_id, documents)}


def analyze_project_payload(
    project_id: str,
    payload: dict[str, Any],
    store: Phase1ProjectStore,
    analyzer: Phase1Analyzer,
    contract_builder: StructuredPhase1ContractBuilder | None = None,
    llm_extractor: Phase1LLMExtractor | None = None,
) -> dict[str, Any]:
    project = store.get_project(project_id)
    context = str(payload.get("context") or "").strip()
    workshop_state = payload.get("workshop_state") if isinstance(payload.get("workshop_state"), dict) else None
    if workshop_state is None:
        ui_state = store.get_ui_state(project_id) or {}
        workshop_state = ui_state.get("workshop") if isinstance(ui_state.get("workshop"), dict) else {}
    documents = store.document_payloads(project_id)
    analysis_inputs = [*documents]
    if context:
        analysis_inputs.append({"source": "Additional context", "kind": "txt", "text": context})
    if workshop_state:
        analysis_inputs.append(
            {
                "source": "Workshop state",
                "kind": "json",
                "text": workshop_state_text(workshop_state),
            }
        )
    if not analysis_inputs:
        raise ValueError("Project analysis requires at least one stored document or context.")

    analysis = analyzer.analyze_texts(analysis_inputs, project["company_name"])
    analysis_json = structured_analysis_payload(analysis, contract_builder, llm_extractor, workshop_state)
    if workshop_state:
        store.save_ui_state(project_id, {"workshop": workshop_state})
    saved = store.save_analysis(
        project_id,
        analysis_json,
        input_checksum(documents, context_with_workshop(context, workshop_state)),
    )
    return {
        "project_id": project_id,
        "analysis_id": saved["id"],
        "analysis": analysis_json,
    }


def structured_analysis_payload(
    analysis: Any,
    contract_builder: StructuredPhase1ContractBuilder | None = None,
    llm_extractor: Phase1LLMExtractor | None = None,
    workshop_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    builder = contract_builder or StructuredPhase1ContractBuilder()
    base_contract = builder.build(analysis)
    extractor = llm_extractor or Phase1LLMExtractor()
    return extractor.enrich(base_contract, workshop_state=workshop_state)


def workshop_state_text(workshop_state: dict[str, Any]) -> str:
    return json.dumps(
        {
            "note": "Human workshop edits and selections. Treat as user-provided context, not source evidence.",
            "workshop_state": workshop_state,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def context_with_workshop(context: str, workshop_state: dict[str, Any]) -> str:
    if not workshop_state:
        return context
    return f"{context}\n{workshop_state_text(workshop_state)}"


def assistant_payload(
    payload: dict[str, Any],
    store: Phase1ProjectStore,
    assistant: Any,
) -> dict[str, Any]:
    project_id = str(payload.get("project_id") or "").strip()
    if not project_id:
        raise ValueError("project_id is required for the Phase 1 assistant.")

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message is required for the Phase 1 assistant.")

    history = payload.get("history") or []
    if not isinstance(history, list):
        raise ValueError("history must be a list when provided.")

    context = store.get_project_assistant_context(project_id)
    current_analysis = context["current_analysis"]
    if current_analysis is None:
        raise ValueError("Project must have a current Phase 1 analysis before using the assistant.")

    return assistant.answer_question(
        analysis_json=current_analysis["analysis"],
        message=message,
        history=history,
        documents=context["documents"],
    )


def normalize_documents_payload(documents: Any, analyzer: Phase1Analyzer) -> list[IngestedDocument]:
    if not isinstance(documents, list):
        raise ValueError("documents must be a list.")

    text_documents: list[dict[str, str]] = []
    uploaded_documents: list[dict[str, str]] = []
    for item in documents:
        if isinstance(item, str):
            text_documents.append({"source": "inline", "kind": "txt", "text": item})
        elif isinstance(item, dict) and isinstance(item.get("data_base64"), str):
            uploaded_documents.append(
                {
                    "source": str(item.get("source") or "upload.txt"),
                    "kind": str(item.get("kind") or ""),
                    "data_base64": item["data_base64"],
                }
            )
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            text_documents.append(
                {
                    "source": str(item.get("source") or "inline"),
                    "kind": str(item.get("kind") or "txt"),
                    "text": item["text"],
                }
            )
        else:
            raise ValueError("Each document must be a string, text object, or base64 upload object.")

    if uploaded_documents:
        with tempfile.TemporaryDirectory() as directory:
            paths: list[Path] = []
            for index, item in enumerate(uploaded_documents, start=1):
                filename = safe_upload_name(item["source"], item["kind"], index)
                target = Path(directory) / filename
                target.write_bytes(decode_upload(item["data_base64"]))
                paths.append(target)

            for index, item in enumerate(text_documents, start=1):
                filename = safe_upload_name(item["source"], item["kind"], index + len(uploaded_documents))
                target = Path(directory) / filename
                target.write_text(item["text"], encoding="utf-8")
                paths.append(target)

            return [
                IngestedDocument(
                    id=document.id,
                    source=Path(document.source).name,
                    kind=document.kind,
                    text=document.text,
                    checksum=document.checksum,
                    metadata=document.metadata,
                )
                for document in analyzer.ingestion.ingest_paths(paths)
            ]

    return analyzer.ingestion.ingest_texts(text_documents)


def decode_upload(data_base64: str) -> bytes:
    encoded = data_base64.split(",", 1)[-1]
    try:
        return base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("Uploaded document data must be valid base64.") from exc


def safe_upload_name(source: str, kind: str, index: int) -> str:
    name = Path(source).name.strip() or f"upload-{index}"
    suffix = Path(name).suffix
    if not suffix and kind:
        suffix = f".{kind.lstrip('.')}"
        name = f"{name}{suffix}"
    if not Path(name).suffix:
        name = f"{name}.txt"
    return "".join(character if character.isalnum() or character in "._- " else "_" for character in name)


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), Phase1APIHandler)
    print(f"Gaia Phase 1 API running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGaia Phase 1 API stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run(
        os.getenv("HOST", DEFAULT_HOST),
        int(os.getenv("PORT", str(DEFAULT_PORT))),
    )
