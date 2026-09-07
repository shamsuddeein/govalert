import React from "react";
import { ShieldAlert, CheckCircle2, AlertTriangle, FileText } from "lucide-react";
import { createFileRoute } from "@tanstack/react-router";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/terms")({
  component: TermsOfServicePage,
});

export function TermsOfServicePage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl font-sans text-foreground">
      <SeoHead
        title="Terms of Service — RecruitmentAlert"
        description="Read the Terms of Service for using RecruitmentAlert.com.ng independent government recruitment monitoring platform."
        canonicalUrl="/terms"
      />
      <div className="mb-6">
        <BackButton to="/" label="Back to Home" />
      </div>
      {/* Header */}
      <div className="border-b border-border pb-6 mb-8">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#0a5c38] dark:text-[#3fb68e] uppercase tracking-wider mb-2">
          <FileText className="size-4" />
          <span>Legal Agreement</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Terms of Service</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Last Updated: July 25, 2026 • Terms governing the use of RecruitmentAlert.com.ng.
        </p>
      </div>

      <div className="space-y-8 text-sm leading-relaxed">
        {/* Zero Fee Prominent Banner */}
        <section className="bg-[#0a5c38]/10 dark:bg-[#3fb68e]/10 border border-[#0a5c38]/30 dark:border-[#3fb68e]/30 p-4 rounded-[8px] space-y-2">
          <div className="flex items-center gap-2 text-[#0a5c38] dark:text-[#3fb68e] font-bold text-base">
            <CheckCircle2 className="size-5 shrink-0" />
            <h2>Zero Fee Guarantee: Beware of Scams</h2>
          </div>
          <p className="text-xs text-foreground font-medium leading-relaxed">
            <strong>Official Nigerian Government recruitment is 100% FREE.</strong> Legitimate federal agencies (Customs, Immigration, Police, EFCC, Civil Service, NNPC) never demand money, processing fees, scratch cards, or payments for application forms. RecruitmentAlert.com.ng will NEVER ask you for money or fees. If anyone asks you for money in exchange for a government job, it is a scam.
          </p>
        </section>

        {/* 1. Independent Service */}
        <section className="space-y-2">
          <h2 className="text-base font-bold text-foreground">1. Independent Service Disclaimer</h2>
          <p>
            RecruitmentAlert.com.ng is an <strong>independent automated monitoring platform</strong>. We are not affiliated, associated, authorized, endorsed by, or in any way officially connected with the Federal Government of Nigeria, the Federal Civil Service Commission (FCSC), or any Ministries, Departments, and Agencies (MDAs).
          </p>
        </section>

        {/* 2. Nature of Content & Verification */}
        <section className="space-y-2">
          <h2 className="text-base font-bold text-foreground">2. Nature of Information & User Verification</h2>
          <p>
            Our service automatically scans official government portal URLs to detect changes, new openings, and shortlist announcements. While we enforce strict verification algorithms to detect fake portals and scam domains:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
            <li>We do not originate or control government portal announcements.</li>
            <li>Users are solely responsible for verifying recruitment notices directly on official <code>.gov.ng</code> websites before submitting credentials or personal information.</li>
            <li>Recruitment deadlines and requirements are determined exclusively by official agencies and may change without notice.</li>
          </ul>
        </section>

        {/* 3. Acceptable Use */}
        <section className="space-y-2">
          <h2 className="text-base font-bold text-foreground">3. Acceptable Use Policy</h2>
          <p>
            You agree to use RecruitmentAlert.com.ng for legitimate job search purposes. You must not:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
            <li>Attempt to scrape, overload, or compromise our alert distribution system.</li>
            <li>Use automated bots or scripts to query our public APIs beyond reasonable rate limits.</li>
            <li>Impersonate RecruitmentAlert staff or send fake job alerts to third parties.</li>
          </ul>
        </section>

        {/* 4. Limitation of Liability */}
        <section className="space-y-2">
          <h2 className="text-base font-bold text-foreground">4. Limitation of Liability</h2>
          <p className="text-muted-foreground">
            RecruitmentAlert.com.ng provides recruitment monitoring "as is" without warranties of any kind. In no event shall RecruitmentAlert or its operators be liable for any decision made or action taken by an applicant in reliance upon information retrieved from external portal URLs.
          </p>
        </section>

        {/* 5. Contact */}
        <section className="border-t border-border pt-4 text-xs text-muted-foreground space-y-1">
          <p className="font-semibold text-foreground">Questions Regarding Terms of Service?</p>
          <p>Email: <a href="mailto:talktoshamsuddeein@gmail.com" className="text-[#0a5c38] dark:text-[#3fb68e] underline font-medium">talktoshamsuddeein@gmail.com</a></p>
        </section>
      </div>
    </div>
  );
}
