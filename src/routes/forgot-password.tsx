import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Nav, Footer } from "../components/layout";
import { Mail, ArrowRight, ShieldCheck, CheckCircle2, ArrowLeft } from "lucide-react";
import { BackButton } from "../components/BackButton";
import { toast } from "sonner";

export const Route = createFileRoute("/forgot-password")({
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
      toast.success("Password reset instructions sent!");
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between selection:bg-secondary/25">
      <Nav />
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-md rounded border border-border bg-card p-8 shadow-sm relative">
          <div className="mb-4">
            <BackButton to="/sign-in" label="Back to Sign In" />
          </div>
          <div className="text-center mb-8">
            <div className="mx-auto grid size-10 place-items-center rounded border border-border bg-muted text-primary">
              <ShieldCheck className="size-5" />
            </div>
            <h1 className="mt-4 text-xl font-bold tracking-tight text-primary">Reset password</h1>
            <p className="mt-1.5 text-xs text-muted-foreground">
              {submitted
                ? "Check your email for reset instructions."
                : "Enter your email to receive recovery instructions."}
            </p>
          </div>

          {!submitted ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <input
                    type="email"
                    required
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded border border-border bg-background py-2 pl-10 pr-4 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="mt-6 w-full inline-flex items-center justify-center gap-2 rounded bg-primary py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/95 disabled:opacity-50 transition-colors cursor-pointer"
              >
                {loading ? "Sending..." : "Send Reset Link"}
                {!loading && <ArrowRight className="size-4" />}
              </button>
            </form>
          ) : (
            <div className="text-center space-y-4">
              <p className="text-xs text-muted-foreground leading-relaxed">
                We've sent a password reset link to{" "}
                <strong className="text-foreground">{email}</strong>. Please check your inbox (and
                spam folder) and follow the instructions to secure your account.
              </p>
              <button
                onClick={() => setSubmitted(false)}
                className="text-xs font-semibold text-primary hover:underline cursor-pointer"
              >
                Try a different email
              </button>
            </div>
          )}

          <div className="mt-8 border-t border-border pt-6 text-center text-xs">
            <Link
              to="/sign-in"
              className="inline-flex items-center gap-1.5 font-semibold text-primary hover:underline"
            >
              <ArrowLeft className="size-3.5" /> Back to Sign In
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
