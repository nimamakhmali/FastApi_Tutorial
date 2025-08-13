"""
FastAPI Tutorial - Main Application
از صفر تا فوق حرفه‌ای
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import routes
from app.routes import auth

# Import database
from app.database.database import create_tables

# Create FastAPI instance
app = FastAPI(
    title="FastAPI Tutorial",
    description="آموزش کامل FastAPI از صفر تا فوق حرفه‌ای",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در تولید، آدرس‌های خاص را مشخص کنید
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """
    صفحه اصلی API
    """
    return {
        "message": "خوش آمدید به FastAPI Tutorial! 🚀",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    بررسی سلامت API
    """
    return {"status": "healthy", "message": "API در حال کار است"}

# Basic CRUD endpoints for tutorial
@app.get("/api/v1/items")
async def get_items():
    """
    دریافت لیست آیتم‌ها
    """
    return {
        "items": [
            {"id": 1, "name": "آیتم ۱", "description": "توضیحات آیتم ۱"},
            {"id": 2, "name": "آیتم ۲", "description": "توضیحات آیتم ۲"},
        ]
    }

@app.get("/api/v1/items/{item_id}")
async def get_item(item_id: int):
    """
    دریافت آیتم بر اساس ID
    """
    if item_id == 1:
        return {"id": 1, "name": "آیتم ۱", "description": "توضیحات آیتم ۱"}
    elif item_id == 2:
        return {"id": 2, "name": "آیتم ۲", "description": "توضیحات آیتم ۲"}
    else:
        raise HTTPException(status_code=404, detail="آیتم یافت نشد")

# Error handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "صفحه مورد نظر یافت نشد"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "خطای داخلی سرور"}
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """
    رویداد شروع برنامه
    """
    create_tables()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
