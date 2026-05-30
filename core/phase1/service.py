from __future__ import annotations

from pathlib import Path
from typing import Iterable

from core.phase1.assistant import GroundedAssistant
from core.phase1.five_c import FiveCAnalysisEngine
from core.phase1.iag import IAGIdentificationEngine
from core.phase1.ingestion import ReportIngestionPipeline
from core.phase1.schema import IngestedDocument, Phase1Analysis, to_plain
from core.phase1.sustainability import SustainabilityGoalExtractor


class Phase1Analyzer:
    """Production-facing orchestration for Phase 1 analysis."""

    def __init__(
        self,
        ingestion: ReportIngestionPipeline | None = None,
        five_c: FiveCAnalysisEngine | None = None,
        sustainability: SustainabilityGoalExtractor | None = None,
        iag: IAGIdentificationEngine | None = None,
        assistant: GroundedAssistant | None = None,
    ):
        self.ingestion = ingestion or ReportIngestionPipeline()
        self.five_c = five_c or FiveCAnalysisEngine()
        self.sustainability = sustainability or SustainabilityGoalExtractor()
        self.iag = iag or IAGIdentificationEngine()
        self.assistant = assistant or GroundedAssistant()

    def analyze_paths(self, paths: Iterable[str | Path], company_name: str) -> Phase1Analysis:
        documents = self.ingestion.ingest_paths(paths)
        return self.analyze_documents(documents, company_name)

    def analyze_texts(self, texts: Iterable[str | dict[str, str]], company_name: str) -> Phase1Analysis:
        documents = self.ingestion.ingest_texts(texts)
        return self.analyze_documents(documents, company_name)

    def analyze_documents(self, documents: list[IngestedDocument], company_name: str) -> Phase1Analysis:
        five_c = self.five_c.analyze(documents, company_name)
        goals = self.sustainability.extract(documents)
        iag = self.iag.analyze(five_c, goals)
        analysis = Phase1Analysis(
            company_name=company_name,
            documents=documents,
            five_c=five_c,
            sustainability_goals=goals,
            iag=iag,
            assistant_system_prompt="",
        )
        return Phase1Analysis(
            company_name=analysis.company_name,
            documents=analysis.documents,
            five_c=analysis.five_c,
            sustainability_goals=analysis.sustainability_goals,
            iag=analysis.iag,
            assistant_system_prompt=self.assistant.system_prompt(analysis),
        )

    def analyze_paths_json(self, paths: Iterable[str | Path], company_name: str) -> dict:
        return to_plain(self.analyze_paths(paths, company_name))

    def analyze_texts_json(self, texts: Iterable[str | dict[str, str]], company_name: str) -> dict:
        return to_plain(self.analyze_texts(texts, company_name))
