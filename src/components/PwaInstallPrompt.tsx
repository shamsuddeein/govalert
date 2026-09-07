import React, { useState, useEffect } from "react";
import { X, Download, ShieldCheck } from "lucide-react";
import { requestAndSubscribeWebPush } from "../lib/pushManager";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

export function PwaInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // 1. Check 7-day suppression period
    const dismissedTime = localStorage.getItem("pwa_prompt_dismissed");
    if (dismissedTime) {
      const daysSinceDismissed = (Date.now() - parseInt(dismissedTime, 10)) / (1000 * 3600 * 24);
      if (daysSinceDismissed < 7) {
        return;
      }
    }

    // 2. Check if already installed
    if (window.matchMedia("(display-mode: standalone)").matches) {
      return;
    }

    // 3. Listen for browser install prompt trigger
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      const event = e as BeforeInstallPromptEvent;
      setDeferredPrompt(event);

      // Check listing view count threshold (display after viewing >= 2 listings)
      const views = parseInt(sessionStorage.getItem("listing_views_count") || "0", 10);
      if (views >= 2) {
        setVisible(true);
      }
    };

    const handleAppInstalled = () => {
      setVisible(false);
      setDeferredPrompt(null);
      localStorage.setItem("pwa_installed", "true");
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    // Also check session storage updates periodically or on mount
    const views = parseInt(sessionStorage.getItem("listing_views_count") || "0", 10);
    if (views >= 2 && deferredPrompt) {
      setVisible(true);
    }

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, [deferredPrompt]);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const choiceResult = await deferredPrompt.userChoice;

    if (choiceResult.outcome === "accepted") {
      // Prompt for Push notification permission simultaneously
      requestAndSubscribeWebPush();
    } else {
      localStorage.setItem("pwa_prompt_dismissed", Date.now().toString());
    }

    setVisible(false);
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setVisible(false);
    localStorage.setItem("pwa_prompt_dismissed", Date.now().toString());
  };

  if (!visible || !deferredPrompt) return null;

  return (
    <div
      role="banner"
      aria-label="Install RecruitmentAlert Progressive Web App"
      className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-md z-50 bg-card border border-[#0a5c38]/40 dark:border-[#3fb68e]/40 rounded-[12px] p-4 shadow-2xl animate-in slide-in-from-bottom-5 duration-300 font-sans"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="size-10 rounded-[8px] bg-[#0a5c38] text-white dark:bg-[#3fb68e] dark:text-[#0c1015] flex items-center justify-center shrink-0 shadow-sm mt-0.5">
            <Download className="size-5" aria-hidden="true" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1.5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Install RecruitmentAlert
              </h3>
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#0a5c38] dark:text-[#3fb68e] bg-[#0a5c38]/10 px-1.5 py-0.5 rounded">
                <ShieldCheck className="size-3" aria-hidden="true" />
                Instant Alerts
              </span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Add RecruitmentAlert to your home screen for instant job updates & offline access. No app store download needed.
            </p>
          </div>
        </div>

        <button
          onClick={handleDismiss}
          aria-label="Dismiss app install banner"
          className="text-muted-foreground hover:text-foreground p-1 rounded-[4px] hover:bg-muted transition-colors cursor-pointer shrink-0"
        >
          <X className="size-4" />
        </button>
      </div>

      <div className="mt-3 pt-3 border-t border-border flex items-center justify-end gap-2">
        <button
          onClick={handleDismiss}
          className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground cursor-pointer rounded-[6px]"
        >
          Not now
        </button>
        <button
          onClick={handleInstallClick}
          className="px-4 py-1.5 text-xs font-semibold text-white bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 dark:text-[#0c1015] rounded-[6px] transition-all cursor-pointer shadow-sm flex items-center gap-1.5"
        >
          <span>Add to Home Screen</span>
        </button>
      </div>
    </div>
  );
}
