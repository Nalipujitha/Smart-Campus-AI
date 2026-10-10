# Smart Campus Analytics - System Architecture

## 1. High-Level Architecture

Smart Campus Analytics is built on a clean, decoupled full-stack architecture featuring dedicated, role-isolated portals for **Institutional Administrators**, **Faculty Advisors**, **Placement Officers**, and **Students**:

```
+---------------------------------------------------------------------------------------------------+
|                                      Role-Based Portals Layer                                     |
|  +------------------+  +-------------------+  +---------------------+  +-----------------------+  |
|  |   Admin Portal   |  |   Faculty Portal  |  |   Placement Portal  |  |    Student Portal     |  |
|  | /admin/dashboard |  | /faculty/dashboard|  | /placement/dashboard|  |   /student/dashboard  |  |
|  +--------+---------+  +---------+---------+  +----------+----------+  +-----------+-----------+  |
+-----------|----------------------|-----------------------|-------------------------|--------------+
            +----------------------+-----------+-----------+-------------------------+
                                               |
                                HTTP / REST JSON & Session Requests
                                               |
+----------------------------------------------v----------------------------------------------------+
|                                    Flask Backend Core Layer                                       |
|  - Auth & RBAC Engine: Session cookies, @roles_required decorators, 403 Forbidden interceptor     |
|  - Modular Blueprints:                                                                            |
|      * auth_bp: Authentication, role routing, password security                                   |
|      * admin_bp: Institutional control, faculty/student CRUD, audit logs, settings, CSV export    |
|      * faculty_bp: Assigned rosters, attendance marking/history, internal marks, mentoring plans  |
|      * placement_bp: Company directory, recruitment drives, applications pipeline, readiness     |
|      * dashboard_bp: Student success radar, GPA trend, attendance %, feedback eligibility         |
|      * api_bp: Versioned REST endpoints (/api/v1/...) & Campus AI Copilot                          |
|  - Pure Business Service Layer:                                                                   |
|      * AttendanceService, SuccessScoreService, RiskAnalysisService, CareerRecommendationEngine   |
+----------------------------------------------+----------------------------------------------------+
                                               |
                                  SQLAlchemy ORM Data Engine
                                               |
+----------------------------------------------v----------------------------------------------------+
|                                  SQLite / PostgreSQL Database                                     |
|  - Relational Schema with foreign keys, unique session constraints, cascade integrity             |
|  - Entities: Users, Students, Faculty, Attendance, Academics, LMS, Interventions, Companies,      |
|              JobOpportunities, JobApplications, PlacementOffers, AuditEvents, SystemConfigs        |
+---------------------------------------------------------------------------------------------------+
```

## 2. Portal Breakdown & Workflows

### A. Administrator Portal (`/admin/...`)
- **Focus**: Global institutional governance, faculty & student directory CRUD, department & course management, system audit logs, and configuration.
- **Key Modules**:
  1. `admin.dashboard`: Real-time institutional KPIs, attendance & risk distributions, recent activity audit feed.
  2. `admin.students`: Enrolling new students, editing profiles, deactivating accounts.
  3. `admin.faculty`: Onboarding professors, managing department designations, account deactivations.
  4. `admin.attendance_overview`: Institution-wide attendance metrics, low-attendance alerts.
  5. `admin.risk_analysis`: Departmental risk hot-spots with explainable rule-based triggers.
  6. `admin.reports`: CSV report generator with dynamic streaming.
  7. `admin.settings`: Configurable warning/critical attendance thresholds and scoring weights.

### B. Faculty Portal (`/faculty/...`)
- **Focus**: Teaching workflows, interactive attendance logging, internal/external exam marks entry, at-risk student monitoring, and mentoring interventions.
- **Key Modules**:
  1. `faculty.dashboard`: Today's class sessions, student count under supervision, class attendance averages.
  2. `faculty.classes`: Assigned class rosters by department and semester.
  3. `faculty.mark_attendance`: Fast interactive session marker with duplicate prevention.
  4. `faculty.attendance_history`: Audit trail of past sessions with formal correction logging.
  5. `faculty.academics`: Entry of internal, midterm, and lab assessment marks.
  6. `faculty.at_risk`: Real-time view of students falling below attendance/academic thresholds with suggested actions.
  7. `faculty.mentoring`: Structured mentoring case management (concerns, action items, follow-up dates, outcomes).

### C. Placement Officer Portal (`/placement/...`)
- **Focus**: Employability tracking, recruitment drive operations, applicant status pipelines, and company relationship management.
- **Key Modules**:
  1. `placement.dashboard`: Recruitment KPIs, eligible student pool, active companies, upcoming drive timeline.
  2. `placement.companies`: Company directory with industry tags, tier, and contact information.
  3. `placement.jobs`: Campus job & internship opportunity listings with criteria.
  4. `placement.drives`: Drive scheduler and candidate eligibility check engine.
  5. `placement.applications`: Visual pipeline for applicant stage progression (`Applied` -> `Shortlisted` -> `Interview` -> `Selected` -> `Offer Accepted`).
  6. `placement.readiness`: Technical coding & aptitude preparation tracking.
  7. `placement.offers`: Official offer tracker with package (LPA) and joining metrics.

### D. Student Portal (`/student/...`)
- **Focus**: Personalized student dashboard, attendance breakdown with 75% feedback unlock threshold, GPA progress, AI Mentor chat assistant, and integrated code editor.

---

## 3. Directory Structure Mapping

- **`frontend/`**: Templates organized by portal (`admin/`, `faculty/`, `placement/`, `components/`) and CSS design tokens.
- **`backend/models/`**: Clean relational database entity definitions (`user.py`, `student.py`, `attendance.py`, `academic.py`, `placement.py`, `intervention.py`, `audit.py`).
- **`backend/services/`**: Pure business logic, explainable scoring calculations, and risk analysis.
- **`backend/routes/`**: Distinct route blueprints enforcing RBAC per portal.
- **`ai-ml/`**: Explainable ML models and cosine similarity matching engines.
- **`database/`**: Initialization scripts, schema DDL, and sample institutional seed datasets.
- **`tests/`**: Automated pytest test suite covering all portals, permissions, workflows, and edge cases.
- **`docs/`**: Architectural specifications, security policies, and API documentation.
