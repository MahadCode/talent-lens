"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useJobs } from "@/lib/hooks/use-jobs";
import { useCandidatesForJob } from "@/lib/hooks/use-candidates";
import { useCreateSchedule, useInterviewDecision, useInterviewFeedback, useSchedules } from "@/lib/hooks/use-schedules";
import { getApiErrorMessage } from "@/lib/api/client";
import { formatDate } from "@/lib/utils/cn";
import type { HiringDecision, InterviewType } from "@/types/domain";

function ScheduleClient() {
  const searchParams = useSearchParams();
  const preselectedCandidate = searchParams.get("candidate") ?? "";
  const preselectedJob = searchParams.get("job") ?? "";
  const { data: jobs } = useJobs();
  const [jobId, setJobId] = React.useState(preselectedJob);
  const { data: candidates } = useCandidatesForJob(jobId);
  const [candidateId, setCandidateId] = React.useState(preselectedCandidate);
  const [when, setWhen] = React.useState("");
  const [interviewer, setInterviewer] = React.useState("");
  const [type, setType] = React.useState<InterviewType>("VIDEO");
  const create = useCreateSchedule();
  const { data: rows } = useSchedules();
  const feedback = useInterviewFeedback();
  const decision = useInterviewDecision();

  React.useEffect(() => {
    if (preselectedJob) setJobId(preselectedJob);
    if (preselectedCandidate) setCandidateId(preselectedCandidate);
  }, [preselectedCandidate, preselectedJob]);

  async function book() {
    if (!candidateId || !when || !interviewer) {
      toast.error("Candidate, time, and interviewer are required.");
      return;
    }
    try {
      const result = await create.mutateAsync({
        candidate_id: candidateId,
        scheduled_at: new Date(when).toISOString(),
        interviewer_name: interviewer,
        interview_type: type,
      });
      toast.success(result.conflict ? "Booked with a conflict warning." : "Interview booked.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Calendar</p>
        <h1 className="mt-1 text-3xl font-normal">Schedule</h1>
        <p className="mt-1 text-sm text-muted-foreground">Book human interviews, record feedback, and close a hire decision.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Book an interview</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Job</Label>
            <Select value={jobId} onValueChange={(value) => { setJobId(value); setCandidateId(""); }}>
              <SelectTrigger><SelectValue placeholder="Select job" /></SelectTrigger>
              <SelectContent>
                {(jobs ?? []).map((job) => (
                  <SelectItem key={job.id} value={job.id}>{job.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Candidate</Label>
            <Select value={candidateId} onValueChange={setCandidateId}>
              <SelectTrigger><SelectValue placeholder="Select candidate" /></SelectTrigger>
              <SelectContent>
                {(candidates ?? []).map((candidate) => (
                  <SelectItem key={candidate.id} value={candidate.id}>
                    {candidate.full_name ?? "Unnamed"} · {candidate.status}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Date and time</Label>
            <Input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Interviewer</Label>
            <Input value={interviewer} onChange={(e) => setInterviewer(e.target.value)} placeholder="Mara Elling" />
          </div>
          <div className="space-y-1.5">
            <Label>Type</Label>
            <Select value={type} onValueChange={(v) => setType(v as InterviewType)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="PHONE">Phone</SelectItem>
                <SelectItem value="VIDEO">Video</SelectItem>
                <SelectItem value="ONSITE">Onsite</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button onClick={() => void book()} isLoading={create.isPending}>·· Book</Button>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-2">
        {(rows ?? []).map((row) => (
          <Card key={row.id}>
            <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="label-mono text-muted-foreground">
                  {row.interview_type}
                  {row.conflict ? " · conflict" : ""}
                  {row.decision ? ` · ${row.decision}` : ""}
                </p>
                <p>{formatDate(row.scheduled_at)} · {row.interviewer_name}</p>
                {row.feedback?.comments ? <p className="text-sm text-muted-foreground">{row.feedback.comments}</p> : null}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    const comments = window.prompt("Feedback") ?? "";
                    if (!comments) return;
                    try {
                      await feedback.mutateAsync({ interviewId: row.id, comments });
                      toast.success("Feedback saved.");
                    } catch (error) {
                      toast.error(getApiErrorMessage(error));
                    }
                  }}
                >
                  Feedback
                </Button>
                {(["HIRED", "NOT_HIRED"] as HiringDecision[]).map((value) => (
                  <Button
                    key={value}
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      try {
                        await decision.mutateAsync({ interviewId: row.id, decision: value });
                        toast.success(`Marked ${value.replace("_", " ").toLowerCase()}.`);
                      } catch (error) {
                        toast.error(getApiErrorMessage(error));
                      }
                    }}
                  >
                    {value.replace("_", " ")}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
        {!rows?.length ? <p className="text-sm text-muted-foreground">No interviews booked yet.</p> : null}
      </div>
    </div>
  );
}

export default function SchedulePage() {
  return (
    <React.Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
      <ScheduleClient />
    </React.Suspense>
  );
}
