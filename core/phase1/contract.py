from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.phase1.schema import (
    EvidenceSource,
    FiveCInsight,
    FiveCKey,
    IAGInsight,
    Phase1Analysis,
    SustainabilityGoal,
    to_plain,
)

CONTRACT_VERSION = "phase1.structured.v1"
DEFAULT_REPORTING_YEAR = 2026


@dataclass(frozen=True)
class FrontendEvidenceBlock:
    title: str
    summary: str
    facts: list[str]
    sources: list[str]
    signals: list[str]
    implications: list[str]


@dataclass(frozen=True)
class CompanyPursuits:
    product: str
    platform: str
    impact: str


@dataclass(frozen=True)
class CompanyBBP:
    brand: str
    market: str
    belief: str
    purpose: str
    pursuits: CompanyPursuits
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class CompetitorProfile:
    name: str
    selected: bool
    position: str
    purpose: str
    profit: str
    opportunity: str
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class CultureDriver:
    title: str
    selected: bool
    confidence: int
    observation: str
    tension: str
    people_impact: str
    people: str
    implication: str
    sources: list[str]
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class CultureAnalysis:
    summary: str
    drivers: list[CultureDriver]
    observation: str
    tension: str
    people_impact: str
    implication: str
    confidence: int
    sources: list[str]
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class ConsumerPersona:
    name: str
    selected: bool
    description: str
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class ConsumerStage:
    stage: str
    selected: bool
    definition: str
    barrier: str
    reviews: list[str]
    signals: list[str]
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class ConsumerAnalysis:
    personas: list[ConsumerPersona]
    stages: list[ConsumerStage]
    journey_barrier: str
    reviews: list[str]
    signals: list[str]
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class NeedState:
    name: str
    selected: bool
    score: int
    description: str
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class CategoryAnalysis:
    need_states: list[NeedState]
    primary_need: str
    score: int
    description: str
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class FrontendSustainabilityGoal:
    id: str
    title: str
    description: str
    category: str
    subcategory: str
    type: str
    status: str
    startYear: int
    endYear: int
    flagship: bool
    confidence: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class SustainabilityAnalysis:
    goals: list[FrontendSustainabilityGoal]
    flagship_count: int
    goal_mix: dict[str, int]
    reporting_year: int
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class FrontendGapInsight:
    key: str
    label: str
    type: str
    importance: str
    confidence: int
    explanation: str
    nextSteps: list[str]
    evidence: list[FrontendEvidenceBlock]
    gap_type: str
    recommendations: list[str]
    raw_evidence: list[EvidenceSource] = field(default_factory=list)


@dataclass(frozen=True)
class Recommendation:
    title: str
    bestFor: str
    headline: str
    overview: str
    outcomes: list[str]
    rationale: str
    evidence: list[FrontendEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class Phase1StructuredContract:
    contract_version: str
    company_name: str
    documents: list[Any]
    executive_summary: str
    company_bbp: CompanyBBP
    competitors: list[CompetitorProfile]
    culture: CultureAnalysis
    consumer: ConsumerAnalysis
    category: CategoryAnalysis
    sustainability: SustainabilityAnalysis
    iag: dict[str, FrontendGapInsight]
    recommendation: Recommendation
    five_c: dict[FiveCKey, FiveCInsight]
    sustainability_goals: list[SustainabilityGoal]
    assistant_system_prompt: str
    analysis_mode: str = "deterministic"
    llm_extraction_status: str = "not_attempted"
    llm_model: str = ""


class StructuredPhase1ContractBuilder:
    """Builds the frontend-ready Phase 1 contract from the stable internal model."""

    def build(self, analysis: Phase1Analysis) -> dict[str, Any]:
        company = self._company_bbp(analysis)
        iag = self._iag(analysis)
        sustainability = self._sustainability(analysis)
        contract = Phase1StructuredContract(
            contract_version=CONTRACT_VERSION,
            company_name=analysis.company_name,
            documents=analysis.documents,
            executive_summary=iag["summary"].explanation,
            company_bbp=company,
            competitors=self._competitors(analysis, iag),
            culture=self._culture(analysis, iag),
            consumer=self._consumer(analysis, iag),
            category=self._category(analysis, iag),
            sustainability=sustainability,
            iag=iag,
            recommendation=self._recommendation(analysis, iag),
            five_c=analysis.five_c,
            sustainability_goals=analysis.sustainability_goals,
            assistant_system_prompt=analysis.assistant_system_prompt,
        )
        return to_plain(contract)

    def _company_bbp(self, analysis: Phase1Analysis) -> CompanyBBP:
        company = analysis.five_c["company"]
        category = analysis.five_c["category"]
        culture = analysis.five_c["culture"]
        summary = analysis.iag["summary"]
        company_gap = analysis.iag["company"]
        brand = brand_from_company(analysis.company_name)
        return CompanyBBP(
            brand=brand,
            market=analysis.company_name,
            belief=company.from_state or company.summary,
            purpose=company.to_state or company.summary,
            pursuits=CompanyPursuits(
                product=category.to_state or category.summary,
                platform=culture.to_state or culture.summary,
                impact=first_item(company_gap.recommendations, summary.recommendations, fallback=summary.explanation),
            ),
            confidence=company.confidence,
            evidence=evidence_blocks(company.evidence, company_gap.recommendations),
        )

    def _competitors(
        self,
        analysis: Phase1Analysis,
        iag: dict[str, FrontendGapInsight],
    ) -> list[CompetitorProfile]:
        competition = analysis.five_c["competition"]
        names = extract_competitor_names(competition.evidence, analysis.company_name)
        if not names:
            missing = missing_evidence_blocks(
                "Competitive Evidence Required",
                (
                    "No named competitors were found in the normalized source evidence. Gaia can identify a "
                    "competitive whitespace, but needs competitor names, claims, positioning, or market notes to "
                    "profile specific rivals."
                ),
                iag["competition"].nextSteps,
            )
            return [
                CompetitorProfile(
                    name="Competitive whitespace",
                    selected=True,
                    position="No named competitor position was evidenced in the uploaded material.",
                    purpose="Competitor purpose is missing from the source set.",
                    profit="Use the whitespace to define a sharper proof-led position before comparing rivals.",
                    opportunity="Add competitor evidence to turn this placeholder into named competitor profiles.",
                    confidence=min(45, competition.confidence),
                    evidence=missing,
                )
            ]

        profiles: list[CompetitorProfile] = []
        for index, name in enumerate(names[:6]):
            opportunity = first_item(
                iag["competition"].nextSteps,
                [competition.to_state],
                fallback="Clarify the opportunity against this named competitor with more evidence.",
            )
            profiles.append(
                CompetitorProfile(
                    name=name,
                    selected=index < 3,
                    position=competition.from_state or competition.summary,
                    purpose=f"{name} is referenced as a competitor, but its explicit purpose needs stronger source evidence.",
                    profit=opportunity,
                    opportunity=opportunity,
                    confidence=max(35, min(competition.confidence - 5, 90)),
                    evidence=evidence_blocks(competition.evidence, iag["competition"].nextSteps),
                )
            )
        return profiles

    def _culture(
        self,
        analysis: Phase1Analysis,
        iag: dict[str, FrontendGapInsight],
    ) -> CultureAnalysis:
        insight = analysis.five_c["culture"]
        gap = iag["culture"]
        drivers = [
            CultureDriver(
                title=driver_title(item.excerpt, "Cultural driver"),
                selected=index == 0,
                confidence=insight.confidence,
                observation=item.excerpt,
                tension=gap.explanation,
                people_impact=people_impact_for("culture"),
                people=people_impact_for("culture"),
                implication=first_item(gap.nextSteps, fallback=insight.to_state),
                sources=[item.source],
                evidence=evidence_blocks([item], gap.nextSteps),
            )
            for index, item in enumerate(insight.evidence[:4])
        ]
        if not drivers:
            drivers = [
                CultureDriver(
                    title="Culture evidence required",
                    selected=False,
                    confidence=35,
                    observation="No strong culture evidence was found in the ingested documents.",
                    tension=gap.explanation,
                    people_impact="People impact cannot be assessed until cultural source evidence is added.",
                    people="People impact cannot be assessed until cultural source evidence is added.",
                    implication=first_item(gap.nextSteps),
                    sources=["Backend analyzer"],
                    evidence=missing_evidence_blocks("Culture Evidence Required", gap.explanation, gap.nextSteps),
                )
            ]
        return CultureAnalysis(
            summary=insight.summary,
            drivers=drivers,
            observation=insight.from_state,
            tension=gap.explanation,
            people_impact=people_impact_for("culture"),
            implication=first_item(gap.nextSteps, fallback=insight.to_state),
            confidence=insight.confidence,
            sources=unique_sources(insight.evidence),
            evidence=evidence_blocks(insight.evidence, gap.nextSteps),
        )

    def _consumer(
        self,
        analysis: Phase1Analysis,
        iag: dict[str, FrontendGapInsight],
    ) -> ConsumerAnalysis:
        insight = analysis.five_c["consumer"]
        gap = iag["consumer"]
        evidence = evidence_blocks(insight.evidence, gap.nextSteps)
        reviews = extract_reviews(insight.evidence)
        signals = [item.excerpt for item in insight.evidence[:4]]
        personas = [
            ConsumerPersona(
                name="Primary audience",
                selected=True,
                description=insight.summary,
                confidence=insight.confidence,
                evidence=evidence,
            )
        ]
        stages = [
            ConsumerStage(
                stage="Evaluation",
                selected=True,
                definition="The point where the audience compares claims, evidence, alternatives, and personal relevance.",
                barrier=insight.from_state,
                reviews=reviews,
                signals=signals,
                confidence=insight.confidence,
                evidence=evidence,
            )
        ]
        if not insight.evidence:
            personas[0] = ConsumerPersona(
                name="Audience evidence required",
                selected=False,
                description="No strong consumer or shopper evidence was found in the normalized source set.",
                confidence=35,
                evidence=missing_evidence_blocks("Consumer Evidence Required", gap.explanation, gap.nextSteps),
            )
            stages[0] = ConsumerStage(
                stage="Evaluation",
                selected=False,
                definition="Consumer journey analysis needs source evidence before it can be scored reliably.",
                barrier=gap.explanation,
                reviews=[],
                signals=[],
                confidence=35,
                evidence=missing_evidence_blocks("Consumer Evidence Required", gap.explanation, gap.nextSteps),
            )
        return ConsumerAnalysis(
            personas=personas,
            stages=stages,
            journey_barrier=insight.from_state,
            reviews=reviews,
            signals=signals,
            confidence=insight.confidence,
            evidence=evidence if insight.evidence else missing_evidence_blocks("Consumer Evidence Required", gap.explanation, gap.nextSteps),
        )

    def _category(
        self,
        analysis: Phase1Analysis,
        iag: dict[str, FrontendGapInsight],
    ) -> CategoryAnalysis:
        insight = analysis.five_c["category"]
        gap = iag["category"]
        need_states = [
            NeedState(
                name=driver_title(item.excerpt, "Category need state"),
                selected=index == 0,
                score=clamp_percent(insight.confidence - index * 4),
                description=item.excerpt,
                confidence=insight.confidence,
                evidence=evidence_blocks([item], gap.nextSteps),
            )
            for index, item in enumerate(insight.evidence[:5])
        ]
        if not need_states:
            need_states = [
                NeedState(
                    name="Category evidence required",
                    selected=False,
                    score=35,
                    description="No strong category need-state evidence was found in the ingested documents.",
                    confidence=35,
                    evidence=missing_evidence_blocks("Category Evidence Required", gap.explanation, gap.nextSteps),
                )
            ]
        primary = next((need for need in need_states if need.selected), need_states[0])
        return CategoryAnalysis(
            need_states=need_states,
            primary_need=primary.name,
            score=primary.score,
            description=primary.description or insight.summary,
            confidence=insight.confidence,
            evidence=evidence_blocks(insight.evidence, gap.nextSteps),
        )

    def _sustainability(self, analysis: Phase1Analysis) -> SustainabilityAnalysis:
        frontend_goals = [
            frontend_goal(goal, index)
            for index, goal in enumerate(analysis.sustainability_goals)
        ]
        if not frontend_goals:
            placeholder_evidence = missing_evidence_blocks(
                "Sustainability Evidence Required",
                "No sustainability goals were extracted from the normalized source evidence.",
                ["Add sustainability reports, targets, commitments, or disclosure notes and rerun analysis."],
            )
            frontend_goals = [
                FrontendSustainabilityGoal(
                    id="sustainability-evidence-required",
                    title="Sustainability evidence required",
                    description="No sustainability goal could be extracted from the uploaded material.",
                    category="governance",
                    subcategory="evidence",
                    type="initiative",
                    status="planned",
                    startYear=DEFAULT_REPORTING_YEAR,
                    endYear=DEFAULT_REPORTING_YEAR,
                    flagship=False,
                    confidence=35,
                    evidence=placeholder_evidence,
                )
            ]
        mix = Counter(goal.category for goal in frontend_goals)
        evidence: list[FrontendEvidenceBlock] = []
        for goal in frontend_goals:
            evidence.extend(goal.evidence[:1])
        return SustainabilityAnalysis(
            goals=frontend_goals,
            flagship_count=sum(1 for goal in frontend_goals if goal.flagship),
            goal_mix=dict(mix),
            reporting_year=max((goal.endYear for goal in frontend_goals), default=DEFAULT_REPORTING_YEAR),
            evidence=evidence or missing_evidence_blocks(
                "Sustainability Evidence Required",
                "No sustainability evidence was available.",
                ["Add sustainability source material."],
            ),
        )

    def _iag(self, analysis: Phase1Analysis) -> dict[str, FrontendGapInsight]:
        return {key: frontend_gap(insight) for key, insight in analysis.iag.items()}

    def _recommendation(
        self,
        analysis: Phase1Analysis,
        iag: dict[str, FrontendGapInsight],
    ) -> Recommendation:
        summary = iag["summary"]
        return Recommendation(
            title="IAG Activation Sprint",
            bestFor=f"{analysis.company_name} leadership, strategy, and sustainability teams.",
            headline=first_sentence(summary.explanation),
            overview=summary.explanation,
            outcomes=summary.nextSteps,
            rationale=summary.explanation,
            evidence=summary.evidence,
        )


def frontend_gap(insight: IAGInsight) -> FrontendGapInsight:
    return FrontendGapInsight(
        key=str(insight.key),
        label=gap_label(str(insight.key)),
        type=insight.gap_type,
        importance=insight.importance,
        confidence=insight.confidence,
        explanation=insight.explanation,
        nextSteps=insight.recommendations,
        evidence=evidence_blocks(insight.evidence, insight.recommendations),
        gap_type=insight.gap_type,
        recommendations=insight.recommendations,
        raw_evidence=insight.evidence,
    )


def frontend_goal(goal: SustainabilityGoal, index: int) -> FrontendSustainabilityGoal:
    end_year = parse_year(goal.timeline, DEFAULT_REPORTING_YEAR)
    start_year = min(DEFAULT_REPORTING_YEAR, end_year)
    evidence = evidence_blocks(
        [
            EvidenceSource(
                source=goal.source or "sustainability_goal",
                excerpt=f"{goal.title}: {goal.description}",
                score=goal.confidence,
                metadata={"category": goal.category, "status": goal.status, "timeline": goal.timeline},
            )
        ],
        ["Use this commitment as a scored proof point in the Phase 1 IAG analysis."],
    )
    return FrontendSustainabilityGoal(
        id=f"{slugify(goal.title)}-{index + 1}",
        title=goal.title,
        description=goal.description,
        category=normalize_goal_category(goal.category),
        subcategory=short_source(goal.source) if goal.source else normalize_goal_category(goal.category),
        type=infer_goal_type(f"{goal.title} {goal.description}"),
        status=normalize_goal_status(goal.status),
        startYear=start_year,
        endYear=end_year,
        flagship=goal.confidence >= 70 or index < 5,
        confidence=goal.confidence,
        evidence=evidence,
    )


def evidence_blocks(
    evidence: list[EvidenceSource],
    implications: list[str] | None = None,
) -> list[FrontendEvidenceBlock]:
    if not evidence:
        return missing_evidence_blocks(
            "Evidence Required",
            "Gaia did not receive enough normalized source evidence for this part of the analysis.",
            implications or ["Add source evidence and rerun backend analysis."],
        )
    return [
        FrontendEvidenceBlock(
            title=f"Evidence {index + 1}: {short_source(item.source)}",
            summary=item.excerpt,
            facts=metadata_facts(item.metadata),
            sources=[item.source],
            signals=[f"Evidence score: {round(item.score)}%"],
            implications=(implications or ["Use this source as a grounded proof point."])[:2],
        )
        for index, item in enumerate(evidence)
    ]


def missing_evidence_blocks(title: str, summary: str, implications: list[str] | None = None) -> list[FrontendEvidenceBlock]:
    return [
        FrontendEvidenceBlock(
            title=title,
            summary=summary,
            facts=["Missing normalized source evidence."],
            sources=["Backend analyzer"],
            signals=["Confidence is limited until evidence is added."],
            implications=implications or ["Add stronger source material and rerun analysis."],
        )
    ]


def extract_competitor_names(evidence: list[EvidenceSource], company_name: str) -> list[str]:
    names: list[str] = []
    for item in evidence:
        text = item.excerpt
        for match in re.finditer(
            r"(?:competitors?|rivals?|alternatives?)\s+(?:include|includes|are|such as|like)\s+([^.;:]+)",
            text,
            flags=re.IGNORECASE,
        ):
            names.extend(split_names(match.group(1)))
        for match in re.finditer(r"(?:against|versus|vs\.)\s+([A-Z][A-Za-z0-9&'. -]{2,60})", text):
            names.append(match.group(1).strip())

    excluded = {company_name.lower(), brand_from_company(company_name).lower(), "brands", "brand"}
    unique: list[str] = []
    for name in names:
        cleaned = clean_name(name)
        if not cleaned or cleaned.lower() in excluded or cleaned.lower().startswith("broad "):
            continue
        if cleaned not in unique:
            unique.append(cleaned)
    return unique


def split_names(value: str) -> list[str]:
    cleaned = re.sub(r"\([^)]*\)", "", value)
    return [
        piece.strip(" ,")
        for piece in re.split(r",| and | & ", cleaned)
        if piece.strip(" ,")
    ]


def clean_name(value: str) -> str:
    value = re.sub(r"\b(focus|focused|position|positioning|with|while|rather|than)\b.*$", "", value, flags=re.IGNORECASE)
    value = value.strip(" .,-")
    return value[:80]


def extract_reviews(evidence: list[EvidenceSource]) -> list[str]:
    reviews: list[str] = []
    for item in evidence:
        quoted = re.findall(r"\"([^\"]{12,220})\"", item.excerpt)
        if quoted:
            reviews.extend(quoted)
        elif any(term in item.excerpt.lower() for term in ("review", "said", "comment", "complain")):
            reviews.append(item.excerpt)
    return reviews[:6]


def driver_title(text: str, fallback: str) -> str:
    words = re.sub(r"^[\W\d_]+", "", text).strip().split()
    if not words:
        return fallback
    return " ".join(words[:8]).strip(" .,:;")[:90]


def first_item(*groups: list[str], fallback: str = "Add more source evidence and rerun analysis.") -> str:
    for group in groups:
        for item in group:
            if str(item).strip():
                return str(item).strip()
    return fallback


def unique_sources(evidence: list[EvidenceSource]) -> list[str]:
    sources: list[str] = []
    for item in evidence:
        if item.source not in sources:
            sources.append(item.source)
    return sources or ["Backend analyzer"]


def metadata_facts(metadata: dict[str, Any] | None) -> list[str]:
    if not metadata:
        return ["No metadata provided."]
    facts = [f"{title_case(key)}: {value}" for key, value in metadata.items()]
    return facts or ["No metadata provided."]


def people_impact_for(key: str) -> str:
    if key == "culture":
        return "People need a simpler bridge between broad intention and practical action."
    return "People impact needs more source evidence before it can be scored reliably."


def brand_from_company(company_name: str) -> str:
    return company_name.strip().split()[0] if company_name.strip() else "Company"


def gap_label(key: str) -> str:
    labels = {
        "summary": "Executive Summary",
        "company": "Company",
        "competition": "Competition",
        "culture": "Culture",
        "consumer": "Consumer",
        "category": "Category",
    }
    return labels.get(key, title_case(key))


def short_source(source: str) -> str:
    return Path(source).name or source or "source"


def parse_year(text: str, fallback: int) -> int:
    years = [int(match) for match in re.findall(r"\b(20\d{2}|19\d{2})\b", text or "")]
    return years[-1] if years else fallback


def normalize_goal_category(category: str) -> str:
    if category in {"environmental", "social", "governance"}:
        return category
    return "social"


def normalize_goal_status(status: str) -> str:
    if status in {"planned", "active", "complete"}:
        return status
    return "planned"


def infer_goal_type(text: str) -> str:
    lower = text.lower()
    if "policy" in lower:
        return "policy"
    if any(term in lower for term in ("target", "reduce", "increase")):
        return "target"
    return "initiative"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "goal"


def first_sentence(text: str) -> str:
    return re.split(r"(?<=\.)\s+", text.strip(), maxsplit=1)[0] if text.strip() else ""


def clamp_percent(value: int) -> int:
    return max(0, min(100, round(value)))


def title_case(value: str) -> str:
    return re.sub(r"\b\w", lambda match: match.group(0).upper(), value.replace("_", " "))
