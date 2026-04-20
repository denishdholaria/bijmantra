import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { Login } from './Login'

const startupAudioStorageKey = 'bijmantra.login.startup-audio-enabled'
const startupAudioSessionKey = 'bijmantra.login.startup-audio-played'

const mockNavigate = vi.fn()
const mockLogin = vi.fn()
const mockClearError = vi.fn()
const mockSetActiveWorkspace = vi.fn()
const mockDismissGateway = vi.fn()

const authStoreState = {
  login: mockLogin,
  isLoading: false,
  error: null as string | null,
  clearError: mockClearError,
}

const workspaceStoreState = {
  preferences: {
    defaultWorkspace: null as string | null,
    showGatewayOnLogin: true,
  },
  setActiveWorkspace: mockSetActiveWorkspace,
  dismissGateway: mockDismissGateway,
}

const mockAudioInstances: MockAudio[] = []

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('@/store/auth', () => ({
  useAuthStore: () => authStoreState,
}))

vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: () => workspaceStoreState,
}))

vi.mock('@/framework/registry/workspaces', () => ({
  getWorkspace: vi.fn(() => null),
}))

class MockAudio {
  currentTime = 0
  duration = 1.2
  loop = false
  muted = false
  paused = true
  preload = 'auto'
  src: string
  volume = 1

  readonly play = vi.fn(async () => {
    this.paused = false
  })

  readonly pause = vi.fn(() => {
    this.paused = true
  })

  readonly load = vi.fn()

  private listeners = new Map<string, Set<EventListener>>()

  constructor(src = '') {
    this.src = src
    mockAudioInstances.push(this)
  }

  addEventListener(type: string, listener: EventListener) {
    const listeners = this.listeners.get(type) ?? new Set<EventListener>()
    listeners.add(listener)
    this.listeners.set(type, listeners)
  }

  removeEventListener(type: string, listener: EventListener) {
    this.listeners.get(type)?.delete(listener)
  }

  dispatch(type: string) {
    const event = new Event(type)
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event)
    }
  }
}

function setConnectionSaveData(saveData?: boolean) {
  Object.defineProperty(navigator, 'connection', {
    configurable: true,
    writable: true,
    value: saveData === undefined ? undefined : { saveData },
  })
}

function setVisiblePageState() {
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    value: 'visible',
  })
}

async function submitLoginForm(email = 'demo@bijmantra.org', password = 'Demo123!') {
  fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: email } })
  fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: password } })

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: /enter bijmantra/i }))
  })

  await waitFor(() => {
    expect(mockLogin).toHaveBeenCalledWith(email, password)
  })
}

describe('Login arrival tone', () => {
  beforeEach(() => {
    cleanup()
    vi.clearAllMocks()
    mockAudioInstances.length = 0
    delete window.__bijmantraLoginStartupAudio
    authStoreState.isLoading = false
    authStoreState.error = null
    workspaceStoreState.preferences.defaultWorkspace = null
    workspaceStoreState.preferences.showGatewayOnLogin = true
    mockLogin.mockResolvedValue(undefined)
    window.localStorage.clear()
    window.sessionStorage.clear()
    setConnectionSaveData(undefined)
    setVisiblePageState()

    vi.stubGlobal('Audio', MockAudio as unknown as typeof Audio)
    vi.stubGlobal('requestAnimationFrame', vi.fn(() => 1))
    vi.stubGlobal('cancelAnimationFrame', vi.fn())
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('plays after a successful login and stays silent on later logins in the same session', async () => {
    const firstRender = render(<Login />)
    expect(mockAudioInstances).toHaveLength(1)
    expect(mockAudioInstances[0]?.src).toContain('bijmantra-start-audio.mp3')

    await act(async () => {
      window.dispatchEvent(new Event('pointerdown'))
    })

    expect(mockAudioInstances[0]?.play).not.toHaveBeenCalled()

    await submitLoginForm()

    await waitFor(() => {
      expect(window.sessionStorage.getItem(startupAudioSessionKey)).toBe('played')
    })

    expect(mockAudioInstances[0]?.play.mock.calls.length ?? 0).toBeGreaterThanOrEqual(1)
    expect(mockNavigate).toHaveBeenCalledWith('/gateway', { replace: true })

    const pauseCallsBeforeUnmount = mockAudioInstances[0]?.pause.mock.calls.length ?? 0

    mockNavigate.mockClear()

    firstRender.unmount()

    expect(mockAudioInstances[0]?.pause).toHaveBeenCalledTimes(pauseCallsBeforeUnmount)

    render(<Login />)
    expect(mockAudioInstances).toHaveLength(1)

    await submitLoginForm('second@bijmantra.org', 'AnotherDemo123!')

    expect(mockAudioInstances[0]?.play).toHaveBeenCalledTimes(1)
  })

  it('respects a persisted mute preference', async () => {
    window.localStorage.setItem(startupAudioStorageKey, 'off')

    render(<Login />)

    await submitLoginForm()

    expect(mockAudioInstances[0]?.play).not.toHaveBeenCalled()
    expect(window.sessionStorage.getItem(startupAudioSessionKey)).toBeNull()
    expect(screen.getByRole('button', { name: /arrival tone off/i })).toBeInTheDocument()
  })

  it('starts muted on data saver, then enables and plays on successful login', async () => {
    setConnectionSaveData(true)

    render(<Login />)

    expect(screen.getByText(/quiet by default on data saver/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /arrival tone off/i }))

    expect(mockAudioInstances[0]?.play).not.toHaveBeenCalled()

    await submitLoginForm()

    await waitFor(() => {
      expect(window.sessionStorage.getItem(startupAudioSessionKey)).toBe('played')
    })

    expect(window.localStorage.getItem(startupAudioStorageKey)).toBe('on')
    expect(screen.getByRole('button', { name: /arrival tone on/i })).toBeInTheDocument()
  })

  it('stops playback when the page is hidden or navigating away', async () => {
    render(<Login />)

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /preview arrival tone/i }))
    })

    await waitFor(() => {
      expect(mockAudioInstances[0]?.play).toHaveBeenCalledTimes(1)
    })

    const pauseCallsBeforeHide = mockAudioInstances[0]?.pause.mock.calls.length ?? 0

    await act(async () => {
      window.dispatchEvent(new Event('pagehide'))
    })

    expect(mockAudioInstances[0]?.pause).toHaveBeenCalledTimes(pauseCallsBeforeHide + 1)
  })

  it('stops playback when the tab becomes hidden', async () => {
    render(<Login />)

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /preview arrival tone/i }))
    })

    await waitFor(() => {
      expect(mockAudioInstances[0]?.play).toHaveBeenCalledTimes(1)
    })

    const pauseCallsBeforeHide = mockAudioInstances[0]?.pause.mock.calls.length ?? 0

    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      value: 'hidden',
    })

    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'))
    })

    expect(mockAudioInstances[0]?.pause).toHaveBeenCalledTimes(pauseCallsBeforeHide + 1)
  })
})