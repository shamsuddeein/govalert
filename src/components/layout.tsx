import { useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { isAuthenticated, api } from "../lib/api";
import { requestAndSubscribeWebPush } from "../lib/pushManager";

export function Logo() {
  return (
    <div className="flex items-center gap-2 shrink-0">
      <Link to="/" className="flex items-center gap-1.5 sm:gap-2 hover:opacity-90 shrink-0">
        <svg
          className="size-[20px] sm:size-[24px] text-[#0a5c38] dark:text-[#3fb68e] shrink-0"
          viewBox="0 0 24 28"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          {/* Document outline */}
          <path d="M4 3h11l5 5v17a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
          <path d="M15 3v5h5" />
          {/* Checkmark */}
          <path d="M8 16.5l3 3 6-7" />
        </svg>
        <span className="text-sm xs:text-base sm:text-lg tracking-tight text-foreground font-sans truncate">
          <span className="font-bold">Recruitment</span>
          <span className="font-normal">Alert</span>
        </span>
      </Link>
    </div>
  );
}

interface ThemeToggleProps {
  storageKey?: string;
}

export function ThemeToggle({ storageKey }: ThemeToggleProps = {}) {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      setTheme("dark");
      document.documentElement.classList.add("dark");
    } else {
      setTheme("light");
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("theme", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  return (
    <button
      onClick={toggleTheme}
      className="inline-flex w-[36px] h-[36px] items-center justify-center rounded-full bg-transparent text-muted-foreground hover:bg-[#F3F4F6] dark:hover:bg-[#1f2937] hover:text-foreground transition-colors cursor-pointer border-0 shrink-0 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0a5c38] dark:focus-visible:ring-[#3fb68e]"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
    >
      {theme === "light" ? (
        <svg
          className="size-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"
          />
        </svg>
      ) : (
        <svg
          className="size-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 3v2.25m0 13.5V21M4.22 4.22l1.59 1.59m12.38 12.38l1.59 1.59M3 12h2.25m13.5 0H21M5.81 18.19l-1.59 1.59m12.38-12.38l-1.59 1.59M12 7.5a4.5 4.5 0 110 9 4.5 4.5 0 010-9z"
          />
        </svg>
      )}
    </button>
  );
}

export function Nav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const isAuthed = isAuthenticated();
    setAuthed(isAuthed);
    if (isAuthed) {
      api.getNotifications({ unread: true }).then((res) => {
        if (res) setUnreadCount(res.unread_count || 0);
      });
    }
  }, []);

  const handleLogout = async () => {
    await api.logout();
    setAuthed(false);
    window.location.href = "/sign-in";
  };

  return (
    <>
      {/* Brand Top Border Indicator (Nigerian Flag Green) */}
      <div className="h-[3px] w-full bg-[#0a5c38] dark:bg-[#3fb68e]" />

      <nav className="sticky top-0 z-50 border-b border-border bg-background h-[60px]">
        <div className="mx-auto flex h-full max-w-[1184px] items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3 md:gap-8 min-w-0 shrink">
            <Logo />
            <div className="hidden gap-6 md:flex">
              <Link
                to="/"
                className="nav-link-underline text-[14px] font-medium text-muted-foreground transition-colors hover:text-primary py-1"
                activeProps={{ className: "text-primary font-semibold" }}
              >
                Home
              </Link>
              <Link
                to="/jobs"
                className="nav-link-underline text-[14px] font-medium text-muted-foreground transition-colors hover:text-primary py-1"
                activeProps={{ className: "text-primary font-semibold" }}
              >
                Jobs
              </Link>
              <Link
                to="/agencies"
                className="nav-link-underline text-[14px] font-medium text-muted-foreground transition-colors hover:text-primary py-1"
                activeProps={{ className: "text-primary font-semibold" }}
              >
                Agencies
              </Link>
              <Link
                to="/verification"
                className="nav-link-underline text-[14px] font-medium text-muted-foreground transition-colors hover:text-primary py-1"
                activeProps={{ className: "text-primary font-semibold" }}
              >
                Verification
              </Link>
              <Link
                to="/about"
                className="nav-link-underline text-[14px] font-medium text-muted-foreground transition-colors hover:text-primary py-1"
                activeProps={{ className: "text-primary font-semibold" }}
              >
                About
              </Link>
              <Link
                to="/telegram"
                className="nav-link-underline text-[14px] font-medium text-muted-foreground transition-colors hover:text-primary py-1"
                activeProps={{ className: "text-primary font-semibold" }}
              >
                Telegram Alerts
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
            <ThemeToggle />
            {authed ? (
              <>
                <Link
                  to="/dashboard"
                  className="relative inline-flex items-center justify-center size-9 rounded-full bg-muted/60 text-muted-foreground hover:text-primary hover:bg-muted transition-colors cursor-pointer"
                  title="In-Dashboard Notifications"
                >
                  <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex size-4 items-center justify-center rounded-full bg-[#0a5c38] dark:bg-[#3fb68e] text-[9px] font-bold text-white dark:text-[#0c1015]">
                      {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                  )}
                </Link>
                <Link
                  to="/dashboard"
                  className="hidden text-[14px] font-medium text-muted-foreground hover:text-primary md:inline-flex cursor-pointer transition-colors"
                  activeProps={{ className: "text-primary font-semibold" }}
                >
                  Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="hidden text-[14px] font-medium text-muted-foreground hover:text-red-600 md:inline-flex cursor-pointer transition-colors"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/sign-in"
                  className="hidden text-[14px] font-medium text-muted-foreground hover:text-primary md:inline-flex cursor-pointer transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="hidden text-[14px] font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline md:inline-flex cursor-pointer transition-colors"
                >
                  Sign Up
                </Link>
              </>
            )}
            <a
              href="https://t.me/govalerts_bot?start=general"
              target="_blank"
              rel="noreferrer"
              onClick={() => requestAndSubscribeWebPush()}
              className="hidden xs:inline-flex items-center gap-1.5 sm:gap-2 rounded-[8px] bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] px-2.5 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-[14px] font-semibold transition-transform active:scale-[0.98] cursor-pointer shrink-0"
            >
              <svg className="size-[12px] sm:size-[14px] fill-current" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.02-1.93 1.23-5.46 3.62-.51.35-.98.53-1.39.51-.46-.01-1.33-.26-1.99-.47-.8-.27-1.44-.41-1.39-.87.03-.24.35-.49.97-.75 3.79-1.65 6.32-2.73 7.57-3.26 3.61-1.53 4.36-1.8 4.85-1.8.11 0 .35.03.5.15.13.12.17.27.18.39-.01.08-.01.18-.02.26z" />
              </svg>
              <span>Get Alerts</span>
            </a>

            {/* Mobile Hamburger Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex size-[36px] sm:size-[40px] items-center justify-center rounded-[8px] border border-border md:hidden cursor-pointer shrink-0 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0a5c38] dark:focus-visible:ring-[#3fb68e]"
              aria-label="Toggle mobile navigation menu"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-nav-drawer"
            >
              {mobileMenuOpen ? (
                <svg className="size-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="size-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div
            id="mobile-nav-drawer"
            aria-label="Mobile Navigation Menu"
            className="absolute top-[60px] left-0 w-full bg-background border-b border-border z-40 flex flex-col p-6 md:hidden shadow-lg animate-in slide-in-from-top-4 duration-200"
          >
            {/* Section 1: Navigation */}
            <div className="flex flex-col space-y-1">
              <Link
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60 transition-colors"
                activeProps={{ className: "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] font-semibold" }}
              >
                Home
              </Link>
              <Link
                to="/jobs"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60 transition-colors"
                activeProps={{ className: "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] font-semibold" }}
              >
                Jobs
              </Link>
              <Link
                to="/agencies"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60 transition-colors"
                activeProps={{ className: "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] font-semibold" }}
              >
                Agencies
              </Link>
              <Link
                to="/verification"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60 transition-colors"
                activeProps={{ className: "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] font-semibold" }}
              >
                Verification
              </Link>
              <Link
                to="/about"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60 transition-colors"
                activeProps={{ className: "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] font-semibold" }}
              >
                About
              </Link>
              <Link
                to="/telegram"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60 transition-colors"
                activeProps={{ className: "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] font-semibold" }}
              >
                Telegram Alerts
              </Link>
            </div>

            <hr className="my-3 border-border/60" />

            {/* Section 2: Account */}
            <div className="flex flex-col space-y-1">
              {authed ? (
                <>
                  <Link
                    to="/dashboard"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60"
                    activeProps={{ className: "bg-[#0a5c38]/10 text-[#0a5c38] dark:bg-[#3fb68e]/15 dark:text-[#3fb68e] font-semibold" }}
                  >
                    Dashboard
                  </Link>
                  <button
                    onClick={() => { setMobileMenuOpen(false); handleLogout(); }}
                    className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-muted-foreground hover:text-red-600 w-full text-left"
                  >
                    Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/sign-in"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-medium text-foreground hover:bg-muted/60"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center h-[44px] px-3 rounded-[6px] text-[15px] font-semibold text-[#0a5c38] dark:text-[#3fb68e]"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>

            <hr className="my-3 border-border/60" />

            {/* Section 3: Get Alerts CTA */}
            <a
              href="https://t.me/govalerts_bot?start=general"
              target="_blank"
              rel="noreferrer"
              className="flex h-[44px] w-full items-center justify-center gap-2 rounded-[8px] bg-[#0a5c38] text-white dark:bg-[#3fb68e] dark:text-[#0c1015] text-[14px] font-semibold"
            >
              <svg className="size-[14px] fill-current" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.02-1.93 1.23-5.46 3.62-.51.35-.98.53-1.39.51-.46-.01-1.33-.26-1.99-.47-.8-.27-1.44-.41-1.39-.87.03-.24.35-.49.97-.75 3.79-1.65 6.32-2.73 7.57-3.26 3.61-1.53 4.36-1.8 4.85-1.8.11 0 .35.03.5.15.13.12.17.27.18.39-.01.08-.01.18-.02.26z" />
              </svg>
              Get Alerts
            </a>

            <hr className="my-3 border-border/60" />

            {/* Section 4: Legal & Verification Links */}
            <div>
              <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Legal & Governance
              </p>
              <div className="flex flex-col space-y-1">
                <Link to="/verification" onClick={() => setMobileMenuOpen(false)} className="flex items-center h-[36px] text-[13px] text-muted-foreground hover:text-primary">Verification FAQ</Link>
                <Link to="/privacy" onClick={() => setMobileMenuOpen(false)} className="flex items-center h-[36px] text-[13px] text-muted-foreground hover:text-primary">Privacy Policy</Link>
                <Link to="/terms" onClick={() => setMobileMenuOpen(false)} className="flex items-center h-[36px] text-[13px] text-muted-foreground hover:text-primary">Terms of Service</Link>
              </div>
            </div>
          </div>
        )}
      </nav>
    </>
  );
}

export function Footer() {
  const cols = [
    {
      heading: "Directory & Audit",
      links: [
        { label: "Monitored Portals (42)", to: "/portals" },
        { label: "Public Audit Log", to: "/audit-log" },
        { label: "Monitored Agencies", to: "/agencies" },
        { label: "System Status", to: "/status" },
      ],
    },
    {
      heading: "Guides & Safety",
      links: [
        { label: "Scam Prevention Blog", to: "/blog" },
        { label: "Telegram Verification", to: "/telegram" },
        { label: "Verification FAQs", to: "/verification" },
        { label: "Contact Developer", to: "/contact" },
      ],
    },
    {
      heading: "Platform & Legal",
      links: [
        { label: "About RecruitmentAlert", to: "/about" },
        { label: "Built by Shamsuddeen Yusuf", to: "/shamsuddeen" },
        { label: "Privacy Policy", to: "/privacy" },
        { label: "Terms of Service", to: "/terms" },
      ],
    },
  ];

  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 bg-[#F9FAFB] dark:bg-[#0F172A] text-foreground py-10 sm:py-16 font-sans">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8 pb-8 sm:pb-12">
          {/* Brand Logo Column (Span 2) */}
          <div className="md:col-span-2 space-y-3 sm:space-y-4">
            <Logo />
            <p className="text-[13px] sm:text-[14px] text-muted-foreground max-w-sm leading-relaxed font-sans">
              Independent recruitment verification for Nigerian job seekers. We monitor official federal government portals so you can tell real listings from fake ones.
            </p>
          </div>

          {/* Navigation Columns (1 column each for Directory, Guides, Platform) */}
          {cols.map((c) => (
            <div key={c.heading} className="md:col-span-1">
              <h3 className="font-mono text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                {c.heading}
              </h3>
              <ul className="mt-3 space-y-2 text-[13px] sm:text-[14px] text-foreground font-sans">
                {c.links.map((l) => (
                  <li key={l.label}>
                    {l.external ? (
                      <a
                        href={l.to}
                        target="_blank"
                        rel="noreferrer"
                        className="transition-colors hover:text-primary inline-flex items-center gap-1 py-1"
                      >
                        {l.label}
                        <svg className="size-3 text-muted-foreground shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    ) : (
                      <Link to={l.to} className="transition-colors hover:text-primary inline-block py-1">
                        {l.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="flex flex-col md:flex-row justify-between items-center mt-12 pt-6 border-t border-gray-200 dark:border-gray-800 gap-4 font-sans">
          <p className="font-sans text-[11px] text-muted-foreground max-w-xl leading-relaxed">
            &copy; {new Date().getFullYear()} RecruitmentAlert. Independent monitoring, not affiliated with the Federal Government of Nigeria.
          </p>
          <div className="flex items-center shrink-0">
            <span className="relative flex h-2 w-2 mr-[6px]">
              <span className="pulsing-dot absolute inline-flex h-full w-full rounded-full bg-[#22C55E] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#22C55E]"></span>
            </span>
            <span className="font-mono text-[12px] font-semibold uppercase tracking-wider text-[#166534] dark:text-[#3fb68e]">
              SYSTEMS OPERATIONAL
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export function Divider({ className = "" }: { className?: string }) {
  return <hr className={`my-8 border-border ${className}`} />;
}
