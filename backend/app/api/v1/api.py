from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, employees, departments, shifts, attendance, leave, anomalies, policies, analytics, exports, ai, system
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(departments.router)
api_router.include_router(shifts.router)
api_router.include_router(attendance.router)
api_router.include_router(leave.router)
api_router.include_router(anomalies.router)
api_router.include_router(policies.router)
api_router.include_router(analytics.router)
api_router.include_router(exports.router)
api_router.include_router(ai.router)
api_router.include_router(system.router)
