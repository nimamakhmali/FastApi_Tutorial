# بخش 1: مبانی FastAPI 🎯

## مقدمه

FastAPI یک فریم‌ورک مدرن و سریع برای ساخت API در Python است که بر اساس Python 3.7+ و type hints ساخته شده است.

## ویژگی‌های کلیدی

- **سریع**: عملکرد بالا، قابل مقایسه با NodeJS و Go
- **سریع در توسعه**: افزایش سرعت توسعه تا 200-300%
- **کمتر خطا**: کاهش 40% خطاهای انسانی
- **هوشمند**: تکمیل خودکار کد
- **ساده**: طراحی شده برای آسان‌سازی استفاده
- **کوتاه**: کمینه‌سازی کد تکراری
- **مستحکم**: تولید کد آماده برای تولید
- **مستندات خودکار**: تولید خودکار مستندات API

## نصب و راه‌اندازی

```bash
# نصب FastAPI
pip install fastapi

# نصب سرور ASGI
pip install uvicorn[standard]

# یا نصب از requirements.txt
pip install -r requirements.txt
```

## اولین API ساده

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

## اجرای سرور

```bash
# اجرای ساده
uvicorn main:app --reload

# اجرا با تنظیمات بیشتر
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## مستندات خودکار

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## مسیریابی (Routing)

### HTTP Methods

```python
@app.get("/items")           # GET
@app.post("/items")          # POST
@app.put("/items/{id}")      # PUT
@app.delete("/items/{id}")   # DELETE
@app.patch("/items/{id}")    # PATCH
```

### Path Parameters

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

### Query Parameters

```python
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

### Request Body

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

@app.post("/items/")
def create_item(item: Item):
    return item
```

## Type Hints و Validation

FastAPI از type hints برای validation و تولید مستندات استفاده می‌کند:

```python
from typing import Optional, List

@app.get("/users/{user_id}")
def read_user(
    user_id: int,
    q: Optional[str] = None,
    items: List[str] = []
):
    return {"user_id": user_id, "q": q, "items": items}
```

## Error Handling

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

## مثال کامل

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="My API", version="1.0.0")

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

items_db = []

@app.get("/")
def read_root():
    return {"message": "Welcome to My API"}

@app.get("/items/", response_model=List[Item])
def read_items():
    return items_db

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.post("/items/", response_model=Item)
def create_item(item: Item):
    items_db.append(item)
    return item

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    if item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id] = item
    return item

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="Item not found")
    items_db.pop(item_id)
    return {"message": "Item deleted"}
```

## نکات مهم

1. **Type Hints**: همیشه از type hints استفاده کنید
2. **Validation**: از Pydantic models برای validation استفاده کنید
3. **Documentation**: از docstrings برای توضیح endpoint ها استفاده کنید
4. **Error Handling**: خطاها را به درستی مدیریت کنید
5. **Testing**: تست‌ها را بنویسید

## تمرین

1. یک API ساده برای مدیریت کتاب‌ها بسازید
2. CRUD operations را پیاده‌سازی کنید
3. Validation را اضافه کنید
4. Error handling را پیاده‌سازی کنید
5. تست‌ها را بنویسید
