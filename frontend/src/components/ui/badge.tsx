import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
        outline: "text-foreground border-border",
        success:
          "border-transparent bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300",
        warning:
          "border-transparent bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300",
        info:
          "border-transparent bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
        // Prakruti Design System variants
        patta:
          "border-transparent bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light",
        "patta-solid":
          "border-transparent bg-prakruti-patta text-white",
        mitti:
          "border-transparent bg-prakruti-mitti-100 text-prakruti-mitti-dark dark:bg-prakruti-mitti/20 dark:text-prakruti-mitti-light",
        "mitti-solid":
          "border-transparent bg-prakruti-mitti text-white",
        sona:
          "border-transparent bg-prakruti-sona-pale text-prakruti-sona-dark dark:bg-prakruti-sona/20 dark:text-prakruti-sona-light",
        "sona-solid":
          "border-transparent bg-prakruti-sona text-white",
        neela:
          "border-transparent bg-prakruti-neela-pale text-prakruti-neela dark:bg-prakruti-neela/20 dark:text-prakruti-neela-light",
        "neela-solid":
          "border-transparent bg-prakruti-neela text-white",
        laal:
          "border-transparent bg-prakruti-laal-pale text-prakruti-laal dark:bg-prakruti-laal/20 dark:text-prakruti-laal-light",
        "laal-solid":
          "border-transparent bg-prakruti-laal text-white",
        narangi:
          "border-transparent bg-prakruti-narangi-pale text-prakruti-narangi-dark dark:bg-prakruti-narangi/20 dark:text-prakruti-narangi-light",
        "narangi-solid":
          "border-transparent bg-prakruti-narangi text-white",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
