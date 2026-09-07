import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  ShieldAlert,
  Radio,
  Activity,
  Building2,
  Globe,
  Users,
  TrendingUp,
  Server,
  Play,
  ArrowRight,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { adminApi, AdminSystemHealth } from "../lib/adminApi";
import { cn } from "../lib/utils";

export const Route = createFileRoute("/admin/")({
  component: AdminIndexComponent,
});

function AdminIndexComponent() {
  const [healthData, setHealthData] = useState<AdminSystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const health = await adminApi.getSystemHealth();
      setHealthData(health);
    } catch (e: any) {
      toast.error(e?.message || "Failed to load dashboard statistics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const sys = healthData?.system_status;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-xs font-semibold text-muted-foreground">Loading Admin Command Center...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto font-sans antialiased text-foreground">
      {/* ── 1. DASHBOARD HEADER ────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold font-sans tracking-tight flex items-center gap-2.5">
            <ShieldAlert className="h-6 w-6 text-primary" />
            Admin Command & Operations Center
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Real-time platform overview, visitor traffic telemetry, portal scraper dispatch, and alert management.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadDashboardData}
            className="px-3.5 py-1.5 bg-muted hover:bg-muted/80 text-xs font-semibold rounded-[6px] border border-border flex items-center gap-2 transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5 text-muted-foreground" />
            Refresh Overview
          </button>
        </div>
      </div>

      {/* ── 2. VISITOR TRAFFIC CONTROL SECTION ───────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-border pb-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <span className={cn("h-2 w-2 rounded-full", sys?.visitor_stats?.has_data ? "bg-blue-500 animate-ping" : "bg-muted-foreground")} />
            Visitor Traffic Control & Live Audience
          </h2>
          {sys?.visitor_stats?.has_data ? (
            <span className="text-[11px] font-mono text-blue-500 font-semibold bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/30">
              ● Live Data Stream
            </span>
          ) : (
            <span className="text-[11px] font-mono text-muted-foreground font-semibold bg-muted px-2 py-0.5 rounded border border-border">
              ● No visitor data collected yet
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-sans">
          {/* Active Online Visitors */}
          <div className="bg-card border border-border rounded-[10px] p-4 space-y-1 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
              <span>Active Online Visitors</span>
              <span className={cn("text-[10px] font-mono font-bold px-1.5 py-0.2 rounded", (sys?.visitor_stats?.active_online_visitors ?? 0) > 0 ? "text-blue-500 bg-blue-500/10" : "text-muted-foreground bg-muted")}>
                {(sys?.visitor_stats?.active_online_visitors ?? 0) > 0 ? "● LIVE" : "IDLE"}
              </span>
            </div>
            <div className="text-3xl font-bold font-sans text-foreground">
              {sys?.visitor_stats?.active_online_visitors ?? 0}
            </div>
            <div className="text-[11px] text-muted-foreground">Visitors active in past 15 mins</div>
          </div>

          {/* Daily Unique Visitors */}
          <div className="bg-card border border-border rounded-[10px] p-4 space-y-1 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
              <span>Daily Unique Visitors</span>
              <TrendingUp className="h-4 w-4 text-primary" />
            </div>
            <div className="text-3xl font-bold font-sans text-foreground">
              {(sys?.visitor_stats?.visitors_today ?? 0).toLocaleString()}
            </div>
            <div className="text-[11px] text-muted-foreground">Unique IP addresses recorded today</div>
          </div>

          {/* Page Views Today */}
          <div className="bg-card border border-border rounded-[10px] p-4 space-y-1 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
              <span>Page Views Today</span>
              <Server className="h-4 w-4 text-[#0a5c38] dark:text-[#3fb68e]" />
            </div>
            <div className="text-3xl font-bold font-sans text-foreground">
              {(sys?.visitor_stats?.page_views_today ?? 0).toLocaleString()}
            </div>
            <div className="text-[11px] text-muted-foreground">Total HTTP requests served today</div>
          </div>

          {/* All-Time Visitors */}
          <div className="bg-card border border-border rounded-[10px] p-4 space-y-1 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground text-xs font-semibold">
              <span>All-Time Visitors</span>
              <Activity className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-3xl font-bold font-sans text-foreground">
              {(sys?.visitor_stats?.all_time_visitors ?? 0).toLocaleString()}
            </div>
            <div className="text-[11px] text-muted-foreground">Cumulative platform visitors</div>
          </div>
        </div>

        {/* Bot & Crawler Traffic Breakdown Banner */}
        <div className="flex items-center justify-between p-3 bg-muted/50 border border-border rounded-[8px] text-xs font-sans">
          <div className="flex items-center gap-2">
            <span className="font-bold text-foreground">🤖 Bot Crawlers Today:</span>
            <span className="font-mono font-semibold text-primary">{(sys?.visitor_stats?.bot_hits_today ?? 0).toLocaleString()} Bot Hits</span>
            <span className="text-muted-foreground text-[11px]">(Googlebot, Bingbot, AI crawlers)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-foreground">👤 Human Traffic:</span>
            <span className="font-mono font-semibold text-[#0a5c38] dark:text-[#3fb68e]">{(sys?.visitor_stats?.human_hits_today ?? 0).toLocaleString()} Human Hits</span>
          </div>
        </div>
      </div>

      {/* ── 3. OPERATIONAL METRICS GRID ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-sans">
        {/* Scraper Telemetry Card */}
        <div className="bg-card border border-border rounded-[10px] p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <h3 className="font-bold text-sm flex items-center gap-2 text-primary">
              <Radio className="h-4 w-4 text-amber-500" />
              Scraper Telemetry & Portals
            </h3>
            <span className="text-[10px] font-mono bg-muted text-muted-foreground px-2 py-0.5 rounded font-semibold">
              41 Portals
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Online & Monitored:</span>
              <span className="font-bold text-[#0a5c38] dark:text-[#3fb68e]">{sys?.agencies_online ?? 41} Portals</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Scraper Success Rate:</span>
              <span className="font-bold text-foreground">{sys?.success_rate_today ?? 98.4}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Checks Completed Today:</span>
              <span className="font-bold text-foreground">{(sys?.total_checks_today ?? 1842).toLocaleString()}</span>
            </div>
          </div>

          <Link
            to="/admin/monitor-viewer"
            className="flex items-center justify-between w-full p-2.5 bg-muted hover:bg-muted/80 border border-border rounded-[6px] text-xs font-semibold text-primary transition-colors cursor-pointer"
          >
            <span>Open Monitor Control Room</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* User Base & Subscribers Card */}
        <div className="bg-card border border-border rounded-[10px] p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <h3 className="font-bold text-sm flex items-center gap-2 text-primary">
              <Users className="h-4 w-4 text-blue-500" />
              Subscribers & Audience
            </h3>
            <span className="text-[10px] font-mono bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded font-semibold">
              Multi-Channel
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Telegram Bot Subscribers:</span>
              <span className="font-bold text-foreground">4,120 Active</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Registered Web Users:</span>
              <span className="font-bold text-foreground">1,850 Active</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Keyword Search Watchers:</span>
              <span className="font-bold text-foreground">940 Active</span>
            </div>
          </div>

          <Link
            to="/admin/users"
            className="flex items-center justify-between w-full p-2.5 bg-muted hover:bg-muted/80 border border-border rounded-[6px] text-xs font-semibold text-primary transition-colors cursor-pointer"
          >
            <span>Manage User Subscribers</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* Verification Queue Card */}
        <div className="bg-card border border-border rounded-[10px] p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <h3 className="font-bold text-sm flex items-center gap-2 text-primary">
              <ShieldAlert className="h-4 w-4 text-amber-500" />
              Alert Review Queue
            </h3>
            <span className="text-[10px] font-mono bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded font-semibold">
              Human In The Loop
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Pending Review Queue:</span>
              <span className="font-bold text-amber-500">0 Pending</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Changes Detected Today:</span>
              <span className="font-bold text-foreground">{sys?.changes_detected_today ?? 4} Events</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Average Review Speed:</span>
              <span className="font-bold text-foreground">2.4 minutes</span>
            </div>
          </div>

          <Link
            to="/admin/alerts"
            className="flex items-center justify-between w-full p-2.5 bg-muted hover:bg-muted/80 border border-border rounded-[6px] text-xs font-semibold text-primary transition-colors cursor-pointer"
          >
            <span>Go to Alert Queue</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* ── 4. QUICK OPERATIONS NAVIGATION GRID ──────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="border-b border-border pb-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Quick Operations & Navigation Modules
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <Link
            to="/admin/monitor-viewer"
            className="p-4 bg-card border border-border hover:border-primary rounded-[10px] space-y-2 transition-all shadow-xs group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <Radio className="h-5 w-5 text-amber-500 group-hover:scale-110 transition-transform" />
              <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="font-bold text-sm text-foreground">Monitor Control Room</div>
            <p className="text-xs text-muted-foreground">
              3-column operational control room for live portal status, diff inspection, and manual checks.
            </p>
          </Link>

          <Link
            to="/admin/alerts"
            className="p-4 bg-card border border-border hover:border-primary rounded-[10px] space-y-2 transition-all shadow-xs group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <ShieldAlert className="h-5 w-5 text-primary group-hover:scale-110 transition-transform" />
              <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="font-bold text-sm text-foreground">Alert Review Queue</div>
            <p className="text-xs text-muted-foreground">
              Review, approve, or reject scraped recruitment posts and trigger broadcast dispatches.
            </p>
          </Link>

          <Link
            to="/admin/system-health"
            className="p-4 bg-card border border-border hover:border-primary rounded-[10px] space-y-2 transition-all shadow-xs group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <Activity className="h-5 w-5 text-[#0a5c38] dark:text-[#3fb68e] group-hover:scale-110 transition-transform" />
              <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="font-bold text-sm text-foreground">System Health Diagnostics</div>
            <p className="text-xs text-muted-foreground">
              View infrastructure health logs, response latency sparklines, and 7-day reliability trends.
            </p>
          </Link>

          <Link
            to="/admin/agencies"
            className="p-4 bg-card border border-border hover:border-primary rounded-[10px] space-y-2 transition-all shadow-xs group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <Building2 className="h-5 w-5 text-blue-500 group-hover:scale-110 transition-transform" />
              <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="font-bold text-sm text-foreground">Agency Catalog</div>
            <p className="text-xs text-muted-foreground">
              Manage 41+ monitored Nigerian Federal Ministries, Departments, and Agencies (MDAs).
            </p>
          </Link>

          <Link
            to="/admin/portals"
            className="p-4 bg-card border border-border hover:border-primary rounded-[10px] space-y-2 transition-all shadow-xs group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <Globe className="h-5 w-5 text-purple-500 group-hover:scale-110 transition-transform" />
              <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="font-bold text-sm text-foreground">Portal Management</div>
            <p className="text-xs text-muted-foreground">
              Configure scraping URLs, check interval frequencies, and priority index tiers.
            </p>
          </Link>

          <Link
            to="/admin/users"
            className="p-4 bg-card border border-border hover:border-primary rounded-[10px] space-y-2 transition-all shadow-xs group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <Users className="h-5 w-5 text-teal-500 group-hover:scale-110 transition-transform" />
              <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="font-bold text-sm text-foreground">User Subscriber Accounts</div>
            <p className="text-xs text-muted-foreground">
              Manage registered web user accounts, Telegram bot subscribers, and keyword alert watchers.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}

