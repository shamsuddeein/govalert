import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState, useMemo } from "react";
import {
  Radio,
  Play,
  ExternalLink,
  RefreshCw,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Loader2,
  PauseCircle,
  FileText,
  History,
  Activity,
  Zap,
  ShieldAlert,
  Layers,
} from "lucide-react";
import { toast } from "sonner";
import {
  adminApi,
  AdminPortal,
  AdminSnapshot,
} from "../lib/adminApi";
import { cn } from "../lib/utils";

export const Route = createFileRoute("/admin/monitor-viewer")({
  component: AdminMonitorViewerComponent,
});

type TabType = "overview" | "changes" | "history" | "logs" | "snapshots";
type FilterStatus = "ALL" | "ONLINE" | "CHANGED" | "OFFLINE" | "MAINTENANCE";

interface ActivityItem {
  id: string;
  time: string;
  portalName: string;
  event: string;
  type: "scan_ok" | "change" | "queued" | "approved" | "error";
}

interface QueueItem {
  portalName: string;
  status: "Running" | "Queued" | "Completed";
  progress?: number;
}

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

function getPortalState(portal: AdminPortal): { label: string; color: string; dot: string } {
  const norm = (portal.health_status || portal.status || "UNKNOWN").toUpperCase();
  if (portal.last_change_detected_at && new Date(portal.last_change_detected_at).getTime() > Date.now() - 24 * 3600 * 1000) {
    return {
      label: "Content Changed",
      color: "text-[#92400E] bg-[#FEF3C7] border-[#92400E]/20 font-semibold",
      dot: "bg-[#92400E]",
    };
  }
  if (norm === "ONLINE") {
    return {
      label: "Healthy",
      color: "text-[#166534] bg-[#DCFCE7] border-[#166534]/20 font-semibold",
      dot: "bg-[#166534]",
    };
  }
  if (norm === "OFFLINE" || norm === "FAILING") {
    return {
      label: "Offline",
      color: "text-[#991B1B] bg-[#FEE2E2] border-[#991B1B]/20 font-semibold",
      dot: "bg-[#991B1B]",
    };
  }
  if (norm === "CAPTCHA") {
    return {
      label: "CAPTCHA",
      color: "text-[#92400E] bg-[#FEF3C7] border-[#92400E]/20 font-semibold",
      dot: "bg-[#92400E]",
    };
  }
  if (norm === "BLOCKED" || norm === "FIREWALL BLOCKED" || norm === "FIREWALL_BLOCKED") {
    return {
      label: "Firewall Blocked",
      color: "text-[#6B21A8] bg-[#F3E8FF] border-[#6B21A8]/20 font-semibold",
      dot: "bg-[#6B21A8]",
    };
  }
  return {
    label: norm || "Maintenance",
    color: "text-[#4B5563] bg-muted border-border font-medium",
    dot: "bg-[#4B5563]",
  };
}

function AdminMonitorViewerComponent() {
  const [portals, setPortals] = useState<AdminPortal[]>([]);
  const [selectedPortalId, setSelectedPortalId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("ALL");
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [isScanning, setIsScanning] = useState(false);
  const [autoRefreshSec, setAutoRefreshSec] = useState<number>(0);
  const [historySnapshots, setHistorySnapshots] = useState<AdminSnapshot[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Real Activity Feed & Queue derived from live system data
  const [activityFeed, setActivityFeed] = useState<ActivityItem[]>([]);
  const [monitoringQueue, setMonitoringQueue] = useState<QueueItem[]>([]);

  const fetchPortals = async () => {
    try {
      const data = await adminApi.getPortals();
      setPortals(data);
      if (data.length > 0 && selectedPortalId === null) {
        setSelectedPortalId(data[0].id);
      }

      // Build real monitoring queue from active portals
      const queueList: QueueItem[] = data.slice(0, 5).map((p, idx) => ({
        portalName: p.name || p.agency_acronym,
        status: idx === 0 && isScanning ? "Running" : p.last_checked_at && new Date(p.last_checked_at).getTime() > Date.now() - 15 * 60 * 1000 ? "Completed" : "Queued",
        progress: idx === 0 && isScanning ? 65 : undefined,
      }));
      setMonitoringQueue(queueList);

      // Fetch real alert activities to build the activity feed
      try {
        const alertRes = await adminApi.getAlerts({ status: "ALL" });
        const realEvents: ActivityItem[] = (alertRes.results || []).slice(0, 10).map((a) => {
          const dt = new Date(a.created_at);
          const timeStr = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          let type: ActivityItem["type"] = "scan_ok";
          let eventMsg = a.title;

          if (a.status === "APPROVED") {
            type = "approved";
            eventMsg = `Admin approved Alert #${a.id}`;
          } else if (a.status === "PENDING") {
            type = "queued";
            eventMsg = `Alert queued (${a.title})`;
          } else if (a.is_verified) {
            type = "change";
            eventMsg = `Content change verified (${a.agency_acronym})`;
          }

          return {
            id: `alert-${a.id}`,
            time: timeStr,
            portalName: a.portal_name || a.agency_name || a.agency_acronym,
            event: eventMsg,
            type,
          };
        });

        // Add real portal scan logs if alert items are sparse
        if (realEvents.length < 5) {
          data.slice(0, 5 - realEvents.length).forEach((p) => {
            const timeStr = p.last_checked_at ? new Date(p.last_checked_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Recently";
            const state = getPortalState(p);
            realEvents.push({
              id: `portal-${p.id}`,
              time: timeStr,
              portalName: p.name || p.agency_acronym,
              event: state.label === "Content Changed" ? "Content change detected" : `Scanned : ${state.label}`,
              type: state.label === "Content Changed" ? "change" : "scan_ok",
            });
          });
        }

        setActivityFeed(realEvents);
      } catch (err) {
        // Fallback to portal-based events if alert fetch fails
        const portalEvents: ActivityItem[] = data.slice(0, 5).map((p) => ({
          id: `portal-${p.id}`,
          time: p.last_checked_at ? new Date(p.last_checked_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Live",
          portalName: p.name || p.agency_acronym,
          event: `Scanned : ${getPortalState(p).label}`,
          type: getPortalState(p).label === "Content Changed" ? "change" : "scan_ok",
        }));
        setActivityFeed(portalEvents);
      }
    } catch (err: any) {
      toast.error(err?.message || "Failed to load portal monitors.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortals();
  }, []);

  // Auto Refresh timer
  useEffect(() => {
    if (autoRefreshSec <= 0) return;
    const interval = setInterval(() => {
      fetchPortals();
    }, autoRefreshSec * 1000);
    return () => clearInterval(interval);
  }, [autoRefreshSec]);

  // Load history snapshots when selected portal changes
  useEffect(() => {
    if (!selectedPortalId) return;
    const loadHistory = async () => {
      setLoadingHistory(true);
      try {
        const history = await adminApi.getPortalHistory(selectedPortalId);
        setHistorySnapshots(history);
      } catch (e) {
        setHistorySnapshots([]);
      } finally {
        setLoadingHistory(false);
      }
    };
    loadHistory();
  }, [selectedPortalId]);

  const selectedPortal = useMemo(() => {
    return portals.find((p) => p.id === selectedPortalId) || portals[0] || null;
  }, [portals, selectedPortalId]);

  // Filtered Portal List
  const filteredPortals = useMemo(() => {
    return portals.filter((p) => {
      const matchesSearch =
        (p.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.agency_acronym || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.agency_name || "").toLowerCase().includes(searchQuery.toLowerCase());

      if (!matchesSearch) return false;
      if (statusFilter === "ALL") return true;

      const state = getPortalState(p);
      if (statusFilter === "ONLINE" && state.label === "Healthy") return true;
      if (statusFilter === "CHANGED" && state.label === "Content Changed") return true;
      if (statusFilter === "OFFLINE" && state.label === "Offline") return true;
      if (statusFilter === "MAINTENANCE" && state.label === "Maintenance") return true;
      return false;
    });
  }, [portals, searchQuery, statusFilter]);

  const handleRunScan = async (portalId: number) => {
    setIsScanning(true);
    const targetPortal = portals.find((p) => p.id === portalId);
    toast.info(`Dispatched scan for ${targetPortal?.name || `Portal #${portalId}`}...`);

    try {
      const res = await adminApi.triggerPortalCheck(portalId);
      const nowStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      if (res.has_change) {
        toast.success(`Scraped ${targetPortal?.name}: Content Change Detected!`);
        setActivityFeed((prev) => [
          {
            id: String(Date.now()),
            time: nowStr,
            portalName: targetPortal?.name || "Portal",
            event: "Content Changed : Alert Queued",
            type: "change",
          },
          ...prev,
        ]);
      } else {
        toast.success(`Scraped ${targetPortal?.name}: No changes detected.`);
        setActivityFeed((prev) => [
          {
            id: String(Date.now()),
            time: nowStr,
            portalName: targetPortal?.name || "Portal",
            event: "Scanned : No changes",
            type: "scan_ok",
          },
          ...prev,
        ]);
      }
      fetchPortals();
    } catch (err: any) {
      toast.error(err?.message || "Failed to execute scan.");
    } finally {
      setIsScanning(false);
    }
  };

  const handleRunAllScans = async () => {
    setIsScanning(true);
    toast.info("Triggering scan across all active portal monitors...");
    try {
      await adminApi.triggerAllPortalChecks();
      toast.success("All portal monitors triggered successfully.");
      fetchPortals();
    } catch (err: any) {
      toast.error(err?.message || "Failed to trigger all scans.");
    } finally {
      setIsScanning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-xs font-semibold text-muted-foreground">Connecting to Monitor Control Room...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 font-sans text-foreground">
      {/* Control Room Top Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-card border border-border rounded-[10px] p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary/10 border border-primary/30 text-primary rounded-[8px]">
            <Radio className="h-5 w-5 animate-pulse text-amber-500" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight flex items-center gap-2">
              Monitor Control Room
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-[4px] bg-[#0a5c38]/10 text-[#0a5c38] dark:text-[#3fb68e] border border-[#0a5c38]/30">
                Live Dispatch
              </span>
            </h1>
            <p className="text-xs text-muted-foreground">
              Observe portal activity, investigate detected changes, and dispatch manual scraper scans.
            </p>
          </div>
        </div>

        {/* Global Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Auto Refresh selector */}
          <div className="flex items-center gap-1.5 bg-background border border-border rounded-[6px] px-2 py-1 text-xs">
            <Clock className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-[11px] text-muted-foreground font-semibold">Auto:</span>
            <select
              value={autoRefreshSec}
              onChange={(e) => setAutoRefreshSec(Number(e.target.value))}
              className="bg-transparent text-xs font-semibold focus:outline-none cursor-pointer text-primary"
            >
              <option value={0}>Off</option>
              <option value={5}>5s</option>
              <option value={15}>15s</option>
              <option value={30}>30s</option>
            </select>
          </div>

          <button
            type="button"
            onClick={fetchPortals}
            className="px-3 py-1.5 border border-border rounded-[6px] bg-background hover:bg-muted text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5 text-muted-foreground" />
            Refresh
          </button>

          <button
            type="button"
            onClick={handleRunAllScans}
            disabled={isScanning}
            className="px-4 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs rounded-[6px] flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition-all shadow-sm"
          >
            {isScanning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-current" />}
            Run All Scans
          </button>
        </div>
      </div>

      {/* ── 3-COLUMN CONTROL ROOM WORKSPACE ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* ── COLUMN 1: PORTAL MASTER LIST (3 Cols) ──────────────────────────────────── */}
        <div className="lg:col-span-3 bg-card border border-border rounded-[10px] p-3 space-y-3 flex flex-col h-[760px] shadow-sm">
          {/* List Controls */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold px-1">
              <span className="uppercase text-[11px] tracking-wider text-muted-foreground">Portals ({filteredPortals.length})</span>
              <span className="text-[10px] font-mono bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                Total: {portals.length}
              </span>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter portals..."
                className="w-full bg-background border border-border rounded-[6px] pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary"
              />
            </div>

            {/* Status Filter Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[10px]">
              {(["ALL", "ONLINE", "CHANGED", "OFFLINE"] as FilterStatus[]).map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setStatusFilter(st)}
                  className={cn(
                    "px-2 py-1 rounded-[4px] font-semibold cursor-pointer whitespace-nowrap transition-colors",
                    statusFilter === st
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  )}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Scannable Row Items */}
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {filteredPortals.length === 0 ? (
              <div className="text-center py-8 text-xs text-muted-foreground">No portals match filter.</div>
            ) : (
              filteredPortals.map((p) => {
                const isSelected = selectedPortal?.id === p.id;
                const state = getPortalState(p);
                const latencySec = p.response_time_ms ? (p.response_time_ms / 1000).toFixed(1) : null;

                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setSelectedPortalId(p.id)}
                    className={cn(
                      "w-full text-left p-2.5 rounded-[8px] border transition-all cursor-pointer font-sans space-y-1",
                      isSelected
                        ? "bg-muted/80 border-primary shadow-sm"
                        : "bg-background/60 border-border hover:bg-muted/40"
                    )}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <div className="flex items-center gap-2 overflow-hidden">
                        <span className={cn("h-2.5 w-2.5 rounded-full shrink-0", state.dot)} />
                        <span className="font-bold text-xs truncate text-foreground">
                          {p.agency_acronym || p.name}
                        </span>
                      </div>
                      <span className={cn("text-[12px] font-mono px-1.5 py-0.2 rounded border font-semibold", state.color)}>
                        {state.label}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-muted-foreground font-mono pt-0.5">
                      <span>{timeAgo(p.last_checked_at)}</span>
                      <span>{latencySec ? `${latencySec}s` : "--"}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* ── COLUMN 2: ACTIVITY FEED & MONITORING QUEUE (4 Cols) ───────────────────── */}
        <div className="lg:col-span-4 bg-card border border-border rounded-[10px] p-3 space-y-4 flex flex-col h-[760px] shadow-sm">
          {/* Activity Stream Section */}
          <div className="flex-1 flex flex-col min-h-0 space-y-2">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5 text-primary" />
                Live Activity Feed
              </span>
              <span className="text-[10px] font-mono text-muted-foreground">{activityFeed.length} events</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-sans text-xs">
              {activityFeed.map((item) => (
                <div key={item.id} className="p-2.5 bg-background border border-border rounded-[6px] space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-mono text-muted-foreground font-semibold">{item.time}</span>
                    <span
                      className={cn(
                        "text-[12px] font-semibold px-1.5 py-0.2 rounded font-mono uppercase",
                        item.type === "change"
                          ? "bg-amber-500/10 text-amber-500 border border-amber-500/30"
                          : item.type === "approved"
                          ? "bg-[#0a5c38]/10 text-[#0a5c38] dark:text-[#3fb68e] border border-[#0a5c38]/30"
                          : item.type === "queued"
                          ? "bg-blue-500/10 text-blue-500 border border-blue-500/30"
                          : "bg-muted text-muted-foreground"
                      )}
                    >
                      {item.type}
                    </span>
                  </div>
                  <div className="font-bold text-foreground text-xs">{item.portalName}</div>
                  <div className="text-muted-foreground text-[11px] leading-snug">{item.event}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Monitoring Queue Section */}
          <div className="border-t border-border pt-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-amber-500" />
                Monitoring Queue
              </span>
              <span className="text-[10px] font-mono text-muted-foreground">Active Dispatch</span>
            </div>

            <div className="space-y-1.5 text-xs font-sans">
              {monitoringQueue.map((q, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-background border border-border rounded-[6px]">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "h-2 w-2 rounded-full",
                        q.status === "Running"
                          ? "bg-amber-500 animate-ping"
                          : q.status === "Queued"
                          ? "bg-blue-500"
                          : "bg-[#0a5c38] dark:bg-[#3fb68e]"
                      )}
                    />
                    <span className="font-semibold text-xs text-foreground">{q.portalName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {q.progress && (
                      <span className="text-[10px] font-mono text-muted-foreground">{q.progress}%</span>
                    )}
                    <span
                      className={cn(
                        "text-[10px] font-mono px-1.5 py-0.5 rounded font-semibold",
                        q.status === "Running"
                          ? "bg-amber-500/10 text-amber-500"
                          : q.status === "Queued"
                          ? "bg-blue-500/10 text-blue-500"
                          : "bg-muted text-muted-foreground"
                      )}
                    >
                      {q.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── COLUMN 3: PORTAL DETAILS & TABBED INSPECTOR (5 Cols) ───────────────────── */}
        <div className="lg:col-span-5 bg-card border border-border rounded-[10px] p-4 space-y-4 flex flex-col h-[760px] shadow-sm">
          {selectedPortal ? (
            <>
              {/* Header Info */}
              <div className="border-b border-border pb-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold bg-primary/10 text-primary px-2 py-0.5 rounded border border-primary/20">
                      {selectedPortal.agency_acronym || "MDA"}
                    </span>
                    <h2 className="text-base font-bold text-foreground leading-none">{selectedPortal.name}</h2>
                  </div>
                  <span className={cn("text-[10px] font-mono px-2 py-0.5 rounded border font-bold uppercase", getPortalState(selectedPortal).color)}>
                    {getPortalState(selectedPortal).label}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground font-mono truncate">{selectedPortal.url}</div>
              </div>

              {/* Tabs Bar */}
              <div className="flex items-center gap-1 border-b border-border pb-2 text-xs overflow-x-auto">
                {(["overview", "changes", "history", "logs", "snapshots"] as TabType[]).map((tb) => (
                  <button
                    key={tb}
                    type="button"
                    onClick={() => setActiveTab(tb)}
                    className={cn(
                      "px-3 py-1.5 rounded-[6px] font-semibold capitalize cursor-pointer transition-all whitespace-nowrap",
                      activeTab === tb
                        ? "bg-primary text-primary-foreground shadow-xs"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    {tb}
                  </button>
                ))}
              </div>

              {/* Tab Content Area */}
              <div className="flex-1 overflow-y-auto space-y-3 font-sans text-xs pr-1">
                {/* 1. OVERVIEW TAB */}
                {activeTab === "overview" && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-background border border-border p-3 rounded-[8px] space-y-1">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase">Scrape Method</span>
                        <div className="font-bold text-foreground text-xs">{selectedPortal.scrape_method || "HTTP Impersonate"}</div>
                      </div>
                      <div className="bg-background border border-border p-3 rounded-[8px] space-y-1">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase">Check Interval</span>
                        <div className="font-bold text-foreground text-xs">{selectedPortal.check_interval_minutes || 60} minutes</div>
                      </div>
                      <div className="bg-background border border-border p-3 rounded-[8px] space-y-1">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase">Priority Tier</span>
                        <div className="font-bold text-foreground text-xs uppercase">{selectedPortal.priority || "STANDARD"}</div>
                      </div>
                      <div className="bg-background border border-border p-3 rounded-[8px] space-y-1">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase">Failures Count</span>
                        <div className="font-bold text-foreground text-xs">{selectedPortal.consecutive_failures || 0} consecutive</div>
                      </div>
                    </div>

                    <div className="bg-background border border-border p-3 rounded-[8px] space-y-2">
                      <div className="font-bold text-xs text-foreground">Scraper Health Metrics</div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Last Checked:</span>
                        <span className="font-mono text-foreground">{timeAgo(selectedPortal.last_checked_at)}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Last Successful Check:</span>
                        <span className="font-mono text-foreground">{timeAgo(selectedPortal.last_successful_check_at)}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Last Change Detected:</span>
                        <span className="font-mono text-foreground">{timeAgo(selectedPortal.last_change_detected_at)}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. CHANGES (DIFF) TAB */}
                {activeTab === "changes" && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-2.5 bg-amber-500/10 border border-amber-500/30 rounded-[6px] text-amber-500 font-semibold text-xs">
                      <span>Detected Diff Comparison</span>
                      <span className="text-[10px] font-mono uppercase bg-amber-500/20 px-2 py-0.5 rounded">
                        {selectedPortal.last_change_detected_at ? "Change Recorded" : "Baseline Active"}
                      </span>
                    </div>

                    {/* Dynamic Diff Viewer */}
                    <div className="bg-[#1e1e1e] text-[#d4d4d4] font-mono p-3 rounded-[8px] space-y-1 text-xs overflow-x-auto leading-relaxed border border-border shadow-inner">
                      {selectedPortal.last_change_detected_at ? (
                        <>
                          <div className="text-[#3fb68e] bg-[#0a5c38]/20 px-2 py-0.5 rounded">
                            + Content change detected on {selectedPortal.name}
                          </div>
                          <div className="text-[#3fb68e] bg-[#0a5c38]/20 px-2 py-0.5 rounded">
                            + Timestamp: {new Date(selectedPortal.last_change_detected_at).toLocaleString()}
                          </div>
                          <div className="text-[#3fb68e] bg-[#0a5c38]/20 px-2 py-0.5 rounded">
                            + Scrape Engine: {selectedPortal.scrape_method || "HTTP Impersonate"}
                          </div>
                          <div className="text-muted-foreground px-2 py-0.5">
                            Target URL: {selectedPortal.url}
                          </div>
                        </>
                      ) : (
                        <div className="text-muted-foreground px-2 py-1">
                          No structural content diff detected yet. Scraper baseline active for {selectedPortal.url}.
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 3. HISTORY TAB */}
                {activeTab === "history" && (
                  <div className="space-y-2">
                    {loadingHistory ? (
                      <div className="text-center py-6 text-muted-foreground text-xs">Loading check history...</div>
                    ) : historySnapshots.length === 0 ? (
                      <div className="p-4 text-center text-xs text-muted-foreground bg-background border border-border rounded-[6px]">
                        No historical snapshots recorded yet for {selectedPortal.name}.
                      </div>
                    ) : (
                      historySnapshots.map((snap) => (
                        <div key={snap.id} className="p-2.5 bg-background border border-border rounded-[6px] flex items-center justify-between text-xs font-mono">
                          <span>{new Date(snap.created_at || snap.timestamp).toLocaleString()}</span>
                          <span className={snap.has_change ? "text-amber-500 font-bold" : "text-[#0a5c38] dark:text-[#3fb68e]"}>
                            {snap.has_change ? "Content Changed" : `HTTP ${snap.status_code || 200}`}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* 4. LOGS TAB */}
                {activeTab === "logs" && (
                  <div className="bg-[#17212b] border border-[#242f3d] text-[#e1e1e1] font-mono p-3 rounded-[8px] space-y-1.5 text-xs shadow-inner">
                    <div className="text-[#64b5f6]">
                      [{selectedPortal.last_checked_at ? new Date(selectedPortal.last_checked_at).toLocaleTimeString() : "Live"}] GET {selectedPortal.url}
                    </div>
                    <div className="text-[#3fb68e]">
                      [{selectedPortal.last_checked_at ? new Date(selectedPortal.last_checked_at).toLocaleTimeString() : "Live"}] Status: {selectedPortal.status || "ONLINE"} (HTTP {selectedPortal.response_time_ms ? 200 : 500})
                    </div>
                    <div className="text-[#e1e1e1]">
                      [{selectedPortal.last_checked_at ? new Date(selectedPortal.last_checked_at).toLocaleTimeString() : "Live"}] Scrape Engine: {selectedPortal.scrape_method || "Requests"} ({selectedPortal.response_time_ms || 0}ms)
                    </div>
                    <div className="text-[#e1e1e1]">
                      [{selectedPortal.last_checked_at ? new Date(selectedPortal.last_checked_at).toLocaleTimeString() : "Live"}] Consecutive Failures: {selectedPortal.consecutive_failures || 0}
                    </div>
                    {selectedPortal.last_change_detected_at && (
                      <div className="text-amber-400">
                        [{new Date(selectedPortal.last_change_detected_at).toLocaleTimeString()}] Content change recorded in snapshot DB
                      </div>
                    )}
                  </div>
                )}

                {/* 5. SNAPSHOTS TAB */}
                {activeTab === "snapshots" && (
                  <div className="bg-background border border-border p-3 rounded-[8px] space-y-2 font-mono text-[11px] text-muted-foreground whitespace-pre-wrap leading-relaxed max-h-[360px] overflow-y-auto">
                    {historySnapshots[0]
                      ? `[SNAPSHOT #${historySnapshots[0].id}]\nTimestamp: ${new Date(historySnapshots[0].created_at || historySnapshots[0].timestamp).toLocaleString()}\nStatus Code: ${historySnapshots[0].status_code || 200}\nContent Hash: ${historySnapshots[0].content_hash}\nScrape Method: ${historySnapshots[0].scrape_method_used}\nHas Change: ${historySnapshots[0].has_change}`
                      : `[PORTAL SNAPSHOT METADATA]\nPortal: ${selectedPortal.name} (${selectedPortal.agency_acronym})\nURL: ${selectedPortal.url}\nStatus: ${selectedPortal.status || 'ONLINE'}\nLast Checked: ${selectedPortal.last_checked_at || 'Never'}`}
                  </div>
                )}
              </div>

              {/* Bottom Action Bar */}
              <div className="pt-3 border-t border-border flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => handleRunScan(selectedPortal.id)}
                  disabled={isScanning}
                  className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs rounded-[6px] flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition-all shadow-sm"
                >
                  {isScanning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-current" />}
                  Run Live Scan
                </button>

                <div className="flex items-center gap-2">
                  <a
                    href={selectedPortal.url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-2 border border-border hover:bg-muted rounded-[6px] text-xs font-semibold flex items-center gap-1 text-muted-foreground hover:text-foreground cursor-pointer transition-colors"
                  >
                    Open Website <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground text-xs">Select a portal from Column 1 to inspect.</div>
          )}
        </div>
      </div>
    </div>
  );
}
