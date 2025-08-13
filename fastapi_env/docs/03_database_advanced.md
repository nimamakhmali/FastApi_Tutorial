# بخش 3: پایگاه داده پیشرفته در FastAPI

## فهرست مطالب
- [Relationships](#relationships)
- [Migrations with Alembic](#migrations-with-alembic)
- [Database Sessions](#database-sessions)
- [CRUD Operations](#crud-operations)
- [Query Optimization](#query-optimization)
- [Transactions](#transactions)
- [Connection Pooling](#connection-pooling)
- [Database Events](#database-events)

## Relationships

### One-to-Many Relationship
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    
    # Relationship
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship
    author = relationship("User", back_populates="posts")
```

### Many-to-Many Relationship
```python
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

# Association table
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id")),
    Column("tag_id", Integer, ForeignKey("tags.id"))
)

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    
    # Many-to-Many relationship
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Many-to-Many relationship
    posts = relationship("Post", secondary=post_tags, back_populates="tags")
```

### One-to-One Relationship
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    
    # One-to-One relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(String)
    avatar_url = Column(String)
    
    # One-to-One relationship
    user = relationship("User", back_populates="profile")
```

## Migrations with Alembic

### Initial Setup
```bash
# Initialize Alembic
alembic init alembic

# Create first migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Migration Configuration (alembic.ini)
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://user:password@localhost/fastapi_tutorial
```

### Migration Environment (env.py)
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.models import Base
from app.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.database_url

def run_migrations_offline() -> None:
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
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Creating Migrations
```bash
# Create migration for new model
alembic revision --autogenerate -m "Add user profile"

# Create empty migration
alembic revision -m "Add custom index"

# Edit migration file
# alembic/versions/xxx_add_user_profile.py
```

### Migration File Example
```python
"""Add user profile

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Create table
    op.create_table('user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index
    op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
```

## Database Sessions

### Session Management
```python
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in FastAPI
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### Async Database Sessions
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async_engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/fastapi_tutorial"
)

AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

# Usage in FastAPI
async def read_users(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

## CRUD Operations

### Create Operations
```python
def create_user(db: Session, user_data: UserCreate):
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_with_profile(db: Session, user_data: UserCreate, profile_data: UserProfileCreate):
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db_profile = UserProfile(
        bio=profile_data.bio,
        avatar_url=profile_data.avatar_url
    )
    
    db_user.profile = db_profile
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

### Read Operations
```python
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_with_posts(db: Session, user_id: int):
    return db.query(User).options(joinedload(User.posts)).filter(User.id == user_id).first()
```

### Update Operations
```python
def update_user(db: Session, user_id: int, user_data: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_partial(db: Session, user_id: int, **kwargs):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    for field, value in kwargs.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user
```

### Delete Operations
```python
def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def soft_delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    
    db_user.is_active = False
    db_user.deleted_at = datetime.utcnow()
    db.commit()
    return True
```

## Query Optimization

### Eager Loading
```python
from sqlalchemy.orm import joinedload, selectinload

# Load related data in one query
def get_users_with_posts(db: Session):
    return db.query(User).options(joinedload(User.posts)).all()

# Load collections efficiently
def get_users_with_posts_selectin(db: Session):
    return db.query(User).options(selectinload(User.posts)).all()
```

### Lazy Loading
```python
def get_user_posts_lazy(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    # Posts will be loaded when accessed
    return user.posts if user else []
```

### Query Optimization
```python
from sqlalchemy import select, func

def get_user_count_by_status(db: Session):
    return db.query(
        User.is_active,
        func.count(User.id).label('count')
    ).group_by(User.is_active).all()

def get_users_with_post_count(db: Session):
    return db.query(
        User,
        func.count(Post.id).label('post_count')
    ).outerjoin(Post).group_by(User.id).all()
```

## Transactions

### Basic Transactions
```python
def create_user_with_posts(db: Session, user_data: UserCreate, posts_data: List[PostCreate]):
    try:
        # Create user
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password)
        )
        db.add(db_user)
        db.flush()  # Get user ID without committing
        
        # Create posts
        for post_data in posts_data:
            db_post = Post(
                title=post_data.title,
                content=post_data.content,
                author_id=db_user.id
            )
            db.add(db_post)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise e
```

### Nested Transactions
```python
from contextlib import contextmanager

@contextmanager
def transaction(db: Session):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

def create_user_with_profile_transaction(db: Session, user_data: UserCreate, profile_data: UserProfileCreate):
    with transaction(db):
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password)
        )
        db.add(db_user)
        db.flush()
        
        db_profile = UserProfile(
            user_id=db_user.id,
            bio=profile_data.bio,
            avatar_url=profile_data.avatar_url
        )
        db.add(db_profile)
        
        return db_user
```

## Connection Pooling

### Pool Configuration
```python
from sqlalchemy import create_engine

engine = create_engine(
    settings.database_url,
    pool_size=20,  # Number of connections to maintain
    max_overflow=30,  # Additional connections when pool is full
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=True  # Log SQL queries
)
```

### Async Pool Configuration
```python
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    settings.async_database_url,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=True
)
```

## Database Events

### Model Events
```python
from sqlalchemy import event
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@event.listens_for(User, 'before_insert')
def set_created_at(mapper, connection, target):
    target.created_at = datetime.utcnow()

@event.listens_for(User, 'before_update')
def set_updated_at(mapper, connection, target):
    target.updated_at = datetime.utcnow()
```

### Session Events
```python
@event.listens_for(Session, 'after_commit')
def after_commit(session):
    print("Transaction committed")

@event.listens_for(Session, 'after_rollback')
def after_rollback(session):
    print("Transaction rolled back")
```

## مثال کامل

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Optional

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(String(500))
    avatar_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="profile")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String(5000))
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    author = relationship("User", back_populates="posts")

# CRUD Operations
class UserCRUD:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_data: UserCreate) -> User:
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_with_posts(self, user_id: int) -> Optional[User]:
        return self.db.query(User).options(joinedload(User.posts)).filter(User.id == user_id).first()
    
    def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete(self, user_id: int) -> bool:
        db_user = self.get_by_id(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
```

## نکات مهم

1. **Always use transactions**: برای عملیات‌های چندگانه از transaction استفاده کنید
2. **Optimize queries**: از eager loading برای جلوگیری از N+1 queries استفاده کنید
3. **Use migrations**: همیشه از Alembic برای تغییرات دیتابیس استفاده کنید
4. **Handle errors**: خطاهای دیتابیس را به درستی مدیریت کنید
5. **Connection pooling**: برای عملکرد بهتر از connection pooling استفاده کنید
6. **Indexes**: برای فیلدهای پرکاربرد index ایجاد کنید
