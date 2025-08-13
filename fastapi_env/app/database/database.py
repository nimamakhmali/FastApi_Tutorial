"""
تنظیمات پایگاه داده
مدیریت اتصال و جلسات پایگاه داده
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_database_url

# Create database engine
engine = create_engine(
    get_database_url(),
    echo=True,  # نمایش کوئری‌ها در کنسول (برای توسعه)
    pool_pre_ping=True,  # بررسی اتصال قبل از استفاده
    pool_recycle=300,  # بازیابی اتصال هر 5 دقیقه
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """
    Dependency برای دریافت جلسه پایگاه داده
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """
    ایجاد تمام جداول
    """
    Base.metadata.create_all(bind=engine)

# Drop all tables
def drop_tables():
    """
    حذف تمام جداول
    """
    Base.metadata.drop_all(bind=engine)
