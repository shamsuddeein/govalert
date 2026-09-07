import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Nav, Footer } from "../components/layout";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";


export const Route = createFileRoute("/verification/")({
  component: VerificationPage,
});

interface FaqItem {
  q: string;
  a: string;
}

const faqList: FaqItem[] = [
  {
    q: "What is RecruitmentAlert Verification?",
    a: "RecruitmentAlert is an independent verification platform that monitors Nigerian federal recruitment portals. Our crawlers check endpoints every 15 minutes, and our automated audit pipeline cross-verifies listings to protect job seekers from widespread recruitment scams.",
  },
  {
    q: "How do you verify a portal is authentic?",
    a: "We use a multi-phase audit process: (1) Domain analysis, checking that the portal operates on a registered, secure .gov.ng domain; (2) SSL examination, confirming valid corporate certificates; (3) Cross-referencing announcement details against national gazette and verified MDA releases.",
  },
  {
    q: "Is RecruitmentAlert affiliated with the Federal Government?",
    a: "No. RecruitmentAlert is completely independent. We are not government employees, and we do not sell employment slots. We function solely as a public utility to assure safety and security in recruitment.",
  },
  {
    q: "Do I pay to apply for listed jobs?",
    a: "Absolutely not. Official government recruitments are free of charge. If any portal or recruiter demands payment for registration or medical checks, it is a scam.",
  },
  {
    q: "What does the verification score mean?",
    a: "The verification score indicates portal authenticity certainty. A high score means the portal operates on a verified official government domain with secure connections and zero security anomalies.",
  },
  {
    q: "How do I get alerts on Telegram?",
    a: "Click 'Get Alerts' in the navigation menu to connect to our official Telegram channel for real-time notifications.",
  },
];

function VerificationPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggleIndex = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  const stages = [
    { n: "1", label: "Stage 1", title: "Portal Monitored", body: "Automated cron checking active government subdomains every 15 minutes." },
    { n: "2", label: "Stage 2", title: "Content Extracted", body: "File system checksum / DOM tree diff comparison triggered." },
    { n: "3", label: "Stage 3", title: "Official Source Verified", body: "DNS and federal gazette indices compared for authenticity." },
    { n: "4", label: "Stage 4", title: "Published", body: "Signed audit record dispatched to feeds and subscriber panels." },
  ];

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqList.map((item) => ({
      "@type": "Question",
      "name": item.q,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": item.a
      }
    }))
  };

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
        "name": "Verification Methodology",
        "item": "https://www.recruitmentalert.com.ng/verification"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <SeoHead
        title="How RecruitmentAlert Verifies Nigerian Government Recruitment — Trust and Methodology"
        description="Learn how RecruitmentAlert monitors official Nigerian government portals, calculates trust scores, and eliminates recruitment scams."
        canonicalUrl="/verification"
        jsonLd={[faqSchema, breadcrumbSchema]}
      />
      <Nav />
      <main className="mx-auto max-w-[800px] w-full px-6 py-16">
        <div className="mb-6">
          <BackButton to="/" label="Back to Home" />
        </div>
        <div className="text-center mb-12">
          <span className="font-mono text-xs font-bold uppercase tracking-widest text-[#0a5c38] dark:text-[#3fb68e]">
            TRUST & VERIFICATION
          </span>
          <h1 className="mt-2 text-[28px] md:text-[36px] font-bold tracking-tight text-foreground">
            Verification Methodology & FAQ
          </h1>
          <p className="mt-3 text-[15px] text-muted-foreground leading-relaxed max-w-[580px] mx-auto">
            How RecruitmentAlert continuously monitors Nigerian MDA portals, calculates confidence scores, and eliminates recruitment scams.
          </p>
        </div>

        {/* Verification Pipeline */}
        <div className="mb-16 border border-border bg-card rounded-[8px] p-6 md:p-8">
          <h2 className="text-[18px] font-bold text-foreground mb-6">4-Stage Verification Pipeline</h2>
          <div className="grid gap-6 md:grid-cols-2">
            {stages.map((s) => (
              <div key={s.n} className="flex items-start gap-4">
                <div className="size-8 rounded-full border-2 border-[#0a5c38] dark:border-[#3fb68e] bg-card flex items-center justify-center font-sans text-xs font-bold text-[#0a5c38] dark:text-[#3fb68e] shrink-0">
                  {s.n}
                </div>
                <div>
                  <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#0a5c38] dark:text-[#3fb68e]">
                    {s.label}
                  </span>
                  <h3 className="text-[14px] font-bold text-foreground">{s.title}</h3>
                  <p className="mt-1 text-[12px] text-muted-foreground leading-relaxed">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ List */}
        <div>
          <h2 className="text-[20px] font-bold text-foreground mb-6">Frequently Asked Questions</h2>
          <div className="border-t border-border">
            {faqList.map((item, idx) => {
              const isOpen = openIndex === idx;
              return (
                <div key={idx} className="border-b border-border">
                  <button
                    onClick={() => toggleIndex(idx)}
                    className="flex w-full items-center justify-between py-5 text-left cursor-pointer group"
                  >
                    <span className="text-[15px] font-semibold text-foreground group-hover:text-[#0a5c38] dark:group-hover:text-[#3fb68e] transition-colors">
                      {item.q}
                    </span>
                    {isOpen ? (
                      <svg className="size-4 text-muted-foreground shrink-0" fill="none" viewBox="0 0 16 16" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M3.5 10L8 5.5 12.5 10" />
                      </svg>
                    ) : (
                      <svg className="size-4 text-muted-foreground shrink-0" fill="none" viewBox="0 0 16 16" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M3.5 6L8 10.5 12.5 6" />
                      </svg>
                    )}
                  </button>

                  {isOpen && (
                    <div className="pb-6 text-[14px] text-muted-foreground leading-relaxed">
                      {item.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
