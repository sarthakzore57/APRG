from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches

from app.services.storage import StorageService


class DocxReportWriter:
    def __init__(self) -> None:
        self.storage = StorageService()

    def build(self, project, report: dict, diagrams: list[dict], screenshots: list, validation: dict) -> tuple[str, int]:
        doc = Document()
        section = doc.sections[0]
        section.header.paragraphs[0].text = project.title
        section.footer.paragraphs[0].text = "AI Project Report Generator"

        title = doc.add_heading(project.title, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for line in [project.student_details, project.college, project.branch, f"Guide: {project.guide}", f"Academic Year: {project.academic_year}"]:
            if line:
                p = doc.add_paragraph(line)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()

        doc.add_heading("Certificate", 1)
        doc.add_paragraph(f"This is to certify that the project report titled '{project.title}' was prepared by {project.student_details or 'the student'} under the guidance of {project.guide or 'the project guide'}.")
        doc.add_page_break()

        doc.add_heading("Acknowledgement", 1)
        doc.add_paragraph("The student expresses sincere gratitude to the guide, department, institution, and all contributors for their support throughout the project.")
        doc.add_page_break()

        doc.add_heading("Abstract", 1)
        doc.add_paragraph(project.abstract or "Not provided.")
        doc.add_page_break()

        doc.add_heading("Table of Contents", 1)
        for idx, chapter in enumerate(report.get("chapters", []), start=1):
            doc.add_paragraph(f"{idx}. {chapter.get('title', 'Chapter')}")
        doc.add_page_break()

        for idx, chapter in enumerate(report.get("chapters", []), start=1):
            doc.add_heading(f"{idx}. {chapter.get('title', 'Chapter')}", 1)
            doc.add_paragraph(chapter.get("content", ""))
            for table_data in chapter.get("tables", []) or []:
                headers = table_data.get("headers") or []
                rows = table_data.get("rows") or []
                if headers:
                    table = doc.add_table(rows=1, cols=len(headers))
                    for cell, header in zip(table.rows[0].cells, headers):
                        cell.text = str(header)
                    for row in rows:
                        cells = table.add_row().cells
                        for cell, value in zip(cells, row):
                            cell.text = str(value)
                    doc.add_paragraph(table_data.get("title", "Table"))

        if diagrams:
            doc.add_heading("Figures and Diagrams", 1)
            for idx, diagram in enumerate(diagrams, start=1):
                path = self.storage.path_for(diagram["storage_key"])
                doc.add_picture(str(path), width=Inches(5.8))
                doc.add_paragraph(f"Figure {idx}: {diagram['title']}")

        if screenshots:
            doc.add_heading("Project Screenshots", 1)
            offset = len(diagrams)
            for idx, file in enumerate(screenshots, start=1):
                path = self.storage.path_for(file.storage_key)
                doc.add_picture(str(path), width=Inches(5.8))
                doc.add_paragraph(f"Figure {offset + idx}: {file.original_name}")

        doc.add_heading("AI Validation", 1)
        doc.add_paragraph(f"Consistency score: {validation.get('score', 'Not available')}")
        for warning in validation.get("warnings", []):
            doc.add_paragraph(str(warning), style="List Bullet")

        doc.add_heading("References", 1)
        for ref in report.get("references", []):
            doc.add_paragraph(str(ref), style="List Number")

        buffer = BytesIO()
        doc.save(buffer)
        return self.storage.write_bytes(buffer.getvalue(), "generated/reports", f"{project.title}.docx")
