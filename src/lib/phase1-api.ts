import {
  companyProfile,
  competitors,
  culturalDrivers,
  consumerStages,
  needStates,
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

export type Phase1AnalysisResponse = {
  company_name: string;
  five_c: Partial<Record<Exclude<FiveCTab, "summary">, BackendFiveCInsight>>;
  sustainability_goals: BackendSustainabilityGoal[];
  iag: Partial<Record<FiveCTab, BackendIagInsight>>;
  assistant_system_prompt: string;
};

export type UploadedEvidence = {
  id: string;
  source: string;
  kind: string;
  dataBase64: string;
};

export type SourceSettings = {
  maxSources: 3 | 5 | 10;
  enabledSourceTypes: {
    website: boolean;
    manual_links: boolean;
    search: boolean;
    reddit: boolean;
    youtube: boolean;
    reviews: boolean;
    social_links: boolean;
  };
};

export type SourceLedgerEntry = {
  url: string;
  type: keyof SourceSettings["enabledSourceTypes"] | string;
  title: string;
  fetched_at: string;
  status: "ok" | "skipped" | "error";
  excerpt: string;
  error?: string;
};

export type CompetitorSuggestion = {
  name: string;
  rationale: string;
  confidence: number;
  source_links: string[];
  selected: boolean;
};

export type WorkspaceDraft = {
  profile: typeof companyProfile;
  gaps: Record<FiveCTab, GapInsight>;
  jobToBeDone: string;
  goals: SustainabilityGoal[];
  recommendation: typeof recommendation;
  strategicShifts: typeof strategicShifts;
  competitors: typeof competitors;
  culturalDrivers: typeof culturalDrivers;
  consumerStages: typeof consumerStages;
  needStates: typeof needStates;
};

export type AnalysisState = {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
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

type OnboardingPayload = {
  website_url: string;
  company_name?: string;
  source_settings: SourceSettings;
  manual_links: string[];
  documents: Array<{ source: string; kind: string; data_base64: string }>;
};

export type OnboardingResponse = {
  profile: typeof companyProfile;
  source_ledger: SourceLedgerEntry[];
  source_settings: SourceSettings;
  analysis: Phase1AnalysisResponse;
  workspace_draft?: WorkspaceDraft;
  synthesis_status?: "ai_generated" | "fallback_no_key" | "fallback_model_error" | "fallback_insufficient_evidence";
  warnings?: string[];
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
  let response: Response;
  try {
    response = await fetch("/api/phase1/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw new Error(
      error instanceof Error
        ? `Phase 1 backend is unreachable: ${error.message}`
        : "Phase 1 backend is unreachable.",
    );
  }

  const responseText = await response.text();
  const data = parseJsonResponse(responseText, response);

  if (!response.ok) {
    throw new Error(data?.error || "Phase 1 analysis failed.");
  }
  return data as Phase1AnalysisResponse;
}

export async function requestOnboarding(payload: OnboardingPayload): Promise<OnboardingResponse> {
  const data = await postJson("/api/phase1/onboard", payload, "Company onboarding failed.");
  return data as OnboardingResponse;
}

export async function requestCompetitorSuggestions(payload: {
  profile: typeof companyProfile;
  website_url: string;
  source_settings: SourceSettings;
  source_ledger: SourceLedgerEntry[];
}): Promise<CompetitorSuggestion[]> {
  const data = await postJson(
    "/api/phase1/competitors/suggest",
    payload,
    "Competitor suggestion failed.",
  );
  return Array.isArray(data?.suggestions) ? (data.suggestions as CompetitorSuggestion[]) : [];
}

async function postJson(path: string, payload: unknown, fallbackError: string) {
  let response: Response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw new Error(
      error instanceof Error
        ? `Phase 1 backend is unreachable: ${error.message}`
        : "Phase 1 backend is unreachable.",
    );
  }

  const responseText = await response.text();
  const data = parseJsonResponse(responseText, response);
  if (!response.ok) {
    throw new Error(data?.error || fallbackError);
  }
  return data;
}

function parseJsonResponse(responseText: string, response: Response) {
  if (!responseText.trim()) {
    throw new Error(
      response.ok
        ? "Phase 1 backend returned an empty response."
        : `Phase 1 backend returned ${response.status} ${
            response.statusText || "without a response body"
          }. Make sure the local API is running at http://127.0.0.1:8787.`,
    );
  }

  try {
    return JSON.parse(responseText);
  } catch {
    throw new Error(
      response.ok
        ? "Phase 1 backend returned a non-JSON response."
        : `Phase 1 backend returned ${response.status} ${response.statusText || "with a non-JSON response"}.`,
    );
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringOr(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback;
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

export function uploadedEvidenceToDocuments(uploads: UploadedEvidence[]) {
  return uploads.map((upload) => ({
    source: upload.source,
    kind: upload.kind,
    data_base64: upload.dataBase64,
  }));
}

export function mapPhase1ToFrontend(
  analysis: Phase1AnalysisResponse,
  currentProfile: typeof companyProfile,
) {
  const gaps = mapGaps(analysis);
  const goals = mapGoals(analysis.sustainability_goals);
  const companyInsight = analysis.five_c.company;
  const summary = analysis.iag.summary;
  const category = analysis.five_c.category;

  return {
    gaps,
    goals,
    profile: {
      ...currentProfile,
      market: analysis.company_name || currentProfile.market,
      brand: inferBrand(analysis.company_name, currentProfile.brand),
      belief: companyInsight?.from_state || companyInsight?.summary || currentProfile.belief,
      purpose: companyInsight?.to_state || companyInsight?.summary || currentProfile.purpose,
      pursuits: {
        ...currentProfile.pursuits,
        impact: summary?.recommendations?.[0] || currentProfile.pursuits.impact,
      },
    },
    jobToBeDone:
      category?.to_state ||
      analysis.five_c.consumer?.to_state ||
      summary?.recommendations?.[0] ||
      "Translate the strongest 5C signal into measurable action, proof, and commercial impact.",
    recommendation: {
      ...recommendation,
      title: "IAG Activation Sprint",
      bestFor: `${analysis.company_name || currentProfile.market} leadership, strategy, and sustainability teams.`,
      headline: firstSentence(summary?.explanation || recommendation.headline),
      overview: summary?.explanation || recommendation.overview,
      outcomes: summary?.recommendations?.length ? summary.recommendations : recommendation.outcomes,
    },
  };
}

export function mapOnboardingToFrontend(response: OnboardingResponse): WorkspaceDraft {
  const fallback = fallbackWorkspaceDraft(response);
  return normalizeWorkspaceDraft(response.workspace_draft, fallback);
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

function mapGaps(analysis: Phase1AnalysisResponse): Record<FiveCTab, GapInsight> {
  return Object.fromEntries(
    fiveCKeys.map((key) => {
      const insight = analysis.iag[key];
      return [
        key,
        {
          key,
          label: labels[key],
          type: insight?.gap_type || "Strategic",
          importance: insight?.importance || "Medium",
          confidence: clampPercent(insight?.confidence ?? 50),
          explanation:
            insight?.explanation ||
            `${labels[key]} needs more source evidence before Gaia can produce a reliable conclusion.`,
          nextSteps: insight?.recommendations?.length
            ? insight.recommendations
            : ["Add more source evidence.", "Run backend analysis again."],
          evidence: mapEvidence(insight),
        },
      ];
    }),
  ) as Record<FiveCTab, GapInsight>;
}

function fallbackWorkspaceDraft(response: OnboardingResponse): WorkspaceDraft {
  const mapped = mapPhase1ToFrontend(response.analysis, response.profile);
  return {
    profile: mapped.profile,
    gaps: mapped.gaps,
    jobToBeDone: mapped.jobToBeDone,
    goals: mapped.goals,
    recommendation: mapped.recommendation,
    strategicShifts: strategicShiftsFromAnalysis(response.analysis),
    competitors: [],
    culturalDrivers: culturalDriversFromAnalysis(response.analysis),
    consumerStages: consumerStagesFromAnalysis(response.analysis),
    needStates: needStatesFromAnalysis(response.analysis),
  };
}

function normalizeWorkspaceDraft(value: unknown, fallback: WorkspaceDraft): WorkspaceDraft {
  if (!isRecord(value)) return fallback;
  return {
    profile: normalizeProfile(value.profile, fallback.profile),
    gaps: normalizeGaps(value.gaps, fallback.gaps),
    jobToBeDone: stringOr(value.jobToBeDone, fallback.jobToBeDone),
    goals: Array.isArray(value.goals)
      ? (value.goals as SustainabilityGoal[]).map(normalizeGoal).filter(Boolean)
      : fallback.goals,
    recommendation: normalizeRecommendation(value.recommendation, fallback.recommendation),
    strategicShifts: normalizeStrategicShifts(value.strategicShifts, fallback.strategicShifts),
    competitors: Array.isArray(value.competitors) ? (value.competitors as typeof competitors) : fallback.competitors,
    culturalDrivers: Array.isArray(value.culturalDrivers)
      ? (value.culturalDrivers as typeof culturalDrivers)
      : fallback.culturalDrivers,
    consumerStages: Array.isArray(value.consumerStages)
      ? (value.consumerStages as typeof consumerStages)
      : fallback.consumerStages,
    needStates: Array.isArray(value.needStates) ? (value.needStates as typeof needStates) : fallback.needStates,
  };
}

function normalizeProfile(value: unknown, fallback: typeof companyProfile) {
  if (!isRecord(value)) return fallback;
  const pursuits = isRecord(value.pursuits) ? value.pursuits : {};
  return {
    brand: stringOr(value.brand, fallback.brand),
    market: stringOr(value.market, fallback.market),
    project: stringOr(value.project, fallback.project),
    belief: stringOr(value.belief, fallback.belief),
    purpose: stringOr(value.purpose, fallback.purpose),
    pursuits: {
      product: stringOr(pursuits.product, fallback.pursuits.product),
      platform: stringOr(pursuits.platform, fallback.pursuits.platform),
      impact: stringOr(pursuits.impact, fallback.pursuits.impact),
    },
  };
}

function normalizeGaps(value: unknown, fallback: Record<FiveCTab, GapInsight>) {
  if (!isRecord(value)) return fallback;
  return Object.fromEntries(
    fiveCKeys.map((key) => {
      const gap = isRecord(value[key]) ? value[key] : {};
      return [
        key,
        {
          ...fallback[key],
          ...gap,
          key,
          confidence: clampPercent(Number(gap.confidence ?? fallback[key].confidence)),
          nextSteps: Array.isArray(gap.nextSteps)
            ? gap.nextSteps.map(String).filter(Boolean)
            : fallback[key].nextSteps,
          evidence: Array.isArray(gap.evidence)
            ? (gap.evidence as EvidenceBlock[])
            : fallback[key].evidence,
        },
      ];
    }),
  ) as Record<FiveCTab, GapInsight>;
}

function normalizeGoal(value: SustainabilityGoal): SustainabilityGoal {
  return {
    id: stringOr(value.id, slugify(value.title || "goal")),
    title: stringOr(value.title, "Evidence-backed commitment"),
    description: stringOr(value.description, "Commitment requires stronger source evidence."),
    category: normalizeCategory(value.category),
    subcategory: stringOr(value.subcategory, normalizeCategory(value.category)),
    type: value.type === "policy" || value.type === "target" || value.type === "initiative" ? value.type : "initiative",
    status: normalizeStatus(value.status),
    startYear: Number.isFinite(Number(value.startYear)) ? Number(value.startYear) : 2026,
    endYear: Number.isFinite(Number(value.endYear)) ? Number(value.endYear) : 2030,
    flagship: Boolean(value.flagship),
  };
}

function normalizeRecommendation(value: unknown, fallback: typeof recommendation) {
  if (!isRecord(value)) return fallback;
  return {
    ...fallback,
    title: stringOr(value.title, fallback.title),
    bestFor: stringOr(value.bestFor, fallback.bestFor),
    headline: stringOr(value.headline, fallback.headline),
    overview: stringOr(value.overview, fallback.overview),
    outcomes: Array.isArray(value.outcomes) ? value.outcomes.map(String).filter(Boolean) : fallback.outcomes,
  };
}

function normalizeStrategicShifts(value: unknown, fallback: typeof strategicShifts) {
  if (!isRecord(value)) return fallback;
  const competition = isRecord(value.competition) ? value.competition : {};
  const culture = isRecord(value.culture) ? value.culture : {};
  const consumer = isRecord(value.consumer) ? value.consumer : {};
  const category = isRecord(value.category) ? value.category : {};
  return {
    competition: {
      from: stringOr(competition.from, fallback.competition.from),
      to: Array.isArray(competition.to)
        ? competition.to.map(String).filter(Boolean)
        : fallback.competition.to,
    },
    culture: {
      from: stringOr(culture.from, fallback.culture.from),
      to: stringOr(culture.to, fallback.culture.to),
    },
    consumer: {
      from: stringOr(consumer.from, fallback.consumer.from),
      to: stringOr(consumer.to, fallback.consumer.to),
    },
    category: {
      from: stringOr(category.from, fallback.category.from),
      to: stringOr(category.to, fallback.category.to),
    },
    job: stringOr(value.job, fallback.job),
  };
}

function strategicShiftsFromAnalysis(analysis: Phase1AnalysisResponse): typeof strategicShifts {
  return {
    competition: {
      from: analysis.five_c.competition?.from_state || analysis.five_c.competition?.summary || "Competitive evidence is still insufficient.",
      to: [
        analysis.five_c.competition?.to_state ||
          "Collect stronger competitor and positioning evidence before defining the shift.",
      ],
    },
    culture: {
      from: analysis.five_c.culture?.from_state || analysis.five_c.culture?.summary || "Cultural evidence is still insufficient.",
      to: analysis.five_c.culture?.to_state || "Collect stronger cultural source evidence.",
    },
    consumer: {
      from: analysis.five_c.consumer?.from_state || analysis.five_c.consumer?.summary || "Consumer evidence is still insufficient.",
      to: analysis.five_c.consumer?.to_state || "Collect stronger consumer source evidence.",
    },
    category: {
      from: analysis.five_c.category?.from_state || analysis.five_c.category?.summary || "Category evidence is still insufficient.",
      to: analysis.five_c.category?.to_state || "Collect stronger category source evidence.",
    },
    job:
      analysis.five_c.category?.to_state ||
      analysis.five_c.consumer?.to_state ||
      "Define the job to be done after stronger source collection.",
  };
}

function culturalDriversFromAnalysis(analysis: Phase1AnalysisResponse): typeof culturalDrivers {
  const insight = analysis.five_c.culture;
  return [
    {
      title: "Evidence-backed cultural signal",
      selected: Boolean(insight?.summary),
      confidence: clampPercent(insight?.confidence ?? 35),
      observation: insight?.summary || "Cultural signal requires stronger source evidence.",
      tension: insight?.from_state || "No source-backed cultural tension was found yet.",
      people: "Audience implications require stronger source evidence.",
      implication: insight?.to_state || "Rerun onboarding with stronger sources.",
      sources: ["Backend analyzer"],
    },
  ];
}

function consumerStagesFromAnalysis(analysis: Phase1AnalysisResponse): typeof consumerStages {
  const insight = analysis.five_c.consumer;
  return [
    {
      stage: "Evaluation",
      selected: Boolean(insight?.summary),
      definition: insight?.summary || "Consumer journey signal requires stronger source evidence.",
      barrier: insight?.from_state || "No source-backed consumer barrier was found yet.",
      reviews: ["No review evidence was collected."],
    },
  ];
}

function needStatesFromAnalysis(analysis: Phase1AnalysisResponse): typeof needStates {
  const insight = analysis.five_c.category;
  return [
    {
      name: "Source-backed category need",
      selected: Boolean(insight?.summary),
      score: clampPercent(insight?.confidence ?? 35),
      description: insight?.summary || "Category need state requires stronger source evidence.",
    },
  ];
}

function mapEvidence(insight?: BackendIagInsight): EvidenceBlock[] {
  if (!insight?.evidence?.length) {
    return [
      {
        title: "Evidence Required",
        summary: "Gaia did not receive enough normalized source evidence for this module.",
        facts: ["Add client reports, workshop notes, or research documents."],
        sources: ["Backend analyzer"],
        signals: ["Confidence is limited until evidence is added."],
        implications: insight?.recommendations || ["Rerun analysis with stronger source material."],
      },
    ];
  }

  return insight.evidence.map((item, index) => ({
    title: `Evidence ${index + 1}: ${shortSource(item.source)}`,
    summary: item.excerpt,
    facts: metadataFacts(item.metadata),
    sources: [item.source],
    links: isHttpUrl(item.source)
      ? [{ label: shortSource(item.source), url: item.source, type: String(item.metadata?.kind || "source") }]
      : undefined,
    signals: [`Evidence score: ${Math.round(item.score)}%`],
    implications: insight.recommendations.slice(0, 2),
  }));
}

function mapGoals(goals: BackendSustainabilityGoal[]): SustainabilityGoal[] {
  return goals.map((goal, index) => {
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

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error(`Could not read ${file.name}.`));
    reader.readAsDataURL(file);
  });
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

function isHttpUrl(value: string) {
  return /^https?:\/\//i.test(value);
}
