from tests.conftest import get_admin_headers, get_student_headers, create_exam, create_question


def test_student_can_start_exam(client):
    admin_headers = get_admin_headers(client)
    student_headers = get_student_headers(client)

    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    response = client.post(
        f"/answers/start?exam_id={exam_id}",
        headers=student_headers
    )

    assert response.status_code == 200
    assert response.json()["exam_id"] == exam_id
    assert response.json()["is_submitted"] is False


def test_student_cannot_start_missing_exam(client):
    student_headers = get_student_headers(client)

    response = client.post(
        "/answers/start?exam_id=999",
        headers=student_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Exam not found"


def test_admin_cannot_start_exam(client):
    admin_headers = get_admin_headers(client)

    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    response = client.post(
        f"/answers/start?exam_id={exam_id}",
        headers=admin_headers
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Students only"


def test_student_can_submit_answer_without_showing_correct(client):
    admin_headers = get_admin_headers(client)
    student_headers = get_student_headers(client)

    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    question_response = create_question(client, admin_headers, exam_id)
    question_id = question_response.json()["id"]

    client.post(f"/answers/start?exam_id={exam_id}", headers=student_headers)

    response = client.post(
        "/answers/",
        json={
            "exam_id": exam_id,
            "question_id": question_id,
            "selected_option": "a"
        },
        headers=student_headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Answer submitted"
    assert "correct" not in response.json()


def test_student_cannot_submit_before_starting_exam(client):
    admin_headers = get_admin_headers(client)
    student_headers = get_student_headers(client)

    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    question_response = create_question(client, admin_headers, exam_id)
    question_id = question_response.json()["id"]

    response = client.post(
        "/answers/",
        json={
            "exam_id": exam_id,
            "question_id": question_id,
            "selected_option": "a"
        },
        headers=student_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Start the exam first"


def test_student_can_finish_exam_and_get_result(client):
    admin_headers = get_admin_headers(client)
    student_headers = get_student_headers(client)

    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    question_response = create_question(client, admin_headers, exam_id)
    question_id = question_response.json()["id"]

    client.post(f"/answers/start?exam_id={exam_id}", headers=student_headers)

    client.post(
        "/answers/",
        json={
            "exam_id": exam_id,
            "question_id": question_id,
            "selected_option": "a"
        },
        headers=student_headers
    )

    finish_response = client.post(
        f"/answers/finish/{exam_id}",
        headers=student_headers
    )

    assert finish_response.status_code == 200
    assert finish_response.json()["message"] == "Exam finished"

    result_response = client.get("/results/my", headers=student_headers)

    assert result_response.status_code == 200
    assert len(result_response.json()) == 1
    assert result_response.json()[0]["score"] == 1
    assert result_response.json()[0]["total_questions"] == 1
    assert result_response.json()[0]["percentage"] == 100


def test_student_cannot_submit_after_finish(client):
    admin_headers = get_admin_headers(client)
    student_headers = get_student_headers(client)

    exam_response = create_exam(client, admin_headers)
    exam_id = exam_response.json()["id"]

    question_response = create_question(client, admin_headers, exam_id)
    question_id = question_response.json()["id"]

    client.post(f"/answers/start?exam_id={exam_id}", headers=student_headers)
    client.post(f"/answers/finish/{exam_id}", headers=student_headers)

    response = client.post(
        "/answers/",
        json={
            "exam_id": exam_id,
            "question_id": question_id,
            "selected_option": "a"
        },
        headers=student_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Start the exam first"