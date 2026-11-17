import pytest
import io
import openpyxl
from datetime import date, time, timedelta
from sqlalchemy import select
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.models import User, Employee, Department, AttendanceRecord, Shift
from app.core.database import get_sessionmaker
from app.harness.orchestrator import ai_orchestrator
from app.harness.tool_registry import ToolRegistry, TOOL_DEFINITIONS
from app.harness.date_resolver import DateRangeResolver
from app.harness.output_validator import OutputValidator
from app.harness.permissions import HarnessPermissions

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
async def admin_user():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        user = (await db.execute(select(User).where(User.email == "admin@attendai.com"))).scalars().first()
        return user

@pytest.fixture
async def hr_user():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        user = (await db.execute(select(User).where(User.email == "hrmanager@attendai.com"))).scalars().first()
        return user

@pytest.fixture
async def employee_user():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        user = (await db.execute(select(User).where(User.email == "employee@attendai.com"))).scalars().first()
        emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()
        return user, emp

# ---------------------------------------------------------------------------
# 1. Employee Personal AI Tools & Identity Isolation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_employee_my_overtime(employee_user):
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        # 1. Execute get_my_overtime directly
        res = await ToolRegistry.execute_tool(
            name="get_my_overtime",
            arguments={"period": "this_month"},
            db=db,
            user=user,
            employee=emp
        )
        assert "total_overtime_hours" in res
        assert "overtime_records" in res
        assert res["employee"] == f"{emp.first_name} {emp.last_name}"
        assert res["employee_code"] == emp.employee_code

        # 2. End-to-end turn via AI Assistant
        turn = await ai_orchestrator.execute_turn(
            db=db,
            user=user,
            employee=emp,
            user_message="How much overtime did I do this month?",
            conversation_history=[]
        )
        assert turn["content"] is not None
        assert "{" not in turn["content"] or "```" in turn["content"]
        assert len(turn["citations"]) > 0
        assert "Personal Overtime" in turn["citations"][0]["source"]

@pytest.mark.asyncio
async def test_employee_my_late_arrivals(employee_user):
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="get_my_late_arrivals",
            arguments={"period": "this_month"},
            db=db,
            user=user,
            employee=emp
        )
        assert "total_late_count" in res
        assert "late_records" in res
        assert res["employee"] == f"{emp.first_name} {emp.last_name}"

@pytest.mark.asyncio
async def test_employee_my_working_hours(employee_user):
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="get_my_working_hours",
            arguments={"period": "this_month"},
            db=db,
            user=user,
            employee=emp
        )
        assert "total_worked_hours" in res
        assert "regular_hours" in res
        assert "logged_days" in res
        assert res["employee"] == f"{emp.first_name} {emp.last_name}"

@pytest.mark.asyncio
async def test_employee_my_leave_balance(employee_user):
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="get_my_leave_balance",
            arguments={},
            db=db,
            user=user,
            employee=emp
        )
        assert "leave_balances" in res
        assert "annual_leave" in res["leave_balances"]
        assert "sick_leave" in res["leave_balances"]
        assert res["leave_balances"]["annual_leave"]["allocated"] == 18.0

@pytest.mark.asyncio
async def test_employee_my_shifts(employee_user):
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="get_my_shifts",
            arguments={},
            db=db,
            user=user,
            employee=emp
        )
        assert "shift_name" in res
        assert "start_time" in res
        assert "end_time" in res
        assert "grace_period_minutes" in res

@pytest.mark.asyncio
async def test_employee_my_attendance_history(employee_user):
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="get_my_attendance_history",
            arguments={"period": "last_30_days", "limit": 10},
            db=db,
            user=user,
            employee=emp
        )
        assert "history" in res
        assert "count" in res
        assert res["employee"] == f"{emp.first_name} {emp.last_name}"

@pytest.mark.asyncio
async def test_employee_idor_override_attempt_blocked(employee_user):
    """
    Verify that even if an attacker attempts to pass employee_id in tool arguments,
    the backend strictly scopes to the authenticated session employee.
    """
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        # Attacker employee attempts to query employee_id="some_other_id"
        res = await ToolRegistry.execute_tool(
            name="get_my_overtime",
            arguments={"employee_id": "malicious_override_target_id", "period": "this_month"},
            db=db,
            user=user,
            employee=emp
        )
        # Result MUST belong to the authenticated emp, NOT the target
        assert res["employee_code"] == emp.employee_code
        assert res["employee"] == f"{emp.first_name} {emp.last_name}"

@pytest.mark.asyncio
async def test_employee_denied_org_wide_tools_and_no_false_citations(employee_user):
    """
    Verify employee cannot call org-wide tools, and OutputValidator never creates
    fake citations or claims data was retrieved.
    """
    user, emp = employee_user
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        # Direct tool registry check
        res = await ToolRegistry.execute_tool(
            name="get_employee_overtime",
            arguments={"period": "this_month"},
            db=db,
            user=user,
            employee=emp
        )
        assert "error" in res
        assert "Permission denied" in res["error"]

        # OutputValidator test
        val = OutputValidator.validate_and_format(
            raw_text="Attempting to fetch organization overtime.",
            tool_results=[{"tool_name": "get_employee_overtime", "output": res}],
            role="employee"
        )
        # Verify NO citations generated for failed tool
        assert len(val["citations"]) == 0
        assert val["is_grounded"] is False
        assert "Authorization" in val["validated_text"]

# ---------------------------------------------------------------------------
# 2. Universal Dynamic Query Intelligence (The Unseen Questions)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_universal_query_arrived_after_11_today(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_workforce_attendance",
            arguments={"period": "today", "min_clock_in_time": "11:00"},
            db=db,
            user=admin_user
        )
        assert "total_matches" in res
        assert "records" in res
        assert res["period"] == "Today"

@pytest.mark.asyncio
async def test_universal_query_worked_more_than_45_hours_this_week(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_workforce_attendance",
            arguments={"period": "this_week", "min_worked_hours": 45.0, "group_by": "employee"},
            db=db,
            user=admin_user
        )
        assert "total_qualifying_employees" in res
        assert "employees" in res
        for e in res["employees"]:
            assert e["total_worked_hours"] >= 45.0

@pytest.mark.asyncio
async def test_universal_query_compare_two_lowest_attendance_departments(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="compare_workforce_metrics",
            arguments={"comparison_type": "departments", "metric": "attendance_rate", "departments": "lowest_attendance"},
            db=db,
            user=admin_user
        )
        assert "ranked_departments" in res
        assert len(res["ranked_departments"]) == 2
        # First department has lower or equal attendance rate than second
        assert res["ranked_departments"][0]["attendance_rate"] <= res["ranked_departments"][1]["attendance_rate"]
        assert "key_observation" in res

@pytest.mark.asyncio
async def test_universal_query_most_sick_leave_this_year(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_leave_analytics",
            arguments={"leave_type": "sick", "period": "this_year", "group_by_employee": True},
            db=db,
            user=admin_user
        )
        assert "top_employees" in res
        assert res["leave_type"] == "Sick"

@pytest.mark.asyncio
async def test_universal_query_unusually_long_breaks(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_workforce_attendance",
            arguments={"period": "this_month", "min_break_minutes": 60, "group_by": "employee"},
            db=db,
            user=admin_user
        )
        assert "employees" in res

@pytest.mark.asyncio
async def test_universal_query_weekend_overtime(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_workforce_attendance",
            arguments={"period": "this_month", "is_weekend_only": True, "min_overtime_hours": 0.1},
            db=db,
            user=admin_user
        )
        assert "records" in res
        assert "total_matches" in res

@pytest.mark.asyncio
async def test_universal_query_increasing_absenteeism_departments(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="compare_workforce_metrics",
            arguments={
                "comparison_type": "periods",
                "metric": "absenteeism_rate",
                "period_a": "this_month",
                "period_b": "last_month"
            },
            db=db,
            user=admin_user
        )
        assert "comparison_type" in res
        assert "comparisons" in res
        assert "departments_with_increasing_absenteeism" in res

@pytest.mark.asyncio
async def test_universal_query_late_but_completed_full_shifts(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_workforce_attendance",
            arguments={"period": "this_month", "late_but_completed_shift": True},
            db=db,
            user=admin_user
        )
        assert "records" in res
        for r in res["records"]:
            assert r["late_minutes"] > 0
            assert r["worked_hours"] >= 8.0

@pytest.mark.asyncio
async def test_universal_query_shifts_missing_clock_outs(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_workforce_attendance",
            arguments={"period": "this_month", "missing_clock_out": True, "group_by": "shift"},
            db=db,
            user=admin_user
        )
        assert "shifts" in res

@pytest.mark.asyncio
async def test_universal_query_attendance_trends_previous_quarter(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ToolRegistry.execute_tool(
            name="query_workforce_attendance",
            arguments={"period": "previous_quarter", "aggregation": "trend"},
            db=db,
            user=admin_user
        )
        assert "summary" in res
        assert "trend_analysis" in res
        assert "overall_punctuality_rate" in res["summary"]

# ---------------------------------------------------------------------------
# 3. DateRangeResolver & Time Parsing Tests
# ---------------------------------------------------------------------------
def test_date_range_resolver_quarter_and_year():
    # Previous quarter
    s_q, e_q, lbl_q = DateRangeResolver.resolve_period("previous_quarter")
    assert s_q < e_q
    assert "Q" in lbl_q

    # This year
    s_y, e_y, lbl_y = DateRangeResolver.resolve_period("this_year")
    assert s_y == date(date.today().year, 1, 1)
    assert e_y == date.today()

    # Last year
    s_ly, e_ly, lbl_ly = DateRangeResolver.resolve_period("last_year")
    assert s_ly == date(date.today().year - 1, 1, 1)
    assert e_ly == date(date.today().year - 1, 12, 31)

def test_time_parser_formats():
    assert DateRangeResolver.parse_time_str("11:00") == time(11, 0, 0)
    assert DateRangeResolver.parse_time_str("11:30:15") == time(11, 30, 15)
    assert DateRangeResolver.parse_time_str("11am") == time(11, 0, 0)
    assert DateRangeResolver.parse_time_str("2pm") == time(14, 0, 0)
    assert DateRangeResolver.parse_time_str("11") == time(11, 0, 0)
    assert DateRangeResolver.parse_time_str(None) is None

# ---------------------------------------------------------------------------
# 4. Out-of-Domain Safety & Generalization Guarantee
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_out_of_domain_query_polite_refusal(admin_user):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        res = await ai_orchestrator.execute_turn(
            db=db,
            user=admin_user,
            employee=None,
            user_message="What is the weather like in Paris today?",
            conversation_history=[]
        )
        assert res["content"] is not None
        assert any(phrase in res["content"].lower() for phrase in ["attendai assistant", "workforce intelligence", "workforce", "attendai"])
        assert len(res["tool_calls"]) == 0
        assert len(res["citations"]) == 0
