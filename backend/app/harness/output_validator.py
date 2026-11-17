import re
import json
from typing import Dict, Any, List, Optional

class OutputValidator:
    """
    Ensures high-fidelity enterprise presentation:
    1. Eliminates raw JSON, Python dicts, and technical traces.
    2. Converts raw structured data into professional Markdown tables, summaries, and observations.
    3. Formats authoritative citations for database records and policy documents.
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

        return {
            "validated_text": cleaned_text,
            "citations": citations,
            "follow_ups": follow_up_prompts,
            "is_grounded": len(citations) > 0 or len(tool_results) == 0
        }

    @classmethod
    def _extract_citations(cls, tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        for tr in tool_results:
            tool_name = tr.get("tool_name")
            output = tr.get("output", {})
            if tool_name == "search_attendance_policy":
                matches = output.get("matches", [])
                for m in matches:
                    citations.append({
                        "source": m.get("citation", "Company Policy Document"),
                        "page": m.get("page_number"),
                        "section": m.get("section"),
                        "type": "policy_document"
                    })
            elif tool_name in [
                "get_late_arrivals", "get_attendance_summary", "get_employee_overtime",
                "get_my_attendance", "get_absenteeism", "get_department_analytics",
                "get_workforce_correlations", "get_anomaly_reports", "get_employee_profile"
            ]:
                readable_source = tool_name.replace("get_", "").replace("_", " ").title()
                citations.append({
                    "source": f"PostgreSQL Database ({readable_source})",
                    "type": "database_record"
                })
        return citations

    @classmethod
    def _remove_raw_json_and_format(cls, text: str, tool_results: List[Dict[str, Any]]) -> str:
        """
        Inspects if text contains unparsed JSON or raw Python dictionary representations,
        and replaces it with an elegant enterprise markdown layout.
        """
        if not text or not text.strip():
            # If text is empty but we have tool results, synthesize directly
            if tool_results:
                return cls._synthesize_tool_results_to_markdown(tool_results)
            return "No records were found matching your criteria in the verified workforce database."

        stripped = text.strip()

        # Check if the text is entirely or predominantly a JSON object or array
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            try:
                parsed = json.loads(stripped)
                return cls._format_parsed_json_to_markdown(parsed)
            except Exception:
                pass

        # Check if the text contains a raw JSON dump like: Based on verified database records: {...}
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(pattern, text)
        if match:
            matched_str = match.group(0)
            # Only convert if it looks like workforce data JSON
            if any(k in matched_str for k in ['"window_days"', '"late_arrivals"', '"top_overtime_employees"', '"attendance"', '"departments"', '"anomalies"', '"absent_employees"']):
                try:
                    parsed = json.loads(matched_str)
                    formatted_table = cls._format_parsed_json_to_markdown(parsed)
                    prefix = text[:match.start()].strip()
                    # Remove "Based on verified database records:" prefix if it exists
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

        sections = []

        # 1. Late Arrivals
        if "late_arrivals" in data or "employees" in data and "threshold_applied" in data:
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

                sections.append("\n### Key Observation")
                dept_counts = {}
                for e in employees:
                    d = e.get("department", "General")
                    dept_counts[d] = dept_counts.get(d, 0) + 1
                top_dept = max(dept_counts.items(), key=lambda x: x[1])[0] if dept_counts else "None"
                sections.append(f"- **{top_dept}** has the highest cluster of late arrivals during this period.")
                sections.append("- Timely supervisor notifications and grace-period reviews are advised.")
            else:
                sections.append("*No employees met the specified late arrival criteria for this period.*")

        # 2. Overtime
        elif "top_overtime_employees" in data:
            period = data.get("period", "Selected Period")
            dept_filter = data.get("department_filter", "All Departments")
            total_ot = data.get("total_overtime_hours", 0)
            employees = data.get("top_overtime_employees", [])

            sections.append(f"### Workforce Overtime Intelligence")
            sections.append(f"**Period:** {period} | **Department Scope:** {dept_filter}")
            sections.append(f"**Total Accumulated Overtime:** **{total_ot} hours**\n")

            if employees:
                sections.append("| Employee | Code | Department | Overtime Hours |")
                sections.append("| :--- | :--- | :--- | :---: |")
                for e in employees[:10]:
                    sections.append(f"| **{e.get('employee')}** | `{e.get('employee_code')}` | {e.get('department')} | **{e.get('overtime_hours')} hrs** |")

                top_person = employees[0]
                sections.append("\n### Key Observation")
                sections.append(f"- **{top_person.get('employee')}** logged the highest overtime (**{top_person.get('overtime_hours')} hours**).")
                sections.append("- Ensure overtime complies with standard Fair Labor & rest-break limits.")
            else:
                sections.append("*No overtime hours logged for this period.*")

        # 3. Department Analytics
        elif "departments" in data:
            period = data.get("period", "This Month")
            depts = data.get("departments", [])
            highest_abs = data.get("highest_absenteeism_department", "N/A")

            sections.append(f"### Department Attendance & Absenteeism Analytics")
            sections.append(f"**Period:** {period}")
            sections.append(f"**Highest Absenteeism:** **{highest_abs}**\n")

            sections.append("| Department | Headcount | Attendance Rate | Absenteeism Rate | Overtime | Attention Needed |")
            sections.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
            for d in depts:
                p_rate = f"{d.get('attendance_rate')}%"
                a_rate = f"{d.get('absenteeism_rate')}%"
                ot = f"{d.get('overtime_hours')}h"
                badge = f"⚠️ **{d.get('hr_attention_needed')}**" if d.get('hr_attention_needed') == "High" else d.get('hr_attention_needed')
                sections.append(f"| **{d.get('department')}** | {d.get('total_headcount')} | {p_rate} | {a_rate} | {ot} | {badge} |")

            sections.append("\n### Actionable HR Recommendations")
            sections.append(f"- Prioritize attendance audits for **{highest_abs}** due to above-average absenteeism.")

        # 4. Absenteeism
        elif "absent_employees" in data:
            period = data.get("period", "Today")
            total = data.get("total_absent_count", 0)
            employees = data.get("absent_employees", [])

            sections.append(f"### Workforce Absenteeism Roster")
            sections.append(f"**Period:** {period} | **Total Absent:** **{total} employees**\n")

            if employees:
                sections.append("| Employee | Employee Code | Department | Status |")
                sections.append("| :--- | :--- | :--- | :--- |")
                for e in employees:
                    sections.append(f"| **{e.get('employee')}** | `{e.get('employee_code')}` | {e.get('department')} | {e.get('status')} |")
            else:
                sections.append("✅ *100% attendance recorded. No employees are currently absent.*")

        # 5. Compound Workforce Correlations (Lateness + Overtime)
        elif "flagged_employees" in data:
            period = data.get("period", "This Month")
            criteria = data.get("criteria", "")
            count = data.get("flagged_employee_count", 0)
            flagged = data.get("flagged_employees", [])

            sections.append(f"### Compound Workforce Pattern Analysis")
            sections.append(f"**Period:** {period} | **Filter:** {criteria}")
            sections.append(f"**Flagged Employees:** **{count}**\n")

            if flagged:
                sections.append("| Employee | Department | Late Arrivals | Overtime Hours | Pattern Indicator |")
                sections.append("| :--- | :--- | :---: | :---: | :--- |")
                for f in flagged:
                    sections.append(f"| **{f.get('employee')}** | {f.get('department')} | {f.get('late_arrivals')} | **{f.get('overtime_hours')} hrs** | {f.get('pattern')} |")

                sections.append("\n### Ergonomic & Fatigue Insight")
                sections.append("- Employees working extended overtime alongside repeated tardiness may be experiencing schedule compression or fatigue.")
                sections.append("- Recommend reviewing shift start times and workload distribution.")
            else:
                sections.append("✅ *No employees matched the threshold for combined repeated tardiness and high overtime.*")

        # 6. Personal Attendance
        elif "summary" in data and "punctuality_rate" in data.get("summary", {}):
            s = data["summary"]
            sections.append(f"### Personal Attendance Summary ({data.get('employee', 'Employee')})")
            sections.append(f"**Period:** {data.get('period', 'This Month')}\n")
            sections.append(f"- **Days Logged:** {s.get('total_logged_days')} days")
            sections.append(f"- **Punctuality Rate:** **{s.get('punctuality_rate')}%**")
            sections.append(f"- **Total Hours Worked:** {s.get('total_worked_hours')} hours")
            sections.append(f"- **Total Overtime:** {s.get('overtime_hours')} hours")
            sections.append(f"- **Late Days:** {s.get('late_days')}")

        # 7. Employee Profile
        elif "employee_code" in data and "name" in data:
            sections.append(f"### Employee Profile: {data.get('name')}")
            sections.append(f"| Attribute | Value |")
            sections.append(f"| :--- | :--- |")
            sections.append(f"| **Employee Code** | `{data.get('employee_code')}` |")
            sections.append(f"| **Department** | {data.get('department', 'General')} |")
            sections.append(f"| **Designation** | {data.get('designation', 'Staff')} |")
            sections.append(f"| **Email** | {data.get('email', '-')} |")
            sections.append(f"| **Joining Date** | {data.get('date_of_joining', '-')} |")
            status_text = "✅ Active" if data.get('is_active') else "Inactive"
            sections.append(f"| **Status** | {status_text} |")

        # 8. Policy Search Matches
        elif "matches" in data and "query" in data:
            sections.append(f"### HR Policy Guidance: '{data.get('query')}'")
            matches = data.get("matches", [])
            if matches:
                for m in matches:
                    sections.append(f"\n#### 📄 {m.get('title')} (Page {m.get('page_number')}, Section {m.get('section', 1)})")
                    sections.append(f"> {m.get('content')}")
            else:
                sections.append("*No matching policy sections found in verified company handbooks.*")

        # 9. Anomalies Report
        elif "anomalies" in data:
            anoms = data.get("anomalies", [])
            sections.append(f"### Attendance Anomaly Investigation Report")
            sections.append(f"**Total Flags:** {len(anoms)}\n")
            if anoms:
                sections.append("| Employee | Date | Anomaly Type | Severity | Method | Status |")
                sections.append("| :--- | :---: | :--- | :---: | :---: | :---: |")
                for a in anoms:
                    sections.append(f"| **{a.get('employee')}** | {a.get('date')} | {a.get('type')} | `{a.get('severity')}` | {a.get('method')} | {a.get('status')} |")
            else:
                sections.append("✅ *Zero pending attendance anomalies found.*")

        else:
            # Fallback formatting for arbitrary dictionary
            sections.append("### Workforce Data Overview")
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
        """Generates smart suggested follow-up questions tailored to the returned data."""
        suggestions = []
        tool_names = [tr.get("tool_name") for tr in tool_results]

        if "get_late_arrivals" in tool_names:
            suggestions.append("Compare late arrivals between Engineering and Sales")
            suggestions.append("What is our grace period policy?")
            suggestions.append("Show employees with both repeated lateness and overtime")

        elif "get_employee_overtime" in tool_names:
            suggestions.append("What about Engineering?")
            suggestions.append("Show their employee details")
            suggestions.append("Which department has the highest absenteeism?")

        elif "get_absenteeism" in tool_names or "get_department_analytics" in tool_names:
            suggestions.append("Which department needs the most HR attention?")
            suggestions.append("Show late arrivals for this month")
            suggestions.append("Summarize pending anomaly flags")

        elif "search_attendance_policy" in tool_names:
            suggestions.append("What are core working hours?")
            suggestions.append("How do I request remote work approval?")

        elif "get_my_attendance" in tool_names:
            suggestions.append("What is my overtime this month?")
            suggestions.append("Search policy on sick leave")

        else:
            if role in ["admin", "hr_manager"]:
                suggestions.append("Which employees arrived late more than five times this month?")
                suggestions.append("Compare absenteeism across departments")
                suggestions.append("Who worked the most overtime this month?")
            else:
                suggestions.append("Show my attendance this month")
                suggestions.append("What is our overtime policy?")

        return suggestions[:3]
