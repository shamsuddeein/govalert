import React from "react";
import { cn } from "../lib/utils";

interface TrustScoreBadgeProps {
  score?: number | null;
  className?: string;
  showLabel?: boolean;
}

export function TrustScoreBadge({ score = 85, className }: TrustScoreBadgeProps) {
  const safeScore = Math.max(0, Math.min(100, Math.round(score ?? 85)));

  let colorStyle = "text-[#0a5c38] dark:text-[#3fb68e] bg-[#0a5c38]/10 border-[#0a5c38]/20";
  if (safeScore < 50) {
    colorStyle = "text-red-600 dark:text-red-400 bg-red-500/10 border-red-500/20";
  } else if (safeScore < 80) {
    colorStyle = "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-[4px] border text-[11px] font-mono font-semibold tracking-tight shrink-0",
        colorStyle,
        className
      )}
    >
      Vetted {safeScore}%
    </span>
  );
}
