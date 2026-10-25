from collections import Counter
from pathlib import Path
import re


DOMAIN_PATTERNS = {
    "civil": [
        r"\bcivil\b", r"\bstructural\b", r"\brcc\b", r"\bconcrete\b", r"\bcement\b",
        r"\bsoil\b", r"\bgeotechnical\b", r"\bhighway\b", r"\bpavement\b", r"\bbridge\b",
        r"\betabs\b", r"\bstaad\b", r"\brevit\b", r"\bautocad\b", r"\bis\s*456\b",
        r"\bis\s*800\b", r"\bis\s*1893\b", r"\bcompressive\s*strength\b", r"\bslump\b",
        r"\bmix\s*design\b", r"\bfoundation\b", r"\bseismic\b", r"\bbeam\b", r"\bcolumn\b",
        r"\bslab\b", r"\bsurveying\b", r"\btotal\s*station\b", r"\bwater\s*treatment\b",
        r"\bhydraulics?\b", r"\bconstruction\b", r"\bestimation\b", r"\bboq\b",
    ],
    "mechanical": [
        r"\bmechanical\b", r"\bthermal\b", r"\bheat\s*transfer\b", r"\bansys\b",
        r"\bsolidworks\b", r"\bcatia\b", r"\bcfd\b", r"\bfea\b", r"\bengine\b",
        r"\bturbine\b", r"\bhvac\b", r"\brefrigeration\b", r"\bmanufacturing\b",
        r"\bcnc\b", r"\blathe\b", r"\bgear\b", r"\brobotics\b", r"\bkinematics\b",
        r"\bfluid\s*mechanics\b", r"\baerodynamic\b", r"\bmechatronics\b", r"\btorque\b",
    ],
    "electrical": [
        r"\belectrical\b", r"\belectronics\b", r"\bcircuit\b", r"\bpcb\b", r"\barduino\b",
        r"\besp32\b", r"\braspberry\s*pi\b", r"\bvlsi\b", r"\bverilog\b", r"\bvhdl\b",
        r"\bmatlab\b", r"\bsimulink\b", r"\binverter\b", r"\btransformer\b", r"\bpower\s*system\b",
        r"\bmicrocontroller\b", r"\bfpga\b", r"\bsignal\s*processing\b", r"\biot\b",
        r"\bantenna\b", r"\btelecom\b", r"\bembedded\b",
    ],
    "management": [
        r"\bmba\b", r"\bmanagement\b", r"\bmarketing\b", r"\bfinance\b", r"\bconsumer\b",
        r"\bsupply\s*chain\b", r"\blogistics\b", r"\bhrm\b", r"\bhuman\s*resource\b",
        r"\baccounting\b", r"\bswot\b", r"\broi\b", r"\bvaluation\b", r"\bfinancial\b",
        r"\bportfolio\b", r"\bcommerce\b", r"\bbusiness\b", r"\bmarket\s*research\b",
        r"\bfmcc?g\b", r"\bretail\b", r"\bbrand\b", r"\beconomics\b",
    ],
    "science": [
        r"\bchemistry\b", r"\bchemical\b", r"\bbiotechnology\b", r"\bpharmacy\b",
        r"\bbiology\b", r"\bdna\b", r"\benzyme\b", r"\bchromatography\b",
        r"\bspectroscopy\b", r"\btitration\b", r"\bpolymer\b", r"\bclinical\b",
        r"\bpharmaceutical\b", r"\bmolecular\b", r"\benvironmental\s*science\b",
    ],
    "tech": [
        r"\bcomputer\b", r"\bsoftware\b", r"\breact\b", r"\bpython\b", r"\bjavascript\b",
        r"\bjava\b", r"\bapi\b", r"\bmachine\s*learning\b", r"\bdeep\s*learning\b",
        r"\bdata\s*science\b", r"\bdatabase\b", r"\bfrontend\b", r"\bbackend\b",
        r"\bfastapi\b", r"\bnode\b", r"\bcloud\b", r"\bdocker\b", r"\bcybersecurity\b",
        r"\bblockchain\b", r"\bnlp\b", r"\bai\b",
    ],
}

STANDARDS_PATTERNS = {
    "Civil": [
        ("IS 456:2000", r"\bis\s*456\b"),
        ("IS 800:2007", r"\bis\s*800\b"),
        ("IS 1893:2016 (Seismic)", r"\bis\s*1893\b"),
        ("IS 13920 (Ductile Detailing)", r"\bis\s*13920\b"),
        ("IS 875 (Wind & Dead Loads)", r"\bis\s*875\b"),
        ("IS 10262 (Concrete Mix Proportioning)", r"\bis\s*10262\b"),
        ("SP 16 Design Aids", r"\bsp\s*16\b"),
        ("IRC (Indian Roads Congress)", r"\birc\b"),
        ("ASTM Standards", r"\bastm\b"),
        ("ACI 318", r"\baci\s*318\b"),
        ("Eurocodes", r"\beurocode\b"),
    ],
    "Mechanical": [
        ("ASME Boiler & Pressure Vessel", r"\basme\b"),
        ("ISO 9001 / 14001", r"\biso\s*(?:9001|14001)\b"),
        ("DIN Standards", r"\bdin\b"),
        ("SAE Standards", r"\bsae\b"),
    ],
    "Electrical": [
        ("IEEE Standards", r"\bieee\b"),
        ("IEC Standards", r"\biec\b"),
        ("NEC / National Electrical Code", r"\bnec\b"),
    ],
    "Tech": [
        ("IEEE 12207 / 830 SRS", r"\bieee\b"),
        ("ISO/IEC 27001 (Security)", r"\b27001\b"),
        ("W3C / RFC Standards", r"\bw3c|rfc\b"),
    ],
    "Management": [
        ("ISO 9001 Quality Management", r"\biso\s*9001\b"),
        ("GAAP / IFRS Accounting Standards", r"\bgaap|ifrs\b"),
        ("COSO Internal Control", r"\bcoso\b"),
    ],
}


def detect_domain(branch: str, title: str, combined_text: str) -> dict:
    search_space = f"{branch}\n{title}\n{combined_text}".lower()

    scores = Counter()
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pat in patterns:
            matches = len(re.findall(pat, search_space, re.I))
            if matches:
                weight = 5 if domain in branch.lower() else (3 if domain in title.lower() else 1)
                scores[domain] += matches * weight

    # Give strong prior from branch if explicitly stated
    branch_l = branch.lower()
    if any(k in branch_l for k in ["civil", "construction", "structure", "structural", "geotech"]):
        scores["civil"] += 30
    elif any(k in branch_l for k in ["mech", "automobile", "production", "aero"]):
        scores["mechanical"] += 30
    elif any(k in branch_l for k in ["elect", "ece", "eee", "instrumentation", "telecom"]):
        scores["electrical"] += 30
    elif any(k in branch_l for k in ["mba", "bba", "management", "commerce", "finance", "business"]):
        scores["management"] += 30
    elif any(k in branch_l for k in ["chem", "bio", "pharma", "biotech", "science"]):
        scores["science"] += 30
    elif any(k in branch_l for k in ["cs", "it", "computer", "software", "data", "ai", "mca"]):
        scores["tech"] += 30

    best_domain = scores.most_common(1)[0][0] if scores else "tech"

    domain_meta = {
        "civil": {
            "key": "civil",
            "name": "Civil & Structural Engineering",
            "standards_group": "Civil",
            "default_architecture": "Structural Load Transfer & Multi-Storey RCC Framing Framework",
            "default_methodology": "Empirical laboratory material investigation, IS code compliance, and finite element modeling (FEM)",
        },
        "mechanical": {
            "key": "mechanical",
            "name": "Mechanical & Automobile Engineering",
            "standards_group": "Mechanical",
            "default_architecture": "Thermodynamic / Mechanical Power Transmission & Component Integration",
            "default_methodology": "CAD geometrical modeling, finite element analysis (FEA), and test bench validation",
        },
        "electrical": {
            "key": "electrical",
            "name": "Electrical & Electronics Engineering",
            "standards_group": "Electrical",
            "default_architecture": "Embedded Hardware, Signal Conditioning & Microcontroller Control Loop",
            "default_methodology": "Schematic design, SPICE/MATLAB simulation, PCB fabrication, and instrumentation testing",
        },
        "management": {
            "key": "management",
            "name": "Business Administration & Management",
            "standards_group": "Management",
            "default_architecture": "Strategic Operational Workflow & Enterprise Value Chain Framework",
            "default_methodology": "Empirical survey sampling, quantitative statistical analysis, and financial valuation modeling",
        },
        "science": {
            "key": "science",
            "name": "Applied Sciences & Biotechnology",
            "standards_group": "Science",
            "default_architecture": "Experimental Protocol, Analytical Instrumentation & Molecular Assay Pipeline",
            "default_methodology": "Controlled laboratory experimentation, spectroscopic characterization, and statistical validation",
        },
        "tech": {
            "key": "tech",
            "name": "Computer Science & IT",
            "standards_group": "Tech",
            "default_architecture": "Full-Stack Application with Frontend Interface, Backend Controller, Database Tier & AI Integration",
            "default_methodology": "Agile software engineering, API modularization, unit testing, and empirical system benchmark",
        },
    }

    return domain_meta.get(best_domain, domain_meta["tech"])


def analyze_project(project, files) -> dict:
    combined = "\n\n".join((f.extracted_text or "")[:15000] for f in files)
    names = [f.original_name for f in files]
    branch = getattr(project, "branch", "") or ""
    title = getattr(project, "title", "") or ""

    domain_info = detect_domain(branch, title, combined)
    domain_key = domain_info["key"]

    # Detect recognized standards and codes
    applicable_standards: list[str] = []
    group = domain_info["standards_group"]
    patterns = STANDARDS_PATTERNS.get(group, [])
    for std_name, pat in patterns:
        if re.search(pat, f"{title}\n{project.technologies}\n{combined}", re.I):
            applicable_standards.append(std_name)

    # Detect empirical findings / numbers in uploaded files
    empirical_observations: list[str] = []
    for line in combined.split("\n"):
        line_clean = line.strip()
        if re.search(r"\b(?:\d+(?:\.\d+)?\s*(?:mpa|n/mm2|kn|kg|m|mm|cm|%|ms|sec|hz|v|a|w|rpm|celsius|°c))\b", line_clean, re.I):
            if len(line_clean) < 140 and line_clean not in empirical_observations:
                empirical_observations.append(line_clean)
        if len(empirical_observations) >= 8:
            break

    # Extract declared tools/technologies
    declared_tools = [item.strip() for item in re.split(r"[,;\n]", project.technologies or "") if item.strip()]

    # Extract key concepts or modules
    modules = sorted(set(re.findall(r"(?:class|def|function|module|algorithm|section|protocol)\s+([A-Za-z_][A-Za-z0-9_]*)", combined)))[:15]
    if not modules:
        # Fallback to key capitalized technical nouns
        tech_nouns = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", combined)
        c = Counter(tech_nouns)
        modules = [w for w, cnt in c.most_common(12) if len(w) > 3 and w.lower() not in {"figure", "table", "project", "chapter", "student"}]

    return {
        "domain_key": domain_key,
        "domain_name": domain_info["name"],
        "architecture_summary": domain_info["default_architecture"],
        "core_methodology": domain_info["default_methodology"],
        "declared_tools_and_materials": declared_tools,
        "applicable_standards": applicable_standards or ["Standard University Academic & Engineering Guidelines"],
        "empirical_observations": empirical_observations[:6],
        "key_modules_and_components": modules[:10],
        "source_files_analyzed": names,
        "total_files_read": len(files),
    }
