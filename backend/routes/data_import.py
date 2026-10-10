import os
import io
import pandas as pd
from flask import Blueprint, render_template, request, flash, redirect, url_for
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.services.data_cleaning import DataCleaningService
from backend.services.attendance_service import AttendanceService
from backend.models.student import Student
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.audit import AuditEvent
from backend.extensions import db

data_import_bp = Blueprint('data_import', __name__)

@data_import_bp.route('/')
@login_required
@roles_required('Admin', 'Faculty')
def index():
    user = get_current_user()
    return render_template('data_import.html', user=user)

@data_import_bp.route('/upload', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def upload_data():
    dataset_type = request.form.get('dataset_type')
    if 'csv_file' not in request.files:
        flash("No file selected for upload.", "danger")
        return redirect(url_for('data_import.index'))

    file = request.files['csv_file']
    if file.filename == '':
        flash("No selected file.", "danger")
        return redirect(url_for('data_import.index'))

    if not file.filename.endswith('.csv'):
        flash("Only standard .csv files are supported.", "danger")
        return redirect(url_for('data_import.index'))

    try:
        df = pd.read_csv(file)
    except Exception as e:
        flash(f"Error parsing CSV: {str(e)}", "danger")
        return redirect(url_for('data_import.index'))

    user = get_current_user()
    inserted_count = 0
    errors = []

    if dataset_type == 'attendance':
        cleaned_records, errs = DataCleaningService.validate_attendance_df(df)
        if errs:
            errors.extend(errs)
        else:
            flash(f"Successfully validated {len(cleaned_records)} attendance rows.", "info")

    elif dataset_type == 'students':
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        for idx, row in df.iterrows():
            row_num = idx + 2
            sid = DataCleaningService.clean_student_id(row.get('student_id'))
            email = DataCleaningService.clean_email(row.get('email'))
            fname = str(row.get('first_name', '')).strip()
            lname = str(row.get('last_name', '')).strip()
            dept = str(row.get('department', 'Computer Science & Engineering')).strip()
            
            if not sid or not fname or not lname or not email:
                errors.append(f"Row {row_num}: Missing or invalid mandatory student field(s).")
                continue

            existing = Student.query.filter_by(student_id=sid).first()
            if existing:
                errors.append(f"Row {row_num}: Student ID '{sid}' already exists in database.")
                continue

            stu = Student(
                student_id=sid,
                first_name=fname,
                last_name=lname,
                email=email,
                department=dept,
                academic_year=int(row.get('academic_year', 1)),
                semester=int(row.get('semester', 1)),
                section=str(row.get('section', 'A')).strip()
            )
            db.session.add(stu)
            inserted_count += 1

        if inserted_count > 0:
            db.session.commit()
            from backend.services.success_score import SuccessScoreService
            SuccessScoreService.recalculate_all_scores()

    audit = AuditEvent(
        user_id=user.id,
        action="DATA_IMPORT",
        module="DataImport",
        details=f"Uploaded {dataset_type} CSV. Inserted: {inserted_count}, Errors: {len(errors)}."
    )
    db.session.add(audit)
    db.session.commit()

    return render_template(
        'data_import.html',
        user=user,
        imported_count=inserted_count,
        errors=errors,
        completed=True,
        dataset_type=dataset_type
    )
