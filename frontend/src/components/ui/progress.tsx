import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const progressVariants = cva(
  "relative w-full overflow-hidden rounded-full",
  {
    variants: {
      variant: {
        default: "bg-secondary",
        // Prakruti Design System variants
        patta: "bg-prakruti-patta-pale dark:bg-prakruti-patta/20",
        mitti: "bg-prakruti-mitti-100 dark:bg-prakruti-mitti/20",
        sona: "bg-prakruti-sona-pale dark:bg-prakruti-sona/20",
        neela: "bg-prakruti-neela-pale dark:bg-prakruti-neela/20",
        laal: "bg-prakruti-laal-pale dark:bg-prakruti-laal/20",
      },
      size: {
        default: "h-4",
        sm: "h-2",
        lg: "h-6",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const indicatorVariants = cva(
  "h-full w-full flex-1 transition-all",
  {
    variants: {
      variant: {
        default: "bg-primary",
        patta: "bg-prakruti-patta",
        mitti: "bg-prakruti-mitti",
        sona: "bg-prakruti-sona",
        neela: "bg-prakruti-neela",
        laal: "bg-prakruti-laal",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface ProgressProps
  extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>,
    VariantProps<typeof progressVariants> {
  /** Accessible label for the progress bar (required for WCAG compliance) */
  "aria-label"?: string
  /** ID of element that labels this progress bar */
  "aria-labelledby"?: string
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value, variant, size, "aria-label": ariaLabel, "aria-labelledby": ariaLabelledBy, ...props }, ref) => {
  // Provide default aria-label if none specified for accessibility
  const accessibleLabel = ariaLabel || ariaLabelledBy ? undefined : "Loading progress"
  
  return (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(progressVariants({ variant, size, className }))}
      aria-label={ariaLabel || accessibleLabel}
      aria-labelledby={ariaLabelledBy}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn(indicatorVariants({ variant }))}
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  )
})
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress, progressVariants }
