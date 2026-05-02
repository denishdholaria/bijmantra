import type { OuterRimsPhaseId, Workstream } from '../models'

export function getExecutionStatusByPhase(workstreams: Workstream[]) {
  const phases: OuterRimsPhaseId[] = ['explore', 'seek', 'go', 'transcend']

  return phases.map((phaseId) => {
    const items = workstreams.filter((workstream) => workstream.phaseId === phaseId)
    return {
      phaseId,
      inProgress: items.filter((workstream) => workstream.status === 'in-progress').length,
      pending: items.filter((workstream) => workstream.status === 'pending').length,
      completed: items.filter((workstream) => workstream.status === 'completed').length,
    }
  })
}