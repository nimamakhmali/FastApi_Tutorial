# بخش 6: تست‌نویسی در FastAPI

## فهرست مطالب
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [API Testing](#api-testing)
- [Database Testing](#database-testing)
- [Authentication Testing](#authentication-testing)
- [Mocking](#mocking)
- [Test Coverage](#test-coverage)
- [Test Configuration](#test-configuration)
- [Performance Testing](#performance-testing)
- [Best Practices](#best-practices)

## Unit Testing

### Basic Unit Tests
```python
import pytest
from unittest.mock import Mock, patch
from app.utils.security import verify_password, get_password_hash

def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Verify the hash is different from original
    assert hashed != password
    
    # Verify password verification works
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_password_hash_is_consistent():
    """Test that password hashing produces consistent results"""
    password = "testpassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    # Hashes should be different (due to salt)
    assert hash1 != hash2
    
    # But both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
```

### Testing Pydantic Models
```python
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserUpdate

def test_user_create_valid():
    """Test valid user creation"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    user = UserCreate(**user_data)
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.password == "testpassword123"
    assert user.full_name == "Test User"

def test_user_create_invalid_email():
    """Test invalid email validation"""
    user_data = {
        "email": "invalid-email",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    with pytest.raises(ValidationError):
        UserCreate(**user_data)

def test_user_update_partial():
    """Test partial user update"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    user = UserCreate(**user_data)
    
    # Update only some fields
    update_data = {"full_name": "Updated Name"}
    updated_user = UserUpdate(**update_data)
    
    # Original user should not be changed
    assert user.full_name is None
    assert updated_user.full_name == "Updated Name"
```

### Testing Utility Functions
```python
from app.utils.security import create_access_token, verify_token
from datetime import timedelta

def test_create_access_token():
    """Test access token creation"""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_token_valid():
    """Test valid token verification"""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    payload = verify_token(token)
    assert payload["sub"] == "testuser"

def test_verify_token_invalid():
    """Test invalid token verification"""
    invalid_token = "invalid.token.here"
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token(invalid_token)
    
    assert exc_info.value.status_code == 401

def test_token_expiration():
    """Test token expiration"""
    data = {"sub": "testuser"}
    expires_delta = timedelta(seconds=1)
    token = create_access_token(data, expires_delta=expires_delta)
    
    # Token should be valid initially
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    
    # Wait for expiration
    import time
    time.sleep(2)
    
    # Token should be invalid after expiration
    with pytest.raises(HTTPException):
        verify_token(token)
```

## Integration Testing

### Database Integration Tests
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.database import Base, get_db
from app.models.user import User
from app.crud.user import create_user, get_user_by_email

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_create_user(db_session):
    """Test user creation in database"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    user = create_user(db_session, user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.hashed_password != "testpassword123"  # Should be hashed

def test_get_user_by_email(db_session):
    """Test getting user by email"""
    # Create a user first
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    created_user = create_user(db_session, user_data)
    
    # Get user by email
    found_user = get_user_by_email(db_session, "test@example.com")
    
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "test@example.com"

def test_get_user_by_email_not_found(db_session):
    """Test getting non-existent user by email"""
    found_user = get_user_by_email(db_session, "nonexistent@example.com")
    assert found_user is None
```

## API Testing

### Basic API Tests
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI Tutorial"}

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_items():
    """Test getting items"""
    response = client.get("/api/v1/items/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_item():
    """Test getting a specific item"""
    response = client.get("/api/v1/items/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data

def test_get_item_not_found():
    """Test getting non-existent item"""
    response = client.get("/api/v1/items/999")
    assert response.status_code == 404
```

### Authentication API Tests
```python
def test_register_user(client):
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "password" not in data  # Password should not be returned

def test_register_user_duplicate_email(client, db_session):
    """Test registering user with duplicate email"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    # Register first user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Try to register second user with same email
    user_data["username"] = "testuser2"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_user(client, db_session):
    """Test user login"""
    # First register a user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    client.post("/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_user_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
```

### Protected Endpoint Tests
```python
def test_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without token"""
    response = client.get("/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_protected_endpoint_with_token(client, db_session):
    """Test accessing protected endpoint with valid token"""
    # Register and login to get token
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    client.post("/auth/register", json=user_data)
    
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    login_response = client.post("/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"

def test_protected_endpoint_with_invalid_token(client):
    """Test accessing protected endpoint with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401
```

## Database Testing

### Database Transaction Tests
```python
import pytest
from sqlalchemy.orm import Session

@pytest.fixture
def db_transaction():
    """Create a database transaction for testing"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

def test_user_creation_rollback(db_transaction):
    """Test that user creation can be rolled back"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    user = create_user(db_transaction, user_data)
    assert user.id is not None
    
    # Transaction will be rolled back automatically
    # So the user should not exist in the database after the test

def test_database_constraints(db_transaction):
    """Test database constraints"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    # Create first user
    create_user(db_transaction, user_data)
    
    # Try to create second user with same email (should fail)
    user_data["username"] = "testuser2"
    with pytest.raises(Exception):  # Should raise integrity error
        create_user(db_transaction, user_data)
```

### Database Migration Tests
```python
def test_database_migrations():
    """Test database migrations"""
    from alembic import command
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    
    # Verify tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "users" in tables
    assert "posts" in tables
    
    # Run downgrade
    command.downgrade(alembic_cfg, "base")
```

## Authentication Testing

### JWT Token Tests
```python
def test_jwt_token_creation():
    """Test JWT token creation and validation"""
    user_data = {"sub": "testuser", "role": "user"}
    token = create_access_token(user_data)
    
    # Verify token structure
    assert isinstance(token, str)
    assert len(token.split('.')) == 3  # JWT has 3 parts
    
    # Verify token content
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    assert payload["role"] == "user"

def test_jwt_token_expiration():
    """Test JWT token expiration"""
    user_data = {"sub": "testuser"}
    expires_delta = timedelta(seconds=1)
    token = create_access_token(user_data, expires_delta=expires_delta)
    
    # Token should be valid initially
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    
    # Wait for expiration
    import time
    time.sleep(2)
    
    # Token should be invalid after expiration
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401

def test_refresh_token():
    """Test refresh token functionality"""
    user_data = {"sub": "testuser"}
    refresh_token = create_refresh_token(user_data)
    
    # Verify refresh token
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "refresh"
    assert payload["sub"] == "testuser"
```

### Role-based Access Tests
```python
def test_admin_only_endpoint(client, db_session):
    """Test admin-only endpoint access"""
    # Create admin user
    admin_data = {
        "email": "admin@example.com",
        "username": "admin",
        "password": "adminpass123",
        "role": "admin"
    }
    admin_user = create_user(db_session, admin_data)
    
    # Login as admin
    login_data = {"username": "admin", "password": "adminpass123"}
    login_response = client.post("/auth/login", data=login_data)
    admin_token = login_response.json()["access_token"]
    
    # Access admin endpoint
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/admin/users", headers=headers)
    assert response.status_code == 200

def test_admin_endpoint_regular_user(client, db_session):
    """Test admin endpoint access by regular user"""
    # Create regular user
    user_data = {
        "email": "user@example.com",
        "username": "user",
        "password": "userpass123",
        "role": "user"
    }
    create_user(db_session, user_data)
    
    # Login as regular user
    login_data = {"username": "user", "password": "userpass123"}
    login_response = client.post("/auth/login", data=login_data)
    user_token = login_response.json()["access_token"]
    
    # Try to access admin endpoint
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/admin/users", headers=headers)
    assert response.status_code == 403
```

## Mocking

### Mocking External Services
```python
from unittest.mock import patch, MagicMock

@patch('app.services.email_service.send_email')
def test_send_notification_email(mock_send_email, client):
    """Test sending notification email with mocked email service"""
    mock_send_email.return_value = True
    
    notification_data = {
        "email": "test@example.com",
        "message": "Test notification"
    }
    
    response = client.post("/send-notification", json=notification_data)
    assert response.status_code == 200
    
    # Verify email service was called
    mock_send_email.assert_called_once_with(
        "test@example.com",
        "Test notification"
    )

@patch('app.services.payment_service.process_payment')
def test_payment_processing(mock_process_payment, client):
    """Test payment processing with mocked payment service"""
    mock_process_payment.return_value = {"status": "success", "transaction_id": "12345"}
    
    payment_data = {
        "amount": 100.00,
        "currency": "USD",
        "card_number": "4111111111111111"
    }
    
    response = client.post("/process-payment", json=payment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["transaction_id"] == "12345"

@patch('app.services.external_api.fetch_data')
def test_external_api_integration(mock_fetch_data, client):
    """Test external API integration with mocked service"""
    mock_fetch_data.return_value = {"data": "external_data"}
    
    response = client.get("/external-data")
    assert response.status_code == 200
    
    data = response.json()
    assert data["data"] == "external_data"
```

### Mocking Database
```python
@patch('app.database.database.get_db')
def test_with_mocked_database(mock_get_db, client):
    """Test with mocked database"""
    # Create mock session
    mock_session = MagicMock()
    mock_get_db.return_value = mock_session
    
    # Mock database query results
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    response = client.get("/users/1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
```

## Test Coverage

### Coverage Configuration
```python
# pytest.ini
[tool:pytest]
addopts = --cov=app --cov-report=html --cov-report=term-missing
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Coverage Tests
```python
def test_coverage_utils():
    """Test utility functions for coverage"""
    # Test all branches of password validation
    assert verify_password("password", get_password_hash("password")) is True
    assert verify_password("wrong", get_password_hash("password")) is False
    
    # Test token creation with different parameters
    data = {"sub": "testuser"}
    token1 = create_access_token(data)
    token2 = create_access_token(data, timedelta(minutes=60))
    
    assert token1 != token2
    assert verify_token(token1)["sub"] == "testuser"
    assert verify_token(token2)["sub"] == "testuser"

def test_coverage_models():
    """Test model validation for coverage"""
    # Test valid user creation
    valid_user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    assert valid_user.email == "test@example.com"
    
    # Test invalid user creation
    with pytest.raises(ValidationError):
        UserCreate(
            email="invalid-email",
            username="testuser",
            password="password123"
        )
    
    # Test partial updates
    update_data = UserUpdate(full_name="New Name")
    assert update_data.full_name == "New Name"
    assert update_data.email is None
```

## Test Configuration

### Test Environment Setup
```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.database import Base, get_db
from app.main import app

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
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    return create_user(db_session, user_data)

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

### Test Data Factories
```python
# tests/factories.py
import factory
from app.models.user import User
from app.schemas.user import UserCreate

class UserFactory(factory.Factory):
    class Meta:
        model = UserCreate
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.Faker("password")
    full_name = factory.Faker("name")

def create_test_user(db_session, **kwargs):
    """Create a test user in database"""
    user_data = UserFactory.build(**kwargs)
    return create_user(db_session, user_data)

def create_multiple_users(db_session, count=5):
    """Create multiple test users"""
    users = []
    for _ in range(count):
        user = create_test_user(db_session)
        users.append(user)
    return users
```

## Performance Testing

### Load Testing
```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

def test_endpoint_performance(client):
    """Test endpoint performance under load"""
    def make_request():
        return client.get("/health")
    
    # Make 100 concurrent requests
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        responses = [future.result() for future in futures]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # All requests should succeed
    assert all(response.status_code == 200 for response in responses)
    
    # Performance should be reasonable (less than 5 seconds for 100 requests)
    assert total_time < 5.0
    
    print(f"Processed 100 requests in {total_time:.2f} seconds")

def test_database_performance(db_session):
    """Test database performance"""
    import time
    
    # Test bulk insert performance
    start_time = time.time()
    
    users = []
    for i in range(1000):
        user_data = {
            "email": f"user{i}@example.com",
            "username": f"user{i}",
            "password": "password123"
        }
        user = create_user(db_session, user_data)
        users.append(user)
    
    end_time = time.time()
    insert_time = end_time - start_time
    
    # Bulk insert should be fast
    assert insert_time < 10.0  # Less than 10 seconds for 1000 users
    
    print(f"Inserted 1000 users in {insert_time:.2f} seconds")
```

## Best Practices

### Test Organization
```python
# tests/test_auth.py
class TestAuthentication:
    """Test authentication functionality"""
    
    def test_user_registration(self, client):
        """Test user registration"""
        # Test implementation
    
    def test_user_login(self, client):
        """Test user login"""
        # Test implementation
    
    def test_token_validation(self, client):
        """Test token validation"""
        # Test implementation

# tests/test_users.py
class TestUserManagement:
    """Test user management functionality"""
    
    def test_get_user_profile(self, client, auth_headers):
        """Test getting user profile"""
        # Test implementation
    
    def test_update_user_profile(self, client, auth_headers):
        """Test updating user profile"""
        # Test implementation

# tests/test_posts.py
class TestPostManagement:
    """Test post management functionality"""
    
    def test_create_post(self, client, auth_headers):
        """Test creating a post"""
        # Test implementation
    
    def test_get_posts(self, client):
        """Test getting posts"""
        # Test implementation
```

### Test Documentation
```python
def test_complex_business_logic():
    """
    Test complex business logic with multiple scenarios.
    
    This test covers:
    1. Valid user registration
    2. Email verification process
    3. Account activation
    4. Welcome email sending
    
    Expected behavior:
    - User should be created with is_verified=False
    - Verification email should be sent
    - Account should be activated after verification
    - Welcome email should be sent after activation
    """
    # Test implementation with detailed comments
    pass
```

### Continuous Integration
```python
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

## مثال کامل

```python
# tests/test_complete_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestCompleteUserFlow:
    """Test complete user flow from registration to post creation"""
    
    def test_complete_user_flow(self, client, db_session):
        """
        Test complete user flow:
        1. User registration
        2. Email verification
        3. Login
        4. Profile update
        5. Post creation
        6. Post retrieval
        """
        # 1. User registration
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # 2. Email verification (mock)
        with patch('app.services.email_service.send_verification_email'):
            verification_response = client.post("/auth/verify-email", json={"token": "mock_token"})
            assert verification_response.status_code == 200
        
        # 3. Login
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Profile update
        update_data = {"full_name": "Updated Name"}
        update_response = client.put("/users/me", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # 5. Post creation
        post_data = {
            "title": "Test Post",
            "content": "This is a test post"
        }
        post_response = client.post("/posts/", json=post_data, headers=headers)
        assert post_response.status_code == 201
        
        post_id = post_response.json()["id"]
        
        # 6. Post retrieval
        get_post_response = client.get(f"/posts/{post_id}")
        assert get_post_response.status_code == 200
        
        post = get_post_response.json()
        assert post["title"] == "Test Post"
        assert post["content"] == "This is a test post"
        assert post["author"]["username"] == "testuser"

def test_error_handling(client):
    """Test error handling scenarios"""
    # Test invalid JSON
    response = client.post("/auth/register", data="invalid json")
    assert response.status_code == 422
    
    # Test missing required fields
    response = client.post("/auth/register", json={"email": "test@example.com"})
    assert response.status_code == 422
    
    # Test invalid email format
    response = client.post("/auth/register", json={
        "email": "invalid-email",
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 422

def test_security_scenarios(client, db_session):
    """Test security scenarios"""
    # Test SQL injection attempt
    response = client.get("/users/1'; DROP TABLE users; --")
    assert response.status_code == 404  # Should not crash
    
    # Test XSS attempt
    malicious_data = {
        "title": "<script>alert('xss')</script>",
        "content": "Normal content"
    }
    # Should be sanitized or rejected
    response = client.post("/posts/", json=malicious_data)
    assert response.status_code in [400, 422]  # Should be rejected
```

## نکات مهم

1. **Test Isolation**: هر تست باید مستقل باشد و به تست‌های دیگر وابسته نباشد
2. **Database Cleanup**: بعد از هر تست دیتابیس را پاک کنید
3. **Mocking**: برای سرویس‌های خارجی از mocking استفاده کنید
4. **Coverage**: حداقل 80% coverage داشته باشید
5. **Performance**: تست‌های عملکرد را اجرا کنید
6. **Security**: تست‌های امنیتی را فراموش نکنید
7. **Documentation**: تست‌ها را به خوبی مستند کنید
