import { useEffect, useMemo, useRef, useState } from "react";
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
  BarChart3,
  Building2,
  CheckCircle2,
  Download,
  FileText,
  Gauge,
  Globe2,
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
  competitors as defaultCompetitors,
  culturalDrivers as defaultCulturalDrivers,
  consumerStages as defaultConsumerStages,
  gapInsights,
  initialGoals,
  needStates as defaultNeedStates,
  pageOptions,
  recommendation,
  strategicShifts as defaultStrategicShifts,
  type EvidenceBlock,
  type FiveCTab,
  type GapInsight,
  type PageKey,
  type SustainabilityGoal,
} from "@/data/gaia";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  buildBaselineEvidenceText,
  createProject,
  deleteProjectDocument,
  fileToUploadedEvidence,
  getProject,
  listProjects,
  mapPhase1ToFrontend,
  requestProjectAnalysis,
  updateProject,
  uploadProjectDocuments,
  type AnalysisState,
  type FrontendCompetitor,
  type FrontendCultureDriver,
  type FrontendConsumerStage,
  type FrontendNeedState,
  type FrontendStrategicShifts,
  type ProjectBundle,
  type ProjectDocument,
  type ProjectSummary,
  type WorkshopState,
} from "@/lib/phase1-api";

const fiveCTabs: Array<{ key: FiveCTab; label: string; icon: typeof Building2 }> = [
  { key: "summary", label: "Executive Summary", icon: Layers3 },
  { key: "company", label: "Company", icon: Building2 },
  { key: "competition", label: "Competition", icon: BarChart3 },
  { key: "culture", label: "Culture", icon: Globe2 },
  { key: "consumer", label: "Consumer", icon: Users },
  { key: "category", label: "Category", icon: Target },
];

const chartColors = ["#ff08cc", "#00aeef", "#ffa603", "#1cc35b", "#b98bcc"];
const chartTooltipContentStyle = {
  background: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "8px",
  boxShadow: "0 18px 48px rgba(0, 0, 0, 0.44)",
  color: "hsl(var(--foreground))",
};
const chartTooltipTextStyle = {
  color: "hsl(var(--foreground))",
  fontWeight: 600,
};

const pageIcons: Record<PageKey, typeof Layers3> = {
  iag: Layers3,
  fiveC: BarChart3,
  sustainability: Leaf,
  next: Target,
};

const pageLeads: Record<PageKey, string> = {
  iag: "Intention-action gap evidence, confidence, and recommended moves from the live Phase 1 analysis.",
  fiveC: "Company, competition, culture, consumer, and category signals mapped into the strategic job.",
  sustainability: "Flagship commitments, goal mix, and nutrition impact opportunities.",
  next: "Recommended product direction and the outcome case behind the next move.",
};

function cloneGaps() {
  return Object.fromEntries(gapInsights.map((gap) => [gap.key, structuredClone(gap)])) as Record<
    FiveCTab,
    GapInsight
  >;
}

function App() {
  const [page, setPage] = useState<PageKey>("iag");
  const [editMode, setEditMode] = useState(false);
  const [context, setContext] = useState("");
  const [activeGap, setActiveGap] = useState<FiveCTab>("summary");
  const [activeFiveC, setActiveFiveC] = useState<FiveCTab>("summary");
  const [gapDrafts, setGapDrafts] = useState<Record<FiveCTab, GapInsight>>(() => cloneGaps());
  const [profile, setProfile] = useState(companyProfile);
  const [phase1Shifts, setPhase1Shifts] = useState<FrontendStrategicShifts>(() => structuredClone(defaultStrategicShifts));
  const [competitorProfiles, setCompetitorProfiles] = useState<FrontendCompetitor[]>(() => structuredClone(defaultCompetitors));
  const [cultureDrivers, setCultureDrivers] = useState<FrontendCultureDriver[]>(() => structuredClone(defaultCulturalDrivers));
  const [consumerJourneyStages, setConsumerJourneyStages] = useState<FrontendConsumerStage[]>(() => structuredClone(defaultConsumerStages));
  const [categoryNeedStates, setCategoryNeedStates] = useState<FrontendNeedState[]>(() => structuredClone(defaultNeedStates));
  const [jobToBeDone, setJobToBeDone] = useState(defaultStrategicShifts.job);
  const [goals, setGoals] = useState<SustainabilityGoal[]>(initialGoals);
  const [rec, setRec] = useState(recommendation);
  const [analysisState, setAnalysisState] = useState<AnalysisState>({ status: "idle", message: "" });
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeProjectId, setActiveProjectId] = useState("");
  const [projectDocuments, setProjectDocuments] = useState<ProjectDocument[]>([]);
  const [projectLoading, setProjectLoading] = useState(true);
  const didInitializeProjects = useRef(false);

  const flagshipCount = goals.filter((goal) => goal.flagship).length;
  const averageConfidence = Math.round(
    Object.values(gapDrafts).reduce((sum, gap) => sum + gap.confidence, 0) /
      Object.values(gapDrafts).length,
  );
  const activeProject = projects.find((project) => project.id === activeProjectId);

  useEffect(() => {
    if (didInitializeProjects.current) return;
    didInitializeProjects.current = true;
    void initializeProjectWorkspace();
  }, []);

  function announce(_message: string) {
    return;
  }

  async function initializeProjectWorkspace() {
    setProjectLoading(true);
    try {
      let projectList = await listProjects();
      if (!projectList.length) {
        const created = await createProject({
          name: "Yoplait UK",
          company_name: "Yoplait UK",
          brand: "Yoplait",
        });
        projectList = [created];
      }

      const selected = projectList[0];
      setProjects(projectList);
      setActiveProjectId(selected.id);
      applyProjectBundle(await getProject(selected.id));
      setAnalysisState({ status: "ready", message: "Project workspace loaded." });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message: error instanceof Error ? error.message : "Could not load persisted projects.",
      });
    } finally {
      setProjectLoading(false);
    }
  }

  function applyProjectBundle(bundle: ProjectBundle) {
    let nextProfile = companyProfile;
    let nextGaps = cloneGaps();
    let nextGoals = initialGoals;
    let nextRecommendation = recommendation;
    let nextShifts = structuredClone(defaultStrategicShifts);
    let nextCompetitors = structuredClone(defaultCompetitors);
    let nextCultureDrivers = structuredClone(defaultCulturalDrivers);
    let nextConsumerStages = structuredClone(defaultConsumerStages);
    let nextNeedStates = structuredClone(defaultNeedStates);
    let nextJobToBeDone = defaultStrategicShifts.job;
    let nextPage: PageKey = "iag";

    if (bundle.current_analysis?.analysis) {
      const mapped = mapPhase1ToFrontend(bundle.current_analysis.analysis, nextProfile);
      nextProfile = mapped.profile;
      nextGaps = mapped.gaps;
      nextGoals = mapped.goals.length ? mapped.goals : nextGoals;
      nextRecommendation = mapped.recommendation;
      nextShifts = mapped.strategicShifts;
      nextCompetitors = mapped.competitors.length ? mapped.competitors : nextCompetitors;
      nextCultureDrivers = mapped.culturalDrivers.length ? mapped.culturalDrivers : nextCultureDrivers;
      nextConsumerStages = mapped.consumerStages.length ? mapped.consumerStages : nextConsumerStages;
      nextNeedStates = mapped.needStates.length ? mapped.needStates : nextNeedStates;
      nextJobToBeDone = mapped.jobToBeDone;
    }

    if (bundle.ui_state?.profile) nextProfile = bundle.ui_state.profile;
    if (bundle.ui_state?.gaps) nextGaps = bundle.ui_state.gaps;
    if (bundle.ui_state?.goals) nextGoals = bundle.ui_state.goals;
    if (bundle.ui_state?.recommendation) nextRecommendation = bundle.ui_state.recommendation;
    if (bundle.ui_state?.workshop) {
      nextCompetitors = bundle.ui_state.workshop.competitors?.length ? bundle.ui_state.workshop.competitors : nextCompetitors;
      nextCultureDrivers = bundle.ui_state.workshop.culture?.length ? bundle.ui_state.workshop.culture : nextCultureDrivers;
      nextConsumerStages = bundle.ui_state.workshop.consumer?.length ? bundle.ui_state.workshop.consumer : nextConsumerStages;
      nextNeedStates = bundle.ui_state.workshop.category?.length ? bundle.ui_state.workshop.category : nextNeedStates;
      if (bundle.ui_state.workshop.strategic_shifts) nextShifts = bundle.ui_state.workshop.strategic_shifts;
    }
    if (bundle.ui_state?.job_to_be_done) nextJobToBeDone = bundle.ui_state.job_to_be_done;
    if (bundle.ui_state?.active_page && isPageKey(bundle.ui_state.active_page)) {
      nextPage = bundle.ui_state.active_page;
    }

    setProfile(nextProfile);
    setGapDrafts(nextGaps);
    setGoals(nextGoals);
    setRec(nextRecommendation);
    setPhase1Shifts(nextShifts);
    setCompetitorProfiles(nextCompetitors);
    setCultureDrivers(nextCultureDrivers);
    setConsumerJourneyStages(nextConsumerStages);
    setCategoryNeedStates(nextNeedStates);
    setJobToBeDone(nextJobToBeDone);
    setPage(nextPage);
    setProjectDocuments(bundle.documents);
  }

  async function selectProject(projectId: string) {
    if (!projectId || projectId === activeProjectId) return;
    setProjectLoading(true);
    try {
      const bundle = await getProject(projectId);
      setActiveProjectId(projectId);
      applyProjectBundle(bundle);
      setContext("");
      setAnalysisState({ status: "ready", message: `${bundle.project.name} loaded.` });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message: error instanceof Error ? error.message : "Could not load project.",
      });
    } finally {
      setProjectLoading(false);
    }
  }

  function setWorkspacePage(nextPage: PageKey) {
    setPage(nextPage);
    if (!activeProjectId) return;
    void updateProject(activeProjectId, { ui_state: { active_page: nextPage } }).catch((error) => {
      setAnalysisState({
        status: "error",
        message: error instanceof Error ? error.message : "Could not save active page.",
      });
    });
  }

  function currentUiState(activePage = page) {
    return {
      profile,
      gaps: gapDrafts,
      goals,
      recommendation: rec,
      workshop: currentWorkshopState(),
      job_to_be_done: jobToBeDone,
      active_page: activePage,
    };
  }

  function currentWorkshopState(): WorkshopState {
    return {
      competitors: competitorProfiles,
      culture: cultureDrivers,
      consumer: consumerJourneyStages,
      category: categoryNeedStates,
      strategic_shifts: phase1Shifts,
    };
  }

  async function refreshProjectList() {
    setProjects(await listProjects());
  }

  async function saveCurrentProjectState(message = "Workspace saved.") {
    if (!activeProjectId) {
      setAnalysisState({ status: "error", message: "Create or select a project before saving." });
      return;
    }
    setAnalysisState({ status: "loading", message: "Saving project workspace." });
    try {
      const bundle = await updateProject(activeProjectId, { ui_state: currentUiState() });
      setProjectDocuments(bundle.documents);
      await refreshProjectList();
      setAnalysisState({ status: "ready", message });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message: error instanceof Error ? error.message : "Could not save project state.",
      });
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
    write(`Gaia ${profile.market} - ${pageOptions.find((option) => option.key === page)?.label}`, 16, 14);
    pdf.setFont("helvetica", "normal");
    write(`Exported view: ${new Date().toLocaleDateString()}`, 9, 12);
    write(gapDrafts.summary.explanation, 10, 12);
    write("Recommended next steps", 12, 6);
    gapDrafts.summary.nextSteps.forEach((step, index) => write(`${index + 1}. ${step}`, 9, 4));
    pdf.save(`gaia-${slugify(profile.market)}-iag-summary.pdf`);
    announce(`PDF export generated for the current ${profile.market} diagnostic.`);
  }

  async function reanalyze(label: string) {
    if (!activeProjectId) {
      setAnalysisState({ status: "error", message: "Create or select a project before running analysis." });
      return;
    }
    setAnalysisState({ status: "loading", message: `Analyzing ${label} with the Phase 1 backend.` });
    try {
      const fallbackText = buildBaselineEvidenceText(profile, jobToBeDone, goals, gapDrafts);
      const analysisContext = context.trim() || (projectDocuments.length ? "" : fallbackText);
      const workshopState = currentWorkshopState();
      const result = await requestProjectAnalysis(activeProjectId, analysisContext, workshopState);
      const mapped = mapPhase1ToFrontend(result.analysis, profile);
      const nextGoals = mapped.goals.length ? mapped.goals : goals;
      const nextCompetitors = workshopState.competitors.length ? workshopState.competitors : mapped.competitors;
      const nextCultureDrivers = workshopState.culture.length ? workshopState.culture : mapped.culturalDrivers;
      const nextConsumerStages = workshopState.consumer.length ? workshopState.consumer : mapped.consumerStages;
      const nextNeedStates = workshopState.category.length ? workshopState.category : mapped.needStates;
      const nextShifts = workshopState.strategic_shifts || mapped.strategicShifts;

      setGapDrafts(mapped.gaps);
      setProfile(mapped.profile);
      setJobToBeDone(mapped.jobToBeDone);
      setRec(mapped.recommendation);
      setGoals(nextGoals);
      setPhase1Shifts(nextShifts);
      setCompetitorProfiles(nextCompetitors);
      setCultureDrivers(nextCultureDrivers);
      setConsumerJourneyStages(nextConsumerStages);
      setCategoryNeedStates(nextNeedStates);
      setPage("iag");
      setActiveGap("summary");
      await updateProject(activeProjectId, {
        ui_state: {
          profile: mapped.profile,
          gaps: mapped.gaps,
          goals: nextGoals,
          recommendation: mapped.recommendation,
          workshop: {
            competitors: nextCompetitors,
            culture: nextCultureDrivers,
            consumer: nextConsumerStages,
            category: nextNeedStates,
            strategic_shifts: nextShifts,
          },
          job_to_be_done: mapped.jobToBeDone,
          active_page: "iag",
        },
      });
      await refreshProjectList();
      setAnalysisState({ status: "ready", message: `Live backend analysis applied to ${label}.` });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message: error instanceof Error ? error.message : "Phase 1 backend analysis failed.",
      });
    }
  }

  async function uploadEvidence(files: FileList | null) {
    if (!files?.length) return;
    if (!activeProjectId) {
      setAnalysisState({ status: "error", message: "Create or select a project before uploading evidence." });
      return;
    }
    setAnalysisState({ status: "loading", message: "Saving uploaded evidence to the project." });
    try {
      const uploads = await Promise.all(Array.from(files).map(fileToUploadedEvidence));
      setProjectDocuments(await uploadProjectDocuments(activeProjectId, uploads));
      await refreshProjectList();
      setAnalysisState({ status: "ready", message: "Evidence saved to the project." });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message: error instanceof Error ? error.message : "Could not save uploaded evidence.",
      });
    }
  }

  async function removeEvidence(documentId: string) {
    if (!activeProjectId) return;
    setAnalysisState({ status: "loading", message: "Removing project evidence." });
    try {
      setProjectDocuments(await deleteProjectDocument(activeProjectId, documentId));
      await refreshProjectList();
      setAnalysisState({ status: "ready", message: "Evidence removed from the project." });
    } catch (error) {
      setAnalysisState({
        status: "error",
        message: error instanceof Error ? error.message : "Could not remove evidence.",
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

  function updateCompetitor(name: string, patch: Partial<FrontendCompetitor>) {
    setCompetitorProfiles((current) => current.map((item) => (item.name === name ? { ...item, ...patch } : item)));
  }

  function updateCultureDriver(title: string, patch: Partial<FrontendCultureDriver>) {
    setCultureDrivers((current) => current.map((item) => (item.title === title ? { ...item, ...patch } : item)));
  }

  function updateConsumerStage(stage: string, patch: Partial<FrontendConsumerStage>) {
    setConsumerJourneyStages((current) => current.map((item) => (item.stage === stage ? { ...item, ...patch } : item)));
  }

  function updateNeedState(name: string, patch: Partial<FrontendNeedState>) {
    setCategoryNeedStates((current) => current.map((item) => (item.name === name ? { ...item, ...patch } : item)));
  }

  function updateStrategicShifts(nextShifts: FrontendStrategicShifts) {
    setPhase1Shifts(nextShifts);
  }

  function addNutritionGoal() {
    if (goals.some((goal) => goal.id === "nutrition-scorecard")) {
      announce("Nutrition scorecard goal is already in the sustainability set.");
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
    announce("Added a child nutrition outcome goal to close the measurement gap.");
  }

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground">
        <div className="mx-auto flex min-h-screen w-full max-w-[1680px] flex-col px-3 py-3 sm:px-5 lg:px-6">
          <WorkspaceTopbar
            page={page}
            setPage={setWorkspacePage}
            profile={profile}
            averageConfidence={averageConfidence}
            flagshipCount={flagshipCount}
          />

          <MobileControlPanel
            page={page}
            setPage={setWorkspacePage}
            editMode={editMode}
            setEditMode={(value) => {
              setEditMode(value);
              announce(value ? "Edit mode enabled." : "Presentation mode enabled.");
            }}
            projects={projects}
            activeProjectId={activeProjectId}
            activeProject={activeProject}
            onSelectProject={(projectId) => void selectProject(projectId)}
            projectLoading={projectLoading}
            context={context}
            setContext={setContext}
            onExport={exportPdf}
            onReanalyze={() => reanalyze(page === "iag" ? "the IAG conclusion" : "the current module")}
            isAnalyzing={analysisState.status === "loading"}
            analysisState={analysisState}
            projectDocuments={projectDocuments}
            onUploadEvidence={uploadEvidence}
            onRemoveEvidence={(id) => void removeEvidence(id)}
            onSummarize={() => {
              setWorkspacePage("iag");
              setActiveGap("summary");
              announce("5C selections summarized into the IAG executive view.");
            }}
            onGenerateGoals={addNutritionGoal}
          />

          <div className="mt-5 grid flex-1 gap-5 lg:grid-cols-[minmax(0,1fr)_360px] 2xl:grid-cols-[minmax(0,1fr)_390px]">
            <main className="min-w-0 overflow-hidden">
              <WorkspaceMasthead page={page} profile={profile} />
              <div id="gaia-export-area" className="pb-10">
                {page === "iag" && (
                  <IagView
                    editMode={editMode}
                    activeGap={activeGap}
                    setActiveGap={setActiveGap}
                    gaps={gapDrafts}
                    updateGap={updateGap}
                    onSave={() => void saveCurrentProjectState("IAG edits saved to the project.")}
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
                    strategicShifts={phase1Shifts}
                    competitors={competitorProfiles}
                    culturalDrivers={cultureDrivers}
                    consumerStages={consumerJourneyStages}
                    needStates={categoryNeedStates}
                    updateCompetitor={updateCompetitor}
                    updateCultureDriver={updateCultureDriver}
                    updateConsumerStage={updateConsumerStage}
                    updateNeedState={updateNeedState}
                    updateStrategicShifts={updateStrategicShifts}
                    onGenerateJob={() => {
                      setJobToBeDone(phase1Shifts.job);
                      announce("Job to be Done generated from selected 5C signals.");
                    }}
                    onReanalyze={reanalyze}
                    onSave={() => void saveCurrentProjectState("5C workspace saved to the project.")}
                  />
                )}
                {page === "sustainability" && (
                  <SustainabilityView
                    editMode={editMode}
                    market={profile.market}
                    goals={goals}
                    updateGoal={updateGoal}
                    removeGoal={(id) => {
                      setGoals((current) => current.filter((goal) => goal.id !== id));
                      announce("Sustainability goal removed from the active analysis set.");
                    }}
                    onGenerateGoals={addNutritionGoal}
                    onSave={() => void saveCurrentProjectState("Sustainability edits saved to the project.")}
                  />
                )}
                {page === "next" && (
                  <NextStepsView
                    editMode={editMode}
                    recommendation={rec}
                    setRecommendation={setRec}
                    onSave={() => void saveCurrentProjectState("Next-step recommendation saved to the project.")}
                  />
                )}
              </div>
            </main>

            <AnalysisDock
              page={page}
              setPage={setWorkspacePage}
              editMode={editMode}
              setEditMode={(value) => {
                setEditMode(value);
                announce(value ? "Edit mode enabled." : "Presentation mode enabled.");
              }}
              projects={projects}
              activeProjectId={activeProjectId}
              activeProject={activeProject}
              onSelectProject={(projectId) => void selectProject(projectId)}
              projectLoading={projectLoading}
              context={context}
              setContext={setContext}
              onExport={exportPdf}
              onReanalyze={() => reanalyze(page === "iag" ? "the IAG conclusion" : "the current module")}
              isAnalyzing={analysisState.status === "loading"}
              analysisState={analysisState}
              projectDocuments={projectDocuments}
              onUploadEvidence={uploadEvidence}
              onRemoveEvidence={(id) => void removeEvidence(id)}
              onSummarize={() => {
                setWorkspacePage("iag");
                setActiveGap("summary");
                announce("5C selections summarized into the IAG executive view.");
              }}
              onGenerateGoals={addNutritionGoal}
            />
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

type AnalysisDockProps = {
  page: PageKey;
  setPage: (page: PageKey) => void;
  editMode: boolean;
  setEditMode: (value: boolean) => void;
  projects: ProjectSummary[];
  activeProjectId: string;
  activeProject?: ProjectSummary;
  onSelectProject: (projectId: string) => void;
  projectLoading: boolean;
  context: string;
  setContext: (value: string) => void;
  onExport: () => void;
  onReanalyze: () => void;
  isAnalyzing: boolean;
  analysisState: AnalysisState;
  projectDocuments: ProjectDocument[];
  onUploadEvidence: (files: FileList | null) => void;
  onRemoveEvidence: (id: string) => void;
  onSummarize: () => void;
  onGenerateGoals: () => void;
};

function WorkspaceTopbar({
  page,
  setPage,
  profile,
  averageConfidence,
  flagshipCount,
}: {
  page: PageKey;
  setPage: (page: PageKey) => void;
  profile: typeof companyProfile;
  averageConfidence: number;
  flagshipCount: number;
}) {
  return (
    <header className="sticky top-3 z-30 overflow-hidden rounded-md border border-white/[0.12] bg-sidebar text-white shadow-[0_24px_90px_rgba(0,0,0,0.54)]">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-2 p-2 md:grid-cols-[236px_minmax(0,1fr)] lg:grid-cols-[236px_minmax(0,1fr)_300px] lg:items-stretch">
        <div className="flex h-12 items-center gap-3 rounded-md border border-white/[0.10] bg-white/[0.08] px-3 lg:h-14">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary font-serif text-lg font-semibold text-primary-foreground lg:size-10 lg:text-xl">
            G
          </div>
          <div className="min-w-0">
            <p className="truncate text-[10px] font-semibold uppercase text-white/[0.58]">IAG diagnostic</p>
            <h1 className="truncate font-serif text-xl font-semibold leading-tight">{profile.market}</h1>
          </div>
        </div>

        <div className="flex h-12 min-w-[108px] flex-col justify-center rounded-md border border-white/[0.10] bg-white/[0.08] px-3 md:hidden">
          <p className="text-[10px] font-semibold uppercase text-white/[0.58]">Status</p>
          <p className="text-sm font-semibold leading-tight">{averageConfidence}% Ready</p>
        </div>

        <nav aria-label="Workspace sections" className="col-span-2 flex gap-2 overflow-x-auto pb-0.5 md:col-span-1 md:grid md:grid-cols-4 md:overflow-visible lg:col-span-1">
          {pageOptions.map((option) => {
            const Icon = pageIcons[option.key];
            const isActive = page === option.key;
            return (
              <Button
                key={option.key}
                type="button"
                variant={isActive ? "default" : "ghost"}
                className={cn(
                  "h-11 min-w-[148px] justify-center border border-white/[0.10] px-2 text-center text-sm text-white hover:bg-white/[0.10] hover:text-white md:min-w-0 lg:h-14 lg:justify-start lg:px-3",
                  isActive && "border-primary bg-primary text-primary-foreground shadow-[0_10px_32px_rgba(255,8,204,0.32)] hover:bg-primary/90 hover:text-primary-foreground",
                )}
                onClick={() => setPage(option.key)}
              >
                <Icon />
                <span className="truncate">{option.label}</span>
              </Button>
            );
          })}
        </nav>

        <div className="col-span-2 hidden grid-cols-3 gap-2 md:grid lg:col-span-1">
          <Metric icon={Gauge} label="Confidence" value={`${averageConfidence}%`} inverse />
          <Metric icon={Leaf} label="Goals" value={String(flagshipCount)} inverse />
          <Metric icon={ShieldCheck} label="QA" value="Ready" inverse />
        </div>
      </div>
      <Progress value={100} aria-label="100% Loaded" className="h-1 rounded-none border-0 bg-white/[0.12]" />
    </header>
  );
}

function WorkspaceMasthead({ page, profile }: { page: PageKey; profile: typeof companyProfile }) {
  const currentPage = pageOptions.find((option) => option.key === page)?.label || "";
  return (
    <section className="mb-4 rounded-md border border-white/[0.12] bg-card p-4 shadow-[0_22px_80px_rgba(0,0,0,0.30)] sm:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">{profile.brand}</Badge>
        <Badge variant="secondary">{profile.market}</Badge>
      </div>
      <h2 className="mt-3 max-w-[980px] font-serif text-3xl font-semibold leading-[0.96] text-foreground sm:text-4xl md:text-5xl">
        {page === "iag" ? "5C Intention Action Gaps" : currentPage}
      </h2>
      <p className="mt-3 max-w-[860px] text-sm leading-6 text-muted-foreground sm:text-base sm:leading-7">{pageLeads[page]}</p>
    </section>
  );
}

function MobileControlPanel({
  page,
  editMode,
  setEditMode,
  projects,
  activeProjectId,
  activeProject,
  onSelectProject,
  projectLoading,
  context,
  setContext,
  onExport,
  onReanalyze,
  isAnalyzing,
  analysisState,
  projectDocuments,
  onUploadEvidence,
  onRemoveEvidence,
  onSummarize,
  onGenerateGoals,
}: AnalysisDockProps) {
  const canAnalyze = page === "iag" || page === "fiveC" || page === "sustainability";

  return (
    <section className="mt-3 rounded-md border border-white/[0.12] bg-card p-3 shadow-[0_20px_70px_rgba(0,0,0,0.34)] lg:hidden">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground">Quick actions</p>
          <h2 className="text-lg font-semibold">Workspace controls</h2>
        </div>
        <Badge variant={editMode ? "warning" : "success"}>{editMode ? "Editing" : "Viewing"}</Badge>
      </div>

      <div className="mt-3">
        <ProjectSelector
          projects={projects}
          activeProjectId={activeProjectId}
          activeProject={activeProject}
          onSelectProject={onSelectProject}
          disabled={projectLoading}
        />
      </div>

      <div className="mt-3">
        <EvidenceStateStrip context={context} projectDocuments={projectDocuments} analysisState={analysisState} />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <Button
          type="button"
          variant="outline"
          className="justify-start"
          aria-pressed={editMode}
          onClick={() => setEditMode(!editMode)}
        >
          <Pencil />
          Edit mode
        </Button>
        {(page === "iag" || page === "fiveC") && (
          <Button type="button" variant="outline" className="justify-start" onClick={onExport}>
            <Download />
            Export PDF
          </Button>
        )}
        {page === "fiveC" && (
          <Button type="button" className="justify-start" onClick={onSummarize}>
            <Sparkles />
            Summarize
          </Button>
        )}
        {page === "sustainability" && (
          <Button type="button" className="justify-start" onClick={onGenerateGoals}>
            <Plus />
            New goals
          </Button>
        )}
        {canAnalyze && (
          <Button type="button" className="col-span-2 justify-start" onClick={onReanalyze} disabled={isAnalyzing}>
            <RefreshCw className={cn(isAnalyzing && "animate-spin")} />
            {isAnalyzing ? "Analyzing..." : page === "sustainability" ? "Analyze goals" : "Run backend analysis"}
          </Button>
        )}
      </div>

      {canAnalyze && (
        <details className="mt-3 rounded-md border border-border bg-muted/40 p-3">
          <summary className="cursor-pointer text-sm font-semibold">Context & evidence</summary>
          <div className="mt-3 space-y-3">
            <Textarea
              value={context}
              onChange={(event) => setContext(event.target.value)}
              aria-label="Additional Context"
              placeholder="Paste additional context..."
              className="min-h-[96px]"
            />
            <EvidenceUploadControl
              inputId="mobile-evidence-upload"
              projectDocuments={projectDocuments}
              onUploadEvidence={onUploadEvidence}
              onRemoveEvidence={onRemoveEvidence}
            />
          </div>
        </details>
      )}
    </section>
  );
}

function AnalysisDock({
  page,
  setPage,
  editMode,
  setEditMode,
  projects,
  activeProjectId,
  activeProject,
  onSelectProject,
  projectLoading,
  context,
  setContext,
  onExport,
  onReanalyze,
  isAnalyzing,
  analysisState,
  projectDocuments,
  onUploadEvidence,
  onRemoveEvidence,
  onSummarize,
  onGenerateGoals,
}: AnalysisDockProps) {
  return (
    <aside className="hidden min-w-0 lg:sticky lg:top-[118px] lg:block lg:h-[calc(100vh-136px)] lg:overflow-y-auto">
      <div className="rounded-md border border-white/[0.12] bg-card p-4 shadow-[0_24px_90px_rgba(0,0,0,0.38)]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase text-muted-foreground">Control dock</p>
            <h2 className="mt-1 text-2xl font-semibold">Workspace</h2>
          </div>
          <Badge variant={editMode ? "warning" : "success"}>{editMode ? "Editing" : "Viewing"}</Badge>
        </div>

        <Separator className="my-4" />

        <div className="space-y-4">
          <div className="rounded-md border border-border/70 bg-muted/40 p-3">
            <ProjectSelector
              projects={projects}
              activeProjectId={activeProjectId}
              activeProject={activeProject}
              onSelectProject={onSelectProject}
              disabled={projectLoading}
            />
          </div>

          <EvidenceStateStrip context={context} projectDocuments={projectDocuments} analysisState={analysisState} />

          <div className="rounded-md border border-border/70 bg-muted/40 p-3">
            <Field label="Quick jump">
              <Select value={page} onValueChange={(value) => setPage(value as PageKey)}>
                <SelectTrigger aria-label="Selected page">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {pageOptions.map((option) => (
                    <SelectItem key={option.key} value={option.key}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          </div>

          <div className="flex items-center justify-between rounded-md border border-border bg-muted/60 px-3 py-3">
            <div className="flex items-center gap-2">
              <Pencil className="size-4 text-primary" />
              <Label htmlFor="edit-mode">Edit mode</Label>
            </div>
            <Switch id="edit-mode" checked={editMode} onCheckedChange={setEditMode} />
          </div>

          <div className="grid gap-2">
            {(page === "iag" || page === "fiveC") && (
              <Button className="w-full justify-start" variant="outline" onClick={onExport}>
                <Download />
                Export Summary PDF
              </Button>
            )}
            {page === "fiveC" && (
              <Button className="w-full justify-start" onClick={onSummarize}>
                <Sparkles />
                Summarize to IAG
              </Button>
            )}
            {page === "sustainability" && (
              <Button className="w-full justify-start" onClick={onGenerateGoals}>
                <Plus />
                Generate new goals
              </Button>
            )}
          </div>

          {(page === "iag" || page === "sustainability" || page === "fiveC") && (
            <div className="space-y-3 rounded-md border border-border bg-muted/[0.45] p-3">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold">
                  {page === "sustainability" ? "Reanalyze Goals" : "Reanalyze"}
                </h3>
                <RefreshCw className={cn("size-4 text-muted-foreground", isAnalyzing && "animate-spin text-primary")} />
              </div>
              <Textarea
                value={context}
                onChange={(event) => setContext(event.target.value)}
                aria-label="Additional Context"
                placeholder="Paste additional context..."
                className="min-h-[132px]"
              />
              <EvidenceUploadControl
                inputId="evidence-upload"
                projectDocuments={projectDocuments}
                onUploadEvidence={onUploadEvidence}
                onRemoveEvidence={onRemoveEvidence}
              />
              <Button className="w-full justify-start" onClick={onReanalyze} disabled={isAnalyzing}>
                <RefreshCw className={cn(isAnalyzing && "animate-spin")} />
                {isAnalyzing ? "Analyzing..." : page === "sustainability" ? "Analyze goals" : "Run backend analysis"}
              </Button>
              {analysisState.status === "error" && (
                <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs leading-5 text-destructive">
                  {analysisState.message}
                </p>
              )}
              {analysisState.status === "ready" && (
                <p className="rounded-md border border-primary/25 bg-primary/10 px-3 py-2 text-xs leading-5 text-muted-foreground">
                  {analysisState.message || "Workspace ready."}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

function EvidenceStateStrip({
  context,
  projectDocuments,
  analysisState,
}: {
  context: string;
  projectDocuments: ProjectDocument[];
  analysisState: AnalysisState;
}) {
  const fileLabel = `${projectDocuments.length} ${projectDocuments.length === 1 ? "file" : "files"}`;
  const contextLabel = context.trim() ? "Added" : "Empty";
  const backendLabel =
    analysisState.status === "loading"
      ? "Running"
      : analysisState.status === "ready"
        ? "Applied"
        : analysisState.status === "error"
          ? "Error"
          : "Ready";

  return (
    <div className="grid grid-cols-3 gap-2">
      <InfoMini label="Evidence" value={fileLabel} />
      <InfoMini label="Context" value={contextLabel} />
      <InfoMini label="Backend" value={backendLabel} />
    </div>
  );
}

function ProjectSelector({
  projects,
  activeProjectId,
  activeProject,
  onSelectProject,
  disabled,
}: {
  projects: ProjectSummary[];
  activeProjectId: string;
  activeProject?: ProjectSummary;
  onSelectProject: (projectId: string) => void;
  disabled?: boolean;
}) {
  return (
    <Field label="Project">
      <Select value={activeProjectId} onValueChange={onSelectProject} disabled={disabled || !projects.length}>
        <SelectTrigger aria-label="Selected project">
          <SelectValue placeholder="Loading project..." />
        </SelectTrigger>
        <SelectContent>
          {projects.map((project) => (
            <SelectItem key={project.id} value={project.id}>
              {project.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {activeProject && (
        <p className="text-xs leading-5 text-muted-foreground">
          {activeProject.company_name}
          {activeProject.last_analyzed_at ? ` | Analyzed ${formatShortDate(activeProject.last_analyzed_at)}` : ""}
        </p>
      )}
    </Field>
  );
}

function EvidenceUploadControl({
  inputId,
  projectDocuments,
  onUploadEvidence,
  onRemoveEvidence,
}: {
  inputId: string;
  projectDocuments: ProjectDocument[];
  onUploadEvidence: (files: FileList | null) => void;
  onRemoveEvidence: (id: string) => void;
}) {
  return (
    <div className="space-y-2 rounded-md border border-border bg-card p-3">
      <input
        id={inputId}
        type="file"
        multiple
        accept=".txt,.md,.csv,.json,.docx,.pdf"
        className="sr-only"
        onChange={(event) => {
          onUploadEvidence(event.target.files);
          event.target.value = "";
        }}
      />
      <Button asChild className="w-full justify-start" variant="outline">
        <label htmlFor={inputId}>
          <Upload />
          Upload evidence
        </label>
      </Button>
      {projectDocuments.length > 0 && (
        <div className="space-y-1">
          {projectDocuments.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-2 rounded-md bg-muted px-2 py-1 text-xs">
              <span className="truncate">
                {item.source} <span className="text-muted-foreground">({item.kind || "txt"})</span>
              </span>
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
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  inverse = false,
}: {
  icon: typeof Gauge;
  label: string;
  value: string;
  inverse?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex h-14 flex-col justify-center rounded-md border px-3 py-2",
        inverse
          ? "border-white/[0.10] bg-white/[0.08] text-white"
          : "border-white/[0.12] bg-card shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]",
      )}
    >
      <div className={cn("flex items-center gap-2 text-xs", inverse ? "text-white/[0.64]" : "text-muted-foreground")}>
        <Icon className={cn("size-4", inverse ? "text-primary" : "text-accent")} />
        {label}
      </div>
      <p className="mt-0.5 text-base font-semibold leading-none">{value}</p>
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
    <Tabs value={activeGap} onValueChange={(value) => setActiveGap(value as FiveCTab)}>
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
            <IagEditor gap={gaps[key]} updateGap={(patch) => updateGap(key, patch)} onSave={onSave} />
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
        <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
          <p className="text-base leading-8 text-foreground">{gap.explanation}</p>
        </div>
        <div className="rounded-md border border-primary/20 bg-primary/5 p-5 shadow-[0_16px_54px_rgba(15,23,42,0.08)]">
          <h3 className="flex items-center gap-2 text-base font-semibold">
            <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <LineChart className="size-4" />
            </span>
            Recommended next steps
          </h3>
          <ol className="mt-4 space-y-2">
            {gap.nextSteps.map((step, index) => (
              <li key={step} className="grid grid-cols-[2rem_minmax(0,1fr)] gap-3 rounded-md border border-border bg-card/80 p-3 text-sm leading-6 text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary text-xs font-semibold text-primary-foreground">
                  {index + 1}
                </span>
                <span>{step}</span>
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
    <div className="space-y-5 rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Gap type">
          <Select value={gap.type.toLowerCase()} onValueChange={(value) => updateGap({ type: titleCase(value) })}>
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
          <Select value={gap.importance.toLowerCase()} onValueChange={(value) => updateGap({ importance: titleCase(value) })}>
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
            <span className="w-10 text-sm font-semibold">{gap.confidence}%</span>
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
          onChange={(event) => updateGap({ nextSteps: event.target.value.split("\n").filter(Boolean) })}
          className="min-h-[150px]"
        />
      </Field>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Key Arguments & Supporting Evidence</h3>
        {gap.evidence.map((item, index) => (
          <div key={item.title} className="grid gap-3 rounded-md border border-border bg-card/85 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] md:grid-cols-2">
            <Field label="Title">
              <Input
                value={item.title}
                onChange={(event) => updateEvidence(gap, index, { title: event.target.value }, updateGap)}
              />
            </Field>
            <Field label="Summary">
              <Textarea
                value={item.summary}
                onChange={(event) => updateEvidence(gap, index, { summary: event.target.value }, updateGap)}
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
    <Accordion type="single" collapsible className="rounded-md border border-border bg-panel/95 px-4 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
      <AccordionItem value="evidence" className="border-0">
        <AccordionTrigger>Key Arguments & Supporting Evidence</AccordionTrigger>
        <AccordionContent>
          <div className="grid gap-4 lg:grid-cols-3">
            {evidence.map((item) => (
              <article key={item.title} className="rounded-md border border-border bg-card/85 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <h4 className="text-base font-semibold">{item.title}</h4>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.summary}</p>
                <EvidenceList title="Key Facts" items={item.facts} />
                <EvidenceList title="Supporting Evidence" items={item.sources} />
                <EvidenceList title="Quantitative Signals" items={item.signals} />
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
      <p className="text-xs font-semibold uppercase text-muted-foreground">{title}</p>
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
  competitors,
  culturalDrivers,
  consumerStages,
  needStates,
  updateCompetitor,
  updateCultureDriver,
  updateConsumerStage,
  updateNeedState,
  updateStrategicShifts,
  onGenerateJob,
  onReanalyze,
  onSave,
}: {
  editMode: boolean;
  activeFiveC: FiveCTab;
  setActiveFiveC: (key: FiveCTab) => void;
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
  jobToBeDone: string;
  setJobToBeDone: (value: string) => void;
  strategicShifts: FrontendStrategicShifts;
  competitors: FrontendCompetitor[];
  culturalDrivers: FrontendCultureDriver[];
  consumerStages: FrontendConsumerStage[];
  needStates: FrontendNeedState[];
  updateCompetitor: (name: string, patch: Partial<FrontendCompetitor>) => void;
  updateCultureDriver: (title: string, patch: Partial<FrontendCultureDriver>) => void;
  updateConsumerStage: (stage: string, patch: Partial<FrontendConsumerStage>) => void;
  updateNeedState: (name: string, patch: Partial<FrontendNeedState>) => void;
  updateStrategicShifts: (nextShifts: FrontendStrategicShifts) => void;
  onGenerateJob: () => void;
  onReanalyze: (label: string) => void;
  onSave: () => void;
}) {
  return (
    <Tabs value={activeFiveC} onValueChange={(value) => setActiveFiveC(value as FiveCTab)}>
      <ResponsiveTabsList>
        {fiveCTabs.map(({ key, label, icon: Icon }) => (
          <TabsTrigger key={key} value={key} className="gap-2">
            <Icon className="size-4" />
            {key === "summary" ? label : `${label} ${isSelectedFiveC(key) ? "*" : ""}`}
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
          updateStrategicShifts={updateStrategicShifts}
          onGenerateJob={onGenerateJob}
          onSave={onSave}
        />
      </TabsContent>
      <TabsContent value="company">
        <CompanyPanel editMode={editMode} profile={profile} setProfile={setProfile} onSave={onSave} />
      </TabsContent>
      <TabsContent value="competition">
        <CompetitionPanel
          competitors={competitors}
          updateCompetitor={updateCompetitor}
          editMode={editMode}
          onReanalyze={() => onReanalyze("the competitive opportunity")}
          onSave={onSave}
        />
      </TabsContent>
      <TabsContent value="culture">
        <CulturePanel
          culturalDrivers={culturalDrivers}
          updateCultureDriver={updateCultureDriver}
          editMode={editMode}
          onReanalyze={() => onReanalyze("the cultural opportunity")}
          onSave={onSave}
        />
      </TabsContent>
      <TabsContent value="consumer">
        <ConsumerPanel
          consumerStages={consumerStages}
          updateConsumerStage={updateConsumerStage}
          editMode={editMode}
          onReanalyze={() => onReanalyze("the consumer opportunity")}
          onSave={onSave}
        />
      </TabsContent>
      <TabsContent value="category">
        <CategoryPanel
          needStates={needStates}
          updateNeedState={updateNeedState}
          editMode={editMode}
          onReanalyze={() => onReanalyze("the category opportunity")}
          onSave={onSave}
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
  updateStrategicShifts,
  onGenerateJob,
  onSave,
}: {
  editMode: boolean;
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
  jobToBeDone: string;
  setJobToBeDone: (value: string) => void;
  strategicShifts: FrontendStrategicShifts;
  updateStrategicShifts: (nextShifts: FrontendStrategicShifts) => void;
  onGenerateJob: () => void;
  onSave: () => void;
}) {
  if (editMode) {
    return (
      <div className="space-y-5 rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
        <CompanyEditor profile={profile} setProfile={setProfile} onSave={onSave} />
        <Separator />
        <ShiftEditor strategicShifts={strategicShifts} updateStrategicShifts={updateStrategicShifts} />
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
          <Button onClick={onGenerateJob}>
            <Sparkles />
            Generate Job to be Done
          </Button>
          <Button variant="outline" onClick={onSave}>
            <Save />
            Save
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 xl:grid-cols-2">
        <SummaryBlock title="Company">
          <p><strong>Belief:</strong> {profile.belief}</p>
          <p><strong>Purpose:</strong> {profile.purpose}</p>
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
          <Button className="mt-4" onClick={onGenerateJob}>
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
    <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
      <CompanyEditor profile={profile} setProfile={setProfile} onSave={onSave} />
    </div>
  ) : (
    <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
        <p className="text-sm font-semibold uppercase text-muted-foreground">Belief</p>
        <p className="mt-2 text-lg leading-8">{profile.belief}</p>
      </div>
      <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
        <p className="text-sm font-semibold uppercase text-muted-foreground">Purpose</p>
        <h3 className="mt-2 font-serif text-2xl leading-9">{profile.purpose}</h3>
      </div>
      {Object.entries(profile.pursuits).map(([key, value]) => (
        <article key={key} className="rounded-md border border-border bg-card/85 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
          <p className="text-sm font-semibold uppercase text-muted-foreground">{key}</p>
          <p className="mt-2 text-sm leading-7 text-muted-foreground">{value}</p>
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
          onChange={(event) => setProfile({ ...profile, belief: event.target.value })}
        />
      </Field>
      <Field label="Purpose">
        <Textarea
          value={profile.purpose}
          onChange={(event) => setProfile({ ...profile, purpose: event.target.value })}
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
  strategicShifts,
  updateStrategicShifts,
}: {
  strategicShifts: FrontendStrategicShifts;
  updateStrategicShifts: (nextShifts: FrontendStrategicShifts) => void;
}) {
  const updateShift = (
    section: keyof Omit<FrontendStrategicShifts, "job">,
    patch: Partial<FrontendStrategicShifts[keyof Omit<FrontendStrategicShifts, "job">]>,
  ) => {
    updateStrategicShifts({
      ...strategicShifts,
      [section]: {
        ...strategicShifts[section],
        ...patch,
      },
    });
  };

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Field label="Opportunity Rationale">
        <Textarea
          value={strategicShifts.competition.from}
          onChange={(event) => updateShift("competition", { from: event.target.value })}
        />
      </Field>
      <Field label="Unmet Needs">
        <Textarea
          value={strategicShifts.competition.to.join("\n")}
          onChange={(event) => updateShift("competition", { to: event.target.value.split("\n").filter(Boolean) })}
        />
      </Field>
      <Field label="Cultural Tension">
        <Textarea
          value={strategicShifts.culture.from}
          onChange={(event) => updateShift("culture", { from: event.target.value })}
        />
      </Field>
      <Field label="Emerging Paradigm">
        <Textarea
          value={strategicShifts.culture.to}
          onChange={(event) => updateShift("culture", { to: event.target.value })}
        />
      </Field>
      <Field label="Core Problem">
        <Textarea
          value={strategicShifts.consumer.from}
          onChange={(event) => updateShift("consumer", { from: event.target.value })}
        />
      </Field>
      <Field label="Cultural Reason">
        <Textarea
          value={strategicShifts.consumer.to}
          onChange={(event) => updateShift("consumer", { to: event.target.value })}
        />
      </Field>
      <Field label="Primary Gap">
        <Textarea
          value={strategicShifts.category.from}
          onChange={(event) => updateShift("category", { from: event.target.value })}
        />
      </Field>
      <Field label="Recommended Fix">
        <Textarea
          value={strategicShifts.category.to}
          onChange={(event) => updateShift("category", { to: event.target.value })}
        />
      </Field>
    </div>
  );
}

function CompetitionPanel({
  competitors,
  updateCompetitor,
  editMode,
  onReanalyze,
  onSave,
}: {
  competitors: FrontendCompetitor[];
  updateCompetitor: (name: string, patch: Partial<FrontendCompetitor>) => void;
  editMode: boolean;
  onReanalyze: () => void;
  onSave: () => void;
}) {
  const [selectedCompetitor, setSelectedCompetitor] = useState(competitors[0]?.name || "");
  const competitor = competitors.find((item) => item.name === selectedCompetitor) || competitors[0];

  useEffect(() => {
    if (!competitors.length) return;
    if (!competitors.some((item) => item.name === selectedCompetitor)) {
      setSelectedCompetitor(competitors[0].name);
    }
  }, [competitors, selectedCompetitor]);

  if (!competitor) {
    return <SummaryBlock title="Competitive Evidence Required">Add competitor evidence and rerun analysis.</SummaryBlock>;
  }

  return (
    <div className="space-y-5">
      <Tabs value={selectedCompetitor} onValueChange={setSelectedCompetitor}>
        <ResponsiveTabsList>
          {competitors.map((item) => (
            <TabsTrigger key={item.name} value={item.name} className="gap-2">
              {item.selected && <Star className="size-4 fill-current text-accent" />}
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
                onSelectedChange={(selected) => updateCompetitor(item.name, { selected })}
                onSave={onSave}
              >
                <Field label="Competitor Position">
                  <Textarea value={item.position} onChange={(event) => updateCompetitor(item.name, { position: event.target.value })} />
                </Field>
                <Field label="Competitor Purpose">
                  <Textarea value={item.purpose} onChange={(event) => updateCompetitor(item.name, { purpose: event.target.value })} />
                </Field>
                <Field label="Purpose into Profit">
                  <Textarea value={item.profit} onChange={(event) => updateCompetitor(item.name, { profit: event.target.value })} />
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
        items={competitors.filter((item) => item.selected).map((item) => item.name)}
        onReanalyze={onReanalyze}
      />
      <div className="sr-only">{competitor.name}</div>
    </div>
  );
}

function CompetitorCard({ competitor }: { competitor: FrontendCompetitor }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <SummaryBlock title="Competitor Position">{competitor.position}</SummaryBlock>
      <SummaryBlock title="Competitor Purpose">{competitor.purpose}</SummaryBlock>
      <SummaryBlock title="Purpose into Profit">{competitor.profit}</SummaryBlock>
    </div>
  );
}

function CulturePanel({
  culturalDrivers,
  updateCultureDriver,
  editMode,
  onReanalyze,
  onSave,
}: {
  culturalDrivers: FrontendCultureDriver[];
  updateCultureDriver: (title: string, patch: Partial<FrontendCultureDriver>) => void;
  editMode: boolean;
  onReanalyze: () => void;
  onSave: () => void;
}) {
  const [driver, setDriver] = useState(culturalDrivers[0]?.title || "");
  const active = culturalDrivers.find((item) => item.title === driver) || culturalDrivers[0];

  useEffect(() => {
    if (!culturalDrivers.length) return;
    if (!culturalDrivers.some((item) => item.title === driver)) {
      setDriver(culturalDrivers[0].title);
    }
  }, [culturalDrivers, driver]);

  if (!active) {
    return <SummaryBlock title="Culture Evidence Required">Add culture evidence and rerun analysis.</SummaryBlock>;
  }

  return (
    <div className="space-y-5">
      <h3 className="text-xl font-semibold">Cultural Drivers</h3>
      <Tabs value={driver} onValueChange={setDriver}>
        <ResponsiveTabsList>
          {culturalDrivers.map((item) => (
            <TabsTrigger key={item.title} value={item.title} className="max-w-[280px] gap-2 text-wrap">
              {item.selected && <Star className="size-4 fill-current text-accent" />}
              {item.title}
            </TabsTrigger>
          ))}
        </ResponsiveTabsList>
        {culturalDrivers.map((item) => (
          <TabsContent key={item.title} value={item.title}>
            {editMode ? (
              <SelectionEditor
                itemLabel={item.title}
                selected={item.selected}
                onSelectedChange={(selected) => updateCultureDriver(item.title, { selected })}
                onSave={onSave}
              >
                <Field label="Cultural Observation">
                  <Textarea value={item.observation} onChange={(event) => updateCultureDriver(item.title, { observation: event.target.value })} />
                </Field>
                <Field label="Underlying Tension">
                  <Textarea value={item.tension} onChange={(event) => updateCultureDriver(item.title, { tension: event.target.value })} />
                </Field>
                <Field label="What This Means for People">
                  <Textarea value={item.people} onChange={(event) => updateCultureDriver(item.title, { people: event.target.value })} />
                </Field>
                <Field label="Marketing Implication">
                  <Textarea value={item.implication} onChange={(event) => updateCultureDriver(item.title, { implication: event.target.value })} />
                </Field>
              </SelectionEditor>
            ) : (
              <div className="grid gap-4 xl:grid-cols-2">
                <SummaryBlock title="Cultural Observation">{item.observation}</SummaryBlock>
                <SummaryBlock title="Underlying Tension">{item.tension}</SummaryBlock>
                <SummaryBlock title="What This Means for People">{item.people}</SummaryBlock>
                <SummaryBlock title="Marketing Implication">{item.implication}</SummaryBlock>
                <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)] xl:col-span-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold">Confidence</p>
                    <Badge variant="success">{item.confidence}%</Badge>
                  </div>
                  <Progress value={item.confidence} className="mt-3" />
                  <Accordion type="single" collapsible className="mt-4 rounded-md border border-border px-4">
                    <AccordionItem value="sources" className="border-0">
                      <AccordionTrigger>Sources</AccordionTrigger>
                      <AccordionContent>
                        <ul className="space-y-2">
                          {item.sources.map((source) => (
                            <li key={source} className="flex gap-2 text-sm text-muted-foreground">
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
        items={culturalDrivers.filter((item) => item.selected).map((item) => item.title)}
        onReanalyze={onReanalyze}
      />
      <div className="sr-only">{active.title}</div>
    </div>
  );
}

function ConsumerPanel({
  consumerStages,
  updateConsumerStage,
  editMode,
  onReanalyze,
  onSave,
}: {
  consumerStages: FrontendConsumerStage[];
  updateConsumerStage: (stage: string, patch: Partial<FrontendConsumerStage>) => void;
  editMode: boolean;
  onReanalyze: () => void;
  onSave: () => void;
}) {
  const [stage, setStage] = useState(consumerStages[0]?.stage || "Evaluation");

  useEffect(() => {
    if (!consumerStages.length) return;
    if (!consumerStages.some((item) => item.stage === stage)) {
      setStage(consumerStages[0].stage);
    }
  }, [consumerStages, stage]);

  if (!consumerStages.length) {
    return <SummaryBlock title="Consumer Evidence Required">Add consumer evidence and rerun analysis.</SummaryBlock>;
  }

  return (
    <div className="space-y-5">
      <Accordion type="single" collapsible className="rounded-md border border-border bg-panel/95 px-4 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
        <AccordionItem value="personas" className="border-0">
          <AccordionTrigger>Personas</AccordionTrigger>
          <AccordionContent>
            <div className="grid gap-4 md:grid-cols-3">
              {consumerStages.slice(0, 3).map((item) => (
                <article key={item.stage} className="rounded-md border border-border bg-card/85 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                  <h4 className="font-semibold">{item.stage} audience</h4>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {item.barrier || item.definition}
                  </p>
                </article>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <Tabs value={stage} onValueChange={setStage}>
        <ResponsiveTabsList>
          {consumerStages.map((item) => (
            <TabsTrigger key={item.stage} value={item.stage} className="gap-2">
              {item.selected && <Star className="size-4 fill-current text-accent" />}
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
                onSelectedChange={(selected) => updateConsumerStage(item.stage, { selected })}
                onSave={onSave}
              >
                <Field label="Stage definition">
                  <Textarea value={item.definition} onChange={(event) => updateConsumerStage(item.stage, { definition: event.target.value })} />
                </Field>
                <Field label="Barrier analysis">
                  <Textarea value={item.barrier} onChange={(event) => updateConsumerStage(item.stage, { barrier: event.target.value })} />
                </Field>
                <Field label="Reviews">
                  <Textarea
                    value={item.reviews.join("\n")}
                    onChange={(event) => updateConsumerStage(item.stage, { reviews: event.target.value.split("\n").filter(Boolean) })}
                  />
                </Field>
              </SelectionEditor>
            ) : (
              <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
                <SummaryBlock title={item.stage}>{item.definition}</SummaryBlock>
                <SummaryBlock title="Barrier Analysis">{item.barrier}</SummaryBlock>
                <Accordion type="single" collapsible className="rounded-md border border-border bg-panel/95 px-4 shadow-[0_16px_54px_rgba(0,0,0,0.16)] xl:col-span-2">
                  <AccordionItem value="reviews" className="border-0">
                    <AccordionTrigger>Reviews</AccordionTrigger>
                    <AccordionContent>
                      <div className="grid gap-3 md:grid-cols-2">
                        {item.reviews.map((review) => (
                          <blockquote key={review} className="rounded-md border border-border bg-card/85 p-4 text-sm leading-6 text-muted-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
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
        items={consumerStages.filter((item) => item.selected).map((item) => `Stage: ${item.stage}`)}
        onReanalyze={onReanalyze}
      />
    </div>
  );
}

function CategoryPanel({
  needStates,
  updateNeedState,
  editMode,
  onReanalyze,
  onSave,
}: {
  needStates: FrontendNeedState[];
  updateNeedState: (name: string, patch: Partial<FrontendNeedState>) => void;
  editMode: boolean;
  onReanalyze: () => void;
  onSave: () => void;
}) {
  const [need, setNeed] = useState(needStates[0]?.name || "");
  const activeNeed = needStates.find((item) => item.name === need) || needStates[0];
  const chartData = needStates.map((item) => ({
    subject: item.name.replace(" & ", " / "),
    score: item.score,
  }));

  useEffect(() => {
    if (!needStates.length) return;
    if (!needStates.some((item) => item.name === need)) {
      setNeed(needStates[0].name);
    }
  }, [needStates, need]);

  if (!activeNeed) {
    return <SummaryBlock title="Category Evidence Required">Add category evidence and rerun analysis.</SummaryBlock>;
  }

  return (
    <div className="space-y-5">
      <h3 className="text-xl font-semibold">Needstates</h3>
      <Tabs value={need} onValueChange={setNeed}>
        <ResponsiveTabsList>
          {needStates.map((item) => (
            <TabsTrigger key={item.name} value={item.name} className="max-w-[290px] gap-2 text-wrap">
              {item.selected && <Star className="size-4 fill-current text-accent" />}
              {item.name}
            </TabsTrigger>
          ))}
        </ResponsiveTabsList>
        {needStates.map((item) => (
          <TabsContent key={item.name} value={item.name}>
            {editMode ? (
              <SelectionEditor
                itemLabel={item.name}
                selected={item.selected}
                onSelectedChange={(selected) => updateNeedState(item.name, { selected })}
                onSave={onSave}
              >
                <Field label="Needstate description">
                  <Textarea value={item.description} onChange={(event) => updateNeedState(item.name, { description: event.target.value })} />
                </Field>
                <Field label="Priority score">
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    value={item.score}
                    onChange={(event) => updateNeedState(item.name, { score: Number(event.target.value) })}
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
        <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-xl font-semibold">Analyses</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="icon" aria-label="Fullscreen chart">
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
                <PolarAngleAxis dataKey="subject" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
                <Radar dataKey="score" stroke="#a3e635" fill="#a3e635" fillOpacity={0.28} />
                <ChartTooltip
                  contentStyle={chartTooltipContentStyle}
                  labelStyle={chartTooltipTextStyle}
                  itemStyle={chartTooltipTextStyle}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
          <h3 className="text-xl font-semibold">Primary category need</h3>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">{activeNeed.description}</p>
          <div className="mt-5">
            <Progress value={activeNeed.score} />
            <p className="mt-2 text-sm font-semibold">{activeNeed.score}% relevance</p>
          </div>
        </div>
      </section>
      <SummarizePanel
        title="Summarize"
        items={needStates.filter((item) => item.selected).map((item) => `Needstate: ${item.name}`)}
        onReanalyze={onReanalyze}
      />
    </div>
  );
}

function SustainabilityView({
  editMode,
  market,
  goals,
  updateGoal,
  removeGoal,
  onGenerateGoals,
  onSave,
}: {
  editMode: boolean;
  market: string;
  goals: SustainabilityGoal[];
  updateGoal: (id: string, patch: Partial<SustainabilityGoal>) => void;
  removeGoal: (id: string) => void;
  onGenerateGoals: () => void;
  onSave: () => void;
}) {
  const reportingYear = goals.reduce((year, goal) => Math.max(year, goal.endYear), 2026);
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
          <h3 className="text-2xl font-semibold">Edit Sustainability Analysis</h3>
          <div className="flex flex-wrap gap-2">
            <Button onClick={onGenerateGoals}>
              <Plus />
              Generate new goals
            </Button>
            <Button variant="outline" onClick={onSave}>
              <Save />
              Save
            </Button>
          </div>
        </div>
        <Accordion type="multiple" className="rounded-md border border-border bg-panel/95 px-4 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
          {goals.map((goal) => (
            <AccordionItem key={goal.id} value={goal.id}>
              <AccordionTrigger>
                <span className="flex items-center gap-2">
                  {goal.flagship ? <Star className="size-4 fill-current text-accent" /> : <FileText className="size-4 text-muted-foreground" />}
                  [{titleCase(goal.status)}] {goal.title}
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <GoalEditor goal={goal} updateGoal={updateGoal} removeGoal={removeGoal} />
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
              <h3 className="font-serif text-3xl font-semibold">Sustainability: {market}</h3>
              <p className="text-sm text-muted-foreground">Reporting Year: {reportingYear}</p>
            </div>
            <Badge variant="success">{goals.filter((goal) => goal.flagship).length} flagship commitments</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {goals.filter((goal) => goal.flagship).map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        </div>
        <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
          <h3 className="text-xl font-semibold">Goal mix</h3>
          <div className="mt-5 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={goalMix} layout="vertical" margin={{ left: 20, right: 20 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="category" type="category" width={96} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                <ChartTooltip
                  contentStyle={chartTooltipContentStyle}
                  labelStyle={chartTooltipTextStyle}
                  itemStyle={chartTooltipTextStyle}
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

      <Accordion type="single" collapsible className="rounded-md border border-border bg-panel/95 px-4 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
        <AccordionItem value="other" className="border-0">
          <AccordionTrigger>View Other Goals & Commitments</AccordionTrigger>
          <AccordionContent>
            <div className="grid gap-3 md:grid-cols-2">
              {goals.filter((goal) => !goal.flagship).map((goal) => (
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
    <article className="rounded-md border border-border bg-card/85 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
      <div className="flex items-start justify-between gap-3">
        <h4 className="font-semibold leading-6">
          {goal.flagship && <Star className="mr-2 inline size-4 fill-current text-accent" />}
          {goal.title}
        </h4>
        <Badge variant={goal.category === "environmental" ? "success" : goal.category === "social" ? "warning" : "secondary"}>
          {titleCase(goal.category)}
        </Badge>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{goal.description}</p>
      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <InfoMini label="Status & Type" value={`${titleCase(goal.status)} | ${titleCase(goal.type)}`} />
        <InfoMini label="Timeline" value={`${goal.startYear} - ${goal.endYear}`} />
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
        <Label htmlFor={`${goal.id}-flagship`}>Flagship / Priority Commitment</Label>
      </div>
      <Field label="Description">
        <Textarea
          value={goal.description}
          onChange={(event) => updateGoal(goal.id, { description: event.target.value })}
          className="min-h-[150px]"
        />
      </Field>
      <div className="grid gap-4">
        <Field label="Category">
          <Select value={goal.category} onValueChange={(value) => updateGoal(goal.id, { category: value as SustainabilityGoal["category"] })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="environmental">Environmental</SelectItem>
              <SelectItem value="social">Social</SelectItem>
              <SelectItem value="governance">Governance</SelectItem>
            </SelectContent>
          </Select>
        </Field>
        <Field label="Sub-category">
          <Input value={goal.subcategory} onChange={(event) => updateGoal(goal.id, { subcategory: event.target.value })} />
        </Field>
        <Field label="Type">
          <Select value={goal.type} onValueChange={(value) => updateGoal(goal.id, { type: value as SustainabilityGoal["type"] })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="target">Target</SelectItem>
              <SelectItem value="initiative">Initiative</SelectItem>
              <SelectItem value="policy">Policy</SelectItem>
            </SelectContent>
          </Select>
        </Field>
        <Field label="Status">
          <Select value={goal.status} onValueChange={(value) => updateGoal(goal.id, { status: value as SustainabilityGoal["status"] })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
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
          onChange={(event) => updateGoal(goal.id, { startYear: Number(event.target.value) })}
        />
      </Field>
      <Field label="End Year">
        <Input
          type="number"
          value={goal.endYear}
          onChange={(event) => updateGoal(goal.id, { endYear: Number(event.target.value) })}
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
  if (editMode) {
    return (
      <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
        <h3 className="text-2xl font-semibold">Edit Recommendation</h3>
        <div className="mt-5 grid gap-4">
          <Field label="Product">
            <Input
              value={recommendation.title}
              onChange={(event) => setRecommendation({ ...recommendation, title: event.target.value })}
            />
          </Field>
          <Field label="Best for">
            <Textarea
              value={recommendation.bestFor}
              onChange={(event) => setRecommendation({ ...recommendation, bestFor: event.target.value })}
            />
          </Field>
          <Field label="Headline">
            <Input
              value={recommendation.headline}
              onChange={(event) => setRecommendation({ ...recommendation, headline: event.target.value })}
            />
          </Field>
          <Field label="Strategic Overview">
            <Textarea
              value={recommendation.overview}
              onChange={(event) => setRecommendation({ ...recommendation, overview: event.target.value })}
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
      <section className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
        <Badge variant="outline">Next recommended product</Badge>
        <h3 className="mt-4 font-serif text-4xl font-semibold">{recommendation.title}</h3>
        <p className="mt-4 text-sm leading-7 text-muted-foreground">
          <strong className="text-foreground">Best for:</strong> {recommendation.bestFor}
        </p>
        <p className="mt-5 text-xl font-semibold italic">{recommendation.headline}</p>
        <Dialog>
          <DialogTrigger asChild>
            <Button className="mt-6" variant="outline">
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
      </section>

      <RecommendationDeck recommendation={recommendation} />
    </div>
  );
}

const recFromData = recommendation;

function RecommendationDeck({ recommendation }: { recommendation: typeof recFromData }) {
  return (
    <section className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
      <h4 className="text-xl font-semibold">Strategic Overview</h4>
      <p className="mt-3 text-sm leading-7 text-muted-foreground">{recommendation.overview}</p>
      <h4 className="mt-6 text-xl font-semibold">Key Outcomes</h4>
      <div className="mt-4 grid gap-3">
        {recommendation.outcomes.map((outcome) => (
          <div key={outcome} className="rounded-md border border-accent/30 bg-accent/10 p-4 text-sm leading-6">
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
  return (
    <div className="space-y-4 rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-xl font-semibold">{itemLabel}</h3>
        <div className="flex items-center gap-3">
          <Switch checked={selected} onCheckedChange={onSelectedChange} />
          <Label>Use in summary</Label>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">{children}</div>
      <Button className="w-fit" onClick={onSave}><Save />Save</Button>
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
    <div className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">
        Here you can reanalyze the opportunity if anything changed, based on:
      </p>
      <ul className="mt-4 grid gap-2 md:grid-cols-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2 rounded-md bg-muted/80 px-3 py-2 text-sm">
            <CheckCircle2 className="mt-0.5 size-4 text-accent" />
            {item}
          </li>
        ))}
      </ul>
      <Button className="mt-4" onClick={onReanalyze}>
        <RefreshCw />
        Reanalyze
      </Button>
    </div>
  );
}

function SummaryBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="rounded-md border border-border bg-panel/95 p-5 shadow-[0_16px_54px_rgba(0,0,0,0.16)]">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">{children}</div>
    </article>
  );
}

function StatusPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card/85 px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
      <p className="text-xs font-semibold uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function InfoMini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border/70 bg-muted/80 px-3 py-2">
      <p className="text-[10px] font-semibold uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-xs text-foreground">{value}</p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  const id = label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  );
}

function ResponsiveTabsList({ children }: { children: React.ReactNode }) {
  return (
    <div className="z-20 -mx-1 rounded-md bg-background/85 px-1 pb-1 backdrop-blur lg:sticky lg:top-[104px]">
      <div className="relative overflow-hidden rounded-md after:pointer-events-none after:absolute after:inset-y-0 after:right-0 after:w-10 after:bg-gradient-to-l after:from-background after:to-transparent">
        <div className="overflow-x-auto pb-1">
          <TabsList className="w-max min-w-full justify-start [&_[role=tab]]:h-9 [&_[role=tab]]:px-2.5 [&_[role=tab]]:text-xs sm:[&_[role=tab]]:text-sm">
            {children}
          </TabsList>
        </div>
      </div>
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

function isPageKey(value: string): value is PageKey {
  return pageOptions.some((option) => option.key === value);
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48) || "phase-1";
}

function formatShortDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "recently";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default App;
