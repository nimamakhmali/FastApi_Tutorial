# FastAPI Tutorial Makefile
# دستورات مفید برای توسعه

.PHONY: install run test lint format clean docs

# نصب وابستگی‌ها
install:
	pip install -r requirements.txt

# اجرای برنامه
run:
	python run.py

# اجرای برنامه با uvicorn
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# اجرای تست‌ها
test:
	pytest

# اجرای تست‌ها با coverage
test-cov:
	pytest --cov=app --cov-report=html

# بررسی کد
lint:
	flake8 app tests
	black --check app tests
	isort --check-only app tests

# فرمت کردن کد
format:
	black app tests
	isort app tests

# پاک کردن فایل‌های موقت
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# ایجاد مستندات
docs:
	mkdocs serve

# نصب pre-commit hooks
setup-hooks:
	pre-commit install

# کمک
help:
	@echo "دستورات موجود:"
	@echo "  install     - نصب وابستگی‌ها"
	@echo "  run         - اجرای برنامه"
	@echo "  dev         - اجرای برنامه در حالت توسعه"
	@echo "  test        - اجرای تست‌ها"
	@echo "  test-cov    - اجرای تست‌ها با coverage"
	@echo "  lint        - بررسی کد"
	@echo "  format      - فرمت کردن کد"
	@echo "  clean       - پاک کردن فایل‌های موقت"
	@echo "  docs        - اجرای مستندات"
	@echo "  setup-hooks - نصب pre-commit hooks"
	@echo "  help        - نمایش این پیام"
