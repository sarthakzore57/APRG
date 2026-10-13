import { useEffect, useState } from "react";
import { BookOpen, KeyRound, LogIn, Mail, RefreshCw, Sparkles, User, UserPlus } from "lucide-react";
import { api, setSession } from "../api/client";

export function Auth({ onAuthed }) {
  const [mode, setMode] = useState("login"); // "login" | "register" | "reset"
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [wakingUp, setWakingUp] = useState(false);

  useEffect(() => {
    let timer;
    if (loading) {
      timer = setTimeout(() => {
        setWakingUp(true);
      }, 2500);
    } else {
      setWakingUp(false);
    }
    return () => clearTimeout(timer);
  }, [loading]);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      let result;
      if (mode === "login") {
        result = await api.login(form.email, form.password);
      } else if (mode === "register") {
        result = await api.register(form);
      } else {
        result = await api.resetPassword({ email: form.email, new_password: form.password });
      }
      setSession(result.access_token, result.user);
      onAuthed();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
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
              <span className="handwriting text-base sm:text-lg text-slate-500 font-bold">
                Draftly v2.0
              </span>
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
              <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-slate-700 font-kalam">
                {mode === "reset" ? "New Password (min 8 chars)" : "Password"}
              </label>
              <div className="relative flex items-center">
                <KeyRound className="absolute left-3.5 text-slate-400 pointer-events-none z-10" size={18} />
                <input
                  className="field font-handwriting"
                  style={{ paddingLeft: "2.75rem" }}
                  placeholder="••••••••••••"
                  type="password"
                  minLength={8}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
            </div>
          </div>

          {/* Render Free-Tier Server Wakeup Progress Indicator */}
          {wakingUp && (
            <div className="mt-4 p-3 rounded-lg border border-amber-300 bg-amber-50 text-amber-900 text-xs flex items-center gap-2.5 animate-pulse">
              <RefreshCw className="animate-spin text-amber-600 flex-shrink-0" size={16} />
              <span>
                <strong>Connecting to cloud server...</strong> The free Render backend spins down when idle and takes ~30–45s to wake up. Please wait!
              </span>
            </div>
          )}

          {/* Sticky Note for Errors or Tips */}
          {error && (
            <div className="sticky-note mt-4 p-3 rounded text-xs font-bold text-red-900 border-red-300 bg-red-100">
              <span>⚠️ {error}</span>
              {error.toLowerCase().includes("invalid email or password") && (
                <div className="mt-1.5 font-normal text-slate-700">
                  Tip: If you haven&apos;t registered on the live database yet, click below to register or reset your password.
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
                ? "Opening Book..."
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
