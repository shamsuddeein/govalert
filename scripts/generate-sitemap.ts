import { db, agencies, alerts } from "../db/index";
import { eq } from "drizzle-orm";
import fs from "fs";
import path from "path";

async function generateSitemap() {
  console.log("Generating sitemap with live database records...");

  const allAgencies = await db
    .select({
      id: agencies.id,
      name: agencies.name,
      acronym: agencies.acronym,
      slug: agencies.slug,
      updatedAt: agencies.updatedAt,
    })
    .from(agencies)
    .where(eq(agencies.isActive, true));

  const allAlerts = await db
    .select({
      id: alerts.id,
      createdAt: alerts.createdAt,
    })
    .from(alerts)
    .where(eq(alerts.status, "APPROVED"));

  const staticUrls = [
    { loc: "https://www.recruitmentalert.com.ng/", freq: "daily", priority: "1.0" },
    { loc: "https://www.recruitmentalert.com.ng/jobs", freq: "hourly", priority: "0.95" },
    { loc: "https://www.recruitmentalert.com.ng/agencies", freq: "daily", priority: "0.9" },
    { loc: "https://www.recruitmentalert.com.ng/blog", freq: "daily", priority: "0.9" },
    { loc: "https://www.recruitmentalert.com.ng/telegram", freq: "weekly", priority: "0.85" },
    { loc: "https://www.recruitmentalert.com.ng/status", freq: "hourly", priority: "0.8" },
    { loc: "https://www.recruitmentalert.com.ng/audit-log", freq: "hourly", priority: "0.8" },
    { loc: "https://www.recruitmentalert.com.ng/verification", freq: "monthly", priority: "0.75" },
    { loc: "https://www.recruitmentalert.com.ng/about", freq: "monthly", priority: "0.7" },
    { loc: "https://www.recruitmentalert.com.ng/faq", freq: "monthly", priority: "0.6" },
  ];

  const today = new Date().toISOString().split("T")[0];

  let xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- Core Static Pages -->
`;

  for (const s of staticUrls) {
    xml += `  <url>
    <loc>${s.loc}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${s.freq}</changefreq>
    <priority>${s.priority}</priority>
  </url>\n`;
  }

  xml += `\n  <!-- 52 Nigerian Federal MDA Profile Pages -->\n`;
  for (const a of allAgencies) {
    const slug = (a.slug || a.acronym).toLowerCase();
    const modDate = a.updatedAt ? a.updatedAt.split("T")[0] : today;
    xml += `  <url>
    <loc>https://www.recruitmentalert.com.ng/agencies/${slug}</loc>
    <lastmod>${modDate}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.85</priority>
  </url>\n`;
  }

  xml += `\n  <!-- Editorial & Investigative Articles -->\n`;
  const { blogPosts } = await import("../src/lib/blogData");
  for (const post of blogPosts) {
    const modDate = (post.published_date || post.date || today).split("T")[0];
    xml += `  <url>
    <loc>https://www.recruitmentalert.com.ng/blog/${post.slug}</loc>
    <lastmod>${modDate}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.88</priority>
  </url>\n`;
  }

  xml += `\n  <!-- Approved Active Vacancies -->\n`;
  for (const j of allAlerts) {
    const modDate = j.createdAt ? j.createdAt.split("T")[0] : today;
    xml += `  <url>
    <loc>https://www.recruitmentalert.com.ng/jobs/${j.id}</loc>
    <lastmod>${modDate}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>\n`;
  }

  xml += `</urlset>\n`;

  const targetPath = path.resolve(process.cwd(), "public/sitemap.xml");
  fs.writeFileSync(targetPath, xml, "utf-8");
  console.log(`✅ Successfully generated sitemap.xml with ${allAgencies.length} agencies, ${blogPosts.length} blog posts, and ${allAlerts.length} jobs!`);
}

generateSitemap().catch((err) => {
  console.error("Failed to generate sitemap:", err);
  process.exit(1);
});
