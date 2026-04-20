import { ReactNode } from 'react'

interface ShellLayoutProps {
  children: ReactNode
}

export function ShellLayout({ children }: ShellLayoutProps) {
  return (
    <section className="absolute inset-0 z-20 flex min-h-0 items-stretch justify-center bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.14),transparent_46%),rgba(7,18,25,0.08)] p-3 backdrop-blur-[8px] sm:p-4">
      <div
        className="shadow-shell border-shell flex h-full w-full min-h-0 overflow-hidden rounded-[24px] border bg-[hsl(var(--app-shell-panel)/0.96)]"
      >
        {children}
      </div>
    </section>
  )
}
