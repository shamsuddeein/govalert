import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Building2,
  Plus,
  Search,
  CheckCircle,
  XCircle,
  Loader2,
  X,
  AlertTriangle,
  Globe,
} from "lucide-react";
import { toast } from "sonner";
import { adminApi, AdminAgency } from "../lib/adminApi";
import { cn } from "../lib/utils";
import { AccessibleModal } from "../components/AccessibleModal";

export const Route = createFileRoute("/admin/agencies")({
  component: AdminAgenciesComponent,
});

function formatDate(dateStr?: string): string {
  if (!dateStr) return ":";
  try {
    return new Date(dateStr).toLocaleDateString("en-NG", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function AdminAgenciesComponent() {
  const [agencies, setAgencies] = useState<AdminAgency[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  
  // Modals state
  const [selectedAgency, setSelectedAgency] = useState<AdminAgency | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deactivatingAgency, setDeactivatingAgency] = useState<AdminAgency | null>(null);
  const [deactivatingInFlight, setDeactivatingInFlight] = useState(false);

  const loadAgencies = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getAgencies({ search, category });
      setAgencies(data);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load agencies.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgencies();
  }, [category]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadAgencies();
  };

  const confirmDeactivate = async () => {
    if (!deactivatingAgency) return;
    setDeactivatingInFlight(true);
    try {
      await adminApi.deleteAgency(deactivatingAgency.id);
      toast.success(`Agency '${deactivatingAgency.name}' deactivated.`);
      setDeactivatingAgency(null);
      if (selectedAgency?.id === deactivatingAgency.id) {
        setSelectedAgency(null);
      }
      loadAgencies();
    } catch (err: any) {
      toast.error(err?.message || "Failed to deactivate agency.");
    } finally {
      setDeactivatingInFlight(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans antialiased">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold font-sans tracking-tight text-foreground flex items-center gap-2.5">
            <Building2 className="h-6 w-6 text-primary" />
            Agency Management
          </h1>
          <p className="text-xs text-muted-foreground mt-1 font-sans">
            Manage monitored Nigerian government bodies, official whitelisted domains, and vetting scores.
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2.5 bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 text-white dark:text-[#0c1015] font-sans font-semibold text-xs rounded-[6px] transition-all flex items-center gap-2 shadow-sm cursor-pointer self-start md:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>Add Agency</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-card p-3.5 rounded-[8px] border border-border">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80 font-sans">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search acronym or name..."
            className="pl-9 pr-4 h-[44px] w-full bg-card border border-border rounded-[6px] text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-primary font-sans"
          />
        </form>

        <div className="w-full sm:w-48">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="h-[44px] w-full px-3 bg-card border border-border rounded-[6px] text-xs font-medium text-foreground outline-none cursor-pointer focus:border-primary font-sans"
          >
            <option value="">All Categories</option>
            <option value="SECURITY">Security & Law Enforcement</option>
            <option value="FINANCE">Finance & Revenue</option>
            <option value="UTILITIES">Utilities & Energy</option>
            <option value="HEALTH">Health & Pharma</option>
            <option value="EDUCATION">Education & Research</option>
            <option value="TRANSPORT">Transport & Aviation</option>
            <option value="STATISTICS">Statistics & Data</option>
            <option value="JUDICIARY">Judiciary & Legal</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-3 font-sans">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-xs font-sans">Loading agency roster...</span>
        </div>
      ) : agencies.length === 0 ? (
        <div className="bg-card border border-border rounded-[8px] p-12 text-center text-muted-foreground text-xs font-sans">
          No agencies match your search.
        </div>
      ) : (
        <div className="bg-card border border-border rounded-[8px] overflow-hidden shadow-sm font-sans">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted border-b border-border text-muted-foreground font-sans font-semibold uppercase tracking-wider">
                <tr>
                  <th className="p-3.5">Acronym</th>
                  <th className="p-3.5">Agency Name</th>
                  <th className="p-3.5">Category</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Vetted Score</th>
                  <th className="p-3.5">Jobs Available</th>
                  <th className="p-3.5">Subscribers</th>
                  <th className="p-3.5">Last Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-foreground">
                {agencies.map((agency) => (
                  <tr
                    key={agency.id}
                    onClick={() => setSelectedAgency(agency)}
                    className="hover:bg-muted/40 cursor-pointer transition-colors group"
                  >
                    <td className="p-3.5 font-mono font-bold text-primary group-hover:underline">
                      {agency.acronym}
                    </td>
                    <td className="p-3.5 font-semibold text-foreground max-w-xs truncate font-sans">
                      {agency.name}
                    </td>
                    <td className="p-3.5 font-sans text-muted-foreground">{agency.category}</td>
                    <td className="p-3.5 font-sans">
                      {agency.is_active ? (
                        <span className="inline-flex items-center gap-1 text-[#0a5c38] dark:text-[#3fb68e] bg-[#0a5c38]/10 border border-[#0a5c38]/30 px-2.5 py-0.5 rounded-[6px] text-[11px] font-semibold uppercase tracking-wider font-sans">
                          <CheckCircle className="h-3 w-3" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-muted-foreground bg-[color:var(--closed)]/10 border border-[color:var(--closed)]/20 px-2.5 py-0.5 rounded-[6px] text-[11px] font-semibold uppercase tracking-wider font-sans">
                          <XCircle className="h-3 w-3" /> Inactive
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 font-mono">
                      <span className="px-2 py-0.5 rounded-[6px] bg-muted text-foreground border border-border font-bold">
                        {agency.vetted_score}/100
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-foreground font-semibold">
                      {agency.alert_count ?? agency.portal_count ?? 0}
                    </td>
                    <td className="p-3.5 font-mono text-muted-foreground font-semibold">
                      {agency.subscriber_count ?? 0}
                    </td>
                    <td className="p-3.5 font-mono text-muted-foreground">
                      {formatDate(agency.updated_at || agency.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Agency Modal */}
      {isCreateModalOpen && (
        <AgencyFormModal
          agency={null}
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={() => {
            setIsCreateModalOpen(false);
            loadAgencies();
          }}
        />
      )}

      {/* Row Click Detail & Edit View Drawer/Modal */}
      {selectedAgency && (
        <AgencyFormModal
          agency={selectedAgency}
          onClose={() => setSelectedAgency(null)}
          onSuccess={() => {
            setSelectedAgency(null);
            loadAgencies();
          }}
          onDeactivateRequest={() => setDeactivatingAgency(selectedAgency)}
        />
      )}

      {/* Deactivation Confirmation Dialog */}
      {deactivatingAgency && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-destructive/40 rounded-[8px] p-6 max-w-md w-full shadow-lg space-y-4 font-sans text-xs">
            <div className="flex items-center gap-3 text-destructive font-sans font-bold text-sm">
              <AlertTriangle className="h-5 w-5 shrink-0" />
              <span>Confirm Agency Deactivation</span>
            </div>

            <p className="text-foreground leading-relaxed font-sans">
              This will hide <strong className="text-foreground font-mono">{deactivatingAgency.name}</strong> from the public site. Portals will stop being monitored. Continue?
            </p>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-border font-sans">
              <button
                type="button"
                onClick={() => setDeactivatingAgency(null)}
                disabled={deactivatingInFlight}
                className="px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-[6px] cursor-pointer font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDeactivate}
                disabled={deactivatingInFlight}
                className="px-4 py-2 bg-destructive hover:bg-destructive/90 text-white font-semibold rounded-[6px] flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                {deactivatingInFlight && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                <span>Confirm Deactivate</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Agency Form & Detail Modal with Tag Input ──────────────────────────────────

function AgencyFormModal({
  agency,
  onClose,
  onSuccess,
  onDeactivateRequest,
}: {
  agency: AdminAgency | null;
  onClose: () => void;
  onSuccess: () => void;
  onDeactivateRequest?: () => void;
}) {
  const [name, setName] = useState(agency?.name || "");
  const [acronym, setAcronym] = useState(agency?.acronym || "");
  const [category, setCategory] = useState(agency?.category || "SECURITY");
  const [domains, setDomains] = useState<string[]>(agency?.official_domains || []);
  const [domainInput, setDomainInput] = useState("");
  const [logoUrl, setLogoUrl] = useState(agency?.logo_url || "");
  const [vettedScore, setVettedScore] = useState(agency?.vetted_score ?? 85);
  const [description, setDescription] = useState(agency?.description || "");
  const [isActive, setIsActive] = useState(agency?.is_active ?? true);
  const [saving, setSaving] = useState(false);

  // Tag Input Handlers
  const handleAddDomain = () => {
    const trimmed = domainInput.trim().toLowerCase().replace(/^https?:\/\//, "").replace(/\/.*$/, "");
    if (trimmed && !domains.includes(trimmed)) {
      setDomains([...domains, trimmed]);
      setDomainInput("");
    }
  };

  const handleDomainKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      handleAddDomain();
    }
  };

  const handleRemoveDomain = (index: number) => {
    setDomains(domains.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !acronym.trim()) {
      toast.error("Name and acronym are required.");
      return;
    }

    setSaving(true);
    const payload = {
      name: name.trim(),
      acronym: acronym.trim(),
      category,
      official_domains: domains,
      logo_url: logoUrl.trim(),
      vetted_score: Number(vettedScore),
      description: description.trim(),
      is_active: isActive,
    };

    try {
      if (agency) {
        await adminApi.updateAgency(agency.id, payload);
        toast.success(`Agency '${acronym}' updated successfully.`);
      } else {
        await adminApi.createAgency(payload);
        toast.success(`Agency '${acronym}' created successfully.`);
      }
      onSuccess();
    } catch (err: any) {
      toast.error(err?.message || "Failed to save agency.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AccessibleModal
      isOpen={true}
      onClose={onClose}
      title={agency ? `Edit Agency: ${agency.acronym}` : "Create New Agency"}
      description="Configure official recruitment agency details, whitelisted domains, and monitoring thresholds."
      maxWidth="max-w-xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4 font-sans text-xs pt-1">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="block font-sans text-muted-foreground font-semibold">Agency Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Nigeria Customs Service"
              className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground focus:outline-none focus:border-primary font-sans"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="block font-sans text-muted-foreground font-semibold">Acronym *</label>
            <input
              type="text"
              value={acronym}
              onChange={(e) => setAcronym(e.target.value)}
              placeholder="e.g. NCS"
              className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-mono focus:outline-none focus:border-primary"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="block font-sans text-muted-foreground font-semibold">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-sans focus:outline-none focus:border-primary"
            >
              <option value="SECURITY">Security & Law Enforcement</option>
              <option value="FINANCE">Finance & Revenue</option>
              <option value="UTILITIES">Utilities & Energy</option>
              <option value="HEALTH">Health & Pharma</option>
              <option value="EDUCATION">Education & Research</option>
              <option value="TRANSPORT">Transport & Aviation</option>
              <option value="STATISTICS">Statistics & Data</option>
              <option value="JUDICIARY">Judiciary & Legal</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="block font-sans text-muted-foreground font-semibold">Vetted Score (0–100)</label>
            <input
              type="number"
              min={0}
              max={100}
              value={vettedScore}
              onChange={(e) => setVettedScore(Number(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-border rounded-[6px] text-foreground font-mono focus:outline-none focus:border-primary"
            />
          </div>
        </div>

        {/* Official Domains Multi-Tag Input */}
        <div className="space-y-1.5">
          <label className="block font-sans text-muted-foreground font-semibold">
            Official Whitelisted Domains (Tag Input : Press Enter or Comma):
          </label>
          <div className="p-2.5 bg-background border border-border rounded-[6px] flex flex-wrap gap-2 items-center min-h-12 font-sans">
            {domains.map((domain, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 bg-muted text-primary border border-border font-mono text-[11px] px-2 py-0.5 rounded-[6px]"
              >
                {domain}
                <button
                  type="button"
                  onClick={() => handleRemoveDomain(index)}
                  className="text-muted-foreground hover:text-destructive cursor-pointer"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            <input
              type="text"
              value={domainInput}
              onChange={(e) => setDomainInput(e.target.value)}
              onKeyDown={handleDomainKeyDown}
              onBlur={handleAddDomain}
              placeholder={domains.length === 0 ? "Type domain (e.g. customs.gov.ng) & press Enter..." : "Add another domain..."}
              className="flex-1 min-w-[200px] bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none font-mono text-xs"
            />
          </div>
          <p className="text-[10px] text-muted-foreground font-sans">
            Only links matching these domains will receive the "Official Whitelisted Source" badge.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="pt-3 border-t border-border flex items-center justify-between">
          {agency ? (
            <button
              type="button"
              onClick={onDeactivateRequest}
              className="px-3 py-1.5 rounded-[6px] font-semibold flex items-center gap-1 transition-colors cursor-pointer text-xs font-sans bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              <XCircle className="h-3.5 w-3.5" />
              <span>Deactivate Agency</span>
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2 font-sans">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-[6px] font-semibold cursor-pointer text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 text-white dark:text-[#0c1015] font-semibold rounded-[6px] flex items-center gap-1.5 shadow-sm cursor-pointer text-xs"
            >
              {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>Save Agency</span>
            </button>
          </div>
        </div>
      </form>
    </AccessibleModal>
  );
}
