import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  PlusCircle,
  ArrowLeft,
  Building2,
  Calendar,
  Globe,
  Briefcase,
  FileText,
  ShieldCheck,
  Send,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Eye,
  Megaphone,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { adminApi, AdminAgency, AdminPortal } from "../lib/adminApi";
import { cn } from "../lib/utils";

export const Route = createFileRoute("/admin/jobs-create")({
  component: AdminJobsCreate,
});

const EVENT_TYPES = [
  {
    id: "RECRUITMENT_OPEN",
    label: "Recruitment Open",
    description: "New job openings or portal registration open",
    badgeBg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  },
  {
    id: "DEADLINE_EXTENDED",
    label: "Deadline Extended",
    description: "Application closing date has been pushed back",
    badgeBg: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
  },
  {
    id: "SHORTLIST_PUBLISHED",
    label: "Shortlist Published",
    description: "Screening list or successful candidate names released",
    badgeBg: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
  },
  {
    id: "RECRUITMENT_CLOSED",
    label: "Recruitment Closed",
    description: "Application window has officially ended",
    badgeBg: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30",
  },
  {
    id: "BROADCAST",
    label: "Official Broadcast",
    description: "Official agency update or high-priority announcement",
    badgeBg: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30",
  },
  {
    id: "OTHER",
    label: "General Update",
    description: "Other recruitment news or portal information",
    badgeBg: "bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/30",
  },
];

function AdminJobsCreate() {
  const navigate = useNavigate();
  const [agencies, setAgencies] = useState<AdminAgency[]>([]);
  const [portals, setPortals] = useState<AdminPortal[]>([]);
  const [loadingAgencies, setLoadingAgencies] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Form State
  const [isCustomAgency, setIsCustomAgency] = useState<boolean>(false);
  const [customAgencyName, setCustomAgencyName] = useState<string>("");
  const [customAgencyAcronym, setCustomAgencyAcronym] = useState<string>("");
  const [customCategory, setCustomCategory] = useState<string>("Civil Service");

  const [selectedAgencyId, setSelectedAgencyId] = useState<number | "">("");
  const [selectedPortalId, setSelectedPortalId] = useState<number | "">("");
  const [eventType, setEventType] = useState<string>("RECRUITMENT_OPEN");
  const [title, setTitle] = useState<string>("");
  const [positions, setPositions] = useState<string>("");
  const [deadline, setDeadline] = useState<string>("");
  const [requirements, setRequirements] = useState<string>("");
  const [sourceUrl, setSourceUrl] = useState<string>("");
  const [contentExcerpt, setContentExcerpt] = useState<string>("");
  const [trustScore, setTrustScore] = useState<number>(100);
  const [status, setStatus] = useState<"APPROVED" | "PENDING" | "HELD">("APPROVED");
  const [notifySubscribers, setNotifySubscribers] = useState<boolean>(true);

  // Load Agencies
  useEffect(() => {
    const fetchAgencies = async () => {
      setLoadingAgencies(true);
      try {
        const data = await adminApi.getAgencies();
        setAgencies(data);
        if (data.length > 0) {
          setSelectedAgencyId(data[0].id);
        }
      } catch (err: any) {
        toast.error("Failed to load agency list.");
      } finally {
        setLoadingAgencies(false);
      }
    };

    fetchAgencies();
  }, []);

  // Load Portals when agency changes
  useEffect(() => {
    if (!selectedAgencyId || isCustomAgency) {
      setPortals([]);
      setSelectedPortalId("");
      return;
    }

    const fetchPortals = async () => {
      try {
        const data = await adminApi.getPortals({ agency: String(selectedAgencyId) });
        setPortals(data);
        if (data.length > 0) {
          setSelectedPortalId(data[0].id);
          if (!sourceUrl && data[0].url) {
            setSourceUrl(data[0].url);
          }
        } else {
          setSelectedPortalId("");
        }
      } catch (err) {
        setPortals([]);
      }
    };

    fetchPortals();
  }, [selectedAgencyId, isCustomAgency]);

  const selectedAgency = agencies.find((a) => a.id === Number(selectedAgencyId));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isCustomAgency && !selectedAgencyId) {
      toast.error("Please select an agency or switch to Custom / External Agency.");
      return;
    }

    if (isCustomAgency && !customAgencyName.trim()) {
      toast.error("Please enter the Custom Agency Name.");
      return;
    }

    if (!title.trim()) {
      toast.error("Job title / headline is required.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await adminApi.createAlert({
        agency_id: !isCustomAgency && selectedAgencyId ? Number(selectedAgencyId) : undefined,
        custom_agency_name: isCustomAgency ? customAgencyName.trim() : undefined,
        custom_agency_acronym: isCustomAgency ? customAgencyAcronym.trim() : undefined,
        custom_category: isCustomAgency ? customCategory : undefined,
        portal_id: !isCustomAgency && selectedPortalId ? Number(selectedPortalId) : null,
        title: title.trim(),
        event_type: eventType,
        positions: positions.trim(),
        deadline: deadline.trim(),
        requirements: requirements.trim(),
        source_url: sourceUrl.trim() || (selectedAgency ? `https://${selectedAgency.official_domains[0] || 'gov.ng'}` : ''),
        content_excerpt: contentExcerpt.trim(),
        trust_score: trustScore,
        status: status,
        notify_subscribers: notifySubscribers && status === "APPROVED",
      });

      toast.success(res.detail || "Job post created & broadcasted successfully!");
      navigate({ to: "/admin/alerts" });
    } catch (err: any) {
      toast.error(err?.message || "Failed to create job post.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans antialiased pb-12">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <Link
            to="/admin/alerts"
            className="p-2 rounded-[8px] bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
            title="Back to Alert Queue"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2.5">
              <PlusCircle className="h-6 w-6 text-[#0a5c38] dark:text-[#3fb68e]" />
              Post New Job / Alert
            </h1>
            <p className="text-xs text-muted-foreground mt-1 font-sans">
              Manually post any recruitment opening, deadline extension, shortlist, or official notice.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <Link
            to="/admin/alerts"
            className="px-4 py-2 bg-muted text-foreground font-semibold rounded-[8px] text-xs hover:bg-muted/80 transition-all cursor-pointer"
          >
            Cancel
          </Link>
          <button
            onClick={handleSubmit}
            disabled={submitting || loadingAgencies}
            className="px-5 py-2 bg-[#0a5c38] dark:bg-[#3fb68e] text-white dark:text-zinc-950 font-semibold rounded-[8px] text-xs flex items-center gap-2 shadow-sm hover:opacity-90 transition-all cursor-pointer disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Publishing...</span>
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span>{status === "APPROVED" ? "Publish Job Post" : "Save Draft"}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Grid: Form (Left) & Preview (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Form Column */}
        <form onSubmit={handleSubmit} className="lg:col-span-7 space-y-6">
          {/* Section 1: Agency & Target */}
          <div className="bg-card border border-border rounded-[10px] p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2 text-sm font-bold text-foreground">
                <Building2 className="h-4 w-4 text-[#0a5c38] dark:text-[#3fb68e]" />
                <span>1. Agency & Destination</span>
              </div>
              <button
                type="button"
                onClick={() => setIsCustomAgency(!isCustomAgency)}
                className="text-xs font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline cursor-pointer"
              >
                {isCustomAgency ? "← Select Monitored MDA" : "+ Custom / External Agency"}
              </button>
            </div>

            {isCustomAgency ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5 md:col-span-2">
                  <label className="text-xs font-semibold text-foreground">
                    Agency Name <span className="text-destructive">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. National Intelligence Agency"
                    value={customAgencyName}
                    onChange={(e) => setCustomAgencyName(e.target.value)}
                    className="w-full h-[44px] px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38]"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Acronym</label>
                  <input
                    type="text"
                    placeholder="e.g. NIA"
                    value={customAgencyAcronym}
                    onChange={(e) => setCustomAgencyAcronym(e.target.value)}
                    className="w-full h-[44px] px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38]"
                  />
                </div>
                <div className="space-y-1.5 md:col-span-3">
                  <label className="text-xs font-semibold text-foreground">Sector Category</label>
                  <select
                    value={customCategory}
                    onChange={(e) => setCustomCategory(e.target.value)}
                    className="w-full h-[44px] px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38]"
                  >
                    <option value="Security and Law Enforcement">Security and Law Enforcement</option>
                    <option value="Finance and Revenue">Finance and Revenue</option>
                    <option value="Education">Education</option>
                    <option value="Health">Health</option>
                    <option value="Transport and Infrastructure">Transport and Infrastructure</option>
                    <option value="Civil Service">Civil Service</option>
                    <option value="Energy and Resources">Energy and Resources</option>
                  </select>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Agency Dropdown */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                    Target Agency <span className="text-destructive">*</span>
                  </label>
                  {loadingAgencies ? (
                    <div className="h-10 w-full bg-muted animate-pulse rounded-[6px]" />
                  ) : (
                    <select
                      value={selectedAgencyId}
                      onChange={(e) => setSelectedAgencyId(e.target.value ? Number(e.target.value) : "")}
                      className="w-full h-[44px] px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans cursor-pointer"
                      required={!isCustomAgency}
                    >
                      <option value="" disabled>
                        Select an Agency...
                      </option>
                      {agencies.map((agency) => (
                        <option key={agency.id} value={agency.id}>
                          {agency.acronym} : {agency.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Portal Dropdown */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                    Portal (Optional)
                  </label>
                  <select
                    value={selectedPortalId}
                    onChange={(e) => setSelectedPortalId(e.target.value ? Number(e.target.value) : "")}
                    className="w-full h-[44px] px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans"
                  >
                    <option value="">No specific portal link</option>
                    {portals.map((portal) => (
                      <option key={portal.id} value={portal.id}>
                        {portal.name} ({portal.url})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Event Type & Job Details */}
          <div className="bg-card border border-border rounded-[10px] p-5 space-y-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-bold text-foreground border-b border-border pb-3">
              <Briefcase className="h-4 w-4 text-[#0a5c38] dark:text-[#3fb68e]" />
              <span>2. Event Classification & Job Content</span>
            </div>

            {/* Event Type Selector Pills */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground">Event Category</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {EVENT_TYPES.map((type) => {
                  const isSelected = eventType === type.id;
                  return (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setEventType(type.id)}
                      className={cn(
                        "p-3 rounded-[8px] border text-left transition-all cursor-pointer flex flex-col justify-between h-full",
                        isSelected
                          ? "border-[#0a5c38] dark:border-[#3fb68e] bg-[#0a5c38]/5 dark:bg-[#3fb68e]/10 ring-1 ring-[#0a5c38] dark:ring-[#3fb68e]"
                          : "border-border bg-background hover:bg-muted/50"
                      )}
                    >
                      <span className="text-xs font-bold text-foreground block">{type.label}</span>
                      <span className="text-[10px] text-muted-foreground mt-1 block leading-tight">
                        {type.description}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Job Title */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                <span>Job Title / Headline <span className="text-destructive">*</span></span>
                <span className="text-[11px] text-muted-foreground font-normal">e.g. NCS 2026 General Officer Recruitment Open</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Nigeria Customs Service (NCS) 2026 General Recruitment Open"
                className="w-full h-10 px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans"
                required
              />
            </div>

            {/* Deadline & Application URL */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                  Application Deadline
                </label>
                <input
                  type="text"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  placeholder="e.g. 30 September 2026"
                  className="w-full h-10 px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                  <Globe className="h-3.5 w-3.5 text-muted-foreground" />
                  Official Application URL
                </label>
                <input
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="https://recruitment.customs.gov.ng"
                  className="w-full h-10 px-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans"
                />
              </div>
            </div>

            {/* Positions */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Available Positions & Roles</label>
              <textarea
                value={positions}
                onChange={(e) => setPositions(e.target.value)}
                placeholder="e.g. Assistant Superintendent II, Inspector of Customs, Customs Assistant II"
                rows={2}
                className="w-full p-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans"
              />
            </div>

            {/* Requirements & Qualifications */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Requirements & Qualifications</label>
              <textarea
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="e.g. B.Sc/HND in relevant field, WAEC/SSCE with minimum 5 credits, Age: 18-30 years"
                rows={2}
                className="w-full p-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans"
              />
            </div>

            {/* Full Excerpt / Description */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Notice Description / Excerpt</label>
              <textarea
                value={contentExcerpt}
                onChange={(e) => setContentExcerpt(e.target.value)}
                placeholder="Full details of the notice or announcement..."
                rows={4}
                className="w-full p-3 rounded-[6px] bg-background border border-border text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#0a5c38] font-sans"
              />
            </div>
          </div>

          {/* Section 3: Publishing Options & Dispatch */}
          <div className="bg-card border border-border rounded-[10px] p-5 space-y-4 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-bold text-foreground border-b border-border pb-3">
              <ShieldCheck className="h-4 w-4 text-[#0a5c38] dark:text-[#3fb68e]" />
              <span>3. Trust Score & Publishing Controls</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
              {/* Status Radio */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground block">Initial Status</label>
                <div className="space-y-2 font-sans">
                  <label className="flex items-center gap-2.5 cursor-pointer text-xs">
                    <input
                      type="radio"
                      name="status"
                      value="APPROVED"
                      checked={status === "APPROVED"}
                      onChange={() => setStatus("APPROVED")}
                      className="text-[#0a5c38] focus:ring-[#0a5c38]"
                    />
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400">APPROVED</span>
                    <span className="text-muted-foreground">(Publish live to public users immediately)</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-xs">
                    <input
                      type="radio"
                      name="status"
                      value="PENDING"
                      checked={status === "PENDING"}
                      onChange={() => setStatus("PENDING")}
                      className="text-amber-600 focus:ring-amber-500"
                    />
                    <span className="font-semibold text-amber-600 dark:text-amber-400">PENDING</span>
                    <span className="text-muted-foreground">(Save to admin queue for team review)</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-xs">
                    <input
                      type="radio"
                      name="status"
                      value="HELD"
                      checked={status === "HELD"}
                      onChange={() => setStatus("HELD")}
                      className="text-purple-600 focus:ring-purple-500"
                    />
                    <span className="font-semibold text-purple-600 dark:text-purple-400">HELD</span>
                    <span className="text-muted-foreground">(Hold for further verification)</span>
                  </label>
                </div>
              </div>

              {/* Trust Score Slider */}
              <div className="space-y-2 bg-muted/30 p-3 rounded-[8px] border border-border">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span>Trust Score</span>
                  <span className="font-mono text-[#0a5c38] dark:text-[#3fb68e] font-bold text-sm">
                    {trustScore}%
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={trustScore}
                  onChange={(e) => setTrustScore(Number(e.target.value))}
                  className="w-full accent-[#0a5c38]"
                />
                <span className="text-[11px] text-muted-foreground block">
                  {trustScore >= 90
                    ? "Verified Official Government Alert"
                    : trustScore >= 70
                    ? "Likely Official"
                    : "Unconfirmed / Custom Notice"}
                </span>
              </div>
            </div>

            {/* Subscriber Notification Checkbox */}
            {status === "APPROVED" && (
              <div className="pt-2 border-t border-border">
                <label className="flex items-start gap-3 cursor-pointer p-3 rounded-[8px] bg-[#0a5c38]/5 dark:bg-[#3fb68e]/10 border border-[#0a5c38]/20">
                  <input
                    type="checkbox"
                    checked={notifySubscribers}
                    onChange={(e) => setNotifySubscribers(e.target.checked)}
                    className="mt-0.5 rounded text-[#0a5c38] focus:ring-[#0a5c38]"
                  />
                  <div>
                    <span className="text-xs font-bold text-foreground block flex items-center gap-1.5">
                      <Megaphone className="h-3.5 w-3.5 text-[#0a5c38] dark:text-[#3fb68e]" />
                      Notify Subscribers Immediately
                    </span>
                    <span className="text-[11px] text-muted-foreground block mt-0.5">
                      Automatically trigger Telegram bot broadcasts and email notifications to keyword watchers.
                    </span>
                  </div>
                </label>
              </div>
            )}
          </div>
        </form>

        {/* Right Column: Live Card Preview */}
        <div className="lg:col-span-5 sticky top-[24px] max-h-[calc(100vh-48px)] overflow-y-auto space-y-4 pr-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Eye className="h-4 w-4 text-[#0a5c38] dark:text-[#3fb68e]" />
              Live Public Card Preview
            </span>
            <span className="text-[10px] bg-muted px-2 py-0.5 rounded text-muted-foreground font-mono">
              /jobs Component
            </span>
          </div>

          {/* Job Card Simulation */}
          <div className="bg-card border border-border rounded-[12px] p-5 space-y-4 shadow-md relative overflow-hidden transition-all">
            {/* Top Green Accent line */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-[#0a5c38] dark:bg-[#3fb68e]" />

            {/* Agency Badge Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-muted border border-border flex items-center justify-center font-bold text-xs text-primary">
                  {selectedAgency?.acronym?.[0] || "A"}
                </div>
                <div>
                  <span className="text-xs font-bold text-foreground block">
                    {selectedAgency?.name || "Select an Agency..."}
                  </span>
                  <span className="text-[10px] text-muted-foreground font-mono">
                    {selectedAgency?.acronym || "AGENCY"}
                  </span>
                </div>
              </div>

              {/* Event Badge */}
              <span
                className={cn(
                  "text-[10px] font-bold uppercase px-2 py-0.5 rounded-[4px] border font-sans",
                  EVENT_TYPES.find((t) => t.id === eventType)?.badgeBg || "bg-muted text-muted-foreground"
                )}
              >
                {EVENT_TYPES.find((t) => t.id === eventType)?.label || "RECRUITMENT OPEN"}
              </span>
            </div>

            {/* Job Title */}
            <div>
              <h3 className="text-base font-bold text-foreground leading-snug">
                {title || "Nigeria Customs Service (NCS) 2026 General Recruitment Open"}
              </h3>
            </div>

            {/* Meta Tags */}
            <div className="space-y-2 pt-1">
              {deadline && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Calendar className="h-3.5 w-3.5 text-[#0a5c38] dark:text-[#3fb68e] shrink-0" />
                  <span>
                    Deadline: <strong className="text-foreground">{deadline}</strong>
                  </span>
                </div>
              )}

              {positions && (
                <div className="flex items-start gap-2 text-xs text-muted-foreground">
                  <Briefcase className="h-3.5 w-3.5 text-[#0a5c38] dark:text-[#3fb68e] shrink-0 mt-0.5" />
                  <span className="line-clamp-2">
                    Positions: <strong className="text-foreground">{positions}</strong>
                  </span>
                </div>
              )}

              {requirements && (
                <div className="flex items-start gap-2 text-xs text-muted-foreground">
                  <FileText className="h-3.5 w-3.5 text-[#0a5c38] dark:text-[#3fb68e] shrink-0 mt-0.5" />
                  <span className="line-clamp-2">
                    Requirements: <strong className="text-foreground">{requirements}</strong>
                  </span>
                </div>
              )}
            </div>

            {/* Footer Trust Bar */}
            <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>{trustScore}% Verified Official</span>
              </div>
              <span className="text-[11px] text-muted-foreground font-mono">Ref: 0043-GA</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
