"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { schedulesApi, type ScheduleCreatePayload } from "@/lib/api/schedules";
import type { HiringDecision } from "@/types/domain";

export function useSchedules(candidateId?: string) {
  return useQuery({
    queryKey: ["schedules", { candidateId }],
    queryFn: () => schedulesApi.list({ candidate_id: candidateId }),
  });
}

export function useCreateSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScheduleCreatePayload) => schedulesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useInterviewFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ interviewId, comments }: { interviewId: string; comments: string }) =>
      schedulesApi.saveFeedback(interviewId, { comments }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["schedules"] }),
  });
}

export function useInterviewDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ interviewId, decision }: { interviewId: string; decision: HiringDecision }) =>
      schedulesApi.recordDecision(interviewId, decision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}
