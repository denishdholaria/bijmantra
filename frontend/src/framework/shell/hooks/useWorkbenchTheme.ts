import { useEffect, useState } from 'react'

export function useWorkbenchTheme() {
  const [theme, setTheme] = useState<'vs-dark' | 'vs-light'>(() =>
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark') ? 'vs-dark' : 'vs-light'
  )

  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }

    const root = document.documentElement
    const observer = new MutationObserver(() => {
      setTheme(root.classList.contains('dark') ? 'vs-dark' : 'vs-light')
    })

    observer.observe(root, {
      attributes: true,
      attributeFilter: ['class'],
    })

    return () => observer.disconnect()
  }, [])

  return theme
}
