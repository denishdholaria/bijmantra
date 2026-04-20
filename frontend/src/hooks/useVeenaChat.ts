import {
  useReevuChat,
  type ReevuMessage,
  type ReevuSource,
} from './useReevuChat'

/**
 * @deprecated Use `useReevuChat()` from `@/hooks/useReevuChat`.
 */
export const useVeenaChat = useReevuChat
export type VeenaMessage = ReevuMessage
export type VeenaSource = ReevuSource

// Compatibility re-exports for mixed migration imports.
export { useReevuChat }
export type { ReevuMessage, ReevuSource }
