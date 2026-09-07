import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Nav, Footer } from "../components/layout";

import { api, ApiSystemStatus, ApiAgency } from "../lib/api";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/status")({
  component: StatusPage,
});

function StatusPage() {
  const [status, setStatus] = useState<ApiSystemStatus | null>(null);
  const [agencies, setAgencies] = useState<ApiAgency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, agenciesRes] = await Promise.all([
        api.getSystemStatus(),
        api.getAgencies(),
      ]);
      if (statusRes) setStatus(statusRes);
      if (agenciesRes && agenciesRes.results) setAgencies(agenciesRes.results);
    } catch (err: any) {
      setError("Failed to fetch system health data from RecruitmentAlert API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);


  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans">
        <Nav />
        <main className="flex-1 flex flex-col items-center justify-center py-20 space-y-4">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#0a5c38] dark:border-[#3fb68e]"></div>
          <p className="text-sm font-medium text-muted-foreground">Loading system status...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !status) {
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
            <h3 className="text-lg font-bold text-primary">Status Offline</h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{error}</p>
          </div>
          <button
            onClick={loadData}
            className="w-full px-4 py-2 text-sm font-semibold text-white bg-[#0a5c38] dark:bg-[#3fb68e] rounded-[6px] hover:opacity-90 cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring"
          >
            Retry Connection
          </button>
        </main>
        <Footer />
      </div>
    );
  }

  const systemOperational = status.system_operational;

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
        "name": "System Status",
        "item": "https://www.recruitmentalert.com.ng/status"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between selection:bg-secondary/25 font-sans">
      <SeoHead
        title="Federal MDA Portal Status & Real-Time Server Uptime Monitor. RecruitmentAlert"
        description="Live reachability status of 42 Nigerian federal government recruitment portals. Check whether a specific agency portal is online before you visit."
        canonicalUrl="/status"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[1184px] px-6 py-10 space-y-8 font-sans outline-none">
        <div className="mb-4">
          <BackButton to="/" label="Back to Home" />
        </div>
        {/* Page Header */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between border-b border-border pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-primary md:text-3xl">System Status</h1>
            <p className="mt-1 text-sm text-muted-foreground font-sans">
              Real-time reachability status of Nigerian government recruitment portals.
            </p>
          </div>
        </div>

        {/* Global Operational Status Banner */}
        <div
          className={`rounded-[8px] border p-5 flex items-center gap-3 ${
            systemOperational
              ? "border-[#15803D]/20 bg-[#15803D]/5"
              : "border-amber-500/20 bg-amber-500/5"
          }`}
        >
          {systemOperational ? (
            /* Circled checkmark */
            <svg className="size-5 text-[#15803D] shrink-0" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="10" cy="10" r="8.5" />
              <path d="M6.5 10.25l2.5 2.5 4.5-5" />
            </svg>
          ) : (
            /* Triangle warning */
            <svg className="size-5 text-amber-600 dark:text-amber-400 shrink-0" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M2.5 16.5L10 3.5l7.5 13H2.5z" />
              <path d="M10 8.5v3M10 13.5h.01" />
            </svg>
          )}
          <div>
            <p className="text-sm font-semibold text-primary">
              {systemOperational ? "All portals reachable" : "Some portals are offline"}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {status.agencies_online} portals reachable online, {status.agencies_maintenance} under maintenance, {status.agencies_offline} offline.
            </p>
          </div>
        </div>

        {/* Portals List Table */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-primary">Agency Portal Status</h2>
          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            <div className="divide-y divide-border font-sans">
              {agencies.map((a) => {
                const isOnline = a.status === "online";
                const isMaintenance = a.status === "maintenance";

                return (
                  <div key={a.acronym} className="p-4 sm:p-6 space-y-3 overflow-hidden">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 min-w-0">
                      <div className="space-y-0.5 min-w-0 flex-1">
                        <h3 className="text-sm font-semibold text-primary truncate min-w-0">{a.name}</h3>
                        <p className="text-xs text-muted-foreground font-mono truncate min-w-0">{a.portal_url.replace("https://", "").replace("http://", "")}</p>
                      </div>
                      <div className="flex flex-wrap items-center gap-2.5 sm:gap-4 text-xs font-mono shrink-0 min-w-0 pt-1 sm:pt-0 border-t sm:border-t-0 border-border/40">
                        <span
                          className={`inline-flex items-center gap-1 font-semibold truncate max-w-[130px] sm:max-w-none shrink-0 ${
                            isOnline ? "text-[#15803D]" : isMaintenance ? "text-[#B45309]" : "text-[#64748B]"
                          }`}
                          title={isOnline ? "Operational" : isMaintenance ? "Maintenance" : "Offline"}
                        >
                          <span style={{
                            width: 5,
                            height: 5,
                            borderRadius: '50%',
                            background: isOnline ? '#15803D' : isMaintenance ? '#B45309' : '#64748B',
                            flexShrink: 0,
                            display: 'inline-block',
                          }} />
                          <span className="truncate">{isOnline ? "Reachable" : isMaintenance ? "Maintenance" : "Offline"}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Operational Guidelines Disclaimer */}
        <div className="rounded-[8px] border border-border bg-muted/20 p-5 space-y-2 flex items-start gap-4">
          {/* Clock icon : drawn */}
          <svg className="size-5 text-muted-foreground shrink-0 mt-0.5" fill="none" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="10" cy="10" r="8" />
            <path d="M10 6v4l2.5 2.5" />
          </svg>
          <div className="space-y-1">
            <h2 className="text-sm font-semibold text-primary font-sans">About this status page</h2>
            <p className="text-xs text-muted-foreground leading-relaxed font-sans">
              This page displays reachability status of official Nigerian government recruitment portals. A portal marked "Offline" indicates connection timeouts or DNS resolution issues detected during recent automated checks.
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
