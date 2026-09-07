import { BookOpen, LogOut, ShieldCheck } from "lucide-react";
import { clearSession, getUser } from "../api/client";

export function Layout({ children, onLogout }) {
  const user = getUser();
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ocean text-white">
              <BookOpen size={22} />
            </div>
            <div>
              <h1 className="text-lg font-semibold">AI Project Report Generator</h1>
              <p className="text-xs text-slate-500">College project documentation workspace</p>
            </div>
          </div>
          {user && (
            <div className="flex items-center gap-3 text-sm">
              {user.role === "admin" && <span className="inline-flex items-center gap-1 text-mint"><ShieldCheck size={16} /> Admin</span>}
              <span className="hidden text-slate-600 sm:inline">{user.full_name}</span>
              <button
                className="btn-secondary"
                onClick={() => {
                  clearSession();
                  onLogout();
                }}
              >
                <LogOut size={16} /> Logout
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
