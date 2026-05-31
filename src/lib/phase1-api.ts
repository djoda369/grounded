import {
  companyProfile,
  competitors as defaultCompetitors,
  culturalDrivers as defaultCulturalDrivers,
  consumerStages as defaultConsumerStages,
  needStates as defaultNeedStates,
  recommendation,
  strategicShifts,
  type EvidenceBlock,
  type FiveCTab,
  type GapInsight,
  type SustainabilityGoal,
} from "@/data/gaia";

type BackendEvidence = {
  source: string;
  excerpt: string;
  score: number;
  metadata?: Record<string, unknown>;
};

type BackendIagInsight = {
  key: FiveCTab;
  gap_type: string;
  importance: string;
  confidence: number;
  explanation: string;
  recommendations: string[];
  evidence: BackendEvidence[];
};

type BackendStructuredGapInsight = {
  key: FiveCTab;
  label: string;
  type: string;
  gap_type?: string;
  importance: string;
  confidence: number;
  explanation: string;
  nextSteps?: string[];
  recommendations?: string[];
  evidence?: EvidenceBlock[];
  raw_evidence?: BackendEvidence[];
};

type BackendFiveCInsight = {
  summary: string;
  from_state: string;
  to_state: string;
  confidence: number;
};

type BackendSustainabilityGoal = {
  title: string;
  description: string;
  category: string;
  status: string;
  timeline: string;
  source: string;
  confidence: number;
};

type BackendFrontendSustainabilityGoal = SustainabilityGoal & {
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendCompanyBBP = {
  brand?: string;
  market?: string;
  belief?: string;
  purpose?: string;
  pursuits?: Partial<typeof companyProfile.pursuits>;
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendCompetitorProfile = {
  name: string;
  selected?: boolean;
  position?: string;
  purpose?: string;
  profit?: string;
  opportunity?: string;
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendCultureDriver = {
  title: string;
  selected?: boolean;
  confidence?: number;
  observation?: string;
  tension?: string;
  people?: string;
  people_impact?: string;
  implication?: string;
  sources?: string[];
  evidence?: EvidenceBlock[];
};

type BackendCultureAnalysis = {
  summary?: string;
  drivers?: BackendCultureDriver[];
  observation?: string;
  tension?: string;
  people_impact?: string;
  implication?: string;
  confidence?: number;
  sources?: string[];
  evidence?: EvidenceBlock[];
};

type BackendConsumerPersona = {
  name: string;
  selected?: boolean;
  description?: string;
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendConsumerStage = {
  stage: string;
  selected?: boolean;
  definition?: string;
  barrier?: string;
  reviews?: string[];
  signals?: string[];
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendConsumerAnalysis = {
  personas?: BackendConsumerPersona[];
  stages?: BackendConsumerStage[];
  journey_barrier?: string;
  reviews?: string[];
  signals?: string[];
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendNeedState = {
  name: string;
  selected?: boolean;
  score?: number;
  description?: string;
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendCategoryAnalysis = {
  need_states?: BackendNeedState[];
  primary_need?: string;
  score?: number;
  description?: string;
  confidence?: number;
  evidence?: EvidenceBlock[];
};

type BackendSustainabilityAnalysis = {
  goals?: BackendFrontendSustainabilityGoal[];
  flagship_count?: number;
  goal_mix?: Record<string, number>;
  reporting_year?: number;
  evidence?: EvidenceBlock[];
};

type BackendRecommendation = {
  title?: string;
  bestFor?: string;
  best_for?: string;
  headline?: string;
  overview?: string;
  outcomes?: string[];
  rationale?: string;
  evidence?: EvidenceBlock[];
};

export type FrontendCompetitor = (typeof defaultCompetitors)[number];
export type FrontendCultureDriver = (typeof defaultCulturalDrivers)[number];
export type FrontendConsumerStage = (typeof defaultConsumerStages)[number];
export type FrontendNeedState = (typeof defaultNeedStates)[number];
export type FrontendStrategicShifts = typeof strategicShifts;

export type WorkshopState = {
  competitors: FrontendCompetitor[];
  culture: FrontendCultureDriver[];
  consumer: FrontendConsumerStage[];
  category: FrontendNeedState[];
  strategic_shifts: FrontendStrategicShifts;
};

export type Phase1AnalysisResponse = {
  contract_version?: string;
  executive_summary?: string;
  analysis_mode?: string;
  llm_extraction_status?: string;
  llm_model?: string;
  llm_error?: string;
  company_name: string;
  documents?: unknown[];
  company_bbp?: BackendCompanyBBP;
  competitors?: BackendCompetitorProfile[];
  culture?: BackendCultureAnalysis;
  consumer?: BackendConsumerAnalysis;
  category?: BackendCategoryAnalysis;
  sustainability?: BackendSustainabilityAnalysis;
  recommendation?: BackendRecommendation;
  five_c: Partial<Record<Exclude<FiveCTab, "summary">, BackendFiveCInsight>>;
  sustainability_goals: BackendSustainabilityGoal[];
  iag: Partial<Record<FiveCTab, BackendIagInsight | BackendStructuredGapInsight>>;
  assistant_system_prompt: string;
};

export type UploadedEvidence = {
  id: string;
  source: string;
  kind: string;
  dataBase64: string;
};

export type AnalysisState = {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
};

export type ProjectSummary = {
  id: string;
  name: string;
  company_name: string;
  brand: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  last_analyzed_at: string | null;
};

export type ProjectDocument = {
  id: string;
  project_id: string;
  source: string;
  kind: string;
  checksum: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ProjectUiState = {
  profile?: typeof companyProfile | null;
  gaps?: Record<FiveCTab, GapInsight> | null;
  goals?: SustainabilityGoal[] | null;
  recommendation?: typeof recommendation | null;
  workshop?: WorkshopState | null;
  job_to_be_done?: string | null;
  active_page?: string | null;
  updated_at?: string | null;
};

export type ProjectAnalysisRecord = {
  id: string;
  project_id: string;
  analysis: Phase1AnalysisResponse;
  input_checksum: string;
  created_at: string;
  is_current: boolean;
};

export type ProjectBundle = {
  project: ProjectSummary;
  documents: ProjectDocument[];
  current_analysis: ProjectAnalysisRecord | null;
  ui_state: ProjectUiState | null;
};

export type ProjectAnalysisResult = {
  project_id: string;
  analysis_id: string;
  analysis: Phase1AnalysisResponse;
};

type Phase1Payload =
  | { company_name: string; text: string }
  | {
      company_name: string;
      documents: Array<
        | { source: string; kind: string; text: string }
        | { source: string; kind: string; data_base64: string }
      >;
    };

const fiveCKeys: FiveCTab[] = ["summary", "company", "competition", "culture", "consumer", "category"];

const labels: Record<FiveCTab, string> = {
  summary: "Executive Summary",
  company: "Company",
  competition: "Competition",
  culture: "Culture",
  consumer: "Consumer",
  category: "Category",
};

export async function requestPhase1Analysis(payload: Phase1Payload): Promise<Phase1AnalysisResponse> {
  const response = await fetch("/api/phase1/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Phase 1 analysis failed.");
  }
  return data as Phase1AnalysisResponse;
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const data = await apiJson<{ projects: ProjectSummary[] }>("/api/phase1/projects");
  return data.projects;
}

export async function createProject(payload: {
  name: string;
  company_name: string;
  brand?: string;
}): Promise<ProjectSummary> {
  return apiJson<ProjectSummary>("/api/phase1/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getProject(projectId: string): Promise<ProjectBundle> {
  return apiJson<ProjectBundle>(`/api/phase1/projects/${projectId}`);
}

export async function updateProject(
  projectId: string,
  payload: Partial<Pick<ProjectSummary, "name" | "company_name" | "brand" | "status">> & {
    ui_state?: ProjectUiState;
  },
): Promise<ProjectBundle> {
  return apiJson<ProjectBundle>(`/api/phase1/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function uploadProjectDocuments(
  projectId: string,
  uploads: UploadedEvidence[],
): Promise<ProjectDocument[]> {
  const data = await apiJson<{ documents: ProjectDocument[] }>(`/api/phase1/projects/${projectId}/documents`, {
    method: "POST",
    body: JSON.stringify({
      documents: uploads.map((upload) => ({
        source: upload.source,
        kind: upload.kind,
        data_base64: upload.dataBase64,
      })),
    }),
  });
  return data.documents;
}

export async function deleteProjectDocument(projectId: string, documentId: string): Promise<ProjectDocument[]> {
  const data = await apiJson<{ documents: ProjectDocument[] }>(
    `/api/phase1/projects/${projectId}/documents/${documentId}`,
    { method: "DELETE" },
  );
  return data.documents;
}

export async function requestProjectAnalysis(
  projectId: string,
  context?: string,
  workshopState?: WorkshopState,
): Promise<ProjectAnalysisResult> {
  return apiJson<ProjectAnalysisResult>(`/api/phase1/projects/${projectId}/analyze`, {
    method: "POST",
    body: JSON.stringify({ context: context || "", workshop_state: workshopState }),
  });
}

export async function fileToUploadedEvidence(file: File): Promise<UploadedEvidence> {
  const dataUrl = await readFileAsDataUrl(file);
  const dataBase64 = dataUrl.split(",", 2)[1] || "";
  return {
    id: `${file.name}-${file.size}-${file.lastModified}`,
    source: file.name,
    kind: file.name.split(".").pop()?.toLowerCase() || "txt",
    dataBase64,
  };
}

export function buildPhase1Payload(
  companyName: string,
  context: string,
  uploads: UploadedEvidence[],
  fallbackText: string,
): Phase1Payload {
  const documents = uploads.map((upload) => ({
    source: upload.source,
    kind: upload.kind,
    data_base64: upload.dataBase64,
  }));

  if (context.trim()) {
    documents.push({
      source: "Additional context",
      kind: "txt",
      data_base64: btoa(unescape(encodeURIComponent(context.trim()))),
    });
  }

  if (documents.length) {
    return { company_name: companyName, documents };
  }

  return { company_name: companyName, text: fallbackText };
}

export function mapPhase1ToFrontend(
  analysis: Phase1AnalysisResponse,
  currentProfile: typeof companyProfile,
) {
  const gaps = mapGaps(analysis);
  const goals = mapGoals(analysis.sustainability?.goals?.length ? analysis.sustainability.goals : analysis.sustainability_goals);
  const companyBbp = analysis.company_bbp;
  const companyInsight = analysis.five_c.company;
  const summary = normalizedGap(analysis.iag.summary);
  const category = analysis.five_c.category;
  const mappedRecommendation = mapRecommendation(analysis.recommendation, analysis.company_name, summary);
  const mappedStrategicShifts = mapStrategicShifts(analysis);

  return {
    gaps,
    goals,
    profile: {
      ...currentProfile,
      market: companyBbp?.market || analysis.company_name || currentProfile.market,
      brand: companyBbp?.brand || inferBrand(analysis.company_name, currentProfile.brand),
      belief: companyBbp?.belief || companyInsight?.from_state || companyInsight?.summary || currentProfile.belief,
      purpose: companyBbp?.purpose || companyInsight?.to_state || companyInsight?.summary || currentProfile.purpose,
      pursuits: {
        ...currentProfile.pursuits,
        ...companyBbp?.pursuits,
        impact: companyBbp?.pursuits?.impact || summary?.nextSteps?.[0] || currentProfile.pursuits.impact,
      },
    },
    jobToBeDone:
      mappedStrategicShifts.job ||
      analysis.category?.description ||
      category?.to_state ||
      analysis.five_c.consumer?.to_state ||
      summary?.nextSteps?.[0] ||
      "Translate the strongest 5C signal into measurable action, proof, and commercial impact.",
    recommendation: mappedRecommendation,
    competitors: mapCompetitors(analysis.competitors),
    culturalDrivers: mapCultureDrivers(analysis.culture),
    consumerStages: mapConsumerStages(analysis.consumer),
    needStates: mapNeedStates(analysis.category),
    strategicShifts: mappedStrategicShifts,
  };
}

export function buildBaselineEvidenceText(
  profile: typeof companyProfile,
  jobToBeDone: string,
  goals: SustainabilityGoal[],
  gaps: Record<FiveCTab, GapInsight>,
) {
  return [
    `Company: ${profile.market}`,
    `Belief: ${profile.belief}`,
    `Purpose: ${profile.purpose}`,
    `Product pursuit: ${profile.pursuits.product}`,
    `Platform pursuit: ${profile.pursuits.platform}`,
    `Impact pursuit: ${profile.pursuits.impact}`,
    `Job to be done: ${jobToBeDone}`,
    `Current IAG: ${gaps.summary.explanation}`,
    "Sustainability goals:",
    ...goals.map((goal) => `${goal.title}. ${goal.description}`),
  ].join("\n");
}

async function apiJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const response = await fetch(url, {
    ...init,
    headers,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Gaia API request failed.");
  }
  return data as T;
}

function mapGaps(analysis: Phase1AnalysisResponse): Record<FiveCTab, GapInsight> {
  return Object.fromEntries(
    fiveCKeys.map((key) => {
      const insight = normalizedGap(analysis.iag[key]);
      return [
        key,
        {
          key,
          label: insight?.label || labels[key],
          type: insight?.type || "Strategic",
          importance: insight?.importance || "Medium",
          confidence: clampPercent(insight?.confidence ?? 50),
          explanation:
            insight?.explanation ||
            `${labels[key]} needs more source evidence before Gaia can produce a reliable conclusion.`,
          nextSteps: insight?.nextSteps?.length
            ? insight.nextSteps
            : ["Add more source evidence.", "Run backend analysis again."],
          evidence: insight?.evidence?.length
            ? insight.evidence
            : mapEvidence(rawInsightEvidence(analysis.iag[key]), insight?.nextSteps),
        },
      ];
    }),
  ) as Record<FiveCTab, GapInsight>;
}

function normalizedGap(insight?: BackendIagInsight | BackendStructuredGapInsight): GapInsight | undefined {
  if (!insight) return undefined;
  if ("nextSteps" in insight || "label" in insight) {
    return {
      key: insight.key,
      label: insight.label || labels[insight.key],
      type: insight.type || insight.gap_type || "Strategic",
      importance: insight.importance,
      confidence: clampPercent(insight.confidence),
      explanation: insight.explanation,
      nextSteps: insight.nextSteps?.length ? insight.nextSteps : insight.recommendations || [],
      evidence: mapEvidenceBlocks(insight.evidence),
    };
  }
  return {
    key: insight.key,
    label: labels[insight.key],
    type: insight.gap_type || "Strategic",
    importance: insight.importance,
    confidence: clampPercent(insight.confidence),
    explanation: insight.explanation,
    nextSteps: insight.recommendations || [],
    evidence: mapEvidence(insight.evidence, insight.recommendations),
  };
}

function rawInsightEvidence(insight?: BackendIagInsight | BackendStructuredGapInsight): BackendEvidence[] {
  if (!insight) return [];
  if ("raw_evidence" in insight && insight.raw_evidence?.length) return insight.raw_evidence;
  if ("gap_type" in insight && Array.isArray((insight as BackendIagInsight).evidence)) {
    const evidence = (insight as BackendIagInsight).evidence;
    return evidence.filter(isBackendEvidence);
  }
  return [];
}

function mapEvidence(evidence?: BackendEvidence[], recommendations?: string[]): EvidenceBlock[] {
  if (!evidence?.length) {
    return [
      {
        title: "Evidence Required",
        summary: "Gaia did not receive enough normalized source evidence for this module.",
        facts: ["Add client reports, workshop notes, or research documents."],
        sources: ["Backend analyzer"],
        signals: ["Confidence is limited until evidence is added."],
        implications: recommendations || ["Rerun analysis with stronger source material."],
      },
    ];
  }

  return evidence.map((item, index) => ({
    title: `Evidence ${index + 1}: ${shortSource(item.source)}`,
    summary: item.excerpt,
    facts: metadataFacts(item.metadata),
    sources: [item.source],
    signals: [`Evidence score: ${Math.round(item.score)}%`],
    implications: recommendations?.slice(0, 2) || ["Use this source as a grounded proof point."],
  }));
}

function mapEvidenceBlocks(evidence?: EvidenceBlock[]): EvidenceBlock[] {
  return evidence?.filter(isEvidenceBlock) || [];
}

function mapGoals(goals: Array<BackendSustainabilityGoal | BackendFrontendSustainabilityGoal> = []): SustainabilityGoal[] {
  return goals.map((goal, index) => {
    if (isFrontendGoal(goal)) {
      return {
        id: goal.id,
        title: goal.title,
        description: goal.description,
        category: normalizeCategory(goal.category),
        subcategory: goal.subcategory,
        type: goal.type,
        status: normalizeStatus(goal.status),
        startYear: goal.startYear,
        endYear: goal.endYear,
        flagship: goal.flagship,
      };
    }
    const endYear = parseYear(goal.timeline, 2030);
    return {
      id: `${slugify(goal.title)}-${index + 1}`,
      title: goal.title,
      description: goal.description,
      category: normalizeCategory(goal.category),
      subcategory: goal.source ? shortSource(goal.source) : goal.category || "sustainability",
      type: inferGoalType(`${goal.title} ${goal.description}`),
      status: normalizeStatus(goal.status),
      startYear: Math.min(2026, endYear),
      endYear,
      flagship: goal.confidence >= 70 || index < 5,
    };
  });
}

function mapRecommendation(
  backendRecommendation: BackendRecommendation | undefined,
  companyName: string,
  summary: GapInsight | undefined,
) {
  if (backendRecommendation) {
    return {
      ...recommendation,
      title: backendRecommendation.title || recommendation.title,
      bestFor:
        backendRecommendation.bestFor ||
        backendRecommendation.best_for ||
        `${companyName || companyProfile.market} leadership, strategy, and sustainability teams.`,
      headline: backendRecommendation.headline || firstSentence(summary?.explanation || recommendation.headline),
      overview: backendRecommendation.overview || summary?.explanation || recommendation.overview,
      outcomes: backendRecommendation.outcomes?.length
        ? backendRecommendation.outcomes
        : summary?.nextSteps?.length
          ? summary.nextSteps
          : recommendation.outcomes,
    };
  }

  return {
    ...recommendation,
    title: "IAG Activation Sprint",
    bestFor: `${companyName || companyProfile.market} leadership, strategy, and sustainability teams.`,
    headline: firstSentence(summary?.explanation || recommendation.headline),
    overview: summary?.explanation || recommendation.overview,
    outcomes: summary?.nextSteps?.length ? summary.nextSteps : recommendation.outcomes,
  };
}

function mapCompetitors(profiles: BackendCompetitorProfile[] = []): FrontendCompetitor[] {
  return profiles.map((profile) => ({
    name: profile.name,
    selected: profile.selected ?? true,
    position: profile.position || "Competitive position needs more source evidence.",
    purpose: profile.purpose || "Competitor purpose needs more source evidence.",
    profit: profile.profit || profile.opportunity || "Add competitor evidence to define the opportunity.",
  }));
}

function mapCultureDrivers(culture?: BackendCultureAnalysis): FrontendCultureDriver[] {
  if (culture?.drivers?.length) {
    return culture.drivers.map((driver) => ({
      title: driver.title,
      selected: driver.selected ?? true,
      confidence: clampPercent(driver.confidence ?? culture.confidence ?? 50),
      observation: driver.observation || culture.observation || culture.summary || "Culture evidence needs more source material.",
      tension: driver.tension || culture.tension || "Cultural tension needs more source evidence.",
      people: driver.people || driver.people_impact || culture.people_impact || "People impact needs more source evidence.",
      implication: driver.implication || culture.implication || "Add cultural evidence and rerun analysis.",
      sources: driver.sources?.length ? driver.sources : culture.sources?.length ? culture.sources : ["Backend analyzer"],
    }));
  }

  if (!culture) return [];
  return [
    {
      title: "Culture signal",
      selected: true,
      confidence: clampPercent(culture.confidence ?? 50),
      observation: culture.observation || culture.summary || "Culture evidence needs more source material.",
      tension: culture.tension || "Cultural tension needs more source evidence.",
      people: culture.people_impact || "People impact needs more source evidence.",
      implication: culture.implication || "Add cultural evidence and rerun analysis.",
      sources: culture.sources?.length ? culture.sources : ["Backend analyzer"],
    },
  ];
}

function mapConsumerStages(consumer?: BackendConsumerAnalysis): FrontendConsumerStage[] {
  if (!consumer) return [];
  if (consumer.stages?.length) {
    return consumer.stages.map((stage) => ({
      stage: stage.stage,
      selected: stage.selected ?? true,
      definition: stage.definition || "Consumer stage definition needs more source evidence.",
      barrier: stage.barrier || consumer.journey_barrier || "Journey barrier needs more source evidence.",
      reviews: stage.reviews?.length
        ? stage.reviews
        : consumer.reviews?.length
          ? consumer.reviews
          : stage.signals?.length
            ? stage.signals
            : ["No review signals were found in the source evidence."],
    }));
  }
  return [
    {
      stage: "Evaluation",
      selected: true,
      definition: "The point where the audience compares claims, evidence, alternatives, and personal relevance.",
      barrier: consumer.journey_barrier || "Journey barrier needs more source evidence.",
      reviews: consumer.reviews?.length
        ? consumer.reviews
        : consumer.signals?.length
          ? consumer.signals
          : ["No review signals were found in the source evidence."],
    },
  ];
}

function mapNeedStates(category?: BackendCategoryAnalysis): FrontendNeedState[] {
  if (!category) return [];
  if (category.need_states?.length) {
    return category.need_states.map((need) => ({
      name: need.name,
      selected: need.selected ?? true,
      score: clampPercent(need.score ?? need.confidence ?? category.score ?? category.confidence ?? 50),
      description: need.description || category.description || "Need-state description needs more source evidence.",
    }));
  }
  return [
    {
      name: category.primary_need || "Category need state",
      selected: true,
      score: clampPercent(category.score ?? category.confidence ?? 50),
      description: category.description || "Need-state description needs more source evidence.",
    },
  ];
}

function mapStrategicShifts(analysis: Phase1AnalysisResponse): FrontendStrategicShifts {
  const competitors = mapCompetitors(analysis.competitors);
  const culture = analysis.culture;
  const consumer = analysis.consumer;
  const category = analysis.category;
  const competitionInsight = analysis.five_c.competition;
  const cultureInsight = analysis.five_c.culture;
  const consumerInsight = analysis.five_c.consumer;
  const categoryInsight = analysis.five_c.category;

  return {
    competition: {
      from:
        competitors.map((item) => item.position).filter(Boolean).join("\n") ||
        competitionInsight?.from_state ||
        competitionInsight?.summary ||
        strategicShifts.competition.from,
      to:
        competitors.map((item) => item.profit).filter(Boolean).length
          ? competitors.map((item) => item.profit).filter(Boolean)
          : [competitionInsight?.to_state || strategicShifts.competition.to[0]],
    },
    culture: {
      from: culture?.observation || cultureInsight?.from_state || cultureInsight?.summary || strategicShifts.culture.from,
      to: culture?.implication || cultureInsight?.to_state || strategicShifts.culture.to,
    },
    consumer: {
      from: consumer?.journey_barrier || consumerInsight?.from_state || consumerInsight?.summary || strategicShifts.consumer.from,
      to: consumer?.signals?.[0] || consumerInsight?.to_state || strategicShifts.consumer.to,
    },
    category: {
      from: category?.primary_need || categoryInsight?.from_state || categoryInsight?.summary || strategicShifts.category.from,
      to: category?.description || categoryInsight?.to_state || strategicShifts.category.to,
    },
    job:
      category?.description ||
      categoryInsight?.to_state ||
      consumer?.journey_barrier ||
      consumerInsight?.to_state ||
      strategicShifts.job,
  };
}

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error(`Could not read ${file.name}.`));
    reader.readAsDataURL(file);
  });
}

function isFrontendGoal(goal: BackendSustainabilityGoal | BackendFrontendSustainabilityGoal): goal is BackendFrontendSustainabilityGoal {
  return "id" in goal && "startYear" in goal && "endYear" in goal && "flagship" in goal;
}

function isEvidenceBlock(value: unknown): value is EvidenceBlock {
  return Boolean(
    value &&
      typeof value === "object" &&
      "title" in value &&
      "summary" in value &&
      "facts" in value &&
      "sources" in value &&
      "signals" in value &&
      "implications" in value,
  );
}

function isBackendEvidence(value: unknown): value is BackendEvidence {
  return Boolean(
    value &&
      typeof value === "object" &&
      "source" in value &&
      "excerpt" in value &&
      "score" in value,
  );
}

function normalizeCategory(category: string): SustainabilityGoal["category"] {
  if (category === "environmental" || category === "social" || category === "governance") {
    return category;
  }
  return "social";
}

function normalizeStatus(status: string): SustainabilityGoal["status"] {
  if (status === "planned" || status === "active" || status === "complete") {
    return status;
  }
  return "planned";
}

function inferGoalType(text: string): SustainabilityGoal["type"] {
  const lower = text.toLowerCase();
  if (lower.includes("policy")) return "policy";
  if (lower.includes("target") || lower.includes("reduce") || lower.includes("increase")) return "target";
  return "initiative";
}

function parseYear(text: string, fallback: number) {
  const years = Array.from(text.matchAll(/\b(20\d{2}|19\d{2})\b/g)).map((match) => Number(match[1]));
  return years.length ? years[years.length - 1] : fallback;
}

function metadataFacts(metadata?: Record<string, unknown>) {
  if (!metadata) return ["No metadata provided."];
  const facts = Object.entries(metadata).map(([key, value]) => `${titleCase(key)}: ${String(value)}`);
  return facts.length ? facts : ["No metadata provided."];
}

function shortSource(source: string) {
  return source.split(/[\\/]/).pop() || source || "source";
}

function inferBrand(companyName: string, fallback: string) {
  return companyName?.trim().split(/\s+/)[0] || fallback;
}

function firstSentence(text: string) {
  return text.split(/(?<=\.)\s+/)[0] || text;
}

function slugify(text: string) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48);
}

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function titleCase(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
