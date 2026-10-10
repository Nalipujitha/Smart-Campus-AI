from datetime import date
from tests.conftest import login_client
from backend.models.intervention import Intervention

def test_create_and_update_intervention(client, app):
    login_client(client, 'test_faculty', 'Faculty@123')
    response = client.post('/interventions/create', data={
        'student_id': 'STU_TEST001',
        'title': 'Academic Mentoring & Remedial Schedule',
        'category': 'Academic',
        'priority': 'High',
        'session_date': date.today().isoformat(),
        'notes': 'Met with student regarding test performance.',
        'action_items': 'Complete 3 problem sets.'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        inv = Intervention.query.filter_by(student_id='STU_TEST001').first()
        assert inv is not None
        assert inv.status == 'Open'
        assert inv.priority == 'High'
