from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import Query
import sqlite3
import bcrypt
import secrets
from jose import JWTError, jwt
from finance_tracker.models import *
from finance_tracker.models import TransactionUpdate

app = FastAPI()

from finance_tracker.database import setup_database, get_db_connection

# Initialize database
setup_database()

# Security config
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (token_data.username,)).fetchone()
    conn.close()

    if user is None:
        raise credentials_exception
    return user

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (form_data.username,)).fetchone()
    conn.close()

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=User)
async def register_user(user: UserCreate):
    conn = get_db_connection()
    try:
        hashed_password = get_password_hash(user.password)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (user.username, hashed_password, user.email)
        )
        user_id = cursor.lastrowid
        conn.commit()

        new_user = conn.execute(
            "SELECT id, username, email, is_locked, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        user_dict = dict(new_user)
        return user_dict
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    finally:
        conn.close()

@app.post("/transactions/", response_model=Transaction)
async def create_transaction(
        transaction: TransactionCreate,
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)]
):
    if transaction.type.lower() not in ['income', 'expense']:
        raise HTTPException(
            status_code=400,
            detail="Transaction type must be either 'income' or 'expense'"
        )

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO transactions 
            (user_id, category_id, amount, description, date, type, is_recurring, recurrence_pattern)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                current_user["id"],
                transaction.category_id,
                transaction.amount,
                transaction.description,
                transaction.date,
                transaction.type.lower(),
                transaction.is_recurring,
                transaction.recurrence_pattern
            )
        )
        transaction_id = cursor.lastrowid
        conn.commit()

        new_transaction = conn.execute(
            """SELECT id, user_id, category_id, amount, description, date, type, 
                  is_recurring, recurrence_pattern, created_at 
               FROM transactions WHERE id = ?""",
            (transaction_id,)
        ).fetchone()

        if not new_transaction:
            raise HTTPException(status_code=400, detail="Transaction not found after creation")

        return dict(new_transaction)

    except sqlite3.IntegrityError as e:
        if "FOREIGN KEY constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Invalid category_id")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/transactions/", response_model=list[Transaction])
async def get_transactions(
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category_id: str = Query(None, description="Comma-separated category IDs"),
        type_: Optional[str] = None
):
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            id, user_id, category_id, amount, description, 
            date, type, is_recurring, recurrence_pattern, created_at
        FROM transactions 
        WHERE user_id = ?
        """
        params = [current_user["id"]]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())

        if category_id:
            try:
                category_ids = [int(id.strip()) for id in category_id.split(",")]
                placeholders = ','.join(['?'] * len(category_ids))
                query += f" AND category_id IN ({placeholders})"
                params.extend(category_ids)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="category_id must be comma-separated integers"
                )

        if type_:
            query += " AND type = ?"
            params.append(type_.lower())

        query += " ORDER BY date DESC"

        transactions = conn.execute(query, params).fetchall()
        return [dict(txn) for txn in transactions]
    finally:
        conn.close()

@app.post("/categories/", response_model=Category)
async def create_category(
        category: CategoryCreate,
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)]
):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, is_predefined, type, user_id) VALUES (?, ?, ?, ?)",
            (category.name, category.is_predefined, category.type, current_user["id"])
        )
        category_id = cursor.lastrowid
        conn.commit()

        new_category = conn.execute(
            "SELECT id, name, type, is_predefined, user_id FROM categories WHERE id = ?",
            (category_id,)
        ).fetchone()

        if not new_category:
            raise HTTPException(status_code=400, detail="Category not found after creation")

        category_dict = dict(new_category)
        return category_dict
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Category already exists")
    finally:
        conn.close()

@app.get("/categories/", response_model=list[Category])
async def get_categories(
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
        type_: Optional[str] = None
):
    conn = get_db_connection()
    try:
        query = """
        SELECT id, name, type, is_predefined, user_id FROM categories 
        WHERE user_id = ? OR is_predefined = 1
        """
        params = [current_user["id"]]

        if type_:
            query += " AND type = ?"
            params.append(type_)

        categories = conn.execute(query, params).fetchall()
        return [dict(category) for category in categories]
    finally:
        conn.close()

# Budget endpoints
@app.post("/budgets/", response_model=Budget)
async def create_budget(
        budget: BudgetCreate,
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)]
):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO budgets 
            (user_id, category_id, target_amount, start_date, end_date, name)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                current_user["id"],
                budget.category_id,
                budget.target_amount,
                budget.start_date,
                budget.end_date,
                budget.name
            )
        )
        budget_id = cursor.lastrowid
        conn.commit()

        new_budget = conn.execute(
            "SELECT * FROM budgets WHERE id = ?", (budget_id,)
        ).fetchone()
        if not new_budget:
            raise HTTPException(status_code=400, detail="Budget not found after creation")
        return dict(new_budget)
    finally:
        conn.close()

@app.get("/budgets/", response_model=list[Budget])
async def get_budgets(
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
        active_only: bool = True
):
    conn = get_db_connection()
    try:
        query = "SELECT * FROM budgets WHERE user_id = ?"
        params = [current_user["id"]]

        if active_only:
            query += " AND is_active = 1 AND date() BETWEEN start_date AND end_date"

        budgets = conn.execute(query, params).fetchall()
        return [dict(budget) for budget in budgets]
    finally:
        conn.close()

# Analytics endpoints
@app.get("/analytics/summary")
async def get_summary(
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
):
    conn = get_db_connection()
    try:
        # Default to current month if no dates provided
        if not start_date or not end_date:
            today = datetime.now()
            start_date = today.replace(day=1)
            end_date = today.replace(day=1, month=today.month+1) - timedelta(days=1)

        # Get total income and expenses
        summary = conn.execute("""
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses
            FROM transactions
            WHERE user_id = ? AND date BETWEEN ? AND ?
        """, (current_user["id"], start_date, end_date)).fetchone()

        # Get expenses by category
        categories = conn.execute("""
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ? AND t.type = 'expense' AND t.date BETWEEN ? AND ?
            GROUP BY c.name
            ORDER BY total DESC
        """, (current_user["id"], start_date, end_date)).fetchall()

        return {
            "period": {"start": start_date, "end": end_date},
            "total_income": summary["total_income"] or 0,
            "total_expenses": summary["total_expenses"] or 0,
            "net_balance": (summary["total_income"] or 0) - (summary["total_expenses"] or 0),
            "expenses_by_category": [dict(row) for row in categories]
        }
    finally:
        conn.close()

@app.patch("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
        transaction_id: int,
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
        transaction_update: TransactionUpdate
):
    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, current_user["id"])
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Transaction not found")

        update_fields = {}
        if transaction_update.amount is not None:
            update_fields["amount"] = transaction_update.amount
        if transaction_update.description is not None:
            update_fields["description"] = transaction_update.description
        if transaction_update.date is not None:
            update_fields["date"] = transaction_update.date
        if transaction_update.category_id is not None:
            update_fields["category_id"] = transaction_update.category_id
        if transaction_update.type is not None:
            update_fields["type"] = transaction_update.type
        if transaction_update.is_recurring is not None:
            update_fields["is_recurring"] = transaction_update.is_recurring
        if transaction_update.recurrence_pattern is not None:
            update_fields["recurrence_pattern"] = transaction_update.recurrence_pattern

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        if "category_id" in update_fields:
            category = conn.execute(
                "SELECT 1 FROM categories WHERE id = ? AND (user_id = ? OR is_predefined = 1)",
                (update_fields["category_id"], current_user["id"])
            ).fetchone()
            if not category:
                raise HTTPException(status_code=400, detail="Invalid category_id")

        set_clause = ", ".join(f"{field} = ?" for field in update_fields.keys())
        values = list(update_fields.values())
        values.extend([transaction_id, current_user["id"]])

        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE transactions SET {set_clause} WHERE id = ? AND user_id = ?", # nosec
            values
        )
        conn.commit()

        updated_transaction = conn.execute(
            """SELECT id, user_id, category_id, amount, description, 
                  date, type, is_recurring, recurrence_pattern, created_at 
               FROM transactions WHERE id = ?""",
            (transaction_id,)
        ).fetchone()

        return dict(updated_transaction)

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
        transaction_id: int,
        current_user: Annotated[sqlite3.Row, Depends(get_current_user)]
):
    conn = get_db_connection()
    try:
        transaction = conn.execute(
            "SELECT id FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, current_user["id"])
        ).fetchone()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or access denied"
            )

        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        conn.close()
