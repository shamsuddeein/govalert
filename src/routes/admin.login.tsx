import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Lock, User, AlertTriangle, Loader2 } from "lucide-react";
import { adminApi } from "../lib/adminApi";
import { Logo, ThemeToggle } from "../components/layout";

export const Route = createFileRoute("/admin/login")({
  component: AdminLoginComponent,
});

function AdminLoginComponent() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Please enter both username and password.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await adminApi.login(username.trim(), password);
      navigate({ to: "/admin/alerts" });
    } catch (err: any) {
      setError(err?.message || "Invalid username or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col antialiased font-sans">
      {/* Top Brand Border Indicator (Nigerian Flag Green) */}
      <div className="h-[3px] w-full bg-[#0a5c38] dark:bg-[#3fb68e]" />

      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-card border border-border rounded-[8px] p-8 shadow-sm space-y-6 relative">
          <div className="absolute top-4 right-4">
            <ThemeToggle />
          </div>

          {/* Header with Official Logo */}
          <div className="text-center space-y-3 pt-2">
            <div className="flex justify-center">
              <Logo />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground font-sans">
                Admin Console
              </h1>
              <p className="text-xs text-muted-foreground mt-1 font-sans">
                Authenticated Operations Portal. Staff Credentials Required.
              </p>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="flex items-start gap-3 p-3.5 rounded-[6px] bg-destructive/10 border border-destructive/30 text-destructive text-xs animate-fadeIn font-sans">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1">{error}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4 font-sans">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-foreground uppercase tracking-wider font-sans">
                Username or Email
              </label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin@recruitmentalert.com.ng or username"
                  className="w-full pl-9 pr-4 py-2.5 bg-background border border-border rounded-[6px] text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary font-sans transition-colors"
                  disabled={loading}
                  autoFocus
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-foreground uppercase tracking-wider font-sans">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-4 py-2.5 bg-background border border-border rounded-[6px] text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary transition-colors font-sans"
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 bg-[#0a5c38] hover:bg-[#0f7a4a] dark:bg-[#3fb68e] dark:hover:bg-[#3fb68e]/90 text-white dark:text-[#0c1015] font-semibold text-sm rounded-[6px] transition-all flex items-center justify-center gap-2 shadow-sm cursor-pointer font-sans"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In to Admin Dashboard</span>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
