from tests.conftest import register_student, register_admin, login_user


def test_register_student_success(client):
    response = register_student(client)

    assert response.status_code == 201
    assert response.json()["message"] == "Student registered successfully"


def test_register_admin_success(client):
    response = register_admin(client)

    assert response.status_code == 201
    assert response.json()["message"] == "Admin registered successfully"


def test_register_admin_wrong_secret_fails(client):
    response = client.post(
        "/auth/register-admin",
        json={
            "username": "badadmin",
            "email": "badadmin@test.com",
            "password": "123456",
            "admin_secret": "wrong-secret"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin secret"


def test_duplicate_student_register_fails(client):
    register_student(client)

    response = register_student(client)

    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already exists"


def test_login_student_success(client):
    register_student(client)

    response = login_user(client)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password_fails(client):
    register_student(client)

    response = login_user(client, username="student1", password="wrongpassword")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_protected_route_without_token_fails(client):
    response = client.get("/exams/")

    assert response.status_code == 401