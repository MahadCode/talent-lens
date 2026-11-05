"use client";

import * as React from "react";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ResumeDropzone } from "@/components/shared/resume-dropzone";
import { ScoreRing } from "@/components/shared/score-ring";
import { SkillRadarChart } from "@/components/shared/skill-radar-chart";
import { useJobs } from "@/lib/hooks/use-jobs";
import { useResumeUpload } from "@/lib/hooks/use-resume-upload";
import { useEvaluateCandidate } from "@/lib/hooks/use-workflow";
import { getApiErrorMessage } from "@/lib/api/client";
import type { ResumeUploadResponse } from "@/lib/api/resumes";
import type { WorkflowEvaluateResponse } from "@/types/domain";

export default function ResumeScreeningPage() {
  const { data: jobs } = useJobs();
  const [jobId, setJobId] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);
  const [parsed, setParsed] = React.useState<ResumeUploadResponse | null>(null);
  const [evaluation, setEvaluation] = React.useState<WorkflowEvaluateResponse | null>(null);

  const uploadResume = useResumeUpload();
  const evaluateCandidate = useEvaluateCandidate();

  async function handleAnalyze() {
    if (!jobId || !file) {
      toast.error("Select a job and choose a resume file first.");
      return;
    }
    try {
      const uploadResult = await uploadResume.mutateAsync({ jobId, file });
      setParsed(uploadResult);
      const evalResult = await evaluateCandidate.mutateAsync({ candidateId: uploadResult.candidate_id });
      setEvaluation(evalResult);
      toast.success("Resume analyzed successfully.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  }

  const isBusy = uploadResume.isPending || evaluateCandidate.isPending;

  const radarData = evaluation
    ? [
        { dimension: "Skills", score: evaluation.score_result.breakdown.skills_score },
        { dimension: "Experience", score: evaluation.score_result.breakdown.experience_score },
        { dimension: "Projects", score: evaluation.score_result.breakdown.projects_score },
        { dimension: "Education", score: evaluation.score_result.breakdown.education_score },
        { dimension: "Certifications", score: evaluation.score_result.breakdown.certifications_score },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Screening</p>
        <h1 className="mt-1 text-3xl font-normal tracking-tight text-heading">Resume screening</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload a resume and let the agents parse, match, and score it against a job.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Upload &amp; Analyze</CardTitle>
            <CardDescription>Select the job this candidate is applying for.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={jobId} onValueChange={setJobId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a job" />
              </SelectTrigger>
              <SelectContent>
                {(jobs ?? []).map((job) => (
                  <SelectItem key={job.id} value={job.id}>
                    {job.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <ResumeDropzone file={file} onFileSelected={setFile} disabled={isBusy} />

            <Button onClick={handleAnalyze} isLoading={isBusy} className="w-full" size="lg">
              <Sparkles className="h-4 w-4" /> Analyze Resume
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resume Score</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center gap-2 pb-8">
            <ScoreRing score={evaluation?.score_result.total_score ?? 0} size={112} label="/ 100" />
            <p className="text-center text-xs text-muted-foreground">
              {evaluation ? evaluation.decision.decision.replace("_", " ") : "Awaiting analysis"}
            </p>
          </CardContent>
        </Card>
      </div>

      {evaluation && parsed && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <SkillRadarChart data={radarData} />

          <Card>
            <CardHeader>
              <CardTitle>Matching Analysis</CardTitle>
              <CardDescription>{Math.round(evaluation.matching_result.match_percentage)}% overall match</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Matching skills</p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {parsed.parsed_profile.skills.map((skill) => (
                    <Badge key={skill} variant="success">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Missing skills</p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {evaluation.matching_result.missing_skills.length ? (
                    evaluation.matching_result.missing_skills.map((skill) => (
                      <Badge key={skill} variant="error">
                        {skill}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground">None.</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">AI Summary</p>
                <p className="mt-1 text-sm text-muted-foreground">{evaluation.matching_result.explanation}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
