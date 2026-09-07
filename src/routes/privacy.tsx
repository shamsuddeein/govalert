import React from "react";
import { ShieldCheck, Mail, Lock, CheckCircle, HelpCircle } from "lucide-react";
import { createFileRoute } from "@tanstack/react-router";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/privacy")({
  component: PrivacyPolicyPage,
});

export function PrivacyPolicyPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl font-sans text-foreground">
      <SeoHead
        title="Privacy Policy — RecruitmentAlert (NDPA 2023 Compliant)"
        description="Read the official Privacy Policy for RecruitmentAlert. NDPA 2023 and NDPR compliant data privacy guidelines for job seekers."
        canonicalUrl="/privacy"
      />
      <div className="mb-6">
        <BackButton to="/" label="Back to Home" />
      </div>
      {/* Header */}
      <div className="border-b border-border pb-6 mb-8">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#0a5c38] dark:text-[#3fb68e] uppercase tracking-wider mb-2">
          <ShieldCheck className="size-4" />
          <span>NDPR & NDPA 2023 Compliance</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Last Updated: July 25, 2026 • Compliant with the Nigeria Data Protection Act (NDPA 2023) & NDPR 2019.
        </p>
      </div>

      <div className="space-y-8 text-sm leading-relaxed">
        {/* Intro */}
        <section className="space-y-3 bg-muted/30 p-4 rounded-[8px] border border-border">
          <h2 className="text-base font-bold text-foreground flex items-center gap-2">
            <Lock className="size-4 text-[#0a5c38] dark:text-[#3fb68e]" />
            1. Our Commitment to Your Privacy
          </h2>
          <p>
            RecruitmentAlert.com.ng ("we", "our", or "us") operates a real-time job monitoring service for Nigerian federal recruitment portals. 
            We respect the privacy of every Nigerian job seeker who visits our site, subscribes to alerts, or interacts with our Telegram bot.
          </p>
          <p>
            This Privacy Policy explains what personal data we collect, why we collect it, how long we retain it, and how you can exercise your legal rights under the <strong>Nigeria Data Protection Regulation (NDPR 2019)</strong> and the <strong>Nigeria Data Protection Act of 2023 (NDPA 2023)</strong>.
          </p>
        </section>

        {/* Data Inventory */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-foreground">2. Personal Data We Collect & Lawful Basis</h2>
          <p>We collect only the minimum data necessary to provide you with verified job alerts. We do not sell your personal data to anyone.</p>
          
          <div className="overflow-x-auto my-4">
            <table className="w-full text-xs text-left border-collapse border border-border">
              <thead>
                <tr className="bg-muted text-foreground font-semibold">
                  <th className="p-2.5 border border-border">Data Collected</th>
                  <th className="p-2.5 border border-border">Purpose</th>
                  <th className="p-2.5 border border-border">Lawful Basis (NDPR Art. 2.2)</th>
                  <th className="p-2.5 border border-border">Retention Period</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="p-2.5 border border-border font-medium">Email Address</td>
                  <td className="p-2.5 border border-border">Account creation & keyword job alerts</td>
                  <td className="p-2.5 border border-border font-medium">Contract (Service fulfillment)</td>
                  <td className="p-2.5 border border-border">Until account closure + 30 days</td>
                </tr>
                <tr>
                  <td className="p-2.5 border border-border font-medium">Telegram User ID & Name</td>
                  <td className="p-2.5 border border-border">Telegram bot recruitment alert delivery</td>
                  <td className="p-2.5 border border-border font-medium">Contract (Service fulfillment)</td>
                  <td className="p-2.5 border border-border">Until /stop command (Immediate deletion)</td>
                </tr>
                <tr>
                  <td className="p-2.5 border border-border font-medium">Web Push Endpoint Keys</td>
                  <td className="p-2.5 border border-border">Instant PWA browser push notifications</td>
                  <td className="p-2.5 border border-border font-medium">Consent (Opt-in permission)</td>
                  <td className="p-2.5 border border-border">Until browser unsubscribe or 404/410 response</td>
                </tr>
                <tr>
                  <td className="p-2.5 border border-border font-medium">IP Address & Security Logs</td>
                  <td className="p-2.5 border border-border">DDoS prevention, rate-limiting & security</td>
                  <td className="p-2.5 border border-border font-medium">Legitimate Interest (Platform safety)</td>
                  <td className="p-2.5 border border-border">90 days (automatic log rotation)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Data Subject Rights */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-foreground">3. Your Rights as a Data Subject</h2>
          <p>Under Part IV of the Nigeria Data Protection Act 2023, you have the following rights regarding your personal data:</p>
          <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
            <li><strong className="text-foreground">Right to Access (Information):</strong> You can request a copy of all data we hold about you.</li>
            <li><strong className="text-foreground">Right to Rectification:</strong> You can request that inaccurate or incomplete data be corrected.</li>
            <li><strong className="text-foreground">Right to Erasure (Deletion):</strong> You can request complete deletion of your personal data from our systems.</li>
            <li><strong className="text-foreground">Right to Withdraw Consent:</strong> You can stop receiving alerts at any time with one click or command.</li>
            <li><strong className="text-foreground">Right to Object:</strong> You can object to processing based on legitimate interests.</li>
          </ul>
        </section>

        {/* How to Exercise Rights */}
        <section className="space-y-3 bg-muted/20 p-4 rounded-[8px] border border-border">
          <h2 className="text-base font-bold text-foreground flex items-center gap-2">
            <CheckCircle className="size-4 text-[#0a5c38] dark:text-[#3fb68e]" />
            4. How to Exercise Your Rights (Instant Options)
          </h2>
          <div className="space-y-2">
            <p><strong>Telegram Users:</strong> Send <code>/stop</code> to <a href="https://t.me/govalerts_bot" target="_blank" rel="noreferrer" className="text-[#0a5c38] dark:text-[#3fb68e] underline">@govalerts_bot</a> at any time. Your Telegram ID and preferences will be permanently erased immediately.</p>
            <p><strong>Browser Push Subscribers:</strong> Click "Get Alerts" or manage your browser notification settings to unsubscribe anytime.</p>
            <p><strong>Data Access / Erasure Request Email:</strong> Email our Data Protection Officer at <a href="mailto:talktoshamsuddeein@gmail.com" className="text-[#0a5c38] dark:text-[#3fb68e] underline">talktoshamsuddeein@gmail.com</a>. We will fulfill all data requests within <strong>72 hours</strong> as required by law.</p>
          </div>
        </section>

        {/* Third Party & Hosting */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-foreground">5. Third-Party Services & Security</h2>
          <p>
            We do not share, rent, or sell your personal data with third-party marketers. We process data strictly using encrypted infrastructure:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
            <li><strong>HTTPS Encryption:</strong> All data transmitted between your browser/device and our servers is protected using 256-bit TLS encryption.</li>
            <li><strong>Sentry Error Monitoring:</strong> Configured with automated Data Scrubbing rules to filter out email addresses, user IDs, and auth tokens before error logs are stored.</li>
          </ul>
        </section>

        {/* DPO Contact */}
        <section className="space-y-2 pt-4 border-t border-border">
          <h2 className="text-base font-bold text-foreground flex items-center gap-2">
            <Mail className="size-4 text-[#0a5c38] dark:text-[#3fb68e]" />
            6. Contact Our Data Protection Officer
          </h2>
          <p className="text-muted-foreground">
            For any questions, data deletion requests, or data protection concerns:
          </p>
          <div className="bg-card p-3 rounded-[6px] border border-border text-xs">
            <p className="font-semibold text-foreground">Data Protection Officer (DPO)</p>
            <p>RecruitmentAlert.com.ng Data Compliance Team</p>
            <p>Email: <a href="mailto:talktoshamsuddeein@gmail.com" className="text-[#0a5c38] dark:text-[#3fb68e] underline font-medium">talktoshamsuddeein@gmail.com</a></p>
            <p>SLA Response Time: Under 72 Hours</p>
          </div>
        </section>
      </div>
    </div>
  );
}
