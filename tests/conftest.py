import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_exam.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_SECRET"] = "test-admin-secret"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6390"

from app.main import app
from app.database import Base, engine, SessionLocal, get_db


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def register_student(client, username="student1", email="student1@test.com", password="123456"):
    return client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )


def register_admin(client, username="admin1", email="admin1@test.com", password="123456"):
    return client.post(
        "/auth/register-admin",
        json={
            "username": username,
            "email": email,
            "password": password,
            "admin_secret": "test-admin-secret"
        }
    )


def login_user(client, username="student1", password="123456"):
    return client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password
        }
    )


def get_student_headers(client, username="student1", email="student1@test.com", password="123456"):
    register_student(client, username, email, password)
    response = login_user(client, username, password)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def get_admin_headers(client, username="admin1", email="admin1@test.com", password="123456"):
    register_admin(client, username, email, password)
    response = login_user(client, username, password)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_exam(client, admin_headers, title="Python Exam", duration_minutes=30):
    return client.post(
        "/exams/",
        json={
            "title": title,
            "duration_minutes": duration_minutes
        },
        headers=admin_headers
    )


def create_question(client, admin_headers, exam_id, correct_option="a"):
    return client.post(
        "/questions/",
        json={
            "exam_id": exam_id,
            "text": "What is FastAPI?",
            "option_a": "A Python web framework",
            "option_b": "A database",
            "option_c": "An operating system",
            "option_d": "A frontend library",
            "correct_option": correct_option
        },
        headers=admin_headers
    )