"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { candidatesApi } from "@/lib/api/candidates";
import type { CandidateStatus } from "@/types/domain";

export function useCandidatesForJob(jobId: string) {
  return useQuery({
    queryKey: ["candidates", "by-job", jobId],
    queryFn: () => candidatesApi.listForJob(jobId),
    enabled: Boolean(jobId),
  });
}

export function useCandidate(candidateId: string) {
  return useQuery({
    queryKey: ["candidates", candidateId],
    queryFn: () => candidatesApi.get(candidateId),
    enabled: Boolean(candidateId),
  });
}

export function useAssessment(candidateId: string) {
  return useQuery({
    queryKey: ["candidates", candidateId, "assessment"],
    queryFn: () => candidatesApi.getAssessment(candidateId),
    enabled: Boolean(candidateId),
    retry: false,
  });
}

export function useCandidateNotes(candidateId: string) {
  return useQuery({
    queryKey: ["candidates", candidateId, "notes"],
    queryFn: () => candidatesApi.listNotes(candidateId),
    enabled: Boolean(candidateId),
  });
}

export function useCandidateEvents(candidateId: string) {
  return useQuery({
    queryKey: ["candidates", candidateId, "events"],
    queryFn: () => candidatesApi.listEvents(candidateId),
    enabled: Boolean(candidateId),
  });
}

export function useChangeStatus(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: CandidateStatus) => candidatesApi.changeStatus(candidateId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useAddNote(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => candidatesApi.addNote(candidateId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates", candidateId, "notes"] }),
  });
}

export function useOverrideScore(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { totalScore: number; reason: string }) =>
      candidatesApi.overrideScore(candidateId, payload.totalScore, payload.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates", candidateId] });
      queryClient.invalidateQueries({ queryKey: ["candidates", candidateId, "assessment"] });
    },
  });
}

export function useMyApplications() {
  return useQuery({
    queryKey: ["candidates", "me"],
    queryFn: () => candidatesApi.listMine(),
  });
}

export function useMyApplication(candidateId: string) {
  return useQuery({
    queryKey: ["candidates", "me", candidateId],
    queryFn: () => candidatesApi.getMine(candidateId),
    enabled: Boolean(candidateId),
  });
}

export function useApplyToJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, file }: { jobId: string; file: File }) => candidatesApi.apply(jobId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates", "me"] }),
  });
}

export function useQuestionSet(candidateId: string) {
  return useQuery({
    queryKey: ["candidates", candidateId, "questions"],
    queryFn: () => candidatesApi.listQuestions(candidateId),
    enabled: Boolean(candidateId),
    retry: false,
  });
}

export function useGenerateQuestions(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => candidatesApi.generateQuestions(candidateId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates", candidateId, "questions"] }),
  });
}

export function useRegenerateQuestions(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => candidatesApi.regenerateQuestions(candidateId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates", candidateId, "questions"] }),
  });
}

export function useUpdateQuestion(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      questionId,
      question,
    }: {
      questionId: string;
      question: string;
    }) => candidatesApi.updateQuestion(questionId, { question }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates", candidateId, "questions"] }),
  });
}

export function useDeleteQuestion(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (questionId: string) => candidatesApi.deleteQuestion(questionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates", candidateId, "questions"] }),
  });
}
