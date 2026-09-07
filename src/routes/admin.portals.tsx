import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Globe,
  Plus,
  Play,
  History,
  Edit2,
  Trash2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  X,
  HelpCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  adminApi,
  AdminPortal,
  AdminAgency,
  AdminSnapshot,
} from "../lib/adminApi";
import { cn } from "../lib/utils";
import { AccessibleModal } from "../components/AccessibleModal";

export const Route = createFileRoute("/admin/portals")({
  component: AdminPortalsComponent,
});

function timeAgo(dateStr?: string | null): string {
  if (!dateStr) return "Never";
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// Strict Health Status Badge helper
function getHealthBadgeStyle(status?: string) {
  const norm = (status || "UNKNOWN").toUpperCase();

  if (norm === "ONLINE") {
    return {
      dotColor: "bg-[#166534]",
      badgeClass: "bg-[#DCFCE7] text-[#166534] border-[#166534]/20 font-semibold",
      label: "ONLINE",
    };
  }

  if (norm === "OFFLINE" || norm === "FAILING") {
    return {
      dotColor: "bg-[#991B1B]",
      badgeClass: "bg-[#FEE2E2] text-[#991B1B] border-[#991B1B]/20 font-semibold",
      label: norm === "FAILING" ? "FAILING" : "OFFLINE",
    };
  }

  if (norm === "CAPTCHA") {
    return {
      dotColor: "bg-[#92400E]",
      badgeClass: "bg-[#FEF3C7] text-[#92400E] border-[#92400E]/20 font-semibold",
      label: "CAPTCHA",
    };
  }

  if (norm === "BLOCKED" || norm === "FIREWALL BLOCKED" || norm === "FIREWALL_BLOCKED") {
    return {
      dotColor: "bg-[#6B21A8]",
      badgeClass: "bg-[#F3E8FF] text-[#6B21A8] border-[#6B21A8]/20 font-semibold",
      label: "FIREWALL BLOCKED",
    };
  }

  if (norm === "MAINTENANCE" || norm === "RATE_LIMITED") {
    return {
      dotColor: "bg-[#92400E]",
      badgeClass: "bg-[#FEF3C7] text-[#92400E] border-[#92400E]/20 font-semibold",
      label: norm === "MAINTENANCE" ? "MAINTENANCE" : "RATE LIMITED",
    };
  }

  return {
    dotColor: "bg-[#4B5563]",
    badgeClass: "bg-muted text-[#4B5563] border-border font-medium",
    label: norm || "UNKNOWN",
  };
}

function AdminPortalsComponent() {
  const [portals, setPortals] = useState<AdminPortal[]>([]);
  const [agencies, setAgencies] = useState<AdminAgency[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgency, setSelectedAgency] = useState("");
  const [healthStatus, setHealthStatus] = useState("");

  // Modals state
  const [selectedPortal, setSelectedPortal] = useState<AdminPortal | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [triggeringId, setTriggeringId] = useState<number | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pData, aData] = await Promise.all([
        adminApi.getPortals({ agency: selectedAgency, health_status: healthStatus }),
        adminApi.getAgencies(),
      ]);
      setPortals(pData);
      setAgencies(aData);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load portals.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedAgency, healthStatus]);

  const handleTriggerCheck = async (portalId: number, portalName: string) => {
    setTriggeringId(portalId);
    try {
      const res = await adminApi.triggerPortalCheck(portalId);
      if (res.has_change) {
        toast.warning(`Check complete for '${portalName}': Page CHANGE DETECTED ⚡`);
      } else {
        toast.success(`Check complete for '${portalName}': No change detected.`);
      }
      loadData();
    } catch (err: any) {
      toast.error(err?.message || `Scrape check error for '${portalName}'.`);
    } finally {
      setTriggeringId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans antialiased">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2.5">
            <Globe className="h-6 w-6 text-primary" />
            Portal Scraping Management
          </h1>
          <p className="text-xs text-muted-foreground mt-1 font-sans">
            Configure web scrapers, monitor consecutive failure thresholds, trigger on-demand checks, and inspect check histories.
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2.5 bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 text-white dark:text-[#0c1015] font-sans font-semibold text-xs rounded-[6px] transition-all flex items-center gap-2 shadow-sm cursor-pointer self-start md:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>Add Portal</span>
        </button>
      </div>

      {/* Filter Dropdowns */}
      <div className="flex flex-col md:flex-row items-center gap-3 bg-card p-3.5 rounded-[8px] border border-border">
        <div className="w-full md:w-72 font-sans">
          <select
            value={selectedAgency}
            onChange={(e) => setSelectedAgency(e.target.value)}
            className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-xs font-sans text-foreground focus:outline-none focus:border-primary"
          >
            <option value="">Filter by Agency (All)</option>
            {agencies.map((a) => (
              <option key={a.id} value={a.acronym}>
                {a.acronym} : {a.name}
              </option>
            ))}
          </select>
        </div>

        <div className="w-full md:w-64 font-sans">
          <select
            value={healthStatus}
            onChange={(e) => setHealthStatus(e.target.value)}
            className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-xs font-sans text-foreground focus:outline-none focus:border-primary"
          >
            <option value="">Filter by Health Status (All)</option>
            <option value="ONLINE">ONLINE (Green)</option>
            <option value="OFFLINE">OFFLINE (Red)</option>
            <option value="BLOCKED">BLOCKED (Amber)</option>
            <option value="CAPTCHA">CAPTCHA (Amber)</option>
            <option value="RATE_LIMITED">RATE LIMITED (Amber)</option>
            <option value="MAINTENANCE">MAINTENANCE (Amber)</option>
            <option value="UNKNOWN">UNKNOWN (Gray)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-3 font-sans">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-xs font-sans">Loading portal configurations...</span>
        </div>
      ) : portals.length === 0 ? (
        <div className="bg-card border border-border rounded-[8px] p-12 text-center text-muted-foreground text-xs font-sans">
          No portals found matching criteria.
        </div>
      ) : (
        <div className="bg-card border border-border rounded-[8px] overflow-hidden shadow-sm font-sans">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted border-b border-border text-muted-foreground font-sans font-semibold uppercase tracking-wider">
                <tr>
                  <th className="p-3.5">Agency</th>
                  <th className="p-3.5">Portal Name</th>
                  <th className="p-3.5">Target URL</th>
                  <th className="p-3.5">Health Status</th>
                  <th className="p-3.5">Priority</th>
                  <th className="p-3.5">Last Checked</th>
                  <th className="p-3.5">Failures</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-foreground">
                {portals.map((portal) => {
                  const badge = getHealthBadgeStyle(portal.health_status || portal.status);
                  const isHighFailure = portal.consecutive_failures > 3;

                  return (
                    <tr
                      key={portal.id}
                      onClick={() => setSelectedPortal(portal)}
                      className="hover:bg-muted/40 cursor-pointer transition-colors group"
                    >
                      <td className="p-3.5 font-mono font-bold text-primary group-hover:underline">
                        {portal.agency_acronym}
                      </td>
                      <td className="p-3.5 font-semibold text-foreground font-sans">{portal.name}</td>
                      <td className="p-3.5 font-mono text-muted-foreground max-w-xs truncate">
                        <span title={portal.url}>{portal.url}</span>
                      </td>
                      {/* STEP 5: Health Status Badge */}
                      <td className="p-3.5 font-sans">
                        <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-[6px] text-[11px] font-semibold uppercase tracking-wider border font-sans", badge.badgeClass)}>
                          <span className={cn("h-2 w-2 rounded-full shrink-0", badge.dotColor)} />
                          <span>{badge.label}</span>
                        </span>
                      </td>
                      <td className="p-3.5 font-sans">
                        <span className="px-2 py-0.5 rounded-[6px] bg-muted text-foreground border border-border font-semibold font-sans">
                          {portal.priority}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-muted-foreground">
                        {timeAgo(portal.last_checked_at)}
                      </td>
                      {/* STEP 5: Failure Badge */}
                      <td className="p-3.5 font-sans">
                        {isHighFailure ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-[6px] text-[11px] font-semibold uppercase tracking-wider bg-destructive/10 text-destructive border border-destructive/30 font-sans">
                            <AlertTriangle className="h-3 w-3 shrink-0" />
                            <span>{portal.consecutive_failures} Failing</span>
                          </span>
                        ) : portal.consecutive_failures > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-[6px] text-[11px] font-semibold uppercase tracking-wider bg-[color:var(--warning)]/10 text-[color:var(--warning)] border border-[color:var(--warning)]/30 font-sans">
                            <span>{portal.consecutive_failures} Failures</span>
                          </span>
                        ) : (
                          <span className="text-muted-foreground font-mono">0</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Portal Modal */}
      {isCreateModalOpen && (
        <PortalDetailFormModal
          portal={null}
          agencies={agencies}
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={() => {
            setIsCreateModalOpen(false);
            loadData();
          }}
        />
      )}

      {/* Row Click Portal Detail View Modal with "Check now" and 10-Check History Dots */}
      {selectedPortal && (
        <PortalDetailFormModal
          portal={selectedPortal}
          agencies={agencies}
          onClose={() => setSelectedPortal(null)}
          onSuccess={() => {
            setSelectedPortal(null);
            loadData();
          }}
          onTriggerCheck={(id, name) => handleTriggerCheck(id, name)}
          isTriggering={triggeringId === selectedPortal.id}
        />
      )}
    </div>
  );
}

// ─── Portal Detail & Form Modal Component ──────────────────────────────────────

function PortalDetailFormModal({
  portal,
  agencies,
  onClose,
  onSuccess,
  onTriggerCheck,
  isTriggering,
}: {
  portal: AdminPortal | null;
  agencies: AdminAgency[];
  onClose: () => void;
  onSuccess: () => void;
  onTriggerCheck?: (id: number, name: string) => void;
  isTriggering?: boolean;
}) {
  const [agencyId, setAgencyId] = useState(portal?.agency || (agencies[0]?.id ?? 1));
  const [name, setName] = useState(portal?.name || "");
  const [url, setUrl] = useState(portal?.url || "");
  const [scrapeMethod, setScrapeMethod] = useState(portal?.scrape_method || "REQUESTS");
  const [pollInterval, setPollInterval] = useState(portal?.poll_interval ?? 900);
  const [priority, setPriority] = useState(portal?.priority || "MEDIUM");
  const [isActive, setIsActive] = useState(portal?.is_active ?? true);
  const [notes, setNotes] = useState(portal?.notes || "");
  const [saving, setSaving] = useState(false);

  // 10-Check History Snapshots State
  const [snapshots, setSnapshots] = useState<AdminSnapshot[]>(portal?.recent_snapshots || []);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (portal) {
      const fetchHistory = async () => {
        setLoadingHistory(true);
        try {
          const history = await adminApi.getPortalHistory(portal.id);
          setSnapshots(history.slice(0, 10));
        } catch {
          // Silently handle history error
        } finally {
          setLoadingHistory(false);
        }
      };
      fetchHistory();
    }
  }, [portal?.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !url.trim()) {
      toast.error("Name and URL are required.");
      return;
    }

    setSaving(true);
    const payload = {
      agency: Number(agencyId),
      name: name.trim(),
      url: url.trim(),
      scrape_method: scrapeMethod,
      poll_interval: Number(pollInterval),
      priority,
      is_active: isActive,
      notes: notes.trim(),
    };

    try {
      if (portal) {
        await adminApi.updatePortal(portal.id, payload);
        toast.success(`Portal '${name}' updated.`);
      } else {
        await adminApi.createPortal(payload);
        toast.success(`Portal '${name}' created.`);
      }
      onSuccess();
    } catch (err: any) {
      toast.error(err?.message || "Failed to save portal.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async () => {
    if (!portal) return;
    if (!confirm(`Are you sure you want to deactivate portal '${portal.name}'?`)) return;
    try {
      await adminApi.deletePortal(portal.id);
      toast.success(`Portal '${portal.name}' deactivated.`);
      onSuccess();
    } catch (err: any) {
      toast.error(err?.message || "Failed to deactivate portal.");
    }
  };

  return (
    <AccessibleModal
      isOpen={true}
      onClose={onClose}
      title={portal ? `Portal Detail: ${portal.name}` : "Add New Scraper Portal"}
      description="Configure web scrapers, monitor consecutive failure thresholds, trigger on-demand checks, and inspect check histories."
      maxWidth="max-w-xl"
    >
      {/* 10-Check History Visualizer Dots (If editing existing portal) */}
      {portal && (
        <div className="bg-muted/40 p-4 rounded-[6px] border border-border space-y-2 font-sans mb-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-foreground font-sans">
              Last 10 Checks History (Hover dot for timestamp + latency):
            </span>
            {onTriggerCheck && (
              <button
                type="button"
                onClick={() => onTriggerCheck(portal.id, portal.name)}
                disabled={isTriggering}
                className="px-3 py-1 bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 disabled:opacity-50 text-white dark:text-[#0c1015] font-semibold rounded-[6px] text-[11px] flex items-center gap-1.5 transition-all cursor-pointer font-sans"
              >
                {isTriggering ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Play className="h-3 w-3 fill-current" />
                )}
                <span>Check now</span>
              </button>
            )}
          </div>

          {loadingHistory ? (
            <div className="flex items-center gap-2 text-muted-foreground py-1 text-[11px] font-sans">
              <Loader2 className="h-3 w-3 animate-spin text-primary" /> Loading check history...
            </div>
          ) : snapshots.length === 0 ? (
            <div className="text-muted-foreground py-1 text-[11px] font-sans">No check snapshots recorded yet.</div>
          ) : (
            <div className="flex items-center gap-3 pt-1 font-sans">
              {snapshots.map((snap) => {
                const isSuccess = snap.status_code && snap.status_code < 400;
                const timeText = new Date(snap.created_at || snap.timestamp).toLocaleString();
                const latencyText = snap.response_time_ms ? `${snap.response_time_ms}ms` : "no latency";

                return (
                  <div key={snap.id} className="relative group">
                    <div
                      className={cn(
                        "h-3.5 w-3.5 rounded-full border shadow-sm transition-transform group-hover:scale-125 cursor-pointer",
                        isSuccess
                          ? "bg-[#0a5c38] border-emerald-600 dark:border-emerald-400"
                          : "bg-destructive border-red-600 dark:border-red-400"
                      )}
                    />

                    {/* Tooltip on Hover */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 bg-card border border-border text-foreground px-2.5 py-1.5 rounded-[6px] shadow-sm whitespace-nowrap text-[10px] pointer-events-none font-sans">
                      <div className="font-bold text-primary">
                        {isSuccess ? `HTTP ${snap.status_code}` : `HTTP ${snap.status_code || "FAIL"}`}
                      </div>
                      <div className="text-muted-foreground font-mono">{timeText}</div>
                      <div className="text-muted-foreground font-mono">{latencyText}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Form Fields */}
      <form onSubmit={handleSubmit} className="space-y-4 font-sans text-xs">
        <div className="space-y-1">
          <label className="block font-sans text-muted-foreground font-semibold">Target Agency *</label>
          <select
            value={agencyId}
            onChange={(e) => setAgencyId(Number(e.target.value))}
            className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-sans focus:outline-none focus:border-primary"
          >
            {agencies.map((a) => (
              <option key={a.id} value={a.id}>
                {a.acronym} : {a.name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="block font-sans text-muted-foreground font-semibold">Portal Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. NCS Recruitment Portal"
            className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground focus:outline-none focus:border-primary font-sans"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="block font-sans text-muted-foreground font-semibold">Target Scrape URL *</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://customs.gov.ng/careers"
            className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-mono focus:outline-none focus:border-primary"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="block font-sans text-muted-foreground font-semibold">Scrape Method</label>
            <select
              value={scrapeMethod}
              onChange={(e) => setScrapeMethod(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-sans focus:outline-none focus:border-primary"
            >
              <option value="REQUESTS">HTTP Requests (BeautifulSoup)</option>
              <option value="PLAYWRIGHT">Headless Browser (Playwright)</option>
              <option value="PDF">PDF Parser</option>
              <option value="RSS">RSS Feed</option>
              <option value="API">REST API</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="block font-sans text-muted-foreground font-semibold">Priority Level</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-sans focus:outline-none focus:border-primary"
            >
              <option value="HIGH">HIGH (Fast Poll)</option>
              <option value="MEDIUM">MEDIUM (Standard)</option>
              <option value="LOW">LOW (Infrequent)</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="block font-sans text-muted-foreground font-semibold">Poll Interval (seconds)</label>
            <input
              type="number"
              value={pollInterval}
              onChange={(e) => setPollInterval(Number(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-mono focus:outline-none focus:border-primary"
            />
          </div>

          <div className="space-y-1 flex items-center pt-5 gap-2">
            <input
              type="checkbox"
              id="portal_active_cb_modal"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded bg-background border-border text-primary focus:ring-0"
            />
            <label htmlFor="portal_active_cb_modal" className="font-sans text-foreground font-semibold">
              Is Active
            </label>
          </div>
        </div>

        <div className="space-y-1">
          <label className="block font-sans text-muted-foreground font-semibold">Admin Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground focus:outline-none focus:border-primary font-sans"
          />
        </div>

        {/* Form Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-border font-sans">
          {portal && portal.is_active ? (
            <button
              type="button"
              onClick={handleDeactivate}
              className="px-3 py-2 border border-destructive/40 text-destructive hover:bg-destructive/10 rounded-[6px] flex items-center gap-1 text-xs font-semibold cursor-pointer"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Deactivate</span>
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2 font-sans">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-[6px] font-semibold cursor-pointer text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 text-white dark:text-[#0c1015] font-semibold rounded-[6px] flex items-center gap-1.5 shadow-sm cursor-pointer text-xs"
            >
              {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>Save Portal</span>
            </button>
          </div>
        </div>
      </form>
    </AccessibleModal>
  );
}
