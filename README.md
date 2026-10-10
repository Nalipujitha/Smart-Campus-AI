# Smart Campus Analytics
### AI-Powered Student Analytics, Institutional Intelligence & Multi-Portal Success Platform

Smart Campus Analytics is a unified platform featuring **four completely separate, role-isolated login pages and dedicated portals**:

1. **Student Portal** ([`/student/login`](http://localhost:5000/student/login) $\rightarrow$ `/student/dashboard`): Student-themed login, real-time attendance rate with 75% feedback unlock threshold, GPA progress, AI Mentor chat assistant, and integrated code practice editor.
2. **Faculty Portal** ([`/faculty/login`](http://localhost:5000/faculty/login) $\rightarrow$ `/faculty/dashboard`): Academic & teaching-themed login, assigned class rosters, interactive attendance marking & correction history, internal/midterm marks recording, and mentoring case management.
3. **Placement Portal** ([`/placement/login`](http://localhost:5000/placement/login) $\rightarrow$ `/placement/dashboard`): Recruitment & career-themed login, company directory, campus recruitment drives, applicant stage tracking pipeline, and offer logging.
4. **Admin Portal** ([`/admin/login`](http://localhost:5000/admin/login) $\rightarrow$ `/admin/dashboard`): Institutional command center login, institutional KPIs, student & faculty directory administration, risk hotspots, dynamic CSV reports, audit logs, and settings.

---

## 🏛️ Top-Level Project Structure

```
student-success-platform/
├── frontend/
│   ├── templates/
│   │   ├── base.html                    # Unified navigation shell with role-tailored sidebars
│   │   ├── login.html                   # Multi-portal gateway landing page
│   │   ├── access_denied.html           # 403 Forbidden Access Denied page
│   │   ├── index.html                   # Student Portal Dashboard
│   │   ├── auth/                        # 4 Dedicated Independent Login Templates
│   │   │   ├── student_login.html       # /student/login
│   │   │   ├── admin_login.html         # /admin/login
│   │   │   ├── faculty_login.html       # /faculty/login
│   │   │   └── placement_login.html     # /placement/login
│   │   ├── admin/                       # Dedicated Admin Portal Views
│   │   ├── faculty/                     # Dedicated Faculty Portal Views
│   │   └── placement/                   # Dedicated Placement Officer Views
│   └── static/
│       ├── css/style.css                # CSS Design System
│       └── js/                          # Modular Portal JS
├── backend/
│   ├── app.py                           # Flask Application Factory & Blueprint Registration
│   ├── config.py                        # Configuration & Database URI
│   ├── extensions.py                    # SQLAlchemy, LoginManager
│   ├── models/                          # Data Models (User, Student, Attendance, Academic, Placement, etc.)
│   ├── routes/                          # Blueprints (auth, admin, faculty, placement, dashboard, api)
│   └── services/                        # Business Logic (AttendanceService, SuccessScoreService, RiskAnalysisService)
├── ai-ml/                               # Career and Success Scoring Engines
├── database/
│   ├── schema.sql                       # Database DDL
│   ├── init_db.py                       # DB Schema Initializer
│   └── seed_data.py                     # Realistic Demo Data Seeder
├── tests/                               # Comprehensive Automated Test Suite (47+ tests)
├── docs/                                # Architecture, Security, Scoring, and API Documentation
├── README.md
├── .env.example
└── .gitignore
```

---

## 🚀 Quick Start (Windows PowerShell)

### 1. Prerequisites
- Python 3.10+ installed and on system PATH.

### 2. Environment Setup & Dependencies
Open PowerShell and navigate to the project directory:
```powershell
cd d:\PROJECTS\student-success-platform
pip install -r backend\requirements.txt
```

### 3. Initialize Database & Seed Demo Data
```powershell
python database\init_db.py
python database\seed_data.py
```

### 4. Run Development Server
```powershell
python backend\app.py
```
Open your browser at **`http://localhost:5000`**.

---

## 🔑 Dedicated Role Login URLs & Demo Credentials

Each role has its own independent login page with server-side role validation:

| Role | Dedicated Login URL | Demo Username | Demo Password | Dedicated Landing Dashboard |
| :--- | :--- | :--- | :--- | :--- |
| **Student** | [`/student/login`](http://localhost:5000/student/login) | `stu_rahul` | `Student@123` | [`/student/dashboard`](http://localhost:5000/student/dashboard) |
| **Faculty Member** | [`/faculty/login`](http://localhost:5000/faculty/login) | `dr.sharma` | `Faculty@123` | [`/faculty/dashboard`](http://localhost:5000/faculty/dashboard) |
| **Placement Officer** | [`/placement/login`](http://localhost:5000/placement/login) | `placement_officer` | `Placement@123` | [`/placement/dashboard`](http://localhost:5000/placement/dashboard) |
| **Administrator** | [`/admin/login`](http://localhost:5000/admin/login) | `admin` | `Admin@123` | [`/admin/dashboard`](http://localhost:5000/admin/dashboard) |

## 💻 Student Portal: Workspace, Editors & Coding History

The Student Portal features a dual-editor environment combining an independent **Personal Workspace IDE** and a competitive **Coding Lab**:

### 1. Coding Lab (`/student/coding-lab`)
- 22+ educational practice problems with 3-panel ByteXL-style IDE.
- Isolated subprocess execution (`python -I`) in temporary directories with 3.0s hard timeouts, 32KB output limits, sanitized environment variables, and hidden test-case confidentiality.
- Direct alignment with the **Placement Readiness Index**.

### 2. Coding History (`/student/coding-history`)
- Complete historical record of all code submissions and execution results.
- Inspection modal showing submitted code, test case outcomes, execution times, and errors.
- One-click problem reopening in the Coding Lab editor.

---

## 🤖 Campus AI Assistant — Real LLM-Powered Chatbot

The Campus AI Assistant (`/campus/` & `/student/chat`) features a multi-turn, context-grounded conversational AI powered by **Google Gemini API** with Retrieval-Augmented Generation (RAG) and authenticated student profile context.

### Key Capabilities:
1. **Real LLM Intelligence**: Connects to Google Gemini (`gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`) via secure backend API calls.
2. **Context-Aware Responses**:
   - Institutional Policies & Guidelines (attendance thresholds, exam rules, library hours, grading criteria).
   - Academic & Subject Explanations (DSA, OOP, Dynamic Programming, SQL, Math formulas).
   - Placement & Career Guidance (resume tips, interview prep, skill roadmaps).
3. **Authenticated Student Profile Grounding**:
   - Securely retrieves the authenticated student's attendance %, GPA, composite success score, placement readiness index, and active recommendations directly from the server session.
   - Strictly enforces server-side student verification (prevents unauthorized access across accounts).
4. **Verified Institutional Knowledge Base**:
   - Administrators and Faculty can add, search, and verify institutional policy records.
   - LLM system prompts are grounded with verified institutional excerpts before generation to eliminate hallucinations.
5. **Chat Memory & Persistence**:
   - Multi-turn conversation history persisted in the database per user (`ChatConversation` & `ChatMessage`).
   - Create new chats, switch between active conversations, rename, clear, or delete conversations.
6. **Rich Interactive UI**:
   - Syntax-highlighted code blocks with "Copy Code" buttons.
   - Formatted Markdown (headings, lists, blockquotes, bold/italic, tables).
   - Stop/Cancel generation button (`AbortController`), retry failed messages, copy responses, and real-time character counter.

### Configuring Google Gemini API

1. **Obtain an API Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/) and create a Gemini API key.
2. **Configure in `.env`**:
   - Copy `.env.example` to `.env` (if not already created):
   ```bash
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   GEMINI_RATE_LIMIT_PER_MINUTE=20
   ```
3. **Supported Models**:
   - `gemini-1.5-flash` (Recommended: fast, low latency, generous rate limits)
   - `gemini-1.5-pro` (Complex reasoning, deep analysis)
   - `gemini-2.0-flash` (Next-gen speed & quality)
4. **Local Fallback Mode**:
   - If `GEMINI_API_KEY` is not set or unavailable, the system automatically falls back to the built-in verified institutional knowledge synthesizer without crashing or blocking the UI.

### Privacy & Security Considerations
- **Backend-Only Credentials**: API keys are kept strictly on the backend and are never exposed to client-side scripts, templates, or logs.
- **Data Minimization**: Passwords, password hashes, and sensitive authentication credentials are never sent to the LLM.
- **Prompt Injection Defense**: User messages and retrieved documents are treated as untrusted data within strict system prompt boundary delimiters.
- **Cross-User Isolation**: Conversations and messages are strictly scoped to the authenticated user ID (`user_id`).

---

## 🏆 KPMG in India Student Success Challenge Implementation

The platform has been upgraded with a complete, transparent, and explainable **AI-Powered Student Analytics & Success Intelligence Engine** fulfilling all KPMG Challenge requirements:

### 1. Feature 1 — At-Risk Student Identification
- **Dual Risk Engine**: Evaluates both **Academic Risk** (GPA, backlog counts, attendance, assignment completion) and **Placement Risk** (interview readiness, aptitude scores, technical coding level).
- **Clear Severity Levels**: `High Risk`, `Medium Risk`, and `Low Risk` with dedicated color badges.
- **Explainable Trigger Evidence**: Every risk classification outputs specific triggering indicators (e.g., `Attendance below 75% (68.0%)`, `2 active backlogs`, `Low mock interview readiness (45.0%)`).
- **Urgent Faculty Attention Flag**: Automatically flags students requiring immediate faculty intervention (`needs_immediate_attention=True`).
- **Interactive Filtering & Search**: Department filter, risk category filter, urgent attention toggle, and student name/ID live search.

### 2. Feature 2 — Explainable Student Success Score (Fixed & Enhanced)
- **Resolved UI Bug**: Replaced empty `/100` display with a real, computed score (0–100) and distinct status categories:
  - `High Performing` (Score $\ge 80$, Emerald)
  - `Good Standing` (Score $65–79$, Blue)
  - `Moderate Risk` (Score $50–64$, Amber)
  - `Critical Risk` (Score $< 50$, Rose)
- **7-Indicator Composite Formula (Weights sum to 100%)**:
  $$\text{Success Score} = 0.30 \times \text{Academic} + 0.20 \times \text{Attendance} + 0.10 \times \text{LMS} + 0.10 \times \text{Engagement} + 0.15 \times \text{Placement} + 0.10 \times \text{Skills} + 0.05 \times \text{Feedback}$$
- **Factor Decomposition & Transparency**:
  - **Academic (30%)**: Normalized GPA (0–10 scaled to 0–100) with backlog deductions (-10 pts per backlog).
  - **Attendance (20%)**: Session attendance percentage.
  - **LMS Completion (10%)**: Course module completion rate.
  - **Student Engagement (10%)**: Extracurricular, workshop, and club participation score.
  - **Placement Readiness (15%)**: Weighted average of mock interview score and aptitude score.
  - **Technical Skills (10%)**: Coding lab performance score and problem solved ratio.
  - **Student Feedback (5%)**: Student course rating satisfaction normalized to 0–100.
- **Explainability Panel**: Displays exact indicator scores, weights, contribution points, top positive drivers, and primary improvement areas.

### 3. Feature 3 — Student Segmentation
Implements 5 data-driven, rule-based student cohorts with dynamic recalculation:
1. **Academic Achievers with Placement Gaps**: GPA $\ge 7.5$ but Placement Readiness $< 60\%$.
2. **Attendance & Academic At-Risk**: Attendance $< 75\%$ and (GPA $< 6.0$ or Active Backlogs $> 0$).
3. **All-Round Placement Ready**: Success Score $\ge 75\%$ and Placement Readiness $\ge 70\%$.
4. **Disengaged High-Potential**: GPA $\ge 7.0$ but LMS Module Completion $< 50\%$.
5. **Core Support Group**: Success Score $< 60\%$ or Critical Risk Flag.
- Supports multi-cohort membership, segment count KPIs, cohort percentage share, and drill-down student rosters.

### 4. Feature 4 — Actionable Intervention Recommendations
- **Personalized Root-Cause Recommendations**: Generated from exact student weakness areas (attendance counseling, remedial tutoring, LMS learning plans, coding drills, aptitude prep, mock interview coaching, club engagement).
- **Governance & Accountability**: Each recommendation specifies `priority` (`Urgent`, `High`, `Medium`, `Standard`), `responsible_role` (e.g. *Faculty Advisor*, *Placement Cell*, *Department HOD*, *Peer Mentor*), `suggested_deadline`, and recommended next steps.
- **Follow-Up Lifecycle Tracking**: Faculty and admins can transition recommendation states (`Open` $\rightarrow$ `In Progress` $\rightarrow$ `Completed`) with persistent SQLite storage.

### 5. Feature 5 — Administrator Decision Intelligence
- **Executive Analytics Dashboard** (`/admin/dashboard` & `/analytics/institutional`):
  - Total students analyzed, average composite success score, risk distribution counts, urgent intervention counters.
  - Department-wise success score and risk breakdown comparisons.
  - Placement readiness tier distribution (High / Moderate / Low).
  - Student segment distribution metrics.
  - Top contributing risk factors institutional ranking.
  - Intervention pipeline progress tracking.
- **At-Risk Student Management** (`/analytics/risk`):
  - Searchable, filterable student risk register.
  - Interactive modal to log faculty follow-up actions, assigned staff, target dates, and status updates directly into SQLite.

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/summary` | Macro institutional metrics and portal summary |
| `GET` | `/api/v1/students` | Searchable student directory with pagination |
| `GET` | `/api/v1/students/<id>` | Full student profile and metrics |
| `GET` | `/api/v1/students/<id>/score-breakdown` | 7-factor explainable success score breakdown |
| `GET` | `/api/v1/analytics/at-risk-students` | Filterable at-risk students (`department`, `risk_level`, `search`, `immediate_only`) |
| `GET` | `/api/v1/analytics/segments` | 5 student segmentation cohorts with statistics |
| `GET` | `/api/v1/analytics/segments/<segment_id>` | Specific cohort student roster |
| `GET` | `/api/v1/analytics/department-comparison` | Department performance and risk comparison |
| `POST` | `/api/v1/recommendations/<id>/status` | Update recommendation status (`Open`, `In Progress`, `Completed`) |
| `POST` | `/api/v1/interventions/record` | Create/update faculty intervention follow-up record |

---

## 🧪 Running Automated Tests

Run the full automated test suite using `pytest`:
```powershell
python -m pytest tests -v
```
All **89 test cases** verify:
- Four dedicated login pages, authentication security, and session management.
- Multi-portal access control for Student, Faculty, Placement Officer, and Admin.
- At-risk student dual-engine identification and trigger evidence generation.
- Explainable Student Success Score calculations, normalization, and component weights.
- Student segmentation cohort assignment and dynamic roster filtering.
- Actionable recommendation lifecycle and SQLite status persistence.
- Google Gemini LLM API integration, rate limiting, and fallback handling.
- Coding Lab sandboxed Python 3 execution and submission history.



