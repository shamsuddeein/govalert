export type SpeedTier = "fast" | "slow" | "offline";

export function speedTier(ms: number | null | undefined): SpeedTier {
  if (ms == null || ms <= 0) return "offline";
  return ms < 500 ? "fast" : "slow";
}

export function speedLabel(ms: number | null | undefined): { text: string; colorStyle: string } {
  if (ms == null || ms <= 0) {
    return { text: "Offline", colorStyle: "text-[#991B1B] bg-red-50 dark:bg-red-950/30 border-red-200" };
  }
  const isFast = ms < 500;
  const label = isFast ? `${ms}ms Fast` : `${ms}ms Slow`;
  const colorStyle = isFast
    ? "text-[#166534] bg-[#DCFCE7] dark:bg-[#DCFCE7] dark:text-[#166534] border-[#166534]/20"
    : "text-[#991B1B] bg-[#FEE2E2] dark:bg-[#FEE2E2] dark:text-[#991B1B] border-[#991B1B]/20";

  return { text: label, colorStyle };
}

interface SpeedDotsProps {
  ms: number | null | undefined;
  className?: string;
}

export function SpeedDots({ ms, className = "" }: SpeedDotsProps) {
  const { text, colorStyle } = speedLabel(ms);

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-[4px] border text-[11px] font-mono font-semibold shrink-0 select-none ${colorStyle} ${className}`}
      title={`Response time: ${ms ?? 0}ms`}
    >
      {text}
    </span>
  );
}