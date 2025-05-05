import pytest
import sqlite3
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from jose import jwt
from finance_tracker.main import app, get_db_connection, SECRET_KEY, \
    ALGORITHM, get_password_hash
from finance_tracker.database import setup_database


@pytest.fixture(scope="function")
def client():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    setup_database(conn=conn)
    app.dependency_overrides[get_db_connection] = lambda: conn
    yield TestClient(app)
    conn.close()


@pytest.fixture
def test_user(client):
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_user = cursor.execute(
        "SELECT * FROM users WHERE username = ?", ("testuser",)
    ).fetchone()

    if not existing_user:
        hashed_password = get_password_hash("password123")
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            ("testuser", hashed_password, "test@example.com")
        )
        conn.commit()

    user = cursor.execute(
        "SELECT * FROM users WHERE username = ?", ("testuser",)
    ).fetchone()
    conn.commit()
    return dict(user)


@pytest.mark.asyncio
async def test_register_user(client):
    response = client.post(
        "/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"
    assert response.json()["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_login(client, test_user):
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_create_transaction(client, test_user):
    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM categories WHERE name = ? AND type = ? "
        "AND is_predefined = 1",
        ("Food", "expense")
    )
    category = cursor.fetchone()
    category_id = category["id"]
    conn.commit()

    response = client.post(
        "/transactions/",
        json={
            "amount": 100.0,
            "description": "Test transaction",
            "date": datetime.now(timezone.utc).isoformat(),
            "type": "expense",
            "category_id": category_id,
            "is_recurring": False
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 100.0
    assert response.json()["type"] == "expense"


@pytest.mark.asyncio
async def test_get_transactions(client, test_user):
    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.get(
        "/transactions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_category(client, test_user):
    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.post(
        "/categories/",
        json={"name": "Travel", "type": "expense", "is_predefined": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Travel"


@pytest.mark.asyncio
async def test_get_categories(client, test_user):
    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.get(
        "/categories/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_budget(client, test_user):
    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.post(
        "/budgets/",
        json={
            "target_amount": 1000.0,
            "start_date": datetime.now(timezone.utc).isoformat(),
            "end_date": (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).isoformat(),
            "name": "Test Budget"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Budget"
    assert response.json()["target_amount"] == 1000.0


@pytest.mark.asyncio
async def test_get_budgets(client, test_user):
    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.get(
        "/budgets/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_summary(client, test_user):
    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.get(
        "/analytics/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "total_income" in response.json()
    assert "total_expenses" in response.json()


@pytest.mark.asyncio
async def test_update_transaction(client, test_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM categories WHERE name = ? AND type = ? "
        "AND is_predefined = 1",
        ("Food", "expense")
    )
    category = cursor.fetchone()
    category_id = category["id"]

    cursor.execute(
        "INSERT INTO transactions (user_id, category_id, amount, date, type, "
        "is_recurring) VALUES (?, ?, ?, ?, ?, ?)",
        (test_user["id"], category_id, 100.0, datetime.now(timezone.utc),
         "expense", False)
    )
    transaction_id = cursor.lastrowid
    conn.commit()

    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.patch(
        f"/transactions/{transaction_id}",
        json={"amount": 150.0, "description": "Updated"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 150.0
    assert response.json()["description"] == "Updated"


@pytest.mark.asyncio
async def test_delete_transaction(client, test_user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM categories WHERE name = ? AND type = ? "
        "AND is_predefined = 1",
        ("Food", "expense")
    )
    category = cursor.fetchone()
    category_id = category["id"]

    cursor.execute(
        "INSERT INTO transactions "
        "(user_id, category_id, amount, date, type, is_recurring) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (test_user["id"], category_id, 100.0, datetime.now(timezone.utc),
         "expense", False)
    )
    transaction_id = cursor.lastrowid
    conn.commit()

    token = jwt.encode(
        {"sub": "testuser",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    response = client.delete(
        f"/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
