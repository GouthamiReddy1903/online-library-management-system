import os
import tempfile
import pytest
from app import app, init_db

@pytest.fixture()
def client(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    monkeypatch.setattr("app.DB_PATH", path)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    init_db()
    with app.test_client() as client:
        yield client
    os.unlink(path)

def login(client, email="admin@library.com", password="admin123"):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)

def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Online Library" in response.data

def test_admin_can_add_book(client):
    login(client)
    response = client.post("/admin/books/add",
        data={"title": "Python Basics", "author": "A. Student", "isbn": "TEST-001", "copies": "3"},
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Python Basics" in response.data

def test_student_registration_and_login(client):
    client.post("/register", data={"name":"Test Student","email":"student@example.com","password":"secret1"})
    response = client.post("/login", data={"email":"student@example.com","password":"secret1"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Student" in response.data

def test_admin_page_requires_login(client):
    response = client.get("/admin/books/add")
    assert response.status_code == 302
