import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowRight,
  BarChart3,
  Building2,
  CheckCircle2,
  Download,
  FileText,
  Gauge,
  Globe2,
  Home,
  ListChecks,
  Layers3,
  Leaf,
  LineChart,
  Maximize2,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  Trash2,
  Upload,
  Users,
} from "lucide-react";

import {
  companyProfile,
  competitors,
  culturalDrivers,
  consumerStages,
  gapInsights,
  initialGoals,
  needStates,
  pageOptions,
  recommendation,
  strategicShifts,
  type EvidenceBlock,
  type FiveCTab,
  type GapInsight,
  type PageKey,
  type SustainabilityGoal,
} from "@/data/gaia";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  buildBaselineEvidenceText,
  buildPhase1Payload,
  fileToUploadedEvidence,
  mapPhase1ToFrontend,
  requestPhase1Analysis,
  type AnalysisState,
  type UploadedEvidence,
} from "@/lib/phase1-api";
import groundedLogo from "@/assets/grounded-logo.png";
import iagLogo from "@/assets/iag-logo.png";
import baLogo from "@/assets/ba-logo.png";
import fwLogo from "@/assets/fw-logo.png";
import saLogo from "@/assets/sa-logo.png";

const workspaceStorageKey = "gaia-workspace-v1";

const fiveCTabs: Array<{
  key: FiveCTab;
  label: string;
  icon: typeof Building2;
}> = [
  { key: "summary", label: "Executive Summary", icon: Layers3 },
  { key: "company", label: "Company", icon: Building2 },
  { key: "competition", label: "Competition", icon: BarChart3 },
  { key: "culture", label: "Culture", icon: Globe2 },
  { key: "consumer", label: "Consumer", icon: Users },
  { key: "category", label: "Category", icon: Target },
];

const chartColors = ["#a3e635", "#38bdf8", "#fb7185", "#fbbf24", "#c084fc"];

function cloneGaps() {
  return Object.fromEntries(
    gapInsights.map((gap) => [gap.key, structuredClone(gap)]),
  ) as Record<FiveCTab, GapInsight>;
}

type RecommendationDraft = typeof recommendation;
type CompanyProfileDraft = typeof companyProfile;
type StrategicShiftDraft = typeof strategicShifts;
type StrategicShiftSection = Exclude<keyof StrategicShiftDraft, "job">;
type CompetitorDrafts = typeof competitors;
type CulturalDriverDrafts = typeof culturalDrivers;
type ConsumerStageDrafts = typeof consumerStages;
type NeedStateDrafts = typeof needStates;

type PersistedWorkspace = {
  version: 1;
  savedAt: string;
  context: string;
  uploadedEvidence: UploadedEvidence[];
  gapDrafts: Record<FiveCTab, GapInsight>;
  profile: CompanyProfileDraft;
  jobToBeDone: string;
  goals: SustainabilityGoal[];
  recommendation: RecommendationDraft;
  strategicShifts: StrategicShiftDraft;
  competitors: CompetitorDrafts;
  culturalDrivers: CulturalDriverDrafts;
  consumerStages: ConsumerStageDrafts;
  needStates: NeedStateDrafts;
};

function cloneDraft<T>(draft: T): T {
  return structuredClone(draft);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function restoreArray<T>(savedValue: unknown, defaultValue: T[]): T[] {
  return Array.isArray(savedValue)
    ? (savedValue as T[])
    : cloneDraft(defaultValue);
}

function loadPersistedWorkspace(): Partial<PersistedWorkspace> | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(workspaceStorageKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return isRecord(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function restoreGaps(savedGaps?: unknown) {
  const defaults = cloneGaps();
  if (!isRecord(savedGaps)) return defaults;

  return Object.fromEntries(
    fiveCTabs.map(({ key }) => {
      const saved = isRecord(savedGaps[key])
        ? (savedGaps[key] as Partial<GapInsight>)
        : undefined;
      return [
        key,
        {
          ...defaults[key],
          ...saved,
          nextSteps: Array.isArray(saved?.nextSteps)
            ? saved.nextSteps
            : defaults[key].nextSteps,
          evidence: Array.isArray(saved?.evidence)
            ? saved.evidence
            : defaults[key].evidence,
        },
      ];
    }),
  ) as Record<FiveCTab, GapInsight>;
}

function restoreStrategicShifts(savedShifts?: unknown) {
  if (!isRecord(savedShifts)) return cloneDraft(strategicShifts);

  return {
    competition: {
      ...strategicShifts.competition,
      ...(isRecord(savedShifts.competition) ? savedShifts.competition : {}),
      to: Array.isArray(
        (savedShifts.competition as { to?: unknown } | undefined)?.to,
      )
        ? (savedShifts.competition as { to: string[] }).to
        : strategicShifts.competition.to,
    },
    culture: {
      ...strategicShifts.culture,
      ...(isRecord(savedShifts.culture) ? savedShifts.culture : {}),
    },
    consumer: {
      ...strategicShifts.consumer,
      ...(isRecord(savedShifts.consumer) ? savedShifts.consumer : {}),
    },
    category: {
      ...strategicShifts.category,
      ...(isRecord(savedShifts.category) ? savedShifts.category : {}),
    },
    job:
      typeof savedShifts.job === "string"
        ? savedShifts.job
        : strategicShifts.job,
  };
}

function restoreProfile(savedProfile?: unknown) {
  if (!isRecord(savedProfile)) return cloneDraft(companyProfile);

  return {
    ...companyProfile,
    ...savedProfile,
    pursuits: {
      ...companyProfile.pursuits,
      ...(isRecord(savedProfile.pursuits) ? savedProfile.pursuits : {}),
    },
  };
}

function restoreRecommendation(savedRecommendation?: unknown) {
  if (!isRecord(savedRecommendation)) return cloneDraft(recommendation);

  return {
    ...recommendation,
    ...savedRecommendation,
    outcomes: Array.isArray(savedRecommendation.outcomes)
      ? savedRecommendation.outcomes
      : recommendation.outcomes,
  };
}

function App() {
  const savedWorkspace = useMemo(loadPersistedWorkspace, []);
  const [page, setPage] = useState<PageKey>("home");
  const [editMode, setEditMode] = useState(false);
  const [context, setContext] = useState(() => savedWorkspace?.context ?? "");
  const [activeGap, setActiveGap] = useState<FiveCTab>("summary");
  const [activeFiveC, setActiveFiveC] = useState<FiveCTab>("summary");
  const [gapDrafts, setGapDrafts] = useState<Record<FiveCTab, GapInsight>>(() =>
    restoreGaps(savedWorkspace?.gapDrafts),
  );
  const [profile, setProfile] = useState<CompanyProfileDraft>(() =>
    restoreProfile(savedWorkspace?.profile),
  );
  const [jobToBeDone, setJobToBeDone] = useState(
    () => savedWorkspace?.jobToBeDone ?? strategicShifts.job,
  );
  const [goals, setGoals] = useState<SustainabilityGoal[]>(() =>
    restoreArray(savedWorkspace?.goals, initialGoals),
  );
  const [rec, setRec] = useState<RecommendationDraft>(() =>
    restoreRecommendation(savedWorkspace?.recommendation),
  );
  const [strategicShiftDrafts, setStrategicShiftDrafts] =
    useState<StrategicShiftDraft>(() =>
      restoreStrategicShifts(savedWorkspace?.strategicShifts),
    );
  const [competitorDrafts, setCompetitorDrafts] = useState<CompetitorDrafts>(
    () =>
      restoreArray(
        savedWorkspace?.competitors,
        competitors,
      ) as CompetitorDrafts,
  );
  const [culturalDriverDrafts, setCulturalDriverDrafts] =
    useState<CulturalDriverDrafts>(
      () =>
        restoreArray(
          savedWorkspace?.culturalDrivers,
          culturalDrivers,
        ) as CulturalDriverDrafts,
    );
  const [consumerStageDrafts, setConsumerStageDrafts] =
    useState<ConsumerStageDrafts>(
      () =>
        restoreArray(
          savedWorkspace?.consumerStages,
          consumerStages,
        ) as ConsumerStageDrafts,
    );
  const [needStateDrafts, setNeedStateDrafts] = useState<NeedStateDrafts>(
    () =>
      restoreArray(savedWorkspace?.needStates, needStates) as NeedStateDrafts,
  );
  const [analysisState, setAnalysisState] = useState<AnalysisState>({
    status: "idle",
    message: "",
  });
  const [uploadedEvidence, setUploadedEvidence] = useState<UploadedEvidence[]>(
    () => restoreArray(savedWorkspace?.uploadedEvidence, []),
  );

  const flagshipCount = goals.filter((goal) => goal.flagship).length;
  const averageConfidence = Math.round(
    Object.values(gapDrafts).reduce((sum, gap) => sum + gap.confidence, 0) /
      Object.values(gapDrafts).length,
  );

  function announce(_message: string) {
    return;
  }

  function saveWorkspace(message = "Workspace saved.") {
    if (typeof window === "undefined") return;

    const workspace: PersistedWorkspace = {
      version: 1,
      savedAt: new Date().toISOString(),
      context,
      uploadedEvidence,
      gapDrafts,
      profile,
      jobToBeDone,
      goals,
      recommendation: rec,
      strategicShifts: strategicShiftDrafts,
      competitors: competitorDrafts,
      culturalDrivers: culturalDriverDrafts,
      consumerStages: consumerStageDrafts,
      needStates: needStateDrafts,
    };

    try {
      window.localStorage.setItem(
        workspaceStorageKey,
        JSON.stringify(workspace),
      );
      announce(message);
    } catch {
      const workspaceWithoutUploads = { ...workspace, uploadedEvidence: [] };
      try {
        window.localStorage.setItem(
          workspaceStorageKey,
          JSON.stringify(workspaceWithoutUploads),
        );
        announce(
          `${message} Uploaded files were not saved because browser storage is limited.`,
        );
      } catch {
        announce("Workspace could not be saved in this browser.");
      }
    }
  }

  async function exportPdf() {
    const { jsPDF } = await import("jspdf");
    const pdf = new jsPDF({ unit: "pt", format: "a4" });
    const width = pdf.internal.pageSize.getWidth();
    const margin = 48;
    const maxWidth = width - margin * 2;
    let y = 56;
    const lineHeight = 16;

    const write = (text: string, size = 10, gap = 8) => {
      pdf.setFontSize(size);
      const lines = pdf.splitTextToSize(text, maxWidth);
      for (const line of lines) {
        if (y > 760) {
          pdf.addPage();
          y = 56;
        }
        pdf.text(line, margin, y);
        y += lineHeight;
      }
      y += gap;
    };

    pdf.setFont("helvetica", "bold");
    write(
      `Gaia ${profile.market} - ${pageOptions.find((option) => option.key === page)?.label}`,
      16,
      14,
    );
    pdf.setFont("helvetica", "normal");
    write(`Exported view: ${new Date().toLocaleDateString()}`, 9, 12);
    write(gapDrafts.summary.explanation, 10, 12);
    write("Recommended next steps", 12, 6);
    gapDrafts.summary.nextSteps.forEach((step, index) =>
      write(`${index + 1}. ${step}`, 9, 4),
    );
    pdf.save("gaia-yoplait-iag-summary.pdf");
    announce("PDF export generated for the current Yoplait diagnostic.");
  }

  async function reanalyze(label: string) {
    setAnalysisState({
      status: "loading",
      message: `Analyzing ${label} with the Phase 1 backend.`,
    });
    try {
      const fallbackText = buildBaselineEvidenceText(
        profile,
        jobToBeDone,
        goals,
        gapDrafts,
      );
      const payload = buildPhase1Payload(
        profile.market,
        context,
        uploadedEvidence,
        fallbackText,
      );
      const analysis = await requestPhase1Analysis(payload);
      const mapped = mapPhase1ToFrontend(analysis, profile);

      setGapDrafts(mapped.gaps);
      setProfile(mapped.profile);
      setJobToBeDone(mapped.jobToBeDone);
      setRec(mapped.recommendation);
      if (mapped.goals.length) {
        setGoals(mapped.goals);
      }
      setPage("iag");
      setActiveGap("summary");
      setAnalysisState({
        status: "ready",
        message: `Live backend analysis applied to ${label}.`,
      });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "Phase 1 backend analysis failed.",
      });
    }
  }

  async function uploadEvidence(files: FileList | null) {
    if (!files?.length) return;
    setAnalysisState({
      status: "loading",
      message: "Preparing uploaded evidence.",
    });
    try {
      const uploads = await Promise.all(
        Array.from(files).map(fileToUploadedEvidence),
      );
      setUploadedEvidence((current) => {
        const existing = new Set(current.map((item) => item.id));
        return [
          ...current,
          ...uploads.filter((item) => !existing.has(item.id)),
        ];
      });
      setAnalysisState({ status: "idle", message: "" });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not prepare uploaded evidence.",
      });
    }
  }

  function updateGap(key: FiveCTab, patch: Partial<GapInsight>) {
    setGapDrafts((current) => ({
      ...current,
      [key]: {
        ...current[key],
        ...patch,
      },
    }));
  }

  function updateGoal(id: string, patch: Partial<SustainabilityGoal>) {
    setGoals((current) =>
      current.map((goal) => (goal.id === id ? { ...goal, ...patch } : goal)),
    );
  }

  function addNutritionGoal() {
    if (goals.some((goal) => goal.id === "nutrition-scorecard")) {
      announce(
        "Nutrition scorecard goal is already in the sustainability set.",
      );
      return;
    }
    setGoals((current) => [
      {
        id: "nutrition-scorecard",
        title: "Child Nutrition Outcome Scorecard",
        description:
          "Create a measurable nutrition impact scorecard for fortified product reach, calcium and vitamin D penetration, school and parent partnerships, and annual child bone-health indicators.",
        category: "social",
        subcategory: "child nutrition",
        type: "target",
        status: "planned",
        startYear: 2026,
        endYear: 2030,
        flagship: true,
      },
      ...current,
    ]);
    announce(
      "Added a child nutrition outcome goal to close the measurement gap.",
    );
  }

  return (
    <TooltipProvider>
      <div className="h-screen overflow-hidden bg-background text-foreground">
        <div className="flex h-full min-h-0 overflow-hidden">
          <Sidebar
            page={page}
            setPage={(nextPage) => {
              setPage(nextPage);
            }}
            onHome={() => {
              setPage("home");
            }}
            editMode={editMode}
            setEditMode={(value) => {
              setEditMode(value);
              announce(
                value ? "Edit mode enabled." : "Presentation mode enabled.",
              );
            }}
            context={context}
            setContext={setContext}
            onExport={exportPdf}
            onReanalyze={() =>
              reanalyze(
                page === "iag" ? "the IAG conclusion" : "the current module",
              )
            }
            isAnalyzing={analysisState.status === "loading"}
            analysisState={analysisState}
            uploadedEvidence={uploadedEvidence}
            onUploadEvidence={uploadEvidence}
            onRemoveEvidence={(id) =>
              setUploadedEvidence((current) =>
                current.filter((item) => item.id !== id),
              )
            }
            onSummarize={() => {
              setPage("iag");
              setActiveGap("summary");
              announce("5C selections summarized into the IAG executive view.");
            }}
            onGenerateGoals={addNutritionGoal}
          />

          <main className="min-h-0 min-w-0 flex-1 overflow-y-auto">
            <div className="mx-auto flex min-h-full w-full max-w-[1480px] flex-col px-5 py-5 md:px-8 lg:px-10">
              {page !== "home" && (
                <Header
                  page={page}
                  profile={profile}
                  averageConfidence={averageConfidence}
                  flagshipCount={flagshipCount}
                />
              )}
              <div id="gaia-export-area" className="flex-1 pb-10">
                {page === "home" && <HomeView setPage={setPage} />}
                {page === "iag" && (
                  <IagView
                    editMode={editMode}
                    activeGap={activeGap}
                    setActiveGap={setActiveGap}
                    gaps={gapDrafts}
                    updateGap={updateGap}
                    onSave={() => saveWorkspace("IAG edits saved.")}
                  />
                )}
                {page === "fiveC" && (
                  <FiveCView
                    editMode={editMode}
                    activeFiveC={activeFiveC}
                    setActiveFiveC={setActiveFiveC}
                    profile={profile}
                    setProfile={setProfile}
                    jobToBeDone={jobToBeDone}
                    setJobToBeDone={setJobToBeDone}
                    strategicShifts={strategicShiftDrafts}
                    setStrategicShifts={setStrategicShiftDrafts}
                    competitors={competitorDrafts}
                    setCompetitors={setCompetitorDrafts}
                    culturalDrivers={culturalDriverDrafts}
                    setCulturalDrivers={setCulturalDriverDrafts}
                    consumerStages={consumerStageDrafts}
                    setConsumerStages={setConsumerStageDrafts}
                    needStates={needStateDrafts}
                    setNeedStates={setNeedStateDrafts}
                    onSave={() => saveWorkspace("5C edits saved.")}
                    onGenerateJob={() => {
                      setJobToBeDone(strategicShiftDrafts.job);
                      announce(
                        "Job to be Done generated from selected 5C signals.",
                      );
                    }}
                    onReanalyze={reanalyze}
                  />
                )}
                {page === "sustainability" && (
                  <SustainabilityView
                    editMode={editMode}
                    goals={goals}
                    updateGoal={updateGoal}
                    removeGoal={(id) => {
                      setGoals((current) =>
                        current.filter((goal) => goal.id !== id),
                      );
                      announce(
                        "Sustainability goal removed from the active analysis set.",
                      );
                    }}
                    onGenerateGoals={addNutritionGoal}
                    onSave={() => saveWorkspace("Sustainability edits saved.")}
                  />
                )}
                {page === "next" && (
                  <NextStepsView
                    editMode={editMode}
                    recommendation={rec}
                    setRecommendation={setRec}
                    onSave={() =>
                      saveWorkspace("Next-step recommendation saved.")
                    }
                  />
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}

type SidebarProps = {
  page: PageKey;
  setPage: (page: PageKey) => void;
  onHome: () => void;
  editMode: boolean;
  setEditMode: (value: boolean) => void;
  context: string;
  setContext: (value: string) => void;
  onExport: () => void;
  onReanalyze: () => void;
  isAnalyzing: boolean;
  analysisState: AnalysisState;
  uploadedEvidence: UploadedEvidence[];
  onUploadEvidence: (files: FileList | null) => void;
  onRemoveEvidence: (id: string) => void;
  onSummarize: () => void;
  onGenerateGoals: () => void;
};

function Sidebar({
  page,
  setPage,
  onHome,
  editMode,
  setEditMode,
  context,
  setContext,
  onExport,
  onReanalyze,
  isAnalyzing,
  analysisState,
  uploadedEvidence,
  onUploadEvidence,
  onRemoveEvidence,
  onSummarize,
  onGenerateGoals,
}: SidebarProps) {
  const isHome = page === "home";

  return (
    <aside className="hidden h-full w-[290px] shrink-0 overflow-y-auto border-r border-border bg-sidebar px-5 py-5 md:block">
      <nav className="flex min-h-full flex-col gap-6">
        <div>
          <img
            src={groundedLogo}
            alt="Grounded World"
            className="h-auto w-full object-contain"
          />
        </div>

        <div className="flex flex-col gap-2">
          <button
            type="button"
            className={cn(
              "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-muted-foreground hover:bg-muted",
              page === "home" && "bg-muted text-foreground",
            )}
            onClick={onHome}
          >
            <Home className="size-4" />
            Home
          </button>
          <button
            type="button"
            className={cn(
              "rounded-md border border-border bg-muted/60 px-3 py-2 text-left text-sm font-semibold hover:bg-muted",
              page !== "home" && "text-foreground",
            )}
            onClick={() => setPage("iag")}
          >
            Yoplait UK
          </button>
        </div>

        {!isHome && (
          <>
            <Separator />

            <div className="flex flex-col gap-3">
              <Label className="flex items-center gap-2 text-muted-foreground">
                <FileText className="size-4" />
                Page
              </Label>
              <Select
                value={page}
                onValueChange={(value) => setPage(value as PageKey)}
              >
                <SelectTrigger aria-label="Selected page">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {pageOptions
                    .filter((option) => option.key !== "home")
                    .map((option) => (
                      <SelectItem key={option.key} value={option.key}>
                        {option.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between rounded-md border border-border bg-card px-3 py-3">
              <div className="flex items-center gap-2">
                <Pencil className="size-4 text-accent" />
                <Label htmlFor="edit-mode">Edit mode</Label>
              </div>
              <Switch
                id="edit-mode"
                checked={editMode}
                onCheckedChange={setEditMode}
              />
            </div>
          </>
        )}

        {isHome && (
          <div className="rounded-md border border-border bg-card px-3 py-3 text-sm leading-6 text-muted-foreground">
            This platform can help you take the first step towards
            commercializing sustainability by finding the biggest gaps between
            stated sustainability goals, go to market strategy and brand
            positioning.
          </div>
        )}

        <div className="flex flex-col gap-2">
          {(page === "iag" || page === "fiveC") && (
            <Button
              className="w-full justify-start"
              variant="outline"
              onClick={onExport}
            >
              <Download />
              Export Summary PDF
            </Button>
          )}
          {page === "fiveC" && (
            <Button
              className="w-full justify-start"
              variant="accent"
              onClick={onSummarize}
            >
              <Sparkles />
              Summarize to IAG
            </Button>
          )}
          {page === "sustainability" && (
            <Button
              className="w-full justify-start"
              variant="accent"
              onClick={onGenerateGoals}
            >
              <Plus />
              Generate new goals
            </Button>
          )}
        </div>

        {(page === "iag" || page === "sustainability" || page === "fiveC") && (
          <div className="space-y-3">
            <div>
              <h2 className="text-sm font-semibold">
                {page === "sustainability" ? "Reanalyze Goals" : "Reanalyze"}
              </h2>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                Add client evidence, proprietary research, or workshop notes.
              </p>
            </div>
            <Textarea
              value={context}
              onChange={(event) => setContext(event.target.value)}
              aria-label="Additional Context"
              placeholder="Paste additional context..."
              className="min-h-[120px]"
            />
            <div className="space-y-2 rounded-md border border-border bg-card p-3">
              <input
                id="evidence-upload"
                type="file"
                multiple
                accept=".txt,.md,.csv,.json,.docx,.pdf"
                className="sr-only"
                onChange={(event) => {
                  onUploadEvidence(event.target.files);
                  event.target.value = "";
                }}
              />
              <Button
                asChild
                className="w-full justify-start"
                variant="outline"
              >
                <label htmlFor="evidence-upload">
                  <Upload />
                  Upload evidence
                </label>
              </Button>
              {uploadedEvidence.length > 0 && (
                <div className="space-y-1">
                  {uploadedEvidence.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between gap-2 rounded-md bg-muted px-2 py-1 text-xs"
                    >
                      <span className="truncate">{item.source}</span>
                      <Button
                        aria-label={`Remove ${item.source}`}
                        variant="ghost"
                        size="icon"
                        className="size-7"
                        onClick={() => onRemoveEvidence(item.id)}
                      >
                        <Trash2 />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <Button
              className="w-full justify-start"
              variant="secondary"
              onClick={onReanalyze}
              disabled={isAnalyzing}
            >
              <RefreshCw className={cn(isAnalyzing && "animate-spin")} />
              {isAnalyzing
                ? "Analyzing..."
                : page === "sustainability"
                  ? "Analyze goals"
                  : "Run backend analysis"}
            </Button>
            {analysisState.status === "error" && (
              <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs leading-5 text-destructive">
                {analysisState.message}
              </p>
            )}
            {analysisState.status === "ready" && (
              <p className="text-xs leading-5 text-muted-foreground">
                Live backend analysis applied.
              </p>
            )}
          </div>
        )}

        {isHome && (
          <div className="mt-auto pt-2">
            <img
              src={iagLogo}
              alt="Intention Action Gap"
              className="h-auto w-full rounded-md object-contain"
            />
          </div>
        )}
      </nav>
    </aside>
  );
}

function Header({
  page,
  profile,
  averageConfidence,
  flagshipCount,
}: {
  page: PageKey;
  profile: typeof companyProfile;
  averageConfidence: number;
  flagshipCount: number;
}) {
  const currentPage =
    pageOptions.find((option) => option.key === page)?.label ?? "Home";
  return (
    <header className="mb-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline">{profile.market}</Badge>
            <span>{currentPage}</span>
          </div>
          <h2 className="mt-3 font-serif text-4xl font-semibold md:text-5xl">
            {page === "home"
              ? "How Gaia Works"
              : page === "iag"
                ? "5C Intention Action Gaps"
                : currentPage}
          </h2>
        </div>
        <div className="grid grid-cols-3 gap-2 lg:w-[520px]">
          <Metric
            icon={Gauge}
            label="Confidence"
            value={`${averageConfidence}%`}
          />
          <Metric icon={Leaf} label="Goals" value={String(flagshipCount)} />
          <Metric icon={ShieldCheck} label="QA" value="Ready" />
        </div>
      </div>
    </header>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Gauge;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="size-4 text-accent" />
        {label}
      </div>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

const homeWorkflow = [
  {
    title: "1. Start with evidence",
    description:
      "Paste context or upload source material so Gaia can ground the diagnostic in research, workshop notes, strategy decks, and market signals.",
    icon: Upload,
  },
  {
    title: "2. Review the 5C analysis",
    description:
      "Move through company, competition, culture, consumer, and category signals. Edit the working assumptions before they feed the summary.",
    icon: ListChecks,
  },
  {
    title: "3. Summarize the intention-action gap",
    description:
      "Convert selected 5C signals into the executive IAG view: gap type, importance, confidence, supporting evidence, and next steps.",
    icon: LineChart,
  },
  {
    title: "4. Build the next recommendation",
    description:
      "Use the sustainability and next-step modules to turn the gap into measurable goals, a focused strategic route, and an exportable summary.",
    icon: Sparkles,
  },
];

const homeModules: Array<{
  page: PageKey;
  title: string;
  description: string;
  action: string;
  icon: typeof Layers3;
}> = [
  {
    page: "fiveC",
    title: "5C Workspace",
    description:
      "Inspect and refine the source analysis behind the recommendation.",
    action: "Open 5C",
    icon: Layers3,
  },
  {
    page: "iag",
    title: "IAG Summary",
    description:
      "See the synthesized gap, confidence score, evidence, and action plan.",
    action: "View IAG",
    icon: LineChart,
  },
  {
    page: "sustainability",
    title: "Sustainability Goals",
    description:
      "Translate the strategic gap into measurable impact commitments.",
    action: "Review Goals",
    icon: Leaf,
  },
  {
    page: "next",
    title: "Next Steps",
    description:
      "Package the strongest route for the client-facing recommendation.",
    action: "See Next Steps",
    icon: Target,
  },
];

function HomeView({ setPage }: { setPage: (page: PageKey) => void }) {
  return (
    <div className="flex flex-col gap-8">
      <section className="grid gap-6 pt-2 xl:grid-cols-[minmax(0,1fr)_360px] xl:items-stretch">
        <div>
          <Badge variant="outline">Gaia workflow</Badge>
          <h2 className="mt-4 max-w-4xl font-serif text-4xl font-semibold leading-[1.08] md:text-5xl">
            Close the Gap Between Brand, Sustainability & Business Performance
          </h2>
          <p className="mt-5 max-w-3xl text-base leading-8 text-muted-foreground">
            This is an AI guided strategy workspace for turning brand context,
            5C research, and sustainability ambition into an executive-ready
            intention-action gap analysis and set of recommendations. Work
            through the modules in order, edit assumptions where needed, run
            backend analysis when new evidence arrives, then export the summary
            when the logic is ready.
          </p>
        </div>

        <Card className="flex h-full flex-col">
          <CardHeader>
            <CardTitle>Start a diagnostic</CardTitle>
            <CardDescription>
              Begin with source analysis, then synthesize the strongest gap and
              recommended action.
            </CardDescription>
          </CardHeader>
          <CardFooter className="mt-auto flex-col items-stretch">
            <Button
              className="w-full justify-start"
              variant="accent"
              onClick={() => setPage("fiveC")}
            >
              Start with 5C
              <ArrowRight data-icon="inline-end" />
            </Button>
            <Button
              className="w-full justify-start"
              variant="outline"
              onClick={() => setPage("iag")}
            >
              View IAG summary
              <ArrowRight data-icon="inline-end" />
            </Button>
          </CardFooter>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-4">
        {homeWorkflow.map(({ title, description, icon: Icon }) => (
          <Card key={title} className="flex flex-col">
            <CardHeader>
              <div className="mb-2 flex size-10 items-center justify-center rounded-md bg-muted text-accent">
                <Icon className="size-4" />
              </div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {homeModules.map(({ page, title, description, action, icon: Icon }) => (
          <Card key={page} className="flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Icon className="size-4 text-accent" />
                {title}
              </CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent className="mt-auto">
              <Button
                className="w-full justify-start"
                variant="outline"
                onClick={() => setPage(page)}
              >
                {action}
                <ArrowRight data-icon="inline-end" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}

function IagView({
  editMode,
  activeGap,
  setActiveGap,
  gaps,
  updateGap,
  onSave,
}: {
  editMode: boolean;
  activeGap: FiveCTab;
  setActiveGap: (key: FiveCTab) => void;
  gaps: Record<FiveCTab, GapInsight>;
  updateGap: (key: FiveCTab, patch: Partial<GapInsight>) => void;
  onSave: () => void;
}) {
  const gap = gaps[activeGap];

  return (
    <Tabs
      value={activeGap}
      onValueChange={(value) => setActiveGap(value as FiveCTab)}
    >
      <ResponsiveTabsList>
        {fiveCTabs.map(({ key, label, icon: Icon }) => (
          <TabsTrigger key={key} value={key} className="gap-2">
            <Icon className="size-4" />
            {label}
          </TabsTrigger>
        ))}
      </ResponsiveTabsList>

      {fiveCTabs.map(({ key }) => (
        <TabsContent key={key} value={key}>
          {editMode ? (
            <IagEditor
              gap={gaps[key]}
              updateGap={(patch) => updateGap(key, patch)}
              onSave={onSave}
            />
          ) : (
            <IagPresentation gap={gaps[key]} />
          )}
        </TabsContent>
      ))}

      <div className="sr-only" aria-live="polite">
        {gap.label} selected
      </div>
    </Tabs>
  );
}

function IagPresentation({ gap }: { gap: GapInsight }) {
  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-3">
        <StatusPill label="Gap type" value={gap.type} />
        <StatusPill label="Importance" value={gap.importance} />
        <StatusPill label="Confidence" value={`${gap.confidence}%`} />
      </div>
      <section className="grid gap-5 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="rounded-md border border-border bg-panel p-5">
          <p className="text-base leading-8 text-foreground">
            {gap.explanation}
          </p>
        </div>
        <div className="rounded-md border border-border bg-panel p-5">
          <h3 className="flex items-center gap-2 text-base font-semibold">
            <LineChart className="size-4 text-accent" />
            Recommended next steps
          </h3>
          <ol className="mt-4 space-y-3 text-sm leading-6 text-muted-foreground">
            {gap.nextSteps.map((step, index) => (
              <li key={step} className="flex gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-muted text-xs text-foreground">
                  {index + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      </section>

      <EvidenceAccordion evidence={gap.evidence} />
    </div>
  );
}

function IagEditor({
  gap,
  updateGap,
  onSave,
}: {
  gap: GapInsight;
  updateGap: (patch: Partial<GapInsight>) => void;
  onSave: () => void;
}) {
  return (
    <div className="space-y-5 rounded-md border border-border bg-panel p-5">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Gap type">
          <Select
            value={gap.type.toLowerCase()}
            onValueChange={(value) => updateGap({ type: titleCase(value) })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="strategic">Strategic</SelectItem>
              <SelectItem value="operational">Operational</SelectItem>
              <SelectItem value="commercial">Commercial</SelectItem>
            </SelectContent>
          </Select>
        </Field>
        <Field label="Importance">
          <Select
            value={gap.importance.toLowerCase()}
            onValueChange={(value) =>
              updateGap({ importance: titleCase(value) })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </Field>
        <Field label="Confidence">
          <div className="flex h-10 items-center gap-3">
            <Slider
              value={[gap.confidence]}
              min={0}
              max={100}
              step={1}
              onValueChange={([confidence]) => updateGap({ confidence })}
            />
            <span className="w-10 text-sm font-semibold">
              {gap.confidence}%
            </span>
          </div>
        </Field>
        <div className="flex items-end">
          <Button className="w-full" onClick={onSave}>
            <Save />
            Save
          </Button>
        </div>
      </div>

      <Field label="Gap explanation">
        <Textarea
          value={gap.explanation}
          onChange={(event) => updateGap({ explanation: event.target.value })}
          className="min-h-[180px]"
        />
      </Field>
      <Field label="One action per line">
        <Textarea
          value={gap.nextSteps.join("\n")}
          onChange={(event) =>
            updateGap({
              nextSteps: event.target.value.split("\n").filter(Boolean),
            })
          }
          className="min-h-[150px]"
        />
      </Field>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">
          Key Arguments & Supporting Evidence
        </h3>
        {gap.evidence.map((item, index) => (
          <div
            key={item.title}
            className="grid gap-3 rounded-md border border-border bg-card p-4 md:grid-cols-2"
          >
            <Field label="Title">
              <Input
                value={item.title}
                onChange={(event) =>
                  updateEvidence(
                    gap,
                    index,
                    { title: event.target.value },
                    updateGap,
                  )
                }
              />
            </Field>
            <Field label="Summary">
              <Textarea
                value={item.summary}
                onChange={(event) =>
                  updateEvidence(
                    gap,
                    index,
                    { summary: event.target.value },
                    updateGap,
                  )
                }
                className="min-h-[92px]"
              />
            </Field>
          </div>
        ))}
      </div>
    </div>
  );
}

function updateEvidence(
  gap: GapInsight,
  index: number,
  patch: Partial<EvidenceBlock>,
  updateGap: (patch: Partial<GapInsight>) => void,
) {
  const evidence = gap.evidence.map((item, itemIndex) =>
    itemIndex === index ? { ...item, ...patch } : item,
  );
  updateGap({ evidence });
}

function EvidenceAccordion({ evidence }: { evidence: EvidenceBlock[] }) {
  return (
    <Accordion
      type="single"
      collapsible
      className="rounded-md border border-border bg-panel px-4"
    >
      <AccordionItem value="evidence" className="border-0">
        <AccordionTrigger>Key Arguments & Supporting Evidence</AccordionTrigger>
        <AccordionContent>
          <div className="grid gap-4 lg:grid-cols-3">
            {evidence.map((item) => (
              <article
                key={item.title}
                className="rounded-md border border-border bg-card p-4"
              >
                <h4 className="text-base font-semibold">{item.title}</h4>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {item.summary}
                </p>
                <EvidenceList title="Key Facts" items={item.facts} />
                <EvidenceList
                  title="Supporting Evidence"
                  items={item.sources}
                />
                <EvidenceList
                  title="Quantitative Signals"
                  items={item.signals}
                />
                <EvidenceList title="Implications" items={item.implications} />
              </article>
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}

function EvidenceList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold uppercase text-muted-foreground">
        {title}
      </p>
      <ul className="mt-2 space-y-2 text-sm leading-5 text-muted-foreground">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-accent" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function FiveCView({
  editMode,
  activeFiveC,
  setActiveFiveC,
  profile,
  setProfile,
  jobToBeDone,
  setJobToBeDone,
  strategicShifts,
  setStrategicShifts,
  competitors,
  setCompetitors,
  culturalDrivers,
  setCulturalDrivers,
  consumerStages,
  setConsumerStages,
  needStates,
  setNeedStates,
  onSave,
  onGenerateJob,
  onReanalyze,
}: {
  editMode: boolean;
  activeFiveC: FiveCTab;
  setActiveFiveC: (key: FiveCTab) => void;
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
  jobToBeDone: string;
  setJobToBeDone: (value: string) => void;
  strategicShifts: StrategicShiftDraft;
  setStrategicShifts: React.Dispatch<React.SetStateAction<StrategicShiftDraft>>;
  competitors: CompetitorDrafts;
  setCompetitors: React.Dispatch<React.SetStateAction<CompetitorDrafts>>;
  culturalDrivers: CulturalDriverDrafts;
  setCulturalDrivers: React.Dispatch<
    React.SetStateAction<CulturalDriverDrafts>
  >;
  consumerStages: ConsumerStageDrafts;
  setConsumerStages: React.Dispatch<React.SetStateAction<ConsumerStageDrafts>>;
  needStates: NeedStateDrafts;
  setNeedStates: React.Dispatch<React.SetStateAction<NeedStateDrafts>>;
  onSave: () => void;
  onGenerateJob: () => void;
  onReanalyze: (label: string) => void;
}) {
  return (
    <Tabs
      value={activeFiveC}
      onValueChange={(value) => setActiveFiveC(value as FiveCTab)}
    >
      <ResponsiveTabsList>
        {fiveCTabs.map(({ key, label, icon: Icon }) => (
          <TabsTrigger key={key} value={key} className="gap-2">
            <Icon className="size-4" />
            {key === "summary"
              ? label
              : `${label} ${isSelectedFiveC(key) ? "*" : ""}`}
          </TabsTrigger>
        ))}
      </ResponsiveTabsList>

      <TabsContent value="summary">
        <FiveCSummary
          editMode={editMode}
          profile={profile}
          setProfile={setProfile}
          jobToBeDone={jobToBeDone}
          setJobToBeDone={setJobToBeDone}
          strategicShifts={strategicShifts}
          setStrategicShifts={setStrategicShifts}
          onSave={onSave}
          onGenerateJob={onGenerateJob}
        />
      </TabsContent>
      <TabsContent value="company">
        <CompanyPanel
          editMode={editMode}
          profile={profile}
          setProfile={setProfile}
          onSave={onSave}
        />
      </TabsContent>
      <TabsContent value="competition">
        <CompetitionPanel
          editMode={editMode}
          competitors={competitors}
          setCompetitors={setCompetitors}
          onSave={onSave}
          onReanalyze={() => onReanalyze("the competitive opportunity")}
        />
      </TabsContent>
      <TabsContent value="culture">
        <CulturePanel
          editMode={editMode}
          culturalDrivers={culturalDrivers}
          setCulturalDrivers={setCulturalDrivers}
          onSave={onSave}
          onReanalyze={() => onReanalyze("the cultural opportunity")}
        />
      </TabsContent>
      <TabsContent value="consumer">
        <ConsumerPanel
          editMode={editMode}
          consumerStages={consumerStages}
          setConsumerStages={setConsumerStages}
          onSave={onSave}
          onReanalyze={() => onReanalyze("the consumer opportunity")}
        />
      </TabsContent>
      <TabsContent value="category">
        <CategoryPanel
          editMode={editMode}
          needStates={needStates}
          setNeedStates={setNeedStates}
          onSave={onSave}
          onReanalyze={() => onReanalyze("the category opportunity")}
        />
      </TabsContent>
    </Tabs>
  );
}

function FiveCSummary({
  editMode,
  profile,
  setProfile,
  jobToBeDone,
  setJobToBeDone,
  strategicShifts,
  setStrategicShifts,
  onSave,
  onGenerateJob,
}: {
  editMode: boolean;
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
  jobToBeDone: string;
  setJobToBeDone: (value: string) => void;
  strategicShifts: StrategicShiftDraft;
  setStrategicShifts: React.Dispatch<React.SetStateAction<StrategicShiftDraft>>;
  onSave: () => void;
  onGenerateJob: () => void;
}) {
  if (editMode) {
    return (
      <div className="space-y-5 rounded-md border border-border bg-panel p-5">
        <CompanyEditor
          profile={profile}
          setProfile={setProfile}
          onSave={onSave}
        />
        <Separator />
        <ShiftEditor
          shifts={strategicShifts}
          setShifts={setStrategicShifts}
          onSave={onSave}
        />
        <Separator />
        <Field label="Job to be Done">
          <Textarea
            value={jobToBeDone}
            onChange={(event) => setJobToBeDone(event.target.value)}
            placeholder="Generate or type the strategic Job to be Done statement..."
            className="min-h-[120px]"
          />
        </Field>
        <div className="flex flex-wrap gap-2">
          <Button onClick={onSave}>
            <Save />
            Save
          </Button>
          <Button onClick={onGenerateJob}>
            <Sparkles />
            Generate Job to be Done
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 xl:grid-cols-2">
        <SummaryBlock title="Company">
          <p>
            <strong>Belief:</strong> {profile.belief}
          </p>
          <p>
            <strong>Purpose:</strong> {profile.purpose}
          </p>
        </SummaryBlock>
        <SummaryBlock title="Competition">
          <p className="uppercase text-muted-foreground">From</p>
          <p>{strategicShifts.competition.from}</p>
          <p className="uppercase text-muted-foreground">To</p>
          <ul className="space-y-2">
            {strategicShifts.competition.to.map((item) => (
              <li key={item} className="flex gap-2">
                <Target className="mt-1 size-4 shrink-0 text-accent" />
                {item}
              </li>
            ))}
          </ul>
        </SummaryBlock>
        <SummaryBlock title="Culture">
          <p className="uppercase text-muted-foreground">From</p>
          <p>{strategicShifts.culture.from}</p>
          <p className="uppercase text-muted-foreground">To</p>
          <p>{strategicShifts.culture.to}</p>
        </SummaryBlock>
        <SummaryBlock title="Consumer">
          <p className="uppercase text-muted-foreground">From</p>
          <p>{strategicShifts.consumer.from}</p>
          <p className="uppercase text-muted-foreground">To</p>
          <p>{strategicShifts.consumer.to}</p>
        </SummaryBlock>
        <SummaryBlock title="Category">
          <p className="uppercase text-muted-foreground">From</p>
          <p>{strategicShifts.category.from}</p>
          <p className="uppercase text-muted-foreground">To</p>
          <p>{strategicShifts.category.to}</p>
        </SummaryBlock>
        <div className="rounded-md border border-accent/40 bg-accent/10 p-5">
          <h3 className="text-lg font-semibold">Job to be Done</h3>
          <p className="mt-3 text-base leading-7">{jobToBeDone}</p>
          <Button className="mt-4" variant="accent" onClick={onGenerateJob}>
            <Sparkles />
            Generate Job to be Done
          </Button>
        </div>
      </div>
    </div>
  );
}

function CompanyPanel({
  editMode,
  profile,
  setProfile,
  onSave,
}: {
  editMode: boolean;
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
  onSave: () => void;
}) {
  return editMode ? (
    <div className="rounded-md border border-border bg-panel p-5">
      <CompanyEditor
        profile={profile}
        setProfile={setProfile}
        onSave={onSave}
      />
    </div>
  ) : (
    <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="rounded-md border border-border bg-panel p-5">
        <p className="text-sm font-semibold uppercase text-muted-foreground">
          Belief
        </p>
        <p className="mt-2 text-lg leading-8">{profile.belief}</p>
      </div>
      <div className="rounded-md border border-border bg-panel p-5">
        <p className="text-sm font-semibold uppercase text-muted-foreground">
          Purpose
        </p>
        <h3 className="mt-2 font-serif text-2xl leading-9">
          {profile.purpose}
        </h3>
      </div>
      {Object.entries(profile.pursuits).map(([key, value]) => (
        <article
          key={key}
          className="rounded-md border border-border bg-card p-5"
        >
          <p className="text-sm font-semibold uppercase text-muted-foreground">
            {key}
          </p>
          <p className="mt-2 text-sm leading-7 text-muted-foreground">
            {value}
          </p>
        </article>
      ))}
    </div>
  );
}

function CompanyEditor({
  profile,
  setProfile,
  onSave,
}: {
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
  onSave: () => void;
}) {
  return (
    <div className="grid gap-4">
      <Field label="Belief">
        <Textarea
          value={profile.belief}
          onChange={(event) =>
            setProfile({ ...profile, belief: event.target.value })
          }
        />
      </Field>
      <Field label="Purpose">
        <Textarea
          value={profile.purpose}
          onChange={(event) =>
            setProfile({ ...profile, purpose: event.target.value })
          }
        />
      </Field>
      {Object.entries(profile.pursuits).map(([key, value]) => (
        <Field key={key} label={titleCase(key)}>
          <Textarea
            value={value}
            onChange={(event) =>
              setProfile({
                ...profile,
                pursuits: { ...profile.pursuits, [key]: event.target.value },
              })
            }
          />
        </Field>
      ))}
      <Button className="w-fit" onClick={onSave}>
        <Save />
        Save
      </Button>
    </div>
  );
}

function ShiftEditor({
  shifts,
  setShifts,
  onSave,
}: {
  shifts: StrategicShiftDraft;
  setShifts: React.Dispatch<React.SetStateAction<StrategicShiftDraft>>;
  onSave: () => void;
}) {
  const updateShift = <
    Section extends StrategicShiftSection,
    Key extends keyof StrategicShiftDraft[Section],
  >(
    section: Section,
    key: Key,
    value: StrategicShiftDraft[Section][Key],
  ) => {
    setShifts((current) => ({
      ...current,
      [section]: {
        ...current[section],
        [key]: value,
      },
    }));
  };

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Field label="Opportunity Rationale">
        <Textarea
          value={shifts.competition.from}
          onChange={(event) =>
            updateShift("competition", "from", event.target.value)
          }
        />
      </Field>
      <Field label="Unmet Needs">
        <Textarea
          value={shifts.competition.to.join("\n")}
          onChange={(event) =>
            updateShift(
              "competition",
              "to",
              event.target.value.split("\n").filter(Boolean),
            )
          }
        />
      </Field>
      <Field label="Cultural Tension">
        <Textarea
          value={shifts.culture.from}
          onChange={(event) =>
            updateShift("culture", "from", event.target.value)
          }
        />
      </Field>
      <Field label="Emerging Paradigm">
        <Textarea
          value={shifts.culture.to}
          onChange={(event) => updateShift("culture", "to", event.target.value)}
        />
      </Field>
      <Field label="Core Problem">
        <Textarea
          value={shifts.consumer.from}
          onChange={(event) =>
            updateShift("consumer", "from", event.target.value)
          }
        />
      </Field>
      <Field label="Cultural Reason">
        <Textarea
          value={shifts.consumer.to}
          onChange={(event) =>
            updateShift("consumer", "to", event.target.value)
          }
        />
      </Field>
      <Field label="Primary Gap">
        <Textarea
          value={shifts.category.from}
          onChange={(event) =>
            updateShift("category", "from", event.target.value)
          }
        />
      </Field>
      <Field label="Recommended Fix">
        <Textarea
          value={shifts.category.to}
          onChange={(event) =>
            updateShift("category", "to", event.target.value)
          }
        />
      </Field>
      <div className="xl:col-span-2">
        <Button className="w-fit" onClick={onSave}>
          <Save />
          Save
        </Button>
      </div>
    </div>
  );
}

function CompetitionPanel({
  editMode,
  competitors,
  setCompetitors,
  onSave,
  onReanalyze,
}: {
  editMode: boolean;
  competitors: CompetitorDrafts;
  setCompetitors: React.Dispatch<React.SetStateAction<CompetitorDrafts>>;
  onSave: () => void;
  onReanalyze: () => void;
}) {
  const [selectedCompetitor, setSelectedCompetitor] = useState(
    competitors[0].name,
  );
  const competitor =
    competitors.find((item) => item.name === selectedCompetitor) ||
    competitors[0];
  const updateCompetitor = (
    name: string,
    patch: Partial<CompetitorDrafts[number]>,
  ) => {
    setCompetitors((current) =>
      current.map((item) =>
        item.name === name ? { ...item, ...patch } : item,
      ),
    );
  };

  return (
    <div className="space-y-5">
      <Tabs value={selectedCompetitor} onValueChange={setSelectedCompetitor}>
        <ResponsiveTabsList>
          {competitors.map((item) => (
            <TabsTrigger key={item.name} value={item.name} className="gap-2">
              {item.selected && (
                <Star className="size-4 fill-current text-accent" />
              )}
              {item.name}
            </TabsTrigger>
          ))}
        </ResponsiveTabsList>
        {competitors.map((item) => (
          <TabsContent key={item.name} value={item.name}>
            {editMode ? (
              <SelectionEditor
                itemLabel={item.name}
                selected={item.selected}
                onSelectedChange={(selected) =>
                  updateCompetitor(item.name, { selected })
                }
                onSave={onSave}
              >
                <Field label="Competitor Position">
                  <Textarea
                    value={item.position}
                    onChange={(event) =>
                      updateCompetitor(item.name, {
                        position: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Competitor Purpose">
                  <Textarea
                    value={item.purpose}
                    onChange={(event) =>
                      updateCompetitor(item.name, {
                        purpose: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Purpose into Profit">
                  <Textarea
                    value={item.profit}
                    onChange={(event) =>
                      updateCompetitor(item.name, {
                        profit: event.target.value,
                      })
                    }
                  />
                </Field>
              </SelectionEditor>
            ) : (
              <CompetitorCard competitor={item} />
            )}
          </TabsContent>
        ))}
      </Tabs>
      <SummarizePanel
        title="Summarize"
        items={competitors
          .filter((item) => item.selected)
          .map((item) => item.name)}
        onReanalyze={onReanalyze}
      />
      <div className="sr-only">{competitor.name}</div>
    </div>
  );
}

function CompetitorCard({
  competitor,
}: {
  competitor: (typeof competitors)[number];
}) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <SummaryBlock title="Competitor Position">
        {competitor.position}
      </SummaryBlock>
      <SummaryBlock title="Competitor Purpose">
        {competitor.purpose}
      </SummaryBlock>
      <SummaryBlock title="Purpose into Profit">
        {competitor.profit}
      </SummaryBlock>
    </div>
  );
}

function CulturePanel({
  editMode,
  culturalDrivers,
  setCulturalDrivers,
  onSave,
  onReanalyze,
}: {
  editMode: boolean;
  culturalDrivers: CulturalDriverDrafts;
  setCulturalDrivers: React.Dispatch<
    React.SetStateAction<CulturalDriverDrafts>
  >;
  onSave: () => void;
  onReanalyze: () => void;
}) {
  const [driver, setDriver] = useState(culturalDrivers[0].title);
  const active =
    culturalDrivers.find((item) => item.title === driver) || culturalDrivers[0];
  const updateDriver = (
    title: string,
    patch: Partial<CulturalDriverDrafts[number]>,
  ) => {
    setCulturalDrivers((current) =>
      current.map((item) =>
        item.title === title ? { ...item, ...patch } : item,
      ),
    );
  };

  return (
    <div className="space-y-5">
      <h3 className="text-xl font-semibold">Cultural Drivers</h3>
      <Tabs value={driver} onValueChange={setDriver}>
        <ResponsiveTabsList containedScroll>
          {culturalDrivers.map((item) => (
            <TabsTrigger
              key={item.title}
              value={item.title}
              className="max-w-[320px] shrink-0 justify-start gap-2 overflow-hidden border border-white/10 bg-white/10 hover:bg-white/15 data-[state=active]:border-border data-[state=active]:bg-background"
              title={item.title}
            >
              {item.selected && (
                <Star className="size-4 fill-current text-accent" />
              )}
              <span className="min-w-0 truncate">{item.title}</span>
            </TabsTrigger>
          ))}
        </ResponsiveTabsList>
        {culturalDrivers.map((item) => (
          <TabsContent key={item.title} value={item.title}>
            {editMode ? (
              <SelectionEditor
                itemLabel={item.title}
                selected={item.selected}
                onSelectedChange={(selected) =>
                  updateDriver(item.title, { selected })
                }
                onSave={onSave}
              >
                <Field label="Cultural Observation">
                  <Textarea
                    value={item.observation}
                    onChange={(event) =>
                      updateDriver(item.title, {
                        observation: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Underlying Tension">
                  <Textarea
                    value={item.tension}
                    onChange={(event) =>
                      updateDriver(item.title, { tension: event.target.value })
                    }
                  />
                </Field>
                <Field label="What This Means for People">
                  <Textarea
                    value={item.people}
                    onChange={(event) =>
                      updateDriver(item.title, { people: event.target.value })
                    }
                  />
                </Field>
                <Field label="Marketing Implication">
                  <Textarea
                    value={item.implication}
                    onChange={(event) =>
                      updateDriver(item.title, {
                        implication: event.target.value,
                      })
                    }
                  />
                </Field>
              </SelectionEditor>
            ) : (
              <div className="grid gap-4 xl:grid-cols-2">
                <SummaryBlock title="Cultural Observation">
                  {item.observation}
                </SummaryBlock>
                <SummaryBlock title="Underlying Tension">
                  {item.tension}
                </SummaryBlock>
                <SummaryBlock title="What This Means for People">
                  {item.people}
                </SummaryBlock>
                <SummaryBlock title="Marketing Implication">
                  {item.implication}
                </SummaryBlock>
                <div className="rounded-md border border-border bg-panel p-5 xl:col-span-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold">Confidence</p>
                    <Badge variant="success">{item.confidence}%</Badge>
                  </div>
                  <Progress value={item.confidence} className="mt-3" />
                  <Accordion
                    type="single"
                    collapsible
                    className="mt-4 rounded-md border border-border px-4"
                  >
                    <AccordionItem value="sources" className="border-0">
                      <AccordionTrigger>Sources</AccordionTrigger>
                      <AccordionContent>
                        <ul className="space-y-2">
                          {item.sources.map((source) => (
                            <li
                              key={source}
                              className="flex gap-2 text-sm text-muted-foreground"
                            >
                              <FileText className="mt-0.5 size-4 text-accent" />
                              {source}
                            </li>
                          ))}
                        </ul>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </div>
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>
      <SummarizePanel
        title="Summarize"
        items={culturalDrivers
          .filter((item) => item.selected)
          .map((item) => item.title)}
        onReanalyze={onReanalyze}
      />
      <div className="sr-only">{active.title}</div>
    </div>
  );
}

function ConsumerPanel({
  editMode,
  consumerStages,
  setConsumerStages,
  onSave,
  onReanalyze,
}: {
  editMode: boolean;
  consumerStages: ConsumerStageDrafts;
  setConsumerStages: React.Dispatch<React.SetStateAction<ConsumerStageDrafts>>;
  onSave: () => void;
  onReanalyze: () => void;
}) {
  const [stage, setStage] = useState("Discovery");
  const updateStage = (
    stage: string,
    patch: Partial<ConsumerStageDrafts[number]>,
  ) => {
    setConsumerStages((current) =>
      current.map((item) =>
        item.stage === stage ? { ...item, ...patch } : item,
      ),
    );
  };

  return (
    <div className="space-y-5">
      <Accordion
        type="single"
        collapsible
        className="rounded-md border border-border bg-panel px-4"
      >
        <AccordionItem value="personas" className="border-0">
          <AccordionTrigger>Personas</AccordionTrigger>
          <AccordionContent>
            <div className="grid gap-4 md:grid-cols-3">
              {["Pragmatic Parent", "Label Scrutinizer", "Nostalgic Buyer"].map(
                (persona) => (
                  <article
                    key={persona}
                    className="rounded-md border border-border bg-card p-4"
                  >
                    <h4 className="font-semibold">{persona}</h4>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      Motivated by child wellbeing, practical routines, and
                      confidence that the product delivers what it promises.
                    </p>
                  </article>
                ),
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <Tabs value={stage} onValueChange={setStage}>
        <ResponsiveTabsList>
          {consumerStages.map((item) => (
            <TabsTrigger key={item.stage} value={item.stage} className="gap-2">
              {item.selected && (
                <Star className="size-4 fill-current text-accent" />
              )}
              {item.stage}
            </TabsTrigger>
          ))}
        </ResponsiveTabsList>
        {consumerStages.map((item) => (
          <TabsContent key={item.stage} value={item.stage}>
            {editMode ? (
              <SelectionEditor
                itemLabel={item.stage}
                selected={item.selected}
                onSelectedChange={(selected) =>
                  updateStage(item.stage, { selected })
                }
                onSave={onSave}
              >
                <Field label="Stage definition">
                  <Textarea
                    value={item.definition}
                    onChange={(event) =>
                      updateStage(item.stage, {
                        definition: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Barrier analysis">
                  <Textarea
                    value={item.barrier}
                    onChange={(event) =>
                      updateStage(item.stage, { barrier: event.target.value })
                    }
                  />
                </Field>
                <Field label="Reviews">
                  <Textarea
                    value={item.reviews.join("\n")}
                    onChange={(event) =>
                      updateStage(item.stage, {
                        reviews: event.target.value.split("\n").filter(Boolean),
                      })
                    }
                  />
                </Field>
              </SelectionEditor>
            ) : (
              <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
                <SummaryBlock title={item.stage}>
                  {item.definition}
                </SummaryBlock>
                <SummaryBlock title="Barrier Analysis">
                  {item.barrier}
                </SummaryBlock>
                <Accordion
                  type="single"
                  collapsible
                  className="rounded-md border border-border bg-panel px-4 xl:col-span-2"
                >
                  <AccordionItem value="reviews" className="border-0">
                    <AccordionTrigger>Reviews</AccordionTrigger>
                    <AccordionContent>
                      <div className="grid gap-3 md:grid-cols-2">
                        {item.reviews.map((review) => (
                          <blockquote
                            key={review}
                            className="rounded-md border border-border bg-card p-4 text-sm leading-6 text-muted-foreground"
                          >
                            "{review}"
                          </blockquote>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>
      <SummarizePanel
        title="Summarize"
        items={consumerStages
          .filter((item) => item.selected)
          .map((item) => `Stage: ${item.stage}`)}
        onReanalyze={onReanalyze}
      />
    </div>
  );
}

function CategoryPanel({
  editMode,
  needStates,
  setNeedStates,
  onSave,
  onReanalyze,
}: {
  editMode: boolean;
  needStates: NeedStateDrafts;
  setNeedStates: React.Dispatch<React.SetStateAction<NeedStateDrafts>>;
  onSave: () => void;
  onReanalyze: () => void;
}) {
  const [need, setNeed] = useState(needStates[0].name);
  const activeNeed =
    needStates.find((item) => item.name === need) || needStates[0];
  const chartData = needStates.map((item) => ({
    subject: item.name.replace(" & ", " / "),
    score: item.score,
  }));
  const updateNeed = (
    name: string,
    patch: Partial<NeedStateDrafts[number]>,
  ) => {
    setNeedStates((current) =>
      current.map((item) =>
        item.name === name ? { ...item, ...patch } : item,
      ),
    );
  };

  return (
    <div className="space-y-5">
      <h3 className="text-xl font-semibold">Needstates</h3>
      <Tabs value={need} onValueChange={setNeed}>
        <ResponsiveTabsList containedScroll>
          {needStates.map((item) => (
            <TabsTrigger
              key={item.name}
              value={item.name}
              className="max-w-[320px] shrink-0 justify-start gap-2 overflow-hidden border border-white/10 bg-white/10 hover:bg-white/15 data-[state=active]:border-border data-[state=active]:bg-background"
              title={item.name}
            >
              {item.selected && (
                <Star className="size-4 fill-current text-accent" />
              )}
              <span className="min-w-0 truncate">{item.name}</span>
            </TabsTrigger>
          ))}
        </ResponsiveTabsList>
        {needStates.map((item) => (
          <TabsContent key={item.name} value={item.name}>
            {editMode ? (
              <SelectionEditor
                itemLabel={item.name}
                selected={item.selected}
                onSelectedChange={(selected) =>
                  updateNeed(item.name, { selected })
                }
                onSave={onSave}
              >
                <Field label="Needstate description">
                  <Textarea
                    value={item.description}
                    onChange={(event) =>
                      updateNeed(item.name, { description: event.target.value })
                    }
                  />
                </Field>
                <Field label="Priority score">
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    value={item.score}
                    onChange={(event) =>
                      updateNeed(item.name, {
                        score: Number(event.target.value),
                      })
                    }
                  />
                </Field>
              </SelectionEditor>
            ) : (
              <SummaryBlock title={item.name}>{item.description}</SummaryBlock>
            )}
          </TabsContent>
        ))}
      </Tabs>

      <section className="grid gap-5 xl:grid-cols-[1fr_0.9fr]">
        <div className="rounded-md border border-border bg-panel p-5">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-xl font-semibold">Analyses</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Fullscreen chart"
                >
                  <Maximize2 />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Fullscreen</TooltipContent>
            </Tooltip>
          </div>
          <div className="mt-4 h-[360px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                />
                <Radar
                  dataKey="score"
                  stroke="#a3e635"
                  fill="#a3e635"
                  fillOpacity={0.28}
                />
                <ChartTooltip
                  contentStyle={{
                    background: "#151712",
                    border: "1px solid #34382e",
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-md border border-border bg-panel p-5">
          <h3 className="text-xl font-semibold">Primary category need</h3>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            {activeNeed.description}
          </p>
          <div className="mt-5">
            <Progress value={activeNeed.score} />
            <p className="mt-2 text-sm font-semibold">
              {activeNeed.score}% relevance
            </p>
          </div>
        </div>
      </section>
      <SummarizePanel
        title="Summarize"
        items={needStates
          .filter((item) => item.selected)
          .map((item) => `Needstate: ${item.name}`)}
        onReanalyze={onReanalyze}
      />
    </div>
  );
}

function SustainabilityView({
  editMode,
  goals,
  updateGoal,
  removeGoal,
  onGenerateGoals,
  onSave,
}: {
  editMode: boolean;
  goals: SustainabilityGoal[];
  updateGoal: (id: string, patch: Partial<SustainabilityGoal>) => void;
  removeGoal: (id: string) => void;
  onGenerateGoals: () => void;
  onSave: () => void;
}) {
  const goalMix = useMemo(
    () =>
      ["environmental", "social", "governance"].map((category) => ({
        category: titleCase(category),
        count: goals.filter((goal) => goal.category === category).length,
      })),
    [goals],
  );

  if (editMode) {
    return (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-2xl font-semibold">
            Edit Sustainability Analysis
          </h3>
          <div className="flex flex-wrap gap-2">
            <Button onClick={onSave}>
              <Save />
              Save
            </Button>
            <Button onClick={onGenerateGoals} variant="accent">
              <Plus />
              Generate new goals
            </Button>
          </div>
        </div>
        <Accordion
          type="multiple"
          className="rounded-md border border-border bg-panel px-4"
        >
          {goals.map((goal) => (
            <AccordionItem key={goal.id} value={goal.id}>
              <AccordionTrigger>
                <span className="flex items-center gap-2">
                  {goal.flagship ? (
                    <Star className="size-4 fill-current text-accent" />
                  ) : (
                    <FileText className="size-4 text-muted-foreground" />
                  )}
                  [{titleCase(goal.status)}] {goal.title}
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <GoalEditor
                  goal={goal}
                  updateGoal={updateGoal}
                  removeGoal={removeGoal}
                />
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <section className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <div>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 className="font-serif text-3xl font-semibold">
                Sustainability: Yoplait
              </h3>
              <p className="text-sm text-muted-foreground">
                Reporting Year: 2026
              </p>
            </div>
            <Badge variant="success">
              {goals.filter((goal) => goal.flagship).length} flagship
              commitments
            </Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {goals
              .filter((goal) => goal.flagship)
              .map((goal) => (
                <GoalCard key={goal.id} goal={goal} />
              ))}
          </div>
        </div>
        <div className="rounded-md border border-border bg-panel p-5">
          <h3 className="text-xl font-semibold">Goal mix</h3>
          <div className="mt-5 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={goalMix}
                layout="vertical"
                margin={{ left: 20, right: 20 }}
              >
                <XAxis type="number" hide />
                <YAxis
                  dataKey="category"
                  type="category"
                  width={96}
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                />
                <ChartTooltip
                  contentStyle={{
                    background: "#151712",
                    border: "1px solid #34382e",
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {goalMix.map((_, index) => (
                    <Cell key={index} fill={chartColors[index]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <Accordion
        type="single"
        collapsible
        className="rounded-md border border-border bg-panel px-4"
      >
        <AccordionItem value="other" className="border-0">
          <AccordionTrigger>View Other Goals & Commitments</AccordionTrigger>
          <AccordionContent>
            <div className="grid gap-3 md:grid-cols-2">
              {goals
                .filter((goal) => !goal.flagship)
                .map((goal) => (
                  <GoalCard key={goal.id} goal={goal} />
                ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}

function GoalCard({ goal }: { goal: SustainabilityGoal }) {
  return (
    <article className="rounded-md border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <h4 className="font-semibold leading-6">
          {goal.flagship && (
            <Star className="mr-2 inline size-4 fill-current text-accent" />
          )}
          {goal.title}
        </h4>
        <Badge
          variant={
            goal.category === "environmental"
              ? "success"
              : goal.category === "social"
                ? "warning"
                : "secondary"
          }
        >
          {titleCase(goal.category)}
        </Badge>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">
        {goal.description}
      </p>
      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <InfoMini
          label="Status & Type"
          value={`${titleCase(goal.status)} | ${titleCase(goal.type)}`}
        />
        <InfoMini
          label="Timeline"
          value={`${goal.startYear} - ${goal.endYear}`}
        />
        <InfoMini label="Sub-category" value={goal.subcategory} />
      </div>
    </article>
  );
}

function GoalEditor({
  goal,
  updateGoal,
  removeGoal,
}: {
  goal: SustainabilityGoal;
  updateGoal: (id: string, patch: Partial<SustainabilityGoal>) => void;
  removeGoal: (id: string) => void;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="flex items-center gap-3 md:col-span-2">
        <Switch
          checked={goal.flagship}
          onCheckedChange={(flagship) => updateGoal(goal.id, { flagship })}
          id={`${goal.id}-flagship`}
        />
        <Label htmlFor={`${goal.id}-flagship`}>
          Flagship / Priority Commitment
        </Label>
      </div>
      <Field label="Description">
        <Textarea
          value={goal.description}
          onChange={(event) =>
            updateGoal(goal.id, { description: event.target.value })
          }
          className="min-h-[150px]"
        />
      </Field>
      <div className="grid gap-4">
        <Field label="Category">
          <Select
            value={goal.category}
            onValueChange={(value) =>
              updateGoal(goal.id, {
                category: value as SustainabilityGoal["category"],
              })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="environmental">Environmental</SelectItem>
              <SelectItem value="social">Social</SelectItem>
              <SelectItem value="governance">Governance</SelectItem>
            </SelectContent>
          </Select>
        </Field>
        <Field label="Sub-category">
          <Input
            value={goal.subcategory}
            onChange={(event) =>
              updateGoal(goal.id, { subcategory: event.target.value })
            }
          />
        </Field>
        <Field label="Type">
          <Select
            value={goal.type}
            onValueChange={(value) =>
              updateGoal(goal.id, { type: value as SustainabilityGoal["type"] })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="target">Target</SelectItem>
              <SelectItem value="initiative">Initiative</SelectItem>
              <SelectItem value="policy">Policy</SelectItem>
            </SelectContent>
          </Select>
        </Field>
        <Field label="Status">
          <Select
            value={goal.status}
            onValueChange={(value) =>
              updateGoal(goal.id, {
                status: value as SustainabilityGoal["status"],
              })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="planned">Planned</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="complete">Complete</SelectItem>
            </SelectContent>
          </Select>
        </Field>
      </div>
      <Field label="Start Year">
        <Input
          type="number"
          value={goal.startYear}
          onChange={(event) =>
            updateGoal(goal.id, { startYear: Number(event.target.value) })
          }
        />
      </Field>
      <Field label="End Year">
        <Input
          type="number"
          value={goal.endYear}
          onChange={(event) =>
            updateGoal(goal.id, { endYear: Number(event.target.value) })
          }
        />
      </Field>
      <div className="md:col-span-2">
        <Button variant="destructive" onClick={() => removeGoal(goal.id)}>
          <Trash2 />
          Remove this goal
        </Button>
      </div>
    </div>
  );
}

function NextStepsView({
  editMode,
  recommendation,
  setRecommendation,
  onSave,
}: {
  editMode: boolean;
  recommendation: typeof recFromData;
  setRecommendation: (value: typeof recFromData) => void;
  onSave: () => void;
}) {
  const recommendationLogo = getRecommendationLogo(recommendation.title);

  if (editMode) {
    return (
      <div className="rounded-md border border-border bg-panel p-5">
        <h3 className="text-2xl font-semibold">Edit Recommendation</h3>
        <div className="mt-5 grid gap-4">
          <Field label="Product">
            <Input
              value={recommendation.title}
              onChange={(event) =>
                setRecommendation({
                  ...recommendation,
                  title: event.target.value,
                })
              }
            />
          </Field>
          <Field label="Best for">
            <Textarea
              value={recommendation.bestFor}
              onChange={(event) =>
                setRecommendation({
                  ...recommendation,
                  bestFor: event.target.value,
                })
              }
            />
          </Field>
          <Field label="Headline">
            <Input
              value={recommendation.headline}
              onChange={(event) =>
                setRecommendation({
                  ...recommendation,
                  headline: event.target.value,
                })
              }
            />
          </Field>
          <Field label="Strategic Overview">
            <Textarea
              value={recommendation.overview}
              onChange={(event) =>
                setRecommendation({
                  ...recommendation,
                  overview: event.target.value,
                })
              }
              className="min-h-[160px]"
            />
          </Field>
          <Field label="Key Outcomes">
            <Textarea
              value={recommendation.outcomes.join("\n")}
              onChange={(event) =>
                setRecommendation({
                  ...recommendation,
                  outcomes: event.target.value.split("\n").filter(Boolean),
                })
              }
            />
          </Field>
          <Button className="w-fit" onClick={onSave}>
            <Save />
            Save
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <section className="flex rounded-md border border-border bg-panel p-5">
        <div className="flex min-h-[560px] w-full flex-col">
        <img
          src={recommendationLogo.src}
          alt={recommendationLogo.alt}
          className="h-auto w-full max-w-[520px] rounded-md object-contain"
        />
        <p className="mt-4 text-sm leading-7 text-muted-foreground">
          <strong className="text-foreground">Best for:</strong>{" "}
          {recommendation.bestFor}
          </p>
          <p className="mt-5 text-xl font-semibold italic">
            {recommendation.headline}
          </p>
          <Dialog>
            <DialogTrigger asChild>
              <Button className="mt-6" variant="accent">
                <Maximize2 />
                Fullscreen
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{recommendation.title}</DialogTitle>
                <DialogDescription>{recommendation.headline}</DialogDescription>
              </DialogHeader>
            <RecommendationDeck recommendation={recommendation} />
          </DialogContent>
        </Dialog>
        </div>
      </section>

      <RecommendationDeck recommendation={recommendation} />
    </div>
  );
}

const recFromData = recommendation;

function getRecommendationLogo(title: string) {
  const normalized = title.toLowerCase();

  if (normalized.includes("brand")) {
    return { src: baLogo, alt: "Brand Activation For Good" };
  }

  if (normalized.includes("fly") || normalized.includes("wheel")) {
    return { src: fwLogo, alt: "Fly Wheel Of Impact" };
  }

  return { src: saLogo, alt: "Sustain-Agility" };
}

function RecommendationDeck({
  recommendation,
}: {
  recommendation: typeof recFromData;
}) {
  return (
    <section className="rounded-md border border-border bg-panel p-5">
      <h4 className="text-xl font-semibold">Strategic Overview</h4>
      <p className="mt-3 text-sm leading-7 text-muted-foreground">
        {recommendation.overview}
      </p>
      <h4 className="mt-6 text-xl font-semibold">Key Outcomes</h4>
      <div className="mt-4 grid gap-3">
        {recommendation.outcomes.map((outcome) => (
          <div
            key={outcome}
            className="rounded-md border border-accent/30 bg-accent/10 p-4 text-sm leading-6"
          >
            {outcome}
          </div>
        ))}
      </div>
    </section>
  );
}

function SelectionEditor({
  itemLabel,
  selected,
  onSelectedChange,
  onSave,
  children,
}: {
  itemLabel: string;
  selected: boolean;
  onSelectedChange: (selected: boolean) => void;
  onSave: () => void;
  children: React.ReactNode;
}) {
  const selectedId = `${itemLabel.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-selected`;

  return (
    <div className="space-y-4 rounded-md border border-border bg-panel p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-xl font-semibold">{itemLabel}</h3>
        <div className="flex items-center gap-3">
          <Switch
            id={selectedId}
            checked={selected}
            onCheckedChange={onSelectedChange}
          />
          <Label htmlFor={selectedId}>Use in summary</Label>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">{children}</div>
      <Button className="w-fit" onClick={onSave}>
        <Save />
        Save
      </Button>
    </div>
  );
}

function SummarizePanel({
  title,
  items,
  onReanalyze,
}: {
  title: string;
  items: string[];
  onReanalyze: () => void;
}) {
  return (
    <div className="rounded-md border border-border bg-panel p-5">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">
        Here you can reanalyze the opportunity if anything changed, based on:
      </p>
      <ul className="mt-4 grid gap-2 md:grid-cols-2">
        {items.map((item) => (
          <li
            key={item}
            className="flex gap-2 rounded-md bg-muted px-3 py-2 text-sm"
          >
            <CheckCircle2 className="mt-0.5 size-4 text-accent" />
            {item}
          </li>
        ))}
      </ul>
      <Button className="mt-4" variant="secondary" onClick={onReanalyze}>
        <RefreshCw />
        Reanalyze
      </Button>
    </div>
  );
}

function SummaryBlock({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-md border border-border bg-panel p-5">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">
        {children}
      </div>
    </article>
  );
}

function StatusPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-4 py-3">
      <p className="text-xs font-semibold uppercase text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function InfoMini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted px-3 py-2">
      <p className="text-[10px] font-semibold uppercase text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 truncate text-xs text-foreground">{value}</p>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  const id = label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  );
}

function ResponsiveTabsList({
  children,
  containedScroll = false,
}: {
  children: React.ReactNode;
  containedScroll?: boolean;
}) {
  if (containedScroll) {
    return (
      <div className="overflow-x-auto rounded-md border border-border bg-muted/50 p-1">
        <TabsList className="w-max min-w-full justify-start border-0 bg-transparent p-0">
          {children}
        </TabsList>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto pb-1">
      <TabsList className="w-max min-w-full justify-start">{children}</TabsList>
    </div>
  );
}

function titleCase(value: string) {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function isSelectedFiveC(key: FiveCTab) {
  if (key === "summary") return false;
  return true;
}

export default App;
