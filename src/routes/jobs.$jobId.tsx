import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Nav, Footer, Divider } from "../components/layout";
import { StatusBadge, type Status } from "./index";
import { safeFormatDate, safeFormatDateTime, safeFormatTime } from "../lib/formatDate";
import { api, ApiJobDetail, isAuthenticated } from "../lib/api";
import { toast } from "sonner";
import { OfficialSourceLink } from "../components/OfficialSourceLink";
import { SeoHead } from "../components/SeoHead";
import { ArrowLeft, CheckCircle2, AlertTriangle, Bookmark, Check } from "lucide-react";

function renderFormattedDescription(rawText: string | undefined | null) {
  if (!rawText || !rawText.trim()) {
    return <p className="mt-4 text-sm text-muted-foreground leading-relaxed">No detailed description provided for this recruitment notice.</p>;
  }

  const cleanText = rawText.replace(/\\n/g, '\n').trim();

  if (cleanText.includes('\n\n')) {
    const paragraphs = cleanText.split('\n\n').filter(p => p.trim().length > 0);
    return (
      <div className="mt-4 space-y-4 text-[14px] leading-relaxed text-foreground/90 font-sans">
        {paragraphs.map((p, idx) => (
          <p key={idx}>{p.trim()}</p>
        ))}
      </div>
    );
  }

  return (
    <div className="mt-4 text-[14px] leading-relaxed text-foreground/90 font-sans">
      <p>{cleanText}</p>
    </div>
  );
}

export const Route = createFileRoute("/jobs/$jobId")({
  component: JobDetailPage,
});

function JobDetailPage() {
  const { jobId } = Route.useParams();
  const router = useRouter();
  const [job, setJob] = useState<ApiJobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleGoBack = () => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.history.back();
    } else {
      router.navigate({ to: "/jobs" });
    }
  };

  const fetchJobDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getJobDetail(jobId);
      if (data) {
        setJob(data);
        if (isAuthenticated()) {
          const savedJobs = await api.getSavedJobs();
          if (savedJobs && savedJobs.some((j: any) => j.ref === data.ref || j.id === data.id)) {
            setIsSaved(true);
          }
        }
      } else {
        setError("The requested recruitment listing could not be found or has been removed.");
      }
    } catch (err: any) {
      console.warn("Error fetching job detail:", err);
      setError("Failed to load recruitment details. Please check your network connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSave = async () => {
    if (!job) return;
    if (!isAuthenticated()) {
      toast.error("Please sign in to save job listings to your dashboard.");
      return;
    }

    setSaving(true);
    if (isSaved) {
      const success = await api.removeSavedJob(job.ref);
      if (success) {
        setIsSaved(false);
        toast.success("Job removed from saved listings.");
      } else {
        toast.error("Failed to remove saved job.");
      }
    } else {
      const success = await api.saveJob(job.ref);
      if (success) {
        setIsSaved(true);
        toast.success("Job saved to your dashboard!");
      } else {
        toast.error("Failed to save job.");
      }
    }
    setSaving(false);
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const currentViews = parseInt(sessionStorage.getItem("listing_views_count") || "0", 10);
      sessionStorage.setItem("listing_views_count", (currentViews + 1).toString());
    }
    fetchJobDetails();
  }, [jobId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
        <Nav />
        <main className="flex-1 mx-auto max-w-[1184px] w-full px-6 py-10 space-y-8">
          <div className="h-4 w-48 bg-muted rounded animate-pulse" />
          <div className="rounded-[8px] border border-border bg-card p-8 animate-pulse space-y-6">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-4">
                <div className="size-12 rounded-full bg-muted" />
                <div className="space-y-2">
                  <div className="h-6 w-64 bg-muted rounded" />
                  <div className="h-4 w-32 bg-muted rounded" />
                </div>
              </div>
              <div className="h-6 w-20 bg-muted rounded" />
            </div>
            <div className="h-20 bg-muted rounded" />
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
        <Nav />
        <main className="flex-1 mx-auto max-w-[500px] w-full px-6 py-16 text-center space-y-6">
          <div className="mx-auto grid size-12 place-items-center rounded-full bg-destructive/10 text-destructive">
            <svg className="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-bold text-primary">Listing Not Found</h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              {error || "The recruitment notice you are looking for is unavailable or has been removed."}
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              onClick={fetchJobDetails}
              className="flex-1 px-4 py-2 text-xs font-semibold text-white bg-[#0a5c38] dark:bg-[#3fb68e] dark:text-[#0c1015] rounded-[6px] hover:opacity-90 transition-opacity cursor-pointer font-sans shadow-sm"
            >
              Try Again
            </button>
            <Link
              to="/jobs"
              className="flex-1 inline-flex items-center justify-center border border-border bg-card rounded-[6px] px-4 py-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors font-sans"
            >
              Back to All Jobs
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const isClosed =
    job.status === "closed" ||
    (job.positions && job.positions.toLowerCase().includes("closed")) ||
    (job.title && job.title.toLowerCase().includes("closed")) ||
    (job.deadline && job.deadline.toLowerCase().includes("closed"));

  const displayStatus = (isClosed ? "closed" : job.status === "new_opening" ? "new" : job.status) as Status;

  // Breadcrumb short title: e.g. "INEC — Registration Closed" or "NPF — Police Constable Intake"
  const shortTitleSnippet = isClosed
    ? "Registration Closed"
    : job.title.length > 32
      ? `${job.title.slice(0, 32)}...`
      : job.title;

  const breadcrumbText = `${job.agency_acronym || "MDA"} — ${shortTitleSnippet}`;

  const pageTitle = `${job.title} (${job.agency_acronym || 'MDA'}). Verified Recruitment 2026 | RecruitmentAlert`;
  const pageDescription = `Verified recruitment notice: ${job.title} by ${job.agency_name} (${job.agency_acronym}). Official portal status, application deadline (${job.deadline || 'Pending'}), and verified direct apply endpoint.`;

  const jobPostingSchema = {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    "title": job.title,
    "description": job.description || pageDescription,
    "datePosted": job.published_at || new Date().toISOString(),
    "validThrough": job.deadline && job.deadline !== "Pending" ? job.deadline : undefined,
    "employmentType": "FULL_TIME",
    "hiringOrganization": {
      "@type": "GovernmentOrganization",
      "name": job.agency_name,
      "alternateName": job.agency_acronym,
      "sameAs": job.official_url || job.source_url || "https://www.recruitmentalert.com.ng"
    },
    "jobLocation": {
      "@type": "Place",
      "address": {
        "@type": "PostalAddress",
        "addressCountry": "NG",
        "addressRegion": job.location_state || "Federal"
      }
    }
  };

  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://www.recruitmentalert.com.ng"
      },
      {
        "@type": "ListItem",
        "position": 2,
        "name": "Jobs",
        "item": "https://www.recruitmentalert.com.ng/jobs"
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": breadcrumbText,
        "item": `https://www.recruitmentalert.com.ng/jobs/${job.ref}`
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <SeoHead
        title={pageTitle}
        description={pageDescription}
        canonicalUrl={`/jobs/${job.ref}`}
        jsonLd={[jobPostingSchema, breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[720px] px-4 sm:px-6 py-8 sm:py-12 outline-none font-sans">
        
        {/* Mobile Full Width & Desktop Back Link */}
        <div className="mb-3 w-full sm:w-auto flex justify-start">
          <button
            type="button"
            onClick={handleGoBack}
            className="w-full sm:w-auto inline-flex items-center justify-start gap-1.5 py-1 text-xs text-muted-foreground hover:text-foreground font-semibold font-mono hover:underline cursor-pointer group transition-colors select-none"
          >
            <ArrowLeft className="size-3.5 group-hover:-translate-x-0.5 transition-transform text-[#0a5c38] dark:text-[#3fb68e]" />
            <span>Back to Jobs</span>
          </button>
        </div>

        {/* Improved Breadcrumb: HOME -> JOBS -> Agency - Short Title */}
        <div className="mb-6 font-mono text-[11px] uppercase tracking-wide text-muted-foreground truncate">
          <Link to="/" className="hover:text-primary">HOME</Link> → <Link to="/jobs" className="hover:text-primary">JOBS</Link> → <span className="text-foreground font-semibold">{breadcrumbText}</span>
        </div>

        {/* Status Badge */}
        <div className="mb-4 inline-flex">
          <StatusBadge status={displayStatus} />
        </div>

        {/* Heading & Agency */}
        <h1 className="text-[22px] sm:text-[28px] font-bold leading-tight tracking-tight text-foreground">
          {job.title}
        </h1>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
          <Link
            to="/agencies/$agencyShort"
            params={{ agencyShort: job.agency_acronym || job.agency_slug || "" }}
            className="text-[15px] sm:text-[16px] font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline"
          >
            {job.agency_name}
          </Link>
          
          <div className="inline-flex items-center gap-2 rounded-[6px] border border-border bg-card px-3 py-1 text-xs font-semibold shrink-0">
            <span className="text-muted-foreground">Verification Score:</span>
            <span className="font-mono text-foreground font-bold">{job.confidence_score != null ? `${job.confidence_score}%` : "Not available"}</span>
          </div>
        </div>

        {/* Top Metadata Row */}
        <div className="mt-6 sm:mt-8 grid grid-cols-1 xs:grid-cols-2 gap-y-4 sm:gap-y-6 gap-x-4 text-[13px] sm:grid-cols-3">
          <div>
            <div className="font-mono text-[11px] uppercase text-muted-foreground">Deadline</div>
            <div className="mt-1 font-medium">{job.deadline || "Pending"}</div>
          </div>
          <div>
            <div className="font-mono text-[11px] uppercase text-muted-foreground">Official source</div>
            <OfficialSourceLink url={job.official_url} label={`${job.agency_acronym} Portal`} />
          </div>
          <div>
            <div className="font-mono text-[11px] uppercase text-muted-foreground">Category</div>
            <div className="mt-1 font-medium">{job.category}</div>
          </div>
          <div>
            <div className="font-mono text-[11px] uppercase text-muted-foreground">Location</div>
            <div className="mt-1 font-medium">{job.location_state}</div>
          </div>
          <div>
            <div className="font-mono text-[11px] uppercase text-muted-foreground">Positions</div>
            <div className="mt-1 font-medium">{job.positions || "Multiple"}</div>
          </div>
          <div>
            <div className="font-mono text-[11px] uppercase text-muted-foreground">Published</div>
            <div className="mt-1 font-medium">{safeFormatDate(job.published_at)}</div>
          </div>
        </div>

        <Divider />

        {/* VERIFICATION SECTION */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Verification</h2>
          
          {job.confidence_score != null ? (() => {
            const score = Math.max(0, Math.min(100, Math.round(job.confidence_score)));
            let barColor = "#10B981";
            if (score < 50) {
              barColor = "#EF4444";
            } else if (score < 80) {
              barColor = "#F59E0B";
            }

            return (
              <div className="mt-6">
                <div className="flex items-center justify-between text-[15px] font-medium max-w-[280px]">
                  <span>Verification Score:</span>
                  <span className="font-mono font-bold" style={{ color: barColor }}>
                    {job.confidence_score}%
                  </span>
                </div>
                <div className="mt-2 h-2 w-full max-w-[280px] overflow-hidden rounded bg-muted dark:bg-[#242c38]">
                  <div 
                    className="h-full transition-all duration-300" 
                    style={{ width: `${job.confidence_score}%`, backgroundColor: barColor }}
                  />
                </div>
              </div>
            );
          })() : <p className="mt-4 text-sm text-muted-foreground">Verification score unavailable.</p>}

          <div className="mt-6">
            <div className="text-[13px] font-semibold uppercase tracking-wider text-muted-foreground font-mono">
              Verification Factors:
            </div>
            <ul className="mt-3 space-y-2.5 text-[14px]">
              {job.confidence_factors?.map((factor, idx) => {
                // Task 5: Only use warning icon if factor actually failed. AI classification passed gets a green checkmark!
                const isPassing = factor.passed || factor.label.toLowerCase().includes("passed") || factor.label.toLowerCase().includes("real");
                
                return (
                  <li key={idx} className="flex items-center gap-2.5">
                    {isPassing ? (
                      <CheckCircle2 className="size-4 text-[#0a5c38] dark:text-[#3fb68e] shrink-0" />
                    ) : (
                      <AlertTriangle className="size-4 text-[#b45309] shrink-0" />
                    )}
                    <span className="text-foreground font-medium">{factor.label}</span>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="mt-6 flex flex-col gap-1">
            <div className="flex gap-2 text-[12px] min-w-0">
              <span className="text-muted-foreground shrink-0 font-mono">Source URL:</span>
              {job.source_url ? <a href={job.source_url} target="_blank" rel="noreferrer" className="font-mono text-[#0a5c38] dark:text-[#3fb68e] hover:underline break-all truncate">{job.source_url}</a> : <span className="font-mono text-muted-foreground">Not available</span>}
            </div>
            <div className="flex gap-2 text-[11px] text-muted-foreground">
              <span className="font-mono">Last monitored:</span>
              <span className="font-mono">
                {safeFormatDateTime(job.last_monitored, "Not available")}
              </span>
            </div>
          </div>
        </section>

        <Divider />

        {/* AUDIT LOG SECTION */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Detection Timeline</h2>
          {job.detection_timeline && job.detection_timeline.length > 0 ? <div className="mt-6 space-y-3">
            {job.detection_timeline?.map((log, idx) => {
              const isLast = idx === (job.detection_timeline?.length ?? 0) - 1;
              return (
                <div key={idx} className="flex gap-4">
                  <div className="w-[40px] shrink-0 font-mono text-[11px] text-muted-foreground pt-0.5">
                    {log.time}
                  </div>
                  <div className="relative pb-3 pl-4 border-l-2 border-border/60">
                    <div style={{
                      position: 'absolute',
                      left: -5,
                      top: 6,
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: isLast ? '#0a5c38' : '#6b7280',
                      flexShrink: 0,
                    }} />
                    <div className="text-[13px]">{log.event}</div>
                  </div>
                </div>
              );
            })}
          </div> : <p className="mt-4 text-sm text-muted-foreground">No detection timeline is available.</p>}
        </section>

        <Divider />

        {/* RECRUITMENT DETAILS SECTION */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Recruitment Details</h2>
          {renderFormattedDescription(job.description)}
          
          {job.requirements && job.requirements.length > 0 && (
            <>
              <h3 className="mt-6 text-[13px] font-semibold text-foreground">Requirements</h3>
              <ul className="mt-3 list-disc pl-5 space-y-2 text-[14px] text-muted-foreground">
                {job.requirements.map((req, idx) => (
                  <li key={idx}>{req}</li>
                ))}
              </ul>
            </>
          )}
          
          {/* Action Buttons Row */}
          <div className="mt-8 flex flex-col gap-2">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              {/* Task 1: Closed Recruitment Handling */}
              {isClosed ? (
                <button
                  disabled
                  className="inline-flex h-[44px] w-full sm:w-auto items-center justify-center rounded-[6px] bg-muted text-muted-foreground px-[20px] text-[14px] font-semibold border border-border cursor-not-allowed pointer-events-none select-none opacity-75"
                >
                  <span>Registration Closed</span>
                </button>
              ) : !job.official_url || job.official_url.trim() === "" || job.official_url.trim() === "#" ? (
                <button
                  disabled
                  title="Official direct portal URL is not provided in source notice"
                  className="inline-flex h-[44px] w-full sm:w-auto items-center justify-center gap-2 rounded-[6px] bg-muted text-muted-foreground px-[20px] text-[14px] font-semibold opacity-70 cursor-not-allowed border border-border font-sans"
                >
                  <span>No Direct Application Link Available</span>
                </button>
              ) : (
                <a
                  href={job.official_url.trim()}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-[44px] w-full sm:w-auto items-center justify-center gap-2 rounded-[6px] bg-[#15803D] hover:bg-[#15803D]/90 text-[#FFFFFF] px-[20px] text-[14px] font-semibold transition-colors cursor-pointer"
                >
                  <span>Apply on Official Portal</span>
                  <svg className="size-4 shrink-0" fill="none" viewBox="0 0 16 16" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M3 13 L13 3" />
                    <path d="M6 3h7v7" />
                  </svg>
                </a>
              )}

              {/* Get Alerts (Remains active) */}
              <a
                href={`https://t.me/govalerts_bot?start=watch_${job.ref}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-[44px] w-full sm:w-auto items-center justify-center gap-2 rounded-[6px] border border-[#15803D] text-[#15803D] hover:bg-[#15803D]/10 bg-transparent px-[20px] text-[14px] font-semibold transition-colors cursor-pointer font-sans"
              >
                <svg className="size-[16px] fill-current shrink-0" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.02-1.93 1.23-5.46 3.62-.51.35-.98.53-1.39.51-.46-.01-1.33-.26-1.99-.47-.8-.27-1.44-.41-1.39-.87.03-.24.35-.49.97-.75 3.79-1.65 6.32-2.73 7.57-3.26 3.61-1.53 4.36-1.8 4.85-1.8.11 0 .35.03.5.15.13.12.17.27.18.39-.01.08-.01.18-.02.26z" />
                </svg>
                <span>Get Alerts</span>
              </a>

              {/* Save Job (Remains active) */}
              <button
                onClick={handleToggleSave}
                disabled={saving}
                className={`inline-flex h-[44px] w-full sm:w-auto items-center justify-center gap-2 rounded-[6px] border px-[20px] text-[14px] font-semibold transition-colors cursor-pointer ${
                  isSaved
                    ? "bg-[#15803D]/10 border-[#15803D] text-[#15803D]"
                    : "border-border bg-card text-foreground hover:bg-muted"
                }`}
              >
                {isSaved ? (
                  <svg className="size-4 shrink-0" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <path d="M3 2a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v12.5l-5-3.5-5 3.5V2z" />
                    <path d="M5.5 7.5l1.5 1.5 3-3" stroke="white" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                  </svg>
                ) : (
                  <svg className="size-4 shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M3 2a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v12.5l-5-3.5-5 3.5V2z" />
                  </svg>
                )}
                <span>{saving ? "Updating..." : isSaved ? "Bookmarked" : "Save Job"}</span>
              </button>
            </div>

            {/* Note below button for closed recruitments */}
            {isClosed && (
              <p className="mt-2 text-xs text-muted-foreground font-sans italic">
                This recruitment window has closed. Monitor the portal for future openings.
              </p>
            )}
          </div>
        </section>

        <Divider />

        {/* PORTAL STATUS SECTION */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Portal Status</h2>
          <div className="mt-6 rounded-[8px] border border-border bg-card p-6">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center rounded bg-muted px-2 py-1 text-[11px] font-semibold font-mono uppercase tracking-wider text-foreground">
                {job.agency_acronym}
              </span>
              <span className={`flex items-center gap-1.5 text-[13px] font-medium ${
                job.portal_status === "online" ? "text-[#0a5c38] dark:text-[#3fb68e]" : job.portal_status === "maintenance" ? "text-[#b45309]" : job.portal_status === "offline" ? "text-[#b91c1c]" : "text-muted-foreground"
              }`}>
                <span style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: 'currentColor',
                  display: 'inline-block',
                  flexShrink: 0,
                }} />
                {job.portal_status === "online" ? "Online" : job.portal_status === "maintenance" ? "Maintenance" : job.portal_status === "offline" ? "Offline" : "Unknown"}
              </span>
            </div>
            
            <div className="mt-5 grid grid-cols-1 gap-y-3 sm:grid-cols-2 text-[13px]">
              <div className="flex gap-2">
                <span className="text-muted-foreground w-28 font-mono">Last checked:</span>
                <span className="font-mono">
                  ↺ {safeFormatTime(job.portal_last_checked, "Not available")}
                </span>
              </div>
              <div className="flex gap-2 items-center">
                <span className="text-muted-foreground w-28 font-mono">Response time:</span>
                {job.portal_response_dots != null ? (
                  <div className="inline-flex items-center gap-1.5">
                    <span
                      className="inline-flex items-center gap-1 text-[#0a5c38] dark:text-[#3fb68e] cursor-help"
                      title={
                        job.portal_response_dots === 3
                          ? "Fast (< 500ms server response time)"
                          : job.portal_response_dots === 2
                            ? "Medium (500ms – 1.5s server response time)"
                            : "Slow (> 1.5s server response time)"
                      }
                    >
                      {Array.from({ length: job.portal_response_dots }).map((_, i) => (
                        <span key={i}>●</span>
                      ))}
                      <span className="text-foreground ml-1 font-semibold">
                        {job.portal_response_dots === 3 ? "Fast" : job.portal_response_dots === 2 ? "Medium" : "Slow"}
                      </span>
                    </span>
                    <span className="text-[11px] text-muted-foreground font-mono bg-muted/60 px-1.5 py-0.5 rounded border border-border/50">
                      {job.portal_response_dots === 3 ? "(< 500ms)" : job.portal_response_dots === 2 ? "(500ms – 1.5s)" : "(> 1.5s)"}
                    </span>
                  </div>
                ) : <span className="text-muted-foreground font-mono">Not available</span>}
              </div>
              <div className="flex gap-2">
                <span className="text-muted-foreground w-28 font-mono">Portal uptime:</span>
                <span className="font-mono">{job.portal_uptime_percent != null ? `${job.portal_uptime_percent}%` : "Not available"}</span>
              </div>
            </div>
            
            <div className="mt-6">
              <Link
                to="/agencies/$agencyShort"
                params={{ agencyShort: job.agency_acronym || job.agency_slug || "" }}
                className="text-[13px] font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline"
              >
                View full agency profile →
              </Link>
            </div>
          </div>
        </section>

        <Divider />

        {/* RELATED RECRUITMENTS */}
        {job.related_jobs && job.related_jobs.length > 0 && (
          <section>
            <h2 className="text-[17px] font-semibold text-foreground">Other verified recruitments</h2>
            <div className="mt-6 flex overflow-x-auto pb-4 gap-5 md:grid md:grid-cols-2 md:overflow-visible">
              {job.related_jobs.map((simJob) => (
                <Link
                  key={simJob.ref}
                  to="/jobs/$jobId"
                  params={{ jobId: simJob.ref }}
                  className="interactive-card min-w-[280px] rounded-[8px] border border-border bg-card p-[24px] cursor-pointer flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="font-mono text-[11px] text-muted-foreground uppercase">REF: {simJob.ref}</div>
                      <StatusBadge status={(simJob.status === "new_opening" ? "new" : simJob.status) as Status} />
                    </div>
                    <h3 className="text-[17px] font-semibold text-foreground leading-snug">
                      {simJob.title}
                    </h3>
                    <div className="mt-2 text-[13px] font-medium text-[#0a5c38] dark:text-[#3fb68e]">
                      {simJob.agency_name}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

      </main>
      <Footer />
    </div>
  );
}
