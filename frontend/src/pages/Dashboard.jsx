import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Award,
  BookMarked,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  FileCode,
  FileText,
  FileUp,
  FolderGit2,
  GraduationCap,
  Image as ImageIcon,
  Layers,
  Paperclip,
  PenTool,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Save,
  ShieldCheck,
  Sparkles,
  Wand2,
} from "lucide-react";
import { api, getUser } from "../api/client";

const FALLBACK_TEMPLATES = [
  {
    id: "btech_standard",
    name: "B.Tech / B.E. Major Project",
    badge: "12 Chapters",
    description: "Standard engineering format with system analysis, design, testing & results.",
    recommended_for: "CSE, IT, ECE, Mechanical, Civil",
    chapters: [
      "Introduction",
      "Literature Survey",
      "Objectives",
      "Requirements",
      "System Analysis",
      "System Design",
      "Implementation",
      "Testing",
      "Results",
      "Conclusion",
      "Future Scope",
      "References",
    ],
  },
  {
    id: "mca_msc",
    name: "MCA / M.Sc Computer Science",
    badge: "9 Chapters",
    description: "Software engineering oriented format featuring formal SRS, database schemas & QA test matrices.",
    recommended_for: "MCA, M.Sc IT, Software Engineering",
    chapters: [
      "Introduction and Problem Definition",
      "Literature Review and Theoretical Background",
      "Software Requirements Specification (SRS)",
      "System Architecture and Database Design",
      "Module Implementation and Workflow",
      "Software Testing and Quality Assurance",
      "Results and Performance Analysis",
      "Conclusion and Future Enhancements",
      "References",
    ],
  },
  {
    id: "ai_ml",
    name: "AI / ML & Data Science",
    badge: "9 Chapters",
    description: "Tailored for AI/ML models covering datasets, training workflows, loss/accuracy metrics & deployment.",
    recommended_for: "Machine Learning, Deep Learning, NLP, Computer Vision",
    chapters: [
      "Introduction and Problem Motivation",
      "Literature Survey and Related Work",
      "Problem Formulation and Dataset Analysis",
      "Proposed Methodology and Model Architecture",
      "Model Training and Implementation",
      "Experimental Evaluation and Metrics",
      "System Workflow and Deployment",
      "Conclusion and Limitations",
      "References",
    ],
  },
  {
    id: "mini_project",
    name: "Mini Project / Fast Track",
    badge: "6 Chapters",
    description: "Concise 6-chapter structure ideal for semester mini projects, agile labs, or quick demos.",
    recommended_for: "Mini Projects, Term Submissions, Hackathons",
    chapters: [
      "Introduction and Objectives",
      "Requirement Analysis",
      "System Architecture and Design",
      "Implementation and Code Walkthrough",
      "Testing and Output Verification",
      "Conclusion and References",
    ],
  },
  {
    id: "ieee_research",
    name: "IEEE / Research Thesis",
    badge: "8 Chapters",
    description: "Formal academic research outline focusing on mathematical modeling and comparative evaluation.",
    recommended_for: "M.Tech / MS Thesis, Research Projects, Conference Papers",
    chapters: [
      "Introduction",
      "Related Work and Background",
      "Mathematical and Architectural Formulation",
      "Proposed Methodology and Algorithm",
      "Implementation Details",
      "Experimental Results and Comparative Analysis",
      "Discussion and Conclusion",
      "References",
    ],
  },
];

const emptyProject = {
  title: "",
  student_details: "",
  college: "",
  branch: "",
  guide: "",
  academic_year: "",
  abstract: "",
  description: "",
  technologies: "",
  custom_chapters: null,
};

export function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [project, setProject] = useState(emptyProject);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [job, setJob] = useState(null);
  const [activePageIndex, setActivePageIndex] = useState(0); // 0: Specs, 1: Materials, 2: Execution & Grade, 3: Manuscript
  const [flipDirection, setFlipDirection] = useState(null); // 'forward' | 'backward'
  const user = getUser();

  const selected = useMemo(() => projects.find((item) => item.id === selectedId), [projects, selectedId]);

  const pageTabs = [
    { id: 0, title: "1. Project Specs", subtitle: "Form & Outline" },
    { id: 1, title: "2. Materials & Exhibits", subtitle: "Code & Uploads" },
    { id: 2, title: "3. Execution & Grade", subtitle: "Workflow & Audit" },
    { id: 3, title: "4. Thesis Manuscript", subtitle: "Editor & Word DOCX" },
  ];

  useEffect(() => {
    loadProjects().catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (selected) {
      setProject(selected);
    }
  }, [selected]);

  useEffect(() => {
    if (!job || ["completed", "failed"].includes(job.status)) return;
    const timer = setInterval(async () => {
      try {
        const next = await api.job(job.project_id, job.id);
        setJob(next);
        if (next.status === "completed") {
          const refreshed = await api.project(job.project_id);
          setProject(refreshed);
          setProjects((items) => items.map((item) => (item.id === refreshed.id ? refreshed : item)));
          // Automatically flip to manuscript editor on completion!
          goToPage(3);
        }
      } catch (err) {
        setError(err.message);
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [job]);

  function goToPage(index) {
    if (index === activePageIndex) return;
    setFlipDirection(index > activePageIndex ? "forward" : "backward");
    setTimeout(() => {
      setActivePageIndex(index);
    }, 150);
    setTimeout(() => {
      setFlipDirection(null);
    }, 600);
  }

  async function loadProjects() {
    const items = await api.projects();
    setProjects(items);
    if (items[0]) setSelectedId(items[0].id);
  }

  async function saveProject(event) {
    event.preventDefault();
    setError("");
    try {
      const payload = { ...project, custom_chapters: parseChapters(project.custom_chapters) };
      const saved = project.id ? await api.updateProject(project.id, payload) : await api.createProject(payload);
      setProject(saved);
      setSelectedId(saved.id);
      await loadProjects();
      setMessage("✓ Written & Saved in Logbook!");
    } catch (err) {
      setError(err.message);
    }
  }

  function parseChapters(value) {
    if (!value || Array.isArray(value)) return value || null;
    return value.split("\n").map((line) => line.trim()).filter(Boolean);
  }

  async function upload(event, kind) {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    for (const file of files) {
      const form = new FormData();
      form.append("kind", kind);
      form.append("file", file);
      await api.upload(project.id, form);
    }
    setMessage(`✓ Attached ${files.length} file(s) to experiment page`);
  }

  async function generate() {
    setError("");
    try {
      const created = await api.generate(project.id);
      setJob(created);
      goToPage(2); // flip to execution page
    } catch (err) {
      setError(err.message);
    }
  }

  async function editChapter(title, content) {
    const updated = await api.editChapter(project.id, { chapter: title, content });
    setProject(updated);
    setMessage(`✓ Ink updated for "${title}"`);
  }

  async function regenerate(title, mode) {
    setMessage(`Regenerating "${title}" (${mode})...`);
    const updated = await api.regenerateChapter(project.id, { chapter: title, mode });
    setProject(updated);
    setMessage(`✓ Rewritten "${title}"`);
  }

  async function downloadReport(fileId) {
    setError("");
    try {
      await api.downloadReport(project.id, fileId, `${project.title || "academic_report"}.docx`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[290px_1fr]">
      {/* Sidebar: Project Index & Notebook Tabs */}
      <aside className="space-y-4">
        {/* New Project Tactile Button */}
        <button
          className="btn-3d-primary w-full py-2.5 text-lg"
          onClick={() => {
            setProject(emptyProject);
            setSelectedId(null);
            setMessage("Opened a fresh blank ruled sheet!");
            goToPage(0);
          }}
        >
          <Plus size={20} />
          <span>New Project Sheet</span>
        </button>

        {/* Notebook Index Tabs (Left Spine) */}
        <div className="realistic-notebook p-3 relative shadow-book-3d">
          <div className="flex items-center justify-between border-b border-[#ded2bd] pb-2 px-1">
            <span className="rough-stamp text-xs text-[#1e40af]">LOGBOOK INDEX</span>
            <span className="font-handwriting text-base font-bold text-slate-500">
              {projects.length} Entries
            </span>
          </div>

          <div className="mt-2 space-y-1.5 max-h-[58vh] overflow-y-auto pr-1">
            {projects.map((item, idx) => {
              const isSelected = item.id === selectedId;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setSelectedId(item.id);
                    setFlipDirection("forward");
                    setTimeout(() => setFlipDirection(null), 500);
                  }}
                  className={`group relative block w-full rounded-md border p-2.5 text-left transition-all ${
                    isSelected
                      ? "border-[#1e40af] bg-white shadow-md translate-x-1 ring-1 ring-[#1e40af]/30"
                      : "border-transparent bg-transparent hover:border-[#ded2bd] hover:bg-white/60"
                  }`}
                >
                  {/* Left Bookmark Pill for Active Tab */}
                  {isSelected && (
                    <span className="absolute -left-1.5 top-2.5 h-6 w-1.5 rounded-full bg-[#1e40af]" />
                  )}
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-400">
                      EXPT #{String(idx + 1).padStart(2, "0")}
                    </span>
                    <span className="font-mono text-[11px] text-slate-500">
                      {item.academic_year || "2025-26"}
                    </span>
                  </div>
                  <h4 className={`text-base font-bold truncate mt-0.5 ${isSelected ? "text-[#1e40af]" : "text-slate-800"}`}>
                    {item.title || "Untitled Project"}
                  </h4>
                  <p className="text-xs text-slate-500 truncate font-handwriting">
                    {item.branch || "Branch not specified"}
                  </p>
                </button>
              );
            })}

            {!projects.length && (
              <div className="p-4 text-center">
                <p className="font-handwriting text-lg text-slate-500">No project sheets yet.</p>
                <p className="text-xs text-slate-400 mt-1">Click "New Project Sheet" above.</p>
              </div>
            )}
          </div>
        </div>

        {/* Admin Knowledge Base Binder */}
        {user?.role === "admin" && <AdminPanel />}
      </aside>

      {/* Main 3D Book Stage (With Realistic Ruled Sheet & Page Flip Animation) */}
      <div className="book-stage relative flex flex-col">
        {/* Top Notebook Divider Tabs (Page Flipping Buttons) */}
        <div className="flex flex-wrap items-end gap-1.5 pl-6 sm:pl-16 z-20">
          {pageTabs.map((tab) => {
            const isActive = activePageIndex === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => goToPage(tab.id)}
                className={`notebook-tab-btn ${isActive ? "active" : ""}`}
              >
                <span className="block text-sm sm:text-base leading-tight">{tab.title}</span>
                <span className="hidden sm:block text-[11px] opacity-75 font-normal">{tab.subtitle}</span>
              </button>
            );
          })}
        </div>

        {/* The Realistic Notebook Page Sheet with Flip Animation */}
        <div
          className={`page-flip-container realistic-notebook relative p-5 sm:p-9 pl-10 sm:pl-20 shadow-book-3d min-h-[75vh] flex flex-col justify-between ${
            flipDirection === "forward"
              ? "page-flip-forward"
              : flipDirection === "backward"
              ? "page-flip-backward"
              : ""
          }`}
        >
          {/* Dual Red Left Margin Line */}
          <div className="notebook-margin-line" />

          {/* Realistic Left Metallic Spiral Wire Rings */}
          <div className="spiral-coil-strip hidden sm:flex">
            {Array.from({ length: 18 }).map((_, i) => (
              <div key={i} className="spiral-wire">
                <div className="spiral-hole-shadow" />
              </div>
            ))}
          </div>

          {/* Top Washi Tape Sticker */}
          <div className="washi-tape -top-2.5 left-16 sm:left-28" />

          {/* Notebook Page Header Stamp (Date, Page No, Expt No) */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-[#fca5a5] pb-3 mb-5">
            <div className="flex items-center gap-2">
              <span className="rough-stamp text-xs text-[#1e40af]">DRAFTLY LOGBOOK</span>
              <span className="font-handwriting text-base font-bold text-slate-700">
                {selected?.title ? selected.title.slice(0, 32) + "..." : "New Project Workspace"}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm font-handwriting text-slate-600 font-bold">
              <span>DATE: <span className="underline decoration-dotted text-[#1e40af]">13 / 10 / 2026</span></span>
              <span>PAGE: <span className="underline decoration-dotted text-[#1e40af]">0{activePageIndex + 1} of 04</span></span>
            </div>
          </div>

          {/* Notification Sticky Note */}
          {error && <Notice tone="error" text={error} />}
          {message && <Notice tone="ok" text={message} />}

          {/* PAGE CONTENT ROUTING (WITHIN REALISTIC NOTEBOOK PAGE) */}
          <div className="flex-1">
            {/* PAGE 1: PROJECT SPECIFICATIONS & TEMPLATES */}
            {activePageIndex === 0 && (
              <ProjectSpecsPage
                project={project}
                setProject={setProject}
                saveProject={saveProject}
                onNext={() => goToPage(1)}
              />
            )}

            {/* PAGE 2: SOURCE CODE & SCREENSHOT UPLOADS */}
            {activePageIndex === 1 && (
              <MaterialsPage
                project={project}
                upload={upload}
                onPrev={() => goToPage(0)}
                onNext={() => goToPage(2)}
              />
            )}

            {/* PAGE 3: GENERATION WORKFLOW & TEACHER VALIDATION */}
            {activePageIndex === 2 && (
              <ExecutionPage
                project={project}
                job={job}
                generate={generate}
                downloadReport={downloadReport}
                onPrev={() => goToPage(1)}
                onNext={() => goToPage(3)}
              />
            )}

            {/* PAGE 4: THESIS MANUSCRIPT & WORD EDITOR */}
            {activePageIndex === 3 && (
              <ManuscriptPage
                project={project}
                editChapter={editChapter}
                regenerate={regenerate}
                downloadReport={downloadReport}
                onPrev={() => goToPage(2)}
              />
            )}
          </div>

          {/* Bottom Notebook Page Turn Navigation & Dog-Ear Corner */}
          <div className="mt-8 pt-4 border-t border-[#ded2bd] flex flex-wrap items-center justify-between gap-3 text-base">
            <button
              type="button"
              disabled={activePageIndex === 0}
              onClick={() => goToPage(activePageIndex - 1)}
              className="btn-3d-secondary py-1.5 px-3 text-sm disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={16} /> Flip to Previous Page
            </button>

            <div className="flex items-center gap-1.5 font-handwriting text-sm text-slate-500 font-bold">
              <span>Sheet {activePageIndex + 1} of 4</span>
              <span>•</span>
              <span className="text-[#1e40af]">{pageTabs[activePageIndex]?.subtitle}</span>
            </div>

            <button
              type="button"
              disabled={activePageIndex === 3}
              onClick={() => goToPage(activePageIndex + 1)}
              className="btn-3d-secondary py-1.5 px-3 text-sm disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Flip to Next Page <ChevronRight size={16} />
            </button>
          </div>

          {/* Dog-Ear Corner at Bottom Right for Tactile Page Turn Click */}
          <div
            className="dog-ear hidden sm:block cursor-pointer"
            onClick={() => {
              if (activePageIndex < 3) goToPage(activePageIndex + 1);
              else goToPage(0);
            }}
            title="Click to turn page"
          />
        </div>
      </div>
    </div>
  );
}

/* =========================================================================
   PAGE 1: PROJECT SPECS & TEMPLATE SELECTOR
   ========================================================================= */
function ProjectSpecsPage({ project, setProject, saveProject, onNext }) {
  const [templates, setTemplates] = useState(FALLBACK_TEMPLATES);
  const [selectedTemplateId, setSelectedTemplateId] = useState("btech_standard");

  useEffect(() => {
    api.templates()
      .then((data) => {
        if (Array.isArray(data) && data.length) setTemplates(data);
      })
      .catch(() => {});
  }, []);

  const set = (key, value) => setProject({ ...project, [key]: value });
  const chapterText = Array.isArray(project.custom_chapters)
    ? project.custom_chapters.join("\n")
    : project.custom_chapters || "";

  function applyTemplate(tpl) {
    setSelectedTemplateId(tpl.id);
    set("custom_chapters", tpl.chapters.join("\n"));
  }

  const activeTemplate = templates.find((t) => t.id === selectedTemplateId) || templates[0];

  return (
    <form onSubmit={saveProject} className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-2">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 font-kalam">
            Project Specification Sheet
          </h2>
          <p className="text-sm text-slate-600 font-handwriting">
            Handwritten fields for student credentials, project domain, and university format.
          </p>
        </div>
        <button type="submit" className="btn-3d-primary py-2 px-4 text-base">
          <Save size={18} /> Save Sheet
        </button>
      </div>

      {/* Form Fields with Ruled Focus & Blue Gel Pen Ink */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Project Title *
          </label>
          <input
            className="field font-bold text-lg text-[#1e40af]"
            placeholder="Write project title (e.g. AI-Powered Autonomous Crop Disease Analyzer)"
            value={project.title}
            onChange={(e) => set("title", e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Student Details & Roll Numbers
          </label>
          <textarea
            className="field-ruled"
            rows="3"
            placeholder="e.g. Sarthak Zore (Roll 42), Team Alpha"
            value={project.student_details}
            onChange={(e) => set("student_details", e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Declared Technologies
          </label>
          <textarea
            className="field-ruled"
            rows="3"
            placeholder="e.g. React, Node.js, Python, PostgreSQL, Machine Learning, TailwindCSS"
            value={project.technologies}
            onChange={(e) => set("technologies", e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            College / University Name
          </label>
          <input
            className="field"
            placeholder="e.g. Veermata Jijabai Technological Institute (VJTI)"
            value={project.college}
            onChange={(e) => set("college", e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Branch / Department
          </label>
          <input
            className="field"
            placeholder="e.g. Computer Engineering / Information Technology"
            value={project.branch}
            onChange={(e) => set("branch", e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Faculty Project Guide
          </label>
          <input
            className="field"
            placeholder="e.g. Dr. Ramesh Kulkarni, Professor"
            value={project.guide}
            onChange={(e) => set("guide", e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Academic Year
          </label>
          <input
            className="field"
            placeholder="e.g. 2025 - 2026"
            value={project.academic_year}
            onChange={(e) => set("academic_year", e.target.value)}
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Project Abstract
          </label>
          <textarea
            className="field-ruled"
            rows="3"
            placeholder="Write abstract summary of the proposed work..."
            value={project.abstract}
            onChange={(e) => set("abstract", e.target.value)}
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-bold text-slate-700 font-kalam">
            Detailed Description & Objectives
          </label>
          <textarea
            className="field-ruled"
            rows="4"
            placeholder="Detail the problem statement, objectives, and project motivation..."
            value={project.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>
      </div>

      {/* Pre-defined Academic Outline Templates */}
      <div className="rounded-lg border border-[#ded2bd] bg-[#fbf8ef] p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e5dcc7] pb-2.5">
          <div className="flex items-center gap-2">
            <GraduationCap className="text-[#1e40af]" size={22} />
            <h3 className="font-bold text-lg text-slate-900 font-kalam">
              Pre-defined University Chapter Templates
            </h3>
          </div>
          <span className="rough-stamp text-xs text-amber-800">1-CLICK APPLIED</span>
        </div>

        {/* Template Buttons */}
        <div className="mt-3 grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((tpl) => {
            const isSelected = selectedTemplateId === tpl.id;
            return (
              <button
                type="button"
                key={tpl.id}
                onClick={() => applyTemplate(tpl)}
                className={`rounded-md border p-3 text-left transition-all relative ${
                  isSelected
                    ? "border-[#1e40af] bg-white ring-2 ring-[#1e40af] shadow-md"
                    : "border-[#e0d6c1] bg-[#fdfbf7] hover:border-[#1e40af]/60 hover:bg-white"
                }`}
              >
                {isSelected && (
                  <span className="absolute right-2 top-2 rounded-full bg-[#1e40af] text-white p-0.5">
                    <Check size={12} />
                  </span>
                )}
                <span className="font-bold text-base text-slate-900 block font-kalam">{tpl.name}</span>
                <span className="inline-block rounded bg-amber-100 px-1.5 py-0.5 text-xs font-bold text-amber-900 mt-0.5 font-mono">
                  {tpl.chapters?.length || 0} Chapters
                </span>
                <p className="mt-1 text-xs text-slate-600 line-clamp-2 font-handwriting">{tpl.description}</p>
              </button>
            );
          })}
        </div>

        {/* Selected Chapters Outline Preview */}
        {activeTemplate && (
          <div className="mt-3.5 rounded-md border border-[#e5dcc7] bg-white p-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="text-xs font-bold text-slate-700 font-kalam">
                Outline Preview: {activeTemplate.name}
              </span>
              <button
                type="button"
                onClick={() => applyTemplate(activeTemplate)}
                className="text-xs font-bold text-[#1e40af] hover:underline flex items-center gap-1"
              >
                <RotateCcw size={12} /> Reset to defaults
              </button>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5 max-h-32 overflow-y-auto pr-1">
              {(activeTemplate.chapters || []).map((ch, idx) => (
                <span
                  key={idx}
                  className="rounded border border-[#ded2bd] bg-[#fcf9ee] px-2 py-0.5 text-xs font-bold text-slate-800"
                >
                  <span className="text-slate-400 font-mono text-[10px] mr-1">{idx + 1}.</span> {ch}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Custom Chapter List */}
        <div className="mt-4">
          <label className="block text-xs font-bold text-slate-700 font-kalam">
            Custom Chapter Sequence (Editable — Add / Reorder lines):
          </label>
          <textarea
            className="field-ruled font-mono text-xs"
            rows="5"
            placeholder="One chapter title per line..."
            value={chapterText}
            onChange={(e) => set("custom_chapters", e.target.value)}
          />
        </div>
      </div>
    </form>
  );
}

/* =========================================================================
   PAGE 2: MATERIALS & EXHIBITS (UPLOADS & SYSTEM BLUEPRINT)
   ========================================================================= */
function MaterialsPage({ project, upload, onPrev, onNext }) {
  return (
    <div className="space-y-6">
      <div className="pb-2 border-b border-[#ded2bd]">
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 font-kalam">
          Lab Materials & Attachments
        </h2>
        <p className="text-sm text-slate-600 font-handwriting">
          Attach project source code and UI screenshots. The AI will extract modules and insert captioned images into the Word report.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {/* Source Code Dropzone */}
        <label className="rounded-xl border-2 border-dashed border-[#1e40af]/50 bg-white/70 p-5 cursor-pointer hover:border-[#1e40af] hover:bg-white transition-all shadow-sm block relative">
          <div className="washi-tape washi-tape-blue -top-2.5 left-8" />
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#1e40af]/10 text-[#1e40af]">
              <FileCode size={26} />
            </div>
            <div>
              <h3 className="font-bold text-lg text-slate-900 font-kalam">Attach Project Code & Docs</h3>
              <p className="text-xs text-slate-500 font-handwriting">Python, JS, Java, C++, SQL, PDF, DOCX, TXT</p>
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-600 leading-relaxed font-handwriting">
            The backend extracts classes, endpoints, database schemas, and algorithms to write factual implementation sections.
          </p>
          <div className="mt-4 flex items-center justify-between rounded-md bg-[#1e40af]/10 px-3 py-2 text-xs font-bold text-[#1e40af]">
            <span className="flex items-center gap-1.5"><FileUp size={16} /> Choose Code / Doc Files</span>
            <span className="rough-stamp text-[10px]">MAX 25MB</span>
          </div>
          <input className="hidden" type="file" multiple onChange={(e) => upload(e, "material")} />
        </label>

        {/* UI Screenshots Dropzone */}
        <label className="rounded-xl border-2 border-dashed border-teal-500/50 bg-white/70 p-5 cursor-pointer hover:border-teal-600 hover:bg-white transition-all shadow-sm block relative">
          <div className="washi-tape washi-tape-mint -top-2.5 left-8" />
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
              <ImageIcon size={26} />
            </div>
            <div>
              <h3 className="font-bold text-lg text-slate-900 font-kalam">Attach UI Screenshots</h3>
              <p className="text-xs text-slate-500 font-handwriting">PNG, JPG, JPEG, WEBP</p>
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-600 leading-relaxed font-handwriting">
            Screenshots are automatically centered and captioned inside the Word document under "Project Screenshots".
          </p>
          <div className="mt-4 flex items-center justify-between rounded-md bg-teal-50 px-3 py-2 text-xs font-bold text-teal-800">
            <span className="flex items-center gap-1.5"><FileUp size={16} /> Choose Screenshots</span>
            <span className="rough-stamp text-[10px]">AUTO-SCALED</span>
          </div>
          <input className="hidden" type="file" multiple accept="image/*" onChange={(e) => upload(e, "screenshot")} />
        </label>
      </div>

      {/* Code Architecture Profile (If Analyzed) */}
      {project.profile && (
        <div className="rounded-xl border border-[#ded2bd] bg-white/80 p-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#ded2bd] pb-2">
            <span className="rough-stamp text-xs text-[#1e40af]">SYSTEM BLUEPRINT</span>
            <span className="text-xs font-mono font-bold text-slate-500">Extracted Architecture</span>
          </div>
          <pre className="mt-2 max-h-60 overflow-auto rounded bg-[#f8f5ee] p-3 font-mono text-xs leading-relaxed text-slate-800 border border-[#ded2bd]">
            {JSON.stringify(project.profile, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

/* =========================================================================
   PAGE 3: EXECUTION WORKFLOW & TEACHER VALIDATION
   ========================================================================= */
function ExecutionPage({ project, job, generate, downloadReport, onPrev, onNext }) {
  const isRunning = job && !["completed", "failed"].includes(job.status);
  const completedFile = job?.result_file_id;

  return (
    <div className="space-y-6">
      <div className="pb-2 border-b border-[#ded2bd]">
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 font-kalam">
          Execution & Faculty Evaluation
        </h2>
        <p className="text-sm text-slate-600 font-handwriting">
          Generate the complete thesis report, compile technical diagrams, and audit consistency.
        </p>
      </div>

      {/* 3D Action Execution Banner */}
      <div className="rounded-xl border border-[#ded2bd] bg-white/90 p-5 shadow-md flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rough-stamp text-xs text-amber-800">WORKFLOW ENGINE</span>
            {isRunning && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-800 animate-pulse font-mono">
                ⚡ Job Running in Background
              </span>
            )}
          </div>
          <h3 className="text-xl font-bold text-slate-900 font-kalam mt-1">
            Build Academic Project Report
          </h3>
          <p className="text-sm text-slate-600 font-handwriting mt-0.5">
            {job ? `${job.status.toUpperCase()}: ${job.message}` : "Ready to analyze project materials, write chapters, and compile Word DOCX."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            className="btn-3d-primary py-2.5 px-5 text-base"
            onClick={generate}
            disabled={isRunning}
          >
            {isRunning ? (
              <RefreshCw size={18} className="animate-spin text-white" />
            ) : (
              <Play size={18} className="fill-white" />
            )}
            <span>{isRunning ? "Writing Report..." : "Start Generation"}</span>
          </button>

          {completedFile && (
            <button
              className="btn-3d-secondary py-2.5 px-5 text-base text-emerald-800 border-emerald-400 hover:bg-emerald-50"
              onClick={() => downloadReport(completedFile)}
            >
              <Download size={18} className="text-emerald-700" />
              <span>Download DOCX</span>
            </button>
          )}
        </div>
      </div>

      {/* Professor Evaluation & AI Grading Sheet */}
      {project.validation ? (
        <div className="rounded-xl border border-[#ded2bd] bg-white/80 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-[#ded2bd] pb-2">
            <span className="rough-stamp text-xs text-red-600">PROFESSOR GRADE SHEET</span>
            <span className="font-handwriting text-sm font-bold text-slate-500">Hallucination & Consistency Audit</span>
          </div>

          <div className="flex items-center gap-5">
            {/* Red Circle Teacher Grade Stamp */}
            <div className="flex h-20 w-20 flex-col items-center justify-center rounded-full border-4 border-double border-red-500 bg-red-50 shadow-sm transform -rotate-6 shrink-0">
              <span className="text-2xl font-black text-red-600 font-mono">
                {project.validation.score ?? "NA"}
              </span>
              <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest">
                / 100
              </span>
            </div>
            <div>
              <h4 className="font-bold text-lg text-slate-900 font-kalam">University Consistency Score</h4>
              <p className="text-xs text-slate-600 font-handwriting">
                {project.validation.score >= 80
                  ? "High alignment between project code and report statements."
                  : "Review the yellow flagged notices below for potential discrepancies."}
              </p>
            </div>
          </div>

          {/* Warning Sticky Notes */}
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {(project.validation.warnings || []).map((warning, i) => (
              <div key={i} className="sticky-note rounded p-2.5 text-xs text-amber-950 flex items-start gap-2">
                <AlertTriangle size={15} className="text-amber-700 shrink-0 mt-0.5" />
                <span>{warning}</span>
              </div>
            ))}
            {!(project.validation.warnings || []).length && (
              <p className="text-xs text-emerald-800 font-bold flex items-center gap-1.5 font-handwriting">
                <CheckCircle2 size={16} /> Clean submission! Zero contradictory statements flagged.
              </p>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-[#ded2bd] bg-white/40 p-8 text-center">
          <p className="font-handwriting text-xl text-slate-500">
            No report generated yet. Click "Start Generation" above to create your report!
          </p>
        </div>
      )}
    </div>
  );
}

/* =========================================================================
   PAGE 4: THESIS MANUSCRIPT & INTERACTIVE CHAPTER EDITOR
   ========================================================================= */
function ManuscriptPage({ project, editChapter, regenerate, downloadReport, onPrev }) {
  const chapters = project.generated_report?.chapters || [];
  const completedFile = project.jobs?.[0]?.result_file_id || project.files?.find((f) => f.kind === "generated")?.id;

  if (!chapters.length) {
    return (
      <div className="rounded-xl border border-dashed border-[#ded2bd] bg-white/40 p-12 text-center space-y-3">
        <p className="font-handwriting text-2xl text-slate-500">
          The thesis manuscript is blank.
        </p>
        <p className="text-sm text-slate-500 font-handwriting">
          Please flip back to Sheet 3 ("Execution & Grade") and click "Start Generation".
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#ded2bd] pb-3">
        <div>
          <span className="rough-stamp text-xs text-[#1e40af]">MANUSCRIPT EDITOR</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 font-kalam mt-1">
            Thesis Chapters ({chapters.length} Total)
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 font-handwriting">
            Edit text in place or click a rubber-stamp prompt to rewrite any section.
          </p>
        </div>

        {completedFile && (
          <button
            className="btn-3d-primary py-2 px-4 text-sm"
            onClick={() => downloadReport(completedFile)}
          >
            <Download size={16} /> Download Final DOCX
          </button>
        )}
      </div>

      <div className="space-y-6">
        {chapters.map((chapter, idx) => (
          <Chapter
            key={chapter.title}
            index={idx + 1}
            chapter={chapter}
            editChapter={editChapter}
            regenerate={regenerate}
          />
        ))}
      </div>
    </div>
  );
}

function Chapter({ chapter, index, editChapter, regenerate }) {
  const [content, setContent] = useState(chapter.content || "");
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    setContent(chapter.content || "");
  }, [chapter.content]);

  async function handleSave() {
    await editChapter(chapter.title, content);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  }

  return (
    <section className="rounded-xl border border-[#ded2bd] bg-white/90 p-4 shadow-sm hover:shadow transition-all">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e5dcc7] pb-2.5">
        <div className="flex items-center gap-2">
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-mono font-bold text-slate-700">
            CH {index}
          </span>
          <h3 className="font-bold text-lg text-slate-900 font-kalam">{chapter.title}</h3>
        </div>

        {/* Rubber-Stamp Regeneration Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          {["shorter", "longer", "simpler", "more technical", "regenerate"].map((mode) => (
            <button
              key={mode}
              className="btn-3d-secondary text-xs py-1 px-2 font-medium capitalize font-handwriting"
              onClick={() => regenerate(chapter.title, mode)}
              title={`Rewrite this chapter to be ${mode}`}
            >
              <RefreshCw size={11} /> {mode}
            </button>
          ))}
          <button
            className={`btn-3d-primary text-xs py-1 px-3 ${isSaved ? "bg-emerald-600" : ""}`}
            onClick={handleSave}
          >
            {isSaved ? <Check size={14} /> : <Save size={14} />}
            <span>{isSaved ? "Saved" : "Save"}</span>
          </button>
        </div>
      </div>

      {/* Ruled Handwriting Content Field */}
      <textarea
        className="field-ruled mt-3 min-h-56 text-base"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Write or edit chapter content..."
      />
    </section>
  );
}

function AdminPanel() {
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setStatus("");
    try {
      const form = new FormData(event.currentTarget);
      const result = await api.uploadKnowledge(form);
      setStatus(`✓ ${result.chunks} reference sections successfully indexed!`);
      event.currentTarget.reset();
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="realistic-notebook p-3.5 relative shadow-book-3d space-y-2.5"
    >
      <div className="flex items-center justify-between border-b border-[#ded2bd] pb-1.5">
        <span className="rough-stamp text-xs text-teal-800">FACULTY REPOSITORY</span>
        <ShieldCheck size={16} className="text-teal-700" />
      </div>
      <p className="text-xs text-slate-600 font-handwriting">
        Upload approved university project reports for structural reference.
      </p>

      <input className="field text-xs py-1" name="college" placeholder="College / University" />
      <input className="field text-xs py-1" name="branch" placeholder="Branch" />
      <input className="field text-xs py-1" name="project_type" placeholder="Degree / Project Type" />
      <input className="field text-xs py-1" name="technology" placeholder="Domain / Technology" />
      <input className="field text-xs py-1" name="year" placeholder="Academic Year" />
      <input className="block w-full text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-teal-50 file:text-teal-700" name="file" type="file" required />

      <button className="btn-3d-primary w-full text-xs py-2 bg-teal-800" disabled={loading}>
        <Wand2 size={14} />
        <span>{loading ? "Indexing..." : "Index Approved Report"}</span>
      </button>

      {status && (
        <p className="font-handwriting text-sm font-bold text-teal-800 text-center">{status}</p>
      )}
    </form>
  );
}

function Notice({ text, tone }) {
  return (
    <div
      className={`sticky-note p-3 rounded-lg text-sm font-bold flex items-center justify-between shadow-sm mb-4 ${
        tone === "error"
          ? "bg-red-100 border-red-300 text-red-900"
          : "bg-emerald-100 border-emerald-300 text-emerald-900"
      }`}
    >
      <span>{text}</span>
      <span className="rough-stamp text-[10px]">VERIFIED</span>
    </div>
  );
}
