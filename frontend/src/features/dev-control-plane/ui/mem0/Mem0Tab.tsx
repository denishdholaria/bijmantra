import { BrainCircuit } from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TabsContent } from '@/components/ui/tabs'
import { Mem0DiagnosticsCard } from './Mem0DiagnosticsCard'
import { Mem0LearningCaptureCard } from './Mem0LearningCaptureCard'
import { Mem0MemoryWorkbench } from './Mem0MemoryWorkbench'
import { Mem0MissionCaptureCard } from './Mem0MissionCaptureCard'
import { Mem0SessionTrailCard } from './Mem0SessionTrailCard'
import { useMem0TabController } from './useMem0TabController'

export function Mem0Tab() {
  const {
    statusState,
    statusRecord,
    statusError,
    statusLastCheckedAt,
    healthState,
    healthRecord,
    healthError,
    userId,
    setUserId,
    appId,
    setAppId,
    runId,
    setRunId,
    category,
    setCategory,
    memoryText,
    setMemoryText,
    searchQuery,
    setSearchQuery,
    addState,
    addError,
    lastAddResult,
    searchState,
    searchError,
    lastSearchResult,
    learningState,
    learningRecord,
    learningError,
    captureState,
    captureError,
    capturingLearningId,
    lastCaptureResult,
    missionState,
    missionRecord,
    missionError,
    captureMissionState,
    captureMissionError,
    capturingMissionId,
    lastMissionCaptureResult,
    refreshDiagnostics,
    refreshLearnings,
    refreshMissions,
    handleAddMemory,
    handleSearch,
    handleCaptureLearning,
    handleCaptureMission,
    activityTrail,
    filteredActivityTrail,
    activityFilter,
    setActivityFilter,
    clearActivityTrail,
    copyActivitySummary,
    copyVisibleActivitySummaries,
  } = useMem0TabController()

  return (
    <TabsContent value="mem0" className="space-y-4">
      <Mem0DiagnosticsCard
        statusState={statusState}
        statusRecord={statusRecord}
        statusError={statusError}
        statusLastCheckedAt={statusLastCheckedAt}
        healthState={healthState}
        healthRecord={healthRecord}
        healthError={healthError}
        onRefreshDiagnostics={refreshDiagnostics}
      />

      <Mem0MemoryWorkbench
        userId={userId}
        appId={appId}
        runId={runId}
        category={category}
        memoryText={memoryText}
        searchQuery={searchQuery}
        addState={addState}
        addError={addError}
        lastAddResult={lastAddResult}
        searchState={searchState}
        searchError={searchError}
        lastSearchResult={lastSearchResult}
        onUserIdChange={setUserId}
        onAppIdChange={setAppId}
        onRunIdChange={setRunId}
        onCategoryChange={setCategory}
        onMemoryTextChange={setMemoryText}
        onSearchQueryChange={setSearchQuery}
        onAddMemory={handleAddMemory}
        onSearchMemory={handleSearch}
      />

      <Mem0LearningCaptureCard
        learningState={learningState}
        learningRecord={learningRecord}
        learningError={learningError}
        captureState={captureState}
        captureError={captureError}
        capturingLearningId={capturingLearningId}
        lastCaptureResult={lastCaptureResult}
        onRefreshLearnings={refreshLearnings}
        onCaptureLearning={handleCaptureLearning}
      />

      <Mem0MissionCaptureCard
        missionState={missionState}
        missionRecord={missionRecord}
        missionError={missionError}
        captureMissionState={captureMissionState}
        captureMissionError={captureMissionError}
        capturingMissionId={capturingMissionId}
        lastMissionCaptureResult={lastMissionCaptureResult}
        onRefreshMissions={refreshMissions}
        onCaptureMission={handleCaptureMission}
      />

      <Mem0SessionTrailCard
        activityTrail={activityTrail}
        filteredActivityTrail={filteredActivityTrail}
        activityFilter={activityFilter}
        onSetActivityFilter={setActivityFilter}
        onCopyVisibleActivitySummaries={copyVisibleActivitySummaries}
        onClearActivityTrail={clearActivityTrail}
        onCopyActivitySummary={copyActivitySummary}
      />

      <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4" />
            Boundary
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Mem0 here is developer cloud memory for short project recall. It is not REEVU, not app scientific authority, and not a replacement for canonical board, queue, mission, or repo evidence surfaces.
        </CardContent>
      </Card>
    </TabsContent>
  )
}