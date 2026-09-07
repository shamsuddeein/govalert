import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Users,
  Search,
  Filter,
  UserCheck,
  UserX,
  MessageSquare,
  Globe,
  Bell,
  RefreshCw,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";
import {
  adminApi,
  AdminUserRecord,
  AdminUserStats,
} from "../lib/adminApi";
import { cn } from "../lib/utils";

export const Route = createFileRoute("/admin/users")({
  component: AdminUsersComponent,
});

function stripEmojis(text?: string | null): string {
  if (!text) return "";
  return text
    .replace(/[\p{Extended_Pictographic}\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}]/gu, "")
    .trim();
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

function AdminUsersComponent() {
  const [users, setUsers] = useState<AdminUserRecord[]>([]);
  const [stats, setStats] = useState<AdminUserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [userTypeFilter, setUserTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const loadData = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const [usersRes, statsRes] = await Promise.all([
        adminApi.getUsers({
          search: search || undefined,
          user_type: userTypeFilter === "all" ? undefined : userTypeFilter,
          status: statusFilter === "all" ? undefined : statusFilter,
          page,
        }),
        adminApi.getUserStats(),
      ]);

      setUsers(usersRes.results || []);
      setTotalCount(usersRes.count || 0);
      setStats(statsRes);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load registered users data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [search, userTypeFilter, statusFilter, page]);

  const handleToggleActive = async (user: AdminUserRecord) => {
    setTogglingId(user.id);
    try {
      const res = await adminApi.toggleUserActive(user.user_type, user.raw_id);
      const newStatus = res.is_active ? "activated" : "suspended";
      toast.success(`User '${user.display_name}' has been ${newStatus}.`);
      loadData();
    } catch (err: any) {
      toast.error(err?.message || `Failed to update status for '${user.display_name}'.`);
    } finally {
      setTogglingId(null);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto font-sans antialiased">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2.5">
            <Users className="h-6 w-6 text-primary" />
            Registered Users & Subscribers
          </h1>
          <p className="text-xs text-muted-foreground mt-1 font-sans">
            Monitor registered web user accounts, Telegram bot subscribers, and keyword alert watchers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="px-3 py-1.5 bg-muted hover:bg-muted/80 text-foreground text-xs font-sans font-semibold rounded-[6px] transition-all flex items-center gap-2 border border-border cursor-pointer"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", refreshing && "animate-spin text-primary")} />
            <span>Refresh Roster</span>
          </button>
        </div>
      </div>

      {/* 1. Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-sans">
        {/* Total Web Users */}
        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Web App Users</span>
            <Globe className="h-4 w-4 text-primary" />
          </div>
          <div className="text-2xl font-bold font-sans text-foreground">
            {stats?.total_web_users ?? 0}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">
            {stats?.active_web_users ?? 0} active accounts
          </div>
        </div>

        {/* Telegram Subscribers */}
        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Telegram Bot</span>
            <MessageSquare className="h-4 w-4 text-[#0a5c38] dark:text-[#3fb68e]" />
          </div>
          <div className="text-2xl font-bold font-sans text-[#0a5c38] dark:text-[#3fb68e]">
            {stats?.total_telegram_subscribers ?? 0}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">
            {stats?.active_telegram_subscribers ?? 0} active bot users
          </div>
        </div>

        {/* Keyword Subscribers */}
        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Keyword Watchers</span>
            <Bell className="h-4 w-4 text-[color:var(--warning)]" />
          </div>
          <div className="text-2xl font-bold font-sans text-[color:var(--warning)]">
            {stats?.total_keyword_subscribers ?? 0}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">
            {stats?.active_keyword_subscriptions ?? 0} active subscriptions
          </div>
        </div>

        {/* New Users Today */}
        <div className="bg-card border border-border rounded-[8px] p-4 space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-muted-foreground text-xs font-sans font-semibold">
            <span>Registered Today</span>
            <UserCheck className="h-4 w-4 text-primary" />
          </div>
          <div className="text-2xl font-bold font-sans text-primary">
            {stats?.new_web_users_today ?? 0}
          </div>
          <div className="text-[11px] text-muted-foreground font-sans">New web registrations</div>
        </div>
      </div>

      {/* 2. Controls & Search Filter Bar */}
      <div className="bg-card border border-border rounded-[8px] p-4 space-y-4 shadow-sm font-sans">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by email, username, or Telegram ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 bg-muted/50 border border-border rounded-[6px] text-xs font-sans placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            {/* User Type Filter */}
            <div className="flex items-center gap-1.5">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              <select
                value={userTypeFilter}
                onChange={(e) => {
                  setUserTypeFilter(e.target.value);
                  setPage(1);
                }}
                className="bg-muted border border-border rounded-[6px] px-2.5 py-1.5 text-xs font-sans font-medium text-foreground focus:outline-none"
              >
                <option value="all">All User Types</option>
                <option value="web">Web Users</option>
                <option value="telegram">Telegram Subscribers</option>
                <option value="keyword">Keyword Watchers</option>
              </select>
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-muted border border-border rounded-[6px] px-2.5 py-1.5 text-xs font-sans font-medium text-foreground focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive / Blocked</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. User Roster Table */}
      <div className="bg-card border border-border rounded-[8px] shadow-sm overflow-hidden font-sans">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-muted-foreground gap-2 text-xs">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span>Loading user directory...</span>
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground space-y-2">
            <UserX className="h-8 w-8 mx-auto text-muted-foreground/60" />
            <p className="text-sm font-semibold text-foreground">No registered users found</p>
            <p className="text-xs text-muted-foreground">
              Try refining your search keyword or clearing user type filters.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-muted-foreground font-semibold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">User Info</th>
                  <th className="py-3 px-4">Platform</th>
                  <th className="py-3 px-4">Identifier / Detail</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Joined Date</th>
                  <th className="py-3 px-4">Last Active</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map((u) => {
                  const isTg = u.user_type === "TELEGRAM";
                  const isKw = u.user_type === "KEYWORD_SUBSCRIBER";
                  const isWeb = u.user_type === "WEB";
                  const sanitizedName = stripEmojis(u.display_name) || u.username || "User";

                  return (
                    <tr key={u.id} className="h-[48px] hover:bg-muted/30 transition-colors">
                      {/* User Info */}
                      <td className="h-[48px] py-1.5 px-4 whitespace-nowrap overflow-hidden text-ellipsis max-w-[220px]">
                        <div className="font-semibold text-foreground whitespace-nowrap overflow-hidden text-ellipsis leading-tight" title={sanitizedName}>
                          {sanitizedName}
                        </div>
                        {u.email && (
                          <div className="text-[11px] text-muted-foreground whitespace-nowrap overflow-hidden text-ellipsis leading-tight" title={u.email}>
                            {u.email}
                          </div>
                        )}
                      </td>

                      {/* Platform */}
                      <td className="h-[48px] py-1.5 px-4 whitespace-nowrap">
                        {isWeb && (u.platform === "Google" || u.auth_provider === "google") && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 text-[10px] font-bold uppercase">
                            <svg className="size-3 shrink-0" viewBox="0 0 24 24">
                              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22-.03-.63z" />
                              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                            </svg>
                            Google
                          </span>
                        )}
                        {isWeb && u.platform !== "Google" && u.auth_provider !== "google" && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-primary/10 text-primary border border-primary/20 text-[10px] font-bold uppercase">
                            <Globe className="h-3 w-3" /> Web User
                          </span>
                        )}
                        {isTg && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-[#0a5c38]/10 text-[#0a5c38] dark:text-[#3fb68e] border border-[#0a5c38]/20 text-[10px] font-bold uppercase">
                            <MessageSquare className="h-3 w-3" /> Telegram
                          </span>
                        )}
                        {isKw && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-[color:var(--warning)]/10 text-[color:var(--warning)] border border-[color:var(--warning)]/20 text-[10px] font-bold uppercase">
                            <Bell className="h-3 w-3" /> Keyword Watcher
                          </span>
                        )}
                      </td>

                      {/* Identifier / Detail */}
                      <td className="h-[48px] py-1.5 px-4 font-mono text-[11px] whitespace-nowrap overflow-hidden text-ellipsis max-w-[180px]">
                        {isTg && u.telegram_id && (
                          <span className="text-foreground font-semibold">ID: {u.telegram_id}</span>
                        )}
                        {isKw && u.query_text && (
                          <span className="text-muted-foreground">Keyword: "{u.query_text}"</span>
                        )}
                        {isWeb && (
                          <span className="text-muted-foreground">{u.email}</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="h-[48px] py-1.5 px-4 whitespace-nowrap">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-[#0a5c38]/10 text-[#0a5c38] dark:text-[#3fb68e] border border-[#0a5c38]/30 font-semibold text-[10px]">
                            <span className="h-1.5 w-1.5 rounded-full bg-[#0a5c38] dark:bg-[#3fb68e]" />
                            ACTIVE
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-destructive/10 text-destructive border border-destructive/30 font-semibold text-[10px]">
                            <span className="h-1.5 w-1.5 rounded-full bg-destructive" />
                            {u.state || "INACTIVE"}
                          </span>
                        )}
                      </td>

                      {/* Joined Date */}
                      <td className="h-[48px] py-1.5 px-4 text-muted-foreground font-mono text-[11px] whitespace-nowrap">
                        {u.date_joined ? new Date(u.date_joined).toLocaleDateString() : "Unknown"}
                      </td>

                      {/* Last Active */}
                      <td className="h-[48px] py-1.5 px-4 text-muted-foreground font-mono text-[11px] whitespace-nowrap">
                        {timeAgo(u.last_login)}
                      </td>

                      {/* Action */}
                      <td className="h-[48px] py-1.5 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => handleToggleActive(u)}
                          disabled={togglingId === u.id}
                          className={cn(
                            "px-2.5 py-1 rounded-[4px] text-[11px] font-semibold transition-all border cursor-pointer inline-flex items-center gap-1",
                            u.is_active
                              ? "bg-destructive/10 text-destructive border-destructive/30 hover:bg-destructive/20"
                              : "bg-[#0a5c38]/10 text-[#0a5c38] dark:text-[#3fb68e] border-[#0a5c38]/30 hover:bg-[#0a5c38]/20"
                          )}
                        >
                          {togglingId === u.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : u.is_active ? (
                            <>
                              <UserX className="h-3 w-3" /> Suspend
                            </>
                          ) : (
                            <>
                              <UserCheck className="h-3 w-3" /> Reactivate
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
