"""
Schema های کاربر
تعریف مدل‌های مربوط به کاربران
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from .base import BaseSchema

class UserBase(BaseSchema):
    """
    Schema پایه کاربر
    """
    email: EmailStr = Field(..., description="ایمیل کاربر")
    username: str = Field(..., min_length=3, max_length=50, description="نام کاربری")
    full_name: Optional[str] = Field(None, max_length=100, description="نام کامل")

class UserCreate(UserBase):
    """
    Schema برای ایجاد کاربر جدید
    """
    password: str = Field(..., min_length=8, description="رمز عبور")

class UserUpdate(BaseSchema):
    """
    Schema برای به‌روزرسانی کاربر
    """
    email: Optional[EmailStr] = Field(None, description="ایمیل کاربر")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="نام کاربری")
    full_name: Optional[str] = Field(None, max_length=100, description="نام کامل")
    is_active: Optional[bool] = Field(None, description="وضعیت فعال بودن")

class UserResponse(UserBase):
    """
    Schema برای پاسخ کاربر
    """
    id: int = Field(..., description="شناسه کاربر")
    is_active: bool = Field(..., description="وضعیت فعال بودن")
    created_at: datetime = Field(..., description="تاریخ ایجاد")
    updated_at: Optional[datetime] = Field(None, description="تاریخ به‌روزرسانی")

class UserInDB(UserResponse):
    """
    Schema برای کاربر در پایگاه داده
    """
    hashed_password: str = Field(..., description="رمز عبور هش شده")

class UserList(BaseSchema):
    """
    Schema برای لیست کاربران
    """
    users: list[UserResponse] = Field(..., description="لیست کاربران")
    total: int = Field(..., description="تعداد کل کاربران")
