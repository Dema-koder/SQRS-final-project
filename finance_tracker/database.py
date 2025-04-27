import sqlite3
from typing import Optional

DATABASE_NAME = "finance_tracker.db"

def setup_database():
    """Initialize the database with all required tables"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Drop all tables in correct order to avoid foreign key violations
        cursor.execute("DROP TABLE IF EXISTS audit_log")
        cursor.execute("DROP TABLE IF EXISTS budgets")
        cursor.execute("DROP TABLE IF EXISTS transactions")
        cursor.execute("DROP TABLE IF EXISTS categories")
        cursor.execute("DROP TABLE IF EXISTS users")

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            is_locked BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Categories table with improved constraints
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_predefined BOOLEAN NOT NULL DEFAULT 0,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (name, user_id)  -- Changed from COALESCE(user_id, -1)
        )
        """)

        # Transactions table with proper foreign key handling
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
            description TEXT,
            date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            is_recurring BOOLEAN NOT NULL DEFAULT 0,
            recurrence_pattern TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
        """)

        # Budgets table with improved constraints
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            target_amount DECIMAL(10, 2) NOT NULL CHECK (target_amount > 0),
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            current_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
            name TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
            CHECK (end_date > start_date)
        )
        """)

        # Audit log table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
        """)

        # Create indexes for better performance
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
        ON transactions(user_id, date)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_category_type 
        ON transactions(category_id, type)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_budgets_user_active 
        ON budgets(user_id, is_active)
        """)

        # Insert predefined categories safely
        predefined_categories = [
            ('Salary', 'income'),
            ('Bonus', 'income'),
            ('Investment', 'income'),
            ('Food', 'expense'),
            ('Transport', 'expense'),
            ('Housing', 'expense'),
            ('Entertainment', 'expense'),
            ('Healthcare', 'expense')
        ]

        for name, type_ in predefined_categories:
            cursor.execute("""
            INSERT OR IGNORE INTO categories (name, is_predefined, type, user_id)
            SELECT ?, 1, ?, NULL
            WHERE NOT EXISTS (
                SELECT 1 FROM categories 
                WHERE name = ? AND type = ? AND is_predefined = 1 AND user_id IS NULL
            )
            """, (name, type_, name, type_))

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn