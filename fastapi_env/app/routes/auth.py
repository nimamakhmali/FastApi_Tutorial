"""
Route های احراز هویت
مدیریت ورود، ثبت‌نام و احراز هویت
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.schemas.base import ResponseSchema

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=ResponseSchema)
async def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    ثبت‌نام کاربر جدید
    """
    # بررسی وجود کاربر با ایمیل یا نام کاربری
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="کاربر با این ایمیل یا نام کاربری قبلاً وجود دارد"
        )
    
    # ایجاد کاربر جدید
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return ResponseSchema(
        message="کاربر با موفقیت ثبت‌نام شد",
        success=True
    )

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    ورود کاربر
    """
    # پیدا کردن کاربر
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="حساب کاربری غیرفعال است"
        )
    
    # ایجاد توکن
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Any:
    """
    دریافت اطلاعات کاربر فعلی
    """
    from app.utils.security import verify_token
    
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربر یافت نشد"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
