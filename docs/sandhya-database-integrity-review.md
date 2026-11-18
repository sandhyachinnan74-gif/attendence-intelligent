# AttendAI – Database Integrity Review

**Contributor:** C Sandhya  
**Area:** Database Engineering  
**Database:** PostgreSQL 16  
**ORM:** SQLAlchemy 2.0 Async

## 1. Overview

This document describes database integrity considerations
for the AttendAI workforce attendance management system.

## 2. Database Integrity

The following integrity rules are important:

- Employee records should have unique identifiers.
- Attendance records should reference valid employees.
- Check-out time must not precede check-in time.
- Duplicate attendance entries should be prevented.
- Attendance corrections should maintain audit history.
- Timecard exceptions should retain valid employee references.

## 3. Referential Integrity

Foreign key relationships should maintain consistency
between employees and their attendance records.

## 4. Data Validation

PostgreSQL constraints can help prevent invalid data
from being stored in attendance-related tables.

Examples include:
- PRIMARY KEY
- FOREIGN KEY
- UNIQUE
- NOT NULL
- CHECK

## 5. Conclusion

Database integrity is essential for reliable attendance
calculations, timecard exception management and payroll
accuracy in AttendAI.