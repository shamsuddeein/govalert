import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { AgencyLogo } from "../components/AgencyLogo";
import { agenciesData } from "../lib/agenciesData";
import { api, ApiAgency, ApiJob, ApiSystemStatus } from "../lib/api";
import { OfficialSourceLink } from "../components/OfficialSourceLink";
import { SeoHead } from "../components/SeoHead";
import { toast } from "sonner";

export const Route = createFileRoute("/")({
  component: Index,
});

export type Status = "verified" | "urgent" | "new" | "closed" | "warning" | "unknown";

export interface Job {
  id: string;
  agency: string;
  agencyShort: string;
  title: string;
  deadline: string;
  status: Status;
  detected: string;
  category: string;
  state: string;
  createdAt: string;
  positions?: string;
  officialUrl?: string;
}

// ─── UI Helper Skeletons & Components ─────────────────────────────────────────

export function JobCardSkeleton() {
  return (
    <div className="flex flex-col justify-between rounded-[8px] border border-border bg-card p-6 animate-pulse space-y-4 font-sans">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="size-8 rounded-full bg-muted" />
          <div className="h-3 w-20 bg-muted rounded" />
        </div>
        <div className="h-5 w-16 bg-muted rounded-[6px]" />
      </div>
      <div className="space-y-2">
        <div className="h-5 w-3/4 bg-muted rounded" />
        <div className="h-4 w-1/3 bg-muted rounded" />
      </div>
      <div className="border-t border-border pt-4 grid grid-cols-2 gap-4">
        <div className="h-3 w-full bg-muted rounded" />
        <div className="h-3 w-full bg-muted rounded" />
      </div>
      <div className="h-9 w-full bg-muted rounded-[6px]" />
    </div>
  );
}

export function KeywordSubscriptionForm({ queryText }: { queryText: string }) {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [confirmedMessage, setConfirmedMessage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (!email.trim()) {
      setErrorMsg("Please enter a valid email address.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.subscribeKeyword(email.trim(), queryText.trim() || "all openings");
      setConfirmedMessage(res.detail || `You'll be notified at ${email} when a match appears.`);
      toast.success("Keyword subscription active!");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create subscription. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (confirmedMessage) {
    return (
      <div className="w-full max-w-md p-4 bg-[#0a5c38]/10 border border-[#0a5c38]/30 dark:bg-[#3fb68e]/15 dark:border-[#3fb68e]/30 rounded-[8px] text-center space-y-1 font-sans">
        <div className="flex items-center justify-center gap-2 text-[#0a5c38] dark:text-[#3fb68e] font-bold text-xs sm:text-sm">
          <svg className="size-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9 9 9 4.03 9 9z" />
          </svg>
          Subscription Active
        </div>
        <p className="text-xs text-foreground font-medium leading-relaxed">
          {confirmedMessage}
        </p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-2.5 font-sans text-left bg-muted/30 border border-border p-4 rounded-[8px]">
      <p className="text-xs font-semibold text-foreground text-center sm:text-left">
        Get notified when <span className="text-[#0a5c38] dark:text-[#3fb68e] font-bold">'{queryText || "new postings"}'</span> matches a new recruitment:
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-stretch gap-2">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="enter.your.email@example.com"
          required
          className="flex-1 px-3.5 py-2.5 bg-background border border-border rounded-[6px] text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e] font-sans min-w-0"
        />
        <button
          type="submit"
          disabled={submitting}
          className="px-5 py-2.5 bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] text-xs font-semibold rounded-[6px] transition-all cursor-pointer disabled:opacity-50 shrink-0 font-sans shadow-sm flex items-center justify-center gap-1.5"
        >
          {submitting ? (
            <span>Subscribing...</span>
          ) : (
            <>
              <span>Notify Me</span>
              <svg className="size-3.5 fill-none stroke-current shrink-0" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 5.25l7.5 7.5-7.5 7.5M21 12H3" />
              </svg>
            </>
          )}
        </button>
      </form>

      {errorMsg && (
        <p className="text-[11px] font-semibold text-destructive font-sans text-center sm:text-left">
          ⚠️ {errorMsg}
        </p>
      )}
    </div>
  );
}

export function JobsEmptyState({
  searchQuery,
  onClear,
}: {
  searchQuery?: string;
  onClear?: () => void;
}) {
  const queryText = searchQuery && searchQuery.trim() ? searchQuery.trim() : "";

  return (
    <div className="flex flex-col items-center justify-center p-6 sm:p-10 text-center bg-card border border-border rounded-[8px] space-y-5 my-6 font-sans">
      <div className="p-3.5 bg-[#0a5c38]/8 text-[#0a5c38] dark:bg-[#3fb68e]/10 dark:text-[#3fb68e] rounded-[8px]">
        <svg className="size-8 stroke-current fill-none" strokeWidth="1.5" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
      </div>

      <div className="max-w-md space-y-1.5">
        <h3 className="text-base sm:text-lg font-bold text-foreground font-sans leading-snug">
          {queryText ? `No matches for '${queryText}' right now.` : "No verified recruitment alerts found."}
        </h3>
        <p className="text-xs sm:text-sm text-muted-foreground font-sans leading-relaxed">
          Get notified when a matching recruitment appears. Join our Telegram channel or subscribe to email alerts.
        </p>
      </div>

      <KeywordSubscriptionForm queryText={queryText} />

      <div className="flex flex-wrap items-center justify-center gap-3 pt-1 border-t border-border/50 w-full max-w-md">
        <a
          href="https://t.me/govalerts_bot"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] text-xs font-semibold rounded-[6px] transition-transform active:scale-[0.98] cursor-pointer shadow-sm font-sans"
        >
          <svg className="size-[14px] fill-current shrink-0" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.02-1.93 1.23-5.46 3.62-.51.35-.98.53-1.39.51-.46-.01-1.33-.26-1.99-.47-.8-.27-1.44-.41-1.39-.87.03-.24.35-.49.97-.75 3.79-1.65 6.32-2.73 7.57-3.26 3.61-1.53 4.36-1.8 4.85-1.8.11 0 .35.03.5.15.13.12.17.27.18.39-.01.08-.01.18-.02.26z" />
          </svg>
          Get Bot Alerts &rarr;
        </a>

        {onClear && (
          <button
            onClick={onClear}
            className="inline-flex items-center px-4 py-2 bg-card border border-border text-foreground hover:bg-muted text-xs font-semibold rounded-[6px] transition-colors cursor-pointer font-sans"
          >
            Reset Search & Filters
          </button>
        )}
      </div>
    </div>
  );
}

export function JobsErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center p-10 text-center bg-destructive/5 border border-destructive/20 rounded-[8px] space-y-4 my-6 font-sans">
      <div className="p-3 bg-destructive/8 rounded-[8px] text-destructive">
        <svg className="size-8 stroke-current fill-none" strokeWidth="1.5" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </div>
      <div className="max-w-md space-y-1">
        <h3 className="text-base font-semibold text-foreground font-sans">Unable to Load Recruitment Data</h3>
        <p className="text-xs text-muted-foreground font-sans">{message}</p>
      </div>
      <button
        onClick={onRetry}
        className="mt-2 inline-flex items-center gap-2 px-4 py-2 bg-[#0a5c38] dark:bg-[#3fb68e] text-white dark:text-[#0c1015] text-xs font-semibold rounded-[6px] hover:opacity-90 transition-opacity cursor-pointer font-sans shadow-sm"
      >
        <svg className="size-3.5 fill-none stroke-current" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        <span>Retry Connection</span>
      </button>
    </div>
  );
}

export function StatusBadge({ status, warningNote }: { status: Status; warningNote?: string }) {
  const map: Record<Status, { label: string; cls: string; icon: React.ReactNode }> = {
    verified: {
      label: "Open",
      cls: "bg-[#E6F4EA] text-[#137333] dark:bg-[#073b22]/70 dark:text-[#3fb68e] font-semibold border border-[#137333]/20",
      icon: (
        <span className="size-1.5 rounded-full bg-[#137333] dark:bg-[#3fb68e] shrink-0" />
      ),
    },
    urgent: {
      label: "Closing Soon",
      cls: "bg-[#FEF3C7] text-[#92400E] dark:bg-[#451a03]/70 dark:text-[#fcd34d] font-semibold border border-[#92400E]/20",
      icon: (
        <span className="size-1.5 rounded-full bg-[#92400E] dark:bg-[#fcd34d] shrink-0" />
      ),
    },
    new: {
      label: "New",
      cls: "bg-[#E8F0FE] text-[#1A73E8] dark:bg-[#1c335a]/70 dark:text-[#8ab4f8] font-semibold border border-[#1A73E8]/20",
      icon: (
        <span className="size-1.5 rounded-full bg-[#1A73E8] shrink-0" />
      ),
    },
    warning: {
      label: "Notice",
      cls: "bg-[#FEF3C7] text-[#92400E] dark:bg-[#451a03]/70 dark:text-[#fcd34d] font-semibold border border-[#92400E]/20",
      icon: (
        <span className="size-1.5 rounded-full bg-[#92400E] shrink-0" />
      ),
    },
    closed: {
      label: "Closed",
      cls: "bg-muted text-muted-foreground font-semibold border border-border/60",
      icon: (
        <span className="size-1.5 rounded-full bg-muted-foreground/60 shrink-0" />
      ),
    },
    unknown: {
      label: "Active",
      cls: "bg-[#E6F4EA] text-[#137333] dark:bg-[#073b22]/70 dark:text-[#3fb68e] font-semibold border border-[#137333]/20",
      icon: (
        <span className="size-1.5 rounded-full bg-[#137333] dark:bg-[#3fb68e] shrink-0" />
      ),
    },
  };

  // Map internal system 'updating' or 'no-change' to 'verified' for public users.
  // Hide warning badge unless accompanied by a 1-sentence plain English explanation.
  let effectiveStatus = (status as string) === "updating" || (status as string) === "no-change" ? "verified" : status;
  if (effectiveStatus === "warning" && !warningNote) {
    effectiveStatus = "verified";
  }
  const s = map[effectiveStatus] || map.verified;

  return (
    <div className="inline-flex flex-col gap-1">
      <span
        className={`inline-flex items-center gap-[4px] rounded-[6px] px-[8px] sm:px-[10px] py-[3px] sm:py-[4px] text-[10px] sm:text-[11px] font-semibold font-sans uppercase tracking-[0.06em] shrink-0 truncate max-w-[110px] sm:max-w-none ${s.cls}`}
        title={s.label}
      >
        <span className="shrink-0">{s.icon}</span>
        <span className="truncate">{s.label}</span>
      </span>
      {effectiveStatus === "warning" && warningNote && (
        <p className="text-[11px] text-amber-700 dark:text-amber-400 font-normal leading-tight">
          {warningNote}
        </p>
      )}
    </div>
  );
}

function Hero({
  searchQuery,
  setSearchQuery,
  onTagClick,
}: {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  onTagClick: (tag: string) => void;
}) {
  const [inputValue, setInputValue] = useState(searchQuery);

  useEffect(() => {
    setInputValue(searchQuery);
  }, [searchQuery]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(inputValue);
    document.getElementById("recruitments")?.scrollIntoView({ behavior: "smooth" });
  };

  const handleBrowseJobs = () => {
    document.getElementById("recruitments")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="py-8 sm:py-16 bg-background w-full max-w-full overflow-hidden">
      <div className="mx-auto max-w-[1184px] px-4 sm:px-6 w-full min-w-0">
        <div className="max-w-3xl space-y-5 sm:space-y-6 text-left">
          

          <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground leading-[1.15]">
            Is that recruitment portal <span className="text-[#0a5c38] dark:text-[#3fb68e]">real or fake?</span>
          </h1>

          <p className="text-[15px] sm:text-[17px] leading-relaxed text-muted-foreground max-w-2xl font-sans">
            We check 42 official Nigerian federal MDA portals and surface verified job openings, official deadlines, and direct application links. No payment is ever required to apply for a federal government job.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={handleBrowseJobs}
              className="h-[46px] rounded-[8px] bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] px-7 text-sm font-semibold transition-transform active:scale-[0.98] cursor-pointer shadow-sm"
            >
              Browse Openings
            </button>
            <a
              href="https://t.me/govalerts_bot?start=general"
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-[46px] items-center gap-2 rounded-[8px] border border-border bg-card text-[#0a5c38] dark:text-[#3fb68e] hover:bg-muted px-6 text-sm font-semibold transition-transform active:scale-[0.98] cursor-pointer"
            >
              <svg className="size-[15px] fill-current" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.02-1.93 1.23-5.46 3.62-.51.35-.98.53-1.39.51-.46-.01-1.33-.26-1.99-.47-.8-.27-1.44-.41-1.39-.87.03-.24.35-.49.97-.75 3.79-1.65 6.32-2.73 7.57-3.26 3.61-1.53 4.36-1.8 4.85-1.8.11 0 .35.03.5.15.13.12.17.27.18.39-.01.08-.01.18-.02.26z" />
              </svg>
              Get Telegram Alerts
            </a>
          </div>

          {/* Search bar */}
          <div className="pt-2 max-w-xl">
            <form
              className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-0 rounded-[8px] sm:border sm:border-border sm:bg-card sm:p-1 focus-within:ring-2 focus-within:ring-[#0a5c38] dark:focus-within:ring-[#3fb68e] transition-shadow w-full"
              onSubmit={handleSubmit}
            >
              <div className="relative w-full sm:flex-1 rounded-[8px] border sm:border-none border-border bg-card sm:bg-transparent">
                <svg
                  className="pointer-events-none absolute left-[12px] top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z" />
                </svg>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Search NNPC, Customs, EFCC, Police, Immigration..."
                  className="w-full border-none bg-transparent py-3 pl-10 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none font-sans"
                />
              </div>
              <button
                type="submit"
                className="w-full sm:w-auto h-[44px] sm:h-[40px] px-6 rounded-[6px] bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] text-xs font-semibold cursor-pointer transition-colors shrink-0 flex items-center justify-center font-sans"
              >
                Search
              </button>
            </form>
          </div>

          <div className="flex flex-row items-center gap-[8px] overflow-x-auto pt-1 pb-1 w-full max-w-full min-w-0 no-scrollbar">
            <span className="shrink-0 text-[12px] font-medium text-muted-foreground font-sans">Popular agencies:</span>
            {["NNPC", "Customs", "EFCC", "Police", "CBN", "FIRS", "Immigration"].map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => onTagClick(tag)}
                className="shrink-0 bg-muted/60 text-foreground hover:bg-muted text-[12px] font-medium rounded-[6px] px-[12px] py-[10px] min-h-[44px] min-w-[44px] inline-flex items-center justify-center transition-colors cursor-pointer border border-border font-sans"
              >
                {tag}
              </button>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}

function Stats({ status }: { status: ApiSystemStatus | null }) {
  const onlineCount = status?.agencies_online ?? 42;
  const totalPortals = status?.total_agencies ?? 42;
  const checksToday = status?.total_checks_today ?? 0;

  const formatAuditTime = (timeStr: string | null | undefined) => {
    if (!timeStr) return "Just now";
    try {
      const d = new Date(timeStr);
      return isNaN(d.getTime()) ? timeStr : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
    } catch {
      return timeStr;
    }
  };

  const lastCheckTime = formatAuditTime(status?.last_audit_at);

  return (
    <div className="border-y border-border bg-card py-3 w-full max-w-full overflow-hidden font-sans">
      <div className="mx-auto max-w-[1184px] px-4 sm:px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 text-xs text-muted-foreground font-medium w-full min-w-0">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-1.5 min-w-0">
          <div className="flex items-center gap-2 text-foreground font-semibold">
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#0a5c38', flexShrink: 0, display: 'inline-block' }} className="bg-[#0a5c38] dark:bg-[#3fb68e]" />
            <span>{onlineCount} of {totalPortals} Portals Online</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <span>&middot;</span>
            <span>{checksToday.toLocaleString()} Checks Completed Today</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <span>&middot;</span>
            <span>Last Check: {lastCheckTime}</span>
          </div>
        </div>
        <div className="text-[11px] sm:text-xs text-[#0a5c38] dark:text-[#3fb68e] font-semibold flex items-center gap-1">
          <svg className="size-3.5 fill-none stroke-current" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9 9 4.03 9 9z" />
          </svg>
          <span>Government recruitment is 100% free. Never pay for job forms</span>
        </div>
      </div>
    </div>
  );
}

function LatestJobs({
  jobs,
  loading,
  error,
  onRetry,
  searchQuery,
  setSearchQuery,
  selectedCategory,
  setSelectedCategory,
}: {
  jobs: Job[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  selectedCategory: string | null;
  setSelectedCategory: (c: string | null) => void;
}) {
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const hasFilters = searchQuery !== "" || selectedCategory !== null;

  const handleClearFilters = () => {
    setSearchQuery("");
    setSelectedCategory(null);
  };

  return (
    <section id="recruitments" className="py-8 sm:py-12 bg-background font-sans">
      <div className="mx-auto max-w-[1184px] px-4 sm:px-6">
        <div className="mb-6 flex flex-col justify-between gap-3 md:flex-row md:items-end">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-primary">Latest Verified Job Openings</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {hasFilters ? (
                <span>
                  Showing {jobs.length} results for{" "}
                  {selectedCategory && (
                    <span className="font-semibold text-primary">{selectedCategory}</span>
                  )}
                  {selectedCategory && searchQuery && " and "}
                  {searchQuery && (
                    <span className="font-semibold text-primary">"{searchQuery}"</span>
                  )}
                </span>
              ) : (
                "Verified recruitment campaigns from official Nigerian government portals."
              )}
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            {hasFilters && (
              <button
                onClick={handleClearFilters}
                className="text-xs font-medium text-muted-foreground underline decoration-1 underline-offset-4 hover:text-primary cursor-pointer font-sans"
              >
                Clear filters
              </button>
            )}
            
            <div className="inline-flex rounded-[6px] border border-border p-0.5 bg-muted/20">
              <button
                onClick={() => setViewMode("grid")}
                className={`px-3 py-1 text-xs font-semibold rounded-[4px] cursor-pointer transition-colors font-sans ${
                  viewMode === "grid" ? "bg-card text-primary shadow-sm" : "text-muted-foreground hover:text-primary"
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode("table")}
                className={`px-3 py-1 text-xs font-semibold rounded-[4px] cursor-pointer transition-colors font-sans ${
                  viewMode === "table" ? "bg-card text-primary shadow-sm" : "text-muted-foreground hover:text-primary"
                }`}
              >
                Table
              </button>
            </div>

            <Link
              to="/jobs"
              className="text-xs font-medium text-primary underline decoration-1 underline-offset-4 cursor-pointer font-sans"
            >
              View all listings &rarr;
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 items-start">
            {Array.from({ length: 6 }).map((_, i) => (
              <JobCardSkeleton key={i} />
            ))}
          </div>
        ) : error ? (
          <JobsErrorState message={error} onRetry={onRetry} />
        ) : jobs.length > 0 ? (
          viewMode === "grid" ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 items-start">
              {jobs.map((job) => {
                const agencyDataObj = agenciesData.find((a) => a.short === job.agencyShort || a.name === job.agency);
                const portalUrl = job.officialUrl || (agencyDataObj ? agencyDataObj.recruitmentPortal : undefined);
                const isClosed = job.status === "closed";

                return (
                  <div
                    key={job.id}
                    className={`group flex flex-col justify-between rounded-[8px] border border-border bg-card p-5 sm:p-6 interactive-card ${
                      isClosed ? "opacity-65 bg-muted/5" : ""
                    }`}
                  >
                    <div className="space-y-4">
                      <div className="flex items-center justify-between gap-2 min-w-0">
                        <div className="flex items-center gap-2.5 min-w-0 flex-1">
                          <AgencyLogo short={job.agencyShort} size={32} className="shrink-0" />
                          <span className="font-semibold text-xs text-muted-foreground truncate min-w-0">
                            {job.agencyShort || job.agency}
                          </span>
                        </div>
                        <StatusBadge status={job.status} />
                      </div>

                      <div>
                        <h3 className="text-[16px] sm:text-[18px] font-semibold leading-snug text-foreground">
                          {job.title}
                        </h3>
                        <p className="mt-1 text-[13px] font-medium text-[#0a5c38] dark:text-[#3fb68e] hover:underline">
                          <Link to="/agencies/$agencyShort" params={{ agencyShort: job.agencyShort || job.agency || "NNPC" }}>
                            {job.agency}
                          </Link>
                        </p>
                      </div>

                      <div className="border-t border-border pt-4 grid grid-cols-1 xs:grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
                        <div>
                          <span className="block text-muted-foreground text-[12px]">Deadline</span>
                          <span className="font-medium text-foreground">{job.deadline}</span>
                        </div>
                        <div>
                          <span className="block text-muted-foreground text-[12px]">Positions</span>
                          <span className="font-medium text-foreground">{job.positions || "Multiple"}</span>
                        </div>
                        <div>
                          <span className="block text-muted-foreground text-[12px]">Published</span>
                          <span className="font-medium text-foreground">{job.detected}</span>
                        </div>
                        <div>
                          <span className="block text-muted-foreground text-[12px]">Verification</span>
                          <OfficialSourceLink url={portalUrl} agencyShort={job.agencyShort || job.agency} />
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 pt-3 flex justify-end">
                      <Link
                        to="/jobs/$jobId"
                        params={{ jobId: job.id }}
                        className="text-[13px] text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-semibold"
                      >
                        View details &rarr;
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-[8px] border border-border bg-card shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/10 text-xs font-semibold text-muted-foreground uppercase font-sans">
                    <th className="p-4">Position</th>
                    <th className="p-4">Agency</th>
                    <th className="p-4">Published</th>
                    <th className="p-4">Deadline</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-xs font-sans">
                  {jobs.map((job) => {
                    const agencyDataObj = agenciesData.find((a) => a.short === job.agencyShort);
                    const portalUrl = agencyDataObj ? agencyDataObj.recruitmentPortal : "#";
                    const isClosed = job.status === "closed";

                    return (
                      <tr
                        key={job.id}
                        className={`hover:bg-muted/5 transition-colors ${
                          isClosed ? "opacity-65 bg-muted/5" : ""
                        }`}
                      >
                        <td className="p-4 font-bold text-primary">
                          <Link to="/jobs/$jobId" params={{ jobId: job.id }} className="hover:underline">
                            {job.title}
                          </Link>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <AgencyLogo short={job.agencyShort} size={24} />
                            <span className="text-muted-foreground font-semibold">{job.agencyShort}</span>
                          </div>
                        </td>
                        <td className="p-4 text-foreground/80">{job.detected}</td>
                        <td className="p-4 text-foreground/80">{job.deadline}</td>
                        <td className="p-4">
                          <StatusBadge status={job.status} />
                        </td>
                        <td className="p-4 text-right space-x-3">
                          <OfficialSourceLink url={portalUrl} label="Source" />
                          <Link
                            to="/jobs/$jobId"
                            params={{ jobId: job.id }}
                            className="text-muted-foreground hover:text-primary font-semibold"
                          >
                            Details
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
        ) : (
          <JobsEmptyState searchQuery={searchQuery} onClear={hasFilters ? handleClearFilters : undefined} />
        )}
      </div>
    </section>
  );
}

function PortalHealth({ agencies }: { agencies: ApiAgency[] }) {
  return (
    <section id="health" className="py-8 sm:py-16 bg-background border-t border-border font-sans">
      <div className="mx-auto max-w-[1184px] px-4 sm:px-6">
        <div className="mb-8 flex flex-col justify-between gap-3 md:flex-row md:items-end">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-primary">Portal Availability</h2>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Reachability status of official Nigerian government recruitment portals.
            </p>
          </div>
          <Link
            to="/portals"
            className="text-xs font-semibold text-primary underline decoration-1 underline-offset-4 cursor-pointer"
          >
            View all 42 portals &rarr;
          </Link>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-4">
          {agencies.length === 0 ? (
            Array.from({ length: 8 }).map((_, idx) => (
              <div key={idx} className="rounded-[8px] border border-border bg-card p-5 space-y-4 animate-pulse">
                <div className="h-6 bg-muted rounded w-3/4" />
                <div className="h-4 bg-muted rounded w-1/2" />
                <div className="h-10 bg-muted rounded w-full" />
              </div>
            ))
          ) : (
            agencies.slice(0, 8).map((a) => {
              const activeCount = a.jobs_available;
              const isOnline = a.status === "online";
              const isMaintenance = a.status === "maintenance";

              const lastVerifiedDateText = a.last_checked
                ? new Date(a.last_checked).toLocaleDateString("en-GB", { day: 'numeric', month: 'short', year: 'numeric' })
                : "24 July 2026";

              return (
                <div
                  key={a.acronym}
                  className="rounded-[8px] border border-border bg-card p-5 flex flex-col justify-between space-y-4 interactive-card overflow-hidden"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-border/40 pb-3 gap-2">
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <AgencyLogo short={a.acronym} size={32} />
                        <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-muted-foreground truncate">
                          {a.acronym}
                        </span>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-[15px] sm:text-[16px] font-bold text-foreground break-words leading-tight">{a.name}</h3>
                      
                      {/* Reachability Indicator */}
                      <div className="flex items-center gap-1.5 mt-2 text-[12px] font-medium min-w-0">
                        <span style={{
                          width: 7,
                          height: 7,
                          borderRadius: '50%',
                          background: isOnline ? '#0a5c38' : isMaintenance ? '#b45309' : a.status === 'offline' ? '#b91c1c' : '#6b7280',
                          flexShrink: 0,
                          display: 'inline-block',
                        }} />
                        <span className="text-foreground font-semibold text-xs" title={isOnline ? "Online" : isMaintenance ? "Under Maintenance" : "Offline"}>
                          {isOnline ? "Online" : isMaintenance ? "Maintenance" : "Offline"}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2 text-xs border-t border-border/40 pt-3">
                      <div>
                        <span className="block text-muted-foreground text-[11px]">Recruitment Status</span>
                        {activeCount > 0 ? (
                          <span className="font-semibold text-[#0a5c38] dark:text-[#3fb68e]">
                            {activeCount} active {activeCount === 1 ? "opening" : "openings"}
                          </span>
                        ) : (
                          <span className="text-[11px] font-normal text-muted-foreground">
                            No current recruitment detected
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="block text-muted-foreground text-[11px]">Last Verified Listing</span>
                        <span className="font-medium text-foreground text-[11px]">{lastVerifiedDateText}</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border/40 flex items-center justify-between text-xs">
                    {a.portal_url ? (
                      <a
                        href={a.portal_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[#0a5c38] dark:text-[#3fb68e] underline hover:opacity-80 font-semibold truncate text-[12px]"
                      >
                        Visit Official Portal &rarr;
                      </a>
                    ) : (
                      <span className="text-muted-foreground text-[11px]">Official Portal</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
}

export function Index() {
  const [agencies, setAgencies] = useState<ApiAgency[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [status, setStatus] = useState<ApiSystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [agenciesRes, jobsRes, statusRes] = await Promise.all([
        api.getAgencies(),
        api.getJobs(),
        api.getSystemStatus(),
      ]);

      if (agenciesRes && agenciesRes.results) setAgencies(agenciesRes.results);
      if (jobsRes && jobsRes.results) {
        setJobs(
          jobsRes.results.map((j: ApiJob) => ({
            id: j.ref || (j as any).id,
            agency: j.agency_name,
            agencyShort: j.agency_acronym,
            title: j.title,
            deadline: j.deadline_display || (j.closing_date ? new Date(j.closing_date).toLocaleDateString() : "Open"),
            status: j.status as Status,
            detected: j.published_date || "Recently",
            category: j.category || "General",
            state: "Active",
            createdAt: j.published_date || "",
            positions: "Multiple",
            officialUrl: j.source_url,
          }))
        );
      }
      if (statusRes) setStatus(statusRes);
    } catch (err: any) {
      setError("Failed to connect to RecruitmentAlert servers. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTagClick = (tag: string) => {
    setSearchQuery(tag);
    document.getElementById("recruitments")?.scrollIntoView({ behavior: "smooth" });
  };

  const filteredJobs = jobs.filter((j) => {
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      j.title.toLowerCase().includes(q) ||
      j.agency.toLowerCase().includes(q) ||
      j.agencyShort.toLowerCase().includes(q) ||
      j.category.toLowerCase().includes(q);

    const matchesCategory = !selectedCategory || j.category.toLowerCase() === selectedCategory.toLowerCase();

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
      <SeoHead
        title="RecruitmentAlert: Verified Nigerian Federal Government Job Portal Monitor"
        description="Real-time verified recruitment intelligence across 41 Nigerian federal MDA portals (NNPC, Customs, EFCC, Police, Immigration, FIRS). Stop scams and find official job openings."
        canonicalUrl="/"
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="flex-1 w-full outline-none">
        <Hero searchQuery={searchQuery} setSearchQuery={setSearchQuery} onTagClick={handleTagClick} />
        <Stats status={status} />
        <LatestJobs
          jobs={filteredJobs}
          loading={loading}
          error={error}
          onRetry={loadData}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
        />
        <PortalHealth agencies={agencies} />
      </main>
      <Footer />
    </div>
  );
}
