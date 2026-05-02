// @ts-nocheck
/**
 * DevGuru (देवगुरु) - AI Research Mentor
 * 
 * Named after Brihaspati (बृहस्पति), the divine teacher of the gods.
 * A dedicated AI mentor for research students — PhD, Masters, and advanced undergraduates.
 * 
 * Core Principle: A mentor, not just an assistant.
 */

import { useState, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { CalendarDays } from 'lucide-react'

import { ChatMessage } from '@/types/devguru'
import {
  fetchProjects,
  fetchProject,
  fetchSuggestions,
  fetchExperiments,
  fetchSynthesis,
  fetchPrograms,
  fetchPapers,
  updatePaper,
  deletePaper,
  fetchLiteratureStats,
  fetchChapters,
  generateDefaultChapters,
  logWritingSession,
  fetchWritingStats,
  fetchCommittee,
  fetchMeetings,
  fetchFeedback,
  fetchCollaborationStats,
  fetchProposals,
  reviewProposal
} from '@/services/devguru'

import { ChatTab } from '@/components/devguru/ChatTab'
import { ExperimentsTab } from '@/components/devguru/ExperimentsTab'
import { SynthesisTab } from '@/components/devguru/SynthesisTab'
import { LiteratureTab } from '@/components/devguru/LiteratureTab'
import { WritingTab } from '@/components/devguru/WritingTab'
import { CommitteeTab } from '@/components/devguru/CommitteeTab'
import { ProposalsTab } from '@/components/devguru/ProposalsTab'
import { NewProjectModal } from '@/components/devguru/NewProjectModal'
import { LinkProgramModal } from '@/components/devguru/LinkProgramModal'
import { AddPaperModal } from '@/components/devguru/AddPaperModal'
import { AddMemberModal } from '@/components/devguru/AddMemberModal'
import { ScheduleMeetingModal } from '@/components/devguru/ScheduleMeetingModal'

// ============================================
// MAIN COMPONENT
// ============================================

export function DevGuru() {
  const queryClient = useQueryClient()
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null)
  const [showNewProject, setShowNewProject] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Namaste! 🙏 I am DevGuru, your research mentor. Select or create a project to begin our journey together.',
      timestamp: new Date()
    }
  ])
  const [chatInput, setChatInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'experiments' | 'synthesis' | 'literature' | 'writing' | 'committee' | 'proposals'>('chat')
  const [showLinkProgram, setShowLinkProgram] = useState(false)
  const [showAddPaper, setShowAddPaper] = useState(false)
  const [showAddMember, setShowAddMember] = useState(false)
  const [showScheduleMeeting, setShowScheduleMeeting] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch projects
  const { data: projectsData, isLoading: loadingProjects } = useQuery({
    queryKey: ['devguru-projects'],
    queryFn: fetchProjects
  })

  // Fetch active project details
  const { data: activeProject } = useQuery({
    queryKey: ['devguru-project', activeProjectId],
    queryFn: () => fetchProject(activeProjectId!),
    enabled: !!activeProjectId
  })

  // Fetch suggestions for active project
  const { data: suggestionsData } = useQuery({
    queryKey: ['devguru-suggestions', activeProjectId],
    queryFn: () => fetchSuggestions(activeProjectId!),
    enabled: !!activeProjectId
  })

  // Fetch experiments for active project
  const { data: experimentsData, isLoading: loadingExperiments } = useQuery({
    queryKey: ['devguru-experiments', activeProjectId],
    queryFn: () => fetchExperiments(activeProjectId!),
    enabled: !!activeProjectId
  })

  // Fetch synthesis for active project
  const { data: synthesisData, isLoading: loadingSynthesis, refetch: refetchSynthesis } = useQuery({
    queryKey: ['devguru-synthesis', activeProjectId],
    queryFn: () => fetchSynthesis(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'synthesis'
  })

  // Fetch available programs for linking
  const { data: programsData } = useQuery({
    queryKey: ['brapi-programs'],
    queryFn: fetchPrograms,
    enabled: showLinkProgram
  })

  // Phase 3: Literature queries
  const { data: papersData, isLoading: loadingPapers } = useQuery({
    queryKey: ['devguru-papers', activeProjectId],
    queryFn: () => fetchPapers(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'literature'
  })

  const { data: literatureStats } = useQuery({
    queryKey: ['devguru-literature-stats', activeProjectId],
    queryFn: () => fetchLiteratureStats(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'literature'
  })

  // Phase 4: Writing queries
  const { data: chaptersData, isLoading: loadingChapters } = useQuery({
    queryKey: ['devguru-chapters', activeProjectId],
    queryFn: () => fetchChapters(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'writing'
  })

  const { data: writingStats } = useQuery({
    queryKey: ['devguru-writing-stats', activeProjectId],
    queryFn: () => fetchWritingStats(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'writing'
  })

  // Phase 5: Collaboration queries
  const { data: committeeData, isLoading: loadingCommittee } = useQuery({
    queryKey: ['devguru-committee', activeProjectId],
    queryFn: () => fetchCommittee(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'committee'
  })

  const { data: meetingsData, isLoading: loadingMeetings } = useQuery({
    queryKey: ['devguru-meetings', activeProjectId],
    queryFn: () => fetchMeetings(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'committee'
  })

  const { data: feedbackData, isLoading: loadingFeedback } = useQuery({
    queryKey: ['devguru-feedback', activeProjectId],
    queryFn: () => fetchFeedback(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'committee'
  })

  const { data: collaborationStats } = useQuery({
    queryKey: ['devguru-collaboration-stats', activeProjectId],
    queryFn: () => fetchCollaborationStats(activeProjectId!),
    enabled: !!activeProjectId && activeTab === 'committee'
  })

  // Phase 6: Proposals query
  const { data: proposalsData, isLoading: loadingProposals, refetch: refetchProposals } = useQuery({
    queryKey: ['devguru-proposals'],
    queryFn: fetchProposals,
    enabled: activeTab === 'proposals'
  })

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const projects = projectsData?.projects || []


  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🎓</span>
            <div>
              <h1 className="text-xl font-bold">DevGuru</h1>
              <p className="text-sm opacity-80">Your AI Research Mentor</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-2 py-1 bg-purple-400/30 text-white text-xs font-medium rounded-full">
              🧪 Experimental
            </span>
            <button
              onClick={() => setShowNewProject(true)}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
            >
              + New Project
            </button>
          </div>
        </div>
      </div>

      {/* Experimental AI Notice */}
      <div className="bg-purple-50 dark:bg-purple-900/20 border-b border-purple-200 dark:border-purple-800 px-6 py-2">
        <p className="max-w-7xl mx-auto text-xs text-purple-800 dark:text-purple-200 text-center">
          🧪 <strong>Experimental Feature:</strong> AI mentoring is in early development. Always verify research analysis, methodology suggestions, and scientific conclusions independently with your supervisor.
        </p>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Projects & Timeline */}
          <div className="lg:col-span-1 space-y-6">
            {/* Project Selector */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">📚 Research Projects</h2>
              {loadingProjects ? (
                <div className="text-center py-4 text-gray-500">Loading...</div>
              ) : projects.length === 0 ? (
                <div className="text-center py-6">
                  <p className="text-gray-500 dark:text-gray-400 text-sm mb-3">No projects yet</p>
                  <button
                    onClick={() => setShowNewProject(true)}
                    className="text-purple-600 dark:text-purple-400 text-sm font-medium hover:underline"
                  >
                    Create your first project →
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {projects.map(project => (
                    <button
                      key={project.id}
                      onClick={() => setActiveProjectId(project.id)}
                      className={cn(
                        'w-full text-left p-3 rounded-lg border transition-all',
                        activeProjectId === project.id
                          ? 'bg-purple-50 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700'
                          : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'
                      )}
                    >
                      <p className="font-medium text-sm text-gray-900 dark:text-white truncate">{project.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">{project.current_phase}</span>
                        <span className="text-xs text-purple-600 dark:text-purple-400">{project.progress_percentage}%</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Timeline */}
            {activeProject && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
                <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2"><CalendarDays className="h-4 w-4" /> Milestone Timeline</h2>
                <div className="space-y-3">
                  {activeProject.milestones?.map((milestone, idx) => (
                    <div key={milestone.id} className="flex items-start gap-3">
                      <div className="flex flex-col items-center">
                        <div className={cn(
                          'w-3 h-3 rounded-full',
                          milestone.status === 'completed' ? 'bg-green-500' :
                          milestone.status === 'in_progress' ? 'bg-yellow-500' :
                          milestone.status === 'delayed' ? 'bg-red-500' : 'bg-gray-300'
                        )} />
                        {idx < activeProject.milestones.length - 1 && (
                          <div className="w-0.5 h-8 bg-gray-200 dark:bg-gray-600" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{milestone.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{milestone.phase}</p>
                      </div>
                      <span className={cn(
                        'text-[10px] px-2 py-0.5 rounded-full',
                        milestone.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        milestone.status === 'in_progress' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        milestone.status === 'delayed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                      )}>
                        {milestone.status.replace('_', ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {suggestionsData?.suggestions && suggestionsData.suggestions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
                <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">💡 Suggestions</h2>
                <div className="space-y-2">
                  {suggestionsData.suggestions.slice(0, 3).map((suggestion, idx) => (
                    <div key={idx} className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <p className="text-xs font-medium text-purple-800 dark:text-purple-300">{suggestion.title}</p>
                      <p className="text-[10px] text-purple-600 dark:text-purple-400 mt-0.5">{suggestion.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>


          {/* Right Column: Tabs (Chat / Experiments / Synthesis) */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 h-[calc(100vh-200px)] flex flex-col">
              {/* Tab Header */}
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex gap-1 overflow-x-auto">
                    {[
                      { id: 'chat', label: '💬 Chat' },
                      { id: 'experiments', label: '🧪 Experiments' },
                      { id: 'synthesis', label: '🔬 Synthesis' },
                      { id: 'literature', label: '📚 Literature' },
                      { id: 'writing', label: '✍️ Writing' },
                      { id: 'committee', label: '👥 Committee' },
                      { id: 'proposals', label: '📜 Proposals' },
                    ].map(tab => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as typeof activeTab)}
                        className={cn(
                          'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors whitespace-nowrap',
                          activeTab === tab.id
                            ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                        )}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    {activeProjectId && activeTab === 'experiments' && (
                      <button
                        onClick={() => setShowLinkProgram(true)}
                        className="px-3 py-1.5 text-xs font-medium text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/40"
                      >
                        + Link Program
                      </button>
                    )}
                    {activeProjectId && activeTab === 'literature' && (
                      <button
                        onClick={() => setShowAddPaper(true)}
                        className="px-3 py-1.5 text-xs font-medium text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/40"
                      >
                        + Add Paper
                      </button>
                    )}
                    {activeProjectId && activeTab === 'committee' && (
                      <>
                        <button
                          onClick={() => setShowAddMember(true)}
                          className="px-3 py-1.5 text-xs font-medium text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/40"
                        >
                          + Member
                        </button>
                        <button
                          onClick={() => setShowScheduleMeeting(true)}
                          className="px-3 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40"
                        >
                          + Meeting
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Tab Content */}
              {activeTab === 'chat' && (
                <ChatTab
                  activeProject={activeProject}
                  chatMessages={chatMessages}
                  setChatMessages={setChatMessages}
                  chatInput={chatInput}
                  setChatInput={setChatInput}
                  isSending={isSending}
                  setIsSending={setIsSending}
                  messagesEndRef={messagesEndRef}
                  activeProjectId={activeProjectId}
                />
              )}

              {activeTab === 'experiments' && (
                <ExperimentsTab
                  experiments={experimentsData?.experiments || []}
                  isLoading={loadingExperiments}
                  hasLinkedProgram={!!activeProject?.program_id}
                  onLinkProgram={() => setShowLinkProgram(true)}
                />
              )}

              {activeTab === 'synthesis' && (
                <SynthesisTab
                  synthesis={synthesisData}
                  isLoading={loadingSynthesis}
                  onRefresh={() => refetchSynthesis()}
                />
              )}

              {activeTab === 'literature' && (
                <LiteratureTab
                  papers={papersData?.papers || []}
                  stats={literatureStats}
                  isLoading={loadingPapers}
                  onUpdatePaper={async (paperId, data) => {
                    await updatePaper(paperId, data)
                    queryClient.invalidateQueries({ queryKey: ['devguru-papers', activeProjectId] })
                    queryClient.invalidateQueries({ queryKey: ['devguru-literature-stats', activeProjectId] })
                  }}
                  onDeletePaper={async (paperId) => {
                    await deletePaper(paperId)
                    queryClient.invalidateQueries({ queryKey: ['devguru-papers', activeProjectId] })
                    queryClient.invalidateQueries({ queryKey: ['devguru-literature-stats', activeProjectId] })
                  }}
                />
              )}

              {activeTab === 'writing' && (
                <WritingTab
                  chapters={chaptersData?.chapters || []}
                  stats={writingStats}
                  isLoading={loadingChapters}
                  projectId={activeProjectId}
                  onGenerateDefaults={async () => {
                    if (activeProjectId) {
                      await generateDefaultChapters(activeProjectId)
                      queryClient.invalidateQueries({ queryKey: ['devguru-chapters', activeProjectId] })
                    }
                  }}
                  onLogSession={async (chapterId, data) => {
                    await logWritingSession(chapterId, data)
                    queryClient.invalidateQueries({ queryKey: ['devguru-chapters', activeProjectId] })
                    queryClient.invalidateQueries({ queryKey: ['devguru-writing-stats', activeProjectId] })
                  }}
                />
              )}

              {activeTab === 'committee' && (
                <CommitteeTab
                  members={committeeData?.members || []}
                  meetings={meetingsData?.meetings || []}
                  feedback={feedbackData?.feedback || []}
                  stats={collaborationStats}
                  isLoading={loadingCommittee || loadingMeetings || loadingFeedback}
                />
              )}

              {activeTab === 'proposals' && (
                <ProposalsTab
                  proposals={proposalsData || []}
                  isLoading={loadingProposals}
                  onReview={async (id, approved, notes) => {
                    await reviewProposal(id, approved, notes)
                    refetchProposals()
                  }}
                />
              )}
            </div>
          </div>
        </div>
      </div>


      {/* New Project Modal */}
      {showNewProject && (
        <NewProjectModal
          onClose={() => setShowNewProject(false)}
          onCreated={(project) => {
            queryClient.invalidateQueries({ queryKey: ['devguru-projects'] })
            setActiveProjectId(project.id)
            setShowNewProject(false)
          }}
        />
      )}

      {/* Link Program Modal */}
      {showLinkProgram && activeProjectId && (
        <LinkProgramModal
          projectId={activeProjectId}
          programs={programsData?.programs || []}
          onClose={() => setShowLinkProgram(false)}
          onLinked={() => {
            queryClient.invalidateQueries({ queryKey: ['devguru-project', activeProjectId] })
            queryClient.invalidateQueries({ queryKey: ['devguru-experiments', activeProjectId] })
            setShowLinkProgram(false)
          }}
        />
      )}

      {/* Add Paper Modal */}
      {showAddPaper && activeProjectId && (
        <AddPaperModal
          projectId={activeProjectId}
          onClose={() => setShowAddPaper(false)}
          onAdded={() => {
            queryClient.invalidateQueries({ queryKey: ['devguru-papers', activeProjectId] })
            queryClient.invalidateQueries({ queryKey: ['devguru-literature-stats', activeProjectId] })
            setShowAddPaper(false)
          }}
        />
      )}

      {/* Add Committee Member Modal */}
      {showAddMember && activeProjectId && (
        <AddMemberModal
          projectId={activeProjectId}
          onClose={() => setShowAddMember(false)}
          onAdded={() => {
            queryClient.invalidateQueries({ queryKey: ['devguru-committee', activeProjectId] })
            queryClient.invalidateQueries({ queryKey: ['devguru-collaboration-stats', activeProjectId] })
            setShowAddMember(false)
          }}
        />
      )}

      {/* Schedule Meeting Modal */}
      {showScheduleMeeting && activeProjectId && (
        <ScheduleMeetingModal
          projectId={activeProjectId}
          onClose={() => setShowScheduleMeeting(false)}
          onScheduled={() => {
            queryClient.invalidateQueries({ queryKey: ['devguru-meetings', activeProjectId] })
            queryClient.invalidateQueries({ queryKey: ['devguru-collaboration-stats', activeProjectId] })
            setShowScheduleMeeting(false)
          }}
        />
      )}
    </div>
  )
}

export default DevGuru
