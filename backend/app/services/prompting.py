DEFAULT_CHAPTERS = [
    "Introduction",
    "Literature Survey",
    "Objectives and Scope",
    "Specifications and Requirements",
    "Theoretical and Design Methodology",
    "System and Architectural Modeling",
    "Implementation and Experimental Setup",
    "Testing and Verification",
    "Results and Performance Discussion",
    "Conclusion",
    "Future Scope",
    "References",
]

TEMPLATE_PRESETS = [
    {
        "id": "btech_standard",
        "name": "B.Tech / B.E. Major Project (Standard)",
        "description": "Comprehensive 12-chapter format following standard AICTE, UGC, and international engineering guidelines.",
        "recommended_for": "Computer Science, IT, Electronics, Mechanical, Civil & Multidisciplinary Engineering",
        "chapters": DEFAULT_CHAPTERS,
    },
    {
        "id": "civil_structural",
        "name": "Civil & Structural Engineering Thesis",
        "description": "Tailored for RCC structures, concrete mix design, geotechnical investigations, transportation, and construction management.",
        "recommended_for": "Civil Engineering, Structural Engineering, Construction Tech, Transportation & Environmental",
        "chapters": [
            "Introduction and Project Significance",
            "Literature Survey and Standard Codes (IS / ASTM / Eurocode)",
            "Site Investigation and Material Characterization",
            "Structural Analysis, Design Philosophy and Load Calculations",
            "Laboratory Testing and Concrete Mix Proportioning",
            "Modeling, Simulation and Structural Load Distribution",
            "Project Scheduling and Quantity Estimation (BOQ)",
            "Results, Structural Verification and Discussion",
            "Conclusion and Environmental Sustainability",
            "References and Standard Regulatory Codes",
        ],
    },
    {
        "id": "mech_electrical",
        "name": "Mechanical & Electrical Engineering",
        "description": "Engineered for thermal systems, CAD/FEA, robotics, power systems, circuits, and mechatronic prototypes.",
        "recommended_for": "Mechanical, Automobile, Production, Electrical (EEE), Electronics (ECE) & Mechatronics",
        "chapters": [
            "Introduction and Engineering Context",
            "Literature Review and Technological State of the Art",
            "Design Specifications and Mathematical Formulation",
            "Component Modeling, CAD / Circuit Layout and Simulation",
            "Fabrication, Assembly and Experimental Test Rig Setup",
            "Performance Evaluation, Testing and Benchmark Verification",
            "Cost Analysis, Safety Considerations and Compliance",
            "Conclusion and Future Enhancements",
            "References",
        ],
    },
    {
        "id": "management_commerce",
        "name": "Business Management & Non-Tech Studies",
        "description": "Professional structure covering executive context, industry analysis, empirical survey sampling, and financial viability.",
        "recommended_for": "MBA, BBA, Commerce, Finance, Supply Chain, Marketing & Interdisciplinary Non-Tech",
        "chapters": [
            "Executive Summary and Industry Background",
            "Literature Review and Theoretical Conceptual Framework",
            "Research Methodology, Sampling and Data Collection",
            "Environmental, Operational and Market Investigation",
            "Implementation Strategy and Value Chain Operations",
            "Empirical Findings, Statistical Analysis and Discussion",
            "Financial Viability, Risk Governance and ROI Evaluation",
            "Strategic Recommendations and Conclusion",
            "References and Appendices",
        ],
    },
    {
        "id": "mca_msc",
        "name": "MCA / Software Engineering",
        "description": "Software-engineering centric structure with SRS, database modeling, API services, and QA testing matrices.",
        "recommended_for": "MCA, M.Sc Computer Science, Software Engineering",
        "chapters": [
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
        "id": "ai_ml",
        "name": "AI / Machine Learning & Data Science",
        "description": "Specialized structure covering dataset curation, feature engineering, model architecture, loss metrics, and deployment.",
        "recommended_for": "AI/ML, Data Science, Deep Learning, NLP & Computer Vision Projects",
        "chapters": [
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
        "id": "mini_project",
        "name": "Mini Project / Fast Track (6 Chapters)",
        "description": "Concise and focused outline ideal for 3rd year mini projects, rapid prototypes, or term papers.",
        "recommended_for": "Mini-projects, Semester Term Papers, Hackathon submissions",
        "chapters": [
            "Introduction and Objectives",
            "Requirement and Feasibility Analysis",
            "System Architecture and Technical Design",
            "Implementation and Workflow Demonstration",
            "Testing and Empirical Verification",
            "Conclusion and References",
        ],
    },
    {
        "id": "ieee_research",
        "name": "IEEE / Academic Research Thesis",
        "description": "Formal academic thesis outline emphasizing theoretical modeling, algorithm formulation, and comparative evaluation.",
        "recommended_for": "M.Tech / MS Thesis, Research Projects, Conference Papers",
        "chapters": [
            "Introduction",
            "Related Work and Background",
            "Mathematical and Architectural Formulation",
            "Proposed Methodology and Framework",
            "Implementation Details",
            "Experimental Results and Comparative Analysis",
            "Discussion and Conclusion",
            "References",
        ],
    },
]


SYSTEM_SAFETY = """
You are a senior academic supervisor and distinguished university professor.
You write comprehensive, university-grade academic project thesis reports matching UGC, AICTE, and IEEE standards.

MANDATORY RULES:
1. PRIMARY GROUND TRUTH: Ground all technical discussion, materials, methodology, metrics, and results
   in the student's actual project files, uploaded code/docs, data spreadsheets, and image vision extractions.
2. DOMAIN INTEGRITY: Respect the project's declared engineering or academic field (e.g., Civil Engineering,
   Mechanical, Electrical, Management, Science, or Computer Science).
   - If Civil Engineering: discuss structural modeling (ETABS, STAAD, Revit), IS codes (IS 456, IS 1893, IS 800), concrete mix proportions, slump, soil parameters, compressive strength (MPa), moments, and construction sequence. NEVER talk about web servers, APIs, or database schemas unless specifically built by the student.
   - If Mechanical / Electrical: discuss physical mechanisms, CAD/FEA, thermodynamics, circuits, sensors, microcontrollers, or test rigs.
   - If Management / Commerce: discuss market dynamics, survey sampling, statistical regressions, financial valuation, ROI, SWOT, and operations.
   - If Tech / CS: discuss architecture, data flow, algorithms, database entities, and test suites.
3. HUMAN-LIKE SCHOLARLY TONE: Write in rich, formal, objective academic prose. Avoid repetitive AI cliches
   (do not repeat phrases like 'in today's rapidly evolving world' or 'delves into'). Write with the depth,
   precision, and nuance of an experienced researcher.
4. INFORMATIVE TABLES: Every chapter where analysis, specifications, comparison, testing, or results are
   discussed MUST include high-quality, publication-grade academic tables with realistic parameters and units.
5. NO HALLUCINATION OF CONTRADICTIONS: When data is present in uploaded attachments, cite the exact numbers,
   grades, ratios, and findings from the student's materials.
"""


def project_context(project, profile: dict, extracted: str, rag_chunks: list[dict]) -> str:
    domain_name = profile.get("domain_name") or "Academic Engineering & Research"
    standards = ", ".join(profile.get("applicable_standards") or ["Standard University Guidelines"])
    empirical = "\n".join(f"- {obs}" for obs in profile.get("empirical_observations", []))

    references = "\n\n".join(
        f"CURRICULUM REFERENCE SAMPLE {i + 1} [{chunk.get('metadata', {})}]:\n{chunk.get('text', '')[:1600]}"
        for i, chunk in enumerate(rag_chunks)
    )

    return f"""
{SYSTEM_SAFETY}

STUDENT PROJECT PROFILE:
Title: {project.title}
Branch / Department: {project.branch or 'Engineering'}
Discipline Domain: {domain_name}
College / University: {project.college or 'University Faculty of Engineering'}
Faculty Project Guide: {project.guide or 'Project Supervisor'}
Candidate(s): {project.student_details or 'Candidate'}
Academic Year: {project.academic_year or '2026-2027'}
Abstract / Synopsis:
{project.abstract or 'Project investigation and technical development.'}

Declared Tools, Materials & Standards:
{project.technologies or 'Standard analytical and experimental methods'}
Applicable Regulatory Codes:
{standards}

EXTRACTED EMPIRICAL OBSERVATIONS FROM ATTACHMENTS:
{empirical or "Standard project metrics and parameters."}

UPLOADED PROJECT ATTACHMENTS & EMPIRICAL EVIDENCE (PRIMARY SOURCE):
{extracted[:35000] if extracted else "No supplementary source files attached; adhere strictly to project specifications."}

CURRICULUM REFERENCE GUIDELINES:
{references or "Adhere to standard national university thesis guidelines."}
"""


def report_prompt(context: str, chapters: list[str], chapter_guidance: str = "", domain_info: dict | None = None) -> str:
    domain_name = domain_info.get("name") if domain_info else "Engineering & Science"
    guidance_block = f"\nCURRICULUM SPECIFICATIONS & MANDATORY OUTLINE:\n{chapter_guidance}\n" if chapter_guidance else ""

    return f"""
{context}

TASK:
Generate a complete, university-grade academic project thesis report for this {domain_name} project.
{guidance_block}

Return strict JSON with this exact schema:
{{
  "chapters": [
    {{
      "title": "Exact Chapter Title",
      "content": "Formal, rigorous academic prose (approx 500 to 750 words per chapter). Structure every chapter with 3 to 4 clearly numbered sub-sections (e.g., '1.1 Problem Background and Motivation', '1.2 Theoretical Context and Technical Scope', '1.3 Detailed Methodology and Design Strategy', '1.4 Summary of Key Technical Highlights'). Thoroughly ground all discussion in the student's actual project domain, uploaded attachments, tools, and empirical data.",
      "tables": [
        {{
          "title": "Descriptive Academic Table Caption (e.g., Table 2.1: Comparative Literature Review Matrix, or Table 5.1: Mix Proportion & Structural Property Specifications)",
          "headers": ["Parameter / Aspect", "Standard Benchmark / Control", "Proposed Specification / Value", "Observed Outcome / Remarks"],
          "rows": [
            ["Row 1 Label", "Value / Ref", "Value / Spec", "Compliant / Remarks"],
            ["Row 2 Label", "Value / Ref", "Value / Spec", "Compliant / Remarks"]
          ]
        }}
      ]
    }}
  ],
  "references": [
    "[1] S. Author and R. Co-Author, 'Foundational Research Title', Journal / Conference Proceedings, vol. 48, no. 4, pp. 210-225, 2024.",
    "[2] ..."
  ],
  "diagram_requests": [
    "Diagram 1 Title matching domain",
    "Diagram 2 Title matching domain",
    "Diagram 3 Title matching domain",
    "Diagram 4 Title matching domain"
  ]
}}

CRITICAL WRITING REQUIREMENTS:
1. FULL CHAPTER SEQUENCE: Provide an entry in 'chapters' for EVERY single chapter in this exact list: {chapters}. Do NOT skip or merge any chapter.
2. STRUCTURED NUMBERED SUBHEADINGS: Every chapter MUST contain 3 to 4 structured numbered subheadings with deep, realistic technical discussion matching the domain.
3. DOMAIN-AUTHENTIC TABLES: Relevant chapters MUST contain realistic academic tables (e.g., Literature review matrix in Chapter 2, Design parameters/Mix proportions/Specifications in Chapter 4/5, Test log/Execution matrix in Chapter 7/8, Performance comparison in Chapter 9).
4. HUMAN-LIKE EXPERT TONE: Never write generic web-app descriptions for non-software projects. If Civil Engineering, use concrete grades (e.g. M25/M30), rebar (Fe500), IS codes (IS 456, IS 1893), loads, and moments. If Management, use financial metrics, survey parameters, and SWOT. If Mechanical, use thermodynamics, CAD, FEA, and mechanisms.
"""


def diagram_prompt(context: str, domain_info: dict | None = None) -> str:
    domain_key = domain_info.get("key") if domain_info else "tech"
    domain_name = domain_info.get("name") if domain_info else "Technical System"

    return f"""
{context}

TASK:
Generate 4 formal technical schematics in Mermaid syntax for this {domain_name} project.
Model the student's real project domain, architecture, physical or logical components, and workflows.

STRICT SYNTAX RULES:
1. Use ONLY alphanumeric node identifiers (e.g. NodeA, NodeB, Step1, Step2). NEVER use spaces, hyphens, colons, slashes, or brackets in the node identifier itself.
2. Put all display text inside square brackets [like this] or rounded brackets (like this).
3. Do NOT use special characters or punctuation inside the node ID.
4. Keep the graph clean and valid with either 'graph TD' (top-down) or 'graph LR' (left-right).

Return valid JSON with exactly 4 diagrams matching the domain ({domain_key}):
{{
  "diagrams": [
    {{
      "title": "Diagram 1 Title (e.g., Structural Load Flow / System Architecture / Process Schematic)",
      "type": "mermaid",
      "definition": "graph TD\\n  A[Step 1] --> B[Step 2]\\n  B --> C[Step 3]\\n  C --> D[Step 4]"
    }},
    {{
      "title": "Diagram 2 Title (e.g., Execution Sequence / Data Flow / Operational Cycle)",
      "type": "mermaid",
      "definition": "graph TD\\n  A[Stage 1] --> B[Stage 2]\\n  B --> C[Stage 3]"
    }},
    {{
      "title": "Diagram 3 Title (e.g., Material Testing Workflow / Signal Pipeline / Value Chain)",
      "type": "mermaid",
      "definition": "graph LR\\n  Input[Input Artifacts] --> Process[Analysis & Quality Check]\\n  Process --> Verification[Standard Verification]\\n  Verification --> Output[Deliverable]"
    }},
    {{
      "title": "Diagram 4 Title (e.g., Component Model / Site Layout / Governance Hierarchy)",
      "type": "mermaid",
      "definition": "graph TD\\n  Tier1[Primary Level] --> Tier2[Secondary Level]\\n  Tier2 --> Tier3[Detailed Unit]"
    }}
  ]
}}
"""


def validation_prompt(context: str, report: dict) -> str:
    return f"""
{context}

Validate this generated academic report against the student's project specifications and empirical files:
{report}

Return strict JSON:
{{
  "score": 85-100,
  "warnings": ["specific check or improvement note..."],
  "summary": "Academic assessment of structural consistency, domain compliance, and curriculum alignment."
}}
Verify factual grounding, domain appropriateness, and academic formatting integrity.
"""
