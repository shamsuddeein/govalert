import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Pencil,
  Trash2,
  Send,
  Radio,
  PlusCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  adminApi,
  AdminAlert,
  AdminAlertStats,
} from "../lib/adminApi";
import { cn } from "../lib/utils";

export const Route = createFileRoute("/admin/alerts")({
  component: AdminAlertsComponent,
});

type TabStatus = "PENDING" | "APPROVED" | "REJECTED" | "HELD" | "SUPERSEDED";

function formatAgeHours(hours: number): string {
  if (!hours || hours <= 0) return "0m";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

function timeAgo(dateString: string): string {
  if (!dateString) return "unknown";
  const date = new Date(dateString);
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

function AdminAlertsComponent() {
  const [activeTab, setActiveTab] = useState<TabStatus>("PENDING");
  const [stats, setStats] = useState<AdminAlertStats | null>(null);
  const [alerts, setAlerts] = useState<AdminAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [editingAlert, setEditingAlert] = useState<AdminAlert | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<AdminAlert | null>(null);
  const [showBroadcastModal, setShowBroadcastModal] = useState<boolean>(false);

  // Load stats & queue alerts
  const loadStats = async () => {
    try {
      const res = await adminApi.getAlertStats();
      setStats(res);
    } catch (err) {
      // Silently handle stats error
    }
  };

  const loadAlerts = async (status: TabStatus) => {
    setLoading(true);
    try {
      const res = await adminApi.getAlerts({ status });
      setAlerts(res.results || []);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    loadAlerts(activeTab);
  }, [activeTab]);

  const handleRefresh = () => {
    loadStats();
    loadAlerts(activeTab);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans antialiased">
      {/* Page Title & Broadcast Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2.5">
            <ShieldAlert className="h-6 w-6 text-[color:var(--warning)]" />
            Alert Review & Post Management
          </h1>
          <p className="text-xs text-muted-foreground mt-1 font-sans">
            Review, edit, publish, or delete recruitment notice posts across all statuses.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <Link
            to="/admin/jobs-create"
            className="px-4 py-2.5 bg-[#0a5c38] dark:bg-[#3fb68e] text-white dark:text-zinc-950 font-semibold rounded-[8px] text-xs flex items-center gap-2 shadow-sm hover:opacity-90 transition-all cursor-pointer"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Post New Job</span>
          </Link>

          <button
            onClick={() => setShowBroadcastModal(true)}
            className="px-4 py-2.5 bg-primary text-primary-foreground font-semibold rounded-[8px] text-xs flex items-center gap-2 shadow-sm hover:bg-primary/90 transition-all cursor-pointer"
          >
            <Radio className="h-4 w-4 animate-pulse text-amber-300" />
            <span>Broadcast</span>
          </button>
        </div>
      </div>

      {/* 1. Stat Cards Header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Pending Review</span>
            <Clock className="h-4 w-4 text-[color:var(--warning)]" />
          </div>
          <div className="text-2xl font-bold font-sans text-foreground">
            {stats ? stats.pending_count : ":"}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">Awaiting human decision</div>
        </div>

        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Approved Today</span>
            <CheckCircle2 className="h-4 w-4 text-[#0a5c38] dark:text-[#3fb68e]" />
          </div>
          <div className="text-2xl font-bold font-sans text-[#0a5c38] dark:text-[#3fb68e]">
            {stats ? stats.approved_today : ":"}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">Verified & dispatched</div>
        </div>

        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Rejected Today</span>
            <XCircle className="h-4 w-4 text-destructive" />
          </div>
          <div className="text-2xl font-bold font-sans text-destructive">
            {stats ? stats.rejected_today : ":"}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">Flagged false / fake</div>
        </div>

        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Oldest Pending</span>
            <Sparkles className="h-4 w-4 text-[color:var(--new)]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[color:var(--new)]">
            {stats ? formatAgeHours(stats.oldest_pending_age_hours) : ":"}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">Time in queue</div>
        </div>
      </div>

      {/* 2. Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2 overflow-x-auto">
        {(["PENDING", "APPROVED", "REJECTED", "HELD", "SUPERSEDED"] as TabStatus[]).map((tab) => {
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-4 py-2 rounded-[6px] font-sans text-xs font-semibold tracking-wider transition-all flex items-center gap-2 cursor-pointer",
                isActive
                  ? "bg-muted text-primary border border-border font-bold"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              )}
            >
              <span>{tab}</span>
              {tab === "PENDING" && stats && stats.pending_count > 0 && (
                <span className="bg-[color:var(--warning)]/20 text-[color:var(--warning)] border border-[color:var(--warning)]/30 px-2 py-0.5 rounded-[6px] text-[10px] font-mono font-bold">
                  {stats.pending_count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-xs font-sans">Fetching alerts from review queue...</span>
        </div>
      ) : activeTab === "PENDING" ? (
        /* 3. Pending Queue Full Cards View */
        alerts.length === 0 ? (
          <div className="bg-card border border-border rounded-[8px] p-12 text-center space-y-3 my-8 shadow-sm">
            <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-[#0a5c38]/10 border border-[#0a5c38]/20 text-[#0a5c38] dark:text-[#3fb68e]">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-foreground font-sans">Queue is clear</h3>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto font-sans">
              No alerts waiting for review right now. New recruitment detections will appear here automatically.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {alerts.map((alert) => (
              <PendingAlertCard
                key={alert.id}
                alert={alert}
                onActionSuccess={() => handleRefresh()}
                onEdit={(a) => setEditingAlert(a)}
                onDelete={(a) => setDeletingAlert(a)}
              />
            ))}
          </div>
        )
      ) : (
        /* 4. Compact Table View for Approved/Rejected/Held/Superseded */
        <CompactAlertsTable
          alerts={alerts}
          status={activeTab}
          onEdit={(a) => setEditingAlert(a)}
          onDelete={(a) => setDeletingAlert(a)}
        />
      )}

      {/* Edit Modal */}
      {editingAlert && (
        <EditAlertModal
          alert={editingAlert}
          onClose={() => setEditingAlert(null)}
          onSaved={() => handleRefresh()}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deletingAlert && (
        <DeleteAlertConfirmModal
          alert={deletingAlert}
          onClose={() => setDeletingAlert(null)}
          onDeleted={() => handleRefresh()}
        />
      )}

      {/* Broadcast Announcement Modal */}
      {showBroadcastModal && (
        <BroadcastModal onClose={() => setShowBroadcastModal(false)} />
      )}
    </div>
  );
}

// ─── Pending Alert Review Card Component ────────────────────────────────────────

function PendingAlertCard({
  alert,
  onActionSuccess,
  onEdit,
  onDelete,
}: {
  alert: AdminAlert;
  onActionSuccess: (action: "approve" | "reject" | "hold", id: number) => void;
  onEdit: (alert: AdminAlert) => void;
  onDelete: (alert: AdminAlert) => void;
}) {
  const [notes, setNotes] = useState(alert.admin_notes || "");
  const [showMoreExcerpt, setShowMoreExcerpt] = useState(false);
  const [actionInFlight, setActionInFlight] = useState<"approve" | "reject" | "hold" | null>(null);
  const [isFadingOut, setIsFadingOut] = useState(false);

  const aiClass = alert.ai_classification || "UNCERTAIN";
  const confidence = alert.ai_confidence || 0;
  const trustScore = alert.trust_score || 0;

  // Action Handlers
  const handleApprove = async () => {
    setActionInFlight("approve");
    try {
      await adminApi.approveAlert(alert.id, notes.trim());
      toast.success(`Alert #${alert.id} approved & queued for public dispatch.`);
      setIsFadingOut(true);
      setTimeout(() => onActionSuccess("approve", alert.id), 300);
    } catch (err: any) {
      toast.error(err?.message || "Failed to approve alert.");
    } finally {
      setActionInFlight(null);
    }
  };

  const handleHold = async () => {
    setActionInFlight("hold");
    try {
      await adminApi.holdAlert(alert.id, notes.trim());
      toast.info(`Alert #${alert.id} placed on hold.`);
      setIsFadingOut(true);
      setTimeout(() => onActionSuccess("hold", alert.id), 300);
    } catch (err: any) {
      toast.error(err?.message || "Failed to hold alert.");
    } finally {
      setActionInFlight(null);
    }
  };

  const handleReject = async () => {
    if (!notes.trim()) {
      toast.error("Please add a note in the Admin Audit Notes field explaining why this alert is being rejected.");
      return;
    }
    setActionInFlight("reject");
    try {
      await adminApi.rejectAlert(alert.id, notes.trim());
      toast.warning(`Alert #${alert.id} rejected.`);
      setIsFadingOut(true);
      setTimeout(() => onActionSuccess("reject", alert.id), 300);
    } catch (err: any) {
      toast.error(err?.message || "Failed to reject alert.");
    } finally {
      setActionInFlight(null);
    }
  };

  return (
    <div
      className={cn(
        "bg-card border border-border rounded-[10px] p-6 space-y-6 shadow-sm transition-all duration-300 font-sans",
        isFadingOut ? "opacity-0 scale-95" : "opacity-100 scale-100"
      )}
    >
      {/* Card Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-border pb-4">
        <div className="space-y-1.5 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-bold text-muted-foreground bg-muted px-2 py-0.5 rounded-[4px]">
              #{alert.id}
            </span>
            <span className="font-mono text-xs font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-[4px]">
              {alert.agency_acronym || alert.agency?.acronym || "GOV"}
            </span>
            <span className="text-xs text-muted-foreground font-sans">
              Detected {timeAgo(alert.created_at)}
            </span>
          </div>

          <h2 className="text-lg font-bold text-foreground font-sans tracking-tight">
            {alert.title}
          </h2>

          <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
            <span>Portal: {alert.portal_name || alert.portal?.name || alert.agency_name || "Official Portal"}</span>
            <span>•</span>
            <a
              href={alert.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline flex items-center gap-1 inline-flex"
            >
              <span>{alert.source_url}</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>

        {/* AI & Trust Badges */}
        <div className="flex flex-row md:flex-col items-end justify-between md:justify-start gap-2">
          {/* AI Classification */}
          <div className="text-xs font-medium font-sans text-[#4B5563] dark:text-muted-foreground">
            AI Class: {aiClass} ({confidence}%)
          </div>

          {/* Trust Score Indicator */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground font-sans font-medium">Trust Score:</span>
            <span
              className={cn(
                "font-mono text-sm font-bold px-2 py-0.5 rounded-[4px]",
                trustScore >= 70
                  ? "text-[#0a5c38] dark:text-[#3fb68e] bg-[#0a5c38]/10"
                  : trustScore >= 50
                  ? "text-[color:var(--warning)] bg-[color:var(--warning)]/10"
                  : "text-destructive bg-destructive/10"
              )}
            >
              {trustScore}/100
            </span>
          </div>
        </div>
      </div>

      {/* Extracted Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-muted/30 border border-border rounded-[8px] p-4 font-sans text-xs">
        <div>
          <span className="font-semibold text-muted-foreground block mb-1">Extracted Positions:</span>
          <p className="text-foreground font-medium font-sans">{alert.positions || "Not specified"}</p>
        </div>
        <div>
          <span className="font-semibold text-muted-foreground block mb-1">Application Deadline:</span>
          <p className="text-foreground font-mono font-medium">{alert.deadline || "Not specified"}</p>
        </div>
        <div className="md:col-span-2 border-t border-border/60 pt-3 mt-1">
          <span className="font-semibold text-muted-foreground block mb-1">Requirements Extracted:</span>
          <p className="text-foreground whitespace-pre-wrap font-sans">{alert.requirements || "Check portal website for details"}</p>
        </div>
      </div>

      {/* Content Excerpt Accordion */}
      {alert.content_excerpt && (
        <div className="border border-border/70 rounded-[6px] overflow-hidden bg-background font-sans text-xs">
          <button
            onClick={() => setShowMoreExcerpt(!showMoreExcerpt)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-left font-sans font-semibold text-muted-foreground hover:bg-muted/40 transition-colors cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <span>Raw Scraped Content Excerpt</span>
              <span className="font-mono text-[11px] text-muted-foreground">({alert.content_excerpt.length} chars)</span>
            </span>
            {showMoreExcerpt ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showMoreExcerpt && (
            <div className="px-4 py-3 border-t border-border bg-muted/20 font-mono text-[11px] leading-relaxed text-muted-foreground whitespace-pre-wrap max-h-60 overflow-y-auto">
              {alert.content_excerpt}
            </div>
          )}
        </div>
      )}

      {/* Admin Review Notes & Action Toolbar */}
      <div className="space-y-4 pt-2">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-muted-foreground font-sans block">
            Admin Audit Notes (Optional for Approve/Hold, Mandatory for Reject):
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add internal notes or reasoning for audit log..."
            rows={2}
            className="w-full bg-background border border-border rounded-[6px] p-3 text-xs font-sans text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:border-primary"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 font-sans">
          {/* Edit & Delete Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onEdit(alert)}
              className="px-3 py-1.5 border border-border text-foreground hover:bg-muted text-xs font-sans font-semibold rounded-[6px] transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <Pencil className="h-3.5 w-3.5 text-primary" />
              <span>Edit Post</span>
            </button>
            <button
              onClick={() => onDelete(alert)}
              className="px-3 py-1.5 border border-destructive/30 text-destructive hover:bg-destructive/10 text-xs font-sans font-semibold rounded-[6px] transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Delete</span>
            </button>
          </div>

          {/* Workflow Actions */}
          <div className="flex items-center gap-2">
            {/* Reject */}
            <button
              onClick={handleReject}
              disabled={actionInFlight !== null || !notes.trim()}
              title={!notes.trim() ? "Notes field required before rejecting" : "Reject alert"}
              className="px-4 py-2 border border-red-600/80 text-destructive hover:bg-destructive/10 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-sans font-semibold rounded-[6px] transition-all flex items-center gap-1.5 cursor-pointer"
            >
              {actionInFlight === "reject" ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <XCircle className="h-3.5 w-3.5" />
              )}
              <span>Reject</span>
            </button>

            {/* Hold */}
            <button
              onClick={handleHold}
              disabled={actionInFlight !== null}
              className="px-4 py-2 border border-amber-600/80 text-[color:var(--warning)] hover:bg-[color:var(--warning)]/10 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-sans font-semibold rounded-[6px] transition-all flex items-center gap-1.5 cursor-pointer"
            >
              {actionInFlight === "hold" ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Clock className="h-3.5 w-3.5" />
              )}
              <span>Hold</span>
            </button>

            {/* Approve */}
            <button
              onClick={handleApprove}
              disabled={actionInFlight !== null}
              className="px-5 py-2 bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 text-white dark:text-[#0c1015] text-xs font-sans font-semibold rounded-[6px] transition-all flex items-center gap-1.5 shadow-sm cursor-pointer"
            >
              {actionInFlight === "approve" ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <CheckCircle2 className="h-3.5 w-3.5" />
              )}
              <span>Approve ✓</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Compact Table View for Approved/Rejected/Held/Superseded ─────────────────────

function CompactAlertsTable({
  alerts,
  status,
  onEdit,
  onDelete,
}: {
  alerts: AdminAlert[];
  status: TabStatus;
  onEdit: (alert: AdminAlert) => void;
  onDelete: (alert: AdminAlert) => void;
}) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  if (alerts.length === 0) {
    return (
      <div className="bg-card border border-border rounded-[8px] p-12 text-center text-muted-foreground text-xs font-sans">
        No alerts found for status "{status}".
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-[8px] overflow-hidden shadow-sm font-sans">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-muted border-b border-border text-muted-foreground font-sans font-semibold uppercase tracking-wider">
            <tr>
              <th className="p-3.5">Ref / ID</th>
              <th className="p-3.5">Title</th>
              <th className="p-3.5">Agency</th>
              <th className="p-3.5">AI Class</th>
              <th className="p-3.5">Trust</th>
              <th className="p-3.5">Verified By</th>
              <th className="p-3.5">Verified At</th>
              <th className="p-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border text-foreground">
            {alerts.map((alert) => {
              const isExpanded = expandedId === alert.id;
              return (
                <tr key={alert.id} className="hover:bg-muted/40 transition-colors">
                  <td className="p-3.5 font-mono text-muted-foreground">#{alert.id}</td>
                  <td className="p-3.5 font-medium text-foreground max-w-xs truncate font-sans">{alert.title}</td>
                  <td className="p-3.5 font-mono font-bold text-primary">
                    {alert.agency_acronym || (alert.agency ? alert.agency.acronym : ":")}
                  </td>
                  <td className="p-3.5 font-sans font-medium text-[12px] text-[#4B5563] dark:text-muted-foreground">
                    {alert.ai_classification} ({alert.ai_confidence}%)
                  </td>
                  <td className="p-3.5 font-mono font-bold">{alert.trust_score}/100</td>
                  <td className="p-3.5 font-sans text-muted-foreground">{alert.verified_by || "N/A"}</td>
                  <td className="p-3.5 font-mono text-muted-foreground">
                    {alert.verified_at ? timeAgo(alert.verified_at) : ":"}
                  </td>
                  <td className="p-3.5 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => onEdit(alert)}
                        title="Edit Alert Post"
                        className="p-1.5 text-muted-foreground hover:text-primary rounded bg-background border border-border cursor-pointer transition-colors"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => onDelete(alert)}
                        title="Delete Alert Post"
                        className="p-1.5 text-muted-foreground hover:text-destructive rounded bg-background border border-border cursor-pointer transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : alert.id)}
                        className="p-1.5 text-muted-foreground hover:text-foreground rounded bg-background border border-border cursor-pointer transition-colors"
                      >
                        {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Expanded Detail View */}
      {expandedId !== null && (
        <div className="p-4 bg-muted/30 border-t border-border text-xs space-y-2 font-sans">
          {(() => {
            const a = alerts.find((item) => item.id === expandedId);
            if (!a) return null;
            return (
              <div className="space-y-2">
                <div className="font-sans text-primary font-bold">Detail View for Alert #{a.id}:</div>
                {a.admin_notes && (
                  <div className="bg-card p-3 rounded-[6px] border border-border">
                    <span className="font-sans font-semibold text-muted-foreground block mb-1">Admin Notes:</span>
                    <p className="whitespace-pre-wrap font-sans text-foreground">{a.admin_notes}</p>
                  </div>
                )}
                <div className="text-muted-foreground font-sans">
                  <span className="font-semibold">Source:</span>{" "}
                  <a href={a.source_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline font-mono">
                    {a.source_url}
                  </a>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}

// ─── Edit Alert Post Modal ───────────────────────────────────────────────────────

function EditAlertModal({
  alert,
  onClose,
  onSaved,
}: {
  alert: AdminAlert;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [formData, setFormData] = useState({
    title: alert.title || "",
    positions: alert.positions || "",
    deadline: alert.deadline || "",
    requirements: alert.requirements || "",
    source_url: alert.source_url || "",
    status: alert.status || "PENDING",
    trust_score: alert.trust_score ?? 70,
    admin_notes: alert.admin_notes || "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminApi.updateAlert(alert.id, formData);
      toast.success(`Alert #${alert.id} updated successfully.`);
      onSaved();
      onClose();
    } catch (err: any) {
      toast.error(err?.message || "Failed to update alert.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-[12px] p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto space-y-4 shadow-xl text-foreground font-sans">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Pencil className="h-5 w-5 text-primary" />
            Edit Alert Post #{alert.id}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-sm font-bold cursor-pointer"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
          <div className="space-y-1">
            <label className="font-semibold text-muted-foreground block">Title / Headline</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-sans text-sm focus:outline-none focus:border-primary"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="font-semibold text-muted-foreground block">Positions / Roles</label>
              <input
                type="text"
                value={formData.positions}
                onChange={(e) => setFormData({ ...formData, positions: e.target.value })}
                className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-sans text-xs focus:outline-none focus:border-primary"
              />
            </div>
            <div className="space-y-1">
              <label className="font-semibold text-muted-foreground block">Deadline</label>
              <input
                type="text"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-sans text-xs focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="font-semibold text-muted-foreground block">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-sans text-xs focus:outline-none focus:border-primary cursor-pointer"
              >
                <option value="PENDING">PENDING</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
                <option value="HELD">HELD</option>
                <option value="SUPERSEDED">SUPERSEDED</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="font-semibold text-muted-foreground block">Trust Score (0 - 100)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.trust_score}
                onChange={(e) => setFormData({ ...formData, trust_score: parseInt(e.target.value) || 0 })}
                className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-mono text-xs focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-muted-foreground block">Official Source URL</label>
            <input
              type="url"
              value={formData.source_url}
              onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
              className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-mono text-xs focus:outline-none focus:border-primary"
            />
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-muted-foreground block">Requirements Extracted</label>
            <textarea
              rows={3}
              value={formData.requirements}
              onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
              className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-sans text-xs focus:outline-none focus:border-primary"
            />
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-muted-foreground block">Admin Audit Notes</label>
            <textarea
              rows={3}
              value={formData.admin_notes}
              onChange={(e) => setFormData({ ...formData, admin_notes: e.target.value })}
              className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-sans text-xs focus:outline-none focus:border-primary font-mono"
              placeholder="Notes detailing edits or verification rationale..."
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-[6px] hover:bg-muted text-muted-foreground text-xs font-semibold cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-[6px] text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Delete Alert Post Confirm Modal ─────────────────────────────────────────────

function DeleteAlertConfirmModal({
  alert,
  onClose,
  onDeleted,
}: {
  alert: AdminAlert;
  onClose: () => void;
  onDeleted: () => void;
}) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await adminApi.deleteAlert(alert.id);
      toast.success(`Alert #${alert.id} permanently deleted.`);
      onDeleted();
      onClose();
    } catch (err: any) {
      toast.error(err?.message || "Failed to delete alert.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-destructive/30 rounded-[12px] p-6 max-w-md w-full space-y-4 shadow-xl text-foreground font-sans">
        <div className="flex items-center gap-3 text-destructive">
          <div className="p-2 bg-destructive/10 rounded-full border border-destructive/20">
            <Trash2 className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-base font-bold">Delete Alert Post #{alert.id}?</h2>
            <p className="text-xs text-muted-foreground">This action cannot be undone.</p>
          </div>
        </div>

        <div className="bg-muted/50 p-3 rounded-[6px] border border-border text-xs space-y-1">
          <div className="font-semibold text-foreground">{alert.title}</div>
          <div className="text-muted-foreground font-mono">
            Agency: {alert.agency_acronym || alert.agency?.acronym || "N/A"}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-[6px] hover:bg-muted text-muted-foreground text-xs font-semibold cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="px-5 py-2 bg-destructive hover:bg-destructive/90 text-destructive-foreground font-semibold rounded-[6px] text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Delete Permanently"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Broadcast Announcement Modal ────────────────────────────────────────────────

function BroadcastModal({ onClose }: { onClose: () => void }) {
  const [subject, setSubject] = useState("📢 RecruitmentAlert Announcement");
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [previewChannel, setPreviewChannel] = useState<"telegram" | "email">("telegram");

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) {
      toast.error("Please enter a message text before sending.");
      return;
    }
    setSending(true);
    try {
      const res = await adminApi.sendBroadcast(text.trim(), subject.trim());
      toast.success(
        `Broadcast delivered! ${res.total_delivered} total subscribers notified (${res.telegram_recipients_count} Telegram, ${res.email_recipients_count} Email).`
      );
      onClose();
    } catch (err: any) {
      toast.error(err?.message || "Failed to send broadcast.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-primary/30 rounded-[12px] p-6 max-w-4xl w-full max-h-[92vh] overflow-y-auto space-y-4 shadow-2xl text-foreground font-sans">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="text-base font-bold flex items-center gap-2 text-primary">
            <Radio className="h-5 w-5 text-amber-500 animate-pulse" />
            Send Broadcast Announcement
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-sm font-bold cursor-pointer"
          >
            ✕
          </button>
        </div>

        <p className="text-xs text-muted-foreground font-sans">
          This message will be immediately dispatched to <span className="text-foreground font-medium">all active Telegram Bot subscribers</span>, <span className="text-foreground font-medium">registered Web users</span>, and <span className="text-foreground font-medium">Keyword search subscribers</span>.
        </p>

        <form onSubmit={handleSend} className="space-y-4 text-xs font-sans">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column: Input Form */}
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground block">Email Subject Line (Optional)</label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full bg-background border border-border rounded-[6px] p-2.5 text-foreground font-sans text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground block">Broadcast Message Content</label>
                <textarea
                  rows={8}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Write your recruitment alert announcement or update here..."
                  className="w-full bg-background border border-border rounded-[6px] p-3 text-foreground font-sans text-xs focus:outline-none focus:border-primary leading-relaxed"
                  required
                />
              </div>
            </div>

            {/* Right Column: Live Chat & Message Preview */}
            <div className="space-y-3 bg-muted/40 border border-border rounded-[8px] p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-border pb-2 mb-3">
                  <span className="font-bold text-xs uppercase tracking-wider text-muted-foreground">Live Message Preview</span>
                  <div className="flex items-center gap-1 bg-background border border-border rounded-[6px] p-0.5 text-[11px]">
                    <button
                      type="button"
                      onClick={() => setPreviewChannel("telegram")}
                      className={cn(
                        "px-2.5 py-1 rounded-[4px] font-semibold transition-colors cursor-pointer",
                        previewChannel === "telegram" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      Telegram Bot
                    </button>
                    <button
                      type="button"
                      onClick={() => setPreviewChannel("email")}
                      className={cn(
                        "px-2.5 py-1 rounded-[4px] font-semibold transition-colors cursor-pointer",
                        previewChannel === "email" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      Email Card
                    </button>
                  </div>
                </div>

                {previewChannel === "telegram" ? (
                  /* Telegram Chat Card Preview */
                  <div className="bg-[#17212b] border border-[#242f3d] text-[#f5f5f5] rounded-[10px] p-4 space-y-3 font-sans shadow-inner text-xs">
                    <div className="flex items-center gap-2 border-b border-[#242f3d] pb-2 text-[11px] text-[#6c7883]">
                      <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                      <span className="font-semibold text-[#8799a7]">GovAlert Bot</span>
                      <span className="bg-blue-500/20 text-blue-400 text-[10px] px-1.5 py-0.5 rounded font-mono">bot</span>
                    </div>

                    <div className="space-y-2">
                      <div className="font-bold text-[#64b5f6] flex items-center gap-1">
                        📢 Broadcast Preview
                      </div>
                      <div className="border-l-2 border-[#64b5f6] pl-3 py-1 bg-[#202b36]/60 rounded-r text-[#e1e1e1] whitespace-pre-wrap leading-relaxed text-xs">
                        {text.trim() || "Type your message on the left to see live Telegram chat card preview..."}
                      </div>
                      <div className="text-[11px] text-[#6c7883] pt-1">
                        ───────────────<br />
                        This broadcast will be delivered to active subscribers.
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Email Notification Card Preview */
                  <div className="bg-background border border-border text-foreground rounded-[10px] p-4 space-y-3 font-sans shadow-sm text-xs">
                    <div className="border-b border-border pb-2">
                      <div className="text-[10px] text-muted-foreground uppercase font-mono">Subject</div>
                      <div className="font-bold text-foreground text-xs">{subject || "No subject line"}</div>
                    </div>

                    <div className="space-y-2 py-1">
                      <div className="text-primary font-bold text-sm">RecruitmentAlert Announcement</div>
                      <div className="bg-muted/30 border border-border rounded-[6px] p-3 text-muted-foreground whitespace-pre-wrap leading-relaxed text-xs">
                        {text.trim() || "Type your broadcast message content on the left to see live Email card preview..."}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>RecruitmentAlert Nigeria</span>
                      <span className="text-primary font-medium">www.recruitmentalert.com.ng</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-[6px] hover:bg-muted text-muted-foreground text-xs font-semibold cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={sending || !text.trim()}
              className="px-5 py-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-[6px] text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Send className="h-3.5 w-3.5" /> Send Broadcast Now</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
