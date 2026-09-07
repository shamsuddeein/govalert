import { createFileRoute, Link } from '@tanstack/react-router';
import { Nav, Footer } from "../components/layout";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/about")({
  component: AboutPage,
});

function AboutPage() {
  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://www.recruitmentalert.com.ng"
      },
      {
        "@type": "ListItem",
        "position": 2,
        "name": "About",
        "item": "https://www.recruitmentalert.com.ng/about"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-secondary/25 font-sans">
      <SeoHead
        title="About RecruitmentAlert — Independent Civil Intelligence & Portal Verification"
        description="Learn about RecruitmentAlert, our mission, monitoring methodology, and founder Shamsuddeen Yusuf."
        canonicalUrl="/about"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[760px] px-4 sm:px-6 py-12 outline-none font-sans">
        <div className="mb-6">
          <BackButton to="/" label="Back to Home" />
        </div>
        <div className="mb-10 text-left space-y-3 border-b border-border pb-8">
          <h1 className="text-3xl font-extrabold tracking-tight text-primary md:text-[34px] leading-tight">
            About RecruitmentAlert
          </h1>
          <p className="text-[16px] text-muted-foreground leading-relaxed font-sans">
            An independent monitoring engine that checks official Nigerian federal government recruitment portals in real time.
          </p>
        </div>

        <article className="prose dark:prose-invert max-w-none space-y-6 text-[15px] sm:text-[16px] leading-[1.75] text-foreground font-sans">

          <p>
            RecruitmentAlert is an automated monitoring system built to track recruitment portals operated by Nigerian federal government ministries, departments, and agencies. The system runs HTTP health checks every 15 minutes across 42 official domain endpoints covering security forces, financial regulators, health institutions, and infrastructure boards.
          </p>

          <p>
            Unverified websites frequently copy official government logos, fabricate deadline dates, and charge job applicants fees for form submissions or pin access. Official federal government recruitment in Nigeria requires no payment at any stage of the application process. RecruitmentAlert monitors official agency servers directly so job seekers can confirm whether a recruitment notice originates from an authentic government website.
          </p>

          <p>
            When an official portal updates its page content with an active recruitment notice, candidate shortlist, or portal closure, the monitoring engine computes page content hashes and records a timestamped snapshot. Confirmed updates dispatch immediately to registered subscribers through Telegram notifications and web push alerts. Every check log remains publicly accessible on the audit log page.
          </p>

          <p>
            RecruitmentAlert operates independently and holds no affiliation with any federal government agency. To read more about the developer behind the platform, visit the <Link to="/shamsuddeen" className="text-[#0a5c38] dark:text-[#3fb68e] font-semibold underline">Shamsuddeen Yusuf developer profile</Link>. For technical inquiries or portal reporting, email <a href="mailto:talktoshamsuddeen@gmail.com" className="text-[#0a5c38] dark:text-[#3fb68e] font-semibold underline">talktoshamsuddeen@gmail.com</a>.
          </p>

        </article>

        <div className="mt-12 border-t border-border pt-8 flex flex-wrap items-center justify-between gap-4 text-xs font-semibold">
          <Link to="/portals" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline">
            &larr; View 42 Monitored Portals
          </Link>
          <Link to="/audit-log" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline">
            View Live Public Audit Log &rarr;
          </Link>
        </div>

      </main>
      <Footer />
    </div>
  );
}
