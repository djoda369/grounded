from __future__ import annotations

import base64
import json
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.phase1 import Phase1Analyzer
from core.phase1.schema import to_plain
from core.phase1.source_collector import (
    collect_sources,
    infer_company_name,
    ledger_to_documents,
    parse_source_settings,
    suggest_competitors,
    validate_public_website_url,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


class Phase1APIHandler(BaseHTTPRequestHandler):
    analyzer = Phase1Analyzer()

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/api/health":
            self._send_json({"ok": True, "service": "gaia-phase1"})
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        route = urlparse(self.path).path.rstrip("/")
        if route not in {
            "/api/phase1/analyze",
            "/api/phase1/onboard",
            "/api/phase1/competitors/suggest",
        }:
            self._send_json({"error": "Not found"}, status=404)
            return

        try:
            payload = self._read_json()
            if route == "/api/phase1/analyze":
                result = analyze_payload(payload, self.analyzer)
            elif route == "/api/phase1/onboard":
                result = onboard_payload(payload, self.analyzer)
            else:
                result = suggest_competitors_payload(payload)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
            return
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return

        self._send_json(result)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            raise ValueError("Request body is required.")
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)


def analyze_payload(payload: dict[str, Any], analyzer: Phase1Analyzer | None = None) -> dict[str, Any]:
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

    return to_plain(analysis)


def onboard_payload(payload: dict[str, Any], analyzer: Phase1Analyzer | None = None) -> dict[str, Any]:
    website_url = validate_public_website_url(str(payload.get("website_url") or ""))
    source_settings = parse_source_settings(payload.get("source_settings"))
    source_ledger = collect_sources(
        website_url,
        source_settings=source_settings,
        manual_links=payload.get("manual_links"),
    )
    company_name = str(payload.get("company_name") or "").strip() or infer_company_name(website_url, source_ledger)
    documents = ledger_to_documents(source_ledger)
    uploaded_documents = payload.get("documents")
    if uploaded_documents is not None:
        if not isinstance(uploaded_documents, list):
            raise ValueError("documents must be a list.")
        documents.extend(uploaded_documents)
    if not documents:
        skipped = "; ".join(
            f"{entry.get('type')}: {entry.get('error')}"
            for entry in source_ledger
            if entry.get("status") != "ok" and entry.get("error")
        )
        raise ValueError(f"No usable public evidence was collected. {skipped}".strip())

    analysis = analyze_documents_payload(documents, company_name, analyzer or Phase1Analyzer())
    plain_analysis = to_plain(analysis)
    profile = build_company_profile(company_name, website_url, plain_analysis, source_ledger)
    return {
        "profile": profile,
        "source_ledger": source_ledger,
        "analysis": plain_analysis,
        "source_settings": source_settings,
    }


def suggest_competitors_payload(payload: dict[str, Any]) -> dict[str, Any]:
    website_url = validate_public_website_url(str(payload.get("website_url") or ""))
    profile = payload.get("profile")
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object.")
    source_ledger = payload.get("source_ledger")
    if not isinstance(source_ledger, list):
        source_ledger = []
    suggestions = suggest_competitors(profile, website_url, source_ledger)
    return {"suggestions": suggestions}


def build_company_profile(
    company_name: str,
    website_url: str,
    analysis: dict[str, Any],
    source_ledger: list[dict[str, Any]],
) -> dict[str, Any]:
    company = analysis.get("five_c", {}).get("company", {}) if isinstance(analysis.get("five_c"), dict) else {}
    summary = analysis.get("iag", {}).get("summary", {}) if isinstance(analysis.get("iag"), dict) else {}
    brand = company_name.split()[0] if company_name else infer_company_name(website_url, source_ledger)
    recommendation = ""
    if isinstance(summary, dict):
        recommendations = summary.get("recommendations")
        if isinstance(recommendations, list) and recommendations:
            recommendation = str(recommendations[0])
    return {
        "brand": brand,
        "market": company_name,
        "project": "Website onboarding diagnostic",
        "belief": str(company.get("from_state") or company.get("summary") or "Belief requires more public evidence."),
        "purpose": str(company.get("to_state") or company.get("summary") or "Purpose requires more public evidence."),
        "pursuits": {
            "product": first_available_source_excerpt(source_ledger, "products")
            or "Product pursuit requires more public evidence.",
            "platform": first_available_source_excerpt(source_ledger, "purpose")
            or first_available_source_excerpt(source_ledger, "about")
            or "Platform pursuit requires more public evidence.",
            "impact": recommendation or "Impact pursuit requires more public evidence.",
        },
    }


def first_available_source_excerpt(source_ledger: list[dict[str, Any]], keyword: str) -> str:
    for entry in source_ledger:
        haystack = f"{entry.get('url', '')} {entry.get('title', '')}".lower()
        if entry.get("status") == "ok" and keyword in haystack:
            return str(entry.get("excerpt") or "")[:360]
    return ""


def analyze_documents_payload(
    documents: Any,
    company_name: str,
    analyzer: Phase1Analyzer,
):
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

            return analyzer.analyze_paths(paths, company_name)

    return analyzer.analyze_texts(text_documents, company_name)


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
    run()
