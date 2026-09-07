import { createFileRoute } from "@tanstack/react-router";
import { Nav, Footer } from "../components/layout";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/telegram")({
  component: TelegramVerificationPage,
});

function TelegramVerificationPage() {
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
        "name": "Telegram Bot Verification",
        "item": "https://www.recruitmentalert.com.ng/telegram"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between font-sans selection:bg-secondary/25">
      <SeoHead
        title="Get Nigerian Government Recruitment Alerts on Telegram — RecruitmentAlert"
        description="Join the RecruitmentAlert Telegram bot and get instant alerts when official Nigerian federal government recruitment portals open."
        canonicalUrl="/telegram"
        jsonLd={[breadcrumbSchema]}
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="flex-1 mx-auto max-w-[760px] w-full px-4 sm:px-6 py-12 space-y-8 outline-none font-sans">
        
        <div>
          <BackButton to="/" label="Back to Home" />
        </div>

        <div className="border-b border-border pb-6 space-y-2 text-left">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">
            Official Telegram Bot Verification
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Scammers frequently create clone bots on Telegram to impersonate recruitment platforms and demand payment. Follow this checklist to verify you are using the real bot.
          </p>
        </div>

        {/* Verification Card */}
        <div className="rounded-[8px] border border-[#0a5c38]/40 bg-card p-6 sm:p-8 space-y-6 shadow-sm">
          <div className="flex items-center gap-4 border-b border-border pb-6">
            <div className="p-3 bg-[#0a5c38] text-white rounded-full shrink-0">
              <svg className="size-8 fill-current" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.11.02-1.93 1.23-5.46 3.62-.51.35-.98.53-1.39.51-.46-.01-1.33-.26-1.99-.47-.8-.27-1.44-.41-1.39-.87.03-.24.35-.49.97-.75 3.79-1.65 6.32-2.73 7.57-3.26 3.61-1.53 4.36-1.8 4.85-1.8.11 0 .35.03.5.15.13.12.17.27.18.39-.01.08-.01.18-.02.26z" />
              </svg>
            </div>
            <div>
              <span className="text-xs text-muted-foreground font-mono uppercase font-bold">Official Bot Username</span>
              <h2 className="text-xl sm:text-2xl font-mono font-bold text-[#0a5c38] dark:text-[#3fb68e]">@govalerts_bot</h2>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-base font-bold text-foreground">3 Steps to Verify Before Starting:</h3>
            <ol className="list-decimal pl-5 space-y-3 text-sm text-foreground leading-relaxed">
              <li>
                <strong>Check Username Spelling:</strong> Ensure the username is exactly <code>@govalerts_bot</code>. Beware of slight variations like <i>@govalert_bot</i>, <i>@govalerts_official_bot</i>, or <i>@govalertsbot</i>.
              </li>
              <li>
                <strong>Use the Direct Official Link:</strong> Always launch the bot from this verified website URL:
                <div className="mt-2">
                  <a
                    href="https://t.me/govalerts_bot"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#0a5c38] hover:bg-[#0f7a4a] text-white dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] text-xs font-bold rounded-[6px] transition-transform active:scale-[0.98] cursor-pointer shadow-xs"
                  >
                    Open Verified Bot (@govalerts_bot) &rarr;
                  </a>
                </div>
              </li>
              <li>
                <strong>Send <code>/verify</code> Command:</strong> Once in the bot chat, send the command <code>/verify</code>. The official bot will immediately return our site domain <code>recruitmentalert.com.ng</code> and founder name <strong>Shamsuddeen Yusuf</strong>.
              </li>
            </ol>
          </div>

          <div className="rounded-[6px] border border-amber-500/30 bg-amber-500/10 p-4 space-y-1">
            <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 font-bold text-xs">
              <svg className="size-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Important Fraud Notice
            </div>
            <p className="text-xs text-foreground leading-relaxed">
              RecruitmentAlert will <strong>NEVER</strong> send you private direct messages asking for money, recharge cards, or bank transfers. All recruitment alerts sent by <code>@govalerts_bot</code> link directly to official <code>.gov.ng</code> websites.
            </p>
          </div>

        </div>

      </main>
      <Footer />
    </div>
  );
}
