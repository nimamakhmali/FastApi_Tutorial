# بخش 8: بهترین شیوه‌ها در FastAPI

## فهرست مطالب
- [Code Organization](#code-organization)
- [Performance Optimization](#performance-optimization)
- [Security Best Practices](#security-best-practices)
- [Error Handling](#error-handling)
- [Documentation](#documentation)
- [Testing Strategies](#testing-strategies)
- [Database Best Practices](#database-best-practices)
- [API Design](#api-design)
- [Development Workflow](#development-workflow)
- [Production Readiness](#production-readiness)

## Code Organization

### Project Structure
```
fastapi_tutorial/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── users.py
│   │   │   │   ├── posts.py
│   │   │   │   └── auth.py
│   │   │   └── api.py
│   │   └── deps.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   └── post.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── post.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── post.py
│   └── utils/
│       ├── __init__.py
│       ├── email.py
│       └── security.py
├── tests/
├── alembic/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Dependency Injection Pattern
```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
```

## Performance Optimization

### Async Operations
```python
# app/crud/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User

class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[User]:
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, user_data: dict) -> User:
        db_user = User(**user_data)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
```

### Caching Strategy
```python
# app/core/cache.py
import redis
from functools import wraps
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time: int = 300, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key,
                expire_time,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator
```

## Security Best Practices

### Input Validation
```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    full_name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
```

### Rate Limiting
```python
# app/core/rate_limiting.py
from fastapi import HTTPException, Request
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True

def rate_limit(requests_per_minute: int = 60):
    limiter = RateLimiter(requests_per_minute)
    
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_id = request.client.host
            
            if not limiter.is_allowed(client_id):
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

## Error Handling

### Custom Exceptions
```python
# app/core/exceptions.py
from fastapi import HTTPException, status

class FastAPIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str | None = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class UserNotFoundException(FastAPIException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
            error_code="USER_NOT_FOUND"
        )

class UserAlreadyExistsException(FastAPIException):
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {email} already exists",
            error_code="USER_ALREADY_EXISTS"
        )

class InsufficientPermissionsException(FastAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
            error_code="INSUFFICIENT_PERMISSIONS"
        )
```

### Global Exception Handler
```python
# app/core/handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import FastAPIException
import logging

logger = logging.getLogger(__name__)

async def fastapi_exception_handler(request: Request, exc: FastAPIException):
    """Handle custom FastAPI exceptions"""
    logger.error(f"FastAPI Exception: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "timestamp": time.time()
            }
        }
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.error(f"Validation Error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors(),
                "timestamp": time.time()
            }
        }
    )
```

## Documentation

### API Documentation
```python
# app/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="FastAPI Tutorial",
    description="""
    A comprehensive FastAPI tutorial covering all aspects of modern web development.
    
    ## Features
    
    * **User Management**: Register, login, and manage user profiles
    * **Post Management**: Create, read, update, and delete posts
    * **Authentication**: JWT-based authentication with role-based access control
    * **File Upload**: Secure file upload with validation
    * **Real-time**: WebSocket support for real-time features
    
    ## Authentication
    
    This API uses JWT tokens for authentication. To use protected endpoints:
    
    1. Register a new user at `/auth/register`
    2. Login at `/auth/login` to get an access token
    3. Include the token in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    contact={
        "name": "FastAPI Tutorial",
        "email": "support@fastapi-tutorial.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Code Documentation
```python
# app/crud/user.py
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserCRUD:
    """
    CRUD operations for User model.
    
    This class provides all database operations related to users,
    including create, read, update, and delete operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize UserCRUD with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            UserAlreadyExistsException: If user with same email exists
        """
        # Check if user already exists
        existing_user = self.get_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsException(user_data.email)
        
        # Create new user
        db_user = User(**user_data.dict())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """
        Get multiple users with pagination.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of user objects
        """
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update(
        self, 
        user_id: int, 
        user_data: UserUpdate
    ) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated user object if found, None otherwise
        """
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None
        
        # Update only provided fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user was deleted, False if user not found
        """
        db_user = self.get_by_id(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
```

## Testing Strategies

### Test Organization
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.main import app
from app.api.deps import get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Create test database session"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from app.crud.user import UserCRUD
    from app.schemas.user import UserCreate
    
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123",
        full_name="Test User"
    )
    
    crud = UserCRUD(db_session)
    return crud.create(user_data)

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers"""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    response = client.post("/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Test Examples
```python
# tests/test_users.py
import pytest
from fastapi.testclient import TestClient
from app.schemas.user import UserCreate

class TestUserManagement:
    """Test user management functionality"""
    
    def test_create_user(self, client: TestClient):
        """Test user creation"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "password" not in data  # Password should not be returned
    
    def test_create_user_duplicate_email(self, client: TestClient, test_user):
        """Test creating user with duplicate email"""
        user_data = {
            "email": "test@example.com",  # Same email as test_user
            "username": "anotheruser",
            "password": "password123",
            "full_name": "Another User"
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_get_user_profile(self, client: TestClient, auth_headers):
        """Test getting user profile"""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    def test_update_user_profile(self, client: TestClient, auth_headers):
        """Test updating user profile"""
        update_data = {"full_name": "Updated Name"}
        
        response = client.put("/users/me", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    def test_get_user_profile_unauthorized(self, client: TestClient):
        """Test getting user profile without authentication"""
        response = client.get("/users/me")
        assert response.status_code == 401
```

## Database Best Practices

### Connection Management
```python
# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Get database session.
    
    Yields:
        Database session
        
    Note:
        This function should be used as a dependency in FastAPI endpoints.
        The session will be automatically closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_context():
    """
    Get database session context manager.
    
    Returns:
        Database session context manager
        
    Example:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    return SessionLocal()
```

### Migration Management
```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.db.base import Base
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.database_url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## API Design

### RESTful API Design
```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_active_user, get_current_superuser
from app.crud.user import UserCRUD
from app.schemas.user import User, UserCreate, UserUpdate
from app.db.session import get_db

router = APIRouter()

@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Retrieve users.
    
    Only superusers can access this endpoint.
    """
    crud = UserCRUD(db)
    users = crud.get_multi(skip=skip, limit=limit)
    return users

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create new user.
    
    Anyone can create a new user account.
    """
    crud = UserCRUD(db)
    return crud.create(user_data)

@router.get("/me", response_model=User)
def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user.
    
    Returns the currently authenticated user's information.
    """
    return current_user

@router.put("/me", response_model=User)
def update_user_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user.
    
    Update the currently authenticated user's information.
    """
    crud = UserCRUD(db)
    return crud.update(current_user.id, user_data)

@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.
    
    Users can only access their own information unless they are superusers.
    """
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    crud = UserCRUD(db)
    user = crud.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Update user.
    
    Only superusers can update other users.
    """
    crud = UserCRUD(db)
    user = crud.update(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Delete user.
    
    Only superusers can delete users.
    """
    crud = UserCRUD(db)
    if not crud.delete(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
```

## Development Workflow

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Development Scripts
```python
# scripts/dev.py
#!/usr/bin/env python3
"""
Development utility scripts.
"""
import subprocess
import sys
from pathlib import Path

def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check)
    return result

def install_dependencies():
    """Install development dependencies."""
    run_command("pip install -r requirements.txt")
    run_command("pip install -r requirements-dev.txt")

def run_tests():
    """Run tests with coverage."""
    run_command("pytest --cov=app --cov-report=html --cov-report=term-missing")

def run_linting():
    """Run code linting."""
    run_command("flake8 app tests")
    run_command("black --check app tests")
    run_command("isort --check-only app tests")

def run_type_checking():
    """Run type checking."""
    run_command("mypy app")

def format_code():
    """Format code."""
    run_command("black app tests")
    run_command("isort app tests")

def run_all_checks():
    """Run all development checks."""
    print("Running all development checks...")
    
    try:
        run_linting()
        run_type_checking()
        run_tests()
        print("All checks passed! ✅")
    except subprocess.CalledProcessError as e:
        print(f"Check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/dev.py <command>")
        print("Commands: install, test, lint, type-check, format, check-all")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "install":
        install_dependencies()
    elif command == "test":
        run_tests()
    elif command == "lint":
        run_linting()
    elif command == "type-check":
        run_type_checking()
    elif command == "format":
        format_code()
    elif command == "check-all":
        run_all_checks()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
```

## Production Readiness

### Health Checks
```python
# app/core/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
import redis
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns the health status of all system components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Database health check
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis health check
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # External API health check
    try:
        # Add your external API health checks here
        health_status["services"]["external_apis"] = "healthy"
    except Exception as e:
        health_status["services"]["external_apis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status

@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Used by Kubernetes to determine if the application is ready to receive traffic.
    """
    return {"status": "ready"}

@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Used by Kubernetes to determine if the application is alive.
    """
    return {"status": "alive"}
```

### Monitoring Setup
```python
# app/core/monitoring.py
import logging
import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

async def metrics_middleware(request: Request, call_next):
    """Middleware to collect metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Database monitoring
def monitor_db_query(operation: str, table: str):
    """Decorator to monitor database queries."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        return wrapper
    return decorator
```

## نکات مهم

1. **Code Organization**: کد را به صورت منطقی سازماندهی کنید
2. **Security First**: همیشه امنیت را در اولویت قرار دهید
3. **Testing**: تست‌های جامع بنویسید
4. **Documentation**: مستندات کامل و به‌روز نگه دارید
5. **Performance**: عملکرد را بهینه کنید
6. **Monitoring**: سیستم‌های monitoring راه‌اندازی کنید
7. **Best Practices**: از بهترین شیوه‌های صنعت پیروی کنید
