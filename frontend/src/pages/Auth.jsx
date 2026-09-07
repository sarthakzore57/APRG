import { useState } from "react";
import { LogIn, UserPlus } from "lucide-react";
import { api, setSession } from "../api/client";

export function Auth({ onAuthed }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = mode === "login" ? await api.login(form.email, form.password) : await api.register(form);
      setSession(result.access_token, result.user);
      onAuthed();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-[75vh] place-items-center">
      <form onSubmit={submit} className="panel w-full max-w-md p-6">
        <h2 className="text-2xl font-semibold">{mode === "login" ? "Login" : "Create Account"}</h2>
        <p className="mt-1 text-sm text-slate-600">Generate structured, editable project reports from verified project data.</p>
        <div className="mt-5 space-y-3">
          {mode === "register" && <input className="field" placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />}
          <input className="field" placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="field" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>
        {error && <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <button className="btn-primary mt-5 w-full" disabled={loading}>{mode === "login" ? <LogIn size={16} /> : <UserPlus size={16} />} {loading ? "Please wait" : mode === "login" ? "Login" : "Register"}</button>
        <button type="button" className="mt-3 w-full text-sm text-ocean" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need an account? Register" : "Already registered? Login"}
        </button>
      </form>
    </div>
  );
}
