import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function sanitizeJobTitle(title: string): string {
  if (!title) return "";
  let clean = title;
  clean = clean.replace(/Recruitment Update Detected/gi, "Recruitment Opening 2026");
  clean = clean.replace(/Recruitment Update — Registration Closed/gi, "Registration Notice");
  clean = clean.replace(/Recruitment Update/gi, "Recruitment Drive");
  clean = clean.replace(/Detected/gi, "");
  return clean.trim();
}
