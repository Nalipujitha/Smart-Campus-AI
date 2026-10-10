# Smart Campus Analytics - Security & Data Protection Policy

## 1. Dedicated Multi-Portal Login Architecture & Role Isolation

Smart Campus Analytics enforces independent, role-isolated authentication across four distinct access portals:

| Role | Dedicated Login URL | Landing Dashboard | Permitted Routes | Prohibited Routes |
| :--- | :--- | :--- | :--- | :--- |
| **Student** | `/student/login` | `/student/dashboard` | `/student/*`, personal profile, self attendance, AI mentor | `/admin/*`, `/faculty/*`, `/placement/*` (all staff portals) |
| **Faculty / Advisor** | `/faculty/login` | `/faculty/dashboard` | `/faculty/*`, assigned student profiles, class attendance & marks | `/admin/*`, `/placement/*`, direct system settings |
| **Placement Officer** | `/placement/login` | `/placement/dashboard` | `/placement/*`, company registry, recruitment drives, applicant pipelines | `/admin/*`, attendance modifications, system settings |
| **Administrator** | `/admin/login` | `/admin/dashboard` | `/admin/*`, `/reports/*`, `/settings/*`, `/audit/*`, `/api/v1/*` | None (institutional root authority) |

### Key Technical Mechanisms:
1. **Server-Side Role Guard on Login**: Each login page validates both the credentials AND the user's database role. If a student attempts to log in via `/admin/login`, `/faculty/login`, or `/placement/login`, the server rejects the request with an explicit `403 Forbidden` / `Access Denied` error, preventing unauthorized session creation.
2. **Decorator Protection**: Route access is verified on the server via `@login_required` and `@roles_required('Admin', 'Faculty', ...)`. Hiding frontend buttons is never treated as authorization.
3. **Password Security**: Passwords use Werkzeug's `generate_password_hash` (`scrypt`/`pbkdf2:sha256`) with unique cryptographic salts.
4. **Session Protection**: Flask signed session cookies configured with `HttpOnly` and `SameSite=Lax` flags.
5. **Cross-Portal Redirect Interceptor**: If an already-authenticated user visits another role's login URL, the server safely redirects them to their authorized dashboard without exposing foreign portal access.

---

## 2. Privacy & Data Isolation

- **Student Data Privacy**: Students can only access their personal attendance records, GPA progress, and recommendations.
- **Faculty Scope Isolation**: Faculty members can only access student lists, attendance records, and grades for classes and departments assigned to them.
- **Placement Officer Scope**: Placement officers can view candidate academic and placement readiness profiles, but cannot alter institutional attendance or modify faculty evaluations.

---

## 3. Audit Trails & Operational Accountability

Every critical platform state mutation writes an immutable row to the `audit_events` table, recording:
- `event_type` (e.g. `LOGIN`, `ATTENDANCE_CORRECTION`, `STUDENT_CREATE`, `STUDENT_DEACTIVATE`, `FACULTY_UPDATE`)
- `actor_id` & `actor_role`
- `description` with detailed change metadata
- `ip_address`
- `created_at` timestamp

---

## 4. Demo Accounts & Credential Safety

For local evaluation, the application provides pre-configured demo accounts in [`database/seed_data.py`](file:///d:/PROJECTS/student-success-platform/database/seed_data.py):
- **Student**: `stu_rahul` / `Student@123` $\rightarrow$ [`/student/login`](http://localhost:5000/student/login)
- **Faculty**: `dr.sharma` / `Faculty@123` $\rightarrow$ [`/faculty/login`](http://localhost:5000/faculty/login)
- **Placement Officer**: `placement_officer` / `Placement@123` $\rightarrow$ [`/placement/login`](http://localhost:5000/placement/login)
- **Admin**: `admin` / `Admin@123` $\rightarrow$ [`/admin/login`](http://localhost:5000/admin/login)
