"use client";

import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { resumesApi } from "@/lib/api/resumes";
import { candidatesApi } from "@/lib/api/candidates";
import { getApiErrorMessage } from "@/lib/api/client";
import { useQuery, useQueryClient } from "@tanstack/react-query";

export default function MyResumePage() {
  const queryClient = useQueryClient();
  const { data, error, isLoading } = useQuery({
    queryKey: ["resumes", "me"],
    queryFn: () => resumesApi.me(),
    retry: false,
  });
  const [skills, setSkills] = React.useState("");
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (data?.parsed_profile?.skills) {
      setSkills(data.parsed_profile.skills.join(", "));
    }
  }, [data]);

  async function save() {
    if (!data) return;
    setSaving(true);
    try {
      await candidatesApi.updateMyProfile(data.candidate_id, {
        skills: skills.split(",").map((item) => item.trim()).filter(Boolean),
      });
      await queryClient.invalidateQueries({ queryKey: ["resumes", "me"] });
      toast.success("Resume updated.");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Profile</p>
        <h1 className="mt-1 text-3xl font-normal">My resume</h1>
      </div>
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : error || !data ? (
        <p className="text-sm text-muted-foreground">Upload a resume when you apply to a job. It will appear here.</p>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>{data.original_filename}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <p className="label-mono text-muted-foreground">Skills</p>
              <Input value={skills} onChange={(event) => setSkills(event.target.value)} />
              <p className="text-xs text-muted-foreground">Comma-separated. Saving clears a stale AI score until a recruiter re-runs evaluation.</p>
            </div>
            <Button onClick={() => void save()} isLoading={saving}>
              Save corrections
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
