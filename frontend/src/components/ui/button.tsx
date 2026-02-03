import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        // Prakruti Design System variants
        patta:
          "bg-prakruti-patta text-white shadow-sm hover:bg-prakruti-patta-dark focus-visible:ring-prakruti-patta",
        "patta-outline":
          "border-2 border-prakruti-patta text-prakruti-patta bg-transparent hover:bg-prakruti-patta-pale dark:hover:bg-prakruti-patta/10",
        "patta-ghost":
          "text-prakruti-patta hover:bg-prakruti-patta-pale dark:hover:bg-prakruti-patta/10",
        mitti:
          "bg-prakruti-mitti text-white shadow-sm hover:bg-prakruti-mitti-dark focus-visible:ring-prakruti-mitti",
        "mitti-outline":
          "border-2 border-prakruti-mitti text-prakruti-mitti bg-transparent hover:bg-prakruti-mitti-50 dark:hover:bg-prakruti-mitti/10",
        sona:
          "bg-prakruti-sona text-white shadow-sm hover:bg-prakruti-sona-dark focus-visible:ring-prakruti-sona",
        "sona-outline":
          "border-2 border-prakruti-sona text-prakruti-sona-dark bg-transparent hover:bg-prakruti-sona-pale dark:hover:bg-prakruti-sona/10",
        neela:
          "bg-prakruti-neela text-white shadow-sm hover:bg-prakruti-neela-dark focus-visible:ring-prakruti-neela",
        "neela-outline":
          "border-2 border-prakruti-neela text-prakruti-neela bg-transparent hover:bg-prakruti-neela-pale dark:hover:bg-prakruti-neela/10",
        laal:
          "bg-prakruti-laal text-white shadow-sm hover:bg-prakruti-laal-dark focus-visible:ring-prakruti-laal",
        "laal-outline":
          "border-2 border-prakruti-laal text-prakruti-laal bg-transparent hover:bg-prakruti-laal-pale dark:hover:bg-prakruti-laal/10",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        xl: "h-12 rounded-md px-10 text-base",
        icon: "h-9 w-9",
        "icon-lg": "h-12 w-12",
        field: "h-14 min-w-[48px] rounded-lg px-6 text-lg font-semibold",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
