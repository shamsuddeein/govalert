import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { StatusBadge, JobsEmptyState, type Status } from "./index";
import { api, ApiAgency } from "../lib/api";
import { safeFormatDate, safeFormatDateTime } from "../lib/formatDate";

import { OfficialSourceLink } from "../components/OfficialSourceLink";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/agencies/$agencyShort")({
  component: AgencyProfilePage,
});

function Divider() {
  return <div className="my-8 h-px w-full bg-border" />;
}

function AgencyProfilePage() {
  const { agencyShort } = Route.useParams();

  const [agency, setAgency] = useState<ApiAgency | null>(null);
  const [activeJobs, setActiveJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgencyData = async () => {
    setLoading(true);
    setError(null);
    const targetKey = agencyShort;
    if (!targetKey || targetKey === "undefined") {
      setError("This agency profile is unavailable.");
      setLoading(false);
      return;
    }
    try {
      const agencyData = await api.getAgency(targetKey);
      if (agencyData) {
        setAgency(agencyData);
        const jobsData = await api.getJobs({ agency: agencyData.acronym });
        if (jobsData && jobsData.results) {
          const mappedJobs = jobsData.results.map((j) => ({
            id: j.ref || (j as any).id,
            agencyShort: j.agency_acronym,
            title: j.title,
            deadline: j.deadline || "Pending",
            status: (j.status === "new_opening" ? "new" : j.status) as Status,
            detected: safeFormatDate(j.published_at),
            category: j.category,
            state: j.location_state,
            createdAt: j.published_at,
            positions: j.positions || "Multiple Positions",
          }));
          setActiveJobs(mappedJobs);
        } else {
          setActiveJobs([]);
        }
      } else {
        setError("This agency profile could not be retrieved from the monitoring service.");
      }
    } catch (err: any) {
      console.warn("Error fetching agency profile:", err);
      setError("This agency profile could not be retrieved from the monitoring service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgencyData();
  }, [agencyShort]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
        <Nav />
        <main className="mx-auto max-w-[720px] w-full px-6 py-12 space-y-6">
          <div className="h-6 bg-muted rounded w-1/4 animate-pulse" />
          <div className="h-8 bg-muted rounded w-1/2 animate-pulse" />
          <div className="h-16 bg-muted rounded w-full animate-pulse" />
          <div className="grid grid-cols-2 gap-4">
            <div className="h-10 bg-muted rounded w-full animate-pulse" />
            <div className="h-10 bg-muted rounded w-full animate-pulse" />
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !agency) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
        <Nav />
        <main className="flex-1 flex flex-col items-center justify-center py-20 px-6 max-w-md mx-auto text-center space-y-6">
          <div className="rounded-[8px] bg-red-100 dark:bg-red-950/50 p-4 text-red-600 dark:text-red-400">
            <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-bold text-primary">Agency Profile Unavailable</h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              {error || `The agency profile for "${agencyShort}" could not be found.`}
            </p>
          </div>
          <div className="flex gap-4 w-full">
            <button
              onClick={fetchAgencyData}
              className="flex-1 px-4 py-2 text-sm font-semibold text-white bg-[#0a5c38] dark:bg-[#3fb68e] rounded-[6px] hover:opacity-90 cursor-pointer"
            >
              Retry
            </button>
            <Link
              to="/agencies"
              className="flex-1 inline-flex items-center justify-center border border-border rounded-[6px] px-4 py-2 text-sm font-semibold hover:bg-muted"
            >
              Back to Directory
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const normStatus = (agency.status || "").toLowerCase();
  const isOnline = normStatus === "online";
  const isMaintenance = normStatus === "maintenance" || normStatus === "captcha";
  const portalStatusLabel = isOnline ? "Online" : isMaintenance ? "Maintenance" : normStatus === "offline" ? "Offline" : "Unknown";
  const portalUrlDisplay = agency.portal_url ? agency.portal_url.replace(/^https?:\/\//, "") : "";

  const totalChecksCount = agency.total_checks ?? (agency.last_10_checks ? agency.last_10_checks.length : 0);
  const checkCount = agency.last_10_checks ? agency.last_10_checks.length : 0;

  const uptimeFormatted = agency.uptime_percent != null
    ? (totalChecksCount > 0 && totalChecksCount < 20
        ? `${agency.uptime_percent}% (${totalChecksCount} check${totalChecksCount === 1 ? '' : 's'})`
        : `${agency.uptime_percent}%`)
    : "No checks recorded";

  const checksHeaderTitle = checkCount === 0
    ? "Recent checks"
    : checkCount < 10
      ? `Last ${checkCount} check${checkCount === 1 ? '' : 's'}`
      : "Last 10 checks";

  const fallbackDescription = `The ${agency.name} (${agency.acronym}) is a Nigerian federal ${agency.category || 'government'} institution monitored in real time by RecruitmentAlert. Job seekers can verify official portal endpoints, track historical hiring campaigns, and check portal availability to protect themselves against fraudulent recruitment scams.`;
  const agencyDescription = agency.description && agency.description.trim().length > 20 ? agency.description.trim() : fallbackDescription;

  const pageTitle = `${agency.acronym} Recruitment 2026: Verified Portal Status and History | RecruitmentAlert`;
  const pageMetaDescription = `Official recruitment portal status, uptime, and recruitment history for ${agency.name} (${agency.acronym}). Verify official .gov.ng portal link and active civil service openings.`;

  const govtOrgSchema = {
    "@context": "https://schema.org",
    "@type": "GovernmentOrganization",
    "name": agency.name,
    "alternateName": agency.acronym,
    "url": agency.portal_url || `https://www.recruitmentalert.com.ng/agencies/${agency.acronym.toLowerCase()}`,
    "description": agencyDescription,
    "sameAs": agency.portal_url || undefined
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
        "name": "Agencies",
        "item": "https://www.recruitmentalert.com.ng/agencies"
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": agency.acronym,
        "item": `https://www.recruitmentalert.com.ng/agencies/${agency.slug || agency.acronym.toLowerCase()}`
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <SeoHead
        title={pageTitle}
        description={pageMetaDescription}
        canonicalUrl={`/agencies/${agency.slug || agency.acronym.toLowerCase()}`}
        jsonLd={[govtOrgSchema, breadcrumbSchema]}
      />
      <Nav />
      <main className="mx-auto max-w-[720px] px-6 py-12">
        <div className="mb-4">
          <BackButton to="/agencies" label="Back to MDA Directory" />
        </div>
        {/* Breadcrumb */}
        <div className="mb-6 font-mono-ui text-[11px] uppercase tracking-wide text-muted-foreground">
          <Link to="/" className="hover:text-primary">Home</Link> → <Link to="/agencies" className="hover:text-primary">Agencies</Link> → {agency.acronym}
        </div>

        {/* Agency Header */}
        <div className="flex items-center gap-4">
          <span className="inline-flex items-center justify-center rounded bg-muted border border-border px-3 py-1 text-[18px] font-bold text-foreground font-sans">
            {agency.acronym}
          </span>
          <span className={`flex items-center gap-1.5 text-[14px] font-medium ${
            isOnline ? "text-[#0a5c38] dark:text-[#3fb68e]" : isMaintenance ? "text-[#b45309]" : normStatus === "offline" ? "text-[#b91c1c]" : "text-muted-foreground"
          }`}>
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'currentColor',
              display: 'inline-block',
              flexShrink: 0,
            }} />
            {portalStatusLabel}
          </span>
        </div>

        <h1 className="mt-4 text-[22px] sm:text-[28px] font-bold leading-tight tracking-tight text-foreground">
          {agency.name}
        </h1>
        <p className="mt-2 text-[14px] sm:text-[15px] leading-relaxed text-muted-foreground max-w-[600px]">
          {agencyDescription}
        </p>

        {/* Status Row */}
        <div className="mt-6 sm:mt-8 grid grid-cols-1 xs:grid-cols-2 gap-y-3 sm:gap-y-4 gap-x-4 text-[13px] sm:text-[14px] md:grid-cols-3">
          <div className="flex gap-2 min-w-0">
            <span className="text-muted-foreground w-24 shrink-0">Portal Status:</span>
            <span className="font-medium text-foreground truncate">{portalStatusLabel}</span>
          </div>
          <div className="flex gap-2 min-w-0">
            <span className="text-muted-foreground w-24 shrink-0">Total Campaigns:</span>
            <span className="font-medium text-foreground truncate">{agency.total_recruitments_detected ?? 0} recruitments</span>
          </div>
          <div className="flex gap-2 min-w-0">
            <span className="text-muted-foreground w-24 shrink-0">Last Verified:</span>
            <span className="font-medium text-foreground truncate">
              {agency.last_update ? safeFormatDate(agency.last_update, "24 July 2026") : "24 July 2026"}
            </span>
          </div>
        </div>

        {/* Official Portal Link */}
        <div className="mt-6">
          <OfficialSourceLink
            url={agency.portal_url}
            label={agency.portal_url ? portalUrlDisplay : "Official Portal"}
            className="text-[14px]"
          />
        </div>

        <Divider />

        {/* ACTIVE RECRUITMENTS */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Active Recruitments</h2>
          {activeJobs.length > 0 ? (
            <div className="mt-6 space-y-4">
              {activeJobs.map((job) => (
                <Link
                  key={job.id}
                  to="/jobs/$jobId"
                  params={{ jobId: job.id }}
                  className="interactive-card flex flex-col justify-between rounded-[8px] border border-border bg-card p-4 sm:p-[24px] cursor-pointer md:flex-row md:items-center"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-4 md:mb-2 md:justify-start md:gap-4 min-w-0">
                      <div className="font-mono-ui text-[11px] text-muted-foreground uppercase truncate">REF: {job.id}</div>
                      <StatusBadge status={job.status} />
                    </div>
                    <h3 className="text-[17px] font-semibold text-foreground leading-snug">
                      {job.title}
                    </h3>
                  </div>
                  <div className="mt-4 shrink-0 border-t border-border pt-4 md:mt-0 md:border-0 md:pt-0 md:pl-6 md:text-right">
                    <div className="font-mono-ui text-[11px] uppercase tracking-wide text-muted-foreground">Deadline</div>
                    <div className="mt-1 text-[13px] font-medium">{job.deadline}</div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="mt-6 flex flex-col items-center justify-center rounded-[8px] border border-border bg-card p-12 text-center">
              <svg className="size-[48px] text-muted-foreground mb-4" fill="none" stroke="currentColor" strokeWidth="1" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <h3 className="text-[17px] font-semibold text-foreground">No active recruitment detected</h3>
              <div className="mt-2 text-[14px] text-muted-foreground">Last checked: <span className="font-mono-ui">{safeFormatDateTime(agency.last_checked, "Not available")}</span></div>
              <p className="mt-4 text-[14px] text-muted-foreground">No active recruitment is currently available from this source.</p>
              <a
                href="https://t.me/govalerts_bot"
                target="_blank"
                rel="noreferrer"
                className="mt-6 inline-flex h-[44px] w-full sm:w-auto items-center justify-center rounded-[8px] border border-[#0a5c38] dark:border-[#3fb68e] bg-transparent px-[20px] text-[14px] font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:bg-[#0a5c38]/5 dark:hover:bg-[#3fb68e]/10 cursor-pointer"
              >
                Subscribe to alerts for this agency
              </a>
            </div>
          )}
        </section>

        <Divider />

        {/* RECRUITMENT HISTORY */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Recruitment History</h2>
          {agency.recruitment_history && agency.recruitment_history.length > 0 ? (
            <div className="mt-6 space-y-3">
              {agency.recruitment_history.map((hist, idx) => {
                return (
                  <div key={idx} className="flex gap-4">
                    <div className="w-[85px] shrink-0 font-mono-ui text-[11px] text-muted-foreground pt-0.5">
                      {safeFormatDate(hist.date)}
                    </div>
                    <div className="relative pb-4 pl-4 border-l border-border/60">
                      <div style={{
                        position: 'absolute',
                        left: -4.5,
                        top: 6,
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: idx === 0 ? '#0a5c38' : 'rgba(107,114,128,0.5)',
                        flexShrink: 0,
                      }} />
                      <div className="text-[14px] text-foreground">{hist.event_description}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground mt-4">No historical campaigns recorded.</p>
          )}
        </section>

        <Divider />

        {/* PORTAL HEALTH */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Portal Availability</h2>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <div className="text-[14px] text-muted-foreground">Reachable Status</div>
              <div className="mt-1 flex items-center gap-1.5 font-medium text-[14px]">
                <span style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: isOnline ? '#0a5c38' : isMaintenance ? '#b45309' : '#b91c1c',
                  display: 'inline-block',
                  flexShrink: 0,
                }} />
                <span>{portalStatusLabel}</span>
              </div>
            </div>
            <div>
              <div className="text-[14px] text-muted-foreground">Uptime</div>
              <div className="mt-1 font-mono-ui text-[14px] font-medium text-foreground">
                {uptimeFormatted}
              </div>
            </div>
            <div>
              <div className="text-[14px] text-muted-foreground">{checksHeaderTitle}</div>
              {checkCount > 0 ? (
                <div className="mt-1 flex items-center gap-1.5 font-mono-ui text-[#0a5c38] dark:text-[#3fb68e]">
                  {agency.last_10_checks!.map((chk, i) => (
                    <span key={i} className={chk ? "text-[#0a5c38] dark:text-[#3fb68e]" : "text-destructive"} title={chk ? "Check passed (200 OK)" : "Check failed / unreachable"}>
                      {chk ? "●" : "○"}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="mt-1 text-xs text-muted-foreground">No checks recorded yet</div>
              )}
            </div>
            <div>
              <div className="text-[14px] text-[#5a6370] dark:text-[#8b9aad]">Last offline</div>
              <div className="mt-1 font-mono-ui text-[13px] text-foreground">
                {agency.last_offline_at ? (
                  <>
                    {safeFormatDate(agency.last_offline_at)}{" "}
                    {agency.last_offline_duration_minutes ? (
                      <span className="text-muted-foreground">
                        (recovered in {agency.last_offline_duration_minutes} mins)
                      </span>
                    ) : (
                      ""
                    )}
                  </>
                ) : (
                  "Not available"
                )}
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-border/50 text-[12px] text-muted-foreground font-mono-ui flex items-center gap-1.5">
            <span>ℹ️</span>
            <span>
              {totalChecksCount === 0
                ? "Monitoring history is not available."
                : totalChecksCount < 20
                ? `Monitoring active. Based on initial sample of ${totalChecksCount} check${totalChecksCount === 1 ? '' : 's'}. History builds over time.`
                : `Monitoring active. Metrics computed across ${totalChecksCount} checks.`}
            </span>
          </div>
        </section>

        <Divider />

        {/* VERIFICATION TRACK RECORD */}
        <section>
          <h2 className="text-[17px] font-semibold text-foreground">Verification Track Record</h2>
          <div className="mt-6 grid grid-cols-1 gap-y-4 sm:grid-cols-2 text-[14px]">
            <div className="flex gap-2">
              <span className="text-muted-foreground w-48 shrink-0">Average confidence score:</span>
              <span className="font-semibold text-foreground">{agency.avg_confidence_score != null ? `${agency.avg_confidence_score}%` : "Not available"}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-48 shrink-0">Total announcements verified:</span>
              <span className="font-semibold text-foreground">{agency.total_recruitments_detected ?? 0}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-48 shrink-0">False positives detected:</span>
              <span className="font-semibold text-foreground">{agency.false_positives ?? 0}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-muted-foreground w-48 shrink-0">Scam domains blocked:</span>
              <span className="font-semibold text-foreground">{agency.scam_domains_blocked ?? 0}</span>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
