import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect, useMemo } from "react";
import { Nav, Footer } from "../components/layout";
import { AgencyLogo } from "../components/AgencyLogo";
import { api, ApiAgency } from "../lib/api";
import { safeFormatDateTime } from "../lib/formatDate";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/portals")({
  component: PortalsDirectoryPage,
});

function PortalsDirectoryPage() {
  const [agencies, setAgencies] = useState<ApiAgency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>("");

  const loadPortals = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAgencies();
      if (res && res.results) {
        setAgencies(res.results);
        setLastRefreshedAt(new Date().toISOString());
      } else {
        setError("Unable to retrieve official portal registry at this time.");
      }
    } catch (err: any) {
      setError("Failed to fetch portal registry from monitoring service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortals();

    // Auto-refresh every 15 minutes (matching 15m cycle)
    const timer = setInterval(() => {
      loadPortals();
    }, 15 * 60 * 1000);

    return () => clearInterval(timer);
  }, []);

  // Alphabetically sorted agencies by agency name
  const sortedAgencies = useMemo(() => {
    return [...agencies].sort((a, b) => a.name.localeCompare(b.name));
  }, [agencies]);

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
        "name": "Monitored Portals Directory",
        "item": "https://www.recruitmentalert.com.ng/portals"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans selection:bg-secondary/25">
      <SeoHead
        title="Verified Federal Government Recruitment Portals Directory 2026. RecruitmentAlert"
        description="Official list of 42 Nigerian federal MDA recruitment portal addresses, reachability status, and live check timestamps. Updated every 15 minutes."
        canonicalUrl="/portals"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="flex-1 mx-auto max-w-[1184px] w-full px-4 sm:px-6 py-10 space-y-6 outline-none">
        
        <div>
          <BackButton to="/" label="Back to Home" />
        </div>

        {/* Header Section */}
        <div className="border-b border-border pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">
              Monitored Federal MDA Portals
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground max-w-2xl font-sans leading-relaxed">
              Every official Nigerian federal agency recruitment portal continuously monitored for reachability, verified notices, and hiring campaign releases.
            </p>
          </div>

        </div>

        {/* Directory Table */}
        {loading ? (
          <div className="rounded-[8px] border border-border bg-card p-12 text-center space-y-3 font-sans">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#0a5c38] dark:border-[#3fb68e] border-t-transparent mx-auto" />
            <p className="text-xs font-medium text-muted-foreground">Loading 42 federal portal endpoints...</p>
          </div>
        ) : error ? (
          <div className="rounded-[8px] border border-destructive/20 bg-destructive/5 p-6 text-center space-y-3 font-sans">
            <p className="text-xs text-destructive font-semibold">{error}</p>
            <button
              onClick={loadPortals}
              className="px-4 py-2 bg-[#0a5c38] text-white text-xs font-semibold rounded-[6px] hover:opacity-90"
            >
              Retry Connection
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-muted-foreground font-mono">
              <span>Total monitored endpoints: <strong className="text-foreground">{sortedAgencies.length}</strong></span>
              <Link to="/audit-log" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-semibold">
                View Live Audit Log &rarr;
              </Link>
            </div>

            <div className="overflow-x-auto rounded-[8px] border border-border bg-card shadow-xs">
              <table className="w-full text-left border-collapse font-sans">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider font-mono">
                    <th className="p-3 sm:p-4">Federal Agency Name</th>
                    <th className="p-3 sm:p-4">Official Portal URL</th>
                    <th className="p-3 sm:p-4">Reachability Status</th>
                    <th className="p-3 sm:p-4 text-right">Last Successful Check</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-xs">
                  {sortedAgencies.map((agency) => {
                    const normStatus = (agency.status || "").toLowerCase();
                    const isOnline = normStatus === "online";
                    const isMaintenance = normStatus === "maintenance" || normStatus === "captcha";
                    const portalUrlDisplay = agency.portal_url.replace(/^https?:\/\//, "");

                    return (
                      <tr key={agency.acronym} className="hover:bg-muted/10 transition-colors">
                        <td className="p-3 sm:p-4 font-semibold text-foreground">
                          <div className="flex items-center gap-2.5">
                            <AgencyLogo short={agency.acronym} url={agency.portal_url} size={28} className="shrink-0" />
                            <div className="min-w-0">
                              <Link
                                to="/agencies/$agencyShort"
                                params={{ agencyShort: agency.slug || agency.acronym }}
                                className="hover:underline hover:text-primary font-bold text-foreground block truncate"
                              >
                                {agency.name}
                              </Link>
                              <span className="font-mono text-[11px] text-muted-foreground uppercase">{agency.acronym}</span>
                            </div>
                          </div>
                        </td>

                        <td className="p-3 sm:p-4 font-mono text-[11px]">
                          <a
                            href={agency.portal_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline flex items-center gap-1 font-semibold truncate max-w-[240px]"
                            aria-label={`Official recruitment portal endpoint for ${agency.acronym}`}
                          >
                            <span>{portalUrlDisplay}</span>
                            <svg className="size-3 shrink-0" fill="none" viewBox="0 0 16 16" stroke="currentColor" strokeWidth="1.75">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13 L13 3 M6 3h7v7" />
                            </svg>
                          </a>
                        </td>

                        <td className="p-3 sm:p-4">
                          <span
                            className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-[4px] text-[11px] font-mono uppercase ${
                              isOnline
                                ? "bg-[#15803D]/10 text-[#15803D] dark:bg-[#15803D]/20 dark:text-[#3fb68e]"
                                : isMaintenance
                                ? "bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400"
                                : "bg-red-500/10 text-red-600 dark:bg-red-950/30 dark:text-red-400"
                            }`}
                          >
                            <span style={{
                              width: 6,
                              height: 6,
                              borderRadius: '50%',
                              background: isOnline ? '#15803D' : isMaintenance ? '#b45309' : '#b91c1c',
                              display: 'inline-block',
                            }} />
                            {isOnline ? "Online" : isMaintenance ? "Maintenance" : "Offline"}
                          </span>
                        </td>

                        <td className="p-3 sm:p-4 text-right font-mono text-[11px] text-muted-foreground">
                          {agency.last_checked ? safeFormatDateTime(agency.last_checked, "24 July 2026") : "24 July 2026"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="mt-8 border-t border-border pt-6 flex flex-wrap items-center justify-between gap-4 text-xs">
          <Link to="/agencies" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-semibold font-sans">
            &larr; Back to Agency Directory
          </Link>
          <Link to="/about" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-semibold font-sans">
            About RecruitmentAlert &rarr;
          </Link>
        </div>

      </main>
      <Footer />
    </div>
  );
}
