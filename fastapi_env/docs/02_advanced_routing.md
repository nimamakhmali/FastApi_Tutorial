# بخش 2: مسیریابی پیشرفته در FastAPI

## فهرست مطالب
- [Dependencies](#dependencies)
- [Path Operations](#path-operations)
- [Query Parameters](#query-parameters)
- [Path Parameters](#path-parameters)
- [Request Body](#request-body)
- [Response Models](#response-models)
- [Status Codes](#status-codes)
- [Headers](#headers)
- [Cookies](#cookies)
- [File Uploads](#file-uploads)
- [Form Data](#form-data)

## Dependencies

### Dependency Injection
```python
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### Multiple Dependencies
```python
def get_current_user(token: str = Depends(oauth2_scheme)):
    # logic here
    pass

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.get("/users/me/")
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
```

## Path Operations

### HTTP Methods
```python
@app.get("/items/")      # GET
@app.post("/items/")     # POST
@app.put("/items/{id}")  # PUT
@app.delete("/items/{id}") # DELETE
@app.patch("/items/{id}")  # PATCH
@app.head("/items/")     # HEAD
@app.options("/items/")  # OPTIONS
```

### Path Parameters with Types
```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

@app.get("/users/{user_id}/orders/{order_id}")
def read_user_order(user_id: int, order_id: int):
    return {"user_id": user_id, "order_id": order_id}
```

### Path Parameters with Validation
```python
from pydantic import Field

@app.get("/items/{item_id}")
def read_item(item_id: int = Field(..., gt=0, description="شناسه آیتم")):
    return {"item_id": item_id}
```

## Query Parameters

### Basic Query Parameters
```python
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}
```

### Optional Query Parameters
```python
from typing import Optional

@app.get("/items/")
def read_items(q: Optional[str] = None):
    return {"q": q}
```

### Query Parameters with Validation
```python
@app.get("/items/")
def read_items(
    skip: int = Field(0, ge=0, description="تعداد آیتم‌های رد شده"),
    limit: int = Field(100, ge=1, le=1000, description="حداکثر تعداد آیتم‌ها")
):
    return {"skip": skip, "limit": limit}
```

### Multiple Query Parameters
```python
@app.get("/items/")
def read_items(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None
):
    return {
        "skip": skip,
        "limit": limit,
        "category": category,
        "price_min": price_min,
        "price_max": price_max
    }
```

## Request Body

### Basic Request Body
```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

@app.post("/items/")
def create_item(item: Item):
    return item
```

### Nested Models
```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class User(BaseModel):
    name: str
    email: str
    address: Address

@app.post("/users/")
def create_user(user: User):
    return user
```

### Request Body with Validation
```python
class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    tax: Optional[float] = Field(None, ge=0)

    class Config:
        schema_extra = {
            "example": {
                "name": "لپ‌تاپ",
                "description": "لپ‌تاپ گیمینگ",
                "price": 50000000,
                "tax": 5000000
            }
        }
```

## Response Models

### Basic Response Model
```python
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    owner_id: int

    class Config:
        from_attributes = True

@app.post("/items/", response_model=ItemResponse)
def create_item(item: Item):
    # logic here
    return item_response
```

### Response with Status Code
```python
from fastapi import status

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item_response
```

### Response with Headers
```python
from fastapi import Response

@app.post("/items/")
def create_item(item: Item, response: Response):
    response.headers["X-Custom-Header"] = "CustomValue"
    return item
```

## Status Codes

### Common Status Codes
```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item

@app.get("/items/{item_id}", status_code=status.HTTP_200_OK)
def read_item(item_id: int):
    return {"item_id": item_id}

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    # delete logic
    return None
```

### Dynamic Status Codes
```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

## Headers

### Reading Headers
```python
from fastapi import Header

@app.get("/items/")
def read_items(user_agent: Optional[str] = Header(None)):
    return {"User-Agent": user_agent}
```

### Multiple Headers
```python
@app.get("/items/")
def read_items(
    user_agent: Optional[str] = Header(None),
    accept_language: Optional[str] = Header(None)
):
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }
```

### Custom Headers
```python
@app.get("/items/")
def read_items(x_token: Optional[str] = Header(None)):
    return {"X-Token": x_token}
```

## Cookies

### Reading Cookies
```python
from fastapi import Cookie

@app.get("/items/")
def read_items(session_id: Optional[str] = Cookie(None)):
    return {"session_id": session_id}
```

### Setting Cookies
```python
from fastapi import Response

@app.post("/login/")
def login(response: Response):
    response.set_cookie(key="session_id", value="abc123", max_age=3600)
    return {"message": "Logged in"}
```

## File Uploads

### Single File Upload
```python
from fastapi import File, UploadFile

@app.post("/upload/")
def upload_file(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }
```

### Multiple File Uploads
```python
@app.post("/upload/")
def upload_files(files: list[UploadFile] = File(...)):
    return {
        "filenames": [file.filename for file in files]
    }
```

### File Upload with Additional Data
```python
@app.post("/upload/")
def upload_file(
    file: UploadFile = File(...),
    description: str = Form(...)
):
    return {
        "filename": file.filename,
        "description": description
    }
```

## Form Data

### Basic Form Data
```python
from fastapi import Form

@app.post("/login/")
def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}
```

### Form with File Upload
```python
@app.post("/upload/")
def upload_file(
    file: UploadFile = File(...),
    description: str = Form(...),
    category: str = Form(...)
):
    return {
        "filename": file.filename,
        "description": description,
        "category": category
    }
```

## مثال کامل

```python
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

app = FastAPI()

# Models
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    category: str
    
    class Config:
        from_attributes = True

# Dependencies
def get_db():
    # database session logic
    pass

# Routes
@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # create item logic
    return item_response

@app.get("/items/", response_model=List[ItemResponse])
def read_items(
    skip: int = Field(0, ge=0),
    limit: int = Field(100, ge=1, le=1000),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # read items logic
    return items

@app.post("/upload/")
def upload_file(
    file: UploadFile = File(...),
    description: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    return {
        "filename": file.filename,
        "description": description,
        "uploaded_by": current_user.username
    }
```

## نکات مهم

1. **Validation**: همیشه از Pydantic برای validation استفاده کنید
2. **Type Hints**: از type hints استفاده کنید تا IDE بهتر کار کند
3. **Error Handling**: از HTTPException برای مدیریت خطاها استفاده کنید
4. **Dependencies**: از dependency injection برای کد تمیزتر استفاده کنید
5. **Response Models**: همیشه response model تعریف کنید
6. **Status Codes**: از status codes مناسب استفاده کنید
