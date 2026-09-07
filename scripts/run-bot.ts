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

if (!bot) {
  console.error("TELEGRAM_BOT_TOKEN is not configured.");
  process.exit(1);
}

console.log("Starting GovAlert Telegram Bot (@govalerts_bot)...");

bot.start({
  onStart(botInfo) {
    console.log(`Telegram Bot @${botInfo.username} (ID: ${botInfo.id}) is ACTIVE and listening!`);
    console.log("Citizens can now message the bot on Telegram (/start, /latest, /agencies, /verify).");
  },
});
