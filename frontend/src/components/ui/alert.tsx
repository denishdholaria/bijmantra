import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive:
          "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
        // Prakruti Design System variants
        patta:
          "border-prakruti-patta/30 bg-prakruti-patta-pale dark:bg-prakruti-patta/10 text-prakruti-patta-dark dark:text-prakruti-patta-light [&>svg]:text-prakruti-patta",
        mitti:
          "border-prakruti-mitti/30 bg-prakruti-mitti-50 dark:bg-prakruti-mitti/10 text-prakruti-mitti-dark dark:text-prakruti-mitti-light [&>svg]:text-prakruti-mitti",
        sona:
          "border-prakruti-sona/30 bg-prakruti-sona-pale dark:bg-prakruti-sona/10 text-prakruti-sona-dark dark:text-prakruti-sona-light [&>svg]:text-prakruti-sona",
        neela:
          "border-prakruti-neela/30 bg-prakruti-neela-pale dark:bg-prakruti-neela/10 text-prakruti-neela-dark dark:text-prakruti-neela-light [&>svg]:text-prakruti-neela",
        laal:
          "border-prakruti-laal/30 bg-prakruti-laal-pale dark:bg-prakruti-laal/10 text-prakruti-laal-dark dark:text-prakruti-laal-light [&>svg]:text-prakruti-laal",
        narangi:
          "border-prakruti-narangi/30 bg-prakruti-narangi-pale dark:bg-prakruti-narangi/10 text-prakruti-narangi-dark dark:text-prakruti-narangi-light [&>svg]:text-prakruti-narangi",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
))
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription }
