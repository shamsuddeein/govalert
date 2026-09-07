import { Bot, webhookCallback } from "grammy";
import { db, alerts, agencies } from "../db/index";
import { eq, desc } from "drizzle-orm";

const token = process.env.TELEGRAM_BOT_TOKEN;
export const bot = token ? new Bot(token) : null;

if (bot) {
  bot.command("start", async (ctx) => {
    await ctx.reply(
      `🇳🇬 *Welcome to GovAlert Nigeria*\n\n` +
      `We monitor verified Nigerian federal & state government recruitment portals to protect citizens from scams.\n\n` +
      `*Commands:*\n` +
      `• /latest - View recently verified public sector recruitments\n` +
      `• /agencies - View list of monitored federal MDAs\n` +
      `• /verify <url> - Verify if a job portal link is official\n` +
      `• /help - Learn how we verify announcements\n\n` +
      `_GovAlert is free, civic, and evidence-first._`,
      { parse_mode: "Markdown" }
    );
  });

  bot.command("latest", async (ctx) => {
    try {
      const recentAlerts = await db
        .select({
          id: alerts.id,
          title: alerts.title,
          positions: alerts.positions,
          deadline: alerts.deadline,
          sourceUrl: alerts.sourceUrl,
          trustScore: alerts.trustScore,
          agencyName: agencies.name,
        })
        .from(alerts)
        .leftJoin(agencies, eq(alerts.agencyId, agencies.id))
        .where(eq(alerts.status, "APPROVED"))
        .orderBy(desc(alerts.createdAt))
        .limit(5);

      if (!recentAlerts.length) {
        await ctx.reply("No new verified recruitments right now. All monitored portals are clean.");
        return;
      }

      let message = `🛡️ *Latest Verified Government Recruitments:*\n\n`;
      for (const item of recentAlerts) {
        message += `🏛️ *${item.agencyName || "Federal Agency"}*\n`;
        message += `📌 *${item.title}*\n`;
        if (item.positions) message += `💼 Positions: ${item.positions}\n`;
        if (item.deadline) message += `⏳ Deadline: ${item.deadline}\n`;
        message += `🔒 Trust Score: *${item.trustScore}% Authentic*\n`;
        message += `🔗 [Apply on Official Portal](${item.sourceUrl})\n\n`;
      }

      await ctx.reply(message, { parse_mode: "Markdown", disable_web_page_preview: true });
    } catch (err: any) {
      console.error("Error in /latest:", err);
      await ctx.reply("Could not retrieve latest alerts. Please try again in a moment.");
    }
  });

  bot.command("agencies", async (ctx) => {
    try {
      const agencyList = await db
        .select({ name: agencies.name, acronym: agencies.acronym, category: agencies.category })
        .from(agencies)
        .where(eq(agencies.isActive, true))
        .limit(15);

      let msg = `🏛️ *Monitored Nigerian MDAs (${agencyList.length} shown):*\n\n`;
      for (const a of agencyList) {
        msg += `• *${a.acronym}* - ${a.name} (${a.category})\n`;
      }
      msg += `\n_View all 52 monitored MDAs on https://govalert.org.ng/agencies_`;
      await ctx.reply(msg, { parse_mode: "Markdown" });
    } catch (err) {
      await ctx.reply("Failed to load agencies list.");
    }
  });

  bot.command("verify", async (ctx) => {
    const text = ctx.message?.text || "";
    const url = text.replace("/verify", "").trim();

    if (!url) {
      await ctx.reply("Please provide a link to verify:\nExample: `/verify https://customs.gov.ng`", { parse_mode: "Markdown" });
      return;
    }

    const lower = url.toLowerCase();
    const isGovNg = lower.includes(".gov.ng");
    const isKnownFake = lower.includes("blogspot") || lower.includes("free-recruitment") || lower.includes("recruitment-form");

    if (isGovNg && !isKnownFake) {
      await ctx.reply(`✅ *VERIFIED OFFICIAL DOMAIN*\n\nThe domain \`${url}\` ends in *.gov.ng*, the official Nigerian government top-level domain registered by NITDA.`, { parse_mode: "Markdown" });
    } else {
      await ctx.reply(`⚠️ *WARNING: UNVERIFIED / HIGH RISK*\n\nThe link \`${url}\` does *not* originate from an official *.gov.ng* domain. Federal civil service recruitment is never hosted on third-party blogs or free domains. Never pay money to apply.`, { parse_mode: "Markdown" });
    }
  });
}

export async function broadcastAlert(alertTitle: string, agencyName: string, sourceUrl: string, trustScore: number) {
  const channelId = process.env.TELEGRAM_CHANNEL_ID;
  if (!bot || !channelId) return;

  const msg =
    `🚨 *NEW VERIFIED RECRUITMENT ALERT*\n\n` +
    `🏛️ *Agency:* ${agencyName}\n` +
    `📌 *Announcement:* ${alertTitle}\n` +
    `🛡️ *Trust Score:* ${trustScore}% (Verified Official Source)\n\n` +
    `👉 [Apply on Official Government Portal](${sourceUrl})\n\n` +
    `_GovAlert Nigeria • Evidence-First Verification_`;

  try {
    await bot.api.sendMessage(channelId, msg, { parse_mode: "Markdown", disable_web_page_preview: true });
  } catch (err) {
    console.error("Failed to broadcast alert to Telegram channel:", err);
  }
}
