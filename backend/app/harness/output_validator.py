import re
import json
from typing import Dict, Any, List, Optional

class OutputValidator:
    """
    Ensures high-fidelity enterprise presentation:
    1. Eliminates raw JSON, Python dicts, and technical traces.
    2. Converts raw structured data into professional Markdown tables, summaries, and observations.
    3. Formats authoritative citations for database records and policy documents (never for errors).
    4. Generates contextual follow-up prompts.
    """

    @classmethod
    def validate_and_format(
        cls,
        raw_text: str,
        tool_results: List[Dict[str, Any]],
        role: str
    ) -> Dict[str, Any]:
        citations = cls._extract_citations(tool_results)
        cleaned_text = cls._remove_raw_json_and_format(raw_text, tool_results)
        follow_up_prompts = cls._generate_follow_up_prompts(tool_results, role)

        # Grounded only if verified citations exist or query didn't require external data
        is_grounded = len(citations) > 0 and not any("error" in tr.get("output", {}) for tr in tool_results)

        return {
            "validated_text": cleaned_text,
            "citations": citations,
            "follow_ups": follow_up_prompts,
            "is_grounded": is_grounded
        }

    @classmethod
    def _extract_citations(cls, tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        for tr in tool_results:
            tool_name = tr.get("tool_name", "")
            output = tr.get("output", {})

            # CRITICAL: Never create citations for failed or permission-denied tools!
            if not isinstance(output, dict) or "error" in output:
                continue

            if tool_name == "search_attendance_policy":
                matches = output.get("matches", [])
                for m in matches:
                    citations.append({
                        "source": m.get("citation", "Company Policy Document"),
                        "page": m.get("page_number"),
                        "section": m.get("section"),
                        "type": "policy_document"
                    })
            else:
                # Clean readable label
                clean_name = (
                    tool_name.replace("query_workforce_", "")
                    .replace("query_", "")
                    .replace("get_my_", "Personal ")
                    .replace("get_", "")
                    .replace("_", " ")
                    .title()
                )
                citations.append({
                    "source": f"PostgreSQL Database ({clean_name})",
                    "type": "database_record"
                })
        return citations

    @classmethod
    def _remove_raw_json_and_format(cls, text: str, tool_results: List[Dict[str, Any]]) -> str:
        """
        Inspects if text contains unparsed JSON or raw Python dictionary representations,
        and replaces it with an elegant enterprise markdown layout.
        """
        # If any tool returned an authorization error, ensure the user sees the explicit warning
        error_tools = [tr for tr in tool_results if isinstance(tr.get("output"), dict) and "error" in tr["output"]]
        if error_tools:
            err_md = "\n\n".join(cls._format_parsed_json_to_markdown(tr["output"]) for tr in error_tools)
            if not text or not text.strip() or not any(k in text.lower() for k in ["permission denied", "authorization"]):
                return err_md

        if not text or not text.strip():
            if tool_results:
                return cls._synthesize_tool_results_to_markdown(tool_results)
            return "No records were found matching your criteria in the verified workforce database."

        stripped = text.strip()

        # Check if the text is entirely a JSON object or array
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            try:
                parsed = json.loads(stripped)
                return cls._format_parsed_json_to_markdown(parsed)
            except Exception:
                pass

        # Check if the text contains a raw JSON dump
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(pattern, text)
        if match:
            matched_str = match.group(0)
            if any(k in matched_str for k in [
                '"window_days"', '"late_arrivals"', '"top_overtime_employees"',
                '"attendance"', '"departments"', '"anomalies"', '"absent_employees"',
                '"total_overtime_hours"', '"leave_balances"', '"shifts"', '"employees"'
            ]):
                try:
                    parsed = json.loads(matched_str)
                    formatted_table = cls._format_parsed_json_to_markdown(parsed)
                    prefix = text[:match.start()].strip()
                    prefix = re.sub(r'Based on verified database records:\s*', '', prefix, flags=re.IGNORECASE).strip()
                    if prefix:
                        return f"{prefix}\n\n{formatted_table}"
                    return formatted_table
                except Exception:
                    pass

        # Strip technical execution remnants if any
        cleaned = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL)
        cleaned = re.sub(r'`\{.*?Tool:.*?`', '', cleaned)
        return cleaned.strip()

    @classmethod
    def _format_parsed_json_to_markdown(cls, data: Any) -> str:
        """Converts structured dictionaries into clean Markdown tables and summaries."""
        if not isinstance(data, dict):
            return str(data)

        # 0. Authorization Boundary / Tool Failure
        if "error" in data:
            return f"⚠️ **Authorization & Scope Boundary**\n\n{data['error']}\n\n*If you believe you should have access to this information, please contact your Organization Administrator or HR Department.*"

        sections = []

        # 1. Personal Overtime (get_my_overtime)
        if "total_overtime_hours" in data and "overtime_records" in data:
            sections.append(f"### Personal Overtime Record")
            sections.append(f"**Period:** {data.get('period', 'This Month')} | **Employee:** **{data.get('employee')}** (`{data.get('employee_code')}`)")
            sections.append(f"**Total Overtime Logged:** **{data.get('total_overtime_hours')} hours** ({data.get('total_overtime_minutes')} minutes across {data.get('overtime_days_count', 0)} days)\n")
            records = data.get("overtime_records", [])
            if records:
                sections.append("| Date | Clock In | Clock Out | Worked Hours | Overtime Hours |")
                sections.append("| :--- | :---: | :---: | :---: | :---: |")
                for r in records[:10]:
                    sections.append(f"| {r.get('date')} | {r.get('clock_in', '-')} | {r.get('clock_out', '-')} | {r.get('worked_hours')}h | **{r.get('overtime_hours')}h** |")
            else:
                sections.append("*No overtime hours logged for this period.*")

        # 2. Personal Late Arrivals (get_my_late_arrivals)
        elif "total_late_count" in data and "late_records" in data:
            sections.append(f"### Personal Punctuality & Late-Arrival Record")
            sections.append(f"**Period:** {data.get('period', 'This Month')} | **Employee:** **{data.get('employee')}** (`{data.get('employee_code')}`)")
            sections.append(f"**Total Late Arrivals:** **{data.get('total_late_count')} times** ({data.get('total_late_minutes', 0)} total minutes late)\n")
            records = data.get("late_records", [])
            if records:
                sections.append("| Date | Clock In | Late Minutes | Status |")
                sections.append("| :--- | :---: | :---: | :---: |")
                for r in records[:10]:
                    sections.append(f"| {r.get('date')} | {r.get('clock_in', '-')} | {r.get('late_minutes')} mins | `{r.get('status')}` |")
            else:
                sections.append("🎉 *Zero late arrivals recorded for this period. Excellent punctuality!*")

        # 3. Personal Working Hours (get_my_working_hours)
        elif "total_worked_hours" in data and "regular_hours" in data and "employee" in data:
            sections.append(f"### Personal Working Hours Summary")
            sections.append(f"**Period:** {data.get('period', 'This Month')} | **Employee:** **{data.get('employee')}** (`{data.get('employee_code')}`)\n")
            sections.append(f"- **Total Hours Logged:** **{data.get('total_worked_hours')} hours**")
            sections.append(f"- **Regular Shift Hours:** {data.get('regular_hours')} hours")
            sections.append(f"- **Overtime Hours:** **{data.get('overtime_hours')} hours**")
            sections.append(f"- **Active Days Worked:** {data.get('logged_days')} days")
            sections.append(f"- **Daily Average:** {data.get('average_hours_per_day')} hours/day")

        # 4. Personal Leave Balances (get_my_leave_balance)
        elif "leave_balances" in data:
            sections.append(f"### Personal Leave Balances & Time-Off Overview")
            sections.append(f"**Employee:** **{data.get('employee')}** (`{data.get('employee_code')}`)\n")
            balances = data.get("leave_balances", {})
            sections.append("| Leave Type | Allocated | Taken | Remaining Balance |")
            sections.append("| :--- | :---: | :---: | :---: |")
            for k, v in balances.items():
                t_name = k.replace("_", " ").title()
                sections.append(f"| **{t_name}** | {v.get('allocated')} days | {v.get('taken')} days | **{v.get('remaining')} days** |")

            requests = data.get("recent_requests", [])
            if requests:
                sections.append("\n#### Recent Leave Applications:")
                sections.append("| Type | Start Date | End Date | Days | Status |")
                sections.append("| :--- | :--- | :--- | :---: | :---: |")
                for req in requests:
                    sections.append(f"| {req.get('leave_type')} | {req.get('start_date')} | {req.get('end_date')} | {req.get('days_count')} | `{req.get('status')}` |")

        # 5. Personal Shift Schedule (get_my_shifts)
        elif "shift_name" in data and "grace_period_minutes" in data:
            sections.append(f"### Assigned Shift Schedule")
            sections.append(f"**Employee:** **{data.get('employee')}**\n")
            sections.append(f"- **Shift Name:** **{data.get('shift_name')}** (`{data.get('shift_code')}`)")
            sections.append(f"- **Scheduled Working Hours:** **{data.get('start_time')} – {data.get('end_time')}** ({data.get('required_hours')} required hours)")
            sections.append(f"- **Grace Period:** **{data.get('grace_period_minutes')} minutes** past shift start before late detection.")

        # 6. Universal Workforce Attendance Queries (query_workforce_attendance)
        elif "query_type" in data:
            q_type = data.get("query_type")
            period = data.get("period", "Selected Period")

            if q_type == "employee_aggregated":
                sections.append(f"### Workforce Hours & Attendance Intelligence")
                sections.append(f"**Period:** {period} | **Total Qualifying Employees:** {data.get('total_qualifying_employees', 0)}\n")
                emps = data.get("employees", [])
                if emps:
                    sections.append("| Employee | Code | Department | Worked Hours | Overtime | Shifts Logged |")
                    sections.append("| :--- | :--- | :--- | :---: | :---: | :---: |")
                    for e in emps[:15]:
                        sections.append(f"| **{e.get('employee')}** | `{e.get('employee_code')}` | {e.get('department')} | **{e.get('total_worked_hours')}h** | {e.get('total_overtime_hours')}h | {e.get('record_count')} |")
                else:
                    sections.append("*No employee records met the specified criteria.*")

            elif q_type == "shift_aggregated":
                sections.append(f"### Shift Attendance & Missing Punch Analysis")
                sections.append(f"**Period:** {period}\n")
                shifts = data.get("shifts", [])
                if shifts:
                    sections.append("| Shift Name | Code | Flagged Occurrences | Sample Employees |")
                    sections.append("| :--- | :---: | :---: | :--- |")
                    for s in shifts:
                        sections.append(f"| **{s.get('shift_name')}** | `{s.get('shift_code')}` | **{s.get('count')}** | {', '.join(s.get('sample_employees', []))} |")
                else:
                    sections.append("✅ *Zero missing clock-outs identified.*")

            elif q_type == "trend_summary":
                s = data.get("summary", {})
                sections.append(f"### Workforce Quarterly Attendance Summary")
                sections.append(f"**Period:** {period}\n")
                sections.append(f"- **Total Operational Shifts:** {s.get('total_logged_shifts')}")
                sections.append(f"- **Overall Punctuality Rate:** **{s.get('overall_punctuality_rate')}%**")
                sections.append(f"- **Total Hours Worked:** {s.get('total_hours_worked')} hours")
                sections.append(f"- **Total Late Arrivals:** {s.get('total_late_arrivals')}\n")
                sections.append(f"#### Trend Analysis:\n{data.get('trend_analysis', '')}")

        # 7. Comparison Metrics (compare_workforce_metrics)
        elif "comparison_type" in data:
            comp_type = data.get("comparison_type")
            if comp_type == "period_comparison":
                sections.append(f"### Comparative Absenteeism & Workforce Analysis")
                sections.append(f"**Baseline:** {data.get('period_b')} ➔ **Comparison:** {data.get('period_a')}\n")
                comps = data.get("comparisons", [])
                if comps:
                    sections.append(f"| Department | Baseline Rate | Current Rate | Delta | Trend |")
                    sections.append(f"| :--- | :---: | :---: | :---: | :---: |")
                    for c in comps:
                        b_rate = c.get(f"rate_{data.get('period_b')}", 0.0)
                        a_rate = c.get(f"rate_{data.get('period_a')}", 0.0)
                        sections.append(f"| **{c.get('department')}** | {b_rate}% | {a_rate}% | {c.get('change_percentage_points'):+}% | {c.get('trend')} |")
                inc = data.get("departments_with_increasing_absenteeism", [])
                if inc:
                    sections.append(f"\n#### Key Observation:\n- Absenteeism increased in: **{', '.join(inc)}**.")
            else:
                sections.append(f"### Cross-Department Attendance Comparison")
                sections.append(f"**Period:** {data.get('period')}\n")
                ranked = data.get("ranked_departments", [])
                if ranked:
                    sections.append("| Department | Attendance Rate | Late Arrivals | Total Shifts |")
                    sections.append("| :--- | :---: | :---: | :---: |")
                    for r in ranked:
                        sections.append(f"| **{r.get('department')}** | **{r.get('attendance_rate')}%** | {r.get('late_arrivals')} | {r.get('total_records')} |")
                if "key_observation" in data:
                    sections.append(f"\n#### Key Observation:\n- {data['key_observation']}")

        # 8. Leave Analytics (query_leave_analytics)
        elif "leave_type" in data and "top_employees" in data:
            sections.append(f"### Workforce Leave Analytics ({data.get('leave_type')} Leave)")
            sections.append(f"**Period:** {data.get('period', 'This Year')} | **Total Employees:** {data.get('total_employees_on_leave', 0)}\n")
            top = data.get("top_employees", [])
            if top:
                sections.append("| Employee | Code | Department | Leave Type | Total Days Taken | Applications |")
                sections.append("| :--- | :--- | :--- | :---: | :---: | :---: |")
                for e in top:
                    sections.append(f"| **{e.get('employee')}** | `{e.get('employee_code')}` | {e.get('department')} | {e.get('leave_type')} | **{e.get('total_days_taken')} days** | {e.get('request_count')} |")
            else:
                sections.append(f"*No employees took {data.get('leave_type')} leave in this period.*")

        # 9. Late Arrivals (get_late_arrivals)
        elif "late_arrivals" in data or ("employees" in data and "threshold_applied" in data):
            period = data.get("period", "Selected Period")
            employees = data.get("employees") or data.get("late_arrivals", [])
            count = data.get("count") or data.get("total_qualifying_employees", len(employees))
            threshold = data.get("threshold_applied")

            sections.append(f"### Workforce Late-Arrival Intelligence")
            sections.append(f"**Period:** {period}")
            if threshold:
                sections.append(f"**Filter Criteria:** Late arrivals {threshold}")
            sections.append(f"**Total Records Identified:** {count}\n")

            if employees:
                sections.append("| Employee | Department | Late Count / Mins | Key Dates |")
                sections.append("| :--- | :--- | :--- | :--- |")
                for e in employees[:15]:
                    name = e.get("employee", "Unknown")
                    dept = e.get("department", "General")
                    count_str = f"{e.get('late_count')} times ({e.get('total_late_minutes', 0)} mins)" if 'late_count' in e else f"{e.get('late_minutes')} mins"
                    dates_str = ", ".join(e.get("dates", [])) if "dates" in e else e.get("date", "-")
                    sections.append(f"| **{name}** | {dept} | {count_str} | {dates_str} |")
            else:
                sections.append("*No employees met the specified late arrival criteria for this period.*")

        # 10. Overtime (get_employee_overtime)
        elif "top_overtime_employees" in data:
            period = data.get("period", "Selected Period")
            total_ot = data.get("total_overtime_hours", 0)
            employees = data.get("top_overtime_employees", [])

            sections.append(f"### Workforce Overtime Intelligence")
            sections.append(f"**Period:** {period} | **Total Accumulated Overtime:** **{total_ot} hours**\n")

            if employees:
                sections.append("| Employee | Code | Department | Overtime Hours | Overtime Days |")
                sections.append("| :--- | :--- | :--- | :---: | :---: |")
                for e in employees[:10]:
                    sections.append(f"| **{e.get('employee')}** | `{e.get('employee_code')}` | {e.get('department')} | **{e.get('overtime_hours')} hrs** | {e.get('overtime_days_count', 1)} |")
            else:
                sections.append("*No overtime hours logged for this period.*")

        # 11. Department Analytics (get_department_analytics)
        elif "departments" in data:
            period = data.get("period", "This Month")
            depts = data.get("departments", [])
            highest_abs = data.get("highest_absenteeism_department", "N/A")

            sections.append(f"### Department Attendance & Absenteeism Analytics")
            sections.append(f"**Period:** {period} | **Highest Absenteeism:** **{highest_abs}**\n")

            sections.append("| Department | Headcount | Attendance Rate | Absenteeism Rate | Overtime | Attention Needed |")
            sections.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
            for d in depts:
                p_rate = f"{d.get('attendance_rate')}%"
                a_rate = f"{d.get('absenteeism_rate')}%"
                ot = f"{d.get('overtime_hours')}h"
                badge = "⚠️ High" if d.get('hr_attention_needed') else "Normal"
                sections.append(f"| **{d.get('department')}** | {d.get('headcount')} | {p_rate} | {a_rate} | {ot} | {badge} |")

        # 12. Absenteeism Roster (get_absenteeism)
        elif "absent_employees" in data:
            period = data.get("period", "Today")
            total = data.get("total_absent_count", 0)
            employees = data.get("absent_employees", [])

            sections.append(f"### Workforce Absenteeism Roster")
            sections.append(f"**Period:** {period} | **Total Absent:** **{total} employees**\n")

            if employees:
                sections.append("| Employee | Code | Department | Status |")
                sections.append("| :--- | :--- | :--- | :--- |")
                for e in employees[:15]:
                    sections.append(f"| **{e.get('employee')}** | `{e.get('employee_code')}` | {e.get('department')} | {e.get('status')} |")
            else:
                sections.append("✅ *100% attendance recorded. No employees are currently absent.*")

        # 13. Compound Workforce Correlations (get_workforce_correlations)
        elif "flagged_employees" in data:
            period = data.get("period", "This Month")
            flagged = data.get("flagged_employees", [])
            sections.append(f"### Compound Workforce Pattern Analysis")
            sections.append(f"**Period:** {period} | **Filter:** {data.get('criteria', '')}")
            sections.append(f"**Flagged Employees:** **{data.get('total_flagged_employees', len(flagged))}**\n")

            if flagged:
                sections.append("| Employee | Department | Late Arrivals | Overtime Hours | Fatigue Risk |")
                sections.append("| :--- | :--- | :---: | :---: | :--- |")
                for f in flagged:
                    sections.append(f"| **{f.get('employee')}** | {f.get('department')} | {f.get('late_arrivals')} | **{f.get('overtime_hours')}h** | {f.get('fatigue_risk_flag', 'High')} |")
            else:
                sections.append("✅ *No employees matched the threshold for combined repeated tardiness and high overtime.*")

        # 14. Fallback formatting
        else:
            sections.append("### Workforce Intelligence Overview")
            for k, v in data.items():
                if isinstance(v, (str, int, float, bool)):
                    sections.append(f"- **{k.replace('_', ' ').title()}:** {v}")

        return "\n".join(sections)

    @classmethod
    def _synthesize_tool_results_to_markdown(cls, tool_results: List[Dict[str, Any]]) -> str:
        parts = []
        for tr in tool_results:
            out = tr.get("output", {})
            parts.append(cls._format_parsed_json_to_markdown(out))
        return "\n\n---\n\n".join(parts)

    @classmethod
    def _generate_follow_up_prompts(cls, tool_results: List[Dict[str, Any]], role: str) -> List[str]:
        suggestions = []
        tool_names = [tr.get("tool_name") for tr in tool_results]

        if role == "employee":
            if "get_my_overtime" in tool_names:
                suggestions.append("What are my working hours this week?")
                suggestions.append("Check my leave balances")
                suggestions.append("What is our overtime policy?")
            elif "get_my_late_arrivals" in tool_names:
                suggestions.append("What is our grace period policy?")
                suggestions.append("Show my assigned shift schedule")
            else:
                suggestions.append("How much overtime did I do this month?")
                suggestions.append("Check my leave balances")
                suggestions.append("What are our core working hours?")
        else:
            if "query_workforce_attendance" in tool_names:
                suggestions.append("Compare attendance between the lowest two departments")
                suggestions.append("Identify departments where absenteeism increased")
                suggestions.append("Which employees took the most sick leave this year?")
            elif "compare_workforce_metrics" in tool_names:
                suggestions.append("Show employees contributing to increased absenteeism")
                suggestions.append("Who worked the most overtime this month?")
            elif "get_late_arrivals" in tool_names:
                suggestions.append("Which employees arrived after 11 today?")
                suggestions.append("Compare late arrivals between Engineering and Sales")
            else:
                suggestions.append("Which employees have worked more than 45 hours this week?")
                suggestions.append("Summarize attendance trends for the previous quarter")
                suggestions.append("Which shifts have the highest missing clock-outs?")

        return suggestions[:3]
