import { apiClient } from '@/lib/api-client'
import {
  ResearchProject,
  MentoringSuggestion,
  ChatMessage,
  Experiment,
  SynthesisResult,
  BrAPIProgram,
  Paper,
  LiteratureStats,
  Chapter,
  WritingStats,
  CommitteeMember,
  Meeting,
  FeedbackItem,
  CollaborationStats,
  Proposal
} from '@/types/devguru'

// ============================================
// API FUNCTIONS
// ============================================

export async function fetchProjects(): Promise<{ projects: ResearchProject[], total: number }> {
  return apiClient.get('/api/v2/devguru/projects')
}

export async function fetchProject(id: string): Promise<ResearchProject> {
  return apiClient.get(`/api/v2/devguru/projects/${id}`)
}

export async function createProject(data: Partial<ResearchProject>): Promise<{ project: ResearchProject }> {
  return apiClient.post('/api/v2/devguru/projects', data)
}

export async function fetchSuggestions(projectId: string): Promise<{ suggestions: MentoringSuggestion[] }> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/suggestions`)
}

export async function sendChatMessage(
  message: string,
  projectId?: string,
  history?: ChatMessage[]
): Promise<{ message: string, provider: string, sources?: Array<{ doc_type: string, title: string, content: string }>, reasoning?: string }> {
  return apiClient.post('/api/v2/devguru/chat', {
    message,
    project_id: projectId,
    conversation_history: history?.slice(-10).map(m => ({ role: m.role, content: m.content }))
  })
}

export async function fetchExperiments(projectId: string): Promise<{ experiments: Experiment[], total: number }> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/experiments`)
}

export async function fetchSynthesis(projectId: string): Promise<SynthesisResult> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/synthesis`)
}

export async function fetchPrograms(): Promise<{ programs: BrAPIProgram[], total: number }> {
  return apiClient.get('/api/v2/programs')
}

export async function linkProgram(projectId: string, programId: number): Promise<{ project: ResearchProject }> {
  return apiClient.post(`/api/v2/devguru/projects/${projectId}/link-program`, { program_id: programId })
}

// Phase 3: Literature API
export async function fetchPapers(projectId: string): Promise<{ papers: Paper[], total: number }> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/papers`)
}

export async function addPaper(projectId: string, data: Partial<Paper>): Promise<{ paper: Paper }> {
  return apiClient.post(`/api/v2/devguru/projects/${projectId}/papers`, data)
}

export async function updatePaper(paperId: string, data: Partial<Paper>): Promise<{ paper: Paper }> {
  return apiClient.put(`/api/v2/devguru/papers/${paperId}`, data)
}

export async function deletePaper(paperId: string): Promise<void> {
  return apiClient.delete(`/api/v2/devguru/papers/${paperId}`)
}

export async function fetchLiteratureStats(projectId: string): Promise<LiteratureStats> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/literature-stats`)
}

// Phase 4: Writing API
export async function fetchChapters(projectId: string): Promise<{ chapters: Chapter[], total: number }> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/chapters`)
}

export async function generateDefaultChapters(projectId: string): Promise<{ chapters: Chapter[] }> {
  return apiClient.post(`/api/v2/devguru/projects/${projectId}/chapters/generate-defaults`, {})
}

export async function logWritingSession(
  chapterId: string,
  data: { words_written: number, duration_minutes?: number, notes?: string }
): Promise<object> {
  return apiClient.post(`/api/v2/devguru/chapters/${chapterId}/sessions`, data)
}

export async function fetchWritingStats(projectId: string): Promise<WritingStats> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/writing-stats`)
}

// Phase 5: Collaboration API
export async function fetchCommittee(projectId: string): Promise<{ members: CommitteeMember[], total: number }> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/committee`)
}

export async function addCommitteeMember(projectId: string, data: Partial<CommitteeMember>): Promise<{ member: CommitteeMember }> {
  return apiClient.post(`/api/v2/devguru/projects/${projectId}/committee`, data)
}

export async function fetchMeetings(projectId: string): Promise<{ meetings: Meeting[], total: number }> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/meetings`)
}

export async function scheduleMeeting(projectId: string, data: Partial<Meeting>): Promise<{ meeting: Meeting }> {
  return apiClient.post(`/api/v2/devguru/projects/${projectId}/meetings`, data)
}

export async function fetchFeedback(projectId: string): Promise<{ feedback: FeedbackItem[], total: number }> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/feedback`)
}

export async function fetchCollaborationStats(projectId: string): Promise<CollaborationStats> {
  return apiClient.get(`/api/v2/devguru/projects/${projectId}/collaboration-stats`)
}

// Phase 6: Proposals API
export async function fetchProposals(): Promise<Proposal[]> {
  return apiClient.get('/api/v2/proposals?status=draft')
}

export async function reviewProposal(id: number, approved: boolean, notes?: string): Promise<Proposal> {
  return apiClient.post(`/api/v2/proposals/${id}/review`, { approved, notes })
}
