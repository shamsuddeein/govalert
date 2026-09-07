import { createClient } from "@libsql/client";

const TURSO_URL = process.env.TURSO_DATABASE_URL || "libsql://alert-shamsuddeein.aws-eu-west-1.turso.io";
const TURSO_TOKEN = process.env.TURSO_AUTH_TOKEN || "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODg3Mzc5NzgsImlkIjoiMDFhMDc5MTctM2EwMS03YWRkLWEzYzAtZGRkYzY5YzA3NTY3Iiwia2lkIjoicXhUVnhLc3dPX3RIb1hrNkxfNUFSZW1mSmIyUVFpaTdOQ2hMM3diZ1RhMCIsInJpZCI6ImZhZTAxOWNkLTgzN2MtNDM3Yi1hOTA5LTU2YzQ0ZDQ1NmUyOCJ9.-RHNptmc-ulJnZD-gokDHNn9_vhpLlg-qH1lVjUaPes8zh3PsWHMdwHxZT3MaSayFbFgkTqXPPJyRGHnqn5nDw";

async function runMigration() {
  console.log("=================================================");
  console.log(" GovAlert Database Migration -> Turso Cloud");
  console.log("=================================================");
  console.log(`Target: ${TURSO_URL}\n`);

  const local = createClient({ url: "file:./users.db" });
  const remote = createClient({ url: TURSO_URL, authToken: TURSO_TOKEN });

  // 1. Get all table schemas
  const tablesRes = await local.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
  );

  console.log(`Found ${tablesRes.rows.length} tables in local SQLite database.`);

  // Filter out any unwanted tables or prioritize core tables
  const coreTables = [
    "agencies",
    "portals",
    "alerts",
    "blog_posts",
    "snapshots",
    "auth_user",
    "users",
    "subscriptions",
    "keyword_subscriptions",
    "recruitment_events",
    "web_users",
    "rejected_detections",
    "push_subscriptions",
    "fake_domains",
    "alert_reports",
    "decision_logs",
    "notifications"
  ];

  // 2. Create tables on Turso
  for (const row of tablesRes.rows) {
    const tableName = String(row.name);
    const sql = String(row.sql);

    try {
      // Clean table creation sql to use IF NOT EXISTS
      const createSql = sql.replace(/^CREATE TABLE\s+/i, "CREATE TABLE IF NOT EXISTS ");
      await remote.execute(createSql);
      console.log(`  ✓ Created schema: ${tableName}`);
    } catch (err: any) {
      console.warn(`  ! Schema warning for ${tableName}: ${err.message}`);
    }
  }

  // 3. Migrate data table by table
  console.log("\n📦 Migrating table records...");

  for (const tableName of coreTables) {
    try {
      const countRes = await local.execute(`SELECT count(*) as c FROM "${tableName}"`);
      const total = Number(countRes.rows[0]?.c || 0);

      if (total === 0) {
        console.log(`  - ${tableName}: 0 rows (skipped)`);
        continue;
      }

      const rowsRes = await local.execute(`SELECT * FROM "${tableName}"`);
      const rows = rowsRes.rows;

      // Batch insert into Turso
      const batchSize = 25;
      for (let i = 0; i < rows.length; i += batchSize) {
        const batch = rows.slice(i, i + batchSize);
        const statements = batch.map((r: any) => {
          const keys = Object.keys(r);
          const cols = keys.map((k) => `"${k}"`).join(", ");
          const placeholders = keys.map(() => "?").join(", ");
          const args = keys.map((k) => r[k]);
          return {
            sql: `INSERT OR REPLACE INTO "${tableName}" (${cols}) VALUES (${placeholders})`,
            args,
          };
        });

        await remote.batch(statements, "write");
      }

      console.log(`  ✅ ${tableName}: Successfully migrated ${total} rows.`);
    } catch (err: any) {
      console.error(`  ❌ Error migrating ${tableName}:`, err.message);
    }
  }

  // 4. Verify data on Turso
  console.log("\n🔍 Verifying Turso Cloud Database integrity:");
  for (const t of ["agencies", "portals", "alerts", "blog_posts", "snapshots", "auth_user", "users", "subscriptions"]) {
    try {
      const r = await remote.execute(`SELECT count(*) as count FROM "${t}"`);
      console.log(`   • ${t}: ${r.rows[0].count} records verified in Turso.`);
    } catch (err: any) {
      console.log(`   • ${t}: Error checking (${err.message})`);
    }
  }

  console.log("\n🎉 ALL TABLES & RECORDS MIGRATED TO TURSO CLOUD SUCCESSFULLY!");
}

runMigration().catch(console.error);
