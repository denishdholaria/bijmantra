export type ReevuAgentMode = 'auto' | 'research' | 'compare' | 'validate'

export interface ReevuAttachmentSummary {
  id: string
  name: string
  size: number
  mime_type: string
  preview?: string
  preview_truncated?: boolean
}
