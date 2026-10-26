"use client";

import { motion } from "framer-motion";
import { Lightbulb, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export interface Recommendation {
  id: string;
  title: string;
  detail: string;
}

export function AIRecommendations({ items }: { items: Recommendation[] }) {
  return (
    <Card className="border-primary/20 bg-gradient-to-br from-primary/[0.04] to-transparent">
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Lightbulb className="h-4 w-4 text-primary" />
          </div>
          <CardTitle>AI Recommendations</CardTitle>
        </div>
        <CardDescription>Insights generated from your current pipeline.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((item, i) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.06 }}
            className="group flex items-start justify-between gap-3 rounded-xl border border-border bg-surface p-3.5 transition-colors hover:border-primary/30"
          >
            <div>
              <p className="text-sm font-medium text-heading">{item.title}</p>
              <p className="text-xs text-muted-foreground">{item.detail}</p>
            </div>
            <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
}
