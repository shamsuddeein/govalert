/**
 * RecruitmentAlert Admin API Client Module
 * Communicates with /api/v1/admin/* endpoints.
 * 
 * Tradeoff Note: Storing JWT tokens in localStorage is used here as a client-side fallback
 * for cross-origin SPA requests. For higher security in production environments, httpOnly
 * cookies set by backend API responses are recommended.
 */

const DEFAULT_BACKEND_URL = "";
const BASE_HOST = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) || DEFAULT_BACKEND_URL;
const ADMIN_API_BASE = `${BASE_HOST ? BASE_HOST.replace(/\/$/, "") : ""}/api/v1/admin`;

// ─── Interfaces ────────────────────────────────────────────────────────────────

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_staff?: boolean;
  is_superuser: boolean;
}

export interface AdminUserRecord {
  id: string;
  raw_id: number;
  user_type: "WEB" | "TELEGRAM" | "KEYWORD_SUBSCRIBER";
  auth_provider?: string;
  platform?: string;
  email: string | null;
  display_name: string;
  username?: string;
  telegram_id?: number | null;
  query_text?: string;
  is_active: boolean;
  state?: string;
  email_alerts_enabled?: boolean;
  date_joined: string | null;
  last_login: string | null;
}

export interface AdminBlogPostRecord {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  category: string;
  author: string;
  read_time: string;
  is_published: boolean;
  created_at: string;
  updated_at?: string;
}

export interface VisitorStats {
  active_online_visitors: number;
  visitors_today: number;
  page_views_today: number;
  all_time_visitors: number;
  bot_hits_today?: number;
  human_hits_today?: number;
  has_data?: boolean;
  is_demo_mode?: boolean;
}

export interface AdminUserStats {
  total_web_users: number;
  active_web_users: number;
  new_web_users_today: number;
  total_telegram_subscribers: number;
  active_telegram_subscribers: number;
  total_keyword_subscribers: number;
  active_keyword_subscriptions: number;
  visitor_stats?: VisitorStats;
}

export interface AdminAlert {
  id: number;
  title: string;
  agency: { name: string; acronym: string } | null;
  portal: { name: string; url: string } | null;
  agency_name: string;
  agency_acronym: string;
  portal_name: string;
  portal_url: string;
  deadline: string;
  positions: string;
  requirements: string;
  source_url: string;
  content_excerpt: string;
  trust_score: number;
  trust_score_overridden_by: string | null;
  trust_score_overridden_at: string | null;
  ai_classification: "REAL" | "FAKE" | "UNCERTAIN";
  ai_confidence: number;
  ai_red_flags: string[];
  status: "PENDING" | "APPROVED" | "REJECTED" | "HELD" | "SUPERSEDED";

  is_verified: boolean;
  verified_by: string | null;
  verified_at: string | null;
  admin_notes: string;
  report_count: number;
  created_at: string;
  recruitment_event: {
    event_id: string;
    fingerprint: string;
    event_type: string;
  } | null;
}

export interface AdminAlertStats {
  pending_count: number;
  approved_today: number;
  rejected_today: number;
  avg_review_time_minutes: number;
  oldest_pending_age_hours: number;
}

export interface AdminAgency {
  id: number;
  name: string;
  acronym: string;
  slug: string;
  official_domains: string[];
  logo_url: string;
  category: string;
  is_active: boolean;
  description: string;
  vetted_score: number;
  avg_confidence_score: number;
  false_positives: number;
  scam_domains_blocked: number;
  subscriber_count: number;
  total_alerts_sent: number;
  portal_count: number;
  alert_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminSnapshot {
  id: number;
  portal: number;
  content_hash: string;
  status_code: number | null;
  response_time_ms: number | null;
  scrape_method_used: string;
  has_change: boolean;
  triggered_alert: boolean;
  created_at: string;
  timestamp: string;
}

export interface AdminPortal {
  id: number;
  agency: number;
  agency_name: string;
  agency_acronym: string;
  name: string;
  url: string;
  scrape_method: string;
  check_interval_minutes: number;
  poll_interval: number;
  priority: string;
  is_active: boolean;
  health_status: string;
  status: string;
  location_state: string;
  last_checked_at: string | null;
  last_successful_check_at: string | null;
  last_change_detected_at: string | null;
  consecutive_failures: number;
  uptime_percentage: string;
  confidence: number;
  response_time_ms: number | null;
  tags: string[];
  country: string;
  notes: string;
  created_at: string;
  updated_at: string;
  recent_snapshots?: AdminSnapshot[];
}

export interface AdminSystemHealth {
  system_status: {
    agencies_online: number;
    agencies_offline: number;
    agencies_maintenance: number;
    total_agencies: number;
    total_checks_today: number;
    successful_checks_today: number;
    failed_checks_today: number;
    success_rate_today: number;
    changes_detected_today: number;
    system_operational: boolean;
    visitor_stats?: VisitorStats;
  };
  portals_breakdown: Array<{
    id: number;
    name: string;
    agency_acronym: string;
    url: string;
    consecutive_failures: number;
    last_checked_at: string | null;
    last_successful_check_at: string | null;
    health_status: string;
    status: string;
    needs_attention: boolean;
    down_duration_seconds?: number;
    failing_over_24h?: boolean;
  }>;
  recent_failed_snapshots: Array<{
    id: number;
    portal_id: number | null;
    portal_name: string;
    agency_acronym: string;
    status_code: number | null;
    response_time_ms: number | null;
    error_detail: string;
    timestamp: string;
  }>;
  daily_trend_7_days: Array<{
    date: string;
    total_checks: number;
    successful_checks: number;
    failed_checks: number;
    success_rate: number;
  }>;
}

// ─── Token Management Helpers ──────────────────────────────────────────────────

export const getAdminAccessToken = (): string | null =>
  typeof window !== "undefined"
    ? localStorage.getItem("recruitmentalert_admin_access_token") || localStorage.getItem("govalert_admin_access_token")
    : null;

export const getAdminRefreshToken = (): string | null =>
  typeof window !== "undefined"
    ? localStorage.getItem("recruitmentalert_admin_refresh_token") || localStorage.getItem("govalert_admin_refresh_token")
    : null;

export const setAdminTokens = (access: string, refresh: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("recruitmentalert_admin_access_token", access);
    localStorage.setItem("recruitmentalert_admin_refresh_token", refresh);
  }
};

export const setAdminUser = (user: AdminUser) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("recruitmentalert_admin_user", JSON.stringify(user));
  }
};

export const getAdminUser = (): AdminUser | null => {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("recruitmentalert_admin_user") || localStorage.getItem("govalert_admin_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const clearAdminTokens = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("recruitmentalert_admin_access_token");
    localStorage.removeItem("recruitmentalert_admin_refresh_token");
    localStorage.removeItem("recruitmentalert_admin_user");
  }
};

export const isAdminAuthenticated = (): boolean => Boolean(getAdminAccessToken());

// Flag to prevent infinite retry loops during silent refresh
let isRefreshingAdminToken = false;

// ─── HTTP Request Helper ───────────────────────────────────────────────────────

async function adminRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T | null> {
  const token = getAdminAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const url = `${ADMIN_API_BASE}${endpoint}`;
    const res = await fetch(url, {
      ...options,
      headers,
    });

    // 401 Unauthorized handling : attempt silent refresh once
    if (res.status === 401 && !isRetry && !endpoint.includes("/auth/login/")) {
      if (!isRefreshingAdminToken) {
        isRefreshingAdminToken = true;
        const newAccess = await adminApi.refreshToken();
        isRefreshingAdminToken = false;
        if (newAccess) {
          return adminRequest<T>(endpoint, options, true);
        } else {
          clearAdminTokens();
          if (typeof window !== "undefined" && !window.location.pathname.includes("/admin/login")) {
            window.location.href = "/admin/login";
          }
          return null;
        }
      }
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      const message = errData?.detail || `API Request Failed: ${res.status} ${res.statusText}`;
      console.warn(`Admin API Error (${endpoint}):`, message);
      return Promise.reject({ status: res.status, message, data: errData });
    }

    return await res.json();
  } catch (err: any) {
    if (err?.status) throw err;
    console.warn(`Network error calling Admin API endpoint ${endpoint}:`, err);
    throw { status: 0, message: err?.message || "Network error. Server may be down." };
  }
}

// ─── Admin API Object Methods ──────────────────────────────────────────────────

export const adminApi = {
  // Auth
  login: async (username: string, password: string): Promise<{ access: string; refresh: string; user: AdminUser }> => {
    const res = await fetch(`${ADMIN_API_BASE}/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json().catch(() => null);
    if (!res.ok) {
      if (res.status === 429) {
        throw new Error("Too many login attempts. Please wait a minute before trying again.");
      }
      let errDetail = data?.detail || "Invalid credentials or non-staff user.";
      if (typeof errDetail === "string" && errDetail.toLowerCase().includes("throttled")) {
        errDetail = "Too many login attempts. Please wait a minute before trying again.";
      }
      throw new Error(errDetail);
    }

    setAdminTokens(data.access, data.refresh);
    setAdminUser(data.user);
    return data;
  },

  refreshToken: async (): Promise<string | null> => {
    const refresh = getAdminRefreshToken();
    if (!refresh) return null;

    try {
      const res = await fetch(`${ADMIN_API_BASE}/auth/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });

      if (!res.ok) return null;
      const data = await res.json();
      if (data?.access) {
        localStorage.setItem("recruitmentalert_admin_access_token", data.access);
        return data.access;
      }
      return null;
    } catch {
      return null;
    }
  },

  getMe: async (): Promise<AdminUser | null> => {
    return adminRequest<AdminUser>("/auth/me/");
  },

  logout: () => {
    clearAdminTokens();
    if (typeof window !== "undefined") {
      window.location.href = "/admin/login";
    }
  },

  // Alert Queue
  getAlerts: async (params?: {
    status?: string;
    agency?: string;
    ai_classification?: string;
    ordering?: string;
    page?: number;
  }): Promise<{ results: AdminAlert[]; count: number }> => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.agency) q.set("agency", params.agency);
    if (params?.ai_classification) q.set("ai_classification", params.ai_classification);
    if (params?.ordering) q.set("ordering", params.ordering);
    if (params?.page) q.set("page", String(params.page));

    const res = await adminRequest<{ results: AdminAlert[]; count: number }>(`/alerts/?${q.toString()}`);
    return res || { results: [], count: 0 };
  },

  getAlertStats: async (): Promise<AdminAlertStats> => {
    const res = await adminRequest<AdminAlertStats>("/alerts/stats/");
    return res || {
      pending_count: 0,
      approved_today: 0,
      rejected_today: 0,
      avg_review_time_minutes: 0,
      oldest_pending_age_hours: 0,
    };
  },

  approveAlert: async (id: number, admin_notes?: string): Promise<{ detail: string; alert: AdminAlert }> => {
    return adminRequest<{ detail: string; alert: AdminAlert }>(`/alerts/${id}/approve/`, {
      method: "POST",
      body: JSON.stringify({ admin_notes: admin_notes || "" }),
    }) as Promise<{ detail: string; alert: AdminAlert }>;
  },

  rejectAlert: async (id: number, admin_notes: string): Promise<{ detail: string; alert: AdminAlert }> => {
    return adminRequest<{ detail: string; alert: AdminAlert }>(`/alerts/${id}/reject/`, {
      method: "POST",
      body: JSON.stringify({ admin_notes }),
    }) as Promise<{ detail: string; alert: AdminAlert }>;
  },

  holdAlert: async (id: number, admin_notes?: string): Promise<{ detail: string; alert: AdminAlert }> => {
    return adminRequest<{ detail: string; alert: AdminAlert }>(`/alerts/${id}/hold/`, {
      method: "POST",
      body: JSON.stringify({ admin_notes: admin_notes || "" }),
    }) as Promise<{ detail: string; alert: AdminAlert }>;
  },

  getSingleAlert: async (id: number): Promise<AdminAlert> => {
    return adminRequest<AdminAlert>(`/alerts/${id}/`) as Promise<AdminAlert>;
  },

  updateAlert: async (
    id: number,
    data: {
      title?: string;
      positions?: string;
      deadline?: string;
      requirements?: string;
      source_url?: string;
      status?: string;
      trust_score?: number;
      admin_notes?: string;
    }
  ): Promise<AdminAlert> => {
    return adminRequest<AdminAlert>(`/alerts/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<AdminAlert>;
  },

  deleteAlert: async (id: number): Promise<{ detail: string; id: number }> => {
    return adminRequest<{ detail: string; id: number }>(`/alerts/${id}/`, {
      method: "DELETE",
    }) as Promise<{ detail: string; id: number }>;
  },

  createAlert: async (data: {
    agency_id: number;
    portal_id?: number | null;
    title: string;
    event_type: string;
    positions?: string;
    deadline?: string;
    requirements?: string;
    source_url?: string;
    content_excerpt?: string;
    trust_score?: number;
    status?: "APPROVED" | "PENDING" | "HELD";
    notify_subscribers?: boolean;
  }): Promise<{ detail: string; alert: AdminAlert }> => {
    return adminRequest<{ detail: string; alert: AdminAlert }>("/alerts/", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<{ detail: string; alert: AdminAlert }>;
  },

  sendBroadcast: async (
    text: string,
    subject?: string
  ): Promise<{ status: string; telegram_recipients_count: number; email_recipients_count: number; total_delivered: number }> => {
    return adminRequest<{
      status: string;
      telegram_recipients_count: number;
      email_recipients_count: number;
      total_delivered: number;
    }>("/broadcast/", {
      method: "POST",
      body: JSON.stringify({ text, subject }),
    });
  },



  // Agencies
  getAgencies: async (params?: { category?: string; search?: string }): Promise<AdminAgency[]> => {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.search) q.set("search", params.search);
    const res = await adminRequest<AdminAgency[]>(`/agencies/?${q.toString()}`);
    return res || [];
  },

  getAgency: async (id: number): Promise<AdminAgency> => {
    return adminRequest<AdminAgency>(`/agencies/${id}/`) as Promise<AdminAgency>;
  },

  createAgency: async (data: Partial<AdminAgency>): Promise<AdminAgency> => {
    return adminRequest<AdminAgency>("/agencies/", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<AdminAgency>;
  },

  updateAgency: async (id: number, data: Partial<AdminAgency>): Promise<AdminAgency> => {
    return adminRequest<AdminAgency>(`/agencies/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<AdminAgency>;
  },

  deleteAgency: async (id: number): Promise<{ detail: string; is_active: boolean }> => {
    return adminRequest<{ detail: string; is_active: boolean }>(`/agencies/${id}/`, {
      method: "DELETE",
    }) as Promise<{ detail: string; is_active: boolean }>;
  },

  // Portals
  getPortals: async (params?: { agency?: string; health_status?: string }): Promise<AdminPortal[]> => {
    const q = new URLSearchParams();
    if (params?.agency) q.set("agency", params.agency);
    if (params?.health_status) q.set("health_status", params.health_status);
    const res = await adminRequest<AdminPortal[]>(`/portals/?${q.toString()}`);
    return res || [];
  },

  getPortal: async (id: number): Promise<AdminPortal> => {
    return adminRequest<AdminPortal>(`/portals/${id}/`) as Promise<AdminPortal>;
  },

  createPortal: async (data: Partial<AdminPortal>): Promise<AdminPortal> => {
    return adminRequest<AdminPortal>("/portals/", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<AdminPortal>;
  },

  updatePortal: async (id: number, data: Partial<AdminPortal>): Promise<AdminPortal> => {
    return adminRequest<AdminPortal>(`/portals/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<AdminPortal>;
  },

  deletePortal: async (id: number): Promise<{ detail: string; is_active: boolean }> => {
    return adminRequest<{ detail: string; is_active: boolean }>(`/portals/${id}/`, {
      method: "DELETE",
    }) as Promise<{ detail: string; is_active: boolean }>;
  },

  triggerPortalCheck: async (id: number): Promise<{ detail: string; has_change: boolean; snapshot: AdminSnapshot | null }> => {
    return adminRequest<{ detail: string; has_change: boolean; snapshot: AdminSnapshot | null }>(
      `/portals/${id}/trigger-check/`,
      { method: "POST" }
    ) as Promise<{ detail: string; has_change: boolean; snapshot: AdminSnapshot | null }>;
  },

  getPortalHistory: async (id: number): Promise<AdminSnapshot[]> => {
    const res = await adminRequest<AdminSnapshot[]>(`/portals/${id}/history/`);
    return res || [];
  },

  triggerCheckAllPortals: async (): Promise<{ detail: string; total_active_portals: number; triggered_count: number }> => {
    return adminRequest<{ detail: string; total_active_portals: number; triggered_count: number }>(
      "/portals/trigger-check-all/",
      { method: "POST" }
    ) as Promise<{ detail: string; total_active_portals: number; triggered_count: number }>;
  },

  triggerAllPortalChecks: async (): Promise<{ detail: string; total_active_portals: number; triggered_count: number }> => {
    return adminRequest<{ detail: string; total_active_portals: number; triggered_count: number }>(
      "/portals/trigger-check-all/",
      { method: "POST" }
    ) as Promise<{ detail: string; total_active_portals: number; triggered_count: number }>;
  },

  // User Management
  getUsers: async (params?: {
    search?: string;
    user_type?: string;
    status?: string;
    page?: number;
  }): Promise<{ results: AdminUserRecord[]; count: number }> => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.user_type) q.set("user_type", params.user_type);
    if (params?.status) q.set("status", params.status);
    if (params?.page) q.set("page", String(params.page));
    const res = await adminRequest<{ results: AdminUserRecord[]; count: number }>(`/users/?${q.toString()}`);
    return res || { results: [], count: 0 };
  },

  getUserStats: async (): Promise<AdminUserStats> => {
    const res = await adminRequest<AdminUserStats>("/users/stats/");
    return res || {
      total_web_users: 0,
      active_web_users: 0,
      new_web_users_today: 0,
      total_telegram_subscribers: 0,
      active_telegram_subscribers: 0,
      total_keyword_subscribers: 0,
      active_keyword_subscriptions: 0,
    };
  },

  toggleUserActive: async (user_type: string, id: number): Promise<{ status: string; is_active: boolean }> => {
    return adminRequest<{ status: string; is_active: boolean }>(
      `/users/${user_type.toLowerCase()}/${id}/toggle-active/`,
      { method: "PATCH" }
    ) as Promise<{ status: string; is_active: boolean }>;
  },

  // System Health
  getSystemHealth: async (): Promise<AdminSystemHealth> => {
    const res = await adminRequest<AdminSystemHealth>("/system-health/");
    return res || {
      system_status: {
        agencies_online: 0,
        agencies_offline: 0,
        agencies_maintenance: 0,
        total_agencies: 0,
        total_checks_today: 0,
        successful_checks_today: 0,
        failed_checks_today: 0,
        success_rate_today: 100,
        changes_detected_today: 0,
        system_operational: true,
      },
      portals_breakdown: [],
      recent_failed_snapshots: [],
      daily_trend_7_days: [],
    };
  },

  // Blog Post Management
  getBlogPosts: async (): Promise<{ results: AdminBlogPostRecord[]; count: number }> => {
    const res = await adminRequest<{ results: AdminBlogPostRecord[]; count: number }>("/blog/");
    return res || { results: [], count: 0 };
  },

  createBlogPost: async (data: {
    title: string;
    slug?: string;
    excerpt?: string;
    content: string;
    category?: string;
    author?: string;
    read_time?: string;
    is_published?: boolean;
  }): Promise<AdminBlogPostRecord> => {
    return adminRequest<AdminBlogPostRecord>("/blog/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateBlogPost: async (
    id: number,
    data: Partial<AdminBlogPostRecord>
  ): Promise<AdminBlogPostRecord> => {
    return adminRequest<AdminBlogPostRecord>(`/blog/${id}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  deleteBlogPost: async (id: number): Promise<void> => {
    await adminRequest(`/blog/${id}/`, { method: "DELETE" });
  },

  // Alert Creation
  createAlert: async (data: {
    agency_id?: number | null;
    portal_id?: number | null;
    event_type: string;
    title: string;
    positions?: string;
    deadline?: string;
    requirements?: string;
    source_url?: string;
    content_excerpt?: string;
    trust_score?: number;
    status?: "APPROVED" | "PENDING" | "HELD" | "REJECTED";
    notify_subscribers?: boolean;
    custom_agency_name?: string;
    custom_agency_acronym?: string;
    custom_category?: string;
  }): Promise<{ detail: string; alert: AdminAlertRecord }> => {
    return adminRequest<{ detail: string; alert: AdminAlertRecord }>("/alerts/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};
