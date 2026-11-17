import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def generate_excel_bytes(
    rows: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    report_title: str,
    scope_summary: str,
    start_date: str,
    end_date: str,
    organization_name: str = "AttendAI Global Technologies",
    split_by_department: bool = False
) -> bytes:
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styles
    title_font = Font(name="Segoe UI", size=15, bold=True, color="1E3A8A")
    meta_label_font = Font(name="Segoe UI", size=9, bold=True, color="475569")
    meta_val_font = Font(name="Segoe UI", size=9, color="1E293B")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=9, color="0F172A")
    summary_stat_font = Font(name="Segoe UI", size=16, bold=True, color="2563EB")

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    summary_box_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color="E2E8F0"),
        right=Side(style='thin', color="E2E8F0"),
        top=Side(style='thin', color="E2E8F0"),
        bottom=Side(style='thin', color="E2E8F0")
    )

    # -------------------------------------------------------------
    # 1. Summary Worksheet
    # -------------------------------------------------------------
    ws_sum = wb.create_sheet(title="Report Summary")
    ws_sum.views.sheetView[0].showGridLines = True

    ws_sum["A1"] = organization_name
    ws_sum["A1"].font = Font(name="Segoe UI", size=10, bold=True, color="64748B")
    ws_sum["A2"] = report_title
    ws_sum["A2"].font = title_font

    ws_sum["A4"] = "Scope:"
    ws_sum["A4"].font = meta_label_font
    ws_sum["B4"] = scope_summary
    ws_sum["B4"].font = meta_val_font

    ws_sum["A5"] = "Period:"
    ws_sum["A5"].font = meta_label_font
    ws_sum["B5"] = f"{start_date} to {end_date}"
    ws_sum["B5"].font = meta_val_font

    ws_sum["A6"] = "Generated:"
    ws_sum["A6"].font = meta_label_font
    ws_sum["B6"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws_sum["B6"].font = meta_val_font

    # Summary KPI boxes
    unique_emps = len(set(r.get("employee_code", "") for r in rows if r.get("employee_code")))
    unique_depts = len(set(r.get("department", "") for r in rows if r.get("department")))

    kpis = [
        ("Total Records", len(rows), "A8", "B8", "A9", "B9"),
        ("Employees Included", unique_emps or len(rows), "D8", "E8", "D9", "E9"),
        ("Departments Included", unique_depts or 1, "G8", "H8", "G9", "H9")
    ]
    for label, val, top_l, top_r, bot_l, bot_r in kpis:
        ws_sum[top_l] = label
        ws_sum[top_l].font = meta_label_font
        ws_sum[bot_l] = val
        ws_sum[bot_l].font = summary_stat_font

    ws_sum.column_dimensions["A"].width = 22
    ws_sum.column_dimensions["B"].width = 35
    ws_sum.column_dimensions["D"].width = 22
    ws_sum.column_dimensions["E"].width = 15
    ws_sum.column_dimensions["G"].width = 24
    ws_sum.column_dimensions["H"].width = 15

    # -------------------------------------------------------------
    # 2. Helper to populate a data sheet
    # -------------------------------------------------------------
    def populate_data_sheet(sheet, sheet_rows, sheet_title):
        sheet.views.sheetView[0].showGridLines = True

        # Sheet header
        sheet["A1"] = f"{report_title} — {sheet_title}"
        sheet["A1"].font = Font(name="Segoe UI", size=12, bold=True, color="1E3A8A")
        sheet["A2"] = f"Period: {start_date} to {end_date} | Records: {len(sheet_rows)}"
        sheet["A2"].font = Font(name="Segoe UI", size=8.5, color="64748B")

        # Table headers on row 4
        headers = [col["label"] for col in columns]
        col_ids = [col["id"] for col in columns]

        for col_idx, h_text in enumerate(headers, 1):
            cell = sheet.cell(row=4, column=col_idx, value=h_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.border = thin_border
            sheet.row_dimensions[4].height = 24

        # Table data rows
        for row_idx, r in enumerate(sheet_rows, start=5):
            is_alt = (row_idx % 2 == 0)
            sheet.row_dimensions[row_idx].height = 19
            for col_idx, cid in enumerate(col_ids, 1):
                val = r.get(cid, "-")
                cell = sheet.cell(row=row_idx, column=col_idx, value=val)
                cell.font = data_font
                cell.border = thin_border
                if is_alt:
                    cell.fill = alt_fill

                # Alignment based on data type
                if isinstance(val, (int, float)):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Auto-adjust column widths
        for col_idx, cid in enumerate(col_ids, 1):
            col_letter = get_column_letter(col_idx)
            header_len = len(headers[col_idx - 1])
            max_len = header_len
            for r in sheet_rows[:50]:
                val_str = str(r.get(cid, ""))
                if len(val_str) > max_len:
                    max_len = len(val_str)
            sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

        # Freeze panes at A5 (data starts on row 5)
        sheet.freeze_panes = "A5"
        # Auto-filter
        last_col = get_column_letter(len(headers))
        sheet.auto_filter.ref = f"A4:{last_col}{max(4, len(sheet_rows) + 4)}"

    # Create Main Records Sheet
    ws_main = wb.create_sheet(title="All Records")
    populate_data_sheet(ws_main, rows, "All Data")

    # If split by department and multiple departments exist
    depts = sorted(list(set(r.get("department") for r in rows if r.get("department"))))
    if len(depts) > 1 and len(rows) > 0 and len(depts) <= 15:
        for d in depts:
            clean_title = d.replace("/", "-").replace("\\", "-")[:30]
            dept_rows = [r for r in rows if r.get("department") == d]
            ws_dept = wb.create_sheet(title=clean_title)
            populate_data_sheet(ws_dept, dept_rows, f"Department: {d}")

    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()
