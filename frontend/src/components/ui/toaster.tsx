"use client";

import { Toaster as Sonner } from "sonner";

/** App-wide toast host, styled to match the Talent Lens design system. */
export function Toaster() {
  return (
    <Sonner
      position="top-right"
      toastOptions={{
        classNames: {
          toast:
            "rounded-2xl border border-border bg-surface text-heading shadow-soft font-sans",
          description: "text-muted-foreground",
          actionButton: "bg-primary text-primary-foreground",
          cancelButton: "bg-muted text-muted-foreground",
        },
      }}
    />
  );
}
