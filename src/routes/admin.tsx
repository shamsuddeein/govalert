import { createFileRoute, Outlet, Link, useLocation, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  ShieldAlert,
  Building2,
  Globe,
  Activity,
  Users,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Radio,
  PlusCircle,
  FileText,
} from "lucide-react";
import {
  adminApi,
  isAdminAuthenticated,
  getAdminUser,
  clearAdminTokens,
} from "../lib/adminApi";
import { Logo, ThemeToggle } from "../components/layout";
import { cn } from "../lib/utils";

export const Route = createFileRoute("/admin")({
  component: AdminLayout,
});

function AdminLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const isLoginPage = location.pathname === "/admin/login";

  const [pendingCount, setPendingCount] = useState<number>(0);
  const [onlineVisitors, setOnlineVisitors] = useState<number>(1);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [user, setUser] = useState(getAdminUser());

  // 1. Auth Guard for all /admin/* except /admin/login
  useEffect(() => {
    if (!isLoginPage && !isAdminAuthenticated()) {
      navigate({ to: "/admin/login" });
    }
  }, [isLoginPage, navigate, location.pathname]);

  // 2. Poll pending alerts count every 30 seconds
  useEffect(() => {
    if (isLoginPage || !isAdminAuthenticated()) return;

    const fetchStats = async () => {
      try {
        const [stats, userStats] = await Promise.all([
          adminApi.getAlertStats().catch(() => null),
          adminApi.getUserStats().catch(() => null),
        ]);
        if (stats && typeof stats.pending_count === "number") {
          setPendingCount(stats.pending_count);
        }
        if (userStats?.visitor_stats?.active_online_visitors !== undefined) {
          setOnlineVisitors(Math.max(1, userStats.visitor_stats.active_online_visitors));
        }
      } catch (e) {
        // Silently handle polling errors
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [isLoginPage]);

  // Sync user state & theme preference on navigation
  useEffect(() => {
    setUser(getAdminUser());
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [location.pathname]);

  const handleLogout = () => {
    clearAdminTokens();
    navigate({ to: "/admin/login" });
  };

  if (isLoginPage) {
    return <Outlet />;
  }

  const navItems = [
    {
      label: "Alert Queue",
      to: "/admin/alerts",
      icon: ShieldAlert,
      badge: pendingCount > 0 ? pendingCount : null,
    },
    {
      label: "Post New Job",
      to: "/admin/jobs-create",
      icon: PlusCircle,
    },
    {
      label: "Agencies",
      to: "/admin/agencies",
      icon: Building2,
    },
    {
      label: "Portals",
      to: "/admin/portals",
      icon: Globe,
    },
    {
      label: "Monitor Viewer",
      to: "/admin/monitor-viewer",
      icon: Radio,
    },
    {
      label: "System Health",
      to: "/admin/system-health",
      icon: Activity,
    },
    {
      label: "Blog Posts",
      to: "/admin/blog",
      icon: FileText,
    },
    {
      label: "Users",
      to: "/admin/users",
      icon: Users,
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans antialiased flex flex-col">
      {/* STEP 6: Top Brand Border Indicator (Nigerian Flag Green) */}
      <div className="h-[3px] w-full bg-[#0a5c38] dark:bg-[#3fb68e] shrink-0" />

      <div className="flex-1 flex flex-col md:flex-row min-h-0">
        {/* Mobile Nav Top Bar */}
        <div className="md:hidden flex items-center justify-between px-4 py-3 bg-card border-b border-border">
          <div className="flex items-center gap-2">
            <Logo />
            <span className="text-[11px] uppercase font-semibold tracking-wider bg-muted text-primary border border-border px-2 py-0.5 rounded-[6px] font-sans">
              ADMIN
            </span>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 text-muted-foreground hover:text-foreground rounded-md bg-muted"
              aria-label="Toggle navigation"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Sidebar (240px) */}
        <aside
          className={cn(
            "w-full md:w-60 bg-card border-r border-border flex flex-col justify-between shrink-0 transition-all z-30",
            mobileMenuOpen ? "block" : "hidden md:flex"
          )}
        >
          <div>
            {/* Logo & Admin Badge Header */}
            <div className="hidden md:flex flex-col gap-2 px-5 py-4 border-b border-border">
              <div className="flex items-center justify-between">
                <Logo />
                <span className="text-[10px] uppercase font-bold tracking-wider bg-muted text-primary border border-border px-2 py-0.5 rounded-[6px] font-sans">
                  Admin
                </span>
              </div>
            </div>

            {/* Navigation */}
            <nav className="p-3 space-y-1 font-sans">
              <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Navigation
              </div>
              {navItems.map((item) => {
                const isActive = location.pathname.startsWith(item.to);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center justify-between px-3 py-2.5 rounded-[6px] text-sm font-medium transition-all group font-sans",
                      isActive
                        ? "bg-muted text-primary border border-border"
                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0 transition-colors",
                          isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                        )}
                      />
                      <span>{item.label}</span>
                    </div>
                    {item.badge !== null && item.badge !== undefined && (
                      <span className="ml-auto font-mono text-[11px] bg-[color:var(--warning)]/15 text-[color:var(--warning)] border border-[color:var(--warning)]/30 font-semibold px-2 py-0.5 rounded-[6px]">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer : User Info & Logout */}
          <div className="p-3 border-t border-border bg-muted/30">
            <div className="flex items-center justify-between px-3 py-2 rounded-[6px] bg-card border border-border">
              <div className="overflow-hidden pr-2">
                <span className="block text-xs font-semibold text-foreground truncate font-sans">
                  {user?.username || "Admin User"}
                </span>
                <span
                  title={user?.email || "talktoshamsuddeein@gmail.com"}
                  className="block text-[11px] text-muted-foreground font-sans w-full max-w-[130px] whitespace-nowrap overflow-hidden text-ellipsis"
                >
                  {user?.email || "talktoshamsuddeein@gmail.com"}
                </span>
              </div>
              <button
                onClick={handleLogout}
                title="Log out"
                className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 bg-background flex flex-col min-h-screen">
          {/* Top bar header */}
          <header className="h-14 border-b border-border bg-card px-6 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 text-xs font-sans text-muted-foreground">
              <span className="text-muted-foreground font-medium">Admin</span>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-primary font-semibold capitalize">
                {location.pathname.replace("/admin/", "").replace("-", " ") || "Dashboard"}
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs font-sans">
              <ThemeToggle />
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-sans text-[11px] font-semibold">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                {onlineVisitors} {onlineVisitors === 1 ? "Visitor" : "Visitors"} Online
              </div>
              <div className="flex items-center gap-2 px-2.5 py-1 rounded-[6px] bg-muted border border-border text-primary font-sans text-[11px] font-semibold">
                <span className="h-2 w-2 rounded-full bg-[#0a5c38] animate-pulse" />
                API Connected
              </div>
            </div>
          </header>

          {/* Dynamic page content */}
          <div className="p-6 md:p-8 flex-1">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
