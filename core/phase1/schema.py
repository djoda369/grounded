from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Literal

FiveCKey = Literal["company", "competition", "culture", "consumer", "category"]

FIVE_C_KEYS: tuple[FiveCKey, ...] = (
    "company",
    "competition",
    "culture",
    "consumer",
    "category",
)


@dataclass(frozen=True)
class IngestedDocument:
    id: str
    source: str
    kind: str
    text: str
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceSource:
    source: str
    excerpt: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FiveCInsight:
    key: FiveCKey
    title: str
    summary: str
    from_state: str
    to_state: str
    confidence: int
    evidence: list[EvidenceSource] = field(default_factory=list)
    selected: bool = True


@dataclass(frozen=True)
class SustainabilityGoal:
    title: str
    description: str
    category: str
    status: str = "planned"
    timeline: str = ""
    source: str = ""
    confidence: int = 70


@dataclass(frozen=True)
class IAGInsight:
    key: FiveCKey | Literal["summary"]
    gap_type: str
    importance: str
    confidence: int
    explanation: str
    recommendations: list[str]
    evidence: list[EvidenceSource] = field(default_factory=list)


@dataclass(frozen=True)
class Phase1Analysis:
    company_name: str
    documents: list[IngestedDocument]
    five_c: dict[FiveCKey, FiveCInsight]
    sustainability_goals: list[SustainabilityGoal]
    iag: dict[FiveCKey | Literal["summary"], IAGInsight]
    assistant_system_prompt: str


def to_plain(value: Any) -> Any:
    """Convert dataclasses nested inside lists/dicts into plain JSON-ready data."""
    if is_dataclass(value):
        return {key: to_plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, tuple):
        return [to_plain(item) for item in value]
    return value
