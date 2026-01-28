/**
 * DevGuru (देवगुरु) - AI Research Mentor
 * 
 * Named after Brihaspati (बृहस्पति), the divine teacher of the gods.
 * A dedicated AI mentor for research students — PhD, Masters, and advanced undergraduates.
 * 
 * Core Principle: A mentor, not just an assistant.
 */

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api-client'

// ============================================
// TYPES
// ============================================

interface ResearchProject {
  id: string
  title: string
  student_name: string
  supervisor: string
  start_date: string
  expected_end_date: string
  research_area: string
  objectives: string[]
  current_phase: string
  progress_percentage: number
  milestones: Milestone[]
  created_at: string
  program_id?: number | null
}

interface Milestone {
  id: string
  name: string
  phase: string
  status: 'not_started' | 'in_progress' | 'completed' | 'delayed'
  target_date: string
  completed_date?: string
  notes?: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface MentoringSuggestion {
  type: string
  title: string
  description: string
  priority: string
}

interface Experiment {
  id: number
  trial_db_id: string
  trial_name: string
  trial_description: string
  trial_type: string
  start_date: string
  end_date: string
  active: boolean
  studies_count: number
  studies: Array<{
    id: number
    study_db_id: string
    study_name: string
    study_type: string
    active: boolean
  }>
}

interface SynthesisResult {
  context: {
    project: {
      id: string
      title: string
      research_area: string
      current_phase: string
      objectives: string[]
    }
    experiments: Experiment[]
    summary: {
      total_experiments: number
      active_experiments: number
      total_studies: number
      has_linked_program: boolean
    }
  }
  synthesis: {
    content: string
    provider: string
    model: string
  } | null
  message?: string
}

interface BrAPIProgram {
  id: number
  program_db_id: string
  program_name: string
  objective: string
  trials_count: number
}

// Phase 3: Literature
interface Paper {
  id: string
  title: string
  authors: string[]
  journal?: string
  year?: number
  doi?: string
  url?: string
  abstract?: string
  notes?: string
  tags: string[]
  relevance_score?: number
  read_status: 'unread' | 'reading' | 'read' | 'to_revisit'
  citation_key?: string
  created_at: string
}

interface LiteratureStats {
  total_papers: number
  read: number
  reading: number
  unread: number
  read_percentage: number
}

// Phase 4: Writing
interface Chapter {
  id: string
  chapter_number: number
  title: string
  chapter_type?: string
  target_word_count: number
  current_word_count: number
  status: 'not_started' | 'drafting' | 'revising' | 'complete'
  outline?: object[]
  target_date?: string
  notes?: string
}

interface WritingStats {
  total_chapters: number
  completed_chapters: number
  total_target_words: number
  total_written_words: number
  overall_progress: number
  recent_sessions: object[]
}

// Phase 5: Collaboration
interface CommitteeMember {
  id: string
  name: string
  email?: string
  role: string
  institution?: string
  expertise?: string
  is_primary: boolean
}

interface Meeting {
  id: string
  title: string
  meeting_type: string
  scheduled_date: string
  duration_minutes: number
  location?: string
  agenda?: string
  status: string
  notes?: string
}

interface FeedbackItem {
  id: string
  content: string
  feedback_type: string
  priority: string
  status: string
  response?: string
  from_member_id?: string
  chapter_id?: string
  created_at: string
}

interface CollaborationStats {
  committee_size: number
  total_meetings: number
  upcoming_meetings: number
  completed_meetings: number
  total_feedback: number
  pending_feedback: number
  addressed_feedback: number
}


// ============================================
// API FUNCTIONS
// ============================================

async function fetchProjects(): Promise<{ projects: ResearchProject[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch('/api/v2/devguru/projects', {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch projects')
  return response.json()
}

async function fetchProject(id: string): Promise<ResearchProject> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${id}`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch project')
  return response.json()
}

async function createProject(data: Partial<ResearchProject>): Promise<{ project: ResearchProject }> {
  const token = apiClient.getToken()
  const response = await fetch('/api/v2/devguru/projects', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to create project')
  return response.json()
}

async function fetchSuggestions(projectId: string): Promise<{ suggestions: MentoringSuggestion[] }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/suggestions`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch suggestions')
  return response.json()
}

async function sendChatMessage(message: string, projectId?: string, history?: ChatMessage[]): Promise<{ message: string, provider: string }> {
  const token = apiClient.getToken()
  const response = await fetch('/api/v2/devguru/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      message,
      project_id: projectId,
      conversation_history: history?.slice(-10).map(m => ({ role: m.role, content: m.content }))
    })
  })
  if (!response.ok) throw new Error('Failed to send message')
  return response.json()
}

async function fetchExperiments(projectId: string): Promise<{ experiments: Experiment[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/experiments`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch experiments')
  return response.json()
}

async function fetchSynthesis(projectId: string): Promise<SynthesisResult> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/synthesis`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch synthesis')
  return response.json()
}

async function fetchPrograms(): Promise<{ programs: BrAPIProgram[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch('/api/v2/programs', {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch programs')
  return response.json()
}

async function linkProgram(projectId: string, programId: number): Promise<{ project: ResearchProject }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/link-program`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ program_id: programId })
  })
  if (!response.ok) throw new Error('Failed to link program')
  return response.json()
}

// Phase 3: Literature API
async function fetchPapers(projectId: string): Promise<{ papers: Paper[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/papers`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch papers')
  return response.json()
}

async function addPaper(projectId: string, data: Partial<Paper>): Promise<{ paper: Paper }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/papers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to add paper')
  return response.json()
}

async function updatePaper(paperId: string, data: Partial<Paper>): Promise<{ paper: Paper }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/papers/${paperId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to update paper')
  return response.json()
}

async function deletePaper(paperId: string): Promise<void> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/papers/${paperId}`, {
    method: 'DELETE',
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to delete paper')
}

async function fetchLiteratureStats(projectId: string): Promise<LiteratureStats> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/literature-stats`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch literature stats')
  return response.json()
}

// Phase 4: Writing API
async function fetchChapters(projectId: string): Promise<{ chapters: Chapter[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/chapters`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch chapters')
  return response.json()
}

async function createChapter(projectId: string, data: Partial<Chapter>): Promise<{ chapter: Chapter }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/chapters`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to create chapter')
  return response.json()
}

async function generateDefaultChapters(projectId: string): Promise<{ chapters: Chapter[] }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/chapters/generate-defaults`, {
    method: 'POST',
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to generate chapters')
  return response.json()
}

async function logWritingSession(chapterId: string, data: { words_written: number, duration_minutes?: number, notes?: string }): Promise<object> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/chapters/${chapterId}/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to log session')
  return response.json()
}

async function fetchWritingStats(projectId: string): Promise<WritingStats> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/writing-stats`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch writing stats')
  return response.json()
}

// Phase 5: Collaboration API
async function fetchCommittee(projectId: string): Promise<{ members: CommitteeMember[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/committee`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch committee')
  return response.json()
}

async function addCommitteeMember(projectId: string, data: Partial<CommitteeMember>): Promise<{ member: CommitteeMember }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/committee`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to add member')
  return response.json()
}

async function fetchMeetings(projectId: string): Promise<{ meetings: Meeting[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/meetings`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch meetings')
  return response.json()
}

async function scheduleMeeting(projectId: string, data: Partial<Meeting>): Promise<{ meeting: Meeting }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/meetings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to schedule meeting')
  return response.json()
}

async function fetchFeedback(projectId: string): Promise<{ feedback: FeedbackItem[], total: number }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/feedback`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch feedback')
  return response.json()
}

async function addFeedback(projectId: string, data: Partial<FeedbackItem>): Promise<{ feedback: FeedbackItem }> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to add feedback')
  return response.json()
}

async function fetchCollaborationStats(projectId: string): Promise<CollaborationStats> {
  const token = apiClient.getToken()
  const response = await fetch(`/api/v2/devguru/projects/${projectId}/collaboration-stats`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  })
  if (!response.ok) throw new Error('Failed to fetch collaboration stats')
  return response.json()
}


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
  const [activeTab, setActiveTab] = useState<'chat' | 'experiments' | 'synthesis' | 'literature' | 'writing' | 'committee'>('chat')
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
                <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">📅 Milestone Timeline</h2>
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

// ============================================
// CHAT TAB COMPONENT
// ============================================

interface ChatTabProps {
  activeProject: ResearchProject | undefined
  chatMessages: ChatMessage[]
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  chatInput: string
  setChatInput: React.Dispatch<React.SetStateAction<string>>
  isSending: boolean
  setIsSending: React.Dispatch<React.SetStateAction<boolean>>
  messagesEndRef: React.RefObject<HTMLDivElement>
  activeProjectId: string | null
}

function ChatTab({ activeProject, chatMessages, setChatMessages, chatInput, setChatInput, isSending, setIsSending, messagesEndRef, activeProjectId }: ChatTabProps) {
  const handleSendMessage = async () => {
    if (!chatInput.trim() || isSending) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date()
    }

    setChatMessages(prev => [...prev, userMessage])
    const query = chatInput.trim()
    setChatInput('')
    setIsSending(true)

    try {
      const response = await sendChatMessage(query, activeProjectId || undefined, chatMessages)
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please ensure the backend is running and your AI provider is configured.',
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <>
      {/* Chat Header */}
      <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">🎓</span>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {activeProject ? `Context: ${activeProject.title}` : 'Select a project for personalized guidance'}
          </p>
        </div>
        <button
          onClick={() => setChatMessages([{
            id: Date.now().toString(),
            role: 'assistant',
            content: 'Conversation cleared. How can I help with your research today?',
            timestamp: new Date()
          }])}
          className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          Clear
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatMessages.map(message => (
          <div key={message.id} className={cn('flex', message.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div className={cn(
              'max-w-[80%] rounded-xl px-4 py-3',
              message.role === 'user'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
            )}>
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p className={cn(
                'text-[10px] mt-1',
                message.role === 'user' ? 'opacity-70' : 'text-gray-400 dark:text-gray-500'
              )}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        {isSending && (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-xs">DevGuru is thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {[
            { label: '📊 Timeline Check', action: 'How am I doing on my timeline?' },
            { label: '📝 Next Steps', action: 'What should I focus on next?' },
            { label: '📚 Literature Help', action: 'Help me with my literature review' },
            { label: '✍️ Writing Tips', action: 'Give me writing tips for my thesis' },
            { label: '🎯 Milestone Update', action: 'I want to update my milestone progress' },
          ].map(qa => (
            <button
              key={qa.label}
              onClick={() => setChatInput(qa.action)}
              className="flex-shrink-0 px-3 py-1.5 text-[10px] font-medium text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-full hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors"
            >
              {qa.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask DevGuru about your research..."
            className="flex-1 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={handleSendMessage}
            disabled={!chatInput.trim() || isSending}
            className={cn(
              'p-2.5 rounded-lg transition-all',
              chatInput.trim() && !isSending
                ? 'bg-purple-600 text-white hover:bg-purple-700'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
            )}
          >
            ➤
          </button>
        </div>
      </div>
    </>
  )
}

// ============================================
// EXPERIMENTS TAB COMPONENT
// ============================================

interface ExperimentsTabProps {
  experiments: Experiment[]
  isLoading: boolean
  hasLinkedProgram: boolean
  onLinkProgram: () => void
}

function ExperimentsTab({ experiments, isLoading, hasLinkedProgram, onLinkProgram }: ExperimentsTabProps) {
  const [expandedTrial, setExpandedTrial] = useState<number | null>(null)

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading experiments...</p>
        </div>
      </div>
    )
  }

  if (!hasLinkedProgram) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <span className="text-4xl mb-4 block">🔗</span>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Link a BrAPI Program</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Connect your research project to a BrAPI Program to track experiments (trials) and studies. 
            This enables DevGuru to synthesize insights across your experimental data.
          </p>
          <button
            onClick={onLinkProgram}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700"
          >
            Link Program
          </button>
        </div>
      </div>
    )
  }

  if (experiments.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <span className="text-4xl mb-4 block">🧪</span>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Experiments Yet</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Your linked program doesn't have any trials yet. Create trials in the Breeding module to see them here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="space-y-3">
        {experiments.map(exp => (
          <div key={exp.id} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandedTrial(expandedTrial === exp.id ? null : exp.id)}
              className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <div className="flex items-center gap-3">
                <span className={cn(
                  'w-2 h-2 rounded-full',
                  exp.active ? 'bg-green-500' : 'bg-gray-400'
                )} />
                <div className="text-left">
                  <p className="font-medium text-sm text-gray-900 dark:text-white">{exp.trial_name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{exp.trial_type || 'Trial'} • {exp.studies_count} studies</p>
                </div>
              </div>
              <span className="text-gray-400">{expandedTrial === exp.id ? '▼' : '▶'}</span>
            </button>
            
            {expandedTrial === exp.id && (
              <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                {exp.trial_description && (
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{exp.trial_description}</p>
                )}
                <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                  {exp.start_date && <span>Start: {exp.start_date}</span>}
                  {exp.end_date && <span>End: {exp.end_date}</span>}
                </div>
                
                {exp.studies.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Studies:</p>
                    {exp.studies.map(study => (
                      <div key={study.id} className="flex items-center gap-2 pl-4 py-1">
                        <span className={cn(
                          'w-1.5 h-1.5 rounded-full',
                          study.active ? 'bg-blue-500' : 'bg-gray-400'
                        )} />
                        <span className="text-sm text-gray-600 dark:text-gray-300">{study.study_name}</span>
                        <span className="text-xs text-gray-400">({study.study_type || 'Study'})</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 italic">No studies in this trial</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================
// SYNTHESIS TAB COMPONENT
// ============================================

interface SynthesisTabProps {
  synthesis: SynthesisResult | undefined
  isLoading: boolean
  onRefresh: () => void
}

function SynthesisTab({ synthesis, isLoading, onRefresh }: SynthesisTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Generating synthesis...</p>
        </div>
      </div>
    )
  }

  if (!synthesis) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <span className="text-4xl mb-4 block">🔬</span>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Research Synthesis</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Select a project to generate AI synthesis of your research progress.
          </p>
        </div>
      </div>
    )
  }

  const { context, synthesis: synthContent, message } = synthesis

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{context.summary.total_experiments}</p>
          <p className="text-xs text-purple-700 dark:text-purple-300">Experiments</p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{context.summary.active_experiments}</p>
          <p className="text-xs text-blue-700 dark:text-blue-300">Active</p>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{context.summary.total_studies}</p>
          <p className="text-xs text-green-700 dark:text-green-300">Studies</p>
        </div>
      </div>

      {/* Synthesis Content */}
      {synthContent ? (
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">AI Synthesis</h4>
            <button
              onClick={onRefresh}
              className="text-xs text-purple-600 dark:text-purple-400 hover:underline"
            >
              Refresh
            </button>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{synthContent.content}</p>
          </div>
          <p className="text-[10px] text-gray-400 mt-3">
            Generated by {synthContent.provider} ({synthContent.model})
          </p>
        </div>
      ) : (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
          <p className="text-sm text-yellow-700 dark:text-yellow-300">{message || 'No synthesis available'}</p>
        </div>
      )}

      {/* Objectives */}
      {context.project.objectives.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Research Objectives</h4>
          <ul className="space-y-1">
            {context.project.objectives.map((obj, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                <span className="text-purple-500">•</span>
                {obj}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ============================================
// LINK PROGRAM MODAL
// ============================================

interface LinkProgramModalProps {
  projectId: string
  programs: BrAPIProgram[]
  onClose: () => void
  onLinked: () => void
}

function LinkProgramModal({ projectId, programs, onClose, onLinked }: LinkProgramModalProps) {
  const [selectedProgram, setSelectedProgram] = useState<number | null>(null)
  const [isLinking, setIsLinking] = useState(false)

  const handleLink = async () => {
    if (!selectedProgram) return
    setIsLinking(true)
    try {
      await linkProgram(projectId, selectedProgram)
      onLinked()
    } catch (error) {
      console.error('Failed to link program:', error)
    } finally {
      setIsLinking(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">🔗 Link BrAPI Program</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">✕</button>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Select a breeding program to link with your research project. This will enable experiment tracking and AI synthesis.
          </p>
          
          {programs.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-gray-500 dark:text-gray-400 text-sm">No programs available</p>
              <p className="text-xs text-gray-400 mt-1">Create a program in the Breeding module first</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {programs.map(program => (
                <button
                  key={program.id}
                  onClick={() => setSelectedProgram(program.id)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    selectedProgram === program.id
                      ? 'bg-purple-50 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700'
                      : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                >
                  <p className="font-medium text-sm text-gray-900 dark:text-white">{program.program_name}</p>
                  {program.objective && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{program.objective}</p>
                  )}
                  <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">{program.trials_count || 0} trials</p>
                </button>
              ))}
            </div>
          )}
          
          <div className="flex justify-end gap-3 mt-6">
            <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
              Cancel
            </button>
            <button
              onClick={handleLink}
              disabled={!selectedProgram || isLinking}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLinking ? 'Linking...' : 'Link Program'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================
// NEW PROJECT MODAL
// ============================================

interface NewProjectModalProps {
  onClose: () => void
  onCreated: (project: ResearchProject) => void
}

function NewProjectModal({ onClose, onCreated }: NewProjectModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    student_name: '',
    supervisor: '',
    start_date: new Date().toISOString().split('T')[0],
    expected_end_date: '',
    research_area: '',
    objectives: ['']
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title || !formData.student_name) return

    setIsSubmitting(true)
    try {
      const result = await createProject({
        ...formData,
        objectives: formData.objectives.filter(o => o.trim())
      })
      onCreated(result.project)
    } catch (error) {
      console.error('Failed to create project:', error)
    } finally {
      setIsSubmitting(false)
    }
  }


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">🎓 New Research Project</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Project Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              placeholder="e.g., Genomic Selection for Drought Tolerance in Rice"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Your Name *</label>
              <input
                type="text"
                value={formData.student_name}
                onChange={(e) => setFormData(prev => ({ ...prev, student_name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Supervisor</label>
              <input
                type="text"
                value={formData.supervisor}
                onChange={(e) => setFormData(prev => ({ ...prev, supervisor: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Research Area</label>
            <input
              type="text"
              value={formData.research_area}
              onChange={(e) => setFormData(prev => ({ ...prev, research_area: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              placeholder="e.g., Plant Breeding, Genomics, Agronomy"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Expected End</label>
              <input
                type="date"
                value={formData.expected_end_date}
                onChange={(e) => setFormData(prev => ({ ...prev, expected_end_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !formData.title || !formData.student_name}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ============================================
// LITERATURE TAB COMPONENT
// ============================================

interface LiteratureTabProps {
  papers: Paper[]
  stats: LiteratureStats | undefined
  isLoading: boolean
  onUpdatePaper: (paperId: string, data: Partial<Paper>) => Promise<void>
  onDeletePaper: (paperId: string) => Promise<void>
}

function LiteratureTab({ papers, stats, isLoading, onUpdatePaper, onDeletePaper }: LiteratureTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading papers...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.total_papers}</p>
            <p className="text-xs text-blue-700">Total</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.read}</p>
            <p className="text-xs text-green-700">Read</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.reading}</p>
            <p className="text-xs text-yellow-700">Reading</p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-gray-600">{stats.unread}</p>
            <p className="text-xs text-gray-700">Unread</p>
          </div>
        </div>
      )}

      {/* Papers List */}
      {papers.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-4xl mb-4 block">📚</span>
          <p className="text-gray-500">No papers yet. Add your first paper!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {papers.map(paper => (
            <div key={paper.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white">{paper.title}</h4>
                  <p className="text-sm text-gray-500 mt-1">{paper.authors.join(', ')}</p>
                  {paper.journal && <p className="text-xs text-gray-400">{paper.journal} {paper.year && `(${paper.year})`}</p>}
                </div>
                <select
                  value={paper.read_status}
                  onChange={(e) => onUpdatePaper(paper.id, { read_status: e.target.value as Paper['read_status'] })}
                  className="text-xs border rounded px-2 py-1"
                >
                  <option value="unread">Unread</option>
                  <option value="reading">Reading</option>
                  <option value="read">Read</option>
                  <option value="to_revisit">To Revisit</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================
// WRITING TAB COMPONENT
// ============================================

interface WritingTabProps {
  chapters: Chapter[]
  stats: WritingStats | undefined
  isLoading: boolean
  projectId: string | null
  onGenerateDefaults: () => Promise<void>
  onLogSession: (chapterId: string, data: { words_written: number; duration_minutes?: number; notes?: string }) => Promise<void>
}

function WritingTab({ chapters, stats, isLoading, onGenerateDefaults }: WritingTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading chapters...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-purple-600">{stats.overall_progress}%</p>
            <p className="text-xs text-purple-700">Progress</p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.total_written_words.toLocaleString()}</p>
            <p className="text-xs text-blue-700">Words Written</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.completed_chapters}/{stats.total_chapters}</p>
            <p className="text-xs text-green-700">Chapters Done</p>
          </div>
        </div>
      )}

      {/* Chapters */}
      {chapters.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-4xl mb-4 block">✍️</span>
          <p className="text-gray-500 mb-4">No chapters yet.</p>
          <button
            onClick={onGenerateDefaults}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm"
          >
            Generate Default Chapters
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {chapters.map(chapter => (
            <div key={chapter.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    Ch. {chapter.chapter_number}: {chapter.title}
                  </h4>
                  <p className="text-xs text-gray-500">{chapter.chapter_type}</p>
                </div>
                <span className={cn(
                  'text-xs px-2 py-1 rounded',
                  chapter.status === 'complete' ? 'bg-green-100 text-green-700' :
                  chapter.status === 'revising' ? 'bg-blue-100 text-blue-700' :
                  chapter.status === 'drafting' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                )}>
                  {chapter.status}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (chapter.current_word_count / chapter.target_word_count) * 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {chapter.current_word_count.toLocaleString()} / {chapter.target_word_count.toLocaleString()} words
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================
// COMMITTEE TAB COMPONENT
// ============================================

interface CommitteeTabProps {
  members: CommitteeMember[]
  meetings: Meeting[]
  feedback: FeedbackItem[]
  stats: CollaborationStats | undefined
  isLoading: boolean
}

function CommitteeTab({ members, meetings, stats, isLoading }: CommitteeTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading committee data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-purple-600">{stats.committee_size}</p>
            <p className="text-xs text-purple-700">Members</p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.upcoming_meetings}</p>
            <p className="text-xs text-blue-700">Upcoming</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.completed_meetings}</p>
            <p className="text-xs text-green-700">Completed</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.pending_feedback}</p>
            <p className="text-xs text-yellow-700">Pending</p>
          </div>
        </div>
      )}

      {/* Members */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Committee Members</h4>
        {members.length === 0 ? (
          <p className="text-sm text-gray-500">No committee members yet.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {members.map(member => (
              <div key={member.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                <p className="font-medium text-gray-900 dark:text-white">{member.name}</p>
                <p className="text-xs text-gray-500">{member.role}</p>
                {member.institution && <p className="text-xs text-gray-400">{member.institution}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Meetings */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Meetings</h4>
        {meetings.length === 0 ? (
          <p className="text-sm text-gray-500">No meetings scheduled.</p>
        ) : (
          <div className="space-y-2">
            {meetings.slice(0, 5).map(meeting => (
              <div key={meeting.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                <div className="flex justify-between">
                  <p className="font-medium text-gray-900 dark:text-white">{meeting.title}</p>
                  <span className={cn(
                    'text-xs px-2 py-1 rounded',
                    meeting.status === 'completed' ? 'bg-green-100 text-green-700' :
                    meeting.status === 'scheduled' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  )}>
                    {meeting.status}
                  </span>
                </div>
                <p className="text-xs text-gray-500">{new Date(meeting.scheduled_date).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================
// ADD PAPER MODAL
// ============================================

interface AddPaperModalProps {
  projectId: string
  onClose: () => void
  onAdded: () => void
}

function AddPaperModal({ projectId, onClose, onAdded }: AddPaperModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    authors: '',
    journal: '',
    year: '',
    doi: '',
    notes: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title) return
    setIsSubmitting(true)
    try {
      await addPaper(projectId, {
        title: formData.title,
        authors: formData.authors.split(',').map((a: string) => a.trim()).filter(Boolean),
        journal: formData.journal || undefined,
        year: formData.year ? parseInt(formData.year) : undefined,
        doi: formData.doi || undefined,
        notes: formData.notes || undefined,
        tags: [],
        read_status: 'unread'
      })
      onAdded()
    } catch (error) {
      console.error('Failed to add paper:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">📚 Add Paper</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Authors (comma-separated)</label>
            <input
              type="text"
              value={formData.authors}
              onChange={(e) => setFormData(prev => ({ ...prev, authors: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Smith J, Doe A"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Journal</label>
              <input
                type="text"
                value={formData.journal}
                onChange={(e) => setFormData(prev => ({ ...prev, journal: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Year</label>
              <input
                type="number"
                value={formData.year}
                onChange={(e) => setFormData(prev => ({ ...prev, year: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
            <button
              type="submit"
              disabled={isSubmitting || !formData.title}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Adding...' : 'Add Paper'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ============================================
// ADD MEMBER MODAL
// ============================================

interface AddMemberModalProps {
  projectId: string
  onClose: () => void
  onAdded: () => void
}

function AddMemberModal({ projectId, onClose, onAdded }: AddMemberModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: 'Committee Member',
    institution: '',
    expertise: '',
    is_primary: false
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name) return
    setIsSubmitting(true)
    try {
      await addCommitteeMember(projectId, formData)
      onAdded()
    } catch (error) {
      console.error('Failed to add member:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">👤 Add Committee Member</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option>Supervisor</option>
              <option>Co-Supervisor</option>
              <option>Committee Member</option>
              <option>External Examiner</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Institution</label>
            <input
              type="text"
              value={formData.institution}
              onChange={(e) => setFormData(prev => ({ ...prev, institution: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
            <button
              type="submit"
              disabled={isSubmitting || !formData.name}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Adding...' : 'Add Member'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ============================================
// SCHEDULE MEETING MODAL
// ============================================

interface ScheduleMeetingModalProps {
  projectId: string
  onClose: () => void
  onScheduled: () => void
}

function ScheduleMeetingModal({ projectId, onClose, onScheduled }: ScheduleMeetingModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    meeting_type: 'Progress Review',
    scheduled_date: '',
    duration_minutes: 60,
    location: '',
    agenda: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title || !formData.scheduled_date) return
    setIsSubmitting(true)
    try {
      await scheduleMeeting(projectId, {
        ...formData,
        status: 'scheduled'
      })
      onScheduled()
    } catch (error) {
      console.error('Failed to schedule meeting:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">📅 Schedule Meeting</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="e.g., Quarterly Progress Review"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Meeting Type</label>
            <select
              value={formData.meeting_type}
              onChange={(e) => setFormData(prev => ({ ...prev, meeting_type: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option>Progress Review</option>
              <option>Proposal Defense</option>
              <option>Comprehensive Exam</option>
              <option>Final Defense</option>
              <option>Committee Meeting</option>
              <option>One-on-One</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Date & Time *</label>
              <input
                type="datetime-local"
                value={formData.scheduled_date}
                onChange={(e) => setFormData(prev => ({ ...prev, scheduled_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duration (min)</label>
              <input
                type="number"
                value={formData.duration_minutes}
                onChange={(e) => setFormData(prev => ({ ...prev, duration_minutes: parseInt(e.target.value) || 60 }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                min="15"
                step="15"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="e.g., Room 301 or Zoom link"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Agenda</label>
            <textarea
              value={formData.agenda}
              onChange={(e) => setFormData(prev => ({ ...prev, agenda: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              rows={3}
              placeholder="Meeting agenda items..."
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
            <button
              type="submit"
              disabled={isSubmitting || !formData.title || !formData.scheduled_date}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Scheduling...' : 'Schedule Meeting'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default DevGuru
