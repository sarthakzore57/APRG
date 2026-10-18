import { useEffect, useState } from "react";
import { BookOpen, CheckCircle2, Eye, EyeOff, KeyRound, LogIn, Mail, RefreshCw, Sparkles, User, UserPlus, Zap } from "lucide-react";
import { api, checkServerHealth, setSession, warmupBackend } from "../api/client";

export function Auth({ onAuthed }) {
  const [mode, setMode] = useState("login"); // "login" | "register" | "reset"
  const [form, setForm] = useState({ email: "sarthakzore237@gmail.com", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [wakingUp, setWakingUp] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [retryNotice, setRetryNotice] = useState("");
  const [serverStatus, setServerStatus] = useState("checking"); // "checking" | "online" | "waking"
  const [showPassword, setShowPassword] = useState(false);

  // Pre-warm backend and monitor health on mount
  useEffect(() => {
    warmupBackend();
    let isMounted = true;
    let pollTimer;

    async function probeServer() {
      const isOnline = await checkServerHealth(4000);
      if (!isMounted) return;
      if (isOnline) {
        setServerStatus("online");
      } else {
        setServerStatus("waking");
        // Keep checking every 6 seconds until awake
        pollTimer = setTimeout(probeServer, 6000);
      }
    }

    probeServer();

    return () => {
      isMounted = false;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, []);

  // Track elapsed waiting time when waking cold server
  useEffect(() => {
    let interval;
    if (loading) {
      setElapsed(0);
      interval = setInterval(() => {
        setElapsed((prev) => {
          const next = prev + 1;
          if (next >= 2) setWakingUp(true);
          return next;
        });
      }, 1000);
    } else {
      setWakingUp(false);
      setElapsed(0);
      setRetryNotice("");
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loading]);

  async function submit(event) {
    if (event) event.preventDefault();
    const cleanEmail = (form.email || "").trim().toLowerCase();
    const cleanPassword = (form.password || "").trim();

    if (!cleanEmail) {
      setError("Please enter your email address.");
      return;
    }
    if (!cleanPassword) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    setError("");
    setRetryNotice("");

    try {
      let result;
      const options = {
        onRetry: (attempt, max) => {
          setRetryNotice(`Cloud server is spinning up, retrying automatically (attempt ${attempt}/${max})...`);
        },
      };

      if (mode === "login") {
        result = await api.login(cleanEmail, cleanPassword, options);
      } else if (mode === "register") {
        result = await api.register({ ...form, email: cleanEmail, password: cleanPassword }, options);
      } else {
        result = await api.resetPassword({ email: cleanEmail, new_password: cleanPassword }, options);
      }
      setSession(result.access_token, result.user);
      onAuthed();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function fillDemoCredentials() {
    setForm({
      ...form,
      email: "sarthakzore237@gmail.com",
      password: "Sarthak@123",
    });
    setMode("login");
    setError("");
  }

  return (
    <div className="perspective-container flex min-h-[78vh] items-center justify-center p-2 sm:p-4">
      {/* 3D Notebook Container */}
      <div className="relative w-full max-w-lg">
        {/* Layered Paper Sheets Effect Behind Main Book */}
        <div className="absolute inset-0 translate-x-2.5 translate-y-3 rotate-1 rounded-xl bg-[#e8dfcf] shadow-md border border-[#d6cbb6]" />
        <div className="absolute inset-0 -translate-x-1 translate-y-1.5 -rotate-1 rounded-xl bg-[#f0e8da] shadow border border-[#dfd4be]" />

        {/* Realistic Left Spiral Binder Rings */}
        <div className="spiral-spine hidden sm:flex">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="spiral-ring">
              <div className="spiral-hole" />
            </div>
          ))}
        </div>

        {/* Washi Tape Header Decoration */}
        <div className="washi-tape -top-3 left-1/2 -translate-x-1/2" />

        {/* Main Ruled Notebook Page */}
        <form
          onSubmit={submit}
          className="notebook-page card-3d relative z-10 p-6 sm:p-9 pl-8 sm:pl-16 shadow-book-3d"
        >
          {/* Notebook Header Stamp & Subject Line */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-dashed border-[#e2d8c3] pb-4">
            <div>
              <span className="rough-stamp text-xs text-[#1e40af]">DRAFTLY ACADEMIC</span>
              <h2 className="mt-1 text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 font-kalam">
                {mode === "login" ? "Student Login" : mode === "register" ? "Create Account" : "Reset Password"}
              </h2>
            </div>
            <div className="text-right">
              <span className="handwriting text-base sm:text-lg text-slate-500 font-bold block">
                Draftly v2.0
              </span>
              {/* Server Live Health Pill */}
              <div className="mt-1 flex items-center justify-end">
                {serverStatus === "online" ? (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-semibold text-emerald-800 bg-emerald-100/90 px-2 py-0.5 rounded-full border border-emerald-300">
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    Cloud Server Online
                  </span>
                ) : serverStatus === "waking" ? (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-semibold text-amber-900 bg-amber-100/90 px-2 py-0.5 rounded-full border border-amber-300 animate-pulse">
                    <RefreshCw size={11} className="animate-spin text-amber-700" />
                    Server Waking Up (~45s)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-300">
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                    Connecting...
                  </span>
                )}
              </div>
            </div>
          </div>

          <p className="mt-2 text-sm text-slate-600 font-handwriting">
            {mode === "login"
              ? "Welcome to Draftly — sign in to access your college project documentation binder."
              : mode === "register"
              ? "Register a new logbook binder to start generating university-formatted project reports."
              : "Enter your email and new password (min 8 chars) to update credentials and open your workspace."}
          </p>

          {/* Ruled Notebook Form Inputs */}
          <div className="mt-6 space-y-4">
            {mode === "register" && (
              <div>
                <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-slate-700 font-kalam">
                  Full Name / Roll No.
                </label>
                <div className="relative flex items-center">
                  <User className="absolute left-3.5 text-slate-400 pointer-events-none z-10" size={18} />
                  <input
                    className="field font-handwriting"
                    style={{ paddingLeft: "2.75rem" }}
                    placeholder="e.g. Sarthak Zore (Roll 42)"
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    required
                  />
                </div>
              </div>
            )}

            <div>
              <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-slate-700 font-kalam">
                Email Address
              </label>
              <div className="relative flex items-center">
                <Mail className="absolute left-3.5 text-slate-400 pointer-events-none z-10" size={18} />
                <input
                  className="field font-handwriting"
                  style={{ paddingLeft: "2.75rem" }}
                  placeholder="student@college.edu"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 font-kalam">
                  {mode === "reset" ? "New Password (min 8 chars)" : "Password"}
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-mono transition-colors"
                >
                  {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                  <span>{showPassword ? "Hide" : "Show"}</span>
                </button>
              </div>
              <div className="relative flex items-center">
                <KeyRound className="absolute left-3.5 text-slate-400 pointer-events-none z-10" size={18} />
                <input
                  className="field font-handwriting"
                  style={{ paddingLeft: "2.75rem", paddingRight: "2.75rem" }}
                  placeholder="••••••••••••"
                  type={showPassword ? "text" : "password"}
                  minLength={8}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
            </div>

            {/* Quick-Fill Default Student Credentials Helper */}
            {mode === "login" && (
              <div className="pt-1">
                <button
                  type="button"
                  onClick={fillDemoCredentials}
                  className="w-full inline-flex items-center justify-center gap-1.5 text-xs font-bold text-[#1e40af] bg-blue-50/80 hover:bg-blue-100/90 py-1.5 px-3 rounded border border-blue-200 transition-colors shadow-sm font-handwriting text-sm"
                >
                  <Zap size={14} className="text-amber-500 fill-amber-500" />
                  <span>Auto-fill Verified Login (sarthakzore237@gmail.com)</span>
                </button>
              </div>
            )}
          </div>

          {/* Render Free-Tier Server Wakeup Progress Indicator with Live Timer */}
          {wakingUp && (
            <div className="mt-4 p-3 rounded-lg border border-amber-300 bg-amber-50 text-amber-900 text-xs flex items-center gap-2.5 animate-pulse">
              <RefreshCw className="animate-spin text-amber-600 flex-shrink-0" size={16} />
              <div className="flex-1">
                <div className="font-bold">
                  {retryNotice || "Connecting to cloud server..."} {elapsed > 0 && `(${elapsed}s)`}
                </div>
                <div className="text-[11px] text-amber-800 mt-0.5">
                  The free Render backend spins down when idle and takes ~30–60s to wake up. Please keep this tab open!
                </div>
              </div>
            </div>
          )}

          {/* Sticky Note for Errors with Direct Retry Action */}
          {error && (
            <div className="sticky-note mt-4 p-3 rounded text-xs font-bold text-red-900 border-red-300 bg-red-100 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <span>⚠️ {error}</span>
                {(error.toLowerCase().includes("timed out") ||
                  error.toLowerCase().includes("spinning up") ||
                  error.toLowerCase().includes("connect")) && (
                  <button
                    type="button"
                    onClick={() => submit()}
                    className="flex-shrink-0 bg-red-200 hover:bg-red-300 text-red-900 px-2 py-1 rounded text-[11px] font-bold border border-red-400 flex items-center gap-1"
                  >
                    <RefreshCw size={12} /> Retry Now
                  </button>
                )}
              </div>
              {error.toLowerCase().includes("invalid email or password") && (
                <div className="font-normal text-slate-700 text-[11px] border-t border-red-200 pt-1.5">
                  Tip: If using the default student account, click <strong>"Auto-fill Verified Login"</strong> above or use <strong>"Forgot password or need to reset?"</strong> below.
                </div>
              )}
            </div>
          )}

          {/* 3D Tactile Submit Button */}
          <button
            type="submit"
            className="btn-3d-primary mt-6 w-full py-2.5 text-base font-bold tracking-wide"
            disabled={loading}
          >
            {mode === "login" ? <LogIn size={18} /> : mode === "register" ? <UserPlus size={18} /> : <Sparkles size={18} />}
            <span>
              {loading
                ? elapsed > 0
                  ? `Opening Book... (${elapsed}s)`
                  : "Opening Book..."
                : mode === "login"
                ? "Open Draftly Workspace"
                : mode === "register"
                ? "Create Draftly Account"
                : "Reset Password & Open Workspace"}
            </span>
          </button>

          {/* Mode Switches */}
          <div className="mt-5 space-y-2 text-center">
            {mode === "login" ? (
              <>
                <div>
                  <button
                    type="button"
                    className="handwriting text-base sm:text-lg text-ocean hover:text-ocean/80 underline decoration-wavy underline-offset-4 font-bold transition-all"
                    onClick={() => {
                      setError("");
                      setMode("register");
                    }}
                  >
                    ✏️ Need a new logbook? Click here to register
                  </button>
                </div>
                <div>
                  <button
                    type="button"
                    className="text-xs text-slate-500 hover:text-ocean underline transition-colors"
                    onClick={() => {
                      setError("");
                      setMode("reset");
                    }}
                  >
                    Forgot password or need to reset? Click here
                  </button>
                </div>
              </>
            ) : mode === "register" ? (
              <div>
                <button
                  type="button"
                  className="handwriting text-base sm:text-lg text-ocean hover:text-ocean/80 underline decoration-wavy underline-offset-4 font-bold transition-all"
                  onClick={() => {
                    setError("");
                    setMode("login");
                  }}
                >
                  📖 Already registered? Click here to login
                </button>
              </div>
            ) : (
              <div>
                <button
                  type="button"
                  className="handwriting text-base sm:text-lg text-ocean hover:text-ocean/80 underline decoration-wavy underline-offset-4 font-bold transition-all"
                  onClick={() => {
                    setError("");
                    setMode("login");
                  }}
                >
                  🔙 Back to Login
                </button>
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
