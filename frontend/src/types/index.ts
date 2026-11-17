export interface User {
  id: string;
  email: string;
  role: 'admin' | 'hr_manager' | 'employee';
  organization_id: string;
  organization_name?: string;
  employee_id?: string;
  first_name?: string;
  last_name?: string;
  employee_code?: string;
  designation?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface Employee {
  id: string;
  organization_id: string;
  department_id?: string;
  user_id?: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  designation: string;
  date_of_joining: string;
  is_active: boolean;
  department_name?: string;
  current_shift?: string;
}

export interface Department {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  manager_id?: string;
  employee_count: number;
  created_at: string;
}

export interface Shift {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: number;
  required_hours: number;
  is_overnight: boolean;
  created_at: string;
}

export interface AttendanceBreak {
  id: string;
  break_start: string;
  break_end?: string;
  duration_minutes: number;
  reason?: string;
}

export interface AttendanceRecord {
  id: string;
  organization_id: string;
  employee_id: string;
  date: string;
  clock_in?: string;
  clock_out?: string;
  worked_minutes: number;
  overtime_minutes: number;
  late_minutes: number;
  status: 'present' | 'late' | 'half_day' | 'absent' | 'incomplete';
  is_corrected: boolean;
  employee_name?: string;
  employee_code?: string;
  department_name?: string;
  breaks?: AttendanceBreak[];
}

export interface LeaveRecord {
  id: string;
  organization_id: string;
  employee_id: string;
  leave_type: 'annual' | 'sick' | 'casual' | 'unpaid';
  start_date: string;
  end_date: string;
  days_count: number;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  reviewed_by?: string;
  reviewed_at?: string;
  resolution_notes?: string;
  employee_name?: string;
  employee_code?: string;
  department_name?: string;
  created_at: string;
}

export interface AttendanceAnomaly {
  id: string;
  organization_id: string;
  employee_id: string;
  attendance_record_id?: string;
  date: string;
  anomaly_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  score: number;
  detection_method: 'rule_based' | 'isolation_forest' | 'hybrid';
  explanation: string;
  status: 'pending' | 'investigating' | 'resolved' | 'dismissed';
  reviewed_by?: string;
  reviewed_at?: string;
  resolution_notes?: string;
  employee_name?: string;
  employee_code?: string;
  department_name?: string;
  created_at: string;
}

export interface Policy {
  id: string;
  organization_id: string;
  title: string;
  category: string;
  file_path?: string;
  file_size: number;
  status: 'processing' | 'active' | 'failed';
  chunk_count: number;
  created_at: string;
}

export interface PolicyChunk {
  id: string;
  policy_id: string;
  title: string;
  section?: string;
  page_number: number;
  content: string;
  citation?: string;
}

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: any[];
  tool_results?: any[];
  citations?: any[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  messages: ConversationMessage[];
}

export interface DashboardData {
  kpis: {
    total_employees: number;
    present_today: number;
    absent_today: number;
    late_arrivals: number;
    overtime_hours: number;
    attendance_rate: number;
    comparison: {
      present: number;
      late: number;
      overtime: number;
    };
  };
  trends: Array<{
    date: string;
    present: number;
    absent: number;
    late: number;
    rate: number;
  }>;
  department_stats: Array<{
    department: string;
    present: number;
    absent: number;
    rate: number;
  }>;
  needs_attention: Array<{
    id: string;
    type: string;
    severity: string;
    employee: string;
    date: string;
    explanation: string;
  }>;
  recent_activity: Array<{
    id: string;
    employee: string;
    department: string;
    clock_in: string;
    clock_out: string;
    worked_hours: number;
    status: string;
  }>;
  ai_insights: Array<{
    title: string;
    insight: string;
    level: string;
  }>;
}
