"""
Module models.

Pydantic models for validating input data and generating API responses.
"""
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Literal
from datetime import datetime


class UserBase(BaseModel):
    """User fields."""

    username: str
    email: str


class UserCreate(UserBase):
    """The model for registering a new user."""

    password: str


class User(UserBase):
    """The model to display info."""

    id: int
    email: str
    is_locked: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    """Category fields."""

    name: str
    type: Literal["income", "expense"]


class CategoryCreate(CategoryBase):
    """The model for creating the new category."""

    is_predefined: bool = False


class Category(CategoryBase):
    """The model to display category."""

    id: int
    is_predefined: bool
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    """The model of transaction data."""

    amount: float
    description: Optional[str] = None
    date: datetime
    type: Literal["income", "expense"]
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        """Validate type."""
        return v.lower()


class TransactionCreate(TransactionBase):
    """The model for creating the new transaction."""

    category_id: int


class Transaction(TransactionBase):
    """The model to display transaction data."""

    id: int
    user_id: int
    category_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetBase(BaseModel):
    """The base model of budget."""

    target_amount: float
    start_date: datetime
    end_date: datetime
    name: Optional[str] = None


class BudgetCreate(BudgetBase):
    """The model for creating the new budget."""

    category_id: Optional[int] = None


class Budget(BudgetBase):
    """The model to display the budget."""

    id: int
    user_id: int
    category_id: Optional[int] = None
    current_amount: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """The model of token data."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """The model of the username of this token."""

    username: Optional[str] = None


class TransactionUpdate(BaseModel):
    """The model to update the transaction data."""

    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    category_id: Optional[int] = None
    type: Optional[Literal["income", "expense"]] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        """Validate type."""
        return v.lower() if v else v
