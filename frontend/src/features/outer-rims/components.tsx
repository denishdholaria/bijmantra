import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import type {
  GovernanceRule,
  Initiative,
  Kpi,
  Milestone,
  OuterRimsPhaseId,
  PhaseSummary,
  Risk,
  Workstream,
  BacklogItem,
} from './models'

type PhaseSelection = OuterRimsPhaseId | 'all'

function matchesPhase<T extends { phaseId: OuterRimsPhaseId }>(items: T[], phase: PhaseSelection) {
  return phase === 'all' ? items : items.filter((item) => item.phaseId === phase)
}

function SimpleList({
  title,
  description,
  items,
}: {
  title: string
  description?: string
  items: Array<{ id: string; primary: string; secondary?: string; badge?: string }>
}) {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No items in this slice.</p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="rounded-lg border border-border bg-muted/20 p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-foreground">{item.primary}</p>
                {item.badge ? <Badge variant="outline">{item.badge}</Badge> : null}
              </div>
              {item.secondary ? <p className="mt-1 text-xs text-muted-foreground">{item.secondary}</p> : null}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}

export function CommandBrief() {
  return (
    <SimpleList
      title="Command Brief"
      description="Current operational framing for the initiative surface."
      items={[
        { id: 'brief-1', primary: 'Promote real domains into owned modules', secondary: 'Current emphasis: route ownership, registry truth, validation.' },
        { id: 'brief-2', primary: 'Keep planning and runtime truth separate', secondary: 'Roadmap surfaces should not masquerade as active product structure.' },
      ]}
    />
  )
}

export function GovernanceProtocolPanel({ rules }: { rules: GovernanceRule[] }) {
  return <SimpleList title="Governance Protocols" items={rules.map((rule) => ({ id: rule.id, primary: rule.title, secondary: rule.description }))} />
}

export function InitiativeDetailPanel({ initiative }: { initiative: Initiative }) {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle>{initiative.title}</CardTitle>
        <CardDescription>{initiative.modelLeap}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{initiative.mission}</p>
        <p className="text-sm text-foreground">{initiative.narrative}</p>
        <div className="flex flex-wrap gap-2">
          {initiative.northStarSignals.map((signal) => (
            <Badge key={signal} variant="outline">{signal}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function InitiativeMatrix({
  initiatives,
  selectedInitiativeId,
  onSelectInitiative,
}: {
  initiatives: Initiative[]
  selectedPhase: PhaseSelection
  selectedInitiativeId: string
  onSelectInitiative: (initiativeId: string) => void
}) {
  return (
    <SimpleList
      title="Initiative Matrix"
      description="Select an initiative to inspect mission-level detail."
      items={initiatives.map((initiative) => ({
        id: initiative.id,
        primary: initiative.title,
        secondary: initiative.mission,
        badge: initiative.id === selectedInitiativeId ? 'Selected' : initiative.phaseId,
      }))}
    />
  )
}

export function KpiTrajectoryGrid({ selectedPhase, kpis }: { selectedPhase: PhaseSelection; kpis: Kpi[] }) {
  const visible = matchesPhase(kpis, selectedPhase)
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle>KPI Trajectory</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {visible.map((kpi) => {
          const progress = kpi.target === 0 ? 0 : Math.min(100, Math.round((kpi.current / kpi.target) * 100))
          return (
            <div key={kpi.id} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>{kpi.name}</span>
                <span className="text-muted-foreground">{kpi.current}{kpi.unit} / {kpi.target}{kpi.unit}</span>
              </div>
              <Progress value={progress} />
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

export function MilestoneTimeline({ milestones, phase }: { milestones: Milestone[]; phase: PhaseSelection }) {
  const visible = matchesPhase(milestones, phase)
  return <SimpleList title="Milestones" items={visible.map((milestone) => ({ id: milestone.id, primary: milestone.title, secondary: milestone.dueDate, badge: milestone.status }))} />
}

export function PhaseCommandDeck({
  phases,
  selectedPhase,
  onSelectPhase,
}: {
  phases: PhaseSummary[]
  selectedPhase: PhaseSelection
  onSelectPhase: (phase: PhaseSelection) => void
}) {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle>Phase Command Deck</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <button type="button" onClick={() => onSelectPhase('all')} className="w-full rounded-lg border border-border px-3 py-2 text-left text-sm">
          All phases
        </button>
        {phases.map((phase) => (
          <button key={phase.phaseId} type="button" onClick={() => onSelectPhase(phase.phaseId)} className="w-full rounded-lg border border-border px-3 py-2 text-left text-sm">
            <div className="flex items-center justify-between gap-3">
              <span>{phase.label}</span>
              <Badge variant={selectedPhase === phase.phaseId ? 'default' : 'outline'}>{phase.status}</Badge>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{phase.description}</p>
          </button>
        ))}
      </CardContent>
    </Card>
  )
}

export function ProgramOpsBoard({
  selectedPhase,
  milestones,
  workstreams,
  backlog,
  risks,
}: {
  selectedPhase: PhaseSelection
  milestones: Milestone[]
  workstreams: Workstream[]
  backlog: BacklogItem[]
  risks: Risk[]
}) {
  const visibleWorkstreams = matchesPhase(workstreams, selectedPhase)
  const visibleMilestones = matchesPhase(milestones, selectedPhase)
  const visibleBacklog = matchesPhase(backlog, selectedPhase)
  const visibleRisks = matchesPhase(risks, selectedPhase)
  return (
    <SimpleList
      title="Program Operations"
      description="Execution lane summary for the selected phase."
      items={[
        { id: 'ops-workstreams', primary: `${visibleWorkstreams.length} active workstreams`, secondary: 'Live execution lanes under this phase.' },
        { id: 'ops-milestones', primary: `${visibleMilestones.length} milestones`, secondary: 'Delivery markers aligned to the mission.' },
        { id: 'ops-backlog', primary: `${visibleBacklog.length} backlog items`, secondary: 'Queued or blocked work not yet in the lane.' },
        { id: 'ops-risks', primary: `${visibleRisks.length} tracked risks`, secondary: 'Visible blockers and mitigations.' },
      ]}
    />
  )
}

export function RiskHeatmap({ risks, phase }: { risks: Risk[]; phase: PhaseSelection }) {
  const visible = matchesPhase(risks, phase)
  return <SimpleList title="Risk Heatmap" items={visible.map((risk) => ({ id: risk.id, primary: risk.title, secondary: risk.mitigation, badge: risk.severity }))} />
}

export function ScenarioLab({ phase, kpis }: { phase: PhaseSelection; kpis: Kpi[] }) {
  const visible = matchesPhase(kpis, phase)
  return <SimpleList title="Scenario Lab" description="What-if analysis anchors around KPI pressure points." items={visible.map((kpi) => ({ id: kpi.id, primary: `${kpi.name} scenario`, secondary: `Target uplift needed: ${Math.max(kpi.target - kpi.current, 0)}${kpi.unit}` }))} />
}

export function WorkstreamDependencyMatrix({
  workstreams,
  milestones,
  phase,
}: {
  workstreams: Workstream[]
  milestones: Milestone[]
  phase: PhaseSelection
}) {
  const visibleWorkstreams = matchesPhase(workstreams, phase)
  const visibleMilestones = matchesPhase(milestones, phase)
  return <SimpleList title="Dependency Matrix" items={visibleWorkstreams.map((workstream, index) => ({ id: workstream.id, primary: workstream.title, secondary: `Depends on milestone: ${visibleMilestones[index % Math.max(visibleMilestones.length, 1)]?.title || 'none mapped'}` }))} />
}

export function NextTaskQueue({ selectedPhase, workstreams }: { selectedPhase: PhaseSelection; workstreams: Workstream[] }) {
  return <SimpleList title="Next Task Queue" items={matchesPhase(workstreams, selectedPhase).filter((item) => item.status !== 'completed').map((item) => ({ id: item.id, primary: item.title, secondary: item.owner, badge: item.priority }))} />
}

export function WeeklyExecutionPlan({ selectedPhase, workstreams, milestones }: { selectedPhase: PhaseSelection; workstreams: Workstream[]; milestones: Milestone[] }) {
  const visibleWorkstreams = matchesPhase(workstreams, selectedPhase)
  const visibleMilestones = matchesPhase(milestones, selectedPhase)
  return <SimpleList title="Weekly Execution Plan" items={visibleWorkstreams.map((item, index) => ({ id: item.id, primary: item.title, secondary: `Target milestone: ${visibleMilestones[index % Math.max(visibleMilestones.length, 1)]?.title || 'unassigned'}` }))} />
}

export function WorkstreamPriorityPanel({ selectedPhase, workstreams }: { selectedPhase: PhaseSelection; workstreams: Workstream[] }) {
  return <SimpleList title="Priority Panel" items={matchesPhase(workstreams, selectedPhase).map((item) => ({ id: item.id, primary: item.title, secondary: item.owner, badge: item.priority }))} />
}

export function BlockerResolutionBoard({ selectedPhase, risks, workstreams }: { selectedPhase: PhaseSelection; risks: Risk[]; workstreams: Workstream[] }) {
  const visibleRisks = matchesPhase(risks, selectedPhase)
  const visibleWorkstreams = matchesPhase(workstreams, selectedPhase)
  return <SimpleList title="Blocker Resolution" items={visibleRisks.map((risk, index) => ({ id: risk.id, primary: risk.title, secondary: `Impacts ${visibleWorkstreams[index % Math.max(visibleWorkstreams.length, 1)]?.title || 'shared lane'}` }))} />
}

export function CriticalPathBoard({ selectedPhase, workstreams, milestones }: { selectedPhase: PhaseSelection; workstreams: Workstream[]; milestones: Milestone[] }) {
  const visibleWorkstreams = matchesPhase(workstreams, selectedPhase)
  const visibleMilestones = matchesPhase(milestones, selectedPhase)
  return <SimpleList title="Critical Path" items={visibleWorkstreams.map((item, index) => ({ id: item.id, primary: item.title, secondary: `Milestone gate: ${visibleMilestones[index % Math.max(visibleMilestones.length, 1)]?.title || 'n/a'}` }))} />
}

export function PendingWorkstreamBoard({ selectedPhase, workstreams }: { selectedPhase: PhaseSelection; workstreams: Workstream[] }) {
  return <SimpleList title="Pending Workstreams" items={matchesPhase(workstreams, selectedPhase).filter((item) => item.status === 'pending').map((item) => ({ id: item.id, primary: item.title, secondary: item.owner }))} />
}

export function WorkstreamCompletionBanner({ selectedPhase, workstreams }: { selectedPhase: PhaseSelection; workstreams: Workstream[] }) {
  const visible = matchesPhase(workstreams, selectedPhase)
  const completed = visible.filter((item) => item.status === 'completed').length
  const progress = visible.length === 0 ? 0 : Math.round((completed / visible.length) * 100)
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle>Completion Banner</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{completed} of {visible.length} workstreams completed.</p>
        <Progress value={progress} />
      </CardContent>
    </Card>
  )
}

export function PublicAccountabilityDashboard({ kpis, risks }: { kpis: Kpi[]; risks: Risk[] }) {
  return <SimpleList title="Public Accountability" items={[
    { id: 'acc-kpis', primary: `${kpis.length} KPIs tracked`, secondary: 'Progress signals with explicit targets.' },
    { id: 'acc-risks', primary: `${risks.length} risks visible`, secondary: 'Blockers remain visible rather than hidden in execution lanes.' },
  ]} />
}