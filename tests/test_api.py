def test_api_dashboard_summary(client):
    response = client.get('/api/v1/dashboard/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_students' in data
    assert 'avg_success_score' in data

def test_api_students_get(client):
    response = client.get('/api/v1/students')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_api_campus_ask(client):
    response = client.post('/api/v1/campus/ask', json={'question': 'What is the attendance policy?'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'answer' in data
    assert 'Attendance' in data['answer'] or 'attendance' in data['answer'].lower()

def test_api_campus_ask_chatgpt_style_coding(client):
    response = client.post('/api/v1/campus/ask', json={'question': 'Explain binary search in Python with code'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'def binary_search' in data['answer'] or 'Binary Search' in data['answer']

def test_placement_code_execution(client):
    from tests.conftest import login_client
    login_client(client, 'test_student', 'Student@123')
    response = client.post('/placement/execute-code', json={
        'code': 'print("Hello Smart Campus")',
        'language': 'python',
        'student_id': 'STU_TEST001'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'Hello Smart Campus' in data['stdout']
