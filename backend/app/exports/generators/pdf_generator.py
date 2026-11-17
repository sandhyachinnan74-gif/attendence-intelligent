import io
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(self._pagesize[0] - 36, 20, page_text)
        self.drawString(36, 20, "AttendAI — Intelligent Workforce Management • Confidential & Proprietary")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 30, self._pagesize[0] - 36, 30)
        self.restoreState()

def generate_pdf_bytes(
    rows: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    report_title: str,
    scope_summary: str,
    start_date: str,
    end_date: str,
    organization_name: str = "AttendAI Global Technologies"
) -> bytes:
    buffer = io.BytesIO()

    # If more than 5 columns, use landscape orientation
    pagesize = landscape(letter) if len(columns) > 5 else letter
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B')
    )
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155')
    )
    table_header_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        alignment=0
    )
    table_cell_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#0F172A'),
        alignment=0
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph(organization_name.upper(), subtitle_style))
    story.append(Paragraph(report_title, title_style))
    story.append(Spacer(1, 4))
    
    meta_text = f"<b>Period:</b> {start_date} to {end_date} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Scope:</b> {scope_summary} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 10))

    # 2. Executive KPI Summary Block
    unique_emps = len(set(r.get("employee_code", "") for r in rows if r.get("employee_code")))
    unique_depts = len(set(r.get("department", "") for r in rows if r.get("department")))

    kpi_data = [
        [
            Paragraph("<b>Total Records</b>", meta_style),
            Paragraph("<b>Employees</b>", meta_style),
            Paragraph("<b>Departments</b>", meta_style),
            Paragraph("<b>Date Range</b>", meta_style)
        ],
        [
            Paragraph(f"<font size=12 color='#2563EB'><b>{len(rows)}</b></font>", meta_style),
            Paragraph(f"<font size=12 color='#2563EB'><b>{unique_emps or len(rows)}</b></font>", meta_style),
            Paragraph(f"<font size=12 color='#2563EB'><b>{unique_depts or 1}</b></font>", meta_style),
            Paragraph(f"<font size=9><b>{start_date} – {end_date}</b></font>", meta_style)
        ]
    ]
    avail_width = pagesize[0] - 72
    kpi_col_width = avail_width / 4.0
    kpi_table = Table(kpi_data, colWidths=[kpi_col_width]*4)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 3. Main Records Table
    # Limit to first 250 rows in PDF to avoid excessive rendering time/size
    display_rows = rows[:250]
    headers = [Paragraph(col["label"], table_header_style) for col in columns]
    table_data = [headers]

    col_ids = [col["id"] for col in columns]
    for r in display_rows:
        row_cells = []
        for cid in col_ids:
            val = str(r.get(cid, "-"))
            row_cells.append(Paragraph(val, table_cell_style))
        table_data.append(row_cells)

    # Calculate column widths evenly or proportionally
    num_cols = len(columns)
    col_w = avail_width / num_cols
    rec_table = Table(table_data, colWidths=[col_w]*num_cols, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#E2E8F0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]
    # Alternating row background
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F8FAFC')))
    
    rec_table.setStyle(TableStyle(t_style))
    story.append(rec_table)

    if len(rows) > len(display_rows):
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<i>* Note: Showing first {len(display_rows)} of {len(rows)} records in printable PDF. For full unrestricted dataset, please select Excel (.xlsx) or CSV format.</i>", subtitle_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
