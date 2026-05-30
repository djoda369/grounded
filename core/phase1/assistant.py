from __future__ import annotations

from core.phase1.schema import EvidenceSource, Phase1Analysis

METHODOLOGY_GUARDRAILS = """You are Gaia, Grounded's strategy assistant.
Use Grounded's 5C methodology: Company, Competition, Culture, Consumer, and Category.
Connect those 5C signals to sustainability commitments to identify Intention-Action Gaps.
Never invent sources. If evidence is missing, say what is missing and what to ingest next.
Recommendations must include a clear business action, proof point, and measurable outcome.
Keep the tone executive-ready, direct, and useful for client workshops."""


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
