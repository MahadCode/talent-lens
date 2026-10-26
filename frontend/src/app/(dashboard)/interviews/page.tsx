"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Bot, User as UserIcon, Send, CheckCircle2, XCircle, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useJobs } from "@/lib/hooks/use-jobs";
import { useCandidatesForJob } from "@/lib/hooks/use-candidates";
import { interviewsApi } from "@/lib/api/interviews";
import { getApiErrorMessage } from "@/lib/api/client";
import type { InterviewEvaluateResponse } from "@/types/domain";

interface Turn {
  role: "ai" | "candidate";
  text: string;
  focusArea?: string;
}

function InterviewsClient() {
  const searchParams = useSearchParams();
  const { data: jobs } = useJobs();
  const [jobId, setJobId] = React.useState(searchParams.get("job") ?? "");
  const { data: candidates } = useCandidatesForJob(jobId);
  const [candidateId, setCandidateId] = React.useState(searchParams.get("candidate") ?? "");

  const [turns, setTurns] = React.useState<Turn[]>([]);
  const [answer, setAnswer] = React.useState("");
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [isEvaluating, setIsEvaluating] = React.useState(false);
  const [evaluation, setEvaluation] = React.useState<InterviewEvaluateResponse | null>(null);

  const selectedJob = jobs?.find((j) => j.id === jobId);

  async function fetchNextQuestion() {
    if (!candidateId || !selectedJob) {
      toast.error("Select a job and candidate first.");
      return;
    }
    setIsGenerating(true);
    try {
      const history = turns.map((t) => `${t.role === "ai" ? "Q" : "A"}: ${t.text}`);
      const question = await interviewsApi.nextQuestion({
        candidateId,
        jobDescription: selectedJob.description,
        conversationHistory: history,
      });
      setTurns((prev) => [...prev, { role: "ai", text: question.question, focusArea: question.focus_area }]);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsGenerating(false);
    }
  }

  function submitAnswer() {
    if (!answer.trim()) return;
    setTurns((prev) => [...prev, { role: "candidate", text: answer.trim() }]);
    setAnswer("");
  }

  async function finishInterview() {
    if (!candidateId) return;
    setIsEvaluating(true);
    try {
      const transcript = turns.map((t) => `${t.role === "ai" ? "Q" : "A"}: ${t.text}`);
      const result = await interviewsApi.evaluate({ candidateId, questionsAndAnswers: transcript });
      setEvaluation(result);
      toast.success("Interview evaluated.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsEvaluating(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Adaptive session</p>
        <h1 className="mt-1 text-3xl font-normal tracking-tight text-heading">AI Interview</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Conduct an adaptive interview and store an evaluation against the candidate.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Session Setup</CardTitle>
                <div className="flex gap-2">
                  <Select value={jobId} onValueChange={(v) => { setJobId(v); setCandidateId(""); }}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Job" />
                    </SelectTrigger>
                    <SelectContent>
                      {(jobs ?? []).map((job) => (
                        <SelectItem key={job.id} value={job.id}>
                          {job.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={candidateId} onValueChange={setCandidateId} disabled={!jobId}>
                    <SelectTrigger className="w-44">
                      <SelectValue placeholder="Candidate" />
                    </SelectTrigger>
                    <SelectContent>
                      {(candidates ?? []).map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.full_name ?? "Unnamed"}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="min-h-[320px] space-y-4 rounded-xl border border-border bg-muted/30 p-4">
                <AnimatePresence initial={false}>
                  {turns.length === 0 && (
                    <p className="py-16 text-center text-sm text-muted-foreground">
                      Select a job and candidate, then generate the first question.
                    </p>
                  )}
                  {turns.map((turn, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-3 ${turn.role === "candidate" ? "flex-row-reverse" : ""}`}
                    >
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                          turn.role === "ai" ? "bg-primary/10 text-primary" : "bg-secondary/10 text-secondary"
                        }`}
                      >
                        {turn.role === "ai" ? <Bot className="h-4 w-4" /> : <UserIcon className="h-4 w-4" />}
                      </div>
                      <div
                        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                          turn.role === "ai"
                            ? "rounded-tl-sm bg-surface text-heading shadow-card"
                            : "rounded-tr-sm bg-primary text-primary-foreground"
                        }`}
                      >
                        {turn.text}
                        {turn.focusArea && (
                          <div className="mt-1.5">
                            <Badge variant="outline">{turn.focusArea}</Badge>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              <div className="mt-4 flex gap-2">
                <input
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && submitAnswer()}
                  placeholder="Type the candidate's answer..."
                  className="h-11 flex-1 rounded-xl border border-border bg-surface px-4 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                />
                <Button variant="secondary" onClick={submitAnswer} size="icon">
                  <Send className="h-4 w-4" />
                </Button>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <Button onClick={fetchNextQuestion} isLoading={isGenerating} disabled={!candidateId}>
                  <Sparkles className="h-4 w-4" /> Generate Next Question
                </Button>
                <Button
                  variant="outline"
                  onClick={finishInterview}
                  isLoading={isEvaluating}
                  disabled={!candidateId || turns.length === 0}
                >
                  Finish &amp; Evaluate
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Evaluation</CardTitle>
            <CardDescription>Overall assessment and recommendation.</CardDescription>
          </CardHeader>
          <CardContent>
            {evaluation ? (
              <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                <div
                  className={`flex items-center gap-2 rounded-xl p-3 ${
                    evaluation.passed ? "bg-success/10 text-success" : "bg-error/10 text-error"
                  }`}
                >
                  {evaluation.passed ? <CheckCircle2 className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                  <span className="text-sm font-medium">{evaluation.passed ? "Passed" : "Did not pass"}</span>
                </div>
                <p className="text-sm text-muted-foreground">{evaluation.overall_assessment}</p>
              </motion.div>
            ) : (
              <p className="text-sm text-muted-foreground">Finish the interview to see the AI evaluation here.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function InterviewsPage() {
  return (
    <React.Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
      <InterviewsClient />
    </React.Suspense>
  );
}
