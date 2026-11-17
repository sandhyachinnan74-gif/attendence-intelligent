from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ColumnDefinition(BaseModel):
    id: str
    label: str
    category: Optional[str] = "General"
    is_default: bool = True

class ReportTypeMetadata(BaseModel):
    id: str
    name: str
    description: str
    category: str
    allowed_roles: List[str]
    default_columns: List[str]
    available_columns: List[ColumnDefinition]
    supported_formats: List[str] = ["csv", "xlsx", "pdf"]

class ReportPreviewRequest(BaseModel):
    report_type: str
    scope_type: str = "organization"  # organization, department, multi_department, individual_employee, multi_employee, personal
    department_ids: Optional[List[str]] = None
    employee_ids: Optional[List[str]] = None
    date_preset: Optional[str] = "this_month"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    columns: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    format: str = "xlsx"  # csv, xlsx, pdf

class ReportPreviewResponse(BaseModel):
    report_type: str
    report_title: str
    scope_summary: str
    start_date: date
    end_date: date
    employees_count: int
    departments_count: int
    selected_columns_count: int
    record_count: int
    format: str
    is_authorized: bool

class ReportGenerateRequest(BaseModel):
    report_type: str
    report_title: Optional[str] = None
    scope_type: str = "organization"
    department_ids: Optional[List[str]] = None
    employee_ids: Optional[List[str]] = None
    date_preset: Optional[str] = "this_month"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    columns: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    format: str = "xlsx"

class ReportGenerateResponse(BaseModel):
    export_id: str
    report_name: str
    report_type: str
    scope_summary: str
    format: str
    record_count: int
    file_size_bytes: int
    status: str
    download_url: str
    created_at: datetime

class ExportHistoryResponse(BaseModel):
    id: str
    report_name: str
    report_type: str
    scope_type: str
    scope_summary: Optional[str] = None
    date_preset: Optional[str] = None
    start_date: date
    end_date: date
    format: str
    record_count: int
    file_size_bytes: int
    status: str
    download_url: str
    created_at: datetime

    class Config:
        from_attributes = True
