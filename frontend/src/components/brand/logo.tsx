import { cn } from "@/lib/utils/cn";

export function BrandLogo({ className, markOnly = false }: { className?: string; markOnly?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2 text-heading", className)}>
      <svg width="27" height="27" viewBox="0 0 27 27" fill="none" aria-hidden>
        <defs>
          <linearGradient id="brand-stroke" x1="0" y1="0" x2="27" y2="27">
            <stop stopColor="#ffb347" />
            <stop offset="0.45" stopColor="#ff5a5f" />
            <stop offset="1" stopColor="#ff3d8b" />
          </linearGradient>
        </defs>
        <rect x="2" y="2" width="23" height="23" rx="6" stroke="url(#brand-stroke)" strokeWidth="1.6" />
        <circle cx="10" cy="12" r="1.4" fill="#141414" />
        <circle cx="17" cy="12" r="1.4" fill="#141414" />
      </svg>
      {markOnly ? null : <span className="text-[18px] font-medium tracking-tight">Talent Lens</span>}
    </span>
  );
}
