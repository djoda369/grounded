from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any

from core.phase1.env import load_local_env
from core.phase1.llm_client import OpenAIJsonClient

MERGEABLE_KEYS = {
    "company_bbp",
    "five_c",
    "sustainability",
    "iag",
    "recommendation",
    "culture",
    "consumer",
    "category",
}


class Phase1LLMExtractor:
    def __init__(self, client: OpenAIJsonClient | None = None):
        load_local_env()
        self.client = client or OpenAIJsonClient()

    def enrich(
        self,
        base_contract: dict[str, Any],
        workshop_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract = deepcopy(base_contract)
        model = getattr(self.client, "model", os.getenv("GAIA_LLM_MODEL", ""))
        extraction_mode = os.getenv("GAIA_LLM_EXTRACTION", "auto").strip().lower()

        contract.setdefault("executive_summary", summary_text(contract))
        contract["analysis_mode"] = "deterministic"
        contract["llm_model"] = model

        if extraction_mode in {"0", "false", "off", "disabled"}:
            contract["llm_extraction_status"] = "skipped_disabled"
            return contract

        if not self.client.has_api_key():
            contract["llm_extraction_status"] = "skipped_no_key"
            return contract

        try:
            llm_output = self.client.json_chat(build_extraction_messages(contract, workshop_state or {}))
        except Exception as exc:
            contract["llm_extraction_status"] = "error_fallback"
            contract["llm_error"] = str(exc)[:500]
            return contract

        merged = merge_llm_contract(contract, llm_output)
        merged["analysis_mode"] = "llm_enriched"
        merged["llm_extraction_status"] = "success"
        merged["llm_model"] = model
        merged["executive_summary"] = (
            non_empty_string(llm_output.get("executive_summary"))
            or non_empty_string(merged.get("executive_summary"))
            or summary_text(merged)
        )
        return merged


def build_extraction_messages(
    base_contract: dict[str, Any],
    workshop_state: dict[str, Any],
) -> list[dict[str, str]]:
    compact_context = {
        "company_name": base_contract.get("company_name"),
        "company_bbp": base_contract.get("company_bbp"),
        "five_c": base_contract.get("five_c"),
        "sustainability": base_contract.get("sustainability"),
        "iag": base_contract.get("iag"),
        "recommendation": base_contract.get("recommendation"),
        "documents": document_excerpts(base_contract.get("documents")),
        "workshop_state": workshop_state,
    }
    return [
        {
            "role": "system",
            "content": (
                "You are Gaia, Grounded's Phase 1 extraction engine. Use Grounded's 5C methodology "
                "(Company, Competition, Culture, Consumer, Category) and connect those signals to "
                "sustainability commitments and Intention-Action Gaps. Use only the supplied evidence. "
                "Never invent sources. Every strategic claim must be supported by an evidence object with "
                "source, excerpt, score, and metadata where possible. If evidence is missing, return a "
                "low-confidence structured finding that names the missing evidence. Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Enrich this deterministic Phase 1 contract. Return only fields that are improved by the "
                "provided evidence. The expected top-level keys are company_bbp, five_c, sustainability, "
                "iag, recommendation, executive_summary, culture, consumer, and category.\n\n"
                f"{json.dumps(compact_context, ensure_ascii=False)}"
            ),
        },
    ]


def merge_llm_contract(base_contract: dict[str, Any], llm_output: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base_contract)
    for key in MERGEABLE_KEYS:
        value = llm_output.get(key)
        if not has_value(value):
            continue
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = deep_merge_non_empty(merged[key], value)
        elif isinstance(value, list):
            if value:
                merged[key] = value
        else:
            merged[key] = value
    return merged


def deep_merge_non_empty(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        output = deepcopy(base)
        for key, value in override.items():
            if not has_value(value):
                continue
            output[key] = deep_merge_non_empty(output.get(key), value)
        return output
    if isinstance(override, list):
        return override if override else base
    return override if has_value(override) else base


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def non_empty_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def summary_text(contract: dict[str, Any]) -> str:
    iag = contract.get("iag") if isinstance(contract.get("iag"), dict) else {}
    summary = iag.get("summary") if isinstance(iag.get("summary"), dict) else {}
    recommendation = contract.get("recommendation") if isinstance(contract.get("recommendation"), dict) else {}
    return (
        non_empty_string(summary.get("explanation"))
        or non_empty_string(recommendation.get("overview"))
        or "Phase 1 analysis needs more evidence before Gaia can produce an executive summary."
    )


def document_excerpts(documents: Any) -> list[dict[str, str]]:
    if not isinstance(documents, list):
        return []
    output: list[dict[str, str]] = []
    for document in documents[:8]:
        if not isinstance(document, dict):
            continue
        text = str(document.get("text") or "")
        output.append(
            {
                "source": str(document.get("source") or "document"),
                "kind": str(document.get("kind") or "txt"),
                "excerpt": " ".join(text.split())[:1400],
            }
        )
    return output
