import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Filter, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OUTER_RIMS_DATASET } from "@/features/outer-rims/data";
import {
  CommandBrief,
  GovernanceProtocolPanel,
  InitiativeDetailPanel,
  InitiativeMatrix,
  KpiTrajectoryGrid,
  MilestoneTimeline,
  PhaseCommandDeck,
  ProgramOpsBoard,
  RiskHeatmap,
  ScenarioLab,
  WorkstreamDependencyMatrix,
  NextTaskQueue,
  WeeklyExecutionPlan,
  WorkstreamPriorityPanel,
  BlockerResolutionBoard,
  CriticalPathBoard,
  PendingWorkstreamBoard,
  WorkstreamCompletionBanner,
  PublicAccountabilityDashboard,
} from "@/features/outer-rims/components";
import { Initiative, OuterRimsPhaseId } from "@/features/outer-rims/models";
import { getExecutionStatusByPhase } from "@/features/outer-rims/utils/analytics";

function pickDefaultInitiative(
  items: Initiative[],
  phase: OuterRimsPhaseId | "all",
): Initiative {
  if (phase === "all") return items[0];
  return items.find((item) => item.phaseId === phase) ?? items[0];
}

export function OuterRimsInitiative() {
  const [selectedPhase, setSelectedPhase] = useState<OuterRimsPhaseId | "all">(
    "all",
  );
  const [search, setSearch] = useState("");
  const [selectedInitiativeId, setSelectedInitiativeId] = useState(
    OUTER_RIMS_DATASET.initiatives[0].id,
  );

  const filteredInitiatives = useMemo(() => {
    const byPhase =
      selectedPhase === "all"
        ? OUTER_RIMS_DATASET.initiatives
        : OUTER_RIMS_DATASET.initiatives.filter(
            (initiative) => initiative.phaseId === selectedPhase,
          );

    const query = search.trim().toLowerCase();
    if (!query) return byPhase;

    return byPhase.filter((initiative) => {
      const text = [
        initiative.title,
        initiative.mission,
        initiative.modelLeap,
        initiative.narrative,
        ...initiative.northStarSignals,
      ]
        .join(" ")
        .toLowerCase();

      return text.includes(query);
    });
  }, [selectedPhase, search]);

  const selectedInitiative =
    filteredInitiatives.find(
      (initiative) => initiative.id === selectedInitiativeId,
    ) ??
    pickDefaultInitiative(
      filteredInitiatives.length > 0
        ? filteredInitiatives
        : OUTER_RIMS_DATASET.initiatives,
      selectedPhase,
    );

  const activeInitiativeCount =
    selectedPhase === "all"
      ? OUTER_RIMS_DATASET.initiatives.length
      : OUTER_RIMS_DATASET.initiatives.filter(
          (initiative) => initiative.phaseId === selectedPhase,
        ).length;

  const executionByPhase = getExecutionStatusByPhase(
    OUTER_RIMS_DATASET.workstreams,
  );
  const totalPending = executionByPhase.reduce(
    (sum, phase) => sum + phase.pending,
    0,
  );

  return (
    <div className="min-h-screen bg-background text-foreground pb-16">
      <section className="max-w-7xl mx-auto px-4 pt-8">
        <div className="flex items-center justify-between mb-6 gap-3 flex-wrap">
          <Link to="/vision">
            <Button
              variant="ghost"
              className="text-muted-foreground hover:text-foreground hover:bg-accent"
            >
              <ArrowLeft className="h-4 w-4 mr-2" /> Back to Vision
            </Button>
          </Link>
          <Link to="/vision">
            <Button variant="outline" className="border-border text-foreground">
              Strategic Narrative
            </Button>
          </Link>
        </div>

        <Card className="border-border bg-card">
          <CardContent className="p-8 md:p-12">
            <div className="flex flex-wrap gap-2 mb-4">
              <Badge className="bg-primary/10 text-primary border-primary/30">
                Outer Rims Initiative
              </Badge>
              <Badge
                variant="outline"
                className="border-border text-foreground"
              >
                Mission Command Center
              </Badge>
              <Badge
                variant="outline"
                className="border-border text-foreground"
              >
                Scenario Lab Enabled
              </Badge>
            </div>

            <h1 className="text-4xl md:text-5xl font-black leading-tight mb-4">
              Outer Rims Program Command Center
            </h1>
            <p className="text-muted-foreground max-w-4xl text-lg">
              This interface operationalizes the Explore → Seek → Go → Transcend
              journey into a live planning, governance, and execution command
              surface for product, science, operations, and platform teams.
            </p>

            <div className="grid md:grid-cols-4 gap-3 mt-6">
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">Initiatives</p>
                <p className="text-2xl font-bold">{activeInitiativeCount}</p>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">Workstreams</p>
                <p className="text-2xl font-bold">
                  {OUTER_RIMS_DATASET.workstreams.length}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">Milestones</p>
                <p className="text-2xl font-bold">
                  {OUTER_RIMS_DATASET.milestones.length}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">Last Updated</p>
                <p className="text-lg font-semibold">
                  {new Date(OUTER_RIMS_DATASET.updatedAt).toLocaleDateString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card mt-4">
          <CardContent className="p-4">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
              <p className="text-sm font-semibold text-foreground">
                Execution Rollout Status
              </p>
              <Badge
                variant="outline"
                className="border-border text-foreground"
              >
                Pending Areas: {totalPending}
              </Badge>
            </div>
            <div className="grid md:grid-cols-4 gap-2">
              {executionByPhase.map((phase) => (
                <div
                  key={phase.phaseId}
                  className="rounded-md border border-border bg-muted/30 p-2 text-xs"
                >
                  <p className="font-semibold capitalize text-foreground">
                    {phase.phaseId}
                  </p>
                  <p className="text-muted-foreground">
                    In Progress: {phase.inProgress}
                  </p>
                  <p className="text-muted-foreground">
                    Pending: {phase.pending}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="max-w-7xl mx-auto px-4 mt-6">
        <Tabs defaultValue="command" className="w-full">
          <TabsList className="grid w-full md:w-[540px] grid-cols-3 bg-muted border border-border">
            <TabsTrigger value="command">Command Surface</TabsTrigger>
            <TabsTrigger value="operations">Operations Lens</TabsTrigger>
            <TabsTrigger value="scenarios">Scenario Lab</TabsTrigger>
          </TabsList>

          <TabsContent value="command" className="mt-4">
            <div className="grid lg:grid-cols-12 gap-4">
              <div className="lg:col-span-4 space-y-4">
                <PhaseCommandDeck
                  phases={OUTER_RIMS_DATASET.phaseSummaries}
                  selectedPhase={selectedPhase}
                  onSelectPhase={(phase) => {
                    setSelectedPhase(phase);
                    const fallback = pickDefaultInitiative(
                      OUTER_RIMS_DATASET.initiatives,
                      phase,
                    );
                    setSelectedInitiativeId(fallback.id);
                  }}
                />

                <div className="rounded-xl border border-border bg-card p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Filter className="h-4 w-4 text-primary" />
                    <p className="text-sm font-semibold">Initiative Filter</p>
                  </div>
                  <div className="relative">
                    <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      className="pl-9 bg-background border-border text-foreground"
                      placeholder="Search mission, model leap, signal..."
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    {filteredInitiatives.length} initiative(s) visible
                  </p>
                </div>

                <CommandBrief />
              </div>

              <div className="lg:col-span-4 space-y-4">
                <InitiativeMatrix
                  initiatives={filteredInitiatives}
                  selectedPhase={selectedPhase}
                  selectedInitiativeId={selectedInitiative.id}
                  onSelectInitiative={setSelectedInitiativeId}
                />
              </div>

              <div className="lg:col-span-4 space-y-4">
                <InitiativeDetailPanel initiative={selectedInitiative} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="operations" className="mt-4">
            <div className="grid lg:grid-cols-12 gap-4">
              <div className="lg:col-span-5">
                <ProgramOpsBoard
                  selectedPhase={selectedPhase}
                  milestones={OUTER_RIMS_DATASET.milestones}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                  backlog={OUTER_RIMS_DATASET.backlog}
                  risks={OUTER_RIMS_DATASET.risks}
                />
              </div>
              <div className="lg:col-span-4 space-y-4">
                <KpiTrajectoryGrid
                  selectedPhase={selectedPhase}
                  kpis={OUTER_RIMS_DATASET.kpis}
                />
                <RiskHeatmap
                  risks={OUTER_RIMS_DATASET.risks}
                  phase={selectedPhase}
                />
              </div>
              <div className="lg:col-span-3 space-y-4">
                <WorkstreamCompletionBanner
                  selectedPhase={selectedPhase}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                />
                <PublicAccountabilityDashboard
                  kpis={OUTER_RIMS_DATASET.kpis}
                  risks={OUTER_RIMS_DATASET.risks}
                />
                <GovernanceProtocolPanel
                  rules={OUTER_RIMS_DATASET.governanceRules}
                />
                <NextTaskQueue
                  selectedPhase={selectedPhase}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                />
                <WeeklyExecutionPlan
                  selectedPhase={selectedPhase}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                  milestones={OUTER_RIMS_DATASET.milestones}
                />
                <WorkstreamPriorityPanel
                  selectedPhase={selectedPhase}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                />
                <BlockerResolutionBoard
                  selectedPhase={selectedPhase}
                  risks={OUTER_RIMS_DATASET.risks}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                />
                <CriticalPathBoard
                  selectedPhase={selectedPhase}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                  milestones={OUTER_RIMS_DATASET.milestones}
                />
                <PendingWorkstreamBoard
                  selectedPhase={selectedPhase}
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="scenarios" className="mt-4">
            <div className="grid lg:grid-cols-12 gap-4">
              <div className="lg:col-span-5">
                <ScenarioLab
                  phase={selectedPhase}
                  kpis={OUTER_RIMS_DATASET.kpis}
                />
              </div>
              <div className="lg:col-span-4">
                <MilestoneTimeline
                  milestones={OUTER_RIMS_DATASET.milestones}
                  phase={selectedPhase}
                />
              </div>
              <div className="lg:col-span-3">
                <WorkstreamDependencyMatrix
                  workstreams={OUTER_RIMS_DATASET.workstreams}
                  milestones={OUTER_RIMS_DATASET.milestones}
                  phase={selectedPhase}
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
