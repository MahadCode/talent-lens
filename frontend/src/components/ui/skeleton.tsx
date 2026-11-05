import { cn } from "@/lib/utils/cn";

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("skeleton-shimmer rounded-xl", className)} {...props} />;
}
