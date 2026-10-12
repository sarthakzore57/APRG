import { BookOpen, LogOut, ShieldCheck } from "lucide-react";
import { clearSession, getUser } from "../api/client";

export function Layout({ children, onLogout }) {
  const user = getUser();
  return (
    <div className="min-h-screen flex flex-col font-handwriting">
      {/* 3D Realistic Notebook Top Header */}
      <header className="sticky top-0 z-50 border-b border-[#d8cca8] bg-[#fbf8ef]/95 backdrop-blur-md shadow-md">
        {/* Top Perforated Spiral Strip */}
        <div className="h-2 w-full bg-gradient-to-r from-[#1e40af] via-[#0f766e] to-[#b45309] opacity-80" />
        
        <div className="mx-auto flex max-w-7xl items-center justify-between px-3 py-2.5 sm:px-6">
          {/* Logo & Subject Header */}
          <div className="flex items-center gap-3">
            <div className="group relative flex h-11 w-11 items-center justify-center rounded-lg bg-gradient-to-br from-[#1e40af] to-[#0f2858] text-white shadow-md transition-transform duration-300 hover:rotate-3 hover:scale-105">
              <BookOpen size={24} className="transition-transform group-hover:scale-110" />
              <div className="absolute -bottom-2 right-2 h-3.5 w-2 rounded-b bg-amber-500 shadow-sm" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#1e293b] flex items-center gap-2 font-kalam">
                  Draftly
                </h1>
                <span className="hidden sm:inline-block rounded-md border border-[#1e40af]/40 bg-[#1e40af]/10 px-2 py-0.5 text-xs font-bold text-[#1e40af] rough-stamp">
                  PROJECT STUDIO
                </span>
              </div>
              <p className="text-sm text-slate-500 flex items-center gap-1.5 font-handwriting">
                <span>Smart Academic Report & Thesis Generator</span>
                <span className="text-slate-300">•</span>
                <span className="text-[#1e40af] font-bold">College Lab Edition</span>
              </p>
            </div>
          </div>

          {/* Student Status & Tactile Logout Button */}
          {user && (
            <div className="flex items-center gap-3">
              {user.role === "admin" && (
                <span className="inline-flex items-center gap-1 rounded border border-teal-300 bg-teal-50 px-2.5 py-0.5 text-xs font-bold text-teal-800">
                  <ShieldCheck size={14} className="text-teal-700" /> Faculty In-Charge
                </span>
              )}
              
              <div className="hidden md:flex items-center gap-2 rounded-md border border-[#d8cca8] bg-[#f8f4ea] px-3 py-1 shadow-sm text-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
                <span className="font-bold text-[#1e3a8a]">Roll: {user.full_name}</span>
              </div>

              <button
                className="btn-3d-secondary text-sm py-1 px-3"
                onClick={() => {
                  clearSession();
                  onLogout();
                }}
                title="Close and log out of notebook"
              >
                <LogOut size={15} />
                <span className="hidden sm:inline">Close Book</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Study Desk Canvas */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-2 py-5 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* Realistic Notebook Bottom Margin / Footer */}
      <footer className="mt-auto border-t border-[#d8cca8] bg-[#f5efe0] py-3 text-center text-sm text-slate-600">
        <div className="mx-auto max-w-7xl px-4 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="rough-stamp text-[#1e40af]">EXPT NO: FINAL-01</span>
            <span className="text-slate-400">|</span>
            <span className="font-handwriting text-slate-600 font-bold">Evaluated & Verified for University Submission</span>
          </div>
          <p className="font-handwriting text-base text-slate-600 font-bold">
            ✍️ Handwritten Notes & Auto-Formatted IEEE / University DOCX
          </p>
        </div>
      </footer>
    </div>
  );
}
