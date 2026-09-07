import React from "react";

export interface OfficialSourceLinkProps {
  url?: string | null;
  agencyShort?: string;
  className?: string;
  label?: string;
}

export function OfficialSourceLink({
  url,
  agencyShort,
  className = "",
  label = "OFFICIAL SOURCE",
}: OfficialSourceLinkProps) {
  const isValidUrl =
    typeof url === "string" &&
    url.trim() !== "" &&
    url.trim() !== "#" &&
    (url.startsWith("http://") || url.startsWith("https://"));

  if (!isValidUrl) {
    return (
      <span
        title="Official direct portal URL is not provided in source notice"
        className={`inline-flex items-center gap-1 font-sans text-[11px] font-semibold text-muted-foreground/50 cursor-not-allowed select-none tracking-wide ${className}`}
      >
        {/* Broken link : two chain links separated */}
        <svg
          className="size-3 shrink-0 opacity-50"
          fill="none"
          viewBox="0 0 16 16"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M6 4.5a2 2 0 0 1 2-2h1a2 2 0 0 1 2 2v.5" />
          <path d="M10 11.5a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-.5" />
          <path d="M3.5 3.5l9 9" />
        </svg>
        <span>NO DIRECT LINK</span>
      </span>
    );
  }

  const hostname = (() => {
    try {
      return new URL(url.trim()).hostname.replace(/^www\./, "");
    } catch {
      return "";
    }
  })();
  const targetName = agencyShort || hostname || "portal";
  const accessibleLabel = `${label} for ${targetName}`;

  return (
    <a
      href={url.trim()}
      target="_blank"
      rel="noreferrer"
      aria-label={accessibleLabel}
      className={`inline-flex items-center gap-1 font-sans text-[11px] font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline underline-offset-2 transition-colors tracking-wide focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0a5c38] dark:focus-visible:ring-[#3fb68e] rounded-[2px] ${className}`}
    >
      <span>{label}</span>
      {/* Diagonal arrow : external link */}
      <svg
        className="size-3 shrink-0"
        fill="none"
        viewBox="0 0 16 16"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M3 13 L13 3" />
        <path d="M6 3h7v7" />
      </svg>
    </a>
  );
}
