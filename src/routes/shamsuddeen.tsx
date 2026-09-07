import { createFileRoute, Link } from '@tanstack/react-router';
import { Nav, Footer } from "../components/layout";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/shamsuddeen")({
  component: ShamsuddeenProfilePage,
});

function ShamsuddeenProfilePage() {
  const profileSchema = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Shamsuddeen Yusuf",
    "jobTitle": "Full Stack Developer",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Kaduna",
      "addressCountry": "Nigeria"
    },
    "almaMater": "Kaduna Polytechnic",
    "url": "https://www.recruitmentalert.com.ng/shamsuddeen",
    "sameAs": [
      "https://github.com/shamsuddeein",
      "https://x.com/shamsuddeein",
      "https://linkedin.com/in/shamsuddeiin",
      "https://instagram.com/shddeen"
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-secondary/25 font-sans">
      <SeoHead
        title="Shamsuddeen Yusuf — Founder & Chief Engineer, RecruitmentAlert"
        description="Software Engineer & Founder of RecruitmentAlert. Building real-time monitoring infrastructure for 42 Nigerian federal government portals."
        canonicalUrl="/shamsuddeen"
        jsonLd={[profileSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[760px] px-6 py-12 outline-none font-sans">
        <div className="mb-6">
          <BackButton to="/" label="Back to Home" />
        </div>
        <div className="mb-10 text-left space-y-3 border-b border-border pb-8">
          <h1 className="text-3xl font-extrabold tracking-tight text-primary md:text-[34px] leading-tight">
            Shamsuddeen Yusuf
          </h1>
          <p className="text-[16px] text-muted-foreground leading-relaxed font-sans">
            Full stack developer based in Kaduna, Nigeria.
          </p>
        </div>

        <article className="prose dark:prose-invert max-w-none space-y-6 text-[15px] sm:text-[16px] leading-[1.75] text-foreground font-sans">

          <p>
            Shamsuddeen Yusuf is a full stack developer based in Kaduna, Nigeria. He is currently completing an HND in Software Engineering at Kaduna Polytechnic. He builds backend systems, REST APIs, Django applications, Telegram bots, and full stack web products. He holds a leadership position in NACOS, the student computing association at Kaduna Polytechnic.
          </p>

          <p>
            He built RecruitmentAlert, an independent platform that monitors 42 Nigerian federal government recruitment portals in real time and alerts job seekers when official recruitment opens. He is co-founder and backend lead of Likita, a telemedicine platform. He is lead developer of Cetoh, a digital marketplace. He built GovAlert, the Telegram bot system that powers recruitment alerts for thousands of Nigerian job seekers.
          </p>

          <p>
            His stack is Python, Django, Django REST Framework, APScheduler, Celery, PostgreSQL, React, TanStack Router, and Telegram Bot API.
          </p>

          <p>
            He is available for remote freelance work and contract projects. Fixed price or milestone based. No location restriction.
          </p>

          <div className="mt-10 border-t border-border pt-8 space-y-3.5 text-sm">
            <div className="flex items-center gap-3">
              <svg className="size-4 text-foreground fill-current shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <a
                href="https://github.com/shamsuddeein"
                target="_blank"
                rel="noreferrer"
                className="text-[#0a5c38] dark:text-[#3fb68e] font-medium hover:underline"
              >
                github.com/shamsuddeein
              </a>
            </div>

            <div className="flex items-center gap-3">
              <svg className="size-4 text-foreground fill-current shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
              <a
                href="https://x.com/shamsuddeein"
                target="_blank"
                rel="noreferrer"
                className="text-[#0a5c38] dark:text-[#3fb68e] font-medium hover:underline"
              >
                x.com/shamsuddeein
              </a>
            </div>

            <div className="flex items-center gap-3">
              <svg className="size-4 text-foreground fill-current shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.25V10.9H6.46M7.86 6.75a1.48 1.48 0 1 0 0 2.96 1.48 1.48 0 0 0 0-2.96z" />
              </svg>
              <a
                href="https://linkedin.com/in/shamsuddeiin"
                target="_blank"
                rel="noreferrer"
                className="text-[#0a5c38] dark:text-[#3fb68e] font-medium hover:underline"
              >
                linkedin.com/in/shamsuddeiin
              </a>
            </div>

            <div className="flex items-center gap-3">
              <svg className="size-4 text-foreground fill-current shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
              </svg>
              <a
                href="https://instagram.com/shddeen"
                target="_blank"
                rel="noreferrer"
                className="text-[#0a5c38] dark:text-[#3fb68e] font-medium hover:underline"
              >
                instagram.com/shddeen
              </a>
            </div>

            <div className="flex items-center gap-3">
              <svg className="size-4 text-foreground fill-current shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M1.5 4.5a1.5 1.5 0 0 1 1.5-1.5h18a1.5 1.5 0 0 1 1.5 1.5v15a1.5 1.5 0 0 1-1.5 1.5H3a1.5 1.5 0 0 1-1.5-1.5V4.5zm1.5.093v14.814l8.28-7.097L3 4.593zm18 0L12.72 12.31 21 19.407V4.593zM3.907 3.5l8.093 6.937L20.093 3.5H3.907zM12 13.626L4.031 20.5h15.938L12 13.626z" />
              </svg>
              <a
                href="mailto:talktoshamsuddeen@gmail.com"
                className="text-[#0a5c38] dark:text-[#3fb68e] font-medium hover:underline"
              >
                talktoshamsuddeen@gmail.com
              </a>
            </div>
          </div>

        </article>

        <div className="mt-12 border-t border-border pt-8 flex flex-wrap items-center justify-between gap-4 text-xs font-semibold">
          <Link to="/about" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline">
            &larr; About RecruitmentAlert
          </Link>
          <Link to="/portals" className="text-[#0a5c38] dark:text-[#3fb68e] hover:underline">
            View 42 Monitored Portals &rarr;
          </Link>
        </div>

      </main>
      <Footer />
    </div>
  );
}
