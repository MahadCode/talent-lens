"use client";

import { BrandLogo } from "@/components/brand/logo";

const HIGHLIGHTS = [
  "Parse a resume into structured evidence.",
  "Score applicants against a role — not keywords.",
  "Humans shortlist. The model explains.",
];

export default function AuthGroupLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden border-r border-heading/10 bg-background lg:flex lg:flex-col lg:justify-between lg:p-12">
        <BrandLogo />
        <div className="max-w-md space-y-6">
          <p className="label-mono text-muted-foreground">Unleash the power of</p>
          <div className="space-y-2">
            <h1 className="border border-heading/20 px-4 py-3 text-[clamp(36px,4vw,64px)] font-normal leading-none">
              Thinking
            </h1>
            <h1 className="border border-heading/20 px-4 py-3 text-[clamp(36px,4vw,64px)] font-normal leading-none">
              Machines
            </h1>
          </div>
          <p className="text-[14.5px] text-muted-foreground">
            Your hiring workspace for evidence-linked scores, human shortlists, and scheduled interviews.
          </p>
          <ul className="divide-y divide-heading/10 border-y border-heading/10">
            {HIGHLIGHTS.map((text) => (
              <li key={text} className="label-mono flex h-[42px] items-center gap-3">
                <span className="h-1 w-1 rounded-full bg-heading" />
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="label-mono text-muted-foreground">Talent Lens · 2026</p>
      </div>

      <div className="flex items-center justify-center bg-background px-6 py-12">
        <div className="glass-panel w-full max-w-md p-8">{children}</div>
      </div>
    </div>
  );
}
