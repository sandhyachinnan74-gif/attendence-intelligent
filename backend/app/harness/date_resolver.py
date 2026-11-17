from datetime import date, timedelta
from typing import Tuple, Optional

class DateRangeResolver:
    """
    Deterministic resolver for natural-language workforce time periods.
    Ensures consistent, verifiable date windows across all backend tools.
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
            # First and last day of previous month
            first_this_month = date(today.year, today.month, 1)
            last_prev_month = first_this_month - timedelta(days=1)
            first_prev_month = date(last_prev_month.year, last_prev_month.month, 1)
            return first_prev_month, last_prev_month, last_prev_month.strftime("%B %Y")

        elif p in ["last_7_days", "past_7_days"]:
            return today - timedelta(days=7), today, "Last 7 Days"

        elif p in ["last_30_days", "past_30_days"]:
            return today - timedelta(days=30), today, "Last 30 Days"

        elif p in ["last_90_days", "quarter"]:
            return today - timedelta(days=90), today, "Last 90 Days"

        # Default fallback: last 30 days
        return today - timedelta(days=30), today, "Last 30 Days"
