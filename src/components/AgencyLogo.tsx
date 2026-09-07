import { useState } from "react";
import { agenciesData } from "../lib/agenciesData";

function domainFor(short: string): string | null {
  const a = agenciesData.find((x) => x.short.toUpperCase() === short.toUpperCase());
  if (!a) return null;
  try {
    return new URL(a.officialWebsite).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

interface Props {
  short: string;
  url?: string;
  size?: number;
  className?: string;
  rounded?: string;
}

function getSectorStyle(short: string): string {
  const s = short.toUpperCase();
  if (["ARMY", "NAVY", "NAF", "NPF", "POLICE", "NDA", "NCS", "CUSTOMS"].includes(s)) {
    return "bg-[#0a5c38] text-white border-[#074228]";
  }
  if (["CBN", "FIRS", "NPA", "CREDICORP", "FMF"].includes(s)) {
    return "bg-[#1e3a8a] text-white border-[#172554]";
  }
  if (["NIS", "NCOS", "NSCDC", "CDCFIB", "DSS", "EFCC", "ICPC", "NDLEA"].includes(s)) {
    return "bg-[#0f766e] text-white border-[#115e59]";
  }
  if (["TRCN", "JAMB", "UBEC", "FCSC", "FME", "FMH", "FMA", "FMI"].includes(s)) {
    return "bg-[#b45309] text-white border-[#78350f]";
  }
  return "bg-slate-800 text-slate-100 border-slate-900";
}

/**
 * Renders the real favicon/logo of a government agency via public favicon services.
 * Falls back gracefully to a heraldic monogram chip if the domain image is unavailable or fails to load.
 */
export function AgencyLogo({ short, url, size = 40, className = "", rounded = "rounded-[6px]" }: Props) {
  const [srcIdx, setSrcIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failedAll, setFailedAll] = useState(false);

  const agency = agenciesData.find((x) => x.short.toUpperCase() === short.toUpperCase());
  
  const targetUrl = url || agency?.officialWebsite || agency?.recruitmentPortal || `https://${short.toLowerCase()}.gov.ng`;

  const domain = (() => {
    try {
      return new URL(targetUrl).hostname.replace(/^www\./, "");
    } catch {
      return `${short.toLowerCase()}.gov.ng`;
    }
  })();

  const sources = [
    `https://www.google.com/s2/favicons?domain=${domain}&sz=32`,
  ];
  const src = !failedAll && srcIdx < sources.length ? sources[srcIdx] : null;

  const boxCls = `relative grid place-items-center overflow-hidden border border-border bg-white dark:bg-[#1a2230] ${rounded} ${className} focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0a5c38] dark:focus-visible:ring-[#3fb68e] focus-visible:ring-offset-2 dark:focus-visible:ring-offset-background`;
  const style = { width: size, height: size } as const;
  const altText = agency ? `${agency.name} official logo` : `${short} official logo`;

  if (!src || failedAll) {
    const fallbackBoxCls = `relative inline-flex items-center justify-center text-center overflow-hidden bg-[#F0FDF4] text-[#166534] border border-[#166534]/30 font-mono font-bold text-xs shrink-0 shadow-xs ${rounded} ${className} focus:outline-none focus-visible:ring-2 focus-visible:ring-[#166534]`;
    return (
      <span
        tabIndex={0}
        role="img"
        aria-label={altText}
        className={fallbackBoxCls}
        style={style}
        title={agency?.name || short}
      >
        {short.slice(0, 4).toUpperCase()}
      </span>
    );
  }

  return (
    <span className={boxCls} style={style} tabIndex={0} role="img" aria-label={altText}>
      {loading && (
        <span className="absolute inset-0 animate-pulse bg-muted/80 dark:bg-muted/40" />
      )}
      <img
        key={src}
        src={src}
        alt=""
        width={Math.round(size * 0.7)}
        height={Math.round(size * 0.7)}
        loading="lazy"
        decoding="async"
        onLoad={(e) => {
          const img = e.currentTarget;
          if (img.naturalWidth <= 16 && img.naturalHeight <= 16 && srcIdx < sources.length - 1) {
            setSrcIdx(srcIdx + 1);
          } else if (img.naturalWidth <= 16 && img.naturalHeight <= 16) {
            setFailedAll(true);
            setLoading(false);
          } else {
            setLoading(false);
          }
        }}
        onError={() => {
          if (srcIdx < sources.length - 1) {
            setSrcIdx(srcIdx + 1);
          } else {
            setFailedAll(true);
            setLoading(false);
          }
        }}
        className={`object-contain transition-opacity duration-300 ${loading ? "opacity-0" : "opacity-100"}`}
      />
    </span>
  );
}