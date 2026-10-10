from tests.conftest import login_client

def test_student_cannot_access_settings(client):
    login_client(client, 'test_student', 'Student@123')
    response = client.get('/admin/settings', follow_redirects=False)
    # Redirects to access_denied or 403
    assert response.status_code in [302, 403]

def test_student_cannot_delete_student(client):
    login_client(client, 'test_student', 'Student@123')
    response = client.post('/students/STU_TEST001/delete', follow_redirects=False)
    assert response.status_code in [302, 403]
