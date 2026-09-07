import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useMemo, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { AgencyLogo } from "../components/AgencyLogo";
import { StatusBadge, JobCardSkeleton, JobsEmptyState, JobsErrorState, type Job, type Status } from "./index";
import { api, ApiAgency, isAuthenticated } from "../lib/api";

import { toast } from "sonner";
import { OfficialSourceLink } from "../components/OfficialSourceLink";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/jobs/")({
  component: JobsPage,
});

function JobsPage() {
  const [search, setSearch] = useState("");
  const [agency, setAgency] = useState("");
  const [category, setCategory] = useState("");
  const [state, setState] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState<"recent" | "oldest" | "alpha" | "deadline">("recent");
  const [currentPage, setCurrentPage] = useState(1);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 640);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Responsive PAGE_SIZE: 12 on desktop, 8 on mobile
  const PAGE_SIZE = isMobile ? 8 : 12;

  const [jobs, setJobs] = useState<Job[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [savedRefMap, setSavedRefMap] = useState<Record<string, boolean>>({});
  const [agenciesList, setAgenciesList] = useState<ApiAgency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAgenciesAndSaved = async () => {
      try {
        const res = await api.getAgencies();
        if (res && res.results) {
          setAgenciesList(res.results);
        }
        if (isAuthenticated()) {
          const saved = await api.getSavedJobs();
          const map: Record<string, boolean> = {};
          saved.forEach((j) => {
            map[j.ref] = true;
          });
          setSavedRefMap(map);
        }
      } catch (e) {}
    };
    loadAgenciesAndSaved();
  }, []);

  const handleToggleBookmark = async (ref: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated()) {
      toast.error("Please sign in to save jobs!");
      return;
    }

    const isCurrentlySaved = !!savedRefMap[ref];
    // Optimistic update
    setSavedRefMap((prev) => ({ ...prev, [ref]: !isCurrentlySaved }));

    if (isCurrentlySaved) {
      const success = await api.removeSavedJob(ref);
      if (success) {
        toast.success("Job removed from saved listings.");
      } else {
        setSavedRefMap((prev) => ({ ...prev, [ref]: true }));
        toast.error("Failed to remove saved job.");
      }
    } else {
      const success = await api.saveJob(ref);
      if (success) {
        toast.success("Job saved to your dashboard!");
      } else {
        setSavedRefMap((prev) => ({ ...prev, [ref]: false }));
        toast.error("Failed to save job.");
      }
    }
  };

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getPublicJobs({
        search,
        agency,
        category,
        state,
        status,
        sortBy,
        page: currentPage,
        pageSize: PAGE_SIZE,
      });

      if (res && res.results) {
        const mapped: Job[] = res.results.map((item) => ({
          id: item.ref,
          title: item.title,
          agency: item.agency_name,
          agencyShort: item.agency_acronym,
          category: item.category,
          detected: item.detected_time,
          status: (item.status === "new_opening" ? "new" : item.status) as Status,
          deadline: item.deadline,
          positions: item.positions,
          locationState: item.location_state,
          officialUrl: item.official_url,
          trustScore: item.trust_score,
        }));
        setJobs(mapped);
        setTotalCount(res.count);
      } else {
        setError("Failed to fetch recruitment listings.");
      }
    } catch (err: any) {
      console.warn("Error loading jobs:", err);
      setError("Network connection issue while loading jobs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [search, agency, category, state, status, sortBy, currentPage, PAGE_SIZE]);

  // Reset to page 1 whenever filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [search, agency, category, state, status, sortBy]);

  const agencies = useMemo(() => {
    if (agenciesList.length > 0) {
      return Array.from(new Set(agenciesList.map((a) => a.acronym))).sort();
    }
    return Array.from(new Set(jobs.map((j) => j.agencyShort))).sort();
  }, [agenciesList, jobs]);

  const states = useMemo(() => {
    return Array.from(new Set(jobs.map((j) => j.locationState))).filter(Boolean).sort();
  }, [jobs]);

  const categoriesList = useMemo(() => {
    return [
      "Security and Law Enforcement",
      "Finance and Revenue",
      "Education",
      "Health",
      "Transport and Infrastructure",
      "Civil Service",
      "Energy and Resources",
    ];
  }, []);

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    if (typeof window !== "undefined") {
      const gridEl = document.getElementById("jobs-feed-grid");
      if (gridEl) {
        gridEl.scrollIntoView({ behavior: "smooth", block: "start" });
      } else {
        window.scrollTo({ top: 250, behavior: "smooth" });
      }
    }
  };

  const handleClearFilters = () => {
    setSearch("");
    setAgency("");
    setCategory("");
    setState("");
    setStatus("");
    setCurrentPage(1);
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
        "name": "Verified Federal Government Job Openings",
        "item": "https://www.recruitmentalert.com.ng/jobs"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-secondary/25 font-sans">
      <SeoHead
        title="Federal Government Job Openings Nigeria 2026 — RecruitmentAlert"
        description="Browse verified Nigerian federal government recruitment openings from 42 official MDA portals. Updated in real time."
        canonicalUrl="/jobs"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[1184px] px-4 sm:px-6 py-8 sm:py-12 outline-none">
        
        {/* Mobile Full Width & Desktop Back Link */}
        <div className="mb-4 w-full sm:w-auto flex justify-start">
          <BackButton to="/" label="Back to Home" />
        </div>

        {/* Header */}
        <div className="mb-8 text-left space-y-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground font-mono">
            <span className="relative flex h-2 w-2">
              <span className="pulsing-dot absolute inline-flex h-full w-full rounded-full bg-[#0a5c38] dark:bg-[#3fb68e] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0a5c38] dark:bg-[#3fb68e]"></span>
            </span>
            <span>Live Official Portal Feed</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-primary md:text-[32px] leading-tight">
            Federal Recruitments Feed
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground max-w-2xl font-sans leading-relaxed">
            Live, continuously audited job postings from official Nigerian MDA portals. Filter by agency, sector category, or application status.
          </p>
        </div>

        {/* Search & Filter Controls Panel */}
        <div className="mb-8 rounded-[8px] border border-border bg-card p-4 sm:p-6 space-y-4 shadow-xs">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              <input
                type="text"
                placeholder="Search job title, keywords, or agency..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-[6px] border border-border bg-background py-2 pl-9 pr-3 text-xs sm:text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-[#0a5c38] dark:focus:border-[#3fb68e] transition-colors"
              />
            </div>
          </div>

          {/* Filter Dropdowns Grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 font-sans text-xs">
            <select
              value={agency}
              onChange={(e) => setAgency(e.target.value)}
              className="rounded-[6px] border border-border bg-background p-2 text-foreground outline-none cursor-pointer focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
            >
              <option value="">All Agencies</option>
              {agencies.map((acronym) => (
                <option key={acronym} value={acronym}>{acronym}</option>
              ))}
            </select>

            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="rounded-[6px] border border-border bg-background p-2 text-foreground outline-none cursor-pointer focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
            >
              <option value="">All Categories</option>
              {categoriesList.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="rounded-[6px] border border-border bg-background p-2 text-foreground outline-none cursor-pointer focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
            >
              <option value="">All Locations</option>
              {states.map((st) => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>

            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="rounded-[6px] border border-border bg-background p-2 text-foreground outline-none cursor-pointer focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
            >
              <option value="">All Statuses</option>
              <option value="new_opening">New Opening</option>
              <option value="verified">Verified Active</option>
              <option value="closing_soon">Closing Soon</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Listings Section Anchor */}
        <div id="jobs-feed-grid">
          {loading ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, idx) => (
                <JobCardSkeleton key={idx} />
              ))}
            </div>
          ) : error ? (
            <JobsErrorState onRetry={fetchJobs} />
          ) : (
            <div className="space-y-6">
              {/* Header & Sort Bar */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center justify-between border-b border-border pb-4 font-sans text-xs">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-muted-foreground">
                    Showing <strong className="text-foreground">{jobs.length}</strong> of <strong className="text-foreground">{totalCount}</strong> listings
                  </span>
                  {(search || agency || category || state || status) && (
                    <button
                      onClick={handleClearFilters}
                      className="text-xs font-semibold text-destructive hover:underline cursor-pointer font-mono"
                    >
                      Reset Filters
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-xs">Sort:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="bg-card border border-border rounded-[6px] px-2 py-1 text-xs font-semibold text-foreground outline-none cursor-pointer font-sans"
                  >
                    <option value="recent" className="bg-card text-foreground">Recently Detected &darr;</option>
                    <option value="oldest" className="bg-card text-foreground">Oldest First</option>
                    <option value="alpha" className="bg-card text-foreground">Alphabetical (A-Z)</option>
                    <option value="deadline" className="bg-card text-foreground">Nearest Deadline</option>
                  </select>
                </div>
              </div>

              {/* Job Listings Grid */}
              {jobs.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {jobs.map((job) => {
                    const portalUrl = job.officialUrl || "";
                    const isClosed = job.status === "closed";

                    return (
                      <div
                        key={job.id}
                        className={`group flex flex-col justify-between rounded-[8px] border border-border bg-card p-4 sm:p-6 interactive-card ${
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
                              <OfficialSourceLink url={portalUrl} />
                            </div>
                          </div>
                        </div>

                        <div className="mt-6 pt-3 flex items-center justify-between gap-3 border-t border-border/40">
                          <button
                            onClick={(e) => handleToggleBookmark(job.id, e)}
                            aria-label={`${savedRefMap[job.id] ? "Unsave" : "Save"} ${job.title}`}
                            className={`inline-flex items-center gap-1.5 h-[44px] px-3 rounded-[6px] text-[13px] font-semibold transition-colors cursor-pointer font-sans shrink-0 ${
                              savedRefMap[job.id]
                                ? "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e]"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                            }`}
                          >
                            {savedRefMap[job.id] ? (
                              <svg className="size-4 shrink-0" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                                <path d="M3 2a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v12.5l-5-3.5-5 3.5V2z" />
                                <path d="M5.5 7.5l1.5 1.5 3-3" stroke="white" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                              </svg>
                            ) : (
                              <svg className="size-4 shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                <path d="M3 2a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v12.5l-5-3.5-5 3.5V2z" />
                              </svg>
                            )}
                            <span>{savedRefMap[job.id] ? "Saved" : "Save"}</span>
                          </button>

                          <Link
                            to="/jobs/$jobId"
                            params={{ jobId: job.id }}
                            aria-label={`View details for ${job.title} (${job.agencyShort})`}
                            className="inline-flex items-center justify-center h-[44px] px-4 rounded-[6px] bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] hover:bg-[#0a5c38] hover:text-white dark:hover:bg-[#3fb68e] dark:hover:text-[#0c1015] text-[13px] font-semibold transition-colors font-sans"
                          >
                            View details &rarr;
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <JobsEmptyState searchQuery={search} onClear={handleClearFilters} />
              )}

              {/* Task 4: Responsive Mobile & Desktop Pagination Controls */}
              {totalPages > 1 && (
                <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border pt-8 font-sans">
                  
                  {/* Previous Button */}
                  <button
                    disabled={currentPage === 1}
                    onClick={() => handlePageChange(Math.max(currentPage - 1, 1))}
                    className="inline-flex h-[42px] w-full sm:w-auto px-5 items-center justify-center rounded-[6px] border border-border bg-card text-xs font-semibold text-foreground hover:bg-muted disabled:opacity-40 disabled:pointer-events-none cursor-pointer transition-colors shadow-2xs"
                  >
                    ← Previous
                  </button>

                  {/* Desktop Page Numbers Enumeration vs Mobile Simple Indicator */}
                  {isMobile ? (
                    <span className="text-xs text-muted-foreground font-mono font-semibold">
                      Page {currentPage} of {totalPages}
                    </span>
                  ) : (
                    <div className="flex items-center gap-1.5">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`size-9 rounded-[6px] text-xs font-mono font-bold transition-colors cursor-pointer ${
                            currentPage === pageNum
                              ? "bg-[#0a5c38] text-white dark:bg-[#3fb68e] dark:text-[#0c1015] shadow-xs"
                              : "bg-card border border-border text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        >
                          {pageNum}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Next Button */}
                  <button
                    disabled={currentPage === totalPages}
                    onClick={() => handlePageChange(Math.min(currentPage + 1, totalPages))}
                    className="inline-flex h-[42px] w-full sm:w-auto px-5 items-center justify-center rounded-[6px] border border-border bg-card text-xs font-semibold text-foreground hover:bg-muted disabled:opacity-40 disabled:pointer-events-none cursor-pointer transition-colors shadow-2xs"
                  >
                    Next →
                  </button>

                </div>
              )}
            </div>
          )}
        </div>

      </main>
      <Footer />
    </div>
  );
}
