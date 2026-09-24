import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  CheckCircle,
  XCircle,
  RefreshCw,
  AlertTriangle,
  Send,
  Loader2,
  ExternalLink,
  PlusCircle,
  ShieldCheck,
  Building,
} from "lucide-react";

interface PendingJob {
  id: number;
  title: string;
  agency?: string | { name?: string; acronym?: string };
  agencyName?: string;
  agencyAcronym?: string;
  trustScore?: number;
  trust_score?: number;
  aiFlags?: string[] | string;
  aiRedFlags?: string[] | string;
  sourceUrl?: string;
  source_url?: string;
}

interface PortalError {
  id: number;
  name: string;
  url?: string;
  lastError?: string;
  error?: string;
  notes?: string;
  consecutiveFailures?: number;
  consecutive_failures?: number;
}

interface ManualJobForm {
  title: string;
  agencyId: string;
  positions: string;
  deadline: string;
  sourceUrl: string;
  rawText: string;
}

export default function AdminCrawlerDashboard() {
  const [tab, setTab] = useState<"review" | "manual" | "errors">("review");
  const [pendingJobs, setPendingJobs] = useState<PendingJob[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [reviewingId, setReviewingId] = useState<number | null>(null);

  const [form, setForm] = useState<ManualJobForm>({
    title: "",
    agencyId: "",
    positions: "",
    deadline: "",
    sourceUrl: "",
    rawText: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const [crawlerErrors, setCrawlerErrors] = useState<PortalError[]>([]);
  const [loadingErrors, setLoadingErrors] = useState(false);
  const [crawlingId, setCrawlingId] = useState<number | null>(null);

  const fetchPendingJobs = async () => {
    setLoadingJobs(true);
    try {
      const res = await fetch("/api/v1/admin/pending-jobs");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPendingJobs(Array.isArray(data) ? data : data.jobs || data.data || []);
    } catch (err: any) {
      toast.error("Failed to load pending jobs: " + err.message);
    } finally {
      setLoadingJobs(false);
    }
  };

  const fetchCrawlerErrors = async () => {
    setLoadingErrors(true);
    try {
      const res = await fetch("/api/v1/admin/crawler/errors");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCrawlerErrors(Array.isArray(data) ? data : data.portals || data.data || []);
    } catch (err: any) {
      toast.error("Failed to load crawler errors: " + err.message);
    } finally {
      setLoadingErrors(false);
    }
  };

  useEffect(() => {
    if (tab === "review") fetchPendingJobs();
    if (tab === "errors") fetchCrawlerErrors();
  }, [tab]);

  const handleReview = async (id: number, action: "approve" | "reject") => {
    setReviewingId(id);
    try {
      const res = await fetch(`/api/v1/admin/jobs/${id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      toast.success(
        action === "approve"
          ? "Job approved and broadcasted to Telegram!"
          : "Job alert rejected."
      );
      setPendingJobs((prev) => prev.filter((job) => job.id !== id));
    } catch (err: any) {
      toast.error(`Action failed: ${err.message}`);
    } finally {
      setReviewingId(null);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/admin/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          agencyId: Number(form.agencyId),
          status: "APPROVED",
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      toast.success("Verified circular posted and set to APPROVED!");
      setForm({ title: "", agencyId: "", positions: "", deadline: "", sourceUrl: "", rawText: "" });
    } catch (err: any) {
      toast.error(`Submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCrawlNow = async (portal: PortalError) => {
    setCrawlingId(portal.id);
    try {
      const res = await fetch(`/api/v1/admin/portals/${portal.id}/crawl`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      toast.success(`Crawl recheck initiated for ${portal.name}`);
      await fetchCrawlerErrors();
    } catch (err: any) {
      toast.error(`Crawl failed: ${err.message}`);
    } finally {
      setCrawlingId(null);
    }
  };

  const parseFlags = (flags?: string[] | string): string[] => {
    if (!flags) return [];
    if (Array.isArray(flags)) return flags;
    try {
      const parsed = JSON.parse(flags);
      return Array.isArray(parsed) ? parsed : [flags];
    } catch {
      return flags.split(",").map((s) => s.trim()).filter(Boolean);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-4 dark:border-neutral-800">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">Crawler Admin Dashboard</h1>
          <p className="text-sm text-neutral-500">RecruitmentAlert verification, manual entry & crawler health</p>
        </div>
        <div className="flex bg-neutral-100 dark:bg-neutral-800 p-1 rounded-xl gap-1">
          {[
            { id: "review", label: `Review Queue (${pendingJobs.length})` },
            { id: "manual", label: "Post Manual Job" },
            { id: "errors", label: `Crawler Errors (${crawlerErrors.length})` },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setTab(item.id as any)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${
                tab === item.id
                  ? "bg-white dark:bg-neutral-900 text-emerald-700 dark:text-emerald-400 shadow-sm"
                  : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* 1. Review Queue Tab */}
      {tab === "review" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-neutral-800 dark:text-neutral-200">Pending Job Alerts</h2>
            <button onClick={fetchPendingJobs} disabled={loadingJobs} className="text-sm flex items-center gap-1.5 text-emerald-600 hover:underline">
              <RefreshCw className={`w-3.5 h-3.5 ${loadingJobs ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
          {loadingJobs && (
            <div className="p-12 text-center text-neutral-500 flex justify-center items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-emerald-600" /> Loading pending alerts...
            </div>
          )}
          {!loadingJobs && pendingJobs.length === 0 && (
            <div className="p-12 text-center border rounded-2xl dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/40">
              <ShieldCheck className="w-12 h-12 text-emerald-600 mx-auto mb-2 opacity-80" />
              <p className="font-medium text-neutral-700 dark:text-neutral-300">All clear! No pending jobs awaiting approval.</p>
            </div>
          )}
          <div className="grid gap-4">
            {pendingJobs.map((job) => {
              const score = job.trustScore ?? job.trust_score ?? 50;
              const flags = parseFlags(job.aiFlags || job.aiRedFlags);
              const agency = typeof job.agency === "object" ? job.agency?.acronym || job.agency?.name : job.agency || job.agencyAcronym || job.agencyName || "Unknown Agency";
              const isWorking = reviewingId === job.id;

              return (
                <div key={job.id} className="p-4 border rounded-xl dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs px-2 py-0.5 rounded font-semibold bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 flex items-center gap-1">
                          <Building className="w-3 h-3" /> {agency}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${score >= 80 ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" : score >= 50 ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"}`}>
                          Trust: {score}%
                        </span>
                      </div>
                      <h3 className="font-semibold text-neutral-900 dark:text-neutral-100">{job.title}</h3>
                    </div>
                    {(job.sourceUrl || job.source_url) && (
                      <a href={job.sourceUrl || job.source_url} target="_blank" rel="noreferrer" className="text-xs text-neutral-500 hover:text-emerald-600 flex items-center gap-1">
                        Source <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  {flags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 items-center">
                      <span className="text-xs text-neutral-400 font-medium">AI Flags:</span>
                      {flags.map((f, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> {f}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex justify-end gap-2 pt-2 border-t dark:border-neutral-800">
                    <button
                      onClick={() => handleReview(job.id, "reject")}
                      disabled={isWorking}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-red-200 dark:border-red-900 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/50 flex items-center gap-1 disabled:opacity-50"
                    >
                      <XCircle className="w-3.5 h-3.5" /> Reject
                    </button>
                    <button
                      onClick={() => handleReview(job.id, "approve")}
                      disabled={isWorking}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1 shadow-sm disabled:opacity-50"
                    >
                      {isWorking ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                      Approve & Broadcast
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 2. Post Manual Job Tab */}
      {tab === "manual" && (
        <form onSubmit={handleManualSubmit} className="max-w-2xl bg-white dark:bg-neutral-900 border dark:border-neutral-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">Post Verified Circular</h2>
            <p className="text-xs text-neutral-500">Submitted directly to database with status=APPROVED.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium mb-1">Job Title *</label>
              <input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="e.g. 2026 Direct Short Service Cadets"
                className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Agency ID *</label>
              <input
                required
                type="number"
                value={form.agencyId}
                onChange={(e) => setForm({ ...form, agencyId: e.target.value })}
                placeholder="e.g. 1 (Customs), 2 (Immigration)"
                className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Deadline</label>
              <input
                type="date"
                value={form.deadline}
                onChange={(e) => setForm({ ...form, deadline: e.target.value })}
                className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium mb-1">Positions Available</label>
              <input
                value={form.positions}
                onChange={(e) => setForm({ ...form, positions: e.target.value })}
                placeholder="e.g. General Duty, Technical Officers, IT Cadre"
                className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium mb-1">Official Circular Source URL *</label>
              <input
                required
                type="url"
                value={form.sourceUrl}
                onChange={(e) => setForm({ ...form, sourceUrl: e.target.value })}
                placeholder="https://customs.gov.ng/careers/circular-2026.pdf"
                className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium mb-1">Raw Circular Text / Requirements *</label>
              <textarea
                required
                rows={5}
                value={form.rawText}
                onChange={(e) => setForm({ ...form, rawText: e.target.value })}
                placeholder="Paste the official circular text, qualifications, and application guidelines..."
                className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-800 dark:border-neutral-700"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 text-sm"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4" />}
            Publish Manual Job (APPROVED)
          </button>
        </form>
      )}

      {/* 3. Crawler Errors Tab */}
      {tab === "errors" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-neutral-800 dark:text-neutral-200">Failing Portals (Offline)</h2>
            <button onClick={fetchCrawlerErrors} disabled={loadingErrors} className="text-sm flex items-center gap-1.5 text-emerald-600 hover:underline">
              <RefreshCw className={`w-3.5 h-3.5 ${loadingErrors ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>

          {loadingErrors && (
            <div className="p-12 text-center text-neutral-500 flex justify-center items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-emerald-600" /> Checking crawler statuses...
            </div>
          )}

          {!loadingErrors && crawlerErrors.length === 0 && (
            <div className="p-12 text-center border rounded-2xl dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/40">
              <CheckCircle className="w-12 h-12 text-emerald-600 mx-auto mb-2 opacity-80" />
              <p className="font-medium text-neutral-700 dark:text-neutral-300">All 83 monitored portals are currently healthy!</p>
            </div>
          )}

          {!loadingErrors && crawlerErrors.length > 0 && (
            <div className="border dark:border-neutral-800 rounded-xl overflow-hidden bg-white dark:bg-neutral-900 shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-neutral-50 dark:bg-neutral-800/60 text-xs text-neutral-500 uppercase border-b dark:border-neutral-800">
                    <tr>
                      <th className="px-4 py-3">Portal Name</th>
                      <th className="px-4 py-3">Last Error</th>
                      <th className="px-4 py-3">Consecutive Failures</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y dark:divide-neutral-800">
                    {crawlerErrors.map((portal) => {
                      const failures = portal.consecutiveFailures ?? portal.consecutive_failures ?? 1;
                      const err = portal.lastError || portal.error || portal.notes || "Connection timeout / 5xx error";
                      const isCrawling = crawlingId === portal.id;

                      return (
                        <tr key={portal.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/40">
                          <td className="px-4 py-3">
                            <div className="font-medium text-neutral-900 dark:text-neutral-100">{portal.name}</div>
                            {portal.url && <div className="text-xs text-neutral-400 truncate max-w-xs">{portal.url}</div>}
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 px-2 py-1 rounded inline-block">
                              {err}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-semibold text-neutral-700 dark:text-neutral-300">
                            <span className="px-2 py-0.5 text-xs rounded bg-neutral-100 dark:bg-neutral-800">{failures} failures</span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleCrawlNow(portal)}
                              disabled={isCrawling}
                              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-neutral-900 hover:bg-neutral-800 dark:bg-neutral-100 dark:hover:bg-neutral-200 text-white dark:text-neutral-900 inline-flex items-center gap-1.5 transition-colors disabled:opacity-50"
                            >
                              <RefreshCw className={`w-3.5 h-3.5 ${isCrawling ? "animate-spin" : ""}`} />
                              Crawl Now
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
