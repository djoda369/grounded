from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FIVE_C_KEYS = ("summary", "company", "competition", "culture", "consumer", "category")
MODEL_ENV = "OPENAI_MODEL"
DEFAULT_MODEL = "gpt-4o-mini"


def synthesize_workspace_draft(
    *,
    company_name: str,
    website_url: str,
    profile: dict[str, Any],
    analysis: dict[str, Any],
    source_ledger: list[dict[str, Any]],
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    fallback = fallback_workspace_draft(company_name, website_url, profile, analysis, source_ledger)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {
            "workspace_draft": fallback,
            "synthesis_status": "fallback_no_key",
            "warnings": ["OPENAI_API_KEY is not configured; deterministic evidence-only fallback was used."],
        }

    try:
        draft = call_openai_workspace_synthesis(
            api_key=api_key,
            company_name=company_name,
            website_url=website_url,
            profile=profile,
            analysis=analysis,
            source_ledger=source_ledger,
            documents=documents,
        )
        return {
            "workspace_draft": sanitize_workspace_draft(draft, fallback, source_ledger),
            "synthesis_status": "ai_generated",
            "warnings": source_quality_warnings(source_ledger),
        }
    except Exception as exc:
        return {
            "workspace_draft": fallback,
            "synthesis_status": "fallback_model_error",
            "warnings": [
                f"OpenAI synthesis failed: {exc}",
                "Deterministic evidence-only fallback was used.",
            ],
        }


def synthesize_competitor_suggestions(
    *,
    company_profile: dict[str, Any],
    website_url: str,
    source_ledger: list[dict[str, Any]],
    fallback_suggestions: list[dict[str, Any]],
) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {
            "suggestions": fallback_suggestions,
            "synthesis_status": "fallback_no_key",
            "warnings": ["OPENAI_API_KEY is not configured; heuristic competitor suggestions were used."],
        }

    ok_sources = ok_source_summaries(source_ledger)
    if not ok_sources:
        return {
            "suggestions": fallback_suggestions,
            "synthesis_status": "fallback_insufficient_evidence",
            "warnings": ["No usable source excerpts were available for AI competitor synthesis."],
        }

    payload = {
        "model": os.environ.get(MODEL_ENV, DEFAULT_MODEL),
        "input": [
            {
                "role": "system",
                "content": (
                    "You suggest competitor benchmarks from public evidence. "
                    "Use only the supplied source excerpts. Do not invent source URLs."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "company_profile": company_profile,
                        "website_url": website_url,
                        "source_ledger": ok_sources,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "competitor_suggestions",
                "strict": True,
                "schema": COMPETITOR_SCHEMA,
            }
        },
    }

    try:
        data = post_openai_response(api_key, payload)
        parsed = json.loads(extract_response_text(data))
        suggestions = parsed.get("suggestions")
        if not isinstance(suggestions, list):
            raise ValueError("OpenAI response did not include a suggestions list.")
        return {
            "suggestions": sanitize_competitors(suggestions, source_ledger),
            "synthesis_status": "ai_generated",
            "warnings": source_quality_warnings(source_ledger),
        }
    except Exception as exc:
        return {
            "suggestions": fallback_suggestions,
            "synthesis_status": "fallback_model_error",
            "warnings": [f"OpenAI competitor synthesis failed: {exc}", "Heuristic suggestions were used."],
        }


def call_openai_workspace_synthesis(
    *,
    api_key: str,
    company_name: str,
    website_url: str,
    profile: dict[str, Any],
    analysis: dict[str, Any],
    source_ledger: list[dict[str, Any]],
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "model": os.environ.get(MODEL_ENV, DEFAULT_MODEL),
        "input": [
            {
                "role": "system",
                "content": (
                    "You are Gaia, Grounded's Phase 1 strategy synthesis engine. "
                    "Create an evidence-grounded company workspace from public source excerpts. "
                    "Never use Yoplait data unless the submitted company is Yoplait. "
                    "If evidence is weak, state the gap directly instead of inventing specifics. "
                    "Every source URL must come from the supplied source ledger."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "company_name": company_name,
                        "website_url": website_url,
                        "deterministic_profile": profile,
                        "deterministic_analysis": analysis,
                        "source_ledger": ok_source_summaries(source_ledger),
                        "document_count": len(documents),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "workspace_draft",
                "strict": True,
                "schema": WORKSPACE_SCHEMA,
            }
        },
    }
    data = post_openai_response(api_key, payload)
    return json.loads(extract_response_text(data))


def post_openai_response(api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read(4000).decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI API returned HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def extract_response_text(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        for part in item.get("content", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                return part["text"]
            if part.get("type") == "refusal":
                raise RuntimeError(str(part.get("refusal") or "Model refused the request."))
    raise RuntimeError("OpenAI response did not include output text.")


def fallback_workspace_draft(
    company_name: str,
    website_url: str,
    profile: dict[str, Any],
    analysis: dict[str, Any],
    source_ledger: list[dict[str, Any]],
) -> dict[str, Any]:
    company_name = company_name or profile.get("market") or "Company"
    five_c = analysis.get("five_c", {}) if isinstance(analysis.get("five_c"), dict) else {}
    iag = analysis.get("iag", {}) if isinstance(analysis.get("iag"), dict) else {}
    summary = iag.get("summary", {}) if isinstance(iag.get("summary"), dict) else {}
    ok_urls = [str(entry.get("url")) for entry in source_ledger if entry.get("status") == "ok" and entry.get("url")]
    recommendation_text = first_string(summary.get("explanation")) or evidence_required(company_name)

    return {
        "profile": {
            "brand": str(profile.get("brand") or company_name.split()[0] or "Company"),
            "market": str(profile.get("market") or company_name),
            "project": str(profile.get("project") or "Website onboarding diagnostic"),
            "belief": str(profile.get("belief") or evidence_required(company_name)),
            "purpose": str(profile.get("purpose") or evidence_required(company_name)),
            "pursuits": {
                "product": str(profile.get("pursuits", {}).get("product") or evidence_required(company_name)),
                "platform": str(profile.get("pursuits", {}).get("platform") or evidence_required(company_name)),
                "impact": str(profile.get("pursuits", {}).get("impact") or evidence_required(company_name)),
            },
        },
        "gaps": {key: fallback_gap(key, iag.get(key), ok_urls) for key in FIVE_C_KEYS},
        "jobToBeDone": first_string(five_c.get("category", {}).get("to_state"))
        or first_string(five_c.get("consumer", {}).get("to_state"))
        or "Add stronger source evidence, then rerun onboarding to define the customer job.",
        "goals": fallback_goals(analysis.get("sustainability_goals", [])),
        "recommendation": {
            "title": "Evidence-Grounded Activation Sprint",
            "bestFor": f"{company_name} leadership, strategy, and sustainability teams.",
            "headline": first_sentence(recommendation_text),
            "overview": recommendation_text,
            "outcomes": string_list(summary.get("recommendations"))
            or ["Collect stronger source evidence.", "Rerun onboarding before client use."],
        },
        "strategicShifts": {
            "competition": shift_from_insight(five_c.get("competition")),
            "culture": simple_shift_from_insight(five_c.get("culture")),
            "consumer": simple_shift_from_insight(five_c.get("consumer")),
            "category": simple_shift_from_insight(five_c.get("category")),
            "job": first_string(five_c.get("category", {}).get("to_state"))
            or "Define the strongest source-backed job to be done after evidence collection.",
        },
        "competitors": [],
        "culturalDrivers": drivers_from_insight(five_c.get("culture"), ok_urls),
        "consumerStages": stages_from_insight(five_c.get("consumer"), ok_urls),
        "needStates": needs_from_insight(five_c.get("category"), ok_urls),
    }


def fallback_gap(key: str, raw: Any, ok_urls: list[str]) -> dict[str, Any]:
    insight = raw if isinstance(raw, dict) else {}
    recommendations = string_list(insight.get("recommendations"))
    return {
        "key": key,
        "label": {
            "summary": "Executive Summary",
            "company": "Company",
            "competition": "Competition",
            "culture": "Culture",
            "consumer": "Consumer",
            "category": "Category",
        }[key],
        "type": first_string(insight.get("gap_type")) or "Strategic",
        "importance": first_string(insight.get("importance")) or "Medium",
        "confidence": bounded_int(insight.get("confidence"), 35, 95, 42),
        "explanation": first_string(insight.get("explanation")) or "More source evidence is required before this gap can be scored reliably.",
        "nextSteps": recommendations or ["Add stronger source evidence.", "Rerun onboarding."],
        "evidence": evidence_blocks(insight.get("evidence"), ok_urls),
    }


def evidence_blocks(raw_evidence: Any, ok_urls: list[str]) -> list[dict[str, Any]]:
    items = raw_evidence if isinstance(raw_evidence, list) else []
    blocks: list[dict[str, Any]] = []
    for index, item in enumerate(items[:4], start=1):
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "")
        blocks.append(
            {
                "title": f"Evidence {index}",
                "summary": str(item.get("excerpt") or "Source evidence requires review."),
                "facts": [f"Source: {source or 'Backend analyzer'}"],
                "sources": [source or "Backend analyzer"],
                "links": link_list([source], ok_urls),
                "signals": [f"Evidence score: {bounded_int(item.get('score'), 0, 100, 50)}"],
                "implications": ["Use this evidence to refine the strategy before presenting."],
            }
        )
    if blocks:
        return blocks
    return [
        {
            "title": "Evidence Required",
            "summary": "No strong normalized source evidence was available for this module.",
            "facts": ["Add public source links, reports, or workshop notes."],
            "sources": ["Backend analyzer"],
            "links": [],
            "signals": ["Confidence is limited until evidence improves."],
            "implications": ["Rerun onboarding with stronger source material."],
        }
    ]


def fallback_goals(raw_goals: Any) -> list[dict[str, Any]]:
    goals = raw_goals if isinstance(raw_goals, list) else []
    output: list[dict[str, Any]] = []
    for index, goal in enumerate(goals[:8], start=1):
        if not isinstance(goal, dict):
            continue
        title = first_string(goal.get("title")) or f"Sustainability commitment {index}"
        output.append(
            {
                "id": slugify(title) or f"goal-{index}",
                "title": title,
                "description": first_string(goal.get("description")) or title,
                "category": normalize_category(goal.get("category")),
                "subcategory": first_string(goal.get("source")) or normalize_category(goal.get("category")),
                "type": infer_goal_type(f"{title} {goal.get('description', '')}"),
                "status": normalize_status(goal.get("status")),
                "startYear": 2026,
                "endYear": extract_year(first_string(goal.get("timeline")) or "", 2030),
                "flagship": index <= 3,
            }
        )
    return output


def shift_from_insight(raw: Any) -> dict[str, Any]:
    insight = raw if isinstance(raw, dict) else {}
    return {
        "from": first_string(insight.get("from_state"))
        or first_string(insight.get("summary"))
        or "No strong source-backed competitive position was identified yet.",
        "to": [
            first_string(insight.get("to_state"))
            or "Rerun onboarding with stronger competitive evidence.",
        ],
    }


def simple_shift_from_insight(raw: Any) -> dict[str, str]:
    insight = raw if isinstance(raw, dict) else {}
    return {
        "from": first_string(insight.get("from_state"))
        or first_string(insight.get("summary"))
        or "No strong source-backed signal was identified yet.",
        "to": first_string(insight.get("to_state")) or "Add stronger evidence and rerun onboarding.",
    }


def drivers_from_insight(raw: Any, ok_urls: list[str]) -> list[dict[str, Any]]:
    insight = raw if isinstance(raw, dict) else {}
    return [
        {
            "title": "Evidence-backed cultural signal",
            "selected": bool(insight.get("selected")),
            "confidence": bounded_int(insight.get("confidence"), 0, 100, 35),
            "observation": first_string(insight.get("summary")) or "No cultural signal was found yet.",
            "tension": first_string(insight.get("from_state")) or "More evidence is required.",
            "people": "Audience implications require stronger source evidence.",
            "implication": first_string(insight.get("to_state")) or "Rerun onboarding with stronger sources.",
            "sources": ok_urls[:3] or ["Backend analyzer"],
        }
    ]


def stages_from_insight(raw: Any, ok_urls: list[str]) -> list[dict[str, Any]]:
    insight = raw if isinstance(raw, dict) else {}
    return [
        {
            "stage": "Evaluation",
            "selected": bool(insight.get("selected")),
            "definition": first_string(insight.get("summary")) or "Consumer journey evidence is not yet strong enough.",
            "barrier": first_string(insight.get("from_state")) or "Add reviews, shopper evidence, or manual links.",
            "reviews": ok_urls[:2] or ["No review evidence was collected."],
        }
    ]


def needs_from_insight(raw: Any, ok_urls: list[str]) -> list[dict[str, Any]]:
    insight = raw if isinstance(raw, dict) else {}
    return [
        {
            "name": "Source-backed category need",
            "selected": bool(insight.get("selected")),
            "score": bounded_int(insight.get("confidence"), 0, 100, 35),
            "description": first_string(insight.get("summary"))
            or "Category need state requires stronger source evidence.",
        }
    ]


def sanitize_workspace_draft(
    draft: dict[str, Any],
    fallback: dict[str, Any],
    source_ledger: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(draft, dict):
        return fallback
    allowed_urls = [str(entry.get("url")) for entry in source_ledger if entry.get("status") == "ok" and entry.get("url")]
    output = {**fallback, **draft}
    output["profile"] = merge_dict(fallback["profile"], draft.get("profile"))
    output["gaps"] = sanitize_gaps(draft.get("gaps"), fallback["gaps"], allowed_urls)
    output["goals"] = list_or(fallback["goals"], draft.get("goals"))[:10]
    output["recommendation"] = merge_dict(fallback["recommendation"], draft.get("recommendation"))
    output["strategicShifts"] = merge_dict(fallback["strategicShifts"], draft.get("strategicShifts"))
    output["competitors"] = list_or([], draft.get("competitors"))[:8]
    output["culturalDrivers"] = list_or(fallback["culturalDrivers"], draft.get("culturalDrivers"))[:8]
    output["consumerStages"] = list_or(fallback["consumerStages"], draft.get("consumerStages"))[:8]
    output["needStates"] = list_or(fallback["needStates"], draft.get("needStates"))[:8]
    output["jobToBeDone"] = first_string(draft.get("jobToBeDone")) or fallback["jobToBeDone"]
    return output


def sanitize_gaps(raw: Any, fallback: dict[str, Any], allowed_urls: list[str]) -> dict[str, Any]:
    raw_gaps = raw if isinstance(raw, dict) else {}
    output: dict[str, Any] = {}
    for key in FIVE_C_KEYS:
        gap = merge_dict(fallback[key], raw_gaps.get(key))
        evidence = []
        for block in list_or(fallback[key]["evidence"], gap.get("evidence")):
            if not isinstance(block, dict):
                continue
            next_block = merge_dict(evidence_blocks([], allowed_urls)[0], block)
            next_block["links"] = sanitize_links(next_block.get("links"), allowed_urls)
            evidence.append(next_block)
        gap["evidence"] = evidence[:6] or fallback[key]["evidence"]
        output[key] = gap
    return output


def sanitize_competitors(raw: list[Any], source_ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed_urls = [str(entry.get("url")) for entry in source_ledger if entry.get("status") == "ok" and entry.get("url")]
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = first_string(item.get("name"))
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        output.append(
            {
                "name": name[:80],
                "selected": False,
                "confidence": bounded_int(item.get("confidence"), 0, 100, 55),
                "rationale": first_string(item.get("rationale")) or "Suggested from public evidence.",
                "source_links": [url for url in string_list(item.get("source_links")) if url in allowed_urls][:5],
            }
        )
    return output[:8]


def source_quality_warnings(source_ledger: list[dict[str, Any]]) -> list[str]:
    warnings = []
    skipped = [entry for entry in source_ledger if entry.get("status") != "ok"]
    if skipped:
        warnings.append(f"{len(skipped)} source(s) were skipped or errored; see source ledger.")
    if not any(entry.get("status") == "ok" for entry in source_ledger):
        warnings.append("No usable public website source was collected.")
    return warnings


def ok_source_summaries(source_ledger: list[dict[str, Any]]) -> list[dict[str, str]]:
    summaries = []
    for entry in source_ledger:
        if entry.get("status") != "ok":
            continue
        summaries.append(
            {
                "url": str(entry.get("url") or ""),
                "type": str(entry.get("type") or "website"),
                "title": str(entry.get("title") or ""),
                "excerpt": str(entry.get("excerpt") or "")[:5000],
            }
        )
    return summaries[:12]


def link_list(urls: list[str], allowed_urls: list[str]) -> list[dict[str, str]]:
    return [{"label": url, "url": url, "type": "source"} for url in urls if url in allowed_urls]


def sanitize_links(raw: Any, allowed_urls: list[str]) -> list[dict[str, str]]:
    links = raw if isinstance(raw, list) else []
    output = []
    for item in links:
        if not isinstance(item, dict):
            continue
        url = first_string(item.get("url"))
        if url not in allowed_urls:
            continue
        output.append(
            {
                "label": first_string(item.get("label")) or url,
                "url": url,
                "type": first_string(item.get("type")) or "source",
            }
        )
    return output


def merge_dict(fallback: dict[str, Any], value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return fallback
    output = {**fallback}
    for key, item in value.items():
        if isinstance(output.get(key), dict) and isinstance(item, dict):
            output[key] = merge_dict(output[key], item)
        else:
            output[key] = item
    return output


def list_or(fallback: list[Any], value: Any) -> list[Any]:
    return value if isinstance(value, list) else fallback


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def first_string(value: Any) -> str:
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def first_sentence(text: str) -> str:
    return text.split(". ")[0].strip() or text


def bounded_int(value: Any, lower: int, upper: int, fallback: int) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return fallback
    return max(lower, min(upper, number))


def evidence_required(company_name: str) -> str:
    return f"{company_name} requires stronger public source evidence before this field can be synthesized reliably."


def normalize_category(value: Any) -> str:
    text = first_string(value).lower()
    return text if text in {"environmental", "social", "governance"} else "social"


def normalize_status(value: Any) -> str:
    text = first_string(value).lower()
    return text if text in {"planned", "active", "complete"} else "planned"


def infer_goal_type(text: str) -> str:
    lower = text.lower()
    if "policy" in lower:
        return "policy"
    if any(term in lower for term in ("target", "reduce", "increase", "by 20", "by 30", "net zero")):
        return "target"
    return "initiative"


def extract_year(text: str, fallback: int) -> int:
    years = [int(match) for match in __import__("re").findall(r"\b20\d{2}\b", text)]
    return years[-1] if years else fallback


def slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]


def object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or list(properties),
        "additionalProperties": False,
    }


string_schema = {"type": "string"}
number_schema = {"type": "number"}
boolean_schema = {"type": "boolean"}
string_array_schema = {"type": "array", "items": string_schema}

link_schema = object_schema({"label": string_schema, "url": string_schema, "type": string_schema})
evidence_schema = object_schema(
    {
        "title": string_schema,
        "summary": string_schema,
        "facts": string_array_schema,
        "sources": string_array_schema,
        "links": {"type": "array", "items": link_schema},
        "signals": string_array_schema,
        "implications": string_array_schema,
    }
)
gap_schema = object_schema(
    {
        "key": {"type": "string", "enum": list(FIVE_C_KEYS)},
        "label": string_schema,
        "type": string_schema,
        "importance": string_schema,
        "confidence": number_schema,
        "explanation": string_schema,
        "nextSteps": string_array_schema,
        "evidence": {"type": "array", "items": evidence_schema},
    }
)

WORKSPACE_SCHEMA = object_schema(
    {
        "profile": object_schema(
            {
                "brand": string_schema,
                "market": string_schema,
                "project": string_schema,
                "belief": string_schema,
                "purpose": string_schema,
                "pursuits": object_schema(
                    {
                        "product": string_schema,
                        "platform": string_schema,
                        "impact": string_schema,
                    }
                ),
            }
        ),
        "gaps": object_schema({key: gap_schema for key in FIVE_C_KEYS}),
        "jobToBeDone": string_schema,
        "goals": {
            "type": "array",
            "items": object_schema(
                {
                    "id": string_schema,
                    "title": string_schema,
                    "description": string_schema,
                    "category": {"type": "string", "enum": ["environmental", "social", "governance"]},
                    "subcategory": string_schema,
                    "type": {"type": "string", "enum": ["target", "initiative", "policy"]},
                    "status": {"type": "string", "enum": ["planned", "active", "complete"]},
                    "startYear": number_schema,
                    "endYear": number_schema,
                    "flagship": boolean_schema,
                }
            ),
        },
        "recommendation": object_schema(
            {
                "title": string_schema,
                "bestFor": string_schema,
                "headline": string_schema,
                "overview": string_schema,
                "outcomes": string_array_schema,
            }
        ),
        "strategicShifts": object_schema(
            {
                "competition": object_schema({"from": string_schema, "to": string_array_schema}),
                "culture": object_schema({"from": string_schema, "to": string_schema}),
                "consumer": object_schema({"from": string_schema, "to": string_schema}),
                "category": object_schema({"from": string_schema, "to": string_schema}),
                "job": string_schema,
            }
        ),
        "competitors": {
            "type": "array",
            "items": object_schema(
                {
                    "name": string_schema,
                    "selected": boolean_schema,
                    "position": string_schema,
                    "purpose": string_schema,
                    "profit": string_schema,
                }
            ),
        },
        "culturalDrivers": {
            "type": "array",
            "items": object_schema(
                {
                    "title": string_schema,
                    "selected": boolean_schema,
                    "confidence": number_schema,
                    "observation": string_schema,
                    "tension": string_schema,
                    "people": string_schema,
                    "implication": string_schema,
                    "sources": string_array_schema,
                }
            ),
        },
        "consumerStages": {
            "type": "array",
            "items": object_schema(
                {
                    "stage": string_schema,
                    "selected": boolean_schema,
                    "definition": string_schema,
                    "barrier": string_schema,
                    "reviews": string_array_schema,
                }
            ),
        },
        "needStates": {
            "type": "array",
            "items": object_schema(
                {
                    "name": string_schema,
                    "selected": boolean_schema,
                    "score": number_schema,
                    "description": string_schema,
                }
            ),
        },
    }
)

COMPETITOR_SCHEMA = object_schema(
    {
        "suggestions": {
            "type": "array",
            "items": object_schema(
                {
                    "name": string_schema,
                    "rationale": string_schema,
                    "confidence": number_schema,
                    "source_links": string_array_schema,
                    "selected": boolean_schema,
                }
            ),
        }
    }
)
