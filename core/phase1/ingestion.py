from __future__ import annotations

import hashlib
import html
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

from core.phase1.schema import IngestedDocument

SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".docx", ".pdf"}
MAX_DOCUMENT_CHARS = 160_000


def normalize_text(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def stable_document_id(source: str, text: str) -> str:
    digest = hashlib.sha256(f"{source}\n{text}".encode("utf-8")).hexdigest()
    return digest[:16]


def checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ReportIngestionPipeline:
    """Normalize Grounded input formats into reproducible text documents."""

    def ingest_paths(self, paths: Iterable[str | Path]) -> list[IngestedDocument]:
        documents: list[IngestedDocument] = []
        for raw_path in paths:
            path = Path(raw_path)
            if path.is_dir():
                documents.extend(self.ingest_paths(sorted(path.rglob("*"))))
                continue
            document = self.ingest_path(path)
            if document is not None:
                documents.append(document)
        return self.dedupe(documents)

    def ingest_texts(self, texts: Iterable[str | dict[str, str]]) -> list[IngestedDocument]:
        documents: list[IngestedDocument] = []
        for index, item in enumerate(texts, start=1):
            if isinstance(item, str):
                source = f"inline:{index}"
                kind = "text"
                raw_text = item
            else:
                source = item.get("source") or f"inline:{index}"
                kind = item.get("kind") or "text"
                raw_text = item.get("text") or ""

            text = normalize_text(raw_text)[:MAX_DOCUMENT_CHARS]
            if not text:
                continue
            documents.append(
                IngestedDocument(
                    id=stable_document_id(source, text),
                    source=source,
                    kind=kind,
                    text=text,
                    checksum=checksum(text),
                    metadata={"input": "inline"},
                )
            )
        return self.dedupe(documents)

    def ingest_path(self, path: str | Path) -> IngestedDocument | None:
        path = Path(path)
        if not path.exists() or not path.is_file():
            return None
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return None

        if extension in {".txt", ".md", ".csv"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
        elif extension == ".json":
            text = self._read_json(path)
        elif extension == ".docx":
            text = self._read_docx(path)
        elif extension == ".pdf":
            text = self._read_pdf(path)
        else:
            return None

        text = normalize_text(text)[:MAX_DOCUMENT_CHARS]
        if not text:
            return None
        return IngestedDocument(
            id=stable_document_id(str(path), text),
            source=str(path),
            kind=extension.lstrip("."),
            text=text,
            checksum=checksum(text),
            metadata={"size_bytes": path.stat().st_size},
        )

    def dedupe(self, documents: Iterable[IngestedDocument]) -> list[IngestedDocument]:
        seen: set[str] = set()
        unique: list[IngestedDocument] = []
        for document in documents:
            if document.checksum in seen:
                continue
            seen.add(document.checksum)
            unique.append(document)
        return unique

    def _read_json(self, path: Path) -> str:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(_json_strings(data))

    def _read_docx(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs: list[str] = []
        for paragraph in root.iter(f"{namespace}p"):
            text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
            if text.strip():
                paragraphs.append(text)
        return "\n".join(paragraphs)

    def _read_pdf(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF ingestion requires the pypdf package.") from exc

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)


def _json_strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            output.extend(_json_strings(item))
        return output
    if isinstance(value, dict):
        output = []
        for key, item in value.items():
            child = _json_strings(item)
            if child:
                output.append(str(key))
                output.extend(child)
        return output
    return [str(value)]
