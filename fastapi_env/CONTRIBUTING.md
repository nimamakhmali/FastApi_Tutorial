# راهنمای مشارکت 🤝

از مشارکت شما در این پروژه استقبال می‌کنیم! این فایل راهنمای مشارکت در پروژه FastAPI Tutorial است.

## نحوه مشارکت

### 1. Fork کردن پروژه

ابتدا پروژه را fork کنید و سپس clone کنید:

```bash
git clone https://github.com/YOUR_USERNAME/fastapi_tutorial.git
cd fastapi_tutorial
```

### 2. ایجاد Branch جدید

برای هر تغییر، یک branch جدید ایجاد کنید:

```bash
git checkout -b feature/your-feature-name
# یا
git checkout -b fix/your-fix-name
```

### 3. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### 4. راه‌اندازی محیط توسعه

```bash
# کپی کردن فایل تنظیمات
cp env.example .env

# ویرایش فایل .env با تنظیمات مناسب
```

### 5. اجرای تست‌ها

قبل از ارسال تغییرات، تست‌ها را اجرا کنید:

```bash
pytest
```

### 6. بررسی کد

کد خود را بررسی کنید:

```bash
# فرمت کردن کد
black app tests
isort app tests

# بررسی کیفیت کد
flake8 app tests
```

### 7. Commit و Push

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

### 8. ایجاد Pull Request

در GitHub، یک Pull Request ایجاد کنید.

## استانداردهای کدنویسی

### Python

- از Python 3.8+ استفاده کنید
- از type hints استفاده کنید
- از docstrings استفاده کنید
- از Black برای فرمت کردن کد استفاده کنید
- از isort برای مرتب کردن imports استفاده کنید

### FastAPI

- از Pydantic models برای validation استفاده کنید
- از dependency injection استفاده کنید
- از proper error handling استفاده کنید
- از async/await استفاده کنید

### تست‌ها

- برای هر endpoint تست بنویسید
- از pytest استفاده کنید
- تست‌ها را در پوشه `tests/` قرار دهید
- نام فایل‌های تست را با `test_` شروع کنید

## ساختار Commit Messages

از [Conventional Commits](https://www.conventionalcommits.org/) استفاده کنید:

```
type(scope): description

feat: add user authentication
fix: resolve database connection issue
docs: update README
style: format code with black
refactor: improve error handling
test: add unit tests for user model
chore: update dependencies
```

## انواع تغییرات

- `feat`: ویژگی جدید
- `fix`: رفع باگ
- `docs`: تغییرات مستندات
- `style`: تغییرات فرمت
- `refactor`: بازنویسی کد
- `test`: اضافه کردن یا تغییر تست‌ها
- `chore`: تغییرات ابزارها و تنظیمات

## بررسی Pull Request

قبل از merge شدن، Pull Request باید:

1. تمام تست‌ها را پاس کند
2. کد quality checks را پاس کند
3. مستندات را به‌روزرسانی کند
4. توسط حداقل یک maintainer بررسی شود

## گزارش باگ

برای گزارش باگ:

1. از template باگ استفاده کنید
2. مراحل تولید باگ را توضیح دهید
3. رفتار مورد انتظار را توضیح دهید
4. اطلاعات سیستم را ارائه دهید

## درخواست ویژگی

برای درخواست ویژگی جدید:

1. از template feature request استفاده کنید
2. مشکل را توضیح دهید
3. راه‌حل پیشنهادی را ارائه دهید
4. مزایای آن را توضیح دهید

## سوالات

اگر سوالی دارید:

1. ابتدا Issues را بررسی کنید
2. اگر پاسخ پیدا نکردید، Issue جدید ایجاد کنید
3. از Discussions استفاده کنید

## لایسنس

با مشارکت در این پروژه، شما موافقت می‌کنید که کد شما تحت لایسنس MIT منتشر شود.

## تشکر

از مشارکت شما در بهبود این پروژه آموزشی تشکر می‌کنیم! 🙏
