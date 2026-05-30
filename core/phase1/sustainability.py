from __future__ import annotations

import re

from core.phase1.five_c import split_sentences
from core.phase1.schema import IngestedDocument, SustainabilityGoal

CATEGORY_TERMS = {
    "environmental": (
        "climate",
        "emissions",
        "carbon",
        "net zero",
        "water",
        "waste",
        "circular",
        "biodiversity",
        "forest",
        "plastic",
        "packaging",
    ),
    "social": (
        "community",
        "health",
        "nutrition",
        "children",
        "wellbeing",
        "safety",
        "dei",
        "diversity",
        "inclusion",
        "food security",
    ),
    "governance": (
        "policy",
        "governance",
        "disclosure",
        "reporting",
        "accountability",
        "compliance",
        "science based",
    ),
}

GOAL_TERMS = (
    "goal",
    "target",
    "commitment",
    "ambition",
    "roadmap",
    "initiative",
    "pledge",
    "reporting",
    "achieve",
    "reduce",
    "increase",
    "improve",
)


class SustainabilityGoalExtractor:
    """Extracts sustainability goals from normalized reports and notes."""

    def extract(self, documents: list[IngestedDocument], limit: int = 12) -> list[SustainabilityGoal]:
        goals: list[SustainabilityGoal] = []
        seen: set[str] = set()
        for document in documents:
            for sentence in split_sentences(document.text):
                lower = sentence.lower()
                if not any(term in lower for term in GOAL_TERMS):
                    continue
                if not any(term in lower for terms in CATEGORY_TERMS.values() for term in terms):
                    continue
                title = title_from_sentence(sentence)
                key = title.lower()
                if key in seen:
                    continue
                seen.add(key)
                goals.append(
                    SustainabilityGoal(
                        title=title,
                        description=sentence,
                        category=classify_category(sentence),
                        status=classify_status(sentence),
                        timeline=extract_timeline(sentence),
                        source=document.source,
                        confidence=goal_confidence(sentence),
                    )
                )
                if len(goals) >= limit:
                    return goals
        return goals


def classify_category(text: str) -> str:
    lower = text.lower()
    scores = {
        category: sum(1 for term in terms if term in lower)
        for category, terms in CATEGORY_TERMS.items()
    }
    return max(scores, key=scores.get)


def classify_status(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ("completed", "achieved", "delivered")):
        return "complete"
    if any(term in lower for term in ("currently", "in progress", "active", "launched")):
        return "active"
    return "planned"


def extract_timeline(text: str) -> str:
    years = re.findall(r"\b20\d{2}\b", text)
    if not years:
        return ""
    if len(years) == 1:
        return years[0]
    return f"{years[0]} - {years[-1]}"


def title_from_sentence(sentence: str) -> str:
    cleaned = re.sub(r"^[\W\d_]+", "", sentence).strip()
    words = cleaned.split()
    title = " ".join(words[:9]).strip(" .,:;")
    return title[:90] or "Sustainability commitment"


def goal_confidence(sentence: str) -> int:
    lower = sentence.lower()
    score = 58
    if any(term in lower for term in ("target", "goal", "commitment")):
        score += 12
    if re.search(r"\b\d+%|\b20\d{2}\b", sentence):
        score += 12
    if any(term in lower for term in ("measure", "kpi", "science based", "reporting")):
        score += 8
    return min(score, 92)
