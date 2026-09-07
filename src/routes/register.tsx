import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Nav, Footer } from "../components/layout";
import { User, Mail, Lock, ArrowRight, Eye, EyeOff, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { cn } from "../lib/utils";
import { initializeGoogleAuth, triggerGoogleSignIn, GoogleAuthButton } from "../lib/googleAuth";
import { SeoHead } from "../components/SeoHead";
import { BackButton } from "../components/BackButton";

export const Route = createFileRoute("/register")({
  component: RegisterPage,
});

function RegisterPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [agree, setAgree] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const handleGoogleCredential = async (idToken: string) => {
    setGoogleLoading(true);
    const res = await api.googleAuth(idToken);
    setGoogleLoading(false);
    if (res.tokens) {
      toast.success("Successfully registered with Google!");
      navigate({ to: "/dashboard" });
    } else {
      toast.error(res.error || "Google sign-up failed. Please try again.");
    }
  };

  useEffect(() => {
    initializeGoogleAuth(handleGoogleCredential);
  }, []);

  const handleGoogleSignUpClick = () => {
    setGoogleLoading(true);
    triggerGoogleSignIn(handleGoogleCredential);
    setTimeout(() => setGoogleLoading(false), 8000);
  };

  const hasMinLength = password.length >= 8;
  const hasNumber = /\d/.test(password);
  const passwordsMatch = password.length > 0 && confirmPassword.length > 0 && password === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasMinLength || !hasNumber) {
      toast.error("Password does not meet requirements.");
      return;
    }
    if (password !== confirmPassword) {
      toast.error("Passwords do not match!");
      return;
    }
    if (!agree) {
      toast.error("You must agree to the Terms of Service & Privacy Policy.");
      return;
    }
    setLoading(true);

    const res = await api.register(name, email, password);
    setLoading(false);

    if (res.tokens) {
      toast.success("Account created successfully!");
      navigate({ to: "/dashboard" });
    } else {
      toast.error(res.error || "Failed to create account.");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between selection:bg-secondary/25">
      <SeoHead
        title="Create an Account — RecruitmentAlert"
        description="Create a free RecruitmentAlert account to receive real-time notifications for verified Nigerian federal government recruitment openings."
        canonicalUrl="/register"
      />
      <Nav />
      <main id="main-content" tabIndex={-1} className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-6 sm:py-12 md:py-16 outline-none">
        <div className="w-full max-w-md rounded-[8px] border border-border bg-card p-5 sm:p-8 shadow-sm relative">
          <div className="mb-4">
            <BackButton to="/" label="Back to Home" />
          </div>
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-2 mb-3">
              <span className="text-2xl font-extrabold tracking-tight text-[#0a5c38] dark:text-[#3fb68e]">
                RecruitmentAlert
              </span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-primary">Create an account</h1>
            <p className="mt-1.5 text-xs text-muted-foreground">
              Monitor portal openings and receive instant recruitment updates.
            </p>
          </div>

          {/* Prominent Official Google Auth Button */}
          <GoogleAuthButton onCredential={handleGoogleCredential} text="signup_with" disabled={googleLoading || loading} />

          {/* Divider */}
          <div className="relative w-full flex items-center justify-center mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <span className="relative bg-card px-3 text-[10px] text-muted-foreground uppercase font-mono tracking-wider">
              or register with email
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="register-name" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" aria-hidden="true" />
                <input
                  id="register-name"
                  type="text"
                  required
                  placeholder="Shamsuddeein Alao"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded border border-border bg-background py-2 pl-10 pr-4 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="register-email" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" aria-hidden="true" />
                <input
                  id="register-email"
                  type="email"
                  required
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded border border-border bg-background py-2 pl-10 pr-4 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="register-password" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" aria-hidden="true" />
                <input
                  id="register-password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded border border-border bg-background py-2 pl-10 pr-10 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>

              {/* Live Password Requirement Checklist */}
              <div aria-live="polite" className="mt-1 rounded-[6px] border border-border/60 bg-muted/20 p-2.5 space-y-1.5 font-sans">
                <div className="flex items-center gap-2">
                  <CheckCircle2
                    className={cn(
                      "size-3.5 shrink-0 transition-colors",
                      hasMinLength ? "text-[#166534]" : "text-[#9CA3AF]"
                    )}
                    aria-hidden="true"
                  />
                  <span className={cn("text-[11px] font-medium transition-colors", hasMinLength ? "text-[#166534] dark:text-[#3fb68e]" : "text-muted-foreground")}>
                    Minimum 8 characters {hasMinLength ? "✓" : ""}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <CheckCircle2
                    className={cn(
                      "size-3.5 shrink-0 transition-colors",
                      hasNumber ? "text-[#166534]" : "text-[#9CA3AF]"
                    )}
                    aria-hidden="true"
                  />
                  <span className={cn("text-[11px] font-medium transition-colors", hasNumber ? "text-[#166534] dark:text-[#3fb68e]" : "text-muted-foreground")}>
                    At least one number {hasNumber ? "✓" : ""}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <CheckCircle2
                    className={cn(
                      "size-3.5 shrink-0 transition-colors",
                      passwordsMatch ? "text-[#166534]" : "text-[#9CA3AF]"
                    )}
                    aria-hidden="true"
                  />
                  <span className={cn("text-[11px] font-medium transition-colors", passwordsMatch ? "text-[#166534] dark:text-[#3fb68e]" : "text-muted-foreground")}>
                    Passwords match {passwordsMatch ? "✓" : ""}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="register-confirm-password" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" aria-hidden="true" />
                <input
                  id="register-confirm-password"
                  type="password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full rounded border border-border bg-background py-2 pl-10 pr-4 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary"
                />
              </div>
            </div>

            <div className="flex items-start">
              <input
                id="agree"
                type="checkbox"
                required
                checked={agree}
                onChange={(e) => setAgree(e.target.checked)}
                className="mt-1 size-4 rounded border-border text-primary focus:ring-primary"
              />
              <label
                htmlFor="agree"
                className="ml-2 text-xs text-muted-foreground leading-relaxed select-none cursor-pointer"
              >
                I agree to the{" "}
                <Link to="/terms" className="text-primary hover:underline font-medium">
                  Terms of Service
                </Link>{" "}
                and{" "}
                <Link to="/privacy" className="text-primary hover:underline font-medium">
                  Privacy Policy
                </Link>
                .
              </label>
            </div>

            <button
              type="submit"
              disabled={loading || googleLoading}
              className="mt-6 w-full inline-flex items-center justify-center gap-2 rounded bg-primary py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/95 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loading ? "Creating..." : "Create Account"}
              {!loading && <ArrowRight className="size-4" aria-hidden="true" />}
            </button>
          </form>

          <div className="mt-8 border-t border-border pt-6 text-center text-xs text-muted-foreground">
            Already have an account?{" "}
            <Link to="/sign-in" className="font-semibold text-primary hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
