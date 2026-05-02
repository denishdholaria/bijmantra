import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('useSystemStore persistence contract', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('hydrates only persisted shell preferences and resets runtime desktop state', async () => {
    localStorage.setItem(
      'bijmantra-system-storage',
      JSON.stringify({
        state: {
          shortcutOrder: ['workspace-a', 'workspace-b'],
          sidebarCollapsed: true,
          lastDesktopToolSurface: 'filesystem',
          desktopToolSurface: 'editor',
          isStrataOpen: true,
          isInShell: true,
        },
        version: 0,
      })
    )

    const { useSystemStore } = await import('./systemStore')
    const state = useSystemStore.getState()

    expect(state.shortcutOrder).toEqual(['workspace-a', 'workspace-b'])
    expect(state.sidebarCollapsed).toBe(true)
    expect(state.lastDesktopToolSurface).toBe('filesystem')
    expect(state.desktopToolSurface).toBeNull()
    expect(state.isStrataOpen).toBe(false)
    expect(state.isInShell).toBe(false)
  })
})