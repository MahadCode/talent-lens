"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { FileSearch, UserCheck, MessagesSquare, Inbox, Lightbulb, Bell } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { cn } from "@/lib/utils/cn";
import { formatRelativeTime } from "@/lib/utils/cn";
import type { AppNotification } from "@/types/domain";

/**
 * NOTE ON SAMPLE DATA: the backend does not yet expose a notifications
 * endpoint. This page is fully built and ready — swap `SAMPLE_NOTIFICATIONS`
 * for a `useNotifications()` query hook once that endpoint exists.
 */
const SAMPLE_NOTIFICATIONS: AppNotification[] = [
  {
    id: "1",
    type: "resume_processed",
    title: "Resume processed",
    message: "6 resumes were parsed for Senior Backend Engineer.",
    read: false,
    created_at: new Date(Date.now() - 10 * 60_000).toISOString(),
  },
  {
    id: "2",
    type: "candidate_shortlisted",
    title: "Candidate shortlisted",
    message: "Priya Nair was shortlisted for Staff Data Engineer.",
    read: false,
    created_at: new Date(Date.now() - 2 * 3_600_000).toISOString(),
  },
  {
    id: "3",
    type: "interview_scheduled",
    title: "Interview scheduled",
    message: "AI interview scheduled with 2 candidates for DevOps Lead.",
    read: true,
    created_at: new Date(Date.now() - 26 * 3_600_000).toISOString(),
  },
  {
    id: "4",
    type: "ai_recommendation",
    title: "New AI recommendation",
    message: "Your job description for \"Senior Backend Engineer\" could be improved.",
    read: true,
    created_at: new Date(Date.now() - 3 * 24 * 3_600_000).toISOString(),
  },
];

const ICONS: Record<AppNotification["type"], React.ElementType> = {
  resume_processed: FileSearch,
  candidate_shortlisted: UserCheck,
  interview_scheduled: MessagesSquare,
  new_application: Inbox,
  ai_recommendation: Lightbulb,
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = React.useState(SAMPLE_NOTIFICATIONS);

  function markAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="label-mono text-muted-foreground">Inbox</p>
          <h1 className="mt-1 text-3xl font-normal tracking-tight text-heading">Notifications</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {unreadCount > 0 ? `${unreadCount} unread` : "You're all caught up"}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" size="sm" onClick={markAllRead}>
            Mark all as read
          </Button>
        )}
      </div>

      {notifications.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications" description="You'll see updates from your AI agents here." />
      ) : (
        <Card>
          <CardContent className="divide-y divide-border p-0">
            {notifications.map((notification, i) => {
              const Icon = ICONS[notification.type];
              return (
                <motion.div
                  key={notification.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.25, delay: i * 0.04 }}
                  className={cn("flex gap-3 px-5 py-4", !notification.read && "bg-primary/[0.03]")}
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-heading">{notification.title}</p>
                      {!notification.read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />}
                    </div>
                    <p className="mt-0.5 text-sm text-muted-foreground">{notification.message}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatRelativeTime(notification.created_at)}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
