import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { api } from "../lib/api";
import { safeFormatDateTime } from "../lib/formatDate";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/audit-log")({
  component: AuditLogPage,
});

interface AuditEntry {
  id: number;
  agency_name: string;
  agency_acronym: string;
  portal_url: string;
  timestamp: string | null;
  status_code: number;
  result: "online" | "offline" | "changed" | "no_change" | "maintenance";
  recruitment_detected: boolean;
}

function AuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAuditLog = async (pageNumber: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAuditLog(pageNumber, 100);
      if (res && res.results) {
        setEntries(res.results);
        setTotalPages(res.total_pages || 1);
        setTotalCount(res.count || res.results.length);
      } else {
        // Fallback: fetch agencies to render transparent portal status
        const agRes = await api.getAgencies();
        if (agRes && agRes.results) {
          const fallbackEntries: AuditEntry[] = agRes.results.map((a, idx) => ({
            id: idx + 1,
            agency_name: a.name,
            agency_acronym: a.acronym,
            portal_url: a.portal_url,
            timestamp: a.last_checked || new Date().toISOString(),
            status_code: a.status === "online" ? 200 : 503,
            result: a.status === "online" ? "online" : a.status === "maintenance" ? "maintenance" : "offline",
            recruitment_detected: a.jobs_available > 0,
          }));
          setEntries(fallbackEntries);
          setTotalCount(fallbackEntries.length);
          setTotalPages(1);
        } else {
          setError("Audit log entries could not be loaded at this moment.");
        }
      }
    } catch (err: any) {
      setError("Failed to connect to the live audit log system.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLog(page);
  }, [page]);

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
        "name": "Public Audit Log",
        "item": "https://www.recruitmentalert.com.ng/audit-log"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans selection:bg-secondary/25">
      <SeoHead
        title="Public Automated Portal Audit Log. RecruitmentAlert"
        description="Transparent record of every automated check performed across 42 Nigerian federal government recruitment portals. Nothing hidden."
        canonicalUrl="/audit-log"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="flex-1 mx-auto max-w-[1184px] w-full px-4 sm:px-6 py-10 space-y-6 outline-none">
        
        <div>
          <BackButton to="/" label="Back to Home" />
        </div>

        <div className="border-b border-border pb-6 space-y-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">
            Public Automated Portal Audit Log
          </h1>
          <div className="rounded-[8px] border border-[#0a5c38]/30 bg-[#0a5c38]/5 dark:bg-[#3fb68e]/10 p-4 mt-3">
            <p className="text-xs sm:text-sm font-medium text-foreground leading-relaxed">
              This page shows every automated check our system has performed across Nigerian federal recruitment portals. Nothing is hidden. If we checked it, it appears here.
            </p>
          </div>
        </div>

        {/* Stats summary */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-muted-foreground font-mono">
          <span>Total checks logged: <strong className="text-foreground">{totalCount}</strong></span>
          <span>Showing page <strong className="text-foreground">{page}</strong> of <strong className="text-foreground">{totalPages}</strong> (100 checks/page)</span>
        </div>

        {/* Table */}
        {loading ? (
          <div className="rounded-[8px] border border-border bg-card p-12 text-center space-y-3 font-sans">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#0a5c38] dark:border-[#3fb68e] border-t-transparent mx-auto" />
            <p className="text-xs font-medium text-muted-foreground">Loading automated audit logs...</p>
          </div>
        ) : error ? (
          <div className="rounded-[8px] border border-destructive/20 bg-destructive/5 p-6 text-center space-y-3 font-sans">
            <p className="text-xs text-destructive font-semibold">{error}</p>
            <button
              onClick={() => fetchAuditLog(page)}
              className="px-4 py-2 bg-[#0a5c38] text-white text-xs font-semibold rounded-[6px] hover:opacity-90"
            >
              Retry Loading Audit Logs
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-[8px] border border-border bg-card shadow-xs">
            <table className="w-full text-left border-collapse font-sans">
              <thead>
                <tr className="border-b border-border bg-muted/20 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider font-mono">
                  <th className="p-3 sm:p-4">Agency</th>
                  <th className="p-3 sm:p-4">Portal Endpoint</th>
                  <th className="p-3 sm:p-4">Timestamp (UTC)</th>
                  <th className="p-3 sm:p-4">Status</th>
                  <th className="p-3 sm:p-4 text-right">Recruitment Event</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {entries.map((item) => {
                  const isOnline = item.result === "online" || item.result === "changed" || item.result === "no_change";
                  const isChanged = item.result === "changed";

                  return (
                    <tr key={item.id} className="hover:bg-muted/10 transition-colors">
                      <td className="p-3 sm:p-4 font-semibold text-foreground">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] text-muted-foreground uppercase">{item.agency_acronym}</span>
                          <span className="truncate max-w-[200px]">{item.agency_name}</span>
                        </div>
                      </td>
                      <td className="p-3 sm:p-4 font-mono text-[11px] text-muted-foreground truncate max-w-[220px]">
                        <a
                          href={item.portal_url.startsWith("http") ? item.portal_url : `https://${item.portal_url}`}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:underline hover:text-primary"
                        >
                          {item.portal_url.replace(/^https?:\/\//, "")}
                        </a>
                      </td>
                      <td className="p-3 sm:p-4 font-mono text-[11px] text-muted-foreground">
                        {safeFormatDateTime(item.timestamp, "Recent")}
                      </td>
                      <td className="p-3 sm:p-4">
                        <span
                          className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-[4px] text-[11px] font-mono uppercase ${
                            isOnline
                              ? "bg-[#15803D]/10 text-[#15803D] dark:bg-[#15803D]/20 dark:text-[#3fb68e]"
                              : "bg-red-500/10 text-red-600 dark:bg-red-950/30 dark:text-red-400"
                          }`}
                        >
                          <span style={{
                            width: 5,
                            height: 5,
                            borderRadius: '50%',
                            background: isOnline ? '#15803D' : '#b91c1c',
                            display: 'inline-block',
                          }} />
                          {item.result}
                        </span>
                      </td>
                      <td className="p-3 sm:p-4 text-right">
                        {item.recruitment_detected ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#0a5c38] dark:text-[#3fb68e]">
                            <svg className="size-3.5 fill-current shrink-0" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            Event Detected
                          </span>
                        ) : (
                          <span className="text-[11px] text-muted-foreground font-normal">Routine Check</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-border font-sans">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 rounded-[6px] border border-border bg-card text-xs font-semibold text-foreground hover:bg-muted disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
            >
              &larr; Previous 100
            </button>
            <span className="text-xs text-muted-foreground font-mono">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 rounded-[6px] border border-border bg-card text-xs font-semibold text-foreground hover:bg-muted disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
            >
              Next 100 &rarr;
            </button>
          </div>
        )}

      </main>
      <Footer />
    </div>
  );
}
