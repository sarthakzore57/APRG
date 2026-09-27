from io import BytesIO

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.image.image import Image
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from app.services.storage import StorageService


class DocxReportWriter:
    def __init__(self) -> None:
        self.storage = StorageService()

    def build(self, project, report: dict, diagrams: list[dict], screenshots: list, validation: dict) -> tuple[str, int]:
        doc = Document()
        self._configure_document(doc, project)
        self._add_cover_page(doc, project)
        self._add_certificate_page(doc, project)
        self._add_acknowledgement_page(doc, project)

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
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    table.style = "Table Grid"
                    for cell, header in zip(table.rows[0].cells, headers):
                        cell.text = str(header)
                        self._style_cell(cell, bold=True)
                    for row in rows:
                        cells = table.add_row().cells
                        for cell, value in zip(cells, row):
                            cell.text = str(value)
                            self._style_cell(cell)
                    self._set_table_borders(table)
                    caption = doc.add_paragraph(table_data.get("title", "Table"))
                    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if diagrams:
            doc.add_heading("Figures and Diagrams", 1)
            for idx, diagram in enumerate(diagrams, start=1):
                path = self.storage.path_for(diagram["storage_key"])
                self._add_fitted_picture(doc, path, max_width=6.1, max_height=6.8)
                caption = doc.add_paragraph(f"Figure {idx}: {diagram['title']}")
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if screenshots:
            doc.add_heading("Project Screenshots", 1)
            offset = len(diagrams)
            for idx, file in enumerate(screenshots, start=1):
                path = self.storage.path_for(file.storage_key)
                self._add_fitted_picture(doc, path, max_width=6.1, max_height=6.8)
                caption = doc.add_paragraph(f"Figure {offset + idx}: {file.original_name}")
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

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

    def _configure_document(self, doc: Document, project) -> None:
        section = doc.sections[0]
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
        section.header.paragraphs[0].text = project.title
        section.footer.paragraphs[0].text = "AI Project Report Generator"

        normal = doc.styles["Normal"]
        normal.font.name = "Times New Roman"
        normal.font.size = Pt(12)
        normal.font.color.rgb = RGBColor(0, 0, 0)
        for style_name in ["Title", "Heading 1", "Heading 2", "Heading 3"]:
            style = doc.styles[style_name]
            style.font.name = "Times New Roman"
            style.font.color.rgb = RGBColor(0, 0, 0)
        doc.styles["Heading 1"].font.size = Pt(16)
        doc.styles["Heading 2"].font.size = Pt(14)

    def _add_cover_page(self, doc: Document, project) -> None:
        self._centered(doc, project.college or "College Name", size=15, bold=True)
        self._centered(doc, project.branch or "Department", size=13)
        doc.add_paragraph()
        self._centered(doc, "A PROJECT REPORT", size=14, bold=True)
        self._centered(doc, "ON", size=12, bold=True)
        title = self._centered(doc, project.title, size=18, bold=True)
        title.paragraph_format.space_before = Pt(8)
        title.paragraph_format.space_after = Pt(14)
        self._centered(doc, "Submitted in partial fulfilment of the academic requirements", size=11)
        if project.academic_year:
            self._centered(doc, f"Academic Year: {project.academic_year}", size=11)
        doc.add_paragraph()
        self._centered(doc, "Submitted By", size=12, bold=True)
        self._centered(doc, project.student_details or "Student Name", size=12)
        doc.add_paragraph()
        self._centered(doc, "Under the Guidance of", size=12, bold=True)
        self._centered(doc, project.guide or "Project Guide", size=12)
        doc.add_paragraph()
        self._centered(doc, "AI Project Report Generator", size=10)
        doc.add_page_break()

    def _add_certificate_page(self, doc: Document, project) -> None:
        self._centered(doc, "Certificate", size=16, bold=True)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.add_run(
            f"This is to certify that the project report titled '{project.title}' has been prepared by "
            f"{project.student_details or 'the student'} under the guidance of "
            f"{project.guide or 'the project guide'}. The work presented in this report is submitted "
            "as part of the academic project requirements and has been reviewed for documentation purpose."
        )
        doc.add_paragraph()
        doc.add_paragraph()
        table = doc.add_table(rows=2, cols=3)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        labels = ["Project Guide", "Head of Department", "External Examiner"]
        for idx, label in enumerate(labels):
            table.cell(0, idx).text = "____________________"
            table.cell(1, idx).text = label
            for cell in [table.cell(0, idx), table.cell(1, idx)]:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()

    def _add_acknowledgement_page(self, doc: Document, project) -> None:
        self._centered(doc, "Acknowledgement", size=16, bold=True)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.add_run(
            f"I express my sincere gratitude to {project.guide or 'my project guide'} for valuable guidance, "
            "continuous support, and constructive suggestions throughout the development of this project. "
            f"I am also thankful to {project.college or 'the institution'} and the "
            f"{project.branch or 'department'} for providing the required academic support and resources. "
            "I would like to thank all faculty members, friends, and contributors who helped in completing "
            "this project report successfully."
        )
        doc.add_page_break()

    def _centered(self, doc: Document, text: str, size: int = 12, bold: bool = False):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(text)
        run.bold = bold
        run.font.name = "Times New Roman"
        run.font.size = Pt(size)
        run.font.color.rgb = RGBColor(0, 0, 0)
        return paragraph

    def _style_cell(self, cell, bold: bool = False) -> None:
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = bold
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor(0, 0, 0)

    def _set_table_borders(self, table) -> None:
        tbl = table._tbl
        tbl_pr = tbl.tblPr
        borders = tbl_pr.first_child_found_in("w:tblBorders")
        if borders is None:
            borders = OxmlElement("w:tblBorders")
            tbl_pr.append(borders)
        for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            tag = f"w:{edge}"
            element = borders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                borders.append(element)
            element.set(qn("w:val"), "single")
            element.set(qn("w:sz"), "8")
            element.set(qn("w:space"), "0")
            element.set(qn("w:color"), "000000")

    def _add_fitted_picture(self, doc: Document, path, max_width: float, max_height: float) -> None:
        # python-docx accepts a string filename or a seekable binary stream. A
        # pathlib.Path is neither on Windows, so passing it directly makes the
        # library call ``seek`` on WindowsPath and abort report generation.
        image = Image.from_file(str(path))
        width = image.px_width / (image.horz_dpi or 96)
        height = image.px_height / (image.vert_dpi or 96)
        scale = min(max_width / width, max_height / height, 1.0)
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_picture(str(path), width=Inches(width * scale), height=Inches(height * scale))
