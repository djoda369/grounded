import {
  companyProfile,
  recommendation,
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
