import { createFileRoute, Link } from '@tanstack/react-router';
import { useState, useMemo, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { AgencyLogo } from "../components/AgencyLogo";
import { api, ApiAgency } from "../lib/api";
import { safeFormatTime } from "../lib/formatDate";
import { JobsErrorState, JobsEmptyState } from "./index";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/agencies/")({
  component: AgenciesIndexPage,
});

function VettedArc({ score }: { score: number }) {
  const radius = 10;
  const stroke = 2.5;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex items-center gap-1.5">
      <svg className="size-5 transform -rotate-90">
        <circle
          className="text-border"
          strokeWidth={stroke}
          fill="transparent"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          className="text-[#0a5c38] dark:text-[#3fb68e]"
          strokeWidth={stroke}
          strokeDasharray={circumference + " " + circumference}
          style={{ strokeDashoffset }}
          strokeLinecap="round"
          stroke="currentColor"
          fill="transparent"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
      </svg>
      <span className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wider">
        Vetted {score}%
      </span>
    </div>
  );
}

function AgenciesIndexPage() {
  const [search, setSearch] = useState("");
  const [status, setSearchStatus] = useState("");
  const [category, setCategory] = useState("");

  const [agencies, setAgencies] = useState<ApiAgency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgencies = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAgencies();
      if (res) {
        setAgencies(res.results);
      } else {
        setError("The agency directory is currently unavailable.");
      }
    } catch (err: any) {
      console.warn("Error fetching agencies:", err);
      setError("The agency directory is currently unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgencies();
  }, []);

  const categories = useMemo(() => {
    return Array.from(new Set(agencies.map((a) => a.category))).sort();
  }, [agencies]);

  const filteredAgencies = useMemo(() => {
    let result = [...agencies];

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (a) =>
          (a.name ? a.name.toLowerCase().includes(q) : false) ||
          (a.acronym ? a.acronym.toLowerCase().includes(q) : false) ||
          (a.description ? a.description.toLowerCase().includes(q) : false)
      );
    }

    if (status) {
      result = result.filter((a) => a.status === status);
    }

    if (category) {
      result = result.filter((a) => a.category === category);
    }

    return result;
  }, [search, status, category, agencies]);

  const handleClearFilters = () => {
    setSearch("");
    setSearchStatus("");
    setCategory("");
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
        "name": "Monitored Agencies",
        "item": "https://www.recruitmentalert.com.ng/agencies"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-secondary/25 font-sans">
      <SeoHead
        title="Nigerian Federal MDA Portal Directory — RecruitmentAlert"
        description="Verify official recruitment portal addresses for Nigerian federal ministries, departments, and agencies. Check uptime status and recruitment history."
        canonicalUrl="/agencies"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main className="mx-auto max-w-[1184px] px-6 py-12">
        <div className="mb-6">
          <BackButton to="/" label="Back to Home" />
        </div>
        {/* Header */}
        <div className="mb-10 text-left space-y-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[#0a5c38] dark:text-[#3fb68e] font-mono">
            <span className="relative flex h-2 w-2">
              <span className="pulsing-dot absolute inline-flex h-full w-full rounded-full bg-[#0a5c38] dark:bg-[#3fb68e] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0a5c38] dark:bg-[#3fb68e]"></span>
            </span>
            <span>{agencies.length} Monitored Federal Agencies</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-primary md:text-[32px] leading-tight">
            Federal MDAs & Portal Directories
          </h1>
          <p className="text-[15px] text-muted-foreground">
            Verify official recruitment portal addresses, check uptime status, and access recruitment history for Ministries, Departments, and Agencies in Nigeria.
          </p>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="mb-8 rounded-[8px] border border-border bg-card p-5 space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {/* Search input */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search by MDA name or acronym..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-[44px] w-full rounded-[6px] border border-border bg-background px-3 text-[14px] text-foreground outline-none placeholder:text-muted-foreground focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
              />
            </div>

            {/* Category Filter */}
            <div>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="h-[44px] w-full rounded-[6px] border border-border bg-background px-3 text-[14px] text-foreground outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e] cursor-pointer"
              >
                <option value="" className="bg-card text-foreground">All Categories ▾</option>
                {categories.map((c) => (
                  <option key={c} value={c} className="bg-card text-foreground">
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={status}
                onChange={(e) => setSearchStatus(e.target.value)}
                className="h-[44px] w-full rounded-[6px] border border-border bg-background px-3 text-[14px] text-foreground outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e] cursor-pointer"
              >
                <option value="" className="bg-card text-foreground">All Portal Statuses ▾</option>
                <option value="online" className="bg-card text-foreground">Online</option>
                <option value="maintenance" className="bg-card text-foreground">Maintenance</option>
                <option value="offline" className="bg-card text-foreground">Offline</option>
              </select>
            </div>
          </div>

          {/* Active Filters Clear Button */}
          {(search || status || category) && (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] text-muted-foreground self-center uppercase font-bold font-mono">Active filters:</span>
                {search && (
                  <span className="inline-flex items-center gap-1 rounded-[4px] bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/10 dark:text-[#3fb68e] px-2 py-0.5 text-xs font-semibold">
                    Search: {search}
                  </span>
                )}
                {category && (
                  <span className="inline-flex items-center gap-1 rounded-[4px] bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/10 dark:text-[#3fb68e] px-2 py-0.5 text-xs font-semibold">
                    Category: {category}
                  </span>
                )}
                {status && (
                  <span className="inline-flex items-center gap-1 rounded-[4px] bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/10 dark:text-[#3fb68e] px-2 py-0.5 text-xs font-semibold">
                    Portal: {status}
                  </span>
                )}
              </div>
              <button
                onClick={handleClearFilters}
                className="text-xs font-semibold text-muted-foreground hover:text-primary cursor-pointer"
              >
                Reset all filters
              </button>
            </div>
          )}
        </div>

        {/* Loading and Error States */}
        {loading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 my-8">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div key={idx} className="rounded-[8px] border border-border bg-card p-6 space-y-4 animate-pulse">
                <div className="flex justify-between items-center">
                  <div className="h-6 bg-muted rounded w-1/3" />
                  <div className="h-4 bg-muted rounded w-1/4" />
                </div>
                <div className="h-6 bg-muted rounded w-3/4" />
                <div className="h-4 bg-muted rounded w-full" />
                <div className="border-t border-border/40 pt-4 grid grid-cols-2 gap-4">
                  <div className="h-4 bg-muted rounded w-full" />
                  <div className="h-4 bg-muted rounded w-full" />
                </div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <JobsErrorState message={error} onRetry={fetchAgencies} />
        )}

        {!loading && !error && (
          <>
            {/* Results count */}
            <div className="mb-6 border-b border-border/40 pb-3 font-sans">
              <p className="text-[13px] text-muted-foreground">
                Monitoring <span className="font-semibold text-foreground font-mono">{filteredAgencies.length}</span> registered Federal MDAs
              </p>
            </div>

            {/* Grid Layout of Agencies */}
            {filteredAgencies.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {filteredAgencies.map((agency) => {
                  const normStatus = (agency.status || "").toLowerCase();
                  const isOnline = normStatus === "online";
                  const isMaintenance = normStatus === "maintenance" || normStatus === "captcha";

                  return (
                    <div
                      key={agency.acronym}
                      className="group flex flex-col justify-between overflow-hidden rounded-[8px] border border-border bg-card p-4 sm:p-5 interactive-card"
                    >
                      <div className="space-y-3 sm:space-y-4">
                        {/* Top Row: Acronym + Status Badge */}
                        <div className="flex items-center justify-between border-b border-border/40 pb-3 gap-2 min-w-0">
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            <AgencyLogo short={agency.acronym} url={agency.portal_url} size={32} className="shrink-0" />
                            <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-muted-foreground truncate min-w-0">
                              {agency.acronym}
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-1.5 text-[12px] font-medium font-sans shrink-0 min-w-0" title={isOnline ? "Online" : isMaintenance ? "Maintenance" : "Offline"}>
                            <span style={{
                              width: 6,
                              height: 6,
                              borderRadius: '50%',
                              background: isOnline ? '#0a5c38' : isMaintenance ? '#b45309' : '#b91c1c',
                              flexShrink: 0,
                              display: 'inline-block',
                            }} />
                            <span className="text-foreground font-semibold truncate max-w-[100px] xs:max-w-none">
                              {isOnline ? "Online" : isMaintenance ? "Maintenance" : "Offline"}
                            </span>
                          </div>
                        </div>

                        {/* Agency Info */}
                        <div>
                          <h3 className="text-[15px] sm:text-[16px] font-semibold text-foreground transition-colors group-hover:text-primary font-sans leading-snug">
                            {agency.name}
                          </h3>
                          {agency.description && agency.description.trim().length > 0 && (
                            <p className="mt-1.5 text-[12px] text-muted-foreground line-clamp-2 leading-relaxed font-sans">
                              {agency.description}
                            </p>
                          )}
                        </div>

                        {/* Metrics details */}
                        <div className="grid grid-cols-1 xs:grid-cols-2 gap-x-3 gap-y-2 border-t border-border pt-3 text-[12px] font-sans">
                          <div>
                            <span className="block text-muted-foreground text-[11px]">Active recruitments</span>
                            <span className="font-semibold text-foreground">{agency.jobs_available} active openings</span>
                          </div>
                          <div>
                            <span className="block text-muted-foreground text-[11px]">Vetted Score</span>
                            <span className="font-semibold text-foreground">{agency.vetted_score}% confidence</span>
                          </div>
                        </div>
                      </div>

                      {/* Footer */}
                      <div className="mt-4 sm:mt-6 flex items-center justify-between text-[11px] border-t border-border/40 pt-3 font-sans gap-2 flex-wrap xs:flex-nowrap">
                        <span className="font-mono text-muted-foreground truncate">
                          &thinsp;&thinsp;&#8635; Checked {safeFormatTime(agency.last_checked, "Never")}
                        </span>
                        <Link
                          to="/agencies/$agencyShort"
                          params={{ agencyShort: agency.slug || agency.acronym }}
                          className="font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-sans shrink-0 h-[36px] px-2 flex items-center justify-center rounded-[4px] bg-[#0a5c38]/10 dark:bg-[#3fb68e]/15 sm:bg-transparent sm:dark:bg-transparent sm:h-auto sm:px-0"
                        >
                          View profile &rarr;
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <JobsEmptyState onClear={handleClearFilters} />
            )}
          </>
        )}
      </main>
      <Footer />
    </div>
  );
}
