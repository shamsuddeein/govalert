import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { Toaster } from "../components/ui/sonner";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error("Root Route Error:", error);
  const router = useRouter();

  const isChunkError =
    error?.message &&
    (error.message.toLowerCase().includes("dynamically imported module") ||
      error.message.toLowerCase().includes("failed to fetch") ||
      error.message.toLowerCase().includes("importing a module script failed"));

  const handleTryAgain = () => {
    if (isChunkError) {
      window.location.href = window.location.pathname + "?v=" + Date.now();
    } else {
      router.invalidate();
      reset();
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 font-sans">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-bold tracking-tight text-foreground font-sans">
          {isChunkError ? "New Version Available" : "This page didn't load"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground font-sans">
          {isChunkError
            ? "RecruitmentAlert was updated with new features. Please reload the page to get the latest version."
            : "Something went wrong on our end. You can try refreshing or head back home."}
        </p>
        {error?.message && (
          <div className="mt-3 p-3 text-xs font-mono text-red-600 bg-red-50 dark:bg-red-950/40 dark:text-red-400 rounded-[6px] border border-red-200 dark:border-red-900 text-left overflow-auto max-h-32">
            {error.message}
          </div>
        )}
        <div className="mt-6 flex flex-wrap justify-center gap-2 font-sans">
          <button
            onClick={handleTryAgain}
            className="inline-flex items-center justify-center rounded-[6px] bg-[#0a5c38] dark:bg-[#3fb68e] px-4 py-2 text-sm font-semibold text-white dark:text-[#0c1015] transition-colors hover:opacity-90 cursor-pointer"
          >
            {isChunkError ? "Reload Page" : "Try again"}
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-[6px] border border-border bg-background px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
          >
            Go home
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "NNPC, NCS & Federal Government Jobs 2026. RecruitmentAlert" },
      {
        name: "description",
        content:
          "Monitor 42 Nigerian federal recruitment portals in real time. Verify NNPC, Customs, EFCC, Immigration, and Civil Service job openings & portal status.",
      },
      { name: "robots", content: "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" },
      { name: "author", content: "RecruitmentAlert" },
      { name: "google-site-verification", content: "kR7UcDpncxOJecVqCmw0GrzlmRq77nWrG8Nd_UsTjjk" },
      {
        property: "og:title",
        content: "NNPC, NCS & Federal Government Jobs 2026. RecruitmentAlert",
      },
      {
        property: "og:description",
        content:
          "Real-time monitoring of 42 Nigerian federal recruitment portals. Every civil service listing verified from official .gov.ng sources.",
      },
      { property: "og:type", content: "website" },
      { property: "og:url", content: "https://www.recruitmentalert.com.ng" },
      { property: "og:image", content: "https://www.recruitmentalert.com.ng/favicon.svg" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:site", content: "@RecruitmentAlertNG" },
      { name: "twitter:title", content: "NNPC, NCS & Federal Government Jobs 2026. RecruitmentAlert" },
      { name: "twitter:description", content: "Real-time monitoring of 42 Nigerian federal recruitment portals. Verified civil service job alerts." },
      { name: "twitter:image", content: "https://www.recruitmentalert.com.ng/favicon.svg" },
      { name: "theme-color", content: "#0a5c38" },
      { name: "mobile-web-app-capable", content: "yes" },
      { name: "apple-mobile-web-app-capable", content: "yes" },
      { name: "apple-mobile-web-app-status-bar-style", content: "black-translucent" },
      { name: "apple-mobile-web-app-title", content: "RecruitmentAlert" },
    ],
    links: [
      { rel: "manifest", href: "/manifest.json" },
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "icon", href: "/favicon.svg", type: "image/svg+xml" },
      { rel: "apple-touch-icon", href: "/icon-192x192.png" },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("theme");if(t==="dark"){document.documentElement.classList.add("dark");}else{document.documentElement.classList.remove("dark");}}catch(e){document.documentElement.classList.remove("dark");}})();`,
          }}
        />
        <HeadContent />
      </head>
      <body className="overflow-x-hidden">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2.5 focus:bg-[#0a5c38] focus:text-white focus:font-semibold focus:rounded-[6px] focus:shadow-xl focus:outline-none focus:ring-2 focus:ring-white"
        >
          Skip to main content
        </a>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

import { PwaInstallPrompt } from "../components/PwaInstallPrompt";

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  useEffect(() => {
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/service-worker.js", { scope: "/" })
          .then((reg) => {
            console.log("PWA Service Worker registered with scope:", reg.scope);
          })
          .catch((err) => {
            console.warn("PWA Service Worker registration failed:", err);
          });
      });
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {/* Required: nested routes render here. Removing <Outlet /> breaks all child routes. */}
      <Outlet />
      <Toaster />
      <PwaInstallPrompt />
    </QueryClientProvider>
  );
}
