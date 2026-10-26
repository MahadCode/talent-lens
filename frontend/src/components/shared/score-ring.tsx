"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  label?: string;
}

/** An animated circular score indicator (0-100), color-coded by threshold. */
export function ScoreRing({ score, size = 96, strokeWidth = 8, className, label }: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, score));
  const offset = circumference - (clamped / 100) * circumference;

  const color = clamped >= 80 ? "hsl(var(--success))" : clamped >= 60 ? "hsl(var(--warning))" : "hsl(var(--error))";

  return (
    <div className={cn("relative flex items-center justify-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xl font-semibold text-heading">{Math.round(clamped)}</span>
        {label ? <span className="text-[10px] text-muted-foreground">{label}</span> : null}
      </div>
    </div>
  );
}
