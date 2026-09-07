from collections import Counter
from pathlib import Path
import re


LANGUAGE_BY_EXT = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "React",
    ".ts": "TypeScript",
    ".tsx": "React TypeScript",
    ".java": "Java",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".php": "PHP",
    ".rb": "Ruby",
    ".go": "Go",
    ".rs": "Rust",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
}

TECH_PATTERNS = {
    "React": r"\breact\b|from ['\"]react",
    "Vite": r"\bvite\b",
    "FastAPI": r"\bfastapi\b",
    "Django": r"\bdjango\b",
    "Flask": r"\bflask\b",
    "PostgreSQL": r"\bpostgres|postgresql\b",
    "MySQL": r"\bmysql\b",
    "MongoDB": r"\bmongodb|mongoose\b",
    "Tailwind CSS": r"\btailwind\b",
    "JWT": r"\bjwt|jsonwebtoken\b",
    "ChromaDB": r"\bchromadb|chroma\b",
}


def analyze_project(project, files) -> dict:
    combined = "\n".join((f.extracted_text or "")[:12000] for f in files)
    names = [f.original_name for f in files]
    languages = sorted({LANGUAGE_BY_EXT.get(Path(name).suffix.lower()) for name in names} - {None})
    detected_tech = {tech for tech, pattern in TECH_PATTERNS.items() if re.search(pattern, combined, re.I)}
    declared_tech = {item.strip() for item in re.split(r"[,;\n]", project.technologies or "") if item.strip()}
    modules = sorted(set(re.findall(r"(?:class|def|function|const)\s+([A-Za-z_][A-Za-z0-9_]*)", combined)))[:25]
    feature_words = Counter(re.findall(r"\b(?:login|register|upload|generate|download|admin|report|project|diagram|preview|edit)\b", combined, re.I))
    features = [word.title() for word, _ in feature_words.most_common(12)]
    database = "PostgreSQL" if "PostgreSQL" in detected_tech or re.search(r"\btable|schema|sqlalchemy|prisma\b", combined, re.I) else ""
    architecture = "Web application with frontend, backend API, database, file storage, RAG knowledge base, and AI generation service."
    return {
        "technologies": sorted(detected_tech | declared_tech),
        "modules": modules,
        "features": features,
        "database": database,
        "programming_languages": languages,
        "architecture": architecture,
        "source_files_analyzed": names,
        "analysis_rule": "Static text extraction only; uploaded source code was not executed.",
    }
