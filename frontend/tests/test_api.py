import pytest
import requests
import requests_mock
from unittest.mock import patch, MagicMock
import pandas as pd
from personal_finance_tracker_front.api import (
    login,
    register_user,
    get_headers,
    get_categories,
    create_category,
    get_summary,
    get_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
    refresh_data,
)


@pytest.fixture
def mock_streamlit_session():
    with patch("personal_finance_tracker_front.api.st.session_state",
              MagicMock(token="mock_token")):
        yield


@pytest.fixture
def mock_requests():
    with requests_mock.Mocker() as m:
        yield m


def test_login_success(mock_requests):
    mock_requests.post(
        "http://localhost:8000/token",
        json={"access_token": "test_token", "token_type": "bearer"},
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        token = login("testuser", "password123")
    assert token == "test_token"


def test_login_failure(mock_requests):
    mock_requests.post(
        "http://localhost:8000/token",
        json={"detail": "Incorrect username or password"},
        status_code=401,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        with pytest.raises(requests.HTTPError):
            login("wronguser", "wrongpass")


def test_register_user_success(mock_requests):
    mock_requests.post(
        "http://localhost:8000/register",
        json={"id": 1, "username": "newuser", "email": "new@example.com"},
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        register_user("newuser", "new@example.com", "password123")
    assert mock_requests.called


def test_register_user_failure(mock_requests):
    mock_requests.post(
        "http://localhost:8000/register",
        json={"detail": "Username or email already exists"},
        status_code=400,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        with pytest.raises(requests.HTTPError):
            register_user("existinguser", "existing@example.com", "password123")


def test_get_headers(mock_streamlit_session):
    headers = get_headers()
    assert headers == {"Authorization": "Bearer mock_token"}


def test_get_categories_success(mock_requests, mock_streamlit_session):
    mock_requests.get(
        "http://localhost:8000/categories/",
        json=[
            {
                "id": 1,
                "name": "Food",
                "type": "expense",
                "is_predefined": True,
                "user_id": None,
            },
            {
                "id": 2,
                "name": "Salary",
                "type": "income",
                "is_predefined": True,
                "user_id": None,
            },
        ],
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        categories = get_categories()
    assert len(categories) == 2
    assert categories[0]["name"] == "Food"
    assert categories[1]["name"] == "Salary"


def test_create_category_success(mock_requests, mock_streamlit_session):
    mock_requests.post(
        "http://localhost:8000/categories/",
        json={
            "id": 3,
            "name": "Travel",
            "type": "expense",
            "is_predefined": False,
            "user_id": 1,
        },
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        category = create_category("Travel", "expense", False)
    assert category["name"] == "Travel"
    assert category["type"] == "expense"


def test_get_summary_success(mock_requests, mock_streamlit_session):
    mock_requests.get(
        "http://localhost:8000/analytics/summary",
        json={
            "total_income": 1000.0,
            "total_expenses": 800.0,
            "net_balance": 200.0,
            "expenses_by_category": [{"name": "Food", "total": 500.0}],
        },
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        summary = get_summary("2025-01-01", "2025-01-31", [1, 2])
    assert summary["net_balance"] == 200.0
    assert len(summary["expenses_by_category"]) == 1


def test_get_transactions_success(mock_requests, mock_streamlit_session):
    mock_requests.get(
        "http://localhost:8000/transactions/",
        json=[
            {
                "id": 1,
                "user_id": 1,
                "category_id": 1,
                "amount": 100.0,
                "date": "2025-01-01",
                "type": "expense",
                "is_recurring": False,
            },
        ],
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        transactions = get_transactions("2025-01-01", "2025-01-31", [1])
    assert len(transactions) == 1
    assert transactions[0]["amount"] == 100.0


def test_create_transaction_success(mock_requests, mock_streamlit_session):
    mock_requests.post(
        "http://localhost:8000/transactions/",
        json={
            "id": 2,
            "user_id": 1,
            "category_id": 1,
            "amount": 50.0,
            "date": "2025-01-02",
            "type": "income",
            "is_recurring": False,
        },
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        txn = {
            "type": "income",
            "amount": 50.0,
            "date": "2025-01-02",
            "category_id": 1,
            "is_recurring": False,
        }
        result = create_transaction(txn)
    assert result["id"] == 2
    assert result["type"] == "income"


def test_update_transaction_success(mock_requests, mock_streamlit_session):
    mock_requests.patch(
        "http://localhost:8000/transactions/1",
        json={
            "id": 1,
            "user_id": 1,
            "category_id": 2,
            "amount": 75.0,
            "date": "2025-01-01",
            "type": "expense",
            "is_recurring": False,
        },
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        update = {
            "amount": 75.0,
            "category_id": 2,
            "is_recurring": False,
        }
        result = update_transaction(1, update)
    assert result["amount"] == 75.0
    assert result["category_id"] == 2


def test_delete_transaction_success(mock_requests, mock_streamlit_session):
    mock_requests.delete("http://localhost:8000/transactions/1", status_code=204)
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        delete_transaction(1)
    assert mock_requests.called


def test_refresh_data_success(mock_requests, mock_streamlit_session):
    mock_requests.get(
        "http://localhost:8000/categories/",
        json=[
            {
                "id": 1,
                "name": "Food",
                "type": "expense",
                "is_predefined": True,
                "user_id": None,
            },
            {
                "id": 2,
                "name": "Salary",
                "type": "income",
                "is_predefined": True,
                "user_id": None,
            },
        ],
        status_code=200,
    )
    mock_requests.get(
        "http://localhost:8000/analytics/summary",
        json={
            "total_income": 1000.0,
            "total_expenses": 800.0,
            "net_balance": 200.0,
        },
        status_code=200,
    )
    mock_requests.get(
        "http://localhost:8000/transactions/",
        json=[
            {
                "id": 1,
                "user_id": 1,
                "category_id": 1,
                "amount": 100.0,
                "date": "2025-01-01",
                "type": "expense",
                "is_recurring": False,
            },
        ],
        status_code=200,
    )
    with patch("personal_finance_tracker_front.api.st.secrets",
              {"api_url": "http://localhost:8000"}):
        result = refresh_data("2025-01-01", "2025-01-31", ["Food"])
    assert result["category_map"] == {"Food": 1, "Salary": 2}
    assert result["id_to_category"] == {1: "Food", 2: "Salary"}
    assert result["categories"] == ["Food", "Salary"]
    assert result["categories_by_type"] == {"income": ["Salary"],
                                           "expense": ["Food"]}
    assert result["summary"]["net_balance"] == 200.0
    assert not result["df"].empty
    assert result["df"]["Category"].iloc[0] == "Food"
