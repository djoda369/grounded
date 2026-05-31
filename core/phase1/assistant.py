from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from core.phase1.env import load_local_env
from core.phase1.schema import EvidenceSource, Phase1Analysis

METHODOLOGY_GUARDRAILS = """You are Gaia, Grounded's strategy assistant.
Use Grounded's 5C methodology: Company, Competition, Culture, Consumer, and Category.
Connect those 5C signals to sustainability commitments to identify Intention-Action Gaps.
Never invent sources. If evidence is missing, say what is missing and what to ingest next.
Recommendations must include a clear business action, proof point, and measurable outcome.
Keep the tone executive-ready, direct, and useful for client workshops."""

DEFAULT_ASSISTANT_MODEL = "gpt-4o-mini"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
MAX_EVIDENCE_ITEMS = 12
MAX_DOCUMENT_ITEMS = 4
MAX_EXCERPT_CHARS = 700

AssistantHistory = list[dict[str, str]]
AssistantSource = dict[str, Any]


class GroundedAssistant:
    """Builds grounded assistant context from normalized Phase 1 analysis."""

    def system_prompt(self, analysis: Phase1Analysis | None = None) -> str:
        if analysis is None:
            return METHODOLOGY_GUARDRAILS

        lines = [METHODOLOGY_GUARDRAILS, "", f"Client: {analysis.company_name}", ""]
        lines.append("Current IAG executive summary:")
        lines.append(analysis.iag["summary"].explanation)
        lines.append("")
        lines.append("Available evidence:")
        for evidence in self.evidence_pack(analysis, limit=8):
            lines.append(f"- {evidence.source}: {evidence.excerpt}")
        return "\n".join(lines)

    def evidence_pack(self, analysis: Phase1Analysis, limit: int = 8) -> list[EvidenceSource]:
        evidence: list[EvidenceSource] = []
        for insight in analysis.five_c.values():
            evidence.extend(insight.evidence[:2])
        for gap in analysis.iag.values():
            evidence.extend(gap.evidence[:1])
        evidence.sort(key=lambda item: (-item.score, item.source, item.excerpt))
        deduped: list[EvidenceSource] = []
        seen: set[tuple[str, str]] = set()
        for item in evidence:
            key = (item.source, item.excerpt)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= limit:
                break
        return deduped

    def deterministic_answer(self, analysis: Phase1Analysis, question: str) -> str:
        """Fallback answer for smoke tests and offline demos."""
        evidence = self.evidence_pack(analysis, limit=3)
        answer = [
            f"Based on the current {analysis.company_name} analysis, Gaia would answer this through the 5C and IAG lens.",
            analysis.iag["summary"].explanation,
        ]
        if evidence:
            answer.append("Supporting evidence:")
            answer.extend(f"- {item.excerpt}" for item in evidence)
        answer.append(f"Question handled: {question}")
        return "\n".join(answer)

    def answer_question(
        self,
        analysis_json: dict[str, Any],
        message: str,
        history: AssistantHistory | None = None,
        documents: list[dict[str, Any]] | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Answer from saved Phase 1 analysis, using OpenAI when configured and deterministic fallback otherwise."""
        clean_message = message.strip()
        evidence = pack_project_evidence(analysis_json, documents or [], clean_message)
        confidence = response_confidence(analysis_json, evidence)
        grounding_status = "grounded" if evidence else "limited_evidence"
        load_local_env()
        api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        model = model or os.getenv("GAIA_ASSISTANT_MODEL") or DEFAULT_ASSISTANT_MODEL

        if not api_key:
            return self.deterministic_project_answer(
                analysis_json=analysis_json,
                message=clean_message,
                evidence=evidence,
                confidence=confidence,
                grounding_status=grounding_status,
            )

        messages = self.build_grounded_messages(analysis_json, clean_message, history or [], evidence)
        try:
            model_answer = call_openai_chat(api_key, model, messages)
        except Exception:
            return self.deterministic_project_answer(
                analysis_json=analysis_json,
                message=clean_message,
                evidence=evidence,
                confidence=confidence,
                grounding_status=grounding_status,
            )

        parsed = parse_assistant_json(model_answer)
        answer = str(parsed.get("answer") or "").strip()
        if not answer:
            answer = self.deterministic_project_answer(
                analysis_json=analysis_json,
                message=clean_message,
                evidence=evidence,
                confidence=confidence,
                grounding_status=grounding_status,
            )["answer"]
        followups = parsed.get("suggested_followups")
        return {
            "answer": answer,
            "sources": response_sources(evidence),
            "confidence": confidence,
            "grounding_status": grounding_status,
            "suggested_followups": followups if isinstance(followups, list) else suggested_followups(analysis_json),
        }

    def build_grounded_messages(
        self,
        analysis_json: dict[str, Any],
        message: str,
        history: AssistantHistory,
        evidence: list[AssistantSource],
    ) -> list[dict[str, str]]:
        system_prompt = str(analysis_json.get("assistant_system_prompt") or METHODOLOGY_GUARDRAILS).strip()
        context = {
            "company_name": analysis_json.get("company_name"),
            "contract_version": analysis_json.get("contract_version"),
            "iag_summary": get_gap(analysis_json, "summary"),
            "company_bbp": compact_dict(analysis_json.get("company_bbp")),
            "recommendation": compact_dict(analysis_json.get("recommendation")),
            "evidence": [
                {
                    "source": item["source"],
                    "module": item["module"],
                    "excerpt": item["excerpt"],
                    "score": item["score"],
                }
                for item in evidence
            ],
        }
        messages = [
            {
                "role": "system",
                "content": (
                    f"{METHODOLOGY_GUARDRAILS}\n\n"
                    f"Saved Phase 1 assistant prompt:\n{system_prompt}\n\n"
                    "Answer only from the saved Phase 1 context below. Do not use external knowledge. "
                    "If the evidence does not support the user's claim or requested detail, say what is missing. "
                    "Return JSON only with keys: answer, suggested_followups."
                ),
            }
        ]
        for item in sanitize_history(history)[-6:]:
            messages.append(item)
        messages.append(
            {
                "role": "user",
                "content": (
                    "Saved Phase 1 context:\n"
                    f"{json.dumps(context, ensure_ascii=False)}\n\n"
                    f"User question: {message}"
                ),
            }
        )
        return messages

    def deterministic_project_answer(
        self,
        analysis_json: dict[str, Any],
        message: str,
        evidence: list[AssistantSource],
        confidence: int | None = None,
        grounding_status: str | None = None,
    ) -> dict[str, Any]:
        company_name = str(analysis_json.get("company_name") or "this project")
        gap_key = select_gap_key(message)
        gap = get_gap(analysis_json, gap_key) or get_gap(analysis_json, "summary")
        explanation = str(gap.get("explanation") or "").strip()
        next_steps = gap_next_steps(gap)
        lines = [
            f"Based only on the saved Phase 1 analysis for {company_name}, Gaia would answer this through the 5C and IAG lens.",
        ]
        if explanation:
            lines.append(explanation)
        else:
            lines.append("The saved analysis does not contain enough IAG explanation to answer this fully.")

        if evidence:
            lines.append("Supporting evidence:")
            for item in evidence[:3]:
                lines.append(f"- [{item['module']}] {item['excerpt']}")
        else:
            lines.append("Evidence is limited: add source documents or rerun Phase 1 before using this as a client-ready answer.")

        if next_steps:
            lines.append("Recommended next moves:")
            for step in next_steps[:3]:
                lines.append(f"- {step}")
        else:
            lines.append("Recommended next move: add an action, proof point, and measurable outcome to the saved analysis.")

        lines.append(f"Question handled: {message}")
        return {
            "answer": "\n".join(lines),
            "sources": response_sources(evidence),
            "confidence": confidence if confidence is not None else response_confidence(analysis_json, evidence),
            "grounding_status": grounding_status or ("grounded" if evidence else "limited_evidence"),
            "suggested_followups": suggested_followups(analysis_json),
        }


def pack_project_evidence(
    analysis_json: dict[str, Any],
    documents: list[dict[str, Any]],
    question: str,
    limit: int = MAX_EVIDENCE_ITEMS,
) -> list[AssistantSource]:
    evidence: list[AssistantSource] = []
    iag = analysis_json.get("iag") if isinstance(analysis_json.get("iag"), dict) else {}
    for module, gap in iag.items():
        if not isinstance(gap, dict):
            continue
        evidence.extend(normalize_evidence_items(gap.get("raw_evidence"), str(module), fallback_score=gap.get("confidence")))
        evidence.extend(normalize_evidence_items(gap.get("evidence"), str(module), fallback_score=gap.get("confidence")))

    five_c = analysis_json.get("five_c") if isinstance(analysis_json.get("five_c"), dict) else {}
    for module, insight in five_c.items():
        if isinstance(insight, dict):
            evidence.extend(normalize_evidence_items(insight.get("evidence"), str(module), fallback_score=insight.get("confidence")))

    for goal in analysis_json.get("sustainability_goals") or []:
        if not isinstance(goal, dict):
            continue
        source = str(goal.get("source") or "sustainability_goal")
        excerpt = f"{goal.get('title') or 'Sustainability goal'}: {goal.get('description') or ''}".strip()
        evidence.append(make_source(source, excerpt, "sustainability", goal.get("confidence")))

    for goal in ((analysis_json.get("sustainability") or {}).get("goals") or []):
        if isinstance(goal, dict):
            evidence.extend(normalize_evidence_items(goal.get("evidence"), "sustainability", fallback_score=goal.get("confidence")))

    for document in documents[:MAX_DOCUMENT_ITEMS]:
        text = str(document.get("text") or "").strip()
        if not text:
            continue
        evidence.append(
            make_source(
                source=str(document.get("source") or "stored_document"),
                excerpt=first_excerpt(text),
                module="document",
                score=35,
                metadata=document.get("metadata") if isinstance(document.get("metadata"), dict) else {},
            )
        )

    return rank_and_dedupe_evidence(evidence, question)[:limit]


def normalize_evidence_items(items: Any, module: str, fallback_score: Any = None) -> list[AssistantSource]:
    if not isinstance(items, list):
        return []
    normalized: list[AssistantSource] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("excerpt"), str):
            normalized.append(
                make_source(
                    source=str(item.get("source") or "analysis"),
                    excerpt=item["excerpt"],
                    module=module,
                    score=item.get("score", fallback_score),
                    metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
                )
            )
            continue
        if isinstance(item.get("summary"), str):
            sources = item.get("sources") if isinstance(item.get("sources"), list) else []
            normalized.append(
                make_source(
                    source=str(sources[0] if sources else "analysis"),
                    excerpt=item["summary"],
                    module=module,
                    score=fallback_score,
                    metadata={},
                )
            )
    return normalized


def make_source(
    source: str,
    excerpt: str,
    module: str,
    score: Any = None,
    metadata: dict[str, Any] | None = None,
) -> AssistantSource:
    return {
        "source": source or "analysis",
        "excerpt": clip(str(excerpt or "").strip(), MAX_EXCERPT_CHARS),
        "module": module,
        "score": numeric_score(score),
        "metadata": metadata or {},
    }


def rank_and_dedupe_evidence(evidence: list[AssistantSource], question: str) -> list[AssistantSource]:
    terms = question_terms(question)
    seen: set[tuple[str, str, str]] = set()
    deduped: list[AssistantSource] = []
    for item in evidence:
        if not item.get("excerpt"):
            continue
        if is_missing_evidence_marker(item):
            continue
        key = (str(item["source"]), str(item["module"]), str(item["excerpt"]).lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    def rank(item: AssistantSource) -> tuple[int, float, str]:
        text = f"{item.get('module')} {item.get('source')} {item.get('excerpt')}".lower()
        relevance = sum(1 for term in terms if term in text)
        return (-relevance, -float(item.get("score") or 0), str(item.get("source") or ""))

    deduped.sort(key=rank)
    return deduped


def response_sources(evidence: list[AssistantSource]) -> list[dict[str, str]]:
    return [
        {
            "source": str(item["source"]),
            "excerpt": str(item["excerpt"]),
            "module": str(item["module"]),
        }
        for item in evidence[:6]
    ]


def response_confidence(analysis_json: dict[str, Any], evidence: list[AssistantSource]) -> int:
    summary = get_gap(analysis_json, "summary")
    summary_confidence = numeric_score(summary.get("confidence") if summary else None)
    if not evidence:
        return min(summary_confidence, 45)
    evidence_average = round(sum(numeric_score(item.get("score")) for item in evidence[:6]) / min(len(evidence), 6))
    return clamp_percent(round((summary_confidence + evidence_average) / 2))


def call_openai_chat(api_key: str, model: str, messages: list[dict[str, str]]) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI assistant request failed: {detail}") from exc
    return str(data["choices"][0]["message"]["content"])


def parse_assistant_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"answer": text, "suggested_followups": []}
    return parsed if isinstance(parsed, dict) else {"answer": text, "suggested_followups": []}


def sanitize_history(history: AssistantHistory) -> AssistantHistory:
    clean: AssistantHistory = []
    if not isinstance(history, list):
        return clean
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str) or not content.strip():
            continue
        clean.append({"role": role, "content": clip(content.strip(), 1200)})
    return clean


def get_gap(analysis_json: dict[str, Any], key: str) -> dict[str, Any]:
    iag = analysis_json.get("iag")
    gap = iag.get(key) if isinstance(iag, dict) else None
    return gap if isinstance(gap, dict) else {}


def gap_next_steps(gap: dict[str, Any]) -> list[str]:
    for key in ("nextSteps", "recommendations"):
        value = gap.get(key)
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
    return []


def select_gap_key(message: str) -> str:
    lower = message.lower()
    for key in ("company", "competition", "culture", "consumer", "category"):
        if key in lower:
            return key
    return "summary"


def suggested_followups(analysis_json: dict[str, Any]) -> list[str]:
    company = str(analysis_json.get("company_name") or "this project")
    return [
        f"What evidence most strongly supports the IAG for {company}?",
        "Which recommendation has the clearest action, proof point, and measurable outcome?",
    ]


def compact_dict(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    output: dict[str, Any] = {}
    for key, item in value.items():
        if key in {"evidence", "raw_evidence", "documents"}:
            continue
        output[key] = clip(str(item), 1000) if isinstance(item, str) else item
    return output


def first_excerpt(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    for sentence in sentences:
        if len(sentence.strip()) >= 40:
            return clip(sentence.strip(), MAX_EXCERPT_CHARS)
    return clip(text, MAX_EXCERPT_CHARS)


def question_terms(question: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]{4,}", question.lower()) if term not in {"what", "which", "from", "with", "that", "this"}}


def is_missing_evidence_marker(item: AssistantSource) -> bool:
    source = str(item.get("source") or "").lower()
    excerpt = str(item.get("excerpt") or "").lower()
    if source != "backend analyzer":
        return False
    return any(
        marker in excerpt
        for marker in (
            "evidence required",
            "missing normalized source evidence",
            "did not receive enough normalized source evidence",
            "no strong",
        )
    )


def numeric_score(value: Any) -> int:
    try:
        return clamp_percent(round(float(value)))
    except (TypeError, ValueError):
        return 50


def clamp_percent(value: int) -> int:
    return max(0, min(100, value))


def clip(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 3)].rstrip()}..."
