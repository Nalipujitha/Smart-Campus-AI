from backend.services.risk_analysis import RiskAnalysisService

def test_risk_evaluation_high_risk():
    res = RiskAnalysisService.evaluate_risk(
        student_id='STU001',
        success_score=42.0,
        academic_score=40.0,
        attendance_score=55.0
    )
    assert res['risk_level'] == 'High'
    assert len(res['risk_factors']) > 0

def test_risk_evaluation_low_risk():
    res = RiskAnalysisService.evaluate_risk(
        student_id='STU002',
        success_score=88.0,
        academic_score=90.0,
        attendance_score=95.0
    )
    assert res['risk_level'] == 'Low'
