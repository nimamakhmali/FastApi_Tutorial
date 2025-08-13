"""
مدل کاربر
تعریف جدول کاربران در پایگاه داده
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database.database import Base

class User(Base):
    """
    مدل کاربر
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="شناسه کاربر")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="ایمیل کاربر")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="نام کاربری")
    full_name = Column(String(100), nullable=True, comment="نام کامل")
    hashed_password = Column(String(255), nullable=False, comment="رمز عبور هش شده")
    is_active = Column(Boolean, default=True, comment="وضعیت فعال بودن")
    is_superuser = Column(Boolean, default=False, comment="وضعیت ادمین")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="تاریخ ایجاد")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="تاریخ به‌روزرسانی")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def to_dict(self):
        """
        تبدیل مدل به دیکشنری
        """
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
