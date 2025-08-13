"""
Schema های پایه
تعریف مدل‌های مشترک
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """
    Schema پایه برای تمام مدل‌ها
    """
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ResponseSchema(BaseSchema):
    """
    Schema پایه برای پاسخ‌ها
    """
    message: str = Field(..., description="پیام پاسخ")
    success: bool = Field(default=True, description="وضعیت موفقیت")

class ErrorSchema(BaseSchema):
    """
    Schema برای خطاها
    """
    detail: str = Field(..., description="جزئیات خطا")
    error_code: Optional[str] = Field(None, description="کد خطا")

class PaginationSchema(BaseSchema):
    """
    Schema برای صفحه‌بندی
    """
    page: int = Field(1, ge=1, description="شماره صفحه")
    size: int = Field(10, ge=1, le=100, description="تعداد آیتم در هر صفحه")
    total: int = Field(..., description="تعداد کل آیتم‌ها")
    pages: int = Field(..., description="تعداد کل صفحات")
