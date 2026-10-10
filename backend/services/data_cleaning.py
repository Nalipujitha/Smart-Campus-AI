import re
from datetime import datetime
import pandas as pd
import numpy as np

class DataCleaningService:
    """
    Data cleaning and validation service for smart campus analytics.
    Handles dirty CSV records, missing fields, malformed values, and type casting.
    """

    @staticmethod
    def clean_student_id(val):
        if not val or pd.isna(val):
            return None
        cleaned = str(val).strip().upper()
        # Ensure valid format e.g. STU2024001 or alphanumeric
        if re.match(r'^[A-Z0-9\-_]{3,20}$', cleaned):
            return cleaned
        return None

    @staticmethod
    def clean_email(val):
        if not val or pd.isna(val):
            return None
        val = str(val).strip().lower()
        if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', val):
            return val
        return None

    @staticmethod
    def clean_numeric(val, min_val=0.0, max_val=100.0, default=None):
        if val is None or pd.isna(val):
            return default
        try:
            num = float(val)
            if min_val <= num <= max_val:
                return round(num, 2)
            elif num < min_val:
                return min_val
            else:
                return max_val
        except (ValueError, TypeError):
            return default

    @staticmethod
    def clean_date(val, date_format="%Y-%m-%d"):
        if not val or pd.isna(val):
            return None
        val_str = str(val).strip()
        for fmt in (date_format, "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(val_str, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def clean_attendance_status(val):
        if not val or pd.isna(val):
            return 'Absent'
        val = str(val).strip().title()
        if val in ['Present', 'P', '1', 'True']:
            return 'Present'
        elif val in ['On Leave', 'Leave', 'L', 'Approved Leave']:
            return 'On Leave'
        return 'Absent'

    @classmethod
    def validate_attendance_df(cls, df):
        """
        Validates an uploaded attendance DataFrame.
        Returns: (cleaned_records, errors_list)
        """
        errors = []
        cleaned = []
        required_cols = {'student_id', 'status'}
        
        # normalize column names
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        missing_req = required_cols - set(df.columns)
        if missing_req:
            errors.append(f"Missing mandatory columns: {', '.join(missing_req)}")
            return [], errors

        for idx, row in df.iterrows():
            row_num = idx + 2 # account for 1-based indexing & header
            raw_id = row.get('student_id')
            student_id = cls.clean_student_id(raw_id)
            if not student_id:
                errors.append(f"Row {row_num}: Invalid or missing student_id '{raw_id}'")
                continue

            status = cls.clean_attendance_status(row.get('status'))
            remarks = str(row.get('remarks', '')).strip() if not pd.isna(row.get('remarks')) else ''
            
            cleaned.append({
                'row_num': row_num,
                'student_id': student_id,
                'status': status,
                'remarks': remarks
            })

        return cleaned, errors
