"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { workflowApi } from "@/lib/api/workflow";

export function useEvaluateCandidate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: workflowApi.evaluate,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["candidates", variables.candidateId] });
    },
  });
}
