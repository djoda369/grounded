from __future__ import annotations

from statistics import mean

from core.phase1.schema import FIVE_C_KEYS, EvidenceSource, FiveCInsight, FiveCKey, IAGInsight, SustainabilityGoal

NUTRITION_TERMS = ("nutrition", "health", "children", "child", "calcium", "vitamin", "fortification", "bone")


class IAGIdentificationEngine:
    """Compares 5C market signals with sustainability commitments."""

    def analyze(
        self,
        five_c: dict[FiveCKey, FiveCInsight],
        goals: list[SustainabilityGoal],
    ) -> dict[FiveCKey | str, IAGInsight]:
        gaps: dict[FiveCKey | str, IAGInsight] = {}
        for key in FIVE_C_KEYS:
            gaps[key] = self.analyze_key(key, five_c[key], goals)
        gaps["summary"] = self.summarize(gaps)
        return gaps

    def analyze_key(
        self,
        key: FiveCKey,
        insight: FiveCInsight,
        goals: list[SustainabilityGoal],
    ) -> IAGInsight:
        nutrition_signal = contains_any(insight.summary, NUTRITION_TERMS) or contains_any(insight.from_state, NUTRITION_TERMS)
        nutrition_goals = [goal for goal in goals if contains_any(f"{goal.title} {goal.description}", NUTRITION_TERMS)]
        environmental_goals = [goal for goal in goals if goal.category == "environmental"]

        if nutrition_signal and not nutrition_goals and environmental_goals:
            explanation = (
                f"The {key} signal points toward a consumer-health or nutrition opportunity, but the extracted "
                "sustainability commitments are weighted toward environmental activity. This creates a strategic "
                "intention-action gap because the brand promise is not yet backed by measurable health outcomes."
            )
            recommendations = [
                "Add nutrition outcome KPIs to the sustainability scorecard.",
                "Link product reformulation and fortification work to annual impact reporting.",
                "Prioritize evidence that a customer can understand at the point of evaluation.",
            ]
            confidence = bounded_average([insight.confidence, *[goal.confidence for goal in environmental_goals[:3]]])
        elif insight.evidence and goals:
            explanation = (
                f"The {key} evidence is directionally supported by sustainability commitments, but the action pathway "
                "needs clearer ownership, metrics, and proof points before it is executive-ready."
            )
            recommendations = [
                "Name the owner, metric, and source evidence for each commitment tied to this insight.",
                "Show how the sustainability action improves the market-facing opportunity.",
                "Keep claims narrow enough to be defensible in client workshops.",
            ]
            confidence = bounded_average([insight.confidence, *[goal.confidence for goal in goals[:3]]])
        else:
            explanation = (
                f"The {key} gap cannot be scored with high confidence yet because source evidence or sustainability "
                "commitments are missing from the normalized input set."
            )
            recommendations = [
                "Add company reports, sustainability disclosures, workshop notes, and market evidence.",
                "Rerun ingestion before presenting this module to a client.",
            ]
            confidence = 42

        evidence = list(insight.evidence[:3])
        evidence.extend(goal_to_evidence(goal) for goal in goals[:2])
        return IAGInsight(
            key=key,
            gap_type="Strategic",
            importance="High" if confidence >= 70 else "Medium",
            confidence=confidence,
            explanation=explanation,
            recommendations=recommendations,
            evidence=dedupe_evidence(evidence),
        )

    def summarize(self, gaps: dict[FiveCKey | str, IAGInsight]) -> IAGInsight:
        child_gaps = [gap for key, gap in gaps.items() if key in FIVE_C_KEYS]
        confidence = bounded_average([gap.confidence for gap in child_gaps])
        high_confidence = max(child_gaps, key=lambda gap: gap.confidence)
        explanation = (
            "The largest current intention-action risk is strategic: Grounded should ensure that the strongest "
            "5C opportunity is translated into measurable sustainability actions and proof points. "
            f"The clearest signal is in {high_confidence.key}, where the analysis shows: {high_confidence.explanation}"
        )
        recommendations = [
            "Use a single executive scorecard for 5C opportunity, sustainability commitments, and IAG recommendations.",
            "Require each recommendation to include source evidence, metric, owner, and next action.",
            "Keep the assistant grounded by passing only normalized evidence and Grounded methodology into prompts.",
        ]
        evidence: list[EvidenceSource] = []
        for gap in child_gaps:
            evidence.extend(gap.evidence[:1])
        evidence = dedupe_evidence(evidence)
        return IAGInsight(
            key="summary",
            gap_type="Strategic",
            importance="High" if confidence >= 70 else "Medium",
            confidence=confidence,
            explanation=explanation,
            recommendations=recommendations,
            evidence=evidence[:6],
        )


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def bounded_average(values: list[int]) -> int:
    if not values:
        return 50
    return max(35, min(95, round(mean(values))))


def goal_to_evidence(goal: SustainabilityGoal) -> EvidenceSource:
    return EvidenceSource(
        source=goal.source or "sustainability_goal",
        excerpt=f"{goal.title}: {goal.description}",
        score=goal.confidence,
        metadata={"category": goal.category, "status": goal.status, "timeline": goal.timeline},
    )


def dedupe_evidence(evidence: list[EvidenceSource]) -> list[EvidenceSource]:
    seen: set[tuple[str, str]] = set()
    unique: list[EvidenceSource] = []
    for item in evidence:
        key = (item.source, item.excerpt)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
