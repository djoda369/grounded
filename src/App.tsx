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
  BarChart3,
  Building2,
  CheckCircle2,
  Download,
  FileText,
  Gauge,
  Globe2,
  Home,
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
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

const fiveCTabs: Array<{ key: FiveCTab; label: string; icon: typeof Building2 }> = [
  { key: "summary", label: "Executive Summary", icon: Layers3 },
  { key: "company", label: "Company", icon: Building2 },
  { key: "competition", label: "Competition", icon: BarChart3 },
  { key: "culture", label: "Culture", icon: Globe2 },
  { key: "consumer", label: "Consumer", icon: Users },
  { key: "category", label: "Category", icon: Target },
];

const chartColors = ["#a3e635", "#38bdf8", "#fb7185", "#fbbf24", "#c084fc"];

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
  const [jobToBeDone, setJobToBeDone] = useState(strategicShifts.job);
  const [goals, setGoals] = useState<SustainabilityGoal[]>(initialGoals);
  const [rec, setRec] = useState(recommendation);

  const flagshipCount = goals.filter((goal) => goal.flagship).length;
  const averageConfidence = Math.round(
    Object.values(gapDrafts).reduce((sum, gap) => sum + gap.confidence, 0) /
      Object.values(gapDrafts).length,
  );

  function announce(_message: string) {
    return;
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
    pdf.save("gaia-yoplait-iag-summary.pdf");
    announce("PDF export generated for the current Yoplait diagnostic.");
  }

  function reanalyze(label: string) {
    const note = context.trim()
      ? `Reanalyzed ${label} using the added context: "${context.trim()}".`
      : `Reanalyzed ${label} with the current selected evidence set.`;
    announce(note);
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
        <div className="flex min-h-screen">
          <Sidebar
            page={page}
            setPage={(nextPage) => {
              setPage(nextPage);
            }}
            editMode={editMode}
            setEditMode={(value) => {
              setEditMode(value);
              announce(value ? "Edit mode enabled." : "Presentation mode enabled.");
            }}
            context={context}
            setContext={setContext}
            onExport={exportPdf}
            onReanalyze={() => reanalyze(page === "iag" ? "the IAG conclusion" : "the current module")}
            onSummarize={() => {
              setPage("iag");
              setActiveGap("summary");
              announce("5C selections summarized into the IAG executive view.");
            }}
            onGenerateGoals={addNutritionGoal}
          />

          <main className="flex-1 overflow-hidden">
            <div className="mx-auto flex min-h-screen w-full max-w-[1480px] flex-col px-5 py-5 md:px-8 lg:px-10">
              <Header
                page={page}
                profile={profile}
                averageConfidence={averageConfidence}
                flagshipCount={flagshipCount}
              />
              <div id="gaia-export-area" className="flex-1 pb-10">
                {page === "iag" && (
                  <IagView
                    editMode={editMode}
                    activeGap={activeGap}
                    setActiveGap={setActiveGap}
                    gaps={gapDrafts}
                    updateGap={updateGap}
                    onSave={() => announce("IAG edits saved locally for the demo session.")}
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
                    onGenerateJob={() => {
                      setJobToBeDone(strategicShifts.job);
                      announce("Job to be Done generated from selected 5C signals.");
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
                      setGoals((current) => current.filter((goal) => goal.id !== id));
                      announce("Sustainability goal removed from the active analysis set.");
                    }}
                    onGenerateGoals={addNutritionGoal}
                  />
                )}
                {page === "next" && (
                  <NextStepsView
                    editMode={editMode}
                    recommendation={rec}
                    setRecommendation={setRec}
                    onSave={() => announce("Next-step recommendation updated.")}
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
  editMode: boolean;
  setEditMode: (value: boolean) => void;
  context: string;
  setContext: (value: string) => void;
  onExport: () => void;
  onReanalyze: () => void;
  onSummarize: () => void;
  onGenerateGoals: () => void;
};

function Sidebar({
  page,
  setPage,
  editMode,
  setEditMode,
  context,
  setContext,
  onExport,
  onReanalyze,
  onSummarize,
  onGenerateGoals,
}: SidebarProps) {
  return (
    <aside className="hidden w-[290px] shrink-0 border-r border-border bg-sidebar px-5 py-5 md:block">
      <nav className="space-y-6">
        <div>
          <h1 className="font-serif text-3xl font-semibold">Gaia</h1>
        </div>

        <div className="space-y-2">
          <a className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted" href="#">
            <Home className="size-4" />
            Home
          </a>
          <div className="rounded-md border border-border bg-muted/60 px-3 py-2 text-sm font-semibold">
            Yoplait UK
          </div>
        </div>

        <Separator />

        <div className="space-y-3">
          <Label className="flex items-center gap-2 text-muted-foreground">
            <FileText className="size-4" />
            Page
          </Label>
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
        </div>

        <div className="flex items-center justify-between rounded-md border border-border bg-card px-3 py-3">
          <div className="flex items-center gap-2">
            <Pencil className="size-4 text-accent" />
            <Label htmlFor="edit-mode">Edit mode</Label>
          </div>
          <Switch id="edit-mode" checked={editMode} onCheckedChange={setEditMode} />
        </div>

        <div className="space-y-2">
          {(page === "iag" || page === "fiveC") && (
            <Button className="w-full justify-start" variant="outline" onClick={onExport}>
              <Download />
              Export Summary PDF
            </Button>
          )}
          {page === "fiveC" && (
            <Button className="w-full justify-start" variant="accent" onClick={onSummarize}>
              <Sparkles />
              Summarize to IAG
            </Button>
          )}
          {page === "sustainability" && (
            <Button className="w-full justify-start" variant="accent" onClick={onGenerateGoals}>
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
            <Button className="w-full justify-start" variant="secondary" onClick={onReanalyze}>
              <RefreshCw />
              {page === "sustainability" ? "Generate new goals" : "Reanalyze conclusion"}
            </Button>
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
  const currentPage = pageOptions.find((option) => option.key === page)?.label;
  return (
    <header className="mb-5 space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline">{profile.market}</Badge>
            <span>{currentPage}</span>
          </div>
          <h2 className="mt-3 font-serif text-4xl font-semibold md:text-5xl">
            {page === "iag" ? "5C Intention Action Gaps" : currentPage}
          </h2>
        </div>
        <div className="grid grid-cols-3 gap-2 lg:w-[520px]">
          <Metric icon={Gauge} label="Confidence" value={`${averageConfidence}%`} />
          <Metric icon={Leaf} label="Goals" value={String(flagshipCount)} />
          <Metric icon={ShieldCheck} label="QA" value="Ready" />
        </div>
      </div>
      <Progress value={100} aria-label="100% Loaded" />
    </header>
  );
}

function Metric({ icon: Icon, label, value }: { icon: typeof Gauge; label: string; value: string }) {
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
        <div className="rounded-md border border-border bg-panel p-5">
          <p className="text-base leading-8 text-foreground">{gap.explanation}</p>
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
          <div key={item.title} className="grid gap-3 rounded-md border border-border bg-card p-4 md:grid-cols-2">
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
    <Accordion type="single" collapsible className="rounded-md border border-border bg-panel px-4">
      <AccordionItem value="evidence" className="border-0">
        <AccordionTrigger>Key Arguments & Supporting Evidence</AccordionTrigger>
        <AccordionContent>
          <div className="grid gap-4 lg:grid-cols-3">
            {evidence.map((item) => (
              <article key={item.title} className="rounded-md border border-border bg-card p-4">
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
  onGenerateJob: () => void;
  onReanalyze: (label: string) => void;
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
          onGenerateJob={onGenerateJob}
        />
      </TabsContent>
      <TabsContent value="company">
        <CompanyPanel editMode={editMode} profile={profile} setProfile={setProfile} />
      </TabsContent>
      <TabsContent value="competition">
        <CompetitionPanel editMode={editMode} onReanalyze={() => onReanalyze("the competitive opportunity")} />
      </TabsContent>
      <TabsContent value="culture">
        <CulturePanel editMode={editMode} onReanalyze={() => onReanalyze("the cultural opportunity")} />
      </TabsContent>
      <TabsContent value="consumer">
        <ConsumerPanel editMode={editMode} onReanalyze={() => onReanalyze("the consumer opportunity")} />
      </TabsContent>
      <TabsContent value="category">
        <CategoryPanel editMode={editMode} onReanalyze={() => onReanalyze("the category opportunity")} />
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
  onGenerateJob,
}: {
  editMode: boolean;
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
  jobToBeDone: string;
  setJobToBeDone: (value: string) => void;
  onGenerateJob: () => void;
}) {
  if (editMode) {
    return (
      <div className="space-y-5 rounded-md border border-border bg-panel p-5">
        <CompanyEditor profile={profile} setProfile={setProfile} />
        <Separator />
        <ShiftEditor />
        <Separator />
        <Field label="Job to be Done">
          <Textarea
            value={jobToBeDone}
            onChange={(event) => setJobToBeDone(event.target.value)}
            placeholder="Generate or type the strategic Job to be Done statement..."
            className="min-h-[120px]"
          />
        </Field>
        <Button onClick={onGenerateJob}>
          <Sparkles />
          Generate Job to be Done
        </Button>
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
}: {
  editMode: boolean;
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
}) {
  return editMode ? (
    <div className="rounded-md border border-border bg-panel p-5">
      <CompanyEditor profile={profile} setProfile={setProfile} />
    </div>
  ) : (
    <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="rounded-md border border-border bg-panel p-5">
        <p className="text-sm font-semibold uppercase text-muted-foreground">Belief</p>
        <p className="mt-2 text-lg leading-8">{profile.belief}</p>
      </div>
      <div className="rounded-md border border-border bg-panel p-5">
        <p className="text-sm font-semibold uppercase text-muted-foreground">Purpose</p>
        <h3 className="mt-2 font-serif text-2xl leading-9">{profile.purpose}</h3>
      </div>
      {Object.entries(profile.pursuits).map(([key, value]) => (
        <article key={key} className="rounded-md border border-border bg-card p-5">
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
}: {
  profile: typeof companyProfile;
  setProfile: (profile: typeof companyProfile) => void;
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
      <Button className="w-fit">
        <Save />
        Save
      </Button>
    </div>
  );
}

function ShiftEditor() {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Field label="Opportunity Rationale">
        <Textarea defaultValue={strategicShifts.competition.from} />
      </Field>
      <Field label="Unmet Needs">
        <Textarea defaultValue={strategicShifts.competition.to.join("\n")} />
      </Field>
      <Field label="Cultural Tension">
        <Textarea defaultValue={strategicShifts.culture.from} />
      </Field>
      <Field label="Emerging Paradigm">
        <Textarea defaultValue={strategicShifts.culture.to} />
      </Field>
      <Field label="Core Problem">
        <Textarea defaultValue={strategicShifts.consumer.from} />
      </Field>
      <Field label="Cultural Reason">
        <Textarea defaultValue={strategicShifts.consumer.to} />
      </Field>
      <Field label="Primary Gap">
        <Textarea defaultValue={strategicShifts.category.from} />
      </Field>
      <Field label="Recommended Fix">
        <Textarea defaultValue={strategicShifts.category.to} />
      </Field>
    </div>
  );
}

function CompetitionPanel({ editMode, onReanalyze }: { editMode: boolean; onReanalyze: () => void }) {
  const [selectedCompetitor, setSelectedCompetitor] = useState(competitors[0].name);
  const competitor = competitors.find((item) => item.name === selectedCompetitor) || competitors[0];
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
              <SelectionEditor itemLabel={item.name} selected={item.selected}>
                <Field label="Competitor Position"><Textarea defaultValue={item.position} /></Field>
                <Field label="Competitor Purpose"><Textarea defaultValue={item.purpose} /></Field>
                <Field label="Purpose into Profit"><Textarea defaultValue={item.profit} /></Field>
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

function CompetitorCard({ competitor }: { competitor: (typeof competitors)[number] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <SummaryBlock title="Competitor Position">{competitor.position}</SummaryBlock>
      <SummaryBlock title="Competitor Purpose">{competitor.purpose}</SummaryBlock>
      <SummaryBlock title="Purpose into Profit">{competitor.profit}</SummaryBlock>
    </div>
  );
}

function CulturePanel({ editMode, onReanalyze }: { editMode: boolean; onReanalyze: () => void }) {
  const [driver, setDriver] = useState(culturalDrivers[0].title);
  const active = culturalDrivers.find((item) => item.title === driver) || culturalDrivers[0];
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
              <SelectionEditor itemLabel={item.title} selected={item.selected}>
                <Field label="Cultural Observation"><Textarea defaultValue={item.observation} /></Field>
                <Field label="Underlying Tension"><Textarea defaultValue={item.tension} /></Field>
                <Field label="What This Means for People"><Textarea defaultValue={item.people} /></Field>
                <Field label="Marketing Implication"><Textarea defaultValue={item.implication} /></Field>
              </SelectionEditor>
            ) : (
              <div className="grid gap-4 xl:grid-cols-2">
                <SummaryBlock title="Cultural Observation">{item.observation}</SummaryBlock>
                <SummaryBlock title="Underlying Tension">{item.tension}</SummaryBlock>
                <SummaryBlock title="What This Means for People">{item.people}</SummaryBlock>
                <SummaryBlock title="Marketing Implication">{item.implication}</SummaryBlock>
                <div className="rounded-md border border-border bg-panel p-5 xl:col-span-2">
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

function ConsumerPanel({ editMode, onReanalyze }: { editMode: boolean; onReanalyze: () => void }) {
  const [stage, setStage] = useState("Discovery");
  return (
    <div className="space-y-5">
      <Accordion type="single" collapsible className="rounded-md border border-border bg-panel px-4">
        <AccordionItem value="personas" className="border-0">
          <AccordionTrigger>Personas</AccordionTrigger>
          <AccordionContent>
            <div className="grid gap-4 md:grid-cols-3">
              {["Pragmatic Parent", "Label Scrutinizer", "Nostalgic Buyer"].map((persona) => (
                <article key={persona} className="rounded-md border border-border bg-card p-4">
                  <h4 className="font-semibold">{persona}</h4>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    Motivated by child wellbeing, practical routines, and confidence that the product delivers what it promises.
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
              <SelectionEditor itemLabel={item.stage} selected={item.selected}>
                <Field label="Stage definition"><Textarea defaultValue={item.definition} /></Field>
                <Field label="Barrier analysis"><Textarea defaultValue={item.barrier} /></Field>
                <Field label="Reviews"><Textarea defaultValue={item.reviews.join("\n")} /></Field>
              </SelectionEditor>
            ) : (
              <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
                <SummaryBlock title={item.stage}>{item.definition}</SummaryBlock>
                <SummaryBlock title="Barrier Analysis">{item.barrier}</SummaryBlock>
                <Accordion type="single" collapsible className="rounded-md border border-border bg-panel px-4 xl:col-span-2">
                  <AccordionItem value="reviews" className="border-0">
                    <AccordionTrigger>Reviews</AccordionTrigger>
                    <AccordionContent>
                      <div className="grid gap-3 md:grid-cols-2">
                        {item.reviews.map((review) => (
                          <blockquote key={review} className="rounded-md border border-border bg-card p-4 text-sm leading-6 text-muted-foreground">
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

function CategoryPanel({ editMode, onReanalyze }: { editMode: boolean; onReanalyze: () => void }) {
  const [need, setNeed] = useState(needStates[0].name);
  const activeNeed = needStates.find((item) => item.name === need) || needStates[0];
  const chartData = needStates.map((item) => ({
    subject: item.name.replace(" & ", " / "),
    score: item.score,
  }));

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
              <SelectionEditor itemLabel={item.name} selected={item.selected}>
                <Field label="Needstate description"><Textarea defaultValue={item.description} /></Field>
                <Field label="Priority score"><Input type="number" min={0} max={100} defaultValue={item.score} /></Field>
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
                <ChartTooltip contentStyle={{ background: "#151712", border: "1px solid #34382e" }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-md border border-border bg-panel p-5">
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
  goals,
  updateGoal,
  removeGoal,
  onGenerateGoals,
}: {
  editMode: boolean;
  goals: SustainabilityGoal[];
  updateGoal: (id: string, patch: Partial<SustainabilityGoal>) => void;
  removeGoal: (id: string) => void;
  onGenerateGoals: () => void;
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
          <h3 className="text-2xl font-semibold">Edit Sustainability Analysis</h3>
          <Button onClick={onGenerateGoals} variant="accent">
            <Plus />
            Generate new goals
          </Button>
        </div>
        <Accordion type="multiple" className="rounded-md border border-border bg-panel px-4">
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
              <h3 className="font-serif text-3xl font-semibold">Sustainability: Yoplait</h3>
              <p className="text-sm text-muted-foreground">Reporting Year: 2026</p>
            </div>
            <Badge variant="success">{goals.filter((goal) => goal.flagship).length} flagship commitments</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {goals.filter((goal) => goal.flagship).map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        </div>
        <div className="rounded-md border border-border bg-panel p-5">
          <h3 className="text-xl font-semibold">Goal mix</h3>
          <div className="mt-5 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={goalMix} layout="vertical" margin={{ left: 20, right: 20 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="category" type="category" width={96} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                <ChartTooltip contentStyle={{ background: "#151712", border: "1px solid #34382e" }} />
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

      <Accordion type="single" collapsible className="rounded-md border border-border bg-panel px-4">
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
    <article className="rounded-md border border-border bg-card p-4">
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
      <div className="rounded-md border border-border bg-panel p-5">
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
      <section className="rounded-md border border-border bg-panel p-5">
        <Badge variant="outline">Next recommended product</Badge>
        <h3 className="mt-4 font-serif text-4xl font-semibold">{recommendation.title}</h3>
        <p className="mt-4 text-sm leading-7 text-muted-foreground">
          <strong className="text-foreground">Best for:</strong> {recommendation.bestFor}
        </p>
        <p className="mt-5 text-xl font-semibold italic">{recommendation.headline}</p>
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
      </section>

      <RecommendationDeck recommendation={recommendation} />
    </div>
  );
}

const recFromData = recommendation;

function RecommendationDeck({ recommendation }: { recommendation: typeof recFromData }) {
  return (
    <section className="rounded-md border border-border bg-panel p-5">
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
  children,
}: {
  itemLabel: string;
  selected: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-4 rounded-md border border-border bg-panel p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-xl font-semibold">{itemLabel}</h3>
        <div className="flex items-center gap-3">
          <Switch checked={selected} />
          <Label>Use in summary</Label>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">{children}</div>
      <Button className="w-fit"><Save />Save</Button>
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
          <li key={item} className="flex gap-2 rounded-md bg-muted px-3 py-2 text-sm">
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

function SummaryBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="rounded-md border border-border bg-panel p-5">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">{children}</div>
    </article>
  );
}

function StatusPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-4 py-3">
      <p className="text-xs font-semibold uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function InfoMini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted px-3 py-2">
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
