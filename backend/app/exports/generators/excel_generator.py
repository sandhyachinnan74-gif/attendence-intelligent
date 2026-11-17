import io
from datetime import datetime, date
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
    split_by_department: bool = False,
    report_type: str = "attendance",
    generated_by: str = "AttendAI Reporting Engine"
) -> bytes:
    wb = openpyxl.Workbook()
    # Remove initial default sheet
    wb.remove(wb.active)

    FONT_NAME = "Segoe UI"
    
    # Fonts
    title_font = Font(name=FONT_NAME, size=14, bold=True, color="1E3A8A")
    subtitle_font = Font(name=FONT_NAME, size=9, italic=True, color="64748B")
    kpi_label_font = Font(name=FONT_NAME, size=8, bold=True, color="475569")
    kpi_value_font = Font(name=FONT_NAME, size=11, bold=True, color="1E3A8A")
    table_header_font = Font(name=FONT_NAME, size=9.5, bold=True, color="FFFFFF")
    data_font = Font(name=FONT_NAME, size=9, color="1E293B")
    total_font = Font(name=FONT_NAME, size=9.5, bold=True, color="0F172A")
    
    # Fills
    navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    kpi_label_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    kpi_val_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    
    # Status Badge Styles
    status_styles = {
        "present": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="065F46"),
            "fill": PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid"),
        },
        "active": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="065F46"),
            "fill": PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid"),
        },
        "approved": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="065F46"),
            "fill": PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid"),
        },
        "late": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="92400E"),
            "fill": PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid"),
        },
        "pending": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="92400E"),
            "fill": PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid"),
        },
        "absent": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="991B1B"),
            "fill": PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"),
        },
        "inactive": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="991B1B"),
            "fill": PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"),
        },
        "rejected": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="991B1B"),
            "fill": PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"),
        },
        "half day": {
            "font": Font(name=FONT_NAME, size=8.5, bold=True, color="1E40AF"),
            "fill": PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid"),
        }
    }
    
    # Borders
    thin_border = Border(
        left=Side(style='thin', color="E2E8F0"),
        right=Side(style='thin', color="E2E8F0"),
        top=Side(style='thin', color="E2E8F0"),
        bottom=Side(style='thin', color="E2E8F0")
    )
    kpi_border = Border(
        left=Side(style='thin', color="CBD5E1"),
        right=Side(style='thin', color="CBD5E1"),
        top=Side(style='thin', color="CBD5E1"),
        bottom=Side(style='thin', color="CBD5E1")
    )
    total_border = Border(
        top=Side(style='thin', color="1E3A8A"),
        bottom=Side(style='double', color="1E3A8A"),
        left=Side(style='thin', color="E2E8F0"),
        right=Side(style='thin', color="E2E8F0")
    )

    # Ensure 'day' column is present right after 'date' for day-wise attendance
    effective_cols = list(columns)
    col_ids = [c["id"] for c in effective_cols]
    if "date" in col_ids and "day" not in col_ids:
        date_idx = col_ids.index("date")
        effective_cols.insert(date_idx + 1, {"id": "day", "label": "Day"})

    # Ensure every row has 'day' calculated
    for r in rows:
        if not r.get("day") or r.get("day") == "-":
            d_val = r.get("date")
            if d_val:
                try:
                    if isinstance(d_val, (date, datetime)):
                        r["day"] = d_val.strftime("%A")
                    elif isinstance(d_val, str):
                        clean_d = d_val.split("T")[0].split(" ")[0]
                        dt = datetime.strptime(clean_d, "%Y-%m-%d")
                        r["day"] = dt.strftime("%A")
                except Exception:
                    r["day"] = "-"

    # Helper function to build a day-wise sheet
    def build_sheet(sheet_title: str, sheet_rows: List[Dict[str, Any]]):
        ws = wb.create_sheet(title=sheet_title[:31])
        ws.views.sheetView[0].showGridLines = True

        # 1. Header Banner
        ws["A1"] = f"{organization_name} — {report_title}"
        ws["A1"].font = title_font
        ws.row_dimensions[1].height = 24

        ws["A2"] = f"Reporting Period: {start_date} to {end_date}   |   Scope: {scope_summary}   |   Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws["A2"].font = subtitle_font
        ws.row_dimensions[2].height = 18

        # 2. Compute Summary Metrics for the KPI ribbon
        total_rec = len(sheet_rows)
        st_counts = {"Present": 0, "Late": 0, "Absent": 0, "Half Day": 0}
        tot_worked = 0.0
        tot_ot = 0.0
        tot_late = 0

        for sr in sheet_rows:
            st = str(sr.get("status", "")).lower()
            if "present" in st:
                st_counts["Present"] += 1
            elif "late" in st:
                st_counts["Late"] += 1
            elif "absent" in st:
                st_counts["Absent"] += 1
            elif "half" in st:
                st_counts["Half Day"] += 1

            try:
                tot_worked += float(sr.get("worked_hours") or sr.get("total_hours") or 0.0)
            except (ValueError, TypeError):
                pass
            try:
                tot_ot += float(sr.get("overtime_hours") or 0.0)
            except (ValueError, TypeError):
                pass
            try:
                tot_late += int(sr.get("late_minutes") or 0)
            except (ValueError, TypeError):
                pass

        pres_days = st_counts["Present"] + st_counts["Late"] + st_counts["Half Day"]
        avg_daily = round(tot_worked / max(1, pres_days), 1) if pres_days > 0 else 0.0

        # 3. Clean 2-Row KPI Ribbon (Row 4 = Label, Row 5 = Value)
        is_leave = "leave" in report_type.lower()
        if is_leave:
            kpi_cards = [
                ("TOTAL APPLICATIONS", str(total_rec), 1),
                ("APPROVED", str(sum(1 for r in sheet_rows if "approved" in str(r.get("status", "")).lower())), 2),
                ("PENDING", str(sum(1 for r in sheet_rows if "pending" in str(r.get("status", "")).lower())), 3),
                ("REJECTED", str(sum(1 for r in sheet_rows if "rejected" in str(r.get("status", "")).lower())), 4),
            ]
        else:
            kpi_cards = [
                ("TOTAL RECORDS", str(total_rec), 1),
                ("PRESENT DAYS", str(st_counts["Present"]), 2),
                ("LATE ARRIVALS", str(st_counts["Late"]), 3),
                ("ABSENT DAYS", str(st_counts["Absent"]), 4),
                ("WORKED HOURS", f"{tot_worked:.2f}h", 5),
                ("OVERTIME", f"{tot_ot:.2f}h", 6),
                ("AVG DAILY", f"{avg_daily:.1f}h", 7),
            ]

        ws.row_dimensions[4].height = 16
        ws.row_dimensions[5].height = 22

        for label, val, c_idx in kpi_cards:
            lbl_cell = ws.cell(row=4, column=c_idx, value=label)
            lbl_cell.font = kpi_label_font
            lbl_cell.fill = kpi_label_fill
            lbl_cell.alignment = Alignment(horizontal="center", vertical="center")
            lbl_cell.border = kpi_border

            val_cell = ws.cell(row=5, column=c_idx, value=val)
            val_cell.font = kpi_value_font
            val_cell.fill = kpi_val_fill
            val_cell.alignment = Alignment(horizontal="center", vertical="center")
            val_cell.border = kpi_border

        # 4. Table Column Headers on Row 7
        headers = [c["label"] for c in effective_cols]
        c_ids = [c["id"] for c in effective_cols]

        ws.row_dimensions[7].height = 26
        for idx, h_text in enumerate(headers, start=1):
            cell = ws.cell(row=7, column=idx, value=h_text)
            cell.font = table_header_font
            cell.fill = navy_fill
            cell.border = thin_border
            
            cid_l = c_ids[idx - 1].lower()
            if any(k in cid_l for k in ["hours", "minutes", "duration", "count"]):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif any(k in cid_l for k in ["date", "day", "time", "clock", "status"]):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

        # 5. Populate Data Rows starting at Row 8
        worked_col_idx = None
        ot_col_idx = None
        late_col_idx = None

        for c_idx, cid in enumerate(c_ids, start=1):
            cid_l = cid.lower()
            if cid_l in ["worked_hours", "total_hours"]:
                worked_col_idx = c_idx
            elif cid_l == "overtime_hours":
                ot_col_idx = c_idx
            elif cid_l == "late_minutes":
                late_col_idx = c_idx

        for r_idx, row_dict in enumerate(sheet_rows, start=8):
            is_even = (r_idx % 2 == 0)
            ws.row_dimensions[r_idx].height = 20

            for c_idx, cid in enumerate(c_ids, start=1):
                val = row_dict.get(cid, "-")
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.font = data_font
                cell.border = thin_border
                cell.fill = zebra_fill if is_even else white_fill

                cid_l = cid.lower()

                if "status" in cid_l:
                    cell.value = str(val) if val is not None else "-"
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    st_match = str(val).strip().lower()
                    for k, s in status_styles.items():
                        if k in st_match:
                            cell.font = s["font"]
                            cell.fill = s["fill"]
                            break
                elif cid_l in ["date", "day"]:
                    cell.value = str(val) if val is not None else "-"
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif any(k in cid_l for k in ["clock_in", "clock_out", "time", "start", "end"]):
                    cell.value = str(val) if val is not None else "-"
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif any(k in cid_l for k in ["worked_hours", "overtime_hours", "regular_hours", "total_hours"]):
                    try:
                        num = float(val)
                        cell.value = num
                        cell.number_format = '#,##0.00'
                    except (ValueError, TypeError):
                        cell.value = val
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif any(k in cid_l for k in ["late_minutes", "break_duration", "days_count"]):
                    try:
                        num = int(val)
                        cell.value = num
                        cell.number_format = '#,##0'
                    except (ValueError, TypeError):
                        cell.value = val
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.value = str(val) if val is not None else "-"
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # 6. Total Summary Row
        last_data_row = 7 + max(1, len(sheet_rows))
        summary_row = last_data_row + 1
        ws.row_dimensions[summary_row].height = 22

        # Apply total row cells
        for c_idx in range(1, len(c_ids) + 1):
            cell = ws.cell(row=summary_row, column=c_idx)
            cell.font = total_font
            cell.border = total_border
            cell.fill = kpi_label_fill

        ws.cell(row=summary_row, column=1, value="TOTAL / SUMMARY").alignment = Alignment(horizontal="left", vertical="center")

        if len(sheet_rows) > 0:
            if worked_col_idx:
                w_let = get_column_letter(worked_col_idx)
                w_cell = ws.cell(row=summary_row, column=worked_col_idx, value=f"=SUM({w_let}8:{w_let}{last_data_row})")
                w_cell.number_format = '#,##0.00'
                w_cell.alignment = Alignment(horizontal="right", vertical="center")
            if ot_col_idx:
                ot_let = get_column_letter(ot_col_idx)
                ot_cell = ws.cell(row=summary_row, column=ot_col_idx, value=f"=SUM({ot_let}8:{ot_let}{last_data_row})")
                ot_cell.number_format = '#,##0.00'
                ot_cell.alignment = Alignment(horizontal="right", vertical="center")
            if late_col_idx:
                l_let = get_column_letter(late_col_idx)
                l_cell = ws.cell(row=summary_row, column=late_col_idx, value=f"=SUM({l_let}8:{l_let}{last_data_row})")
                l_cell.number_format = '#,##0'
                l_cell.alignment = Alignment(horizontal="right", vertical="center")

        # 7. Freeze Panes below table header & Enable Auto-Filter
        ws.freeze_panes = "A8"
        last_col_let = get_column_letter(len(effective_cols))
        if len(sheet_rows) > 0:
            ws.auto_filter.ref = f"A7:{last_col_let}{last_data_row}"

        # 8. Set Dynamic Column Widths with padding
        for c_idx in range(1, len(effective_cols) + 1):
            col_letter = get_column_letter(c_idx)
            max_len = len(str(headers[c_idx - 1]))
            # Sample up to 100 rows for length
            for r_sample in range(8, min(summary_row + 1, 108)):
                val = ws.cell(row=r_sample, column=c_idx).value
                if val:
                    max_len = max(max_len, len(str(val)))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Build primary sheet
    main_title = "Daily Attendance" if "attendance" in report_type.lower() else "Report Records"
    build_sheet(main_title, rows)

    # Optional: Split by Department tabs for multi-department reports
    if split_by_department and len(rows) > 0:
        depts = sorted(list(set(r.get("department", "General") for r in rows if r.get("department"))))
        if len(depts) > 1:
            for dept_name in depts:
                dept_rows = [r for r in rows if r.get("department") == dept_name]
                if dept_rows:
                    build_sheet(dept_name, dept_rows)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream.getvalue()
