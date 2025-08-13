"""
تست‌های اصلی
تست endpoint های اصلی
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """
    تست endpoint اصلی
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

def test_health_check():
    """
    تست endpoint بررسی سلامت
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_get_items():
    """
    تست دریافت آیتم‌ها
    """
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

def test_get_item():
    """
    تست دریافت آیتم خاص
    """
    response = client.get("/api/v1/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

def test_get_item_not_found():
    """
    تست دریافت آیتم ناموجود
    """
    response = client.get("/api/v1/items/999")
    assert response.status_code == 404
