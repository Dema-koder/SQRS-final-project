import pytest
from datetime import datetime
from pydantic import ValidationError
from finance_tracker.models import (
    UserBase, UserCreate, User,
    CategoryBase, CategoryCreate, Category,
    TransactionBase, TransactionCreate, Transaction,
    BudgetBase, BudgetCreate, Budget,
    Token, TokenData, TransactionUpdate
)


def test_user_base():
    user = UserBase(username="testuser", email="test@example.com")
    assert user.username == "testuser"
    assert user.email == "test@example.com"

    with pytest.raises(ValidationError):
        UserBase(username="testuser")


def test_user_create():
    user = UserCreate(username="testuser", email="test@example.com",
                      password="password123")
    assert user.password == "password123"


def test_user():
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        is_locked=False,
        created_at=datetime.now()
    )
    assert user.id == 1
    assert user.is_locked is False
    assert user.model_config["from_attributes"] is True


def test_category_base():
    category = CategoryBase(name="Food", type="expense")
    assert category.name == "Food"
    assert category.type == "expense"

    with pytest.raises(ValidationError):
        CategoryBase(name="Food", type="invalid")


def test_category_create():
    category = CategoryCreate(
        name="Transport",
        type="income",
        is_predefined=True
    )
    assert category.is_predefined is True


def test_category():
    category = Category(
        id=1,
        name="Housing",
        type="expense",
        is_predefined=False,
        user_id=1
    )
    assert category.id == 1
    assert category.user_id == 1


def test_transaction_base():
    transaction = TransactionBase(
        amount=100.0,
        description="Test",
        date=datetime.now(),
        type="income",
        is_recurring=False
    )
    assert transaction.type == "income"

    with pytest.raises(ValidationError):
        TransactionBase(
            amount=100.0,
            date=datetime.now(),
            type="invalid"
        )


def test_transaction_create():
    transaction = TransactionCreate(
        amount=50.0,
        date=datetime.now(),
        type="expense",
        category_id=1
    )
    assert transaction.category_id == 1


def test_transaction():
    transaction = Transaction(
        id=1,
        user_id=1,
        category_id=1,
        amount=200.0,
        date=datetime.now(),
        type="income",
        created_at=datetime.now()
    )
    assert transaction.id == 1
    assert transaction.model_config["from_attributes"] is True


def test_budget_base():
    budget = BudgetBase(
        target_amount=1000.0,
        start_date=datetime.now(),
        end_date=datetime.now()
    )
    assert budget.target_amount == 1000.0


def test_budget_create():
    budget = BudgetCreate(
        target_amount=500.0,
        start_date=datetime.now(),
        end_date=datetime.now(),
        category_id=1
    )
    assert budget.category_id == 1


def test_budget():
    budget = Budget(
        id=1,
        user_id=1,
        target_amount=1000.0,
        start_date=datetime.now(),
        end_date=datetime.now(),
        current_amount=0.0,
        is_active=True,
        category_id=None
    )
    assert budget.is_active is True


def test_token():
    token = Token(access_token="abc123", token_type="bearer")
    assert token.access_token == "abc123"


def test_token_data():
    token_data = TokenData(username="testuser")
    assert token_data.username == "testuser"


def test_transaction_update():
    update = TransactionUpdate(
        amount=150.0,
        type="expense",
        category_id=2
    )
    assert update.amount == 150.0
    assert update.type == "expense"

    with pytest.raises(ValidationError):
        TransactionUpdate(type="invalid")
