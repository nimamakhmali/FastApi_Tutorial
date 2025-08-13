"""
FastAPI Tutorial - Development Runner
فایل اجرای برنامه در حالت توسعه
"""

import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    # تنظیمات توسعه
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("ENVIRONMENT", "development")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True
    )
