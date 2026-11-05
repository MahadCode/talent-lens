"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils/cn";

export interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  value?: number;
  indicatorClassName?: string;
}

export const Progress = React.forwardRef<React.ElementRef<typeof ProgressPrimitive.Root>, ProgressProps>(
  ({ className, value = 0, indicatorClassName, ...props }, ref) => (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-muted", className)}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn("h-full flex-1 bg-gradient-brand transition-transform duration-500 ease-out", indicatorClassName)}
        style={{ transform: `translateX(-${100 - Math.min(100, Math.max(0, value))}%)` }}
      />
    </ProgressPrimitive.Root>
  ),
);
Progress.displayName = "Progress";
