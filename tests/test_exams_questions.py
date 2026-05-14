from tests.conftest import get_admin_headers, get_student_headers, create_exam, create_question


def test_student_cannot_create_exam(client):
    student_headers = get_student_headers(client)

    response = client.post(
        "/exams/",
        json={
            "title": "Python Exam",
            "duration_minutes": 30
        },
        headers=student_headers
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin only"


def test_admin_can_create_exam(client):
    admin_headers = get_admin_headers(client)

    response = create_exam(client, admin_headers)

    assert response.status_code == 201
    assert response.json()["title"] == "Python Exam"
    assert response.json()["duration_minutes"] == 30


def test_get_all_exams_with_token(client):
    admin_headers = get_admin_headers(client)
    create_exam(client, admin_headers)

    response = client.get("/exams/", headers=admin_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


def test_get_exam_by_id(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    response = client.get(f"/exams/{exam_id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["id"] == exam_id


def test_admin_can_update_exam(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    response = client.put(
        f"/exams/{exam_id}",
        json={
            "title": "Updated Exam",
            "duration_minutes": 45
        },
        headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Exam"
    assert response.json()["duration_minutes"] == 45


def test_admin_can_delete_exam(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    response = client.delete(f"/exams/{exam_id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Exam deleted successfully"


def test_admin_can_create_question(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    response = create_question(client, admin_headers, exam_id)

    assert response.status_code == 201
    assert response.json()["exam_id"] == exam_id
    assert response.json()["correct_option"] == "a"


def test_student_can_get_exam_questions_without_correct_answer(client):
    admin_headers = get_admin_headers(client)
    student_headers = get_student_headers(
        client,
        username="student2",
        email="student2@test.com"
    )

    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]
    create_question(client, admin_headers, exam_id)

    response = client.get(f"/questions/exam/{exam_id}", headers=student_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "correct_option" not in response.json()[0]


def test_admin_can_get_all_questions(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]
    create_question(client, admin_headers, exam_id)

    response = client.get("/questions/", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "correct_option" in response.json()[0]


def test_admin_can_update_question(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]
    question_response = create_question(client, admin_headers, exam_id)
    question_id = question_response.json()["id"]

    response = client.put(
        f"/questions/{question_id}",
        json={
            "text": "Updated question?",
            "option_a": "A1",
            "option_b": "B1",
            "option_c": "C1",
            "option_d": "D1",
            "correct_option": "b"
        },
        headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Updated question?"
    assert response.json()["correct_option"] == "b"


def test_admin_can_delete_question(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]
    question_response = create_question(client, admin_headers, exam_id)
    question_id = question_response.json()["id"]

    response = client.delete(f"/questions/{question_id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Question deleted successfully"


def test_cache_header_exists_for_questions(client):
    admin_headers = get_admin_headers(client)
    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]
    create_question(client, admin_headers, exam_id)

    response = client.get(f"/questions/exam/{exam_id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.headers.get("X-Cache") in ["HIT", "MISS", None]