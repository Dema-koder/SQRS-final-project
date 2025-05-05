import pytest
import sqlite3
from finance_tracker.database import setup_database, get_db_connection


@pytest.fixture
def in_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_setup_database(in_memory_db):
    original_connect = sqlite3.connect
    sqlite3.connect = lambda *args, **kwargs: in_memory_db
    try:
        cursor = in_memory_db.cursor()
        setup_database(conn=in_memory_db)

        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        expected_tables = ["users", "categories", "transactions", "budgets",
                           "audit_log"]
        for table in expected_tables:
            assert table in table_names

        categories = cursor.execute(
            "SELECT name, type, is_predefined FROM categories "
            "WHERE is_predefined = 1"
        ).fetchall()
        assert len(categories) >= 8
        for cat in categories:
            assert cat["is_predefined"] == 1
            assert cat["type"] in ["income", "expense"]

        indexes = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        index_names = [i["name"] for i in indexes]
        assert "idx_transactions_user_date" in index_names
        assert "idx_transactions_category_type" in index_names
        assert "idx_budgets_user_active" in index_names
    finally:
        sqlite3.connect = original_connect


def test_get_db_connection():
    conn = get_db_connection()
    assert isinstance(conn, sqlite3.Connection)
    assert conn.row_factory == sqlite3.Row
    conn.close()
