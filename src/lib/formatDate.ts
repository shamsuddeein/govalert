export function safeFormatTime(val: string | null | undefined, fallback: string = "Recently"): string {
  if (!val) return fallback;
  const d = new Date(val);
  if (isNaN(d.getTime())) return val;
  try {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return val;
  }
}

export function safeFormatDate(val: string | null | undefined, fallback: string = "Recently"): string {
  if (!val) return fallback;
  const d = new Date(val);
  if (isNaN(d.getTime())) return val;
  try {
    return d.toLocaleDateString();
  } catch {
    return val;
  }
}

export function safeFormatDateTime(val: string | null | undefined, fallback: string = "Recently"): string {
  if (!val) return fallback;
  const d = new Date(val);
  if (isNaN(d.getTime())) return val;
  try {
    return d.toLocaleString();
  } catch {
    return val;
  }
}
