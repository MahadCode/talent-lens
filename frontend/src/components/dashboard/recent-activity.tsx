"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { FileSearch, Sparkles, MessagesSquare, UserCheck } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { formatRelativeTime } from "@/lib/utils/cn";

export interface ActivityEvent {
  id: string;
  type: "resume_parsed" | "match_scored" | "interview_scheduled" | "candidate_shortlisted";
  message: string;
  timestamp: string;
}

const ICONS: Record<ActivityEvent["type"], LucideIcon> = {
  resume_parsed: FileSearch,
  match_scored: Sparkles,
  interview_scheduled: MessagesSquare,
  candidate_shortlisted: UserCheck,
};

export function RecentActivity({ events }: { events: ActivityEvent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>What your AI agents have been doing.</CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="relative space-y-5 border-l border-border pl-6">
          {events.map((event, i) => {
            const Icon = ICONS[event.type];
            return (
              <motion.li
                key={event.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                className="relative"
              >
                <span className="absolute -left-[31px] flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 ring-4 ring-surface">
                  <Icon className="h-3 w-3 text-primary" />
                </span>
                <p className="text-sm text-heading">{event.message}</p>
                <p className="text-xs text-muted-foreground">{formatRelativeTime(event.timestamp)}</p>
              </motion.li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
