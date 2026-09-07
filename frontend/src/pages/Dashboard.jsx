import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Download, FileUp, Play, Plus, RefreshCw, Save, Wand2 } from "lucide-react";
import { api, getUser } from "../api/client";

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
  custom_chapters: null
};

export function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [project, setProject] = useState(emptyProject);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [job, setJob] = useState(null);
  const user = getUser();

  const selected = useMemo(() => projects.find((item) => item.id === selectedId), [projects, selectedId]);

  useEffect(() => {
    loadProjects().catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (selected) setProject(selected);
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
        }
      } catch (err) {
        setError(err.message);
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [job]);

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
      setMessage("Project saved");
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
    for (const file of files) {
      const form = new FormData();
      form.append("kind", kind);
      form.append("file", file);
      await api.upload(project.id, form);
    }
    setMessage(`${files.length} file(s) uploaded`);
  }

  async function generate() {
    setError("");
    try {
      const created = await api.generate(project.id);
      setJob(created);
    } catch (err) {
      setError(err.message);
    }
  }

  async function editChapter(title, content) {
    const updated = await api.editChapter(project.id, { chapter: title, content });
    setProject(updated);
  }

  async function regenerate(title, mode) {
    setMessage(`Regenerating ${title}`);
    const updated = await api.regenerateChapter(project.id, { chapter: title, mode });
    setProject(updated);
  }

  async function downloadReport(fileId) {
    setError("");
    try {
      await api.downloadReport(project.id, fileId, `${project.title || "report"}.docx`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="space-y-4">
        <button className="btn-primary w-full" onClick={() => { setProject(emptyProject); setSelectedId(null); }}>
          <Plus size={16} /> New Project
        </button>
        <div className="panel divide-y divide-slate-100">
          {projects.map((item) => (
            <button key={item.id} className={`block w-full px-4 py-3 text-left text-sm ${item.id === selectedId ? "bg-mint/10 text-ocean" : "hover:bg-slate-50"}`} onClick={() => setSelectedId(item.id)}>
              <span className="font-medium">{item.title}</span>
              <span className="mt-1 block text-xs text-slate-500">{item.branch || "Branch not set"}</span>
            </button>
          ))}
          {!projects.length && <p className="px-4 py-6 text-sm text-slate-500">No projects yet.</p>}
        </div>
        {user?.role === "admin" && <AdminPanel />}
      </aside>

      <section className="space-y-6">
        {error && <Notice tone="error" text={error} />}
        {message && <Notice tone="ok" text={message} />}
        <ProjectForm project={project} setProject={setProject} saveProject={saveProject} />
        {project.id && (
          <>
            <UploadPanel upload={upload} />
            <ActionPanel project={project} job={job} generate={generate} downloadReport={downloadReport} />
            <ProfilePanel project={project} />
            <ReportEditor project={project} editChapter={editChapter} regenerate={regenerate} />
          </>
        )}
      </section>
    </div>
  );
}

function ProjectForm({ project, setProject, saveProject }) {
  const set = (key, value) => setProject({ ...project, [key]: value });
  const chapterText = Array.isArray(project.custom_chapters) ? project.custom_chapters.join("\n") : project.custom_chapters || "";
  return (
    <form onSubmit={saveProject} className="panel p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Project Details</h2>
        <button className="btn-primary"><Save size={16} /> Save</button>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <input className="field md:col-span-2" placeholder="Project title" value={project.title} onChange={(e) => set("title", e.target.value)} required />
        <textarea className="field" rows="3" placeholder="Student details" value={project.student_details} onChange={(e) => set("student_details", e.target.value)} />
        <textarea className="field" rows="3" placeholder="Technologies" value={project.technologies} onChange={(e) => set("technologies", e.target.value)} />
        <input className="field" placeholder="College" value={project.college} onChange={(e) => set("college", e.target.value)} />
        <input className="field" placeholder="Branch" value={project.branch} onChange={(e) => set("branch", e.target.value)} />
        <input className="field" placeholder="Guide" value={project.guide} onChange={(e) => set("guide", e.target.value)} />
        <input className="field" placeholder="Academic year" value={project.academic_year} onChange={(e) => set("academic_year", e.target.value)} />
        <textarea className="field md:col-span-2" rows="4" placeholder="Abstract" value={project.abstract} onChange={(e) => set("abstract", e.target.value)} />
        <textarea className="field md:col-span-2" rows="5" placeholder="Description" value={project.description} onChange={(e) => set("description", e.target.value)} />
        <textarea className="field md:col-span-2" rows="3" placeholder="Custom chapter list, one per line" value={chapterText} onChange={(e) => set("custom_chapters", e.target.value)} />
      </div>
    </form>
  );
}

function UploadPanel({ upload }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="panel block cursor-pointer p-5 hover:border-ocean">
        <FileUp className="mb-3 text-ocean" />
        <span className="font-medium">Upload Materials</span>
        <p className="mt-1 text-sm text-slate-600">Source code, PDF, DOCX and TXT files.</p>
        <input className="mt-4 block text-sm" type="file" multiple onChange={(e) => upload(e, "material")} />
      </label>
      <label className="panel block cursor-pointer p-5 hover:border-ocean">
        <FileUp className="mb-3 text-mint" />
        <span className="font-medium">Upload Screenshots</span>
        <p className="mt-1 text-sm text-slate-600">PNG, JPG, JPEG or WEBP project images.</p>
        <input className="mt-4 block text-sm" type="file" multiple accept="image/*" onChange={(e) => upload(e, "screenshot")} />
      </label>
    </div>
  );
}

function ActionPanel({ job, generate, downloadReport }) {
  const completedFile = job?.result_file_id;
  return (
    <div className="panel flex flex-wrap items-center justify-between gap-3 p-5">
      <div>
        <h3 className="font-semibold">Generation Workflow</h3>
        <p className="text-sm text-slate-600">{job ? `${job.status}: ${job.message}` : "Analyze, retrieve RAG context, generate, validate, diagram, export DOCX."}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <button className="btn-primary" onClick={generate} disabled={job && !["completed", "failed"].includes(job.status)}>
          <Play size={16} /> Generate
        </button>
        {completedFile && <button className="btn-secondary" onClick={() => downloadReport(completedFile)}><Download size={16} /> Download DOCX</button>}
      </div>
    </div>
  );
}

function ProfilePanel({ project }) {
  if (!project.profile && !project.validation) return null;
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {project.profile && (
        <div className="panel p-5">
          <h3 className="font-semibold">Project Profile</h3>
          <pre className="mt-3 max-h-72 overflow-auto rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(project.profile, null, 2)}</pre>
        </div>
      )}
      {project.validation && (
        <div className="panel p-5">
          <h3 className="font-semibold">AI Validation</h3>
          <p className="mt-2 text-3xl font-semibold text-ocean">{project.validation.score ?? "NA"}</p>
          {(project.validation.warnings || []).map((warning) => (
            <p key={warning} className="mt-2 flex gap-2 text-sm text-coral"><AlertTriangle size={16} /> {warning}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function ReportEditor({ project, editChapter, regenerate }) {
  const chapters = project.generated_report?.chapters || [];
  if (!chapters.length) return null;
  return (
    <div className="panel p-5">
      <h2 className="text-xl font-semibold">Report Preview and Editor</h2>
      <div className="mt-4 space-y-5">
        {chapters.map((chapter) => (
          <Chapter key={chapter.title} chapter={chapter} editChapter={editChapter} regenerate={regenerate} />
        ))}
      </div>
    </div>
  );
}

function Chapter({ chapter, editChapter, regenerate }) {
  const [content, setContent] = useState(chapter.content || "");
  useEffect(() => setContent(chapter.content || ""), [chapter.content]);
  return (
    <section className="border-t border-slate-200 pt-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold">{chapter.title}</h3>
        <div className="flex flex-wrap gap-2">
          {["shorter", "longer", "simpler", "more technical", "regenerate"].map((mode) => (
            <button key={mode} className="btn-secondary" onClick={() => regenerate(chapter.title, mode)}><RefreshCw size={14} /> {mode}</button>
          ))}
          <button className="btn-primary" onClick={() => editChapter(chapter.title, content)}><Save size={14} /> Save</button>
        </div>
      </div>
      <textarea className="field mt-3 min-h-56" value={content} onChange={(event) => setContent(event.target.value)} />
    </section>
  );
}

function AdminPanel() {
  const [status, setStatus] = useState("");
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const result = await api.uploadKnowledge(form);
    setStatus(`${result.chunks} chunks added to ChromaDB`);
    event.currentTarget.reset();
  }
  return (
    <form onSubmit={submit} className="panel space-y-3 p-4">
      <h3 className="font-semibold">Admin Knowledge Base</h3>
      <input className="field" name="college" placeholder="College" />
      <input className="field" name="branch" placeholder="Branch" />
      <input className="field" name="project_type" placeholder="Project type" />
      <input className="field" name="technology" placeholder="Technology" />
      <input className="field" name="year" placeholder="Year" />
      <input className="block text-sm" name="file" type="file" required />
      <button className="btn-primary w-full"><Wand2 size={16} /> Add Report</button>
      {status && <p className="text-sm text-mint">{status}</p>}
    </form>
  );
}

function Notice({ text, tone }) {
  return <p className={`rounded-md px-3 py-2 text-sm ${tone === "error" ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`}>{text}</p>;
}
