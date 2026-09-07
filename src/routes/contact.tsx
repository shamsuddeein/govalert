import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Nav, Footer } from "../components/layout";
import { ShieldCheck, Mail, Send, AlertTriangle, MessageSquare, MapPin } from "lucide-react";
import { toast } from "sonner";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/contact")({
  component: ContactPage,
});

function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [inquiryType, setInquiryType] = useState("scam");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      setName("");
      setEmail("");
      setSubject("");
      setMessage("");

      if (inquiryType === "scam") {
        toast.success(
          "Scam Report Received! Our intelligence officers will audit this URL immediately.",
        );
      } else {
        toast.success("Inquiry Received! We will respond within 12 hours.");
      }
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between selection:bg-secondary/25">
      <SeoHead
        title="Contact RecruitmentAlert — Report Fake Portals & Support"
        description="Contact the RecruitmentAlert team to report a fake job portal, verify hiring announcements, or inquire about portal monitoring."
        canonicalUrl="/contact"
      />
      <Nav />
      <main className="flex-1 mx-auto max-w-5xl w-full px-6 py-12">
        <div className="mb-4">
          <BackButton to="/" label="Back to Home" />
        </div>
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-primary md:text-4xl font-semibold">
            Contact & Scam Desk
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Report a fake recruitment portal, notify us of portal uptime issues, or request general
            information.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.8fr_1fr]">
          {/* Contact Form */}
          <div className="rounded border border-border bg-card p-6 md:p-8 shadow-sm">
            <h2 className="text-sm font-bold tracking-tight mb-6 flex items-center gap-2 text-primary">
              <MessageSquare className="size-4" />
              Inquiry & Reporting Details
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Your Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Shamsuddeein Alao"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="rounded border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="rounded border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Inquiry Department
                </label>
                <select
                  value={inquiryType}
                  onChange={(e) => setInquiryType(e.target.value)}
                  className="rounded border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary"
                >
                  <option value="scam">Report a Fake Recruitment Portal (Scam Desk)</option>
                  <option value="uptime">Report Official Portal Outage / Link Issue</option>
                  <option value="support">Technical Support & Account Issues</option>
                  <option value="partnership">Vetting Partnerships & Press inquiries</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Subject / Portal URL
                </label>
                <input
                  type="text"
                  required
                  placeholder={
                    inquiryType === "scam"
                      ? "e.g., Suspicious Portal URL: http://nnpc-recruitment-2024.xyz"
                      : "e.g., Account sync issue"
                  }
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="rounded border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Description / Message
                </label>
                <textarea
                  required
                  rows={5}
                  placeholder="Provide detailed information to help our intelligence analysts process this quickly..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="rounded border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary resize-none"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center gap-2 rounded bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/95 disabled:opacity-50 transition-colors cursor-pointer"
                >
                  <Send className="size-3.5" />
                  {loading ? "Transmitting..." : "Send Report"}
                </button>
              </div>
            </form>
          </div>

          {/* Sidebar Info */}
          <div className="space-y-6">
            <section className="rounded border border-border bg-card p-6 shadow-sm">
              <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-4">
                Anti-Scam Operations
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                If you encounter a WhatsApp broadcast, Facebook post, or SMS directing you to a
                non-government website (like .xyz, .site, .org, or .info) for public sector
                recruitment, please submit the link.
              </p>
              <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-primary">
                <AlertTriangle className="size-4 text-warning" />
                <span>Audited within 15 minutes.</span>
              </div>
            </section>

            <section className="rounded border border-border bg-card p-6 shadow-sm space-y-4 font-sans">
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">
                Direct Contact
              </h3>
              <div className="space-y-3 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Mail className="size-4 text-primary shrink-0" />
                  <span className="font-semibold text-foreground">talktoshamsuddeein@gmail.com</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="size-4 text-primary shrink-0" />
                  <span>Kaduna, Nigeria (Shamsuddeen Yusuf)</span>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
