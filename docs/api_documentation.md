# Smart Campus Analytics - REST API Documentation

All platform endpoints are versioned under `/api/v1/` and return standard JSON responses.

## 1. Dashboard & Analytics Endpoints

### `GET /api/v1/dashboard/summary`
Returns institutional KPI cards, distribution metrics, and department breakdowns.
- **Query Params**: `department`, `academic_year`, `semester`
- **Response**:
```json
{
  "total_students": 110,
  "avg_success_score": 73.4,
  "avg_attendance_pct": 84.6,
  "attendance_concern_count": 18,
  "academic_support_count": 14,
  "avg_placement_readiness": 68.2,
  "active_interventions_count": 8,
  "overdue_interventions_count": 2,
  "department_distribution": [...],
  "risk_distribution": {"High": 14, "Medium": 32, "Low": 64}
}
```

### `GET /api/v1/analytics/risk-distribution`
Returns institution-wide risk counts and percentages.

## 2. Student Endpoints

### `GET /api/v1/students`
- **Query Params**: `department`, `status`, `search`
- **Response**: Array of student objects with IDs, emails, departments, and semesters.

### `GET /api/v1/students/<student_id>`
Returns complete student dossier with score breakdown and attendance details.

### `POST /api/v1/students`
Creates a new student profile.
- **Request Body**: `{ "student_id": "STU2024200", "first_name": "Anita", "last_name": "Patel", "email": "anita@campus.edu", "department": "Computer Science & Engineering" }`

## 3. Attendance Endpoints

### `GET /api/v1/attendance/sessions`
Returns paginated list of conducted attendance sessions.

### `POST /api/v1/attendance/sessions`
Creates an attendance session and records student statuses.

### `GET /api/v1/attendance/students/<student_id>`
Returns student-specific attendance statistics and policy flags.

## 4. Interventions & Campus Assistant

### `POST /api/v1/interventions`
Logs a new faculty mentoring session.

### `POST /api/v1/campus/ask`
Queries verified local campus knowledge base.
- **Request Body**: `{ "question": "What is the minimum attendance requirement?" }`
- **Response**:
```json
{
  "answer": "As per institutional regulations...",
  "category": "Attendance",
  "confidence": "High",
  "contact_person": "Academic Dean Office",
  "contact_email": "dean.academics@campus.edu",
  "verified": true
}
```
