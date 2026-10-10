-- Smart Campus Analytics - SQLite Database Schema
-- Standard SQL Table Definitions for SQLite

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'Student',
    department VARCHAR(64),
    student_id VARCHAR(32) REFERENCES students(student_id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) UNIQUE NOT NULL,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    department VARCHAR(64) NOT NULL,
    academic_year INTEGER NOT NULL DEFAULT 1,
    semester INTEGER NOT NULL DEFAULT 1,
    section VARCHAR(8) DEFAULT 'A',
    enrollment_date DATE,
    status VARCHAR(32) NOT NULL DEFAULT 'Active',
    mentor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department VARCHAR(64) NOT NULL,
    class_code VARCHAR(32) NOT NULL,
    semester INTEGER NOT NULL,
    subject VARCHAR(120) NOT NULL,
    session_date DATE NOT NULL,
    time_slot VARCHAR(32),
    faculty_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_cancelled BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    status VARCHAR(16) NOT NULL, -- 'Present', 'Absent', 'On Leave'
    remarks VARCHAR(255),
    correction_reason VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_session_student_attendance UNIQUE (session_id, student_id)
);

CREATE TABLE IF NOT EXISTS academic_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    semester INTEGER NOT NULL,
    gpa REAL NOT NULL,
    cgpa REAL,
    credits_completed INTEGER NOT NULL DEFAULT 20,
    total_credits INTEGER NOT NULL DEFAULT 20,
    backlogs_count INTEGER NOT NULL DEFAULT 0,
    academic_standing VARCHAR(32) DEFAULT 'Good',
    exam_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_semester_academic UNIQUE (student_id, semester)
);

CREATE TABLE IF NOT EXISTS subject_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    semester INTEGER NOT NULL,
    subject_code VARCHAR(32) NOT NULL,
    subject_name VARCHAR(120) NOT NULL,
    internal_marks REAL DEFAULT 0,
    external_marks REAL DEFAULT 0,
    marks_obtained REAL NOT NULL,
    max_marks REAL NOT NULL DEFAULT 100.0,
    grade VARCHAR(4),
    is_passed BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    faculty_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'Academic',
    priority VARCHAR(16) NOT NULL DEFAULT 'Medium',
    status VARCHAR(32) NOT NULL DEFAULT 'Open',
    session_date DATE NOT NULL,
    follow_up_date DATE,
    notes TEXT NOT NULL,
    action_items TEXT,
    outcome_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'Academic',
    priority VARCHAR(16) NOT NULL DEFAULT 'Medium',
    reason TEXT NOT NULL,
    trigger_data TEXT,
    suggested_action TEXT NOT NULL,
    status VARCHAR(32) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lms_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    course_name VARCHAR(120) NOT NULL,
    course_code VARCHAR(32),
    modules_completed INTEGER NOT NULL DEFAULT 0,
    total_modules INTEGER NOT NULL DEFAULT 10,
    time_spent_hours REAL NOT NULL DEFAULT 0.0,
    quiz_score_avg REAL NOT NULL DEFAULT 0.0,
    assignment_submission_rate REAL DEFAULT 100.0,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    target_skill VARCHAR(120) NOT NULL,
    weekly_goal_hours REAL DEFAULT 5.0,
    status VARCHAR(32) DEFAULT 'In Progress',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES learning_plans(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    resource_type VARCHAR(32) DEFAULT 'Article',
    estimated_minutes INTEGER DEFAULT 30,
    is_completed BOOLEAN DEFAULT 0,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS placement_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) UNIQUE NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    target_role VARCHAR(120) DEFAULT 'Software Developer',
    secondary_role VARCHAR(120),
    aptitude_score REAL DEFAULT 0.0,
    coding_score REAL DEFAULT 0.0,
    communication_score REAL DEFAULT 0.0,
    interview_score REAL DEFAULT 0.0,
    resume_score REAL DEFAULT 0.0,
    readiness_percentage REAL DEFAULT 0.0,
    placement_status VARCHAR(32) DEFAULT 'Seeking',
    skills_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS practice_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(32) NOT NULL,
    topic VARCHAR(64) NOT NULL,
    difficulty VARCHAR(16) DEFAULT 'Medium',
    question_text TEXT NOT NULL,
    options_json TEXT,
    correct_answer VARCHAR(255) NOT NULL,
    explanation TEXT,
    code_template TEXT
);

CREATE TABLE IF NOT EXISTS practice_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES practice_questions(id) ON DELETE CASCADE,
    user_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    score_earned REAL DEFAULT 0.0,
    feedback TEXT,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    module VARCHAR(64) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campus_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(64) NOT NULL,
    topic VARCHAR(120) NOT NULL,
    keywords VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    contact_person VARCHAR(120),
    contact_email VARCHAR(120),
    is_verified BOOLEAN DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagement_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    activity_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    participation_level VARCHAR(32) DEFAULT 'Participant',
    score_points REAL DEFAULT 10.0,
    event_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    faculty_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    behavioral_score REAL DEFAULT 80.0,
    punctuality_score REAL DEFAULT 80.0,
    teamwork_score REAL DEFAULT 80.0,
    initiative_score REAL DEFAULT 80.0,
    general_notes TEXT,
    term VARCHAR(32) DEFAULT 'Midterm',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(32) UNIQUE NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    academic_component REAL DEFAULT 0.0,
    attendance_component REAL DEFAULT 0.0,
    lms_component REAL DEFAULT 0.0,
    engagement_component REAL DEFAULT 0.0,
    placement_component REAL DEFAULT 0.0,
    skills_component REAL DEFAULT 0.0,
    feedback_component REAL DEFAULT 0.0,
    success_score REAL DEFAULT 0.0,
    risk_level VARCHAR(32) DEFAULT 'Low',
    risk_factors_json TEXT,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(64) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'New Chat',
    model_name VARCHAR(100) DEFAULT 'gemini-1.5-flash',
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    model_name VARCHAR(100),
    is_fallback BOOLEAN NOT NULL DEFAULT 0,
    verified_context_used BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

