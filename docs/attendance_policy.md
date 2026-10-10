# Institutional Attendance Policy & Calculation Specification

## 1. Core Attendance Formula

The Smart Campus Analytics attendance engine evaluates student eligibility based on verified session records:

$$\text{Attendance Percentage} = \frac{\text{Present Sessions}}{\text{Eligible Sessions}} \times 100$$

### Approved Leave Handling
When `ATTENDANCE_EXCLUDE_APPROVED_LEAVE` is enabled:
$$\text{Eligible Sessions} = \text{Total Sessions Conducted} - \text{Approved Leave Sessions}$$

If no eligible sessions exist ($\text{Eligible Sessions} = 0$), the system returns `Not Available (N/A)` rather than throwing a division by zero error.

## 2. Attendance Warning & Critical Cutoffs
- **Warning Threshold (75.0%)**: Default institutional threshold below which automated advisory notices and notifications to faculty mentors are triggered.
- **Critical Threshold (65.0%)**: Escalates into a high-priority faculty mentoring case requiring remedial action items.

## 3. Data Integrity & Audit Safeguards
- **Duplicate Prevention**: Database-level unique constraint on `(session_id, student_id)` prevents accidental multiple submissions.
- **Correction Audit Trails**: Any subsequent modification to attendance status requires a mandatory justification reason logged into `audit_events`.
