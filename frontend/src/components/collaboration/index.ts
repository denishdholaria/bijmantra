/**
 * Collaboration Components
 * Real-time collaboration features for Bijmantra
 * 
 * APEX FEATURE: First breeding platform with real-time collaboration
 */

export {
  RealtimePresenceProvider,
  PresenceAvatars,
  useRealtimePresence,
  getUserColor,
  getInitials
} from './RealtimePresence'

export type { User, Cursor, PresenceState } from './RealtimePresence'

export {
  CollaborativeForm,
  CollaborativeField,
  useCollaborative
} from './CollaborativeEditor'

export type { CollaboratorActivity } from './CollaborativeEditor'

export { TeamChat } from './TeamChat'
