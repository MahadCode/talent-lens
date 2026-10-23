import type { User, UserRole } from "@/types/domain";

export const HR_ROLES: UserRole[] = ["ADMIN", "HR_MANAGER", "RECRUITER"];
export const STAFF_ROLES: UserRole[] = ["ADMIN", "HR_MANAGER", "RECRUITER", "INTERVIEWER"];

export function isCandidate(user?: User | null): boolean {
  return user?.role === "CANDIDATE";
}

export function isHr(user?: User | null): boolean {
  return Boolean(user && HR_ROLES.includes(user.role));
}

export function isStaff(user?: User | null): boolean {
  return Boolean(user && STAFF_ROLES.includes(user.role));
}

export function homeForRole(role?: UserRole): string {
  return role === "CANDIDATE" ? "/app" : "/dashboard";
}
