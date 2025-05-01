from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import validator

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

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CategoryBase(BaseModel):
    name: str
    type: str  # 'income' or 'expense'

class CategoryCreate(CategoryBase):
    is_predefined: bool = False

class Category(CategoryBase):
    id: int
    is_predefined: bool
    user_id: Optional[int] = None

    class Config:
        from_attributes = True  # или orm_mode = True для Pydantic v2
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None
    date: datetime
    type: str  # 'income' or 'expense'
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

    @validator('type')
    def validate_type(cls, v):
        if v.lower() not in ['income', 'expense']:
            raise ValueError("Type must be either 'income' or 'expense'")
        return v.lower()

class TransactionCreate(TransactionBase):
    category_id: int

class Transaction(TransactionBase):
    id: int
    user_id: int
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

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
    category_id: Optional[int]
    current_amount: float
    is_active: bool

    class Config:
        from_attributes = True

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
    type: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None

    @validator('type')
    def validate_type(cls, v):
        if v is not None and v.lower() not in ['income', 'expense']:
            raise ValueError("Type must be either 'income' or 'expense'")
        return v.lower() if v else v