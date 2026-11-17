import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import PieChart, BarChart, Reference

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

    # -------------------------------------------------------------
    # Common Styling Definitions
    # -------------------------------------------------------------
    FONT_NAME = "Segoe UI"
    
    # Fonts
    brand_font = Font(name=FONT_NAME, size=9, bold=True, color="2563EB")
    title_font = Font(name=FONT_NAME, size=16, bold=True, color="0F172A")
    subtitle_font = Font(name=FONT_NAME, size=9.5, italic=True, color="64748B")
    
    card_title_font = Font(name=FONT_NAME, size=8.5, bold=True, color="475569")
    card_val_font = Font(name=FONT_NAME, size=16, bold=True, color="1E3A8A")
    card_sub_font = Font(name=FONT_NAME, size=8, color="64748B")
    
    meta_head_font = Font(name=FONT_NAME, size=9, bold=True, color="1E3A8A")
    meta_label_font = Font(name=FONT_NAME, size=8.5, bold=True, color="475569")
    meta_val_font = Font(name=FONT_NAME, size=8.5, color="0F172A")
    
    table_header_font = Font(name=FONT_NAME, size=9.5, bold=True, color="FFFFFF")
    data_font = Font(name=FONT_NAME, size=9, color="1E293B")
    total_font = Font(name=FONT_NAME, size=9.5, bold=True, color="0F172A")
    
    # Fills
    navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    card_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    card_header_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
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
        "resolved": {
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
        "pending review": {
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
    card_border = Border(
        left=Side(style='thin', color="CBD5E1"),
        right=Side(style='thin', color="CBD5E1"),
        top=Side(style='thin', color="CBD5E1"),
        bottom=Side(style='thin', color="CBD5E1")
    )
    total_border = Border(
        top=Side(style='thin', color="1E3A8A"),
        bottom=Side(style='double', color="1E3A8A")
    )

    # -------------------------------------------------------------
    # Compute Authoritative Summary Aggregates
    # -------------------------------------------------------------
    total_records = len(rows)
    unique_emps = set(r.get("employee_code") for r in rows if r.get("employee_code"))
    unique_depts = set(r.get("department") for r in rows if r.get("department"))
    
    # Attendance specific metrics
    status_counts = {"Present": 0, "Late": 0, "Absent": 0, "Half Day": 0}
    status_hours = {"Present": 0.0, "Late": 0.0, "Absent": 0.0, "Half Day": 0.0}
    total_worked_hours = 0.0
    total_ot_hours = 0.0
    total_late_minutes = 0
    
    # Leave specific metrics
    leave_status_counts = {"Approved": 0, "Pending": 0, "Rejected": 0}
    leave_type_counts = {}
    leave_total_days = 0.0
    
    is_leave_report = "leave" in report_type.lower()
    is_anomaly_report = "anomaly" in report_type.lower()
    is_shift_report = "shift" in report_type.lower()
    
    for r in rows:
        # Attendance metrics
        st_raw = str(r.get("status", "")).strip().lower()
        if "present" in st_raw:
            status_counts["Present"] += 1
            st_key = "Present"
        elif "late" in st_raw:
            status_counts["Late"] += 1
            st_key = "Late"
        elif "absent" in st_raw:
            status_counts["Absent"] += 1
            st_key = "Absent"
        elif "half" in st_raw:
            status_counts["Half Day"] += 1
            st_key = "Half Day"
        else:
            st_key = None
            
        try:
            wh = float(r.get("worked_hours") or r.get("total_hours") or 0.0)
            total_worked_hours += wh
            if st_key:
                status_hours[st_key] += wh
        except (ValueError, TypeError):
            pass
            
        try:
            ot = float(r.get("overtime_hours") or 0.0)
            total_ot_hours += ot
        except (ValueError, TypeError):
            pass
            
        try:
            lm = int(r.get("late_minutes") or 0)
            total_late_minutes += lm
        except (ValueError, TypeError):
            pass

        # Leave metrics
        if is_leave_report:
            l_st = str(r.get("status", "")).capitalize()
            if l_st in leave_status_counts:
                leave_status_counts[l_st] += 1
            try:
                days = float(r.get("days_count") or 0.0)
                leave_total_days += days
            except (ValueError, TypeError):
                pass
            lt = str(r.get("leave_type", "General")).capitalize()
            leave_type_counts[lt] = leave_type_counts.get(lt, 0) + 1

    present_workdays = status_counts["Present"] + status_counts["Late"] + status_counts["Half Day"]
    avg_daily_hours = round(total_worked_hours / present_workdays, 1) if present_workdays > 0 else 0.0
    punctuality_rate = round((status_counts["Present"] / present_workdays) * 100, 1) if present_workdays > 0 else 100.0

    # -------------------------------------------------------------
    # 1. REPORT SUMMARY SHEET (Cover & Executive Dashboard)
    # -------------------------------------------------------------
    ws_sum = wb.create_sheet(title="Report Summary")
    ws_sum.views.sheetView[0].showGridLines = True

    # 1.1 Header Banner
    ws_sum["A1"] = f"{organization_name.upper()} • ENTERPRISE WORKFORCE AUDIT"
    ws_sum["A1"].font = brand_font
    
    ws_sum["A2"] = report_title
    ws_sum["A2"].font = title_font
    ws_sum.row_dimensions[2].height = 24
    
    ws_sum["A3"] = "Official Workforce Analytics, Punctuality Records, and Compliance Report"
    ws_sum["A3"].font = subtitle_font
    ws_sum.row_dimensions[3].height = 18

    # 1.2 Two-Column Metadata Card
    # Left Card: Report Scope (Cols A to C)
    ws_sum["A5"] = "REPORT SPECIFICATIONS"
    ws_sum["A5"].font = meta_head_font
    
    spec_rows = [
        ("Organization", organization_name),
        ("Report Scope", scope_summary),
        ("Reporting Period", f"{start_date} to {end_date}"),
        ("Audit Classification", "Production Verified Records")
    ]
    for idx, (label, val) in enumerate(spec_rows, start=6):
        ws_sum[f"A{idx}"] = label
        ws_sum[f"A{idx}"].font = meta_label_font
        ws_sum[f"B{idx}"] = val
        ws_sum[f"B{idx}"].font = meta_val_font

    # Right Card: Generation Details (Cols E to G)
    ws_sum["E5"] = "GENERATION & SECURITY AUDIT"
    ws_sum["E5"].font = meta_head_font
    
    audit_rows = [
        ("Generated Date/Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Generated By", generated_by),
        ("System Architecture", "AttendAI Core Engine v2.4"),
        ("Access Authorization", "Role-Scoped RBAC Enforced")
    ]
    for idx, (label, val) in enumerate(audit_rows, start=6):
        ws_sum[f"E{idx}"] = label
        ws_sum[f"E{idx}"].font = meta_label_font
        ws_sum[f"F{idx}"] = val
        ws_sum[f"F{idx}"].font = meta_val_font

    # 1.3 Executive KPI Dashboard Cards (Row 11 to 14)
    if is_leave_report:
        kpi_defs = [
            ("TOTAL APPLICATIONS", str(total_records), "Filed in period", "A", "B"),
            ("APPROVED LEAVE DAYS", f"{leave_total_days:.1f} days", "Authorized time off", "C", "D"),
            ("PENDING REQUESTS", str(leave_status_counts.get("Pending", 0)), "Awaiting review", "E", "F"),
            ("EMPLOYEES ON LEAVE", str(len(unique_emps) or 1), "Unique team members", "G", "H")
        ]
    else:
        kpi_defs = [
            ("TOTAL RECORDS", str(total_records), "Logged punches", "A", "B"),
            ("PRESENT DAYS", str(status_counts["Present"]), f"{round((status_counts['Present']/max(1, total_records))*100, 1)}% attendance", "C", "D"),
            ("LATE ARRIVALS", str(status_counts["Late"]), f"{total_late_minutes} tardy mins", "E", "F"),
            ("ABSENT DAYS", str(status_counts["Absent"]), "Unscheduled", "G", "H"),
            ("WORKED HOURS", f"{total_worked_hours:.1f} hrs", "Productive duration", "A", "B", 15),
            ("OVERTIME HOURS", f"{total_ot_hours:.1f} hrs", "Beyond shift", "C", "D", 15),
            ("AVG DAILY HOURS", f"{avg_daily_hours:.1f} hrs", "Per present shift", "E", "F", 15),
            ("PUNCTUALITY RATE", f"{punctuality_rate:.1f}%", "On-time arrival index", "G", "H", 15)
        ]

    for kpi in kpi_defs:
        label = kpi[0]
        val = kpi[1]
        sub = kpi[2]
        col1 = kpi[3]
        col2 = kpi[4]
        start_row = kpi[5] if len(kpi) > 5 else 11
        
        # Merge col1 and col2 for card
        ws_sum.merge_cells(f"{col1}{start_row}:{col2}{start_row}")
        ws_sum.merge_cells(f"{col1}{start_row+1}:{col2}{start_row+1}")
        ws_sum.merge_cells(f"{col1}{start_row+2}:{col2}{start_row+2}")
        
        top_cell = ws_sum[f"{col1}{start_row}"]
        top_cell.value = label
        top_cell.font = card_title_font
        top_cell.alignment = Alignment(horizontal="center", vertical="center")
        top_cell.fill = card_header_fill
        
        val_cell = ws_sum[f"{col1}{start_row+1}"]
        val_cell.value = val
        val_cell.font = card_val_font
        val_cell.alignment = Alignment(horizontal="center", vertical="center")
        val_cell.fill = card_fill
        
        sub_cell = ws_sum[f"{col1}{start_row+2}"]
        sub_cell.value = sub
        sub_cell.font = card_sub_font
        sub_cell.alignment = Alignment(horizontal="center", vertical="center")
        sub_cell.fill = card_fill

        # Apply borders to the 3 card rows
        for r_i in range(start_row, start_row + 3):
            for c_letter in [col1, col2]:
                ws_sum[f"{c_letter}{r_i}"].border = card_border

    # Set row heights for KPI cards
    ws_sum.row_dimensions[11].height = 18
    ws_sum.row_dimensions[12].height = 24
    ws_sum.row_dimensions[13].height = 16
    if not is_leave_report:
        ws_sum.row_dimensions[15].height = 18
        ws_sum.row_dimensions[16].height = 24
        ws_sum.row_dimensions[17].height = 16

    # 1.4 Structured Breakdown Table & Embedded Chart
    table_start_row = 20 if not is_leave_report else 16
    ws_sum[f"A{table_start_row}"] = "ATTENDANCE STATUS DISTRIBUTION" if not is_leave_report else "LEAVE APPLICATIONS BREAKDOWN"
    ws_sum[f"A{table_start_row}"].font = meta_head_font
    
    # Breakdown Table Headers
    b_headers = ["Status Category", "Days / Count", "Percentage", "Hours Logged"] if not is_leave_report else ["Leave Status", "Request Count", "Percentage", "Status Flag"]
    for b_idx, bh in enumerate(b_headers, start=1):
        cell = ws_sum.cell(row=table_start_row+1, column=b_idx, value=bh)
        cell.font = table_header_font
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center" if b_idx > 1 else "left", vertical="center")
        cell.border = thin_border
    ws_sum.row_dimensions[table_start_row+1].height = 22

    # Breakdown Table Rows
    curr_r = table_start_row + 2
    if not is_leave_report:
        breakdown_items = [
            ("Present", status_counts["Present"], status_hours["Present"]),
            ("Late Arrival", status_counts["Late"], status_hours["Late"]),
            ("Absent", status_counts["Absent"], status_hours["Absent"]),
            ("Half Day", status_counts["Half Day"], status_hours["Half Day"])
        ]
        for name, count, hrs in breakdown_items:
            pct = round((count / max(1, total_records)) * 100, 1)
            
            c1 = ws_sum.cell(row=curr_r, column=1, value=name)
            c2 = ws_sum.cell(row=curr_r, column=2, value=count)
            c3 = ws_sum.cell(row=curr_r, column=3, value=f"{pct}%")
            c4 = ws_sum.cell(row=curr_r, column=4, value=f"{hrs:.1f} hrs")
            
            for c in [c1, c2, c3, c4]:
                c.font = data_font
                c.border = thin_border
                c.fill = white_fill
            c2.alignment = Alignment(horizontal="right", vertical="center")
            c3.alignment = Alignment(horizontal="right", vertical="center")
            c4.alignment = Alignment(horizontal="right", vertical="center")
            curr_r += 1

        # Total row
        tot_c1 = ws_sum.cell(row=curr_r, column=1, value="Total Period Workdays")
        tot_c2 = ws_sum.cell(row=curr_r, column=2, value=total_records)
        tot_c3 = ws_sum.cell(row=curr_r, column=3, value="100.0%")
        tot_c4 = ws_sum.cell(row=curr_r, column=4, value=f"{total_worked_hours:.1f} hrs")
        for tc in [tot_c1, tot_c2, tot_c3, tot_c4]:
            tc.font = total_font
            tc.border = total_border
        tot_c2.alignment = Alignment(horizontal="right", vertical="center")
        tot_c3.alignment = Alignment(horizontal="right", vertical="center")
        tot_c4.alignment = Alignment(horizontal="right", vertical="center")
    else:
        for name, count in leave_status_counts.items():
            pct = round((count / max(1, total_records)) * 100, 1)
            c1 = ws_sum.cell(row=curr_r, column=1, value=name)
            c2 = ws_sum.cell(row=curr_r, column=2, value=count)
            c3 = ws_sum.cell(row=curr_r, column=3, value=f"{pct}%")
            c4 = ws_sum.cell(row=curr_r, column=4, value=name.upper())
            for c in [c1, c2, c3, c4]:
                c.font = data_font
                c.border = thin_border
            curr_r += 1

    # 1.5 Add OpenPyXL Distribution Chart
    if total_records >= 2:
        try:
            chart = PieChart()
            chart.title = "Attendance Distribution Breakdown" if not is_leave_report else "Leave Status Distribution"
            chart.title.text.font = Font(name=FONT_NAME, size=10, bold=True, color="1E3A8A")
            chart.width = 14
            chart.height = 9.5
            chart.style = 10
            
            # Reference categories and data from the breakdown table
            labels = Reference(ws_sum, min_col=1, min_row=table_start_row+2, max_row=curr_r-1)
            data = Reference(ws_sum, min_col=2, min_row=table_start_row+1, max_row=curr_r-1)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(labels)
            
            # Place chart to the right of the table
            ws_sum.add_chart(chart, f"F{table_start_row}")
        except Exception:
            pass

    # Column Widths on Summary Sheet
    ws_sum.column_dimensions["A"].width = 24
    ws_sum.column_dimensions["B"].width = 22
    ws_sum.column_dimensions["C"].width = 16
    ws_sum.column_dimensions["D"].width = 18
    ws_sum.column_dimensions["E"].width = 22
    ws_sum.column_dimensions["F"].width = 20
    ws_sum.column_dimensions["G"].width = 18
    ws_sum.column_dimensions["H"].width = 18

    # -------------------------------------------------------------
    # 2. DETAIL RECORDS WORKSHEET
    # -------------------------------------------------------------
    detail_sheet_title = "Attendance Details"
    if is_leave_report:
        detail_sheet_title = "Leave Details"
    elif is_anomaly_report:
        detail_sheet_title = "Anomaly Details"
    elif is_shift_report:
        detail_sheet_title = "Shift Details"
    elif "employee" in report_type.lower() and not ("multi" in report_type.lower() or "org" in report_type.lower()):
        detail_sheet_title = "Attendance Details"

    ws_data = wb.create_sheet(title=detail_sheet_title)
    ws_data.views.sheetView[0].showGridLines = True

    # Sheet Header
    ws_data["A1"] = f"{report_title} — Itemized Records"
    ws_data["A1"].font = Font(name=FONT_NAME, size=13, bold=True, color="1E3A8A")
    ws_data["A2"] = f"Scope: {scope_summary} | Period: {start_date} to {end_date} | Total Records: {len(rows)}"
    ws_data["A2"].font = Font(name=FONT_NAME, size=8.5, color="64748B")

    # Table Column Headers on Row 4
    headers = [col["label"] for col in columns]
    col_ids = [col["id"] for col in columns]

    for c_idx, h_text in enumerate(headers, start=1):
        cell = ws_data.cell(row=4, column=c_idx, value=h_text)
        cell.font = table_header_font
        cell.fill = navy_fill
        cell.border = thin_border
        
        # Header alignment matches data type
        cid_lower = col_ids[c_idx - 1].lower()
        if any(k in cid_lower for k in ["hours", "minutes", "count", "rate"]):
            cell.alignment = Alignment(horizontal="right", vertical="center")
        elif any(k in cid_lower for k in ["date", "time", "clock", "status"]):
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_data.row_dimensions[4].height = 26

    # Populate Data Rows starting at Row 5
    for r_idx, row_dict in enumerate(rows, start=5):
        is_even = (r_idx % 2 == 0)
        ws_data.row_dimensions[r_idx].height = 20
        
        for c_idx, cid in enumerate(col_ids, start=1):
            val = row_dict.get(cid, "-")
            cell = ws_data.cell(row=r_idx, column=c_idx)
            cell.font = data_font
            cell.border = thin_border
            cell.fill = zebra_fill if is_even else white_fill
            
            cid_lower = cid.lower()
            
            # Format and align based on column field
            if "status" in cid_lower:
                cell.value = str(val) if val is not None else "-"
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Check for badge styling
                st_match = str(val).strip().lower()
                matched_style = None
                for k, v in status_styles.items():
                    if k in st_match:
                        matched_style = v
                        break
                if matched_style:
                    cell.font = matched_style["font"]
                    cell.fill = matched_style["fill"]
                    
            elif any(k in cid_lower for k in ["date", "joining"]):
                cell.value = str(val) if val is not None else "-"
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
            elif any(k in cid_lower for k in ["clock_in", "clock_out", "time", "start", "end"]):
                cell.value = str(val) if val is not None else "-"
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
            elif any(k in cid_lower for k in ["worked_hours", "overtime_hours", "regular_hours", "total_hours", "days_count"]):
                try:
                    num_val = float(val)
                    cell.value = num_val
                    cell.number_format = '#,##0.00'
                except (ValueError, TypeError):
                    cell.value = val
                cell.alignment = Alignment(horizontal="right", vertical="center")
                
            elif any(k in cid_lower for k in ["late_minutes", "break_duration", "token_count"]):
                try:
                    num_val = int(val)
                    cell.value = num_val
                    cell.number_format = '#,##0'
                except (ValueError, TypeError):
                    cell.value = val
                cell.alignment = Alignment(horizontal="right", vertical="center")
                
            else:
                cell.value = val if val is not None else "-"
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Bottom Summary / Total Row
    total_row_idx = len(rows) + 5
    if len(rows) > 0:
        ws_data.row_dimensions[total_row_idx].height = 22
        first_cell = ws_data.cell(row=total_row_idx, column=1, value="Total / Average Summary")
        first_cell.font = total_font
        first_cell.border = total_border
        
        for c_idx, cid in enumerate(col_ids, start=1):
            cell = ws_data.cell(row=total_row_idx, column=c_idx)
            cell.border = total_border
            cell.font = total_font
            cid_lower = cid.lower()
            col_letter = get_column_letter(c_idx)
            
            if any(k in cid_lower for k in ["worked_hours", "overtime_hours", "regular_hours", "total_hours", "days_count"]):
                cell.value = f"=SUM({col_letter}5:{col_letter}{total_row_idx-1})"
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif any(k in cid_lower for k in ["late_minutes"]):
                cell.value = f"=SUM({col_letter}5:{col_letter}{total_row_idx-1})"
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right", vertical="center")

    # Freeze Header Pane at row 5
    ws_data.freeze_panes = "A5"
    
    # Auto-filter
    if len(headers) > 0:
        last_col = get_column_letter(len(headers))
        ws_data.auto_filter.ref = f"A4:{last_col}{max(4, len(rows) + 4)}"

    # Auto-adjust column widths
    for c_idx, cid in enumerate(col_ids, start=1):
        c_letter = get_column_letter(c_idx)
        h_len = len(str(headers[c_idx - 1]))
        max_len = h_len
        for r in rows[:75]:
            v_str = str(r.get(cid, ""))
            if len(v_str) > max_len:
                max_len = len(v_str)
        ws_data.column_dimensions[c_letter].width = min(max(max_len + 5, 13), 42)

    # Print Setup for Details Sheet
    ws_data.page_setup.orientation = ws_data.ORIENTATION_LANDSCAPE
    ws_data.page_setup.paperSize = ws_data.PAPERSIZE_LETTER
    ws_data.page_setup.fitToWidth = 1
    ws_data.page_setup.fitToHeight = 0
    ws_data.sheet_properties.pageSetUpPr.fitToPage = True
    ws_data.print_title_rows = "4:4"

    # -------------------------------------------------------------
    # 3. DEPARTMENT BREAKDOWN SHEET (If multiple departments exist)
    # -------------------------------------------------------------
    depts_list = sorted(list(set(str(r.get("department")) for r in rows if r.get("department"))))
    if not is_leave_report and len(depts_list) > 1 and len(rows) > 0 and len(depts_list) <= 20:
        ws_dept = wb.create_sheet(title="Department Summary")
        ws_dept.views.sheetView[0].showGridLines = True
        
        ws_dept["A1"] = f"{report_title} — Departmental Summary"
        ws_dept["A1"].font = Font(name=FONT_NAME, size=13, bold=True, color="1E3A8A")
        ws_dept["A2"] = f"Comparative metrics across {len(depts_list)} departments"
        ws_dept["A2"].font = subtitle_font
        
        d_headers = ["Department", "Records", "Employees", "Present", "Late", "Absent", "Worked Hours", "Overtime", "Punctuality %"]
        for d_idx, dh in enumerate(d_headers, start=1):
            cell = ws_dept.cell(row=4, column=d_idx, value=dh)
            cell.font = table_header_font
            cell.fill = navy_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="right" if d_idx > 1 else "left", vertical="center")
        ws_dept.row_dimensions[4].height = 24

        d_row_idx = 5
        for d_name in depts_list:
            d_rows = [r for r in rows if str(r.get("department")) == d_name]
            d_emps = len(set(r.get("employee_code") for r in d_rows if r.get("employee_code"))) or 1
            d_pres = sum(1 for r in d_rows if "present" in str(r.get("status", "")).lower())
            d_late = sum(1 for r in d_rows if "late" in str(r.get("status", "")).lower() or int(r.get("late_minutes") or 0) > 0)
            d_abs = sum(1 for r in d_rows if "absent" in str(r.get("status", "")).lower())
            d_hrs = sum(float(r.get("worked_hours") or r.get("total_hours") or 0.0) for r in d_rows)
            d_ot = sum(float(r.get("overtime_hours") or 0.0) for r in d_rows)
            d_workdays = d_pres + d_late
            d_punc = round((d_pres / max(1, d_workdays)) * 100, 1)

            vals = [d_name, len(d_rows), d_emps, d_pres, d_late, d_abs, round(d_hrs, 1), round(d_ot, 1), f"{d_punc}%"]
            is_ev = (d_row_idx % 2 == 0)
            ws_dept.row_dimensions[d_row_idx].height = 20
            
            for c_i, v in enumerate(vals, start=1):
                c = ws_dept.cell(row=d_row_idx, column=c_i, value=v)
                c.font = data_font
                c.border = thin_border
                c.fill = zebra_fill if is_ev else white_fill
                c.alignment = Alignment(horizontal="right" if c_i > 1 else "left", vertical="center")
            d_row_idx += 1

        # Department Totals
        ws_dept.row_dimensions[d_row_idx].height = 22
        t1 = ws_dept.cell(row=d_row_idx, column=1, value="Organization Total")
        t2 = ws_dept.cell(row=d_row_idx, column=2, value=len(rows))
        t3 = ws_dept.cell(row=d_row_idx, column=3, value=len(unique_emps))
        t4 = ws_dept.cell(row=d_row_idx, column=4, value=status_counts["Present"])
        t5 = ws_dept.cell(row=d_row_idx, column=5, value=status_counts["Late"])
        t6 = ws_dept.cell(row=d_row_idx, column=6, value=status_counts["Absent"])
        t7 = ws_dept.cell(row=d_row_idx, column=7, value=round(total_worked_hours, 1))
        t8 = ws_dept.cell(row=d_row_idx, column=8, value=round(total_ot_hours, 1))
        t9 = ws_dept.cell(row=d_row_idx, column=9, value=f"{punctuality_rate}%")
        
        for tc in [t1, t2, t3, t4, t5, t6, t7, t8, t9]:
            tc.font = total_font
            tc.border = total_border
            tc.alignment = Alignment(horizontal="right" if tc != t1 else "left", vertical="center")

        ws_dept.freeze_panes = "A5"
        ws_dept.auto_filter.ref = f"A4:I{d_row_idx-1}"
        for col_idx in range(1, 10):
            ws_dept.column_dimensions[get_column_letter(col_idx)].width = 18

        # Add Department Hours Bar Chart
        if len(depts_list) >= 2:
            try:
                b_chart = BarChart()
                b_chart.type = "col"
                b_chart.style = 10
                b_chart.title = "Total Worked Hours by Department"
                b_chart.y_axis.title = "Hours Logged"
                b_chart.x_axis.title = "Department"
                b_chart.width = 16
                b_chart.height = 10
                
                b_data = Reference(ws_dept, min_col=7, min_row=4, max_row=d_row_idx-1)
                b_cats = Reference(ws_dept, min_col=1, min_row=5, max_row=d_row_idx-1)
                b_chart.add_data(b_data, titles_from_data=True)
                b_chart.set_categories(b_cats)
                b_chart.legend = None
                ws_dept.add_chart(b_chart, "K4")
            except Exception:
                pass

    # Save to buffer
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()
