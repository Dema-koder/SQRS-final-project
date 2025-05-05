import sqlite3
from datetime import datetime


def adapt_datetime(dt):
    return dt.isoformat()


sqlite3.register_adapter(datetime, adapt_datetime)


DATABASE_NAME = "finance.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database(conn=None):
    if conn is None:
        conn = sqlite3.connect(DATABASE_NAME)
        close_conn = True
    else:
        close_conn = False

    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("DROP TABLE IF EXISTS audit_log")
        cursor.execute("DROP TABLE IF EXISTS budgets")
        cursor.execute("DROP TABLE IF EXISTS transactions")
        cursor.execute("DROP TABLE IF EXISTS categories")
        cursor.execute("DROP TABLE IF EXISTS users")

        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                is_locked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                is_predefined BOOLEAN DEFAULT FALSE,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(name, user_id)
            )
        """)

        # Create transactions table
        cursor.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date TIMESTAMP NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Create budgets table
        cursor.execute("""
            CREATE TABLE budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0.0,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                name TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Create audit_log table
        cursor.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_transactions_user_date "
                       "ON transactions(user_id, date)")
        cursor.execute("CREATE INDEX idx_transactions_category_type "
                       "ON transactions(category_id, type)")
        cursor.execute("CREATE INDEX idx_budgets_user_active "
                       "ON budgets(user_id, is_active)")

        # Insert predefined categories
        predefined_categories = [
            ("Salary", "income", True),
            ("Freelance", "income", True),
            ("Investments", "income", True),
            ("Other Income", "income", True),
            ("Food", "expense", True),
            ("Housing", "expense", True),
            ("Transportation", "expense", True),
            ("Entertainment", "expense", True),
            ("Healthcare", "expense", True),
            ("Other Expenses", "expense", True),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, type, is_predefined) "
            "VALUES (?, ?, ?)",
            predefined_categories
        )

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if close_conn:
            conn.close()
