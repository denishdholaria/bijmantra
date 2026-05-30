import * as React from "react"
import { cn } from "@/lib/utils"

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Accessible label for screen readers */
  "aria-label"?: string
}

function Spinner({ className, "aria-label": ariaLabel = "Loading...", ...props }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label={ariaLabel}
      className={cn(
        "inline-block h-6 w-6 animate-spin rounded-full border-2 border-current border-t-transparent",
        className
      )}
      {...props}
    />
  )
}

export { Spinner }
