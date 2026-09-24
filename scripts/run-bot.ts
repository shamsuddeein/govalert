import fs from "fs";
import path from "path";

// Native .env loader
try {
  if (typeof (process as any).loadEnvFile === "function") {
    (process as any).loadEnvFile();
  } else {
    const envPath = path.resolve(process.cwd(), ".env");
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, "utf-8");
      for (const line of content.split("\n")) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith("#") && trimmed.includes("=")) {
          const [key, ...rest] = trimmed.split("=");
          process.env[key.trim()] = rest.join("=").trim();
        }
      }
    }
  }
} catch (e) {
  // Ignored
}

const { bot } = await import("../server/telegram");
const { handleApiRequest } = await import("../server/api");

if (!bot) {
  console.error("TELEGRAM_BOT_TOKEN is not configured.");
  process.exit(1);
}

// ─── SCHEDULED 15-MINUTE PORTAL CRAWLER ──────────────────────────────────────
const CRAWL_INTERVAL_MS = 15 * 60 * 1000; // 15 minutes

async function runScheduledCrawler() {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`\n⏱️ [${timestamp}] [CRON] Starting 15-minute portal verification cycle...`);

  try {
    const req = new Request("http://localhost:3000/api/cron/monitor", { method: "POST" });
    const res = await handleApiRequest(req);

    if (!res) {
      console.warn(`⚠️ [${timestamp}] [CRON] Crawler endpoint returned no response.`);
      return;
    }

    const data: any = await res.json();
    const checked = data.portalsChecked || [];
    const success = checked.filter((p: any) => p.status === 200).length;
    const failed = checked.length - success;
    const changed = checked.filter((p: any) => p.changed).length;

    console.log(
      `✅ [${timestamp}] [CRON] Completed in ${data.executionTimeMs || 0}ms: ` +
      `${checked.length} portals checked (${success} online, ${failed} offline, ${changed} changes detected)`
    );
  } catch (err: any) {
    console.error(`❌ [${timestamp}] [CRON] Scheduled crawl tick failed:`, err?.message || err);
  }
}

// ─── START BOT & SCHEDULER ───────────────────────────────────────────────────
console.log("Starting GovAlert Telegram Bot (@govalerts_bot)...");

bot.start({
  onStart(botInfo) {
    console.log(`Telegram Bot @${botInfo.username} (ID: ${botInfo.id}) is ACTIVE and listening!`);
    console.log("Citizens can now message the bot on Telegram (/start, /latest, /agencies, /verify).");
    console.log(`Autonomous Crawler Worker is scheduled to run every 15 minutes (next tick in 3s)...`);

    // Run initial crawl 3 seconds after boot, then every 15 minutes continuously
    setTimeout(runScheduledCrawler, 3000);
    setInterval(runScheduledCrawler, CRAWL_INTERVAL_MS);
  },
});
