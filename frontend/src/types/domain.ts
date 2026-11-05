/**
 * Domain types mirrored from the FastAPI backend's Pydantic schemas.
 */

export type UserRole = "ADMIN" | "HR_MANAGER" | "RECRUITER" | "INTERVIEWER" | "CANDIDATE";

export type JobStatus = "DRAFT" | "OPEN" | "CLOSED" | "ARCHIVED";

export type CandidateStatus =
  | "NEW"
  | "PARSED"
  | "SHORTLISTED"
  | "MANUAL_REVIEW"
  | "REJECTED"
  | "INTERVIEWING"
  | "HIRED"
  | "NOT_HIRED";

export type InterviewType = "PHONE" | "VIDEO" | "ONSITE";

export type HiringDecision = "HIRED" | "NOT_HIRED";

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  company_name: string | null;
  profile_image: string | null;
  is_active: boolean;
  is_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  last_login: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginResult {
  access_token?: string | null;
  refresh_token?: string | null;
  token_type?: string;
  requires_2fa: boolean;
  challenge_id?: string | null;
}

export interface RegisterResult {
  user: User;
  verification_required: boolean;
}

export interface ExtractedRequirements {
  required_skills?: string[];
  preferred_skills?: string[];
  experience?: string;
  qualifications?: string[];
}

export interface Job {
  id: string;
  title: string;
  description: string;
  requirements: string;
  extracted_requirements: ExtractedRequirements | null;
  status: JobStatus;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface ParsedCandidateProfile {
  name: string | null;
  email: string | null;
  phone: string | null;
  skills: string[];
  experience: string[];
  education: string[];
  projects: string[];
  certifications: string[];
  github: string | null;
  linkedin: string | null;
}

export interface Candidate {
  id: string;
  job_id: string;
  full_name: string | null;
  email: string | null;
  github_url: string | null;
  status: CandidateStatus;
  parsed_profile: ParsedCandidateProfile | null;
  match_percentage: number | null;
  score_overridden?: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandidateApplication {
  id: string;
  job_id: string;
  job_title: string | null;
  status: CandidateStatus;
  parsed_profile: ParsedCandidateProfile | null;
  created_at: string;
  updated_at: string;
}

export interface Assessment {
  candidate_id: string;
  total_score: number;
  skills_score: number;
  experience_score: number;
  projects_score: number;
  education_score: number;
  certifications_score: number;
  reasoning: string;
  match_percentage: number | null;
  missing_skills: string[];
  extra_skills: string[];
  experience_comparison: string | null;
  explanation: string | null;
  score_overridden: boolean;
}

export interface CandidateNote {
  id: string;
  candidate_id: string;
  author_id: string;
  body: string;
  created_at: string;
}

export interface StatusEvent {
  id: string;
  candidate_id: string;
  actor_id: string;
  from_status: CandidateStatus;
  to_status: CandidateStatus;
  created_at: string;
}

export interface MatchingResult {
  match_percentage: number;
  missing_skills: string[];
  extra_skills: string[];
  experience_comparison: string;
  explanation: string;
}

export interface ScoreBreakdown {
  skills_score: number;
  experience_score: number;
  projects_score: number;
  education_score: number;
  certifications_score: number;
}

export interface ScoringResult {
  breakdown: ScoreBreakdown;
  total_score: number;
  reasoning: string;
}

export type DecisionType = "SHORTLIST" | "MANUAL_REVIEW" | "REJECT";

export interface DecisionResult {
  decision: DecisionType;
  reason: string;
}

export interface EmailContent {
  subject: string;
  body: string;
}

export interface WorkflowEvaluateResponse {
  parsed_candidate: ParsedCandidateProfile;
  matching_result: MatchingResult;
  score_result: ScoringResult;
  decision: DecisionResult;
  email_content: EmailContent | null;
  final_recommendation: string | null;
}

export interface InterviewQuestionResponse {
  question: string;
  focus_area: string;
  is_follow_up: boolean;
}

export interface InterviewEvaluateResponse {
  interview_id: string;
  overall_assessment: string;
  passed: boolean;
}

export interface StoredQuestion {
  id: string;
  question: string;
  focus_area: string;
  difficulty: string;
  guideline: string;
  is_follow_up: boolean;
}

export interface QuestionSet {
  candidate_id: string;
  interview_id: string | null;
  questions: StoredQuestion[];
}

export interface ScheduledInterview {
  id: string;
  candidate_id: string;
  scheduled_at: string;
  interviewer_name: string;
  interview_type: InterviewType;
  notes: string | null;
  feedback: { ratings?: Record<string, number>; comments?: string } | null;
  decision: HiringDecision | null;
  conflict: boolean;
  conflicting_interview_id: string | null;
  created_at: string;
}

export interface AnalyticsSummary {
  active_jobs: number;
  applications: number;
  shortlisted: number;
  pending_reviews: number;
  upcoming_interviews: number;
}

export interface SkillGapCount {
  skill: string;
  count: number;
}

export interface JobAnalytics {
  job_id: string;
  counts_by_status: Record<string, number>;
  application_to_shortlist_rate: number;
  average_processing_hours: number | null;
  common_skill_gaps: SkillGapCount[];
}

export interface ResumeSelf {
  resume_id: string;
  candidate_id: string;
  job_id: string;
  original_filename: string;
  parsed_profile: ParsedCandidateProfile | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface AppNotification {
  id: string;
  type: "resume_processed" | "candidate_shortlisted" | "interview_scheduled" | "new_application" | "ai_recommendation";
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}
