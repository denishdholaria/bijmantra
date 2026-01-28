import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const inputVariants = cva(
  "flex h-9 w-full rounded-md border bg-background px-3 py-1 text-base text-foreground shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
  {
    variants: {
      variant: {
        default: "border-input focus-visible:ring-1 focus-visible:ring-ring",
        // Prakruti Design System variants
        prakruti: 
          "border-prakruti-dhool-300 dark:border-prakruti-dhool-600 focus-visible:ring-2 focus-visible:ring-prakruti-patta focus-visible:border-prakruti-patta",
        patta:
          "border-prakruti-patta/30 focus-visible:ring-2 focus-visible:ring-prakruti-patta focus-visible:border-prakruti-patta",
        mitti:
          "border-prakruti-mitti/30 focus-visible:ring-2 focus-visible:ring-prakruti-mitti focus-visible:border-prakruti-mitti",
        neela:
          "border-prakruti-neela/30 focus-visible:ring-2 focus-visible:ring-prakruti-neela focus-visible:border-prakruti-neela",
        error:
          "border-prakruti-laal focus-visible:ring-2 focus-visible:ring-prakruti-laal focus-visible:border-prakruti-laal",
      },
      inputSize: {
        default: "h-9",
        sm: "h-8 text-xs",
        lg: "h-11 text-base",
        field: "h-14 text-lg rounded-lg px-4",
      },
    },
    defaultVariants: {
      variant: "default",
      inputSize: "default",
    },
  }
)

export interface InputProps
  extends Omit<React.ComponentProps<"input">, "size">,
    VariantProps<typeof inputVariants> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, variant, inputSize, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(inputVariants({ variant, inputSize, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input, inputVariants }
