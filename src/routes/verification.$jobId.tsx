import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { Share2, CheckCircle2, AlertTriangle, XCircle, Check, ExternalLink } from "lucide-react";
import { BackButton } from "../components/BackButton";
import { toast } from "sonner";
import { api, ApiJobVerification } from "../lib/api";

export const Route = createFileRoute("/verification/$jobId")({
  component: VerificationReportPage,
  head: ({ params }) => {
    return {
      meta: [
        { title: `Verification Report: ${params.jobId} | RecruitmentAlert` }
      ],
    };
  }
});

function Divider() {
  return <div className="my-8 h-px w-full bg-border" />;
}

function VerificationReportPage() {
  const { jobId } = Route.useParams();

  const [report, setReport] = useState<ApiJobVerification | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getJobVerification(jobId);
      if (res) {
        setReport(res);
      } else {
        setError("Verification report not found or unavailable.");
      }
    } catch (err: any) {
      setError("Failed to fetch verification report from RecruitmentAlert API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [jobId]);

  const handleShare = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      toast.success("Report link copied to clipboard");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
        <Nav />
        <main className="flex-1 flex flex-col items-center justify-center py-20 space-y-4">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#0a5c38] dark:bg-[#3fb68e]"></div>
          <p className="text-sm font-medium text-muted-foreground">Loading verification report...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
        <Nav />
        <main className="flex-1 flex flex-col items-center justify-center py-20 px-6 max-w-md mx-auto text-center space-y-6">
          <div className="rounded-full bg-red-100 dark:bg-red-950/50 p-4 text-red-600 dark:text-red-400">
            <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-bold text-primary">Report Not Found</h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              {error || "The verification report you are looking for is unavailable."}
            </p>
          </div>
          <Link
            to="/jobs"
            className="w-full px-4 py-2 text-sm font-semibold text-white bg-[#0a5c38] dark:bg-[#3fb68e] rounded-[6px] hover:opacity-90 cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring inline-block"
          >
            Back to Jobs
          </Link>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Nav />
      <main className="mx-auto max-w-[720px] px-6 py-12 font-sans">
        <div className="mb-4">
          <BackButton to="/jobs/$jobId" params={{ jobId: report.ref }} label="Back to Job Details" />
        </div>
        {/* Breadcrumb */}
        <div className="mb-6 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
          <Link to="/" className="hover:text-primary">Home</Link> → <Link to="/jobs" className="hover:text-primary">Jobs</Link> → <Link to="/jobs/$jobId" params={{ jobId: report.ref }} className="hover:text-primary">{report.agency_acronym || 'Job Details'}</Link> → Verification Report
        </div>

        {/* Verification Status Badge */}
        <div className="mb-4">
          {report.ai_classification === "REAL" ? (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-[#0a5c38]/10 dark:bg-[#3fb68e]/10 text-[#0a5c38] dark:text-[#3fb68e] text-[12px] font-bold uppercase tracking-wide">
              <CheckCircle2 className="size-4" /> AUTHENTIC SOURCE. Confirmed Federal MDA Portal
            </span>
          ) : report.ai_classification === "FAKE" ? (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-red-100 dark:bg-red-950/30 text-red-700 dark:text-red-400 text-[12px] font-bold uppercase tracking-wide">
              <XCircle className="size-4" /> UNVERIFIED. Suspected fraudulent listing
            </span>
          ) : (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-amber-100 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 text-[12px] font-bold uppercase tracking-wide">
              <AlertTriangle className="size-4" /> UNDER REVIEW. Verification in progress
            </span>
          )}
        </div>

        <h1 className="text-[28px] font-bold leading-tight tracking-tight text-foreground">
          Verification Report
        </h1>
        <div className="mt-1 font-mono text-[13px] text-muted-foreground">
          {report.agency_acronym} — {report.job_title}
        </div>

        {/* Verification Overview */}
        <div className="mt-6 rounded-[8px] border border-border bg-card p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-sans text-[13px]">
            <div>
              <span className="block text-muted-foreground text-[12px]">Agency</span>
              <span className="font-medium mt-1 block">{report.agency_name} ({report.agency_acronym})</span>
            </div>
            <div>
              <span className="block text-muted-foreground text-[12px]">Verification Score</span>
              <span className="font-mono mt-1 block text-foreground font-bold">{report.ai_confidence != null ? `${report.ai_confidence}%` : "Not available"}</span>
            </div>
            <div>
              <span className="block text-muted-foreground text-[12px]">Report Reference</span>
              <span className="font-mono mt-1 block text-foreground">
                VR-{report.ref}
              </span>
            </div>
          </div>

          {/* Security Anomalies */}
          {report.ai_red_flags && report.ai_red_flags.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <span className="inline-flex items-center gap-1.5 text-[12px] font-bold text-red-600 dark:text-red-400 uppercase tracking-wide">
                <AlertTriangle className="size-3.5" aria-hidden />
                Security Anomalies Flagged
              </span>
              <ul className="mt-2 space-y-1">
                {report.ai_red_flags.map((flag, i) => (
                  <li key={i} className="text-[13px] text-red-700 dark:text-red-400 flex items-start gap-2">
                    <XCircle className="size-3.5 mt-0.5 shrink-0" />
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <Divider />

        {/* Audit Timeline */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Audit Timeline</h2>
          <div className="mt-6 space-y-3">
            {report.detection_timeline.length > 0 ? report.detection_timeline.map((log, idx, arr) => {
              const isLast = idx === arr.length - 1;
              return (
                <div key={idx} className="flex gap-4">
                  <div className="w-[40px] shrink-0 font-mono text-[11px] text-muted-foreground pt-0.5">
                    {log.time}
                  </div>
                  <div className="relative pb-3 pl-4 border-l-2 border-border/60">
                    <div className={"absolute -left-[5px] top-1.5 h-2 w-2 rounded-full " + (isLast ? "bg-[#0a5c38] dark:bg-[#3fb68e]" : "bg-muted-foreground")} />
                    <div className="text-[13px]">{log.event}</div>
                  </div>
                </div>
              );
            }) : <p className="text-sm text-muted-foreground">No audit events are available for this report.</p>}
          </div>
        </section>

        <Divider />

        {/* Verification Breakdown */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Verification Breakdown</h2>
          
          {report.confidence_score != null ? <div className="mt-6">
            <div className="text-[15px] font-medium">Verification Score: {report.confidence_score}%</div>
            <div className="mt-2 h-2 w-full max-w-[200px] overflow-hidden rounded bg-border">
              <div 
                className="h-full bg-[#0a5c38] dark:bg-[#3fb68e]" 
                style={{ width: `${report.confidence_score}%` }}
              />
            </div>
          </div> : <p className="mt-4 text-sm text-muted-foreground">Verification score unavailable.</p>}

          {report.confidence_factors.length > 0 ? <div className="mt-6">
            <div className="text-[15px] text-muted-foreground">Based on:</div>
            <ul className="mt-3 space-y-2 text-[14px]">
              {report.confidence_factors.map((factor, idx) => (
                <li key={idx} className="flex gap-2">
                  {factor.passed ? (
                    <Check className="size-4 mt-0.5 shrink-0 text-[#0a5c38] dark:text-[#3fb68e]" aria-hidden />
                  ) : (
                    <AlertTriangle className="size-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden />
                  )}
                  <span>{factor.label}</span>
                </li>
              ))}
            </ul>
          </div> : <p className="mt-6 text-sm text-muted-foreground">No verification factors are available.</p>}
        </section>

        <Divider />

        {/* Source evidence */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Source evidence</h2>
          <dl className="mt-6 space-y-4 text-[14px]">
            <div className="flex flex-col gap-1 sm:flex-row sm:gap-3">
              <dt className="w-32 shrink-0 text-muted-foreground">Source URL</dt>
              <dd>{report.source_url ? <a href={report.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 break-all text-primary hover:underline">{report.source_url}<ExternalLink className="size-3.5" /></a> : "Not available"}</dd>
            </div>
            <div className="flex flex-col gap-1 sm:flex-row sm:gap-3">
              <dt className="w-32 shrink-0 text-muted-foreground">Last monitored</dt>
              <dd>{report.last_monitored || "Not available"}</dd>
            </div>
          </dl>
        </section>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-wrap gap-4">
          <button
            onClick={handleShare}
            className="inline-flex h-[36px] items-center justify-center gap-2 rounded-[8px] border border-[#0a5c38] dark:border-[#3fb68e] bg-transparent px-[16px] text-[14px] font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:bg-[#0a5c38]/5 dark:hover:bg-[#3fb68e]/10 cursor-pointer animate-interactive"
          >
            <Share2 className="size-4" /> Share report
          </button>
        </div>
      </main>
      <Footer />
    </div>
  );
}
