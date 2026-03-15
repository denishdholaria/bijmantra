import type { MouseEventHandler } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { SystemBarBrand, SystemBarControls } from './SystemBarParts'

type SystemBarProps = {
  onToggleConsole?: () => void
  isConsoleOpen?: boolean
}

export function SystemBar({
  onToggleConsole: _onToggleConsole,
  isConsoleOpen: _isConsoleOpen,
}: SystemBarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((state) => state.logout)
  const isDesktop = ['/', '/gateway', '/dashboard'].includes(location.pathname)

  const handleLogout: MouseEventHandler<HTMLButtonElement> = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="bg-shell-chrome border-shell shadow-shell relative z-50 flex h-14 items-center justify-between border-b px-4 text-shell backdrop-blur-xl sm:px-6 flex-shrink-0">
      <SystemBarBrand isDesktop={isDesktop} onGoHome={() => navigate('/dashboard')} />
      <SystemBarControls isDesktop={isDesktop} onLogout={handleLogout} />
    </header>
  )
}
