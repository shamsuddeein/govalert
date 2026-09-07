import { createClient } from "@libsql/client";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const targetUrl = process.env.TARGET_TURSO_URL || process.env.TURSO_DATABASE_URL;
  const targetToken = process.env.TARGET_TURSO_AUTH_TOKEN || process.env.TURSO_AUTH_TOKEN;

  if (!targetUrl || targetUrl.startsWith("file:")) {
    console.log("ℹ️  No remote TURSO_DATABASE_URL provided.");
    console.log("    To push to Turso cloud, run:");
    console.log("    $env:TURSO_DATABASE_URL=\"libsql://your-db-name.turso.io\"");
    console.log("    $env:TURSO_AUTH_TOKEN=\"your-turso-auth-token\"");
    console.log("    npm run db:migrate\n");
    console.log("✅ Local SQLite database (users.db) is already fully populated and working with Drizzle ORM!");
    return;
  }

  console.log(`🚀 Connecting to source local DB and target Turso DB (${targetUrl})...`);

  const sourceClient = createClient({ url: "file:./users.db" });
  const targetClient = createClient({ url: targetUrl, authToken: targetToken });

  console.log("📦 Creating schema on target Turso database...");

  // Create tables on target
  await targetClient.execute(`
    CREATE TABLE IF NOT EXISTS agencies (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      acronym TEXT NOT NULL,
      official_domains TEXT,
      logo_url TEXT,
      category TEXT NOT NULL DEFAULT 'OTHER',
      is_active INTEGER NOT NULL DEFAULT 1,
      description TEXT,
      subscriber_count INTEGER NOT NULL DEFAULT 0,
      total_alerts_sent INTEGER NOT NULL DEFAULT 0,
      created_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      updated_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      slug TEXT NOT NULL UNIQUE,
      avg_confidence_score INTEGER NOT NULL DEFAULT 90,
      false_positives INTEGER NOT NULL DEFAULT 0,
      scam_domains_blocked INTEGER NOT NULL DEFAULT 0,
      vetted_score INTEGER NOT NULL DEFAULT 100
    );
  `);

  await targetClient.execute(`
    CREATE TABLE IF NOT EXISTS portals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      url TEXT NOT NULL,
      scrape_method TEXT NOT NULL DEFAULT 'REQUESTS',
      check_interval_minutes INTEGER NOT NULL DEFAULT 30,
      is_active INTEGER NOT NULL DEFAULT 1,
      status TEXT NOT NULL DEFAULT 'online',
      last_checked_at TEXT,
      last_successful_check_at TEXT,
      last_change_detected_at TEXT,
      consecutive_failures INTEGER NOT NULL DEFAULT 0,
      uptime_percentage REAL NOT NULL DEFAULT 100.0,
      notes TEXT,
      created_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      updated_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      agency_id INTEGER REFERENCES agencies(id) ON DELETE CASCADE,
      confidence INTEGER,
      country TEXT DEFAULT 'NG',
      health_status TEXT DEFAULT 'ONLINE',
      poll_interval INTEGER,
      priority TEXT NOT NULL DEFAULT 'MEDIUM',
      response_time_ms INTEGER NOT NULL DEFAULT 0,
      tags TEXT,
      location_state TEXT DEFAULT 'Federal'
    );
  `);

  await targetClient.execute(`
    CREATE TABLE IF NOT EXISTS alerts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT NOT NULL DEFAULT 'RECRUITMENT_OPEN',
      title TEXT NOT NULL,
      positions TEXT,
      deadline TEXT,
      requirements TEXT,
      source_url TEXT NOT NULL,
      content_excerpt TEXT,
      trust_score INTEGER NOT NULL DEFAULT 50,
      ai_classification TEXT NOT NULL DEFAULT 'UNCERTAIN',
      ai_confidence REAL NOT NULL DEFAULT 0.0,
      ai_red_flags TEXT,
      status TEXT NOT NULL DEFAULT 'APPROVED',
      is_verified INTEGER NOT NULL DEFAULT 1,
      verified_at TEXT,
      admin_notes TEXT,
      recipients_count INTEGER NOT NULL DEFAULT 0,
      sent_at TEXT,
      report_count INTEGER NOT NULL DEFAULT 0,
      created_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      updated_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      agency_id INTEGER REFERENCES agencies(id) ON DELETE CASCADE,
      portal_id INTEGER REFERENCES portals(id) ON DELETE SET NULL,
      verified_by_id INTEGER,
      recruitment_event_id INTEGER,
      trust_score_overridden_at TEXT,
      trust_score_overridden_by_id INTEGER,
      decision_source TEXT DEFAULT 'AI_ASSISTED',
      trust_category TEXT
    );
  `);

  await targetClient.execute(`
    CREATE TABLE IF NOT EXISTS blog_posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      slug TEXT NOT NULL UNIQUE,
      excerpt TEXT,
      category TEXT DEFAULT 'Verification Guide',
      author TEXT DEFAULT 'GovAlert Verification Team',
      read_time TEXT DEFAULT '4 min read',
      is_published INTEGER NOT NULL DEFAULT 1,
      created_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      updated_at TEXT DEFAULT (CURRENT_TIMESTAMP),
      body TEXT,
      meta_description TEXT,
      published_date TEXT,
      reading_time INTEGER DEFAULT 4,
      content TEXT
    );
  `);

  console.log("🔄 Migrating Agencies...");
  const agenciesRes = await sourceClient.execute("SELECT * FROM agencies");
  for (const row of agenciesRes.rows) {
    await targetClient.execute({
      sql: `INSERT OR REPLACE INTO agencies (
        id, name, acronym, official_domains, logo_url, category, is_active,
        description, subscriber_count, total_alerts_sent, created_at, updated_at,
        slug, avg_confidence_score, false_positives, scam_domains_blocked, vetted_score
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      args: [
        row.id, row.name, row.acronym, row.official_domains, row.logo_url, row.category, row.is_active,
        row.description, row.subscriber_count, row.total_alerts_sent, row.created_at, row.updated_at,
        row.slug, row.avg_confidence_score, row.false_positives, row.scam_domains_blocked, row.vetted_score
      ]
    });
  }
  console.log(`✅ Migrated ${agenciesRes.rows.length} agencies to Turso.`);

  console.log("🔄 Migrating Portals...");
  const portalsRes = await sourceClient.execute("SELECT * FROM portals");
  for (const row of portalsRes.rows) {
    await targetClient.execute({
      sql: `INSERT OR REPLACE INTO portals (
        id, name, url, scrape_method, check_interval_minutes, is_active, status,
        last_checked_at, last_successful_check_at, last_change_detected_at,
        consecutive_failures, uptime_percentage, notes, created_at, updated_at,
        agency_id, confidence, country, health_status, poll_interval, priority,
        response_time_ms, tags, location_state
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      args: [
        row.id, row.name, row.url, row.scrape_method, row.check_interval_minutes, row.is_active, row.status,
        row.last_checked_at, row.last_successful_check_at, row.last_change_detected_at,
        row.consecutive_failures, row.uptime_percentage, row.notes, row.created_at, row.updated_at,
        row.agency_id, row.confidence, row.country, row.health_status, row.poll_interval, row.priority,
        row.response_time_ms, row.tags, row.location_state
      ]
    });
  }
  console.log(`✅ Migrated ${portalsRes.rows.length} portals to Turso.`);

  console.log("🔄 Migrating Alerts...");
  const alertsRes = await sourceClient.execute("SELECT * FROM alerts");
  for (const row of alertsRes.rows) {
    await targetClient.execute({
      sql: `INSERT OR REPLACE INTO alerts (
        id, event_type, title, positions, deadline, requirements, source_url,
        content_excerpt, trust_score, ai_classification, ai_confidence, ai_red_flags,
        status, is_verified, verified_at, admin_notes, recipients_count, sent_at,
        report_count, created_at, updated_at, agency_id, portal_id, verified_by_id,
        recruitment_event_id, trust_score_overridden_at, trust_score_overridden_by_id,
        decision_source, trust_category
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      args: [
        row.id, row.event_type, row.title, row.positions, row.deadline, row.requirements, row.source_url,
        row.content_excerpt, row.trust_score, row.ai_classification, row.ai_confidence, row.ai_red_flags,
        row.status, row.is_verified, row.verified_at, row.admin_notes, row.recipients_count, row.sent_at,
        row.report_count, row.created_at, row.updated_at, row.agency_id, row.portal_id, row.verified_by_id,
        row.recruitment_event_id, row.trust_score_overridden_at, row.trust_score_overridden_by_id,
        row.decision_source, row.trust_category
      ]
    });
  }
  console.log(`✅ Migrated ${alertsRes.rows.length} alerts to Turso.`);

  console.log("🔄 Migrating Blog Posts...");
  const blogRes = await sourceClient.execute("SELECT * FROM blog_posts");
  for (const row of blogRes.rows) {
    await targetClient.execute({
      sql: `INSERT OR REPLACE INTO blog_posts (
        id, title, slug, excerpt, category, author, read_time, is_published,
        created_at, updated_at, body, meta_description, published_date,
        reading_time, content
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      args: [
        row.id, row.title, row.slug, row.excerpt, row.category, row.author, row.read_time, row.is_published,
        row.created_at, row.updated_at, row.body, row.meta_description, row.published_date,
        row.reading_time, row.content
      ]
    });
  }
  console.log(`✅ Migrated ${blogRes.rows.length} blog posts to Turso.`);

  console.log("\n🎉 Migration to Turso completed successfully!");
}

main().catch(console.error);
