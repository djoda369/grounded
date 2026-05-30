from __future__ import annotations

import re
from collections import Counter

from core.phase1.schema import FIVE_C_KEYS, EvidenceSource, FiveCInsight, FiveCKey, IngestedDocument

KEYWORDS: dict[FiveCKey, tuple[str, ...]] = {
    "company": (
        "belief",
        "purpose",
        "mission",
        "brand",
        "business",
        "product",
        "service",
        "impact",
        "ambition",
        "commitment",
    ),
    "competition": (
        "competition",
        "competitor",
        "market",
        "positioning",
        "alternative",
        "differentiation",
        "rival",
        "share",
        "category leader",
    ),
    "culture": (
        "culture",
        "trend",
        "social",
        "behavior",
        "behaviour",
        "narrative",
        "trust",
        "transparency",
        "simplicity",
        "change",
    ),
    "consumer": (
        "consumer",
        "customer",
        "shopper",
        "parent",
        "buyer",
        "persona",
        "barrier",
        "review",
        "purchase",
        "choice",
    ),
    "category": (
        "category",
        "need",
        "needstate",
        "yogurt",
        "yoghurt",
        "dairy",
        "nutrition",
        "fortification",
        "calcium",
        "vitamin",
    ),
}

TITLES: dict[FiveCKey, str] = {
    "company": "Company belief, purpose, and pursuits",
    "competition": "Competitive positioning opportunity",
    "culture": "Cultural drivers and tensions",
    "consumer": "Consumer journey barriers",
    "category": "Category need states",
}

TO_STATE: dict[FiveCKey, str] = {
    "company": "Translate stated purpose into measurable product, platform, and impact priorities.",
    "competition": "Prioritize a defensible market position that competitors are not credibly owning.",
    "culture": "Connect cultural tension to a simple, proof-led behavior change opportunity.",
    "consumer": "Identify the highest-friction purchase journey barrier and the proof needed to overcome it.",
    "category": "Select the need state most likely to convert purpose into category growth.",
}


class FiveCAnalysisEngine:
    """Deterministic 5C extractor with stable evidence scoring."""

    def analyze(self, documents: list[IngestedDocument], company_name: str = "the company") -> dict[FiveCKey, FiveCInsight]:
        return {key: self.analyze_key(key, documents, company_name) for key in FIVE_C_KEYS}

    def analyze_key(
        self,
        key: FiveCKey,
        documents: list[IngestedDocument],
        company_name: str = "the company",
    ) -> FiveCInsight:
        evidence = self.find_evidence(key, documents)
        summary = self.summarize(key, evidence, company_name)
        from_state = evidence[0].excerpt if evidence else f"No strong {key} evidence was found in the ingested documents."
        confidence = confidence_from_evidence(evidence)
        return FiveCInsight(
            key=key,
            title=TITLES[key],
            summary=summary,
            from_state=from_state,
            to_state=TO_STATE[key],
            confidence=confidence,
            evidence=evidence,
            selected=bool(evidence),
        )

    def find_evidence(self, key: FiveCKey, documents: list[IngestedDocument], limit: int = 6) -> list[EvidenceSource]:
        terms = KEYWORDS[key]
        candidates: list[EvidenceSource] = []
        for document in documents:
            for sentence in split_sentences(document.text):
                score = score_sentence(sentence, terms)
                if score <= 0:
                    continue
                candidates.append(
                    EvidenceSource(
                        source=document.source,
                        excerpt=sentence,
                        score=score,
                        metadata={"document_id": document.id, "kind": document.kind},
                    )
                )
        candidates.sort(key=lambda item: (-item.score, item.source, item.excerpt))
        return candidates[:limit]

    def summarize(self, key: FiveCKey, evidence: list[EvidenceSource], company_name: str) -> str:
        if not evidence:
            return (
                f"{company_name} does not yet have enough normalized source material to generate a reliable "
                f"{key} insight. Add company materials, reports, workshop notes, or source links and rerun analysis."
            )

        terms = Counter()
        for item in evidence:
            for term in KEYWORDS[key]:
                if term in item.excerpt.lower():
                    terms[term] += 1
        leading_terms = ", ".join(term for term, _ in terms.most_common(3))
        lead = evidence[0].excerpt
        return (
            f"The strongest {key} signal for {company_name} centers on {leading_terms or 'the available evidence'}. "
            f"{lead}"
        )


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [chunk.strip() for chunk in chunks if 40 <= len(chunk.strip()) <= 700]


def score_sentence(sentence: str, terms: tuple[str, ...]) -> float:
    lower = sentence.lower()
    matches = sum(1 for term in terms if term in lower)
    if matches == 0:
        return 0
    density = min(len(sentence) / 220, 2.0)
    return round(matches * 10 + density, 2)


def confidence_from_evidence(evidence: list[EvidenceSource]) -> int:
    if not evidence:
        return 35
    unique_sources = len({item.source for item in evidence})
    score = 55 + min(len(evidence), 6) * 5 + unique_sources * 4
    return max(35, min(score, 95))
