import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-heading text-background hover:opacity-90",
        secondary: "bg-muted text-heading hover:bg-muted/80",
        outline: "border border-heading/20 bg-transparent text-heading hover:bg-heading/5",
        ghost: "bg-transparent text-heading hover:bg-heading/5",
        destructive: "border border-error text-error hover:bg-error/10",
        link: "text-heading underline-offset-4 hover:underline",
        brand:
          "border border-heading/20 bg-transparent font-mono text-[11px] uppercase tracking-[0.06em] hover:bg-heading/5",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, isLoading = false, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        {...props}
      >
        {asChild ? (
          children
        ) : (
          <>
            {isLoading ? <Loader2 className="animate-spin" /> : null}
            {children}
          </>
        )}
      </Comp>
    );
  },
);
Button.displayName = "Button";
