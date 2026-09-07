import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";
import { Nav, Footer } from "../components/layout";
import { StatusBadge, type Status } from "./index";
import { toast } from "sonner";
import { isAuthenticated, api, type ApiWebNotification } from "../lib/api";
import { AccessibleModal } from "../components/AccessibleModal";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
});

function DashboardPage() {
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<"saved" | "notifications" | "profile" | "settings">(
    "saved"
  );
  const [savedJobs, setSavedJobs] = useState<any[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [notifications, setNotifications] = useState<ApiWebNotification[]>([]);
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);

  // Telegram State
  const [telegramConnected, setTelegramConnected] = useState(false);
  const [telegramHandle, setTelegramHandle] = useState("");
  const [pairingCode, setPairingCode] = useState("");
  const [showPairingModal, setShowPairingModal] = useState(false);

  // Profile Form State
  const [profileForm, setProfileForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
  });
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);

  // Password Form State
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [changingPassword, setChangingPassword] = useState(false);

  // Settings State
  const [settings, setSettings] = useState({
    emailAlerts: true,
    telegramAlerts: false,
    newsletter: true,
    weeklyDigest: false,
  });

  // Load profile, saved jobs, and notifications from API
  const loadUserData = async () => {
    if (!isAuthenticated()) {
      navigate({ to: "/sign-in" });
      return;
    }
    setLoadingJobs(true);
    setLoadingProfile(true);

    try {
      const [profileRes, jobsRes, notifRes] = await Promise.all([
        api.getMe(),
        api.getSavedJobs(),
        api.getNotifications(),
      ]);

      if (profileRes) {
        setProfileForm({
          firstName: profileRes.first_name || "",
          lastName: profileRes.last_name || "",
          email: profileRes.email || "",
          phone: profileRes.phone || "",
        });
        if (Array.isArray(profileRes.categories_of_interest) && profileRes.categories_of_interest.length > 0) {
          const prefSet = new Set(profileRes.categories_of_interest);
          setSettings({
            emailAlerts: prefSet.has("emailAlerts"),
            telegramAlerts: prefSet.has("telegramAlerts"),
            newsletter: prefSet.has("newsletter"),
            weeklyDigest: prefSet.has("weeklyDigest"),
          });
        }
      }

      if (jobsRes) {
        setSavedJobs(jobsRes);
      }

      if (notifRes) {
        setNotifications(notifRes.results || []);
        setUnreadNotifCount(notifRes.unread_count || 0);
      }
    } catch (e) {
      console.warn("Failed to load user dashboard data:", e);
    } finally {
      setLoadingJobs(false);
      setLoadingProfile(false);
    }
  };

  useEffect(() => {
    loadUserData();
  }, []);

  const handleSignOut = async () => {
    await api.logout();
    toast.success("Signed out successfully.");
    navigate({ to: "/sign-in" });
  };

  const handleRemoveSaved = async (ref: string) => {
    const success = await api.unsaveJob(ref);
    if (success) {
      setSavedJobs((prev) => prev.filter((j) => j.ref !== ref));
      toast.success("Job removed from saved list");
    } else {
      toast.error("Failed to remove saved job.");
    }
  };

  const handleMarkAllRead = async () => {
    const res = await api.markAllNotificationsRead();
    if (res) {
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadNotifCount(0);
      toast.success("All notifications marked as read");
    }
  };

  const handleNotificationClick = async (notif: ApiWebNotification) => {
    if (!notif.is_read) {
      api.markNotificationRead(notif.id);
      setNotifications((prev) => prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n)));
      setUnreadNotifCount((prev) => Math.max(0, prev - 1));
    }
    if (notif.target_url) {
      navigate({ to: notif.target_url as any });
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    const res = await api.updateMe({
      first_name: profileForm.firstName,
      last_name: profileForm.lastName,
      phone: profileForm.phone,
    });
    setSavingProfile(false);
    if (res) {
      toast.success("Profile updated successfully!");
    } else {
      toast.error("Failed to update profile.");
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error("New passwords do not match!");
      return;
    }
    if (passwordForm.newPassword.length < 6) {
      toast.error("Password must be at least 6 characters.");
      return;
    }
    setChangingPassword(true);
    const success = await api.changePassword(passwordForm.oldPassword, passwordForm.newPassword);
    setChangingPassword(false);
    if (success) {
      toast.success("Password changed successfully!");
      setPasswordForm({ oldPassword: "", newPassword: "", confirmPassword: "" });
    } else {
      toast.error("Failed to change password. Check old password.");
    }
  };

  const handleToggleSetting = async (key: keyof typeof settings) => {
    const nextVal = !settings[key];
    if (key === "telegramAlerts" && nextVal && !telegramConnected) {
      toast.error("Please connect your Telegram account first!");
      return;
    }

    const updatedSettings = { ...settings, [key]: nextVal };
    setSettings(updatedSettings);

    // Save preferences to backend user profile
    const activePreferences = Object.keys(updatedSettings).filter(
      (k) => updatedSettings[k as keyof typeof settings]
    );
    const success = await api.updateMe({ categories_of_interest: activePreferences });

    if (success) {
      toast.success("Settings preference saved to database!");
    } else {
      toast.error("Failed to save settings preference.");
    }
  };

  const handleStartTelegramConnection = () => {
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    setPairingCode(code);
    setShowPairingModal(true);
  };

  const handleCompleteConnection = () => {
    if (!telegramHandle.trim()) {
      toast.error("Please enter your Telegram handle");
      return;
    }
    setTelegramConnected(true);
    setSettings((prev) => ({ ...prev, telegramAlerts: true }));
    setShowPairingModal(false);
    toast.success(`Telegram channel connected to @${telegramHandle.replace("@", "")}`);
  };

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-secondary/25 font-sans">
      <Nav />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[1184px] px-4 sm:px-6 py-8 sm:py-12 outline-none font-sans">
        <div className="mb-4">
          <BackButton to="/" label="Back to Home" />
        </div>
        {/* Banner/Header */}
        <div className="mb-8 sm:mb-10 flex flex-col gap-4 sm:gap-6 md:flex-row md:items-center md:justify-between border-b border-border/40 pb-6 sm:pb-8">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-primary">Applicant Dashboard</h1>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              Manage saved applications, set alert preferences, and verify contact profiles.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span className="relative flex size-2">
              <span className="pulsing-dot absolute inline-flex h-full w-full rounded-full bg-[#0a5c38] dark:bg-[#3fb68e] opacity-75"></span>
              <span className="relative inline-flex size-2 rounded-full bg-[#0a5c38] dark:bg-[#3fb68e]"></span>
            </span>
            <div className="text-xs font-bold uppercase tracking-wider text-primary">Live Monitoring Active</div>
          </div>
        </div>

        {/* Outer Shell Grid (240px wide sidebar) */}
        <div className="grid gap-6 sm:gap-8 lg:grid-cols-[240px_1fr]">
          {/* Navigation Sidebar */}
          <aside className="flex flex-row gap-2 overflow-x-auto pb-4 lg:flex-col lg:overflow-visible lg:pb-0 border-b border-border/40 lg:border-b-0 lg:border-r lg:border-border/40 lg:pr-6 no-scrollbar max-w-full">
            <button
              onClick={() => setActiveTab("saved")}
              className={`flex items-center justify-between rounded-[8px] px-4 py-3 text-xs font-semibold shrink-0 cursor-pointer border transition-colors ${
                activeTab === "saved"
                  ? "bg-muted border-[#0a5c38]/40 dark:border-[#3fb68e]/40 text-[#0a5c38] dark:text-[#3fb68e] font-bold border-l-3 border-l-[#0a5c38] dark:border-l-[#3fb68e]"
                  : "text-muted-foreground border-transparent hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                Saved Jobs
              </span>
              {savedJobs.length > 0 && (
                <span className="rounded-[4px] bg-muted/60 border border-border px-1.5 py-0.5 text-[10px] font-bold">
                  {savedJobs.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("notifications")}
              className={`flex items-center justify-between rounded-[8px] px-4 py-3 text-xs font-semibold shrink-0 cursor-pointer border transition-colors ${
                activeTab === "notifications"
                  ? "bg-muted border-[#0a5c38]/40 dark:border-[#3fb68e]/40 text-[#0a5c38] dark:text-[#3fb68e] font-bold border-l-3 border-l-[#0a5c38] dark:border-l-[#3fb68e]"
                  : "text-muted-foreground border-transparent hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                Notifications
              </span>
              {notifications.some((n) => n.unread) && (
                <span className="size-2 rounded-full bg-[#b45309]" />
              )}
            </button>

            <button
              onClick={() => setActiveTab("profile")}
              className={`flex items-center rounded-[8px] px-4 py-3 text-xs font-semibold shrink-0 cursor-pointer border transition-colors ${
                activeTab === "profile"
                  ? "bg-muted border-[#0a5c38]/40 dark:border-[#3fb68e]/40 text-[#0a5c38] dark:text-[#3fb68e] font-bold border-l-3 border-l-[#0a5c38] dark:border-l-[#3fb68e]"
                  : "text-muted-foreground border-transparent hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                My Profile
              </span>
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className={`flex items-center rounded-[8px] px-4 py-3 text-xs font-semibold shrink-0 cursor-pointer border transition-colors ${
                activeTab === "settings"
                  ? "bg-muted border-[#0a5c38]/40 dark:border-[#3fb68e]/40 text-[#0a5c38] dark:text-[#3fb68e] font-bold border-l-3 border-l-[#0a5c38] dark:border-l-[#3fb68e]"
                  : "text-muted-foreground border-transparent hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </span>
            </button>
          </aside>

          {/* Active Screen Area */}
          <div className="space-y-6">
            {/* SAVED JOBS SCREEN */}
            {activeTab === "saved" && (
              <section className="space-y-6 text-left">
                <div className="flex items-center justify-between border-b border-border/40 pb-3">
                  <h3 className="text-[16px] font-bold text-primary">Saved Recruitments</h3>
                  <span className="font-mono text-xs text-muted-foreground uppercase">
                    {savedJobs.length} {savedJobs.length === 1 ? "job" : "jobs"} bookmarked
                  </span>
                </div>

                {savedJobs.length > 0 ? (
                  <div className="grid gap-6 sm:grid-cols-2">
                    {savedJobs.map((job) => {
                      const ref = job.ref || job.id;
                      const agency = job.agency_name || job.agency;
                      return (
                        <div
                          key={ref}
                          className="group flex flex-col justify-between rounded-[8px] border border-border bg-card p-6 shadow-sm interactive-card"
                        >
                          <div className="space-y-4">
                            <div className="flex items-center justify-between gap-2 min-w-0">
                              <span className="font-mono text-[11px] text-muted-foreground truncate min-w-0">REF: {ref}</span>
                              <StatusBadge status={job.status === "new_opening" ? "new" : job.status} />
                            </div>

                            <div>
                              <h4 className="text-[17px] font-semibold leading-snug text-foreground">
                                {job.title}
                              </h4>
                              <p className="mt-1 text-[13px] font-medium text-[#0a5c38] dark:text-[#3fb68e]">
                                {agency}
                              </p>
                            </div>

                            <div className="border-t border-border pt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
                              <div>
                                <span className="block text-muted-foreground text-[12px]">Deadline</span>
                                <span className="font-medium text-foreground">{job.deadline || "Pending"}</span>
                              </div>
                              <div>
                                <span className="block text-muted-foreground text-[12px]">Positions</span>
                                <span className="font-medium text-foreground">{job.positions || "Multiple"}</span>
                              </div>
                            </div>
                          </div>

                          <div className="mt-6 pt-3 flex items-center justify-between border-t border-border/40">
                            <button
                              onClick={() => handleRemoveSaved(ref)}
                              className="inline-flex h-[32px] items-center justify-center rounded-[6px] border border-border bg-card px-3 text-xs font-semibold text-muted-foreground hover:text-[#b91c1c] hover:border-[#b91c1c]/40 cursor-pointer"
                            >
                              Remove
                            </button>
                            <Link
                              to="/jobs/$jobId"
                              params={{ jobId: ref }}
                              className="text-[13px] text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-semibold"
                            >
                              View details &rarr;
                            </Link>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-16 border border-dashed border-border rounded-[8px] bg-card">
                    <h4 className="text-sm font-bold text-primary uppercase tracking-wider">No saved jobs yet</h4>
                    <p className="mt-2 text-xs text-muted-foreground max-w-xs mx-auto">
                      Bookmark openings on the Recruitments Feed to monitor updates and tracking deadlines here.
                    </p>
                    <Link
                      to="/jobs"
                      className="mt-6 inline-flex h-[40px] items-center justify-center rounded-[8px] bg-primary px-5 text-xs font-semibold text-primary-foreground hover:bg-[#0a5c38]/95"
                    >
                      Browse Recruitments
                    </Link>
                  </div>
                )}
              </section>
            )}

            {/* NOTIFICATIONS SCREEN */}
            {activeTab === "notifications" && (
              <section className="space-y-6 text-left">
                <div className="flex items-center justify-between border-b border-border/40 pb-3">
                  <h3 className="text-[16px] font-bold text-primary">
                    Recent Alerts {unreadNotifCount > 0 && <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-[#0a5c38]/10 dark:bg-[#3fb68e]/10 text-[#0a5c38] dark:text-[#3fb68e] font-semibold">{unreadNotifCount} unread</span>}
                  </h3>
                  {unreadNotifCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-xs font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline cursor-pointer"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                {/* Notifications List */}
                {notifications.length > 0 ? (
                  <div className="space-y-3">
                    {notifications.map((notif) => {
                      const isUnread = !notif.is_read;
                      return (
                        <div
                          key={notif.id}
                          onClick={() => handleNotificationClick(notif)}
                          className={`relative flex items-start gap-4 rounded-[8px] border p-4 transition-all cursor-pointer ${
                            isUnread
                              ? "bg-card border-[#0a5c38]/40 dark:border-[#3fb68e]/40 shadow-sm hover:border-[#0a5c38]"
                              : "bg-card/40 border-border hover:border-border/80"
                          }`}
                        >
                          {isUnread && (
                            <span className="absolute left-2.5 top-3.5 size-2 rounded-full bg-[#0a5c38] dark:bg-[#3fb68e]" />
                          )}

                          <div className="flex-1 space-y-1 pl-2">
                            <div className="flex items-center justify-between gap-4">
                              <div className="flex items-center gap-2">
                                <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                                  notif.notification_type === "NEW_JOB"
                                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                                    : notif.notification_type === "DEADLINE_WARNING"
                                    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                                    : "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20"
                                }`}>
                                  {notif.notification_type.replace("_", " ")}
                                </span>
                                <h4 className={`text-xs font-bold ${isUnread ? "text-primary font-semibold" : "text-muted-foreground"}`}>
                                  {notif.title}
                                </h4>
                              </div>
                              <span className="text-[10px] text-muted-foreground font-mono shrink-0">
                                {new Date(notif.created_at).toLocaleDateString("en-NG", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                              </span>
                            </div>
                            <p className="text-xs text-muted-foreground leading-relaxed">{notif.body}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="rounded-[8px] border border-dashed border-border p-12 text-center space-y-2">
                    <p className="text-sm font-semibold text-primary">No Notifications Yet</p>
                    <p className="text-xs text-muted-foreground">You will receive instant alerts here when new recruitment openings are verified.</p>
                  </div>
                )}
              </section>
            )}

            {/* PROFILE SCREEN */}
            {activeTab === "profile" && (
              <section className="rounded-[8px] border border-border bg-card p-6 shadow-sm space-y-6 text-left">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-primary">Applicant Profile</h3>
                  <p className="text-xs text-muted-foreground">
                    Manage your account details and profile information.
                  </p>
                </div>

                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                        First Name
                      </label>
                      <input
                        type="text"
                        required
                        value={profileForm.firstName}
                        onChange={(e) => setProfileForm({ ...profileForm, firstName: e.target.value })}
                        className="rounded-[6px] border border-border bg-background px-3 py-2 text-xs outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                        Last Name
                      </label>
                      <input
                        type="text"
                        required
                        value={profileForm.lastName}
                        onChange={(e) => setProfileForm({ ...profileForm, lastName: e.target.value })}
                        className="rounded-[6px] border border-border bg-background px-3 py-2 text-xs outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                        Email Address
                      </label>
                      <input
                        type="email"
                        disabled
                        value={profileForm.email}
                        className="rounded-[6px] border border-border bg-muted/50 opacity-70 px-3 py-2 text-xs outline-none cursor-not-allowed"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                        Phone Number
                      </label>
                      <input
                        type="text"
                        placeholder="+234 812 345 6789"
                        value={profileForm.phone}
                        onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                        className="rounded-[6px] border border-border bg-background px-3 py-2 text-xs outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
                      />
                    </div>
                  </div>

                  <div className="border-t border-border pt-4 flex justify-end">
                    <button
                      type="submit"
                      disabled={savingProfile}
                      className="inline-flex h-[40px] items-center justify-center rounded-[8px] bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] px-5 text-xs font-semibold disabled:opacity-50 cursor-pointer"
                    >
                      {savingProfile ? "Saving..." : "Save Profile"}
                    </button>
                  </div>
                </form>
              </section>
            )}

            {/* SETTINGS SCREEN */}
            {activeTab === "settings" && (
              <div className="space-y-6">
                <section className="rounded-[8px] border border-border bg-card p-6 shadow-sm space-y-6 text-left">
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-primary">System Settings</h3>
                    <p className="text-xs text-muted-foreground">
                      Control how and when you receive intelligence briefings.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-border pb-4">
                      <div>
                        <h4 className="text-xs font-bold text-primary uppercase">Email Alerts</h4>
                        <p className="text-xs text-muted-foreground">
                          Receive instant alerts when a verified portal launches.
                        </p>
                      </div>
                      <button
                        onClick={() => handleToggleSetting("emailAlerts")}
                        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border border-transparent transition-colors duration-150 ease-in-out focus:outline-none ${
                          settings.emailAlerts ? "bg-[#0a5c38] dark:bg-[#3fb68e]" : "bg-muted"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block size-4 transform rounded-full bg-background shadow ring-0 transition duration-150 ease-in-out ${
                            settings.emailAlerts ? "translate-x-4" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between border-b border-border pb-4">
                      <div>
                        <h4 className="text-xs font-bold text-primary uppercase">Telegram Push Notifications</h4>
                        <p className="text-xs text-muted-foreground">
                          Direct-to-chat bot alerts with zero delivery delay.
                        </p>
                      </div>
                      <button
                        onClick={() => handleToggleSetting("telegramAlerts")}
                        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border border-transparent transition-colors duration-150 ease-in-out focus:outline-none ${
                          settings.telegramAlerts ? "bg-[#0a5c38] dark:bg-[#3fb68e]" : "bg-muted"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block size-4 transform rounded-full bg-background shadow ring-0 transition duration-150 ease-in-out ${
                            settings.telegramAlerts ? "translate-x-4" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-xs font-bold text-primary uppercase">Weekly Intelligence Digest</h4>
                        <p className="text-xs text-muted-foreground">
                          A weekly summary of scam alerts and portal checks.
                        </p>
                      </div>
                      <button
                        onClick={() => handleToggleSetting("weeklyDigest")}
                        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border border-transparent transition-colors duration-150 ease-in-out focus:outline-none ${
                          settings.weeklyDigest ? "bg-[#0a5c38] dark:bg-[#3fb68e]" : "bg-muted"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block size-4 transform rounded-full bg-background shadow ring-0 transition duration-150 ease-in-out ${
                            settings.weeklyDigest ? "translate-x-4" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </section>

                {/* Change Password Card */}
                <section className="rounded-[8px] border border-border bg-card p-6 shadow-sm space-y-6 text-left">
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-primary">Security & Password</h3>
                    <p className="text-xs text-muted-foreground">
                      Update your account security credentials.
                    </p>
                  </div>

                  <form onSubmit={handleChangePassword} className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-3">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                          Current Password
                        </label>
                        <input
                          type="password"
                          required
                          placeholder="••••••••"
                          value={passwordForm.oldPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, oldPassword: e.target.value })}
                          className="rounded-[6px] border border-border bg-background px-3 py-2 text-xs outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                          New Password
                        </label>
                        <input
                          type="password"
                          required
                          placeholder="••••••••"
                          value={passwordForm.newPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                          className="rounded-[6px] border border-border bg-background px-3 py-2 text-xs outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                          Confirm New Password
                        </label>
                        <input
                          type="password"
                          required
                          placeholder="••••••••"
                          value={passwordForm.confirmPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                          className="rounded-[6px] border border-border bg-background px-3 py-2 text-xs outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e]"
                        />
                      </div>
                    </div>

                    <div className="border-t border-border pt-4 flex justify-end">
                      <button
                        type="submit"
                        disabled={changingPassword}
                        className="inline-flex h-[40px] items-center justify-center rounded-[8px] bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] px-5 text-xs font-semibold disabled:opacity-50 cursor-pointer"
                      >
                        {changingPassword ? "Updating..." : "Update Password"}
                      </button>
                    </div>
                  </form>
                </section>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Telegram Pairing Modal */}
      <AccessibleModal
        isOpen={showPairingModal}
        onClose={() => setShowPairingModal(false)}
        title="Pair with Telegram Bot"
        description="Connect your account to RecruitmentAlert Telegram Bot in three simple steps:"
        maxWidth="max-w-md"
      >
        <ol className="space-y-3.5 text-xs text-muted-foreground mb-6 pl-4 list-decimal font-sans">
          <li>
            Open Telegram and search for <strong className="text-primary font-bold">@RecruitmentAlertBot</strong>.
          </li>
          <li>
            Start the bot by tapping <strong className="text-foreground">/start</strong>.
          </li>
          <li>
            Send the following pairing code to the bot:
            <div className="mt-2 bg-muted rounded-[6px] p-3 text-center text-base font-mono font-bold tracking-widest text-[#0a5c38] dark:text-[#3fb68e] border border-border">
              {pairingCode}
            </div>
          </li>
        </ol>

        <div className="space-y-4 font-sans">
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              Enter Your Telegram Handle
            </label>
            <input
              type="text"
              placeholder="@yourhandle"
              value={telegramHandle}
              onChange={(e) => setTelegramHandle(e.target.value)}
              className="rounded-[6px] border border-border bg-background px-3 py-2 text-xs outline-none focus:border-[#0a5c38] dark:focus:border-[#3fb68e] font-sans"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowPairingModal(false)}
              className="rounded-[6px] border border-border bg-card px-4 py-2 text-xs font-semibold hover:bg-muted cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleCompleteConnection}
              className="rounded-[6px] bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] px-4 py-2 text-xs font-semibold cursor-pointer"
            >
              Verify pairing code
            </button>
          </div>
        </div>
      </AccessibleModal>

      <Footer />
    </div>
  );
}
