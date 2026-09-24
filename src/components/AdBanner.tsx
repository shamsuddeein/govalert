import React, { useEffect, useRef } from "react";

interface AdBannerProps {
  slotId?: string;
  format?: "auto" | "rectangle" | "horizontal";
  responsive?: boolean;
  className?: string;
  minHeight?: number;
  label?: string;
}

export function AdBanner({
  slotId,
  format = "auto",
  responsive = true,
  className = "",
  minHeight = 280,
  label = "Advertisement",
}: AdBannerProps) {
  const adRef = useRef<HTMLModElement>(null);
  const pushedRef = useRef(false);

  useEffect(() => {
    // Only run on browser client after mount
    if (typeof window === "undefined") return;

    // Guard against multiple pushes in Single Page App navigation
    if (pushedRef.current) return;

    try {
      if (adRef.current && !adRef.current.getAttribute("data-adsbygoogle-status")) {
        ((window as any).adsbygoogle = (window as any).adsbygoogle || []).push({});
        pushedRef.current = true;
      }
    } catch (err) {
      console.warn("Google AdSense push error:", err);
    }
  }, [slotId]);

  return (
    <div
      className={`my-6 flex flex-col items-center justify-center overflow-hidden rounded-[8px] border border-border bg-card/60 dark:bg-card/40 text-center transition-colors ${className}`}
      style={{ minHeight: `${minHeight}px` }}
      aria-label="Advertisement"
    >
      <div className="w-full py-1 text-center font-mono text-[10px] tracking-wider text-muted-foreground uppercase opacity-70">
        {label}
      </div>

      <div className="w-full flex-1 flex items-center justify-center min-h-[250px] p-2">
        <ins
          ref={adRef}
          className="adsbygoogle block w-full"
          style={{ display: "block", minHeight: `${minHeight - 30}px` }}
          data-ad-client="ca-pub-5879973938003381"
          data-ad-slot={slotId}
          data-ad-format={format}
          data-full-width-responsive={responsive ? "true" : "false"}
        />
      </div>
    </div>
  );
}

export default AdBanner;
