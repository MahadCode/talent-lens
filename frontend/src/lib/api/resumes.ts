import { apiClient } from "@/lib/api/client";
import type { ParsedCandidateProfile, ResumeSelf } from "@/types/domain";

export interface ResumeUploadResponse {
  resume_id: string;
  candidate_id: string;
  parsed_profile: ParsedCandidateProfile;
}

export const resumesApi = {
  async upload(params: { jobId: string; candidateId?: string; file: File }): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append("job_id", params.jobId);
    if (params.candidateId) formData.append("candidate_id", params.candidateId);
    formData.append("file", params.file);

    const { data } = await apiClient.post<ResumeUploadResponse>("/resumes/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async me(candidateId?: string): Promise<ResumeSelf> {
    const { data } = await apiClient.get<ResumeSelf>("/resumes/me", {
      params: candidateId ? { candidate_id: candidateId } : undefined,
    });
    return data;
  },
};
