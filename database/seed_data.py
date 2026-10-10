import os
import sys
import json
import random
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from flask import Flask
from backend.config import Config
from backend.extensions import db
from backend.models.user import User
from backend.models.student import Student
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.intervention import Intervention
from backend.models.recommendation import Recommendation
from backend.models.learning import LmsActivity, LearningPlan, LearningTask
from backend.models.placement import (
    PlacementProfile, PracticeQuestion, PracticeAttempt,
    Company, JobOpportunity, JobApplication, PlacementOffer
)
from backend.models.audit import AuditEvent, CampusKnowledge, EngagementRecord, FeedbackRecord, StudentScore, SystemConfig
from backend.services.success_score import SuccessScoreService
from backend.services.recommendations import RecommendationService

DEPARTMENTS = [
    'Computer Science & Engineering',
    'Electronics & Communication',
    'Information Technology',
    'Artificial Intelligence & Data Science',
    'Mechanical Engineering'
]

SUBJECTS_BY_DEPT = {
    'Computer Science & Engineering': ['Data Structures', 'Database Systems', 'Algorithms', 'Operating Systems', 'Computer Networks', 'Software Engineering'],
    'Electronics & Communication': ['Digital Signal Processing', 'Microprocessors', 'VLSI Design', 'Signals and Systems', 'Embedded Systems', 'Analog Circuits'],
    'Information Technology': ['Web Technologies', 'Cloud Computing', 'Information Security', 'Data Mining', 'Python Programming', 'DevOps'],
    'Artificial Intelligence & Data Science': ['Machine Learning', 'Deep Learning', 'Data Visualization', 'Natural Language Processing', 'Big Data Analytics', 'Statistics'],
    'Mechanical Engineering': ['Thermodynamics', 'Fluid Mechanics', 'Theory of Machines', 'Heat Transfer', 'Manufacturing Tech', 'CAD/CAM']
}

FIRST_NAMES = ['Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Ayaan', 'Krishna', 'Ishaan',
               'Diya', 'Ananya', 'Aadhya', 'Pari', 'Saanvi', 'Myra', 'Anvi', 'Prisha', 'Riya', 'Isha',
               'Kavya', 'Rohan', 'Kiran', 'Tanvi', 'Varun', 'Neha', 'Nikhil', 'Sneha', 'Manish', 'Pooja',
               'Rahul', 'Priya', 'Amit', 'Divya', 'Sanjay', 'Meera', 'Rajesh', 'Sunita', 'Vikram', 'Swati']

LAST_NAMES = ['Sharma', 'Verma', 'Gupta', 'Patel', 'Reddy', 'Rao', 'Nair', 'Singh', 'Kumar', 'Joshi',
              'Mehta', 'Bose', 'Das', 'Iyer', 'Deshmukh', 'Chopra', 'Kulkarni', 'Malhotra', 'Bhat', 'Menon']

def seed_database(app=None):
    if app is None:
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)

    with app.app_context():
        # Ensure tables exist
        db.create_all()
        print("Starting idempotent data seeding for Smart Campus Analytics...")

        # 1. System Configs
        configs = [
            ('scoring_weights', json.dumps(Config.WEIGHTS), 'Institutional composite success score weights'),
            ('attendance_warning_threshold', str(Config.ATTENDANCE_WARNING_THRESHOLD), 'Threshold for attendance warning alerts (%)'),
            ('attendance_critical_threshold', str(Config.ATTENDANCE_CRITICAL_THRESHOLD), 'Threshold for critical attendance intervention (%)'),
            ('attendance_exclude_leave', 'true', 'Exclude approved medical/official leave from denominator'),
            ('risk_high_threshold', str(Config.RISK_HIGH_THRESHOLD), 'Threshold for high academic risk classification'),
            ('risk_medium_threshold', str(Config.RISK_MEDIUM_THRESHOLD), 'Threshold for medium academic risk classification'),
        ]
        for k, v, desc in configs:
            cfg = SystemConfig.query.filter_by(config_key=k).first()
            if not cfg:
                db.session.add(SystemConfig(config_key=k, config_value=v, description=desc))
        db.session.commit()

        # 2. Staff & Admin Users
        demo_users = [
            ('admin', 'admin@campus.edu', 'Admin@123', 'Administrator', 'Admin', None),
            ('dr.sharma', 'dr.sharma@campus.edu', 'Faculty@123', 'Dr. Ramesh Sharma', 'Faculty', 'Computer Science & Engineering'),
            ('prof.anita', 'prof.anita@campus.edu', 'Faculty@123', 'Prof. Anita Deshmukh', 'Faculty', 'Electronics & Communication'),
            ('prof.rajesh', 'prof.rajesh@campus.edu', 'Faculty@123', 'Prof. Rajesh Nair', 'Faculty', 'Information Technology'),
            ('placement_officer', 'placement@campus.edu', 'Placement@123', 'Vikram Malhotra', 'Placement_Officer', None),
        ]
        for uname, uemail, upass, ufullname, urole, udept in demo_users:
            u = User.query.filter_by(username=uname).first()
            if not u:
                u = User(
                    username=uname,
                    email=uemail,
                    full_name=ufullname,
                    role=urole,
                    department=udept
                )
                u.set_password(upass)
                db.session.add(u)
        db.session.commit()

        faculty_users = User.query.filter_by(role='Faculty').all()

        # 3. Generate 110 Fictional Students
        random.seed(42)
        total_students_to_seed = 110
        existing_students_count = Student.query.count()

        if existing_students_count < total_students_to_seed:
            print(f"Generating {total_students_to_seed} fictional student profiles...")
            for i in range(1, total_students_to_seed + 1):
                stu_id = f"STU2024{i:03d}"
                if Student.query.filter_by(student_id=stu_id).first():
                    continue

                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                dept = random.choice(DEPARTMENTS)
                year = random.choice([1, 2, 3, 4])
                semester = (year * 2) - random.choice([0, 1])
                mentor = random.choice(faculty_users) if faculty_users else None

                student = Student(
                    student_id=stu_id,
                    first_name=fname,
                    last_name=lname,
                    email=f"{fname.lower()}.{lname.lower()}{i}@campus.edu",
                    department=dept,
                    academic_year=year,
                    semester=semester,
                    section=random.choice(['A', 'B', 'C']),
                    enrollment_date=date(2024 - year + 1, 8, 1),
                    status=random.choice(['Active', 'Active', 'Active', 'Active', 'At Risk' if i % 7 == 0 else 'Active']),
                    mentor_id=mentor.id if mentor else None
                )
                db.session.add(student)

                # Also create student user accounts for demo testing
                stu_username = f"stu_{fname.lower()}{i}"
                if i == 1:
                    stu_username = "stu_rahul"
                elif i == 2:
                    stu_username = "stu_priya"

                if not User.query.filter_by(username=stu_username).first():
                    stu_user = User(
                        username=stu_username,
                        email=student.email,
                        full_name=f"{fname} {lname}",
                        role='Student',
                        department=dept,
                        student_id=stu_id
                    )
                    stu_user.set_password('Student@123')
                    db.session.add(stu_user)

            db.session.commit()

        students = Student.query.all()
        print(f"Database contains {len(students)} student records.")

        # 4. Seed Academic Records & Subject Scores
        print("Seeding academic marks and semesters...")
        for stu in students:
            # Seed previous semesters up to current semester
            for sem in range(1, stu.semester + 1):
                if not AcademicRecord.query.filter_by(student_id=stu.student_id, semester=sem).first():
                    # Deterministic performance profile with realistic variance
                    base_gpa = random.uniform(5.5, 9.8) if (int(stu.student_id[-3:]) % 6 != 0) else random.uniform(4.5, 6.2)
                    backlogs = 0 if base_gpa >= 6.5 else random.choice([1, 2, 3])
                    gpa = round(base_gpa, 2)
                    
                    ar = AcademicRecord(
                        student_id=stu.student_id,
                        semester=sem,
                        gpa=gpa,
                        cgpa=gpa,
                        credits_completed=20 if backlogs == 0 else 16,
                        total_credits=20,
                        backlogs_count=backlogs,
                        academic_standing='Good' if backlogs == 0 and gpa >= 6.5 else 'At Risk',
                        exam_date=date(2024, 5 if sem % 2 == 0 else 12, 15)
                    )
                    db.session.add(ar)

                # Seed 4-5 subject scores for current semester
                dept_subjects = SUBJECTS_BY_DEPT.get(stu.department, ['Core Subject 1', 'Core Subject 2', 'Core Subject 3', 'Core Subject 4'])
                for sub_idx, sub_name in enumerate(dept_subjects[:4]):
                    code = f"{stu.department[:3].upper()}{sem}0{sub_idx+1}"
                    if not SubjectScore.query.filter_by(student_id=stu.student_id, semester=sem, subject_code=code).first():
                        marks = random.uniform(50, 95) if (int(stu.student_id[-3:]) % 8 != 0) else random.uniform(32, 58)
                        marks = round(marks, 1)
                        is_pass = marks >= 40.0
                        grade = 'O' if marks >= 90 else ('A+' if marks >= 80 else ('A' if marks >= 70 else ('B+' if marks >= 60 else ('B' if marks >= 50 else ('C' if marks >= 40 else 'F')))))
                        
                        ss = SubjectScore(
                            student_id=stu.student_id,
                            semester=sem,
                            subject_code=code,
                            subject_name=sub_name,
                            internal_marks=round(marks * 0.3, 1),
                            external_marks=round(marks * 0.7, 1),
                            marks_obtained=marks,
                            max_marks=100.0,
                            grade=grade,
                            is_passed=is_pass
                        )
                        db.session.add(ss)

        db.session.commit()

        # 5. Seed Attendance Sessions & Records
        print("Seeding attendance sessions & records...")
        if AttendanceSession.query.count() < 25:
            base_date = date.today() - timedelta(days=45)
            session_counter = 0

            for dept in DEPARTMENTS:
                dept_students = Student.query.filter_by(department=dept).all()
                if not dept_students:
                    continue
                dept_subjects = SUBJECTS_BY_DEPT.get(dept, ['Subject A', 'Subject B'])

                for day_offset in range(0, 45, 3):
                    s_date = base_date + timedelta(days=day_offset)
                    subj = random.choice(dept_subjects)
                    mentor = random.choice(faculty_users) if faculty_users else None

                    session = AttendanceSession(
                        department=dept,
                        class_code=f"{dept[:3].upper()}-SEM3-A",
                        semester=3,
                        subject=subj,
                        session_date=s_date,
                        time_slot="09:00 - 10:00 AM",
                        faculty_id=mentor.id if mentor else None
                    )
                    db.session.add(session)
                    db.session.flush()

                    for stu in dept_students:
                        # Some students have lower attendance for realistic variance
                        stu_num = int(stu.student_id[-3:])
                        if stu_num % 10 == 0:
                            # Critical attendance student (~55%)
                            status = random.choices(['Present', 'Absent', 'On Leave'], weights=[55, 40, 5])[0]
                        elif stu_num % 5 == 0:
                            # Warning attendance student (~70%)
                            status = random.choices(['Present', 'Absent', 'On Leave'], weights=[70, 25, 5])[0]
                        else:
                            # Regular good attendance (~88%)
                            status = random.choices(['Present', 'Absent', 'On Leave'], weights=[88, 8, 4])[0]

                        rec = AttendanceRecord(
                            session_id=session.id,
                            student_id=stu.student_id,
                            status=status,
                            updated_by=mentor.id if mentor else None
                        )
                        db.session.add(rec)
                    
                    session_counter += 1

            db.session.commit()
            print(f"Created {session_counter} attendance sessions with records.")

        # 6. Seed LMS Activities
        print("Seeding LMS online engagement...")
        for stu in students:
            dept_subjects = SUBJECTS_BY_DEPT.get(stu.department, ['Core Subject 1', 'Core Subject 2'])
            for sub_name in dept_subjects[:3]:
                if not LmsActivity.query.filter_by(student_id=stu.student_id, course_name=sub_name).first():
                    stu_num = int(stu.student_id[-3:])
                    mod_done = random.randint(3, 10) if stu_num % 7 != 0 else random.randint(1, 4)
                    time_hrs = round(mod_done * random.uniform(1.5, 3.5), 1)
                    quiz = round(random.uniform(60, 95) if mod_done > 4 else random.uniform(35, 65), 1)

                    lms = LmsActivity(
                        student_id=stu.student_id,
                        course_name=sub_name,
                        course_code=f"{stu.department[:3].upper()}-LMS",
                        modules_completed=mod_done,
                        total_modules=10,
                        time_spent_hours=time_hrs,
                        quiz_score_avg=quiz,
                        assignment_submission_rate=round(random.uniform(70, 100), 1)
                    )
                    db.session.add(lms)
        db.session.commit()

        # 7. Seed Engagement & Feedback Records
        print("Seeding co-curricular engagement and faculty feedback...")
        activities_pool = [
            ('Hackathon', 'Smart India Hackathon Internal Round', 'Winner', 30.0),
            ('Workshop', 'Hands-on Cloud & Kubernetes Workshop', 'Participant', 15.0),
            ('Club', 'Open Source Developers Club Lead', 'Organizer', 25.0),
            ('Seminar', 'AI in Healthcare Guest Lecture', 'Participant', 10.0),
            ('Sports', 'Inter-College Badminton Tournament', 'Participant', 15.0)
        ]
        for stu in students:
            if not EngagementRecord.query.filter_by(student_id=stu.student_id).first():
                num_acts = random.randint(1, 3)
                for _ in range(num_acts):
                    act_type, title, level, pts = random.choice(activities_pool)
                    db.session.add(EngagementRecord(
                        student_id=stu.student_id,
                        activity_type=act_type,
                        title=title,
                        participation_level=level,
                        score_points=pts,
                        event_date=date.today() - timedelta(days=random.randint(10, 120))
                    ))

            if not FeedbackRecord.query.filter_by(student_id=stu.student_id).first():
                mentor = random.choice(faculty_users) if faculty_users else None
                b_score = round(random.uniform(65, 95), 1)
                db.session.add(FeedbackRecord(
                    student_id=stu.student_id,
                    faculty_id=mentor.id if mentor else None,
                    behavioral_score=b_score,
                    punctuality_score=round(random.uniform(60, 95), 1),
                    teamwork_score=round(random.uniform(70, 98), 1),
                    initiative_score=round(random.uniform(60, 92), 1),
                    general_notes="Demonstrates steady commitment and good classroom participation."
                ))
        db.session.commit()

        # 8. Seed Placement Profiles & Practice Questions
        print("Seeding placement profiles and practice question bank...")
        target_roles = ['Software Developer', 'Frontend Developer', 'Backend Developer', 'Data Analyst', 'QA Engineer', 'Cloud or IT Support Associate']
        
        for stu in students:
            if not PlacementProfile.query.filter_by(student_id=stu.student_id).first():
                role = random.choice(target_roles)
                skills_sample = random.sample(['Python', 'Java', 'SQL', 'Data Structures', 'Git', 'JavaScript', 'React', 'Linux', 'Pandas', 'REST APIs'], k=5)
                
                apt = round(random.uniform(50, 95), 1)
                cod = round(random.uniform(45, 95), 1)
                comm = round(random.uniform(55, 92), 1)
                interv = round(random.uniform(50, 90), 1)
                
                prof = PlacementProfile(
                    student_id=stu.student_id,
                    target_role=role,
                    aptitude_score=apt,
                    coding_score=cod,
                    communication_score=comm,
                    interview_score=interv,
                    resume_score=round(random.uniform(60, 95), 1),
                    skills_json=', '.join(skills_sample),
                    placement_status='Seeking' if stu.academic_year < 4 else random.choice(['Seeking', 'Placed', 'Seeking'])
                )
                prof.calculate_readiness()
                db.session.add(prof)

        # Question Bank
        questions_pool = [
            ('Aptitude', 'Quantitative', 'Medium', 'A train running at 60 km/hr crosses a pole in 9 seconds. What is the length of the train?', '["120 m", "150 m", "180 m", "200 m"]', '150 m', 'Speed = 60 * 5/18 = 50/3 m/s. Length = Speed * Time = (50/3) * 9 = 150 meters.'),
            ('Aptitude', 'Logical Reasoning', 'Easy', 'Find the next number in the series: 3, 6, 12, 24, 48, ?', '["72", "96", "84", "108"]', '96', 'Each number is multiplied by 2. 48 * 2 = 96.'),
            ('Aptitude', 'Data Interpretation', 'Medium', 'If 20% of an alloy is copper and 30% is zinc, what is the ratio of copper to zinc in 500g of alloy?', '["2:3", "3:2", "1:2", "3:5"]', '2:3', 'Ratio of percentages is 20:30 = 2:3 directly.'),
            ('Coding', 'Data Structures', 'Medium', 'What is the average time complexity of searching an element in a balanced Binary Search Tree (BST)?', '["O(1)", "O(n)", "O(log n)", "O(n log n)"]', 'O(log n)', 'In a balanced BST, tree height is log2(n), making search time O(log n).'),
            ('Coding', 'Algorithms', 'Easy', 'Which sorting algorithm has the best-case time complexity of O(n) when the array is already sorted?', '["Quick Sort", "Insertion Sort", "Merge Sort", "Selection Sort"]', 'Insertion Sort', 'Insertion sort runs in linear O(n) time for already sorted arrays.'),
            ('Coding', 'Python Basics', 'Easy', 'What is the output of `type([1, 2, 3])` in Python?', '["tuple", "list", "array", "set"]', 'list', 'Square brackets define Python standard lists.'),
            ('Communication', 'Verbal Ability', 'Easy', 'Select the appropriate synonym for "METICULOUS":', '["Careless", "Thorough & Precise", "Hasty", "Vague"]', 'Thorough & Precise', 'Meticulous means showing great attention to detail and precision.'),
            ('Communication', 'Email Etiquette', 'Medium', 'When writing an email to request academic leave, what is the best opening line?', '["Hey prof, need off tomorrow.", "Dear Professor Sharma, I am writing to formally request medical leave...", "I won\'t come to class.", "Urgent leave request."] ', 'Dear Professor Sharma, I am writing to formally request medical leave...', 'Professional salutations and clear formal context are essential in institutional communications.'),
            ('Interview', 'Behavioral', 'Medium', 'In the STAR interview methodology, what does the letter "R" stand for?', '["Reason", "Result", "Reaction", "Responsibility"]', 'Result', 'STAR stands for Situation, Task, Action, and Result.'),
            ('Interview', 'Technical HR', 'Medium', 'How should you answer the common question: "What is your biggest weakness?"', '["I am a perfectionist and work too hard.", "State a genuine non-critical skill gap and the concrete steps you are taking to improve.", "I have no weaknesses.", "I dislike team members."] ', 'State a genuine non-critical skill gap and the concrete steps you are taking to improve.', 'Authentic self-awareness paired with an active learning remedy is the most credible response.')
        ]
        for cat, topic, diff, qtext, opts, ans, expl in questions_pool:
            if not PracticeQuestion.query.filter_by(question_text=qtext).first():
                db.session.add(PracticeQuestion(
                    category=cat,
                    topic=topic,
                    difficulty=diff,
                    question_text=qtext,
                    options_json=opts,
                    correct_answer=ans,
                    explanation=expl
                ))

        db.session.commit()

        # 8b. Seed Placement Companies & Opportunities
        print("Seeding recruitment companies, jobs, and placement drives...")
        companies_data = [
            ('Google Cloud Labs', 'Cloud Computing & AI', 'https://cloud.google.com', 'Sarah Jenkins', 'sarah.j@google.com', '+91-80-67210000', 7.5, 'Computer Science & Engineering,Information Technology,Artificial Intelligence & Data Science', 'Python, Go, Kubernetes, Cloud Architecture, DSA'),
            ('Microsoft IDC', 'Software & Cloud Platforms', 'https://microsoft.com', 'Anil Verma', 'anil.v@microsoft.com', '+91-80-67890000', 7.0, 'Computer Science & Engineering,Information Technology,Electronics & Communication', 'C++, C#, Data Structures, Distributed Systems, SQL'),
            ('Amazon Web Services', 'E-Commerce & Cloud Infrastructure', 'https://aws.amazon.com', 'Kavita Rao', 'kavita.r@amazon.com', '+91-80-45670000', 6.8, 'Computer Science & Engineering,Information Technology,Artificial Intelligence & Data Science,Electronics & Communication', 'Java, Python, AWS Services, System Design, Algorithms'),
            ('TCS Digital', 'Enterprise IT & Digital Transformation', 'https://tcs.com', 'Rohan Mathur', 'rohan.m@tcs.com', '+91-22-67780000', 6.0, 'Computer Science & Engineering,Information Technology,Electronics & Communication,Mechanical Engineering', 'Python, Java, Web Technologies, Database Systems'),
            ('Infosys Springboard', 'Technology Consulting', 'https://infosys.com', 'Pooja Hegde', 'pooja.h@infosys.com', '+91-80-28520000', 6.0, 'Computer Science & Engineering,Information Technology,Electronics & Communication,Mechanical Engineering', 'JavaScript, Python, Problem Solving, Communication')
        ]

        for cname, cind, cweb, cperson, cmail, cphone, cmgpa, cdepts, cskills in companies_data:
            if not Company.query.filter_by(name=cname).first():
                db.session.add(Company(
                    name=cname,
                    industry=cind,
                    website=cweb,
                    contact_person=cperson,
                    contact_email=cmail,
                    contact_phone=cphone,
                    min_cgpa=cmgpa,
                    eligible_departments=cdepts,
                    required_skills=cskills,
                    status='Active'
                ))
        db.session.commit()

        # Seed Jobs & Drives
        comp_google = Company.query.filter_by(name='Google Cloud Labs').first()
        comp_msft = Company.query.filter_by(name='Microsoft IDC').first()
        comp_aws = Company.query.filter_by(name='Amazon Web Services').first()
        comp_tcs = Company.query.filter_by(name='TCS Digital').first()

        jobs_data = [
            (comp_google.id if comp_google else 1, 'Cloud Solutions Engineer', 'Full-time', 'Bengaluru (Hybrid)', '14.5 LPA', 7.5, 70.0, 'Computer Science & Engineering,Information Technology', 'Python, Cloud Infrastructure, Docker, Networking', date.today() + timedelta(days=14), date.today() + timedelta(days=20)),
            (comp_msft.id if comp_msft else 2, 'Software Development Engineer - 1', 'Full-time', 'Hyderabad', '16.0 LPA', 7.0, 65.0, 'Computer Science & Engineering,Information Technology,Electronics & Communication', 'Data Structures, Algorithms, C++, Problem Solving', date.today() + timedelta(days=10), date.today() + timedelta(days=16)),
            (comp_aws.id if comp_aws else 3, 'DevOps & Cloud Associate', 'Full-time', 'Bengaluru', '12.0 LPA', 6.8, 60.0, 'Computer Science & Engineering,Information Technology,Artificial Intelligence & Data Science', 'Linux, Python, CI/CD, AWS Cloud, Git', date.today() + timedelta(days=7), date.today() + timedelta(days=12)),
            (comp_tcs.id if comp_tcs else 4, 'Digital Systems Engineer', 'Full-time', 'Pan India', '7.5 LPA', 6.0, 50.0, 'Computer Science & Engineering,Information Technology,Electronics & Communication,Mechanical Engineering', 'Python, SQL, Communication, Aptitude', date.today() + timedelta(days=21), date.today() + timedelta(days=28))
        ]

        for cid, jtitle, jtype, jloc, jctc, jgpa, jread, jdepts, jskills, jdl, jdrive in jobs_data:
            if not JobOpportunity.query.filter_by(title=jtitle, company_id=cid).first():
                db.session.add(JobOpportunity(
                    company_id=cid,
                    title=jtitle,
                    role_type=jtype,
                    location=jloc,
                    ctc_package=jctc,
                    min_cgpa=jgpa,
                    min_readiness=jread,
                    eligible_departments=jdepts,
                    required_skills=jskills,
                    application_deadline=jdl,
                    drive_date=jdrive,
                    status='Active'
                ))
        db.session.commit()

        # Seed Job Applications and Offers for senior students (Semester 7 or 8)
        senior_students = Student.query.filter(Student.semester >= 5).limit(25).all()
        active_jobs = JobOpportunity.query.all()

        if senior_students and active_jobs:
            stages_pool = ['Applied', 'Shortlisted', 'Interview', 'Selected', 'Offer Accepted']
            for s_idx, stu in enumerate(senior_students):
                job = active_jobs[s_idx % len(active_jobs)]
                if not JobApplication.query.filter_by(student_id=stu.student_id, job_id=job.id).first():
                    stage = stages_pool[s_idx % len(stages_pool)]
                    db.session.add(JobApplication(
                        student_id=stu.student_id,
                        job_id=job.id,
                        stage=stage,
                        round_cleared='Technical Round 1' if stage in ['Interview', 'Selected', 'Offer Accepted'] else 'Aptitude Test',
                        applied_at=datetime.utcnow() - timedelta(days=random.randint(3, 15))
                    ))

                    # If Selected or Offer Accepted, create PlacementOffer
                    if stage in ['Selected', 'Offer Accepted']:
                        if not PlacementOffer.query.filter_by(student_id=stu.student_id, job_title=job.title).first():
                            db.session.add(PlacementOffer(
                                student_id=stu.student_id,
                                company_id=job.company_id,
                                company_name=job.company.name if job.company else 'Partner Tech',
                                job_title=job.title,
                                ctc_package=job.ctc_package,
                                ctc_numeric=float(job.ctc_package.replace(' LPA', '').strip()) if 'LPA' in job.ctc_package else 8.0,
                                offer_date=date.today() - timedelta(days=random.randint(1, 5)),
                                status='Accepted' if stage == 'Offer Accepted' else 'Offered'
                            ))
                            # Mark placement profile status
                            prof = PlacementProfile.query.filter_by(student_id=stu.student_id).first()
                            if prof:
                                prof.placement_status = 'Placed'

        db.session.commit()
        print("Seeding campus AI knowledge base...")
        kb_entries = [
            ('Attendance', 'Minimum Attendance Requirement Policy', 'attendance, percentage, shortage, eligibility, condonation, 75%',
             'As per institutional academic regulations, students must maintain a minimum of 75% aggregate attendance in each registered course to be eligible for end-semester examinations. Medical leave up to 10% can be condoned upon submission of verified medical certificates within 7 working days to the Department Head.',
             'Academic Dean Office', 'dean.academics@campus.edu'),
            
            ('Examination', 'End-Semester Exam Hall Ticket & Revaluation', 'exam, hall ticket, dates, revaluation, backlog exam, fee, grading',
             'End-semester examinations commence in May (Even Semesters) and December (Odd Semesters). Hall tickets can be downloaded via the student portal 7 days prior to exams if attendance criteria are met. Revaluation requests must be filed within 14 days of result declaration with the Examination Controller.',
             'Controller of Examinations', 'coe@campus.edu'),

            ('Library', 'Central Digital Library Access & Timings', 'library, books, journals, timings, digital library, wifi, borrowing, fine',
             'The Central Library is open Monday to Saturday from 08:00 AM to 10:00 PM and Sundays from 09:00 AM to 05:00 PM. Students can borrow up to 4 physical books for 15 days. Digital research journals (IEEE, ACM, ScienceDirect) are accessible 24/7 on the campus VPN using student credentials.',
             'Chief Librarian', 'library@campus.edu'),

            ('Placement', 'Campus Placement Eligibility & Training Drives', 'placement, internship, eligibility, resume, interview, tpo, drive, companies',
             'Training & Placement Cell (T&P) initiates pre-placement training from Semester 5. To be eligible for Tier-1 recruitment drives, students must maintain a CGPA of 7.0 or above with zero standing backlogs and at least 75% attendance in placement bootcamps.',
             'Placement Officer', 'placement@campus.edu'),

            ('Mentoring', 'Faculty Mentoring & Counseling Services', 'mentor, advisor, counselor, mental health, stress, guidance, grievance',
             'Every enrolled student is assigned a dedicated Faculty Mentor for academic guidance and career mentoring. Additionally, the Campus Student Wellness & Counseling Center offers confidential 1-on-1 counseling sessions Mon-Fri (10 AM - 4 PM) in Block B, Room 204.',
             'Student Wellness Coordinator', 'wellness@campus.edu'),

            ('Facilities', 'Hostel, Transport & Wi-Fi Network Access', 'hostel, bus, transport, wifi, sports, cafeteria, id card, medical emergency',
             'Campus Wi-Fi (SSID: SmartCampus-Secure) requires 802.1x authentication with your student ID and default password. College bus routes cover all major city points. The Campus Health Center operates 24/7 with emergency ambulance support at Ext. 108.',
             'Campus Administration Desk', 'admin.facilities@campus.edu')
        ]
        for cat, top, keys, cont, cperson, cmail in kb_entries:
            if not CampusKnowledge.query.filter_by(topic=top).first():
                db.session.add(CampusKnowledge(
                    category=cat,
                    topic=top,
                    keywords=keys,
                    content=cont,
                    contact_person=cperson,
                    contact_email=cmail,
                    is_verified=True
                ))
        db.session.commit()

        # 10. Seed Interventions
        print("Seeding mentoring interventions...")
        if Intervention.query.count() < 10:
            at_risk_students = Student.query.filter(Student.status == 'At Risk').limit(8).all()
            for stu in at_risk_students:
                mentor = random.choice(faculty_users) if faculty_users else None
                db.session.add(Intervention(
                    student_id=stu.student_id,
                    faculty_id=mentor.id if mentor else None,
                    title="Attendance Shortage & Subject Backlog Counseling",
                    category="Academic",
                    priority="High",
                    status=random.choice(['Open', 'In Progress', 'Completed']),
                    session_date=date.today() - timedelta(days=random.randint(5, 20)),
                    follow_up_date=date.today() + timedelta(days=random.randint(-3, 10)),
                    notes="Met with student to discuss low attendance in Data Structures and 1 active backlog. Student cited transportation issues.",
                    action_items="1. Student to attend Saturday remedial classes.\n2. Submit attendance certificate from mentor weekly.",
                    outcome_notes="Student showed 10% attendance improvement in subsequent 2 weeks."
                ))
            db.session.commit()

        # 11. Calculate Success Scores & Recommendations for all students
        print("Computing composite student success scores and automated recommendations...")
        SuccessScoreService.recalculate_all_scores()
        for stu in students[:30]:
            RecommendationService.generate_student_recommendations(stu, save_db=True)

        # 12. Export Snapshot CSV files to database/data/ for reproducibility
        data_dir = os.path.join(BASE_DIR, 'database', 'data')
        os.makedirs(data_dir, exist_ok=True)
        print("Exporting database records into reproducible CSV snapshots...")

        # Export Academic CSV
        acads = [a.to_dict() for a in AcademicRecord.query.all()]
        pd.DataFrame(acads).to_csv(os.path.join(data_dir, 'academic.csv'), index=False)

        # Export Attendance CSV
        atts = [r.to_dict() for r in AttendanceRecord.query.all()]
        pd.DataFrame(atts).to_csv(os.path.join(data_dir, 'attendance.csv'), index=False)

        # Export LMS CSV
        lms_recs = [l.to_dict() for l in LmsActivity.query.all()]
        pd.DataFrame(lms_recs).to_csv(os.path.join(data_dir, 'lms.csv'), index=False)

        # Export Engagement CSV
        engs = [e.to_dict() for e in EngagementRecord.query.all()]
        pd.DataFrame(engs).to_csv(os.path.join(data_dir, 'engagement.csv'), index=False)

        # Export Placement CSV
        placs = [p.to_dict() for p in PlacementProfile.query.all()]
        pd.DataFrame(placs).to_csv(os.path.join(data_dir, 'placement.csv'), index=False)

        # Export Skills CSV
        skills_data = []
        for p in PlacementProfile.query.all():
            skills_data.append({
                'student_id': p.student_id,
                'target_role': p.target_role,
                'skills': p.skills_json,
                'coding_score': p.coding_score,
                'aptitude_score': p.aptitude_score
            })
        pd.DataFrame(skills_data).to_csv(os.path.join(data_dir, 'skills.csv'), index=False)

        # Export Feedback CSV
        fbs = [f.to_dict() for f in FeedbackRecord.query.all()]
        pd.DataFrame(fbs).to_csv(os.path.join(data_dir, 'feedback.csv'), index=False)

        print("Data seeding and CSV export completed successfully!")

if __name__ == '__main__':
    seed_database()
