"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { Users } from "lucide-react";
import { getInitials } from "@/lib/utils/cn";
import type { Candidate } from "@/types/domain";
import { CandidateStatusBadge } from "@/components/candidates/candidate-status-badge";

export function LatestCandidates({ candidates }: { candidates: Candidate[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Latest Candidates</CardTitle>
        <CardDescription>Most recently parsed applicants across all jobs.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-1">
        {candidates.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No candidates yet"
            description="Upload a resume to see candidates appear here."
          />
        ) : (
          candidates.map((candidate, i) => (
            <motion.div
              key={candidate.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.25, delay: i * 0.05 }}
            >
              <Link
                href={`/candidates/${candidate.id}`}
                className="flex items-center gap-3 rounded-xl px-2 py-2.5 transition-colors hover:bg-muted"
              >
                <Avatar>
                  <AvatarFallback>{getInitials(candidate.full_name)}</AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-heading">
                    {candidate.full_name ?? "Unnamed candidate"}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">{candidate.email ?? "No email parsed"}</p>
                </div>
                {candidate.match_percentage != null && (
                  <Badge variant="secondary">{Math.round(candidate.match_percentage)}% match</Badge>
                )}
                <CandidateStatusBadge status={candidate.status} />
              </Link>
            </motion.div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
