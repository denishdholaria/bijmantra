// ============================================
// TYPES
// ============================================

export interface ResearchProject {
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

export interface Milestone {
  id: string
  name: string
  phase: string
  status: 'not_started' | 'in_progress' | 'completed' | 'delayed'
  target_date: string
  completed_date?: string
  notes?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  reasoning?: string
  sources?: Array<{ doc_type: string, title: string, content: string }>
}

export interface MentoringSuggestion {
  type: string
  title: string
  description: string
  priority: string
}

export interface Experiment {
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

export interface SynthesisResult {
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

export interface BrAPIProgram {
  id: number
  program_db_id: string
  program_name: string
  objective: string
  trials_count: number
}

// Phase 3: Literature
export interface Paper {
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

export interface LiteratureStats {
  total_papers: number
  read: number
  reading: number
  unread: number
  read_percentage: number
}

// Phase 4: Writing
export interface Chapter {
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

export interface WritingStats {
  total_chapters: number
  completed_chapters: number
  total_target_words: number
  total_written_words: number
  overall_progress: number
  recent_sessions: object[]
}

// Phase 5: Collaboration
export interface CommitteeMember {
  id: string
  name: string
  email?: string
  role: string
  institution?: string
  expertise?: string
  is_primary: boolean
}

export interface Meeting {
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

export interface FeedbackItem {
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

export interface CollaborationStats {
  committee_size: number
  total_meetings: number
  upcoming_meetings: number
  completed_meetings: number
  total_feedback: number
  pending_feedback: number
  addressed_feedback: number
}

// Phase 6: Proposals (Scribe)
export interface Proposal {
  id: number
  title: string
  description: string
  action_type: string
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'executed' | 'failed'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  target_data: any
  ai_rationale: string
  confidence_score: number
  created_at: string
  reviewer_notes?: string
}
