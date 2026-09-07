import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Nav, Footer } from "../components/layout";
import { ChevronDown, ChevronUp } from "lucide-react";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/faq")({
  component: FaqPage,
});

interface FaqItem {
  q: string;
  a: string;
}

const faqList: FaqItem[] = [
  {
    q: "What is RecruitmentAlert?",
    a: "RecruitmentAlert is an independent verification platform that monitors Nigerian federal recruitment portals. Our crawlers check endpoints every 15 minutes, and our analysts cross-verify listings to protect job seekers from widespread recruitment scams.",
  },
  {
    q: "How do you verify a portal is authentic?",
    a: "We use a multi-phase audit process: (1) Domain analysis, checking that the portal operates on a registered, secure .gov.ng or verified corporate domain extension; (2) SSL examination, confirming the presence of genuine corporate EV certificates; (3) Cross-referencing announcement details against the national gazette, federal budget allocations, or verified MDA media releases.",
  },
  {
    q: "Is RecruitmentAlert affiliated with the Federal Government?",
    a: "No. RecruitmentAlert is completely independent. We are not government employees, and we do not influence, represent, or sell employment slots. We function solely as a public utility to assure safety and security in recruitment.",
  },
  {
    q: "Do I pay to apply for listed jobs?",
    a: "Absolutely not. Official government recruitments are free of charge. If any agency portal, recruiter, or third party demands payment for registration, exams, medical checks, or training kits, it is a scam.",
  },
  {
    q: "What does the verification score mean?",
    a: "The verification score indicates portal authenticity certainty. A high score means the portal operates on a verified official government domain with secure HTTPS connections, has no security anomalies, and content matches historical patterns. Scores drop if warning flags like non-standard domains, external redirections, or format deviations are found.",
  },
  {
    q: "How do I get alerts on Telegram?",
    a: "Click 'Get Alerts' in the navigation menu to connect to our official Telegram channel. You will receive real-time notifications on your phone whenever new recruitments are verified.",
  },
];

function FaqPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggleIndex = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <SeoHead
        title="Frequently Asked Questions — RecruitmentAlert"
        description="Find answers to common questions about RecruitmentAlert, how we monitor 42 Nigerian federal MDA portals, confidence scores, and scam prevention."
        canonicalUrl="/faq"
      />
      <Nav />
      <main className="mx-auto max-w-[720px] px-6 py-12 font-sans">
        <div className="mb-6">
          <BackButton to="/" label="Back to Home" />
        </div>
        <div className="mb-10 text-left space-y-2">
          <h1 className="text-[28px] font-bold tracking-tight text-foreground">
            Frequently Asked Questions
          </h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            Get answers on how we track MDA portals, verify sources, and prevent scams.
          </p>
        </div>

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
                    <ChevronUp className="size-4 text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronDown className="size-4 text-muted-foreground shrink-0" />
                  )}
                </button>

                {isOpen && (
                  <div className="pb-6 text-[15px] text-muted-foreground leading-relaxed">
                    {item.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </main>
      <Footer />
    </div>
  );
}
