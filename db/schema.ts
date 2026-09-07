import { sqliteTable, text, integer, real, index } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const agencies = sqliteTable(
  "agencies",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    name: text("name").notNull(),
    acronym: text("acronym").notNull(),
    officialDomains: text("official_domains"),
    logoUrl: text("logo_url"),
    category: text("category").notNull().default("OTHER"),
    isActive: integer("is_active", { mode: "boolean" }).notNull().default(true),
    description: text("description"),
    subscriberCount: integer("subscriber_count").notNull().default(0),
    totalAlertsSent: integer("total_alerts_sent").notNull().default(0),
    createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
    updatedAt: text("updated_at").default(sql`(CURRENT_TIMESTAMP)`),
    slug: text("slug").notNull().unique(),
    avgConfidenceScore: integer("avg_confidence_score").notNull().default(90),
    falsePositives: integer("false_positives").notNull().default(0),
    scamDomainsBlocked: integer("scam_domains_blocked").notNull().default(0),
    vettedScore: integer("vetted_score").notNull().default(100),
  },
  (table) => [
    index("idx_agencies_slug").on(table.slug),
    index("idx_agencies_category").on(table.category),
  ]
);

export const portals = sqliteTable(
  "portals",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    name: text("name").notNull(),
    url: text("url").notNull(),
    scrapeMethod: text("scrape_method").notNull().default("REQUESTS"),
    checkIntervalMinutes: integer("check_interval_minutes").notNull().default(30),
    isActive: integer("is_active", { mode: "boolean" }).notNull().default(true),
    status: text("status").notNull().default("online"), // online, offline, maintenance, unknown
    lastCheckedAt: text("last_checked_at"),
    lastSuccessfulCheckAt: text("last_successful_check_at"),
    lastChangeDetectedAt: text("last_change_detected_at"),
    consecutiveFailures: integer("consecutive_failures").notNull().default(0),
    uptimePercentage: real("uptime_percentage").notNull().default(100.0),
    notes: text("notes"),
    createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
    updatedAt: text("updated_at").default(sql`(CURRENT_TIMESTAMP)`),
    agencyId: integer("agency_id").references(() => agencies.id, { onDelete: "cascade" }),
    confidence: integer("confidence"),
    country: text("country").default("NG"),
    healthStatus: text("health_status").default("ONLINE"),
    pollInterval: integer("poll_interval"),
    priority: text("priority").notNull().default("MEDIUM"),
    responseTimeMs: integer("response_time_ms").notNull().default(0),
    tags: text("tags"),
    locationState: text("location_state").default("Federal"),
  },
  (table) => [
    index("idx_portals_agency").on(table.agencyId),
    index("idx_portals_status").on(table.status),
    index("idx_portals_last_checked").on(table.lastCheckedAt),
  ]
);

export const alerts = sqliteTable(
  "alerts",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    eventType: text("event_type").notNull().default("RECRUITMENT_OPEN"),
    title: text("title").notNull(),
    positions: text("positions"),
    deadline: text("deadline"),
    requirements: text("requirements"),
    sourceUrl: text("source_url").notNull(),
    contentExcerpt: text("content_excerpt"),
    trustScore: integer("trust_score").notNull().default(50),
    aiClassification: text("ai_classification").notNull().default("UNCERTAIN"),
    aiConfidence: real("ai_confidence").notNull().default(0.0),
    aiRedFlags: text("ai_red_flags"),
    status: text("status").notNull().default("APPROVED"), // APPROVED, PENDING, REJECTED, HELD
    isVerified: integer("is_verified", { mode: "boolean" }).notNull().default(true),
    verifiedAt: text("verified_at"),
    adminNotes: text("admin_notes"),
    recipientsCount: integer("recipients_count").notNull().default(0),
    sentAt: text("sent_at"),
    reportCount: integer("report_count").notNull().default(0),
    createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
    updatedAt: text("updated_at").default(sql`(CURRENT_TIMESTAMP)`),
    agencyId: integer("agency_id").references(() => agencies.id, { onDelete: "cascade" }),
    portalId: integer("portal_id").references(() => portals.id, { onDelete: "set null" }),
    verifiedById: integer("verified_by_id"),
    recruitmentEventId: integer("recruitment_event_id"),
    trustScoreOverriddenAt: text("trust_score_overridden_at"),
    trustScoreOverriddenById: integer("trust_score_overridden_by_id"),
    decisionSource: text("decision_source").default("AI_ASSISTED"),
    trustCategory: text("trust_category"),
  },
  (table) => [
    index("idx_alerts_agency").on(table.agencyId),
    index("idx_alerts_status").on(table.status),
    index("idx_alerts_created_at").on(table.createdAt),
  ]
);

export const recruitmentEvents = sqliteTable("recruitment_events", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  eventId: text("event_id").notNull().unique(),
  eventType: text("event_type").notNull().default("RECRUITMENT_OPEN"),
  contentHash: text("content_hash"),
  createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
  portalId: integer("portal_id").references(() => portals.id),
  status: text("status").notNull().default("NEW"),
  title: text("title"),
  deadline: text("deadline"),
  positions: text("positions"),
  fingerprint: text("fingerprint"),
  previousEventId: integer("previous_event_id"),
});

export const snapshots = sqliteTable("snapshots", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  contentHash: text("content_hash").notNull(),
  rawContent: text("raw_content"),
  statusCode: integer("status_code").notNull().default(200),
  responseTimeMs: integer("response_time_ms").notNull().default(0),
  scrapeMethodUsed: text("scrape_method_used").default("REQUESTS"),
  hasChange: integer("has_change", { mode: "boolean" }).notNull().default(false),
  triggeredAlert: integer("triggered_alert", { mode: "boolean" }).notNull().default(false),
  createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
  portalId: integer("portal_id").references(() => portals.id, { onDelete: "cascade" }),
});

export const blogPosts = sqliteTable("blog_posts", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  slug: text("slug").notNull().unique(),
  excerpt: text("excerpt"),
  category: text("category").default("Verification Guide"),
  author: text("author").default("GovAlert Verification Team"),
  readTime: text("read_time").default("4 min read"),
  isPublished: integer("is_published", { mode: "boolean" }).notNull().default(true),
  createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
  updatedAt: text("updated_at").default(sql`(CURRENT_TIMESTAMP)`),
  body: text("body"),
  metaDescription: text("meta_description"),
  publishedDate: text("published_date"),
  readingTime: integer("reading_time").default(4),
  content: text("content"),
});

export const keywordSubscriptions = sqliteTable("keyword_subscriptions", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  email: text("email").notNull(),
  queryText: text("query_text").notNull(),
  isActive: integer("is_active", { mode: "boolean" }).notNull().default(true),
  createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
  lastMatchedAt: text("last_matched_at"),
});

export const auditLogs = sqliteTable("audit_logs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  action: text("action").notNull(),
  details: text("details"),
  actor: text("actor").default("System"),
  ipAddress: text("ip_address"),
  createdAt: text("created_at").default(sql`(CURRENT_TIMESTAMP)`),
});
