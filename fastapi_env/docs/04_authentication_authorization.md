# بخش 4: احراز هویت و مجوزدهی در FastAPI

## فهرست مطالب
- [JWT Authentication](#jwt-authentication)
- [OAuth2 with Password Bearer](#oauth2-with-password-bearer)
- [Role-based Access Control](#role-based-access-control)
- [Permission-based Access](#permission-based-access)
- [Session-based Authentication](#session-based-authentication)
- [Two-Factor Authentication](#two-factor-authentication)
- [Password Reset](#password-reset)
- [Email Verification](#email-verification)

## JWT Authentication

### JWT Configuration
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### Password Hashing
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
```

## OAuth2 with Password Bearer

### OAuth2 Configuration
```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Login Endpoint
```python
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = get_user_by_username(db, username=username)
        if user is None:
            raise HTTPException(status_code=400, detail="User not found")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid refresh token")
```

## Role-based Access Control

### User Model with Roles
```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
```

### Role-based Dependencies
```python
def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

def require_admin():
    return require_role(UserRole.ADMIN)

def require_moderator():
    return require_role(UserRole.MODERATOR)

# Usage in routes
@app.get("/admin/users/")
def get_all_users(current_user: User = Depends(require_admin)):
    return {"message": "Admin only endpoint"}

@app.get("/moderator/posts/")
def moderate_posts(current_user: User = Depends(require_moderator)):
    return {"message": "Moderator endpoint"}
```

### Role-based Route Protection
```python
from functools import wraps

def require_roles(*roles: UserRole):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_active_user), **kwargs):
            if current_user.role not in roles and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

@app.get("/admin/dashboard/")
@require_roles(UserRole.ADMIN)
async def admin_dashboard(current_user: User):
    return {"message": f"Welcome {current_user.username} to admin dashboard"}
```

## Permission-based Access

### Permission Model
```python
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    permissions = relationship("Permission", secondary="role_permissions")
```

### Permission-based Dependencies
```python
def require_permission(permission_name: str):
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        user_permissions = get_user_permissions(current_user)
        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required"
            )
        return current_user
    return permission_checker

def get_user_permissions(user: User) -> List[str]:
    # Get user's role permissions
    permissions = []
    for role in user.roles:
        for permission in role.permissions:
            permissions.append(permission.name)
    return list(set(permissions))

@app.get("/posts/{post_id}/edit")
def edit_post(
    post_id: int,
    current_user: User = Depends(require_permission("edit_posts"))
):
    return {"message": f"Editing post {post_id}"}
```

## Session-based Authentication

### Session Management
```python
from fastapi import Request, Response
import secrets

class SessionManager:
    def __init__(self):
        self.sessions = {}  # In production, use Redis
    
    def create_session(self, user_id: int) -> str:
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        return session_id
    
    def get_session(self, session_id: str):
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

session_manager = SessionManager()

@app.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    session_id = session_manager.create_session(user.id)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    
    return {"message": "Logged in successfully"}

def get_current_user_from_session(
    request: Request,
    db: Session = Depends(get_db)
):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = get_user_by_id(db, session_data["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

## Two-Factor Authentication

### 2FA Setup
```python
import pyotp
import qrcode
from io import BytesIO
import base64

class TwoFactorAuth:
    def __init__(self):
        self.totp = pyotp.TOTP('base32secret3232')
    
    def generate_secret(self) -> str:
        return pyotp.random_base32()
    
    def generate_qr_code(self, username: str, secret: str) -> str:
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name="FastAPI Tutorial"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_code(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

two_factor_auth = TwoFactorAuth()

@app.post("/setup-2fa")
def setup_2fa(current_user: User = Depends(get_current_active_user)):
    secret = two_factor_auth.generate_secret()
    qr_code = two_factor_auth.generate_qr_code(current_user.username, secret)
    
    # Save secret to user (in production, encrypt it)
    current_user.two_factor_secret = secret
    
    return {
        "secret": secret,
        "qr_code": qr_code,
        "message": "Scan QR code with your authenticator app"
    }

@app.post("/verify-2fa")
def verify_2fa(
    code: str,
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.two_factor_secret:
        raise HTTPException(status_code=400, detail="2FA not set up")
    
    if two_factor_auth.verify_code(current_user.two_factor_secret, code):
        return {"message": "2FA verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
```

## Password Reset

### Password Reset Flow
```python
import secrets
from datetime import timedelta

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def create_password_reset_token(email: str) -> str:
    token = generate_reset_token()
    expires = datetime.utcnow() + timedelta(hours=1)
    
    # In production, save to database
    reset_tokens[token] = {
        "email": email,
        "expires": expires
    }
    
    return token

def verify_reset_token(token: str) -> str:
    token_data = reset_tokens.get(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    if datetime.utcnow() > token_data["expires"]:
        del reset_tokens[token]
        raise HTTPException(status_code=400, detail="Token expired")
    
    return token_data["email"]

@app.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        # Don't reveal if user exists
        return {"message": "If email exists, reset link sent"}
    
    reset_token = create_password_reset_token(email)
    reset_url = f"https://yourapp.com/reset-password?token={reset_token}"
    
    # Send email with reset_url
    # send_reset_email(email, reset_url)
    
    return {"message": "If email exists, reset link sent"}

@app.post("/reset-password")
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    email = verify_reset_token(token)
    user = get_user_by_email(db, email)
    
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    # Delete used token
    del reset_tokens[token]
    
    return {"message": "Password reset successfully"}
```

## Email Verification

### Email Verification Flow
```python
def create_verification_token(email: str) -> str:
    token = generate_reset_token()
    expires = datetime.utcnow() + timedelta(hours=24)
    
    verification_tokens[token] = {
        "email": email,
        "expires": expires
    }
    
    return token

@app.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user (not verified)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        is_verified=False
    )
    db.add(user)
    db.commit()
    
    # Send verification email
    verification_token = create_verification_token(user.email)
    verification_url = f"https://yourapp.com/verify-email?token={verification_token}"
    # send_verification_email(user.email, verification_url)
    
    return {"message": "Registration successful. Please check your email."}

@app.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        email = verify_reset_token(token)
        user = get_user_by_email(db, email)
        
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        user.is_verified = True
        db.commit()
        
        del verification_tokens[token]
        
        return {"message": "Email verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@app.post("/resend-verification")
def resend_verification(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    verification_token = create_verification_token(current_user.email)
    verification_url = f"https://yourapp.com/verify-email?token={verification_token}"
    # send_verification_email(current_user.email, verification_url)
    
    return {"message": "Verification email sent"}
```

## مثال کامل

```python
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import List, Optional
import secrets

app = FastAPI()

# Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Storage for tokens (use Redis in production)
reset_tokens = {}
verification_tokens = {}

class AuthService:
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = AuthService.verify_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker

@app.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=AuthService.get_password_hash(user_data.password),
        is_verified=False
    )
    db.add(user)
    db.commit()
    
    return {"message": "Registration successful"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = AuthService.create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/admin/users")
def get_all_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    return {"message": "Admin endpoint"}

@app.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if user:
        token = create_password_reset_token(email)
        # Send email with token
        pass
    
    return {"message": "If email exists, reset link sent"}
```

## نکات مهم

1. **Always hash passwords**: هرگز پسوردها را به صورت plain text ذخیره نکنید
2. **Use HTTPS**: در production حتماً از HTTPS استفاده کنید
3. **Token expiration**: برای توکن‌ها حتماً expiration time تعیین کنید
4. **Rate limiting**: برای endpoint های حساس rate limiting اعمال کنید
5. **Logging**: تمام عملیات احراز هویت را log کنید
6. **Error messages**: پیام‌های خطا را generic نگه دارید تا اطلاعات حساس لو نرود
