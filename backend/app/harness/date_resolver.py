from datetime import date, timedelta, time
from typing import Tuple, Optional
import re

class DateRangeResolver:
    """
    Deterministic resolver for natural-language workforce time periods and timestamps.
    Ensures consistent, verifiable date windows and threshold parameters across all backend tools.
    """
    @staticmethod
    def resolve_period(
        period: Optional[str] = None,
        days: Optional[int] = None,
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None
    ) -> Tuple[date, date, str]:
        today = date.today()

        # If explicit start and end dates are provided
        if start_date_str:
            try:
                s_date = date.fromisoformat(start_date_str)
                e_date = date.fromisoformat(end_date_str) if end_date_str else today
                return s_date, e_date, f"{s_date} to {e_date}"
            except ValueError:
                pass

        if not period and days:
            s_date = today - timedelta(days=days)
            return s_date, today, f"Last {days} days"

        p = (period or "this_month").lower().strip().replace(" ", "_").replace("-", "_")

        if p == "today":
            return today, today, "Today"

        elif p == "yesterday":
            y = today - timedelta(days=1)
            return y, y, "Yesterday"

        elif p in ["this_week", "current_week"]:
            # Monday of current week
            start = today - timedelta(days=today.weekday())
            return start, today, "This Week"

        elif p in ["last_week", "previous_week"]:
            # Monday to Sunday of previous week
            prev_monday = today - timedelta(days=today.weekday() + 7)
            prev_sunday = prev_monday + timedelta(days=6)
            return prev_monday, prev_sunday, "Last Week"

        elif p in ["this_month", "current_month"]:
            start = date(today.year, today.month, 1)
            return start, today, f"{today.strftime('%B %Y')} (Month-to-Date)"

        elif p in ["last_month", "previous_month"]:
            first_this_month = date(today.year, today.month, 1)
            last_prev_month = first_this_month - timedelta(days=1)
            first_prev_month = date(last_prev_month.year, last_prev_month.month, 1)
            return first_prev_month, last_prev_month, last_prev_month.strftime("%B %Y")

        elif p in ["last_7_days", "past_7_days"]:
            return today - timedelta(days=7), today, "Last 7 Days"

        elif p in ["last_30_days", "past_30_days"]:
            return today - timedelta(days=30), today, "Last 30 Days"

        elif p in ["last_90_days", "past_90_days"]:
            return today - timedelta(days=90), today, "Last 90 Days"

        elif p in ["previous_quarter", "last_quarter"]:
            # Quarters: Q1 (1-3), Q2 (4-6), Q3 (7-9), Q4 (10-12)
            cur_quarter = (today.month - 1) // 3 + 1
            if cur_quarter == 1:
                prev_q_year = today.year - 1
                return date(prev_q_year, 10, 1), date(prev_q_year, 12, 31), f"Q4 {prev_q_year}"
            elif cur_quarter == 2:
                return date(today.year, 1, 1), date(today.year, 3, 31), f"Q1 {today.year}"
            elif cur_quarter == 3:
                return date(today.year, 4, 1), date(today.year, 6, 30), f"Q2 {today.year}"
            else:  # cur_quarter == 4
                return date(today.year, 7, 1), date(today.year, 9, 30), f"Q3 {today.year}"

        elif p in ["this_quarter", "current_quarter"]:
            cur_quarter = (today.month - 1) // 3 + 1
            q_start_month = (cur_quarter - 1) * 3 + 1
            return date(today.year, q_start_month, 1), today, f"Q{cur_quarter} {today.year} (Quarter-to-Date)"

        elif p in ["this_year", "current_year", "year_to_date", "ytd"]:
            return date(today.year, 1, 1), today, f"{today.year} Year-to-Date"

        elif p in ["last_year", "previous_year"]:
            prev_year = today.year - 1
            return date(prev_year, 1, 1), date(prev_year, 12, 31), f"Calendar Year {prev_year}"

        # Default fallback: last 30 days
        return today - timedelta(days=30), today, "Last 30 Days"

    @staticmethod
    def parse_time_str(time_str: Optional[str]) -> Optional[time]:
        """Parses time strings like '11:00', '11:00:00', '11am', '2pm', '14:30'."""
        if not time_str:
            return None
        t_clean = time_str.strip().lower()
        # Format HH:MM:SS
        m = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', t_clean)
        if m:
            h, minute = int(m.group(1)), int(m.group(2))
            sec = int(m.group(3)) if m.group(3) else 0
            return time(h, minute, sec)
        # Format with am/pm (e.g. 11am, 11:30am, 2pm)
        m = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$', t_clean)
        if m:
            h = int(m.group(1))
            minute = int(m.group(2)) if m.group(2) else 0
            ampm = m.group(3)
            if ampm == "pm" and h < 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
            return time(h, minute, 0)
        # Simple integer hour (e.g. '11')
        if t_clean.isdigit():
            h = int(t_clean)
            if 0 <= h <= 23:
                return time(h, 0, 0)
        return None
