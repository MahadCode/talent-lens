"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { ScoreRing } from "@/components/shared/score-ring";
import { CandidateStatusBadge } from "@/components/candidates/candidate-status-badge";
import {
  useAddNote,
  useAssessment,
  useCandidate,
  useCandidateEvents,
  useCandidateNotes,
  useChangeStatus,
  useDeleteQuestion,
  useGenerateQuestions,
  useOverrideScore,
  useQuestionSet,
  useRegenerateQuestions,
  useUpdateQuestion,
} from "@/lib/hooks/use-candidates";
import { useEvaluateCandidate } from "@/lib/hooks/use-workflow";
import { getApiErrorMessage } from "@/lib/api/client";
import { getInitials } from "@/lib/utils/cn";
import type { CandidateStatus } from "@/types/domain";
import { useQueryClient } from "@tanstack/react-query";

const NEXT: Partial<Record<CandidateStatus, CandidateStatus[]>> = {
  PARSED: ["SHORTLISTED", "REJECTED"],
  MANUAL_REVIEW: ["SHORTLISTED", "REJECTED"],
  SHORTLISTED: ["INTERVIEWING", "REJECTED"],
  INTERVIEWING: ["HIRED", "NOT_HIRED"],
};

export default function CandidateDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { data: candidate, isLoading } = useCandidate(params.id);
  const { data: assessment } = useAssessment(params.id);
  const { data: notes } = useCandidateNotes(params.id);
  const { data: events } = useCandidateEvents(params.id);
  const { data: questions } = useQuestionSet(params.id);
  const changeStatus = useChangeStatus(params.id);
  const addNote = useAddNote(params.id);
  const overrideScore = useOverrideScore(params.id);
  const generateQuestions = useGenerateQuestions(params.id);
  const regenerateQuestions = useRegenerateQuestions(params.id);
  const updateQuestion = useUpdateQuestion(params.id);
  const deleteQuestion = useDeleteQuestion(params.id);
  const evaluate = useEvaluateCandidate();
  const [note, setNote] = React.useState("");
  const [override, setOverride] = React.useState("72");
  const [reason, setReason] = React.useState("");

  async function runEvaluation() {
    try {
      await evaluate.mutateAsync({ candidateId: params.id });
      await queryClient.invalidateQueries({ queryKey: ["candidates", params.id] });
      await queryClient.invalidateQueries({ queryKey: ["candidates", params.id, "assessment"] });
      toast.success("Evaluation stored.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  }

  if (isLoading || !candidate) {
    return <Skeleton className="h-64" />;
  }

  const profile = candidate.parsed_profile;
  const allowed = NEXT[candidate.status] ?? [];

  return (
    <div className="space-y-6">
      <Link href="/candidates" className="label-mono inline-flex items-center gap-2 text-muted-foreground hover:text-heading">
        <ArrowLeft className="h-3.5 w-3.5" /> Candidates
      </Link>

      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div className="flex items-center gap-4">
          <Avatar className="h-14 w-14">
            <AvatarFallback>{getInitials(candidate.full_name)}</AvatarFallback>
          </Avatar>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-normal">{candidate.full_name ?? "Unnamed candidate"}</h1>
              <CandidateStatusBadge status={candidate.status} />
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{candidate.email}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {allowed.map((status) => (
            <Button
              key={status}
              variant="outline"
              size="sm"
              isLoading={changeStatus.isPending}
              onClick={async () => {
                try {
                  await changeStatus.mutateAsync(status);
                  toast.success(`Moved to ${status}.`);
                } catch (error) {
                  toast.error(getApiErrorMessage(error));
                }
              }}
            >
              {status.replace("_", " ")}
            </Button>
          ))}
          <Button asChild variant="outline" size="sm">
            <Link href={`/schedule?candidate=${candidate.id}&job=${candidate.job_id}`}>Schedule</Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href={`/interviews?candidate=${candidate.id}&job=${candidate.job_id}`}>AI Interview</Link>
          </Button>
          <Button size="sm" onClick={() => void runEvaluation()} isLoading={evaluate.isPending}>
            <Sparkles className="h-4 w-4" /> Run evaluation
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Skills</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-1.5">
              {profile?.skills?.length ? profile.skills.map((skill) => <Badge key={skill} variant="outline">{skill}</Badge>) : <p className="text-sm text-muted-foreground">None parsed.</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Assessment</CardTitle>
              <CardDescription>Stored explanation. Refresh-safe.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {assessment ? (
                <>
                  <p className="text-sm">{assessment.explanation ?? assessment.reasoning}</p>
                  {assessment.experience_comparison ? (
                    <p className="text-sm text-muted-foreground">{assessment.experience_comparison}</p>
                  ) : null}
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {[
                      ["Skills", assessment.skills_score],
                      ["Experience", assessment.experience_score],
                      ["Projects", assessment.projects_score],
                      ["Education", assessment.education_score],
                      ["Certifications", assessment.certifications_score],
                    ].map(([label, value]) => (
                      <div key={String(label)} className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">{label}</span>
                          <span>{Math.round(Number(value))}</span>
                        </div>
                        <Progress value={Number(value)} />
                      </div>
                    ))}
                  </div>
                  <div>
                    <p className="label-mono mb-2 text-muted-foreground">Missing evidence</p>
                    <div className="flex flex-wrap gap-1.5">
                      {assessment.missing_skills.length ? assessment.missing_skills.map((skill) => (
                        <Badge key={skill} variant="error">{skill}</Badge>
                      )) : <p className="text-xs text-muted-foreground">None listed.</p>}
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No assessment yet. Run evaluation after the resume is parsed.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Question bank</CardTitle>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  isLoading={generateQuestions.isPending}
                  onClick={async () => {
                    try {
                      await generateQuestions.mutateAsync();
                      toast.success("Question set saved.");
                    } catch (error) {
                      toast.error(getApiErrorMessage(error));
                    }
                  }}
                >
                  Generate
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  isLoading={regenerateQuestions.isPending}
                  onClick={async () => {
                    try {
                      await regenerateQuestions.mutateAsync();
                      toast.success("Question set replaced.");
                    } catch (error) {
                      toast.error(getApiErrorMessage(error));
                    }
                  }}
                >
                  Regenerate
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {(questions?.questions ?? []).map((item) => (
                <div key={item.id} className="space-y-2 border border-heading/10 p-3">
                  <p className="label-mono text-muted-foreground">{item.difficulty} · {item.focus_area}</p>
                  <Input
                    defaultValue={item.question}
                    onBlur={(event) => {
                      if (event.target.value !== item.question) {
                        updateQuestion.mutate({ questionId: item.id, question: event.target.value });
                      }
                    }}
                  />
                  <p className="text-xs text-muted-foreground">{item.guideline}</p>
                  <Button size="sm" variant="ghost" onClick={() => deleteQuestion.mutate(item.id)}>
                    Remove
                  </Button>
                </div>
              ))}
              {!questions?.questions.length ? <p className="text-sm text-muted-foreground">No saved questions yet.</p> : null}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Match score</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-3">
              <ScoreRing score={assessment?.total_score ?? candidate.match_percentage ?? 0} size={112} label="/ 100" />
              {assessment?.score_overridden ? <p className="label-mono text-muted-foreground">Overridden</p> : null}
              <Input type="number" min={0} max={100} value={override} onChange={(e) => setOverride(e.target.value)} />
              <Input placeholder="Reason" value={reason} onChange={(e) => setReason(e.target.value)} />
              <Button
                variant="outline"
                className="w-full"
                isLoading={overrideScore.isPending}
                onClick={async () => {
                  if (!reason.trim()) {
                    toast.error("Give a reason for the override.");
                    return;
                  }
                  try {
                    await overrideScore.mutateAsync({ totalScore: Number(override), reason });
                    toast.success("Score overridden.");
                  } catch (error) {
                    toast.error(getApiErrorMessage(error));
                  }
                }}
              >
                Override score
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Private notes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Visible to staff only" />
              <Button
                variant="outline"
                className="w-full"
                onClick={async () => {
                  if (!note.trim()) return;
                  await addNote.mutateAsync(note);
                  setNote("");
                }}
              >
                Add note
              </Button>
              <div className="space-y-2">
                {(notes ?? []).map((item) => (
                  <p key={item.id} className="border-t border-heading/10 pt-2 text-sm">
                    {item.body}
                  </p>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Status history</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(events ?? []).map((event) => (
                <p key={event.id} className="label-mono text-muted-foreground">
                  {event.from_status} → {event.to_status}
                </p>
              ))}
              {!events?.length ? <p className="text-sm text-muted-foreground">No human status changes yet.</p> : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
