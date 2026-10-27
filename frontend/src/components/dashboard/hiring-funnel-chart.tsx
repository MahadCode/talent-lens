"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils/cn";

export interface FunnelStage {
  label: string;
  value: number;
}

/**
 * A custom horizontal funnel visualization (not a generic bar chart) so the
 * hiring pipeline reads as a narrowing funnel, stage by stage.
 */
export function HiringFunnelChart({ stages }: { stages: FunnelStage[] }) {
  const max = Math.max(...stages.map((s) => s.value), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hiring Funnel</CardTitle>
        <CardDescription>Candidates moving through each stage this month.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {stages.map((stage, i) => {
          const widthPct = Math.max(8, (stage.value / max) * 100);
          return (
            <div key={stage.label} className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-heading">{stage.label}</span>
                <span className="text-muted-foreground">{stage.value}</span>
              </div>
              <div className="h-8 w-full overflow-hidden rounded-lg bg-muted">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.6, delay: i * 0.08, ease: "easeOut" }}
                  className={cn(
                    "h-full rounded-lg bg-gradient-brand",
                    i === 0 && "opacity-100",
                    i === 1 && "opacity-90",
                    i === 2 && "opacity-80",
                    i >= 3 && "opacity-70",
                  )}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
