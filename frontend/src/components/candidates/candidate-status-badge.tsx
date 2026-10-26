import { Badge } from "@/components/ui/badge";
import type { CandidateStatus } from "@/types/domain";

const STATUS_CONFIG: Record<CandidateStatus, { label: string; variant: "default" | "secondary" | "success" | "warning" | "error" | "outline" }> = {
  NEW: { label: "New", variant: "outline" },
  PARSED: { label: "Parsed", variant: "secondary" },
  SHORTLISTED: { label: "Shortlisted", variant: "success" },
  MANUAL_REVIEW: { label: "Manual Review", variant: "warning" },
  REJECTED: { label: "Rejected", variant: "error" },
  INTERVIEWING: { label: "Interviewing", variant: "default" },
  HIRED: { label: "Hired", variant: "success" },
  NOT_HIRED: { label: "Not Hired", variant: "error" },
};

export function CandidateStatusBadge({ status }: { status: CandidateStatus }) {
  const config = STATUS_CONFIG[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
