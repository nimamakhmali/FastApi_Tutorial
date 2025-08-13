# بخش 5: ویژگی‌های پیشرفته FastAPI

## فهرست مطالب
- [Background Tasks](#background-tasks)
- [WebSockets](#websockets)
- [File Upload & Download](#file-upload--download)
- [Caching](#caching)
- [Rate Limiting](#rate-limiting)
- [Middleware](#middleware)
- [Custom Responses](#custom-responses)
- [API Versioning](#api-versioning)
- [Async Operations](#async-operations)
- [Event Handlers](#event-handlers)

## Background Tasks

### Basic Background Tasks
```python
from fastapi import BackgroundTasks
import time

def send_email_background(email: str, message: str):
    time.sleep(10)  # Simulate email sending
    print(f"Email sent to {email}: {message}")

@app.post("/send-notification/")
def send_notification(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email_background, email, message)
    return {"message": "Notification sent in background"}

def process_file_background(filename: str):
    time.sleep(5)  # Simulate file processing
    print(f"File {filename} processed")

@app.post("/upload-and-process/")
def upload_and_process(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # Process in background
    background_tasks.add_task(process_file_background, file.filename)
    
    return {"message": "File uploaded and processing started"}
```

### Background Tasks with Dependencies
```python
def send_email_with_db(email: str, message: str, db: Session):
    # Email sending logic
    time.sleep(5)
    
    # Log to database
    log = EmailLog(
        email=email,
        message=message,
        sent_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()

@app.post("/send-notification/")
def send_notification(
    email: str,
    message: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    background_tasks.add_task(send_email_with_db, email, message, db)
    return {"message": "Notification queued"}
```

## WebSockets

### Basic WebSocket
```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
```

### WebSocket with Authentication
```python
@app.websocket("/ws/")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    # Verify token
    try:
        payload = AuthService.verify_token(token)
        username = payload.get("sub")
        if not username:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{username} left the chat")
```

### WebSocket with Room Management
```python
class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect_to_room(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.rooms:
            self.rooms[room] = []
        self.rooms[room].append(websocket)

    def disconnect_from_room(self, websocket: WebSocket, room: str):
        if room in self.rooms:
            self.rooms[room].remove(websocket)
            if not self.rooms[room]:
                del self.rooms[room]

    async def broadcast_to_room(self, message: str, room: str):
        if room in self.rooms:
            for connection in self.rooms[room]:
                await connection.send_text(message)

room_manager = RoomManager()

@app.websocket("/ws/room/{room_name}")
async def websocket_room_endpoint(
    websocket: WebSocket,
    room_name: str
):
    await room_manager.connect_to_room(websocket, room_name)
    try:
        while True:
            data = await websocket.receive_text()
            await room_manager.broadcast_to_room(f"Message: {data}", room_name)
    except WebSocketDisconnect:
        room_manager.disconnect_from_room(websocket, room_name)
```

## File Upload & Download

### File Upload with Validation
```python
import os
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile):
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    return True

@app.post("/upload/")
def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    validate_file(file)
    
    # Create unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{current_user.id}_{int(time.time())}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # Save file info to database
    db_file = FileUpload(
        filename=unique_filename,
        original_filename=file.filename,
        file_size=len(content),
        uploaded_by=current_user.id,
        file_path=str(file_path)
    )
    db.add(db_file)
    db.commit()
    
    return {
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_size": len(content)
    }
```

### Multiple File Upload
```python
@app.post("/upload-multiple/")
def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user)
):
    uploaded_files = []
    
    for file in files:
        try:
            validate_file(file)
            
            file_extension = Path(file.filename).suffix
            unique_filename = f"{current_user.id}_{int(time.time())}_{len(uploaded_files)}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            uploaded_files.append({
                "filename": unique_filename,
                "original_filename": file.filename,
                "file_size": len(content)
            })
            
        except Exception as e:
            return {"error": f"Error uploading {file.filename}: {str(e)}"}
    
    return {"uploaded_files": uploaded_files}
```

### File Download
```python
from fastapi.responses import FileResponse
import mimetypes

@app.get("/download/{filename}")
def download_file(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if user has permission to download this file
    db_file = get_file_by_filename(db, filename)
    if not db_file or db_file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if content_type is None:
        content_type = "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=db_file.original_filename,
        media_type=content_type
    )
```

## Caching

### Redis Caching
```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
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

@app.get("/users/{user_id}")
@cache_result(expire_time=600)  # Cache for 10 minutes
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/posts/")
@cache_result(expire_time=300)  # Cache for 5 minutes
async def get_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    posts = get_posts_paginated(db, skip=skip, limit=limit)
    return posts
```

### In-Memory Caching
```python
from typing import Dict, Any
import time

class SimpleCache:
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str):
        if key in self.cache:
            item = self.cache[key]
            if time.time() < item['expires_at']:
                return item['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, expire_time: int = 300):
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + expire_time
        }
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()

simple_cache = SimpleCache()

def cache_result_simple(expire_time: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached_result = simple_cache.get(cache_key)
            if cached_result:
                return cached_result
            
            result = func(*args, **kwargs)
            simple_cache.set(cache_key, result, expire_time)
            
            return result
        return wrapper
    return decorator
```

## Rate Limiting

### Simple Rate Limiting
```python
from collections import defaultdict
import time

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

rate_limiter = RateLimiter(requests_per_minute=60)

def rate_limit(client_id: str = Depends(get_client_id)):
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )
    return client_id

@app.get("/api/data/")
def get_data(client_id: str = Depends(rate_limit)):
    return {"data": "some data"}

def get_client_id(request: Request) -> str:
    # Get client IP or user ID
    return request.client.host
```

### Advanced Rate Limiting with Redis
```python
def rate_limit_redis(
    requests_per_minute: int = 60,
    client_id: str = Depends(get_client_id)
):
    key = f"rate_limit:{client_id}"
    
    # Get current count
    current_count = redis_client.get(key)
    if current_count and int(current_count) >= requests_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )
    
    # Increment counter
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)  # Expire after 1 minute
    pipe.execute()
    
    return client_id

@app.get("/api/data/")
def get_data(client_id: str = Depends(rate_limit_redis)):
    return {"data": "some data"}
```

## Middleware

### Custom Middleware
```python
from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.2f}s")
    
    return response

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response
```

### Authentication Middleware
```python
@app.middleware("http")
async def authenticate_requests(request: Request, call_next):
    # Skip authentication for certain paths
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Check for authentication header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return await call_next(request)
    
    try:
        # Verify token
        token = auth_header.replace("Bearer ", "")
        payload = AuthService.verify_token(token)
        request.state.user = payload
    except:
        pass
    
    return await call_next(request)
```

## Custom Responses

### Custom Response Classes
```python
from fastapi.responses import JSONResponse
from typing import Any, Dict

class SuccessResponse(JSONResponse):
    def __init__(self, data: Any, message: str = "Success", status_code: int = 200):
        content = {
            "success": True,
            "message": message,
            "data": data
        }
        super().__init__(content=content, status_code=status_code)

class ErrorResponse(JSONResponse):
    def __init__(self, message: str, error_code: str = None, status_code: int = 400):
        content = {
            "success": False,
            "message": message,
            "error_code": error_code
        }
        super().__init__(content=content, status_code=status_code)

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        return ErrorResponse(
            message="User not found",
            error_code="USER_NOT_FOUND",
            status_code=404
        )
    
    return SuccessResponse(
        data=user,
        message="User retrieved successfully"
    )
```

### Streaming Response
```python
from fastapi.responses import StreamingResponse
import csv
import io

@app.get("/export/users")
def export_users_csv(db: Session = Depends(get_db)):
    def generate_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["ID", "Username", "Email", "Created At"])
        
        # Write data
        users = get_all_users(db)
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.created_at
            ])
        
        output.seek(0)
        return output.getvalue()
    
    return StreamingResponse(
        iter([generate_csv()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )
```

## API Versioning

### URL-based Versioning
```python
from fastapi import APIRouter

# Version 1
v1_router = APIRouter(prefix="/v1")

@v1_router.get("/users/")
def get_users_v1():
    return {"version": "v1", "users": []}

# Version 2
v2_router = APIRouter(prefix="/v2")

@v2_router.get("/users/")
def get_users_v2():
    return {"version": "v2", "users": [], "metadata": {}}

# Include routers
app.include_router(v1_router, tags=["v1"])
app.include_router(v2_router, tags=["v2"])
```

### Header-based Versioning
```python
from fastapi import Header

def get_api_version(accept_version: str = Header(None, alias="Accept-Version")):
    if accept_version is None:
        return "v1"
    return accept_version

@app.get("/users/")
def get_users(version: str = Depends(get_api_version)):
    if version == "v1":
        return {"version": "v1", "users": []}
    elif version == "v2":
        return {"version": "v2", "users": [], "metadata": {}}
    else:
        raise HTTPException(status_code=400, detail="Unsupported version")
```

## Async Operations

### Async Database Operations
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

@app.get("/users/")
async def get_users(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@app.post("/users/")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    db_user = User(**user_data.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

### Async External API Calls
```python
import httpx
import asyncio

async def fetch_user_data(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()

async def fetch_multiple_users(user_ids: List[int]):
    tasks = [fetch_user_data(user_id) for user_id in user_ids]
    results = await asyncio.gather(*tasks)
    return results

@app.get("/users/{user_id}/external")
async def get_user_with_external_data(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get external data
    external_data = await fetch_user_data(user_id)
    
    return {
        "user": user,
        "external_data": external_data
    }
```

## Event Handlers

### Startup and Shutdown Events
```python
@app.on_event("startup")
async def startup_event():
    # Initialize database
    await create_tables()
    
    # Initialize cache
    await initialize_cache()
    
    # Start background tasks
    asyncio.create_task(background_task())
    
    print("Application started")

@app.on_event("shutdown")
async def shutdown_event():
    # Close database connections
    await close_database_connections()
    
    # Clear cache
    await clear_cache()
    
    print("Application shutdown")

async def background_task():
    while True:
        await asyncio.sleep(60)  # Run every minute
        # Perform background operations
        await process_pending_tasks()
```

### Custom Event Handlers
```python
from fastapi import Request

@app.middleware("http")
async def add_event_handlers(request: Request, call_next):
    # Pre-request event
    await pre_request_handler(request)
    
    response = await call_next(request)
    
    # Post-request event
    await post_request_handler(request, response)
    
    return response

async def pre_request_handler(request: Request):
    # Log request
    logger.info(f"Request started: {request.method} {request.url}")
    
    # Add request ID
    request.state.request_id = str(uuid.uuid4())

async def post_request_handler(request: Request, response):
    # Log response
    logger.info(f"Request completed: {response.status_code}")
    
    # Add custom headers
    response.headers["X-Request-ID"] = getattr(request.state, "request_id", "")
```

## مثال کامل

```python
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import redis
from typing import List, Dict, Any

app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Background tasks
def send_email_background(email: str, message: str):
    time.sleep(5)  # Simulate email sending
    print(f"Email sent to {email}: {message}")

# Caching decorator
def cache_result(expire_time: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire_time, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

# Routes
@app.post("/send-notification/")
def send_notification(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email_background, email, message)
    return {"message": "Notification sent in background"}

@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/users/")
@cache_result(expire_time=600)
async def get_users(db: Session = Depends(get_db)):
    users = get_all_users(db)
    return users

@app.post("/upload/")
def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # Process in background
    background_tasks.add_task(process_file_background, file.filename)
    
    return {"message": "File uploaded and processing started"}

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = f"uploads/{filename}"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

# Event handlers
@app.on_event("startup")
async def startup_event():
    print("Application started")
    # Initialize services

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown")
    # Cleanup resources
```

## نکات مهم

1. **Background Tasks**: برای عملیات‌های زمان‌بر از background tasks استفاده کنید
2. **WebSockets**: برای ارتباط real-time از WebSockets استفاده کنید
3. **Caching**: برای بهبود عملکرد از caching استفاده کنید
4. **Rate Limiting**: برای جلوگیری از سوء استفاده از rate limiting استفاده کنید
5. **File Handling**: برای آپلود و دانلود فایل از validation استفاده کنید
6. **Async Operations**: برای عملیات‌های I/O از async استفاده کنید
7. **Error Handling**: خطاها را به درستی مدیریت کنید
