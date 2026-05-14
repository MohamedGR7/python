from tests.conftest import get_admin_headers, get_student_headers, create_exam, create_question


def create_finished_exam_result(client):
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

    client.post(f"/answers/finish/{exam_id}", headers=student_headers)

    return admin_headers, student_headers


def test_student_can_view_own_results(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    response = client.get("/results/my", headers=student_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_admin_can_view_all_results(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    response = client.get("/results/all", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_student_cannot_view_all_results(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    response = client.get("/results/all", headers=student_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin only"


def test_admin_can_view_analytics(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    response = client.get("/results/analytics", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["total_results"] == 1
    assert response.json()["average_percentage"] == 100


def test_admin_can_delete_result(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    all_results_response = client.get("/results/all", headers=admin_headers)
    result_id = all_results_response.json()[0]["id"]

    delete_response = client.delete(
        f"/results/{result_id}",
        headers=admin_headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Result deleted successfully"

    all_results_after_delete = client.get("/results/all", headers=admin_headers)

    assert all_results_after_delete.status_code == 200
    assert len(all_results_after_delete.json()) == 0


def test_student_cannot_delete_result(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    all_results_response = client.get("/results/all", headers=admin_headers)
    result_id = all_results_response.json()[0]["id"]

    delete_response = client.delete(
        f"/results/{result_id}",
        headers=student_headers
    )

    assert delete_response.status_code == 403
    assert delete_response.json()["detail"] == "Admin only"


def test_dashboard_stats_admin_only(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    response = client.get("/dashboard/stats", headers=admin_headers)

    assert response.status_code == 200
    assert "api_request_count" in response.json()
    assert "average_response_time" in response.json()
    assert "error_count" in response.json()
    assert "database_health" in response.json()
    assert "redis_health" in response.json()
    assert "endpoint_stats" in response.json()
    assert "recent_auth_failures" in response.json()


def test_student_cannot_view_dashboard(client):
    admin_headers, student_headers = create_finished_exam_result(client)

    response = client.get("/dashboard/stats", headers=student_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin only"