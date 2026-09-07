import { useRouter, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

interface BackButtonProps {
  to?: string;
  label?: string;
  fallbackTo?: string;
  className?: string;
  params?: Record<string, any>;
}

export function BackButton({
  to,
  label = "Back",
  fallbackTo = "/",
  className = "",
  params,
}: BackButtonProps) {
  const router = useRouter();

  const handleBack = () => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.history.back();
    } else {
      router.navigate({ to: fallbackTo as any });
    }
  };

  if (to) {
    return (
      <Link
        to={to as any}
        params={params}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] text-xs font-semibold text-muted-foreground hover:text-foreground bg-muted/40 hover:bg-muted border border-border/60 transition-all cursor-pointer group select-none ${className}`}
      >
        <ArrowLeft className="size-3.5 group-hover:-translate-x-0.5 transition-transform text-[#0a5c38] dark:text-[#3fb68e]" />
        <span>{label}</span>
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={handleBack}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] text-xs font-semibold text-muted-foreground hover:text-foreground bg-muted/40 hover:bg-muted border border-border/60 transition-all cursor-pointer group select-none ${className}`}
    >
      <ArrowLeft className="size-3.5 group-hover:-translate-x-0.5 transition-transform text-[#0a5c38] dark:text-[#3fb68e]" />
      <span>{label}</span>
    </button>
  );
}
