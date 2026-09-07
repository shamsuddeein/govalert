import * as cheerio from "cheerio";
import * as crypto from "crypto";

export interface CrawlResult {
  url: string;
  statusCode: number;
  responseTimeMs: number;
  contentHash: string;
  hasChanged: boolean;
  cleanText: string;
  title: string;
  error?: string;
}

const BROWSER_USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
];

export async function crawlPortal(url: string, previousHash?: string | null): Promise<CrawlResult> {
  const startTime = Date.now();
  const userAgent = BROWSER_USER_AGENTS[Math.floor(Math.random() * BROWSER_USER_AGENTS.length)];

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000); // 12s timeout for serverless safety

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "User-Agent": userAgent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
      },
      signal: controller.signal,
      redirect: "follow",
    });

    clearTimeout(timeoutId);
    const responseTimeMs = Date.now() - startTime;
    const html = await response.text();

    const $ = cheerio.load(html);

    // Remove noise (scripts, styles, tracking, navbars, footers)
    $("script, style, noscript, iframe, svg, nav, footer, header, .footer, .header, #footer, #header").remove();

    const title = $("title").text().trim() || $("h1").first().text().trim() || "Portal Page";
    const bodyText = $("body").text().replace(/\s+/g, " ").trim();
    const cleanText = bodyText.slice(0, 15000); // Take first 15k characters for hashing & AI analysis

    // Calculate SHA-256 fingerprint of the cleaned text
    const contentHash = crypto.createHash("sha256").update(cleanText).digest("hex");
    const hasChanged = previousHash ? contentHash !== previousHash : false;

    return {
      url,
      statusCode: response.status,
      responseTimeMs,
      contentHash,
      hasChanged,
      cleanText,
      title,
    };
  } catch (err: any) {
    const responseTimeMs = Date.now() - startTime;
    return {
      url,
      statusCode: 504,
      responseTimeMs,
      contentHash: previousHash || "",
      hasChanged: false,
      cleanText: "",
      title: "",
      error: err.name === "AbortError" ? "Request timed out after 12s" : err.message,
    };
  }
}
