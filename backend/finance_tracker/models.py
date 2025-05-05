from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Literal
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    email: str
    is_locked: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CategoryBase(BaseModel):
    name: str
    type: Literal["income", "expense"]

class CategoryCreate(CategoryBase):
    is_predefined: bool = False

class Category(CategoryBase):
    id: int
    is_predefined: bool
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None
    date: datetime
    type: Literal["income", "expense"]
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        return v.lower()

class TransactionCreate(TransactionBase):
    category_id: int

class Transaction(TransactionBase):
    id: int
    user_id: int
    category_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BudgetBase(BaseModel):
    target_amount: float
    start_date: datetime
    end_date: datetime
    name: Optional[str] = None

class BudgetCreate(BudgetBase):
    category_id: Optional[int] = None

class Budget(BudgetBase):
    id: int
    user_id: int
    category_id: Optional[int] = None
    current_amount: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TransactionUpdate(BaseModel):
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
        return v.lower() if v else v
