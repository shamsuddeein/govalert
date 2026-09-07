import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { initializeGoogleAuth, triggerGoogleSignIn, GoogleAuthButton } from "../lib/googleAuth";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/sign-in")({
  component: SignInPage,
});

function SignInPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const handleGoogleCredential = async (idToken: string) => {
    setGoogleLoading(true);
    setAuthError(null);
    const res = await api.googleAuth(idToken);
    setGoogleLoading(false);
    if (res.tokens) {
      toast.success("Successfully signed in with Google!");
      navigate({ to: "/dashboard" });
    } else {
      setAuthError(res.error || "Google authentication failed. Please try again.");
    }
  };

  useEffect(() => {
    initializeGoogleAuth(handleGoogleCredential);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAuthError(null);

    const res = await api.login(email, password);
    setLoading(false);

    if (res.tokens) {
      toast.success("Successfully signed in!");
      navigate({ to: "/dashboard" });
    } else {
      setAuthError(res.error || "Invalid email or password. Please try again.");
    }
  };

  const handleGoogleSignInClick = () => {
    setGoogleLoading(true);
    setAuthError(null);
    triggerGoogleSignIn(handleGoogleCredential);
    setTimeout(() => setGoogleLoading(false), 8000);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between selection:bg-secondary/25 font-sans">
      <SeoHead
        title="Sign In — RecruitmentAlert"
        description="Sign in to your RecruitmentAlert account to manage saved job alerts and portal monitoring preferences."
        canonicalUrl="/sign-in"
      />
      <Nav />
      <main className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-6 sm:py-12 md:py-16">
        <div className="w-full max-w-md rounded-[8px] border border-border bg-card p-5 sm:p-8 shadow-sm relative flex flex-col items-center">
          <div className="self-start mb-4">
            <BackButton to="/" label="Back to Home" />
          </div>
          <div className="flex items-center gap-2 mb-6 focus:outline-none select-none">
            <span className="text-xl font-extrabold tracking-tight text-[#0a5c38] dark:text-[#3fb68e]">
              RecruitmentAlert
            </span>
          </div>

          <div className="text-center w-full mb-6">
            <h1 className="text-xl font-bold tracking-tight text-primary">Sign in to RecruitmentAlert</h1>
            <p className="mt-1.5 text-xs text-muted-foreground">
              Save jobs and receive personalised alerts.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="w-full space-y-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Email</label>
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded border border-border bg-background py-2 px-3 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary transition-all"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Password</label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-[#0a5c38] dark:text-[#3fb68e] hover:underline font-medium"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded border border-border bg-background py-2 pl-3 pr-10 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer focus:outline-none"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || googleLoading}
              className="w-full h-10 inline-flex items-center justify-center rounded bg-[#0a5c38] dark:bg-[#3fb68e] text-xs font-bold text-white hover:opacity-90 disabled:opacity-50 transition-all cursor-pointer"
            >
              {loading ? "Verifying..." : "Sign in"}
            </button>

            {authError && (
              <div className="rounded border border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-900 px-3 py-2 text-xs text-red-700 dark:text-red-400 text-center">
                {authError}
              </div>
            )}
          </form>

          {/* Divider */}
          <div className="relative w-full flex items-center justify-center my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <span className="relative bg-card px-3 text-[10px] text-muted-foreground uppercase font-mono tracking-wider">
              or
            </span>
          </div>

          {/* Continue with Google (Official GIS Button) */}
          <GoogleAuthButton onCredential={handleGoogleCredential} text="signin_with" disabled={googleLoading || loading} />

          <div className="mt-8 text-center text-[13px] text-muted-foreground">
            No account?{" "}
            <Link to="/register" className="font-semibold text-[#0a5c38] dark:text-[#3fb68e] hover:underline">
              Create one
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
