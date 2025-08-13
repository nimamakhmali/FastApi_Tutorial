# بخش 7: استقرار (Deployment) FastAPI

## فهرست مطالب
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Server Configuration](#server-configuration)
- [Environment Management](#environment-management)
- [Monitoring & Logging](#monitoring--logging)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Load Balancing](#load-balancing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Performance Optimization](#performance-optimization)
- [Security Best Practices](#security-best-practices)

## Docker Deployment

### Basic Dockerfile
```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multi-stage Dockerfile
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/fastapi_tutorial
      - SECRET_KEY=your-secret-key-here
      - DEBUG=true
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=fastapi_tutorial
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### Docker Compose for Production
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/fastapi_tutorial
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=fastapi_tutorial
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Cloud Deployment

### AWS Deployment with ECS
```yaml
# task-definition.json
{
  "family": "fastapi-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "fastapi-app",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fastapi-app:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:password@rds-endpoint:5432/dbname"
        },
        {
          "name": "SECRET_KEY",
          "value": "your-secret-key"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastapi-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/fastapi-app:$COMMIT_SHA', '.']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/fastapi-app:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'fastapi-app'
      - '--image'
      - 'gcr.io/$PROJECT_ID/fastapi-app:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'DATABASE_URL=postgresql://user:password@host:5432/dbname,SECRET_KEY=your-secret-key'

images:
  - 'gcr.io/$PROJECT_ID/fastapi-app:$COMMIT_SHA'
```

### Azure Container Instances
```yaml
# azure-deploy.yml
apiVersion: 2019-12-01
location: eastus
name: fastapi-app
properties:
  containers:
  - name: fastapi-app
    properties:
      image: your-registry.azurecr.io/fastapi-app:latest
      ports:
      - port: 8000
      environmentVariables:
      - name: DATABASE_URL
        value: "postgresql://user:password@host:5432/dbname"
      - name: SECRET_KEY
        value: "your-secret-key"
      resources:
        requests:
          cpu: 1.0
          memoryInGB: 1.5
        limits:
          cpu: 2.0
          memoryInGB: 3.0
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 8000
```

## Server Configuration

### Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream fastapi_backend {
        server app:8000;
        server app:8001;
        server app:8002;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

        location / {
            proxy_pass http://fastapi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            proxy_pass http://fastapi_backend;
            access_log off;
        }
    }
}
```

### Gunicorn Configuration
```python
# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "fastapi-app"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
```

### Systemd Service
```ini
# /etc/systemd/system/fastapi-app.service
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=notify
User=appuser
Group=appuser
WorkingDirectory=/app
Environment=PATH=/app/venv/bin
ExecStart=/app/venv/bin/gunicorn app.main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Environment Management

### Environment Variables
```bash
# .env.production
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=false
ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Redis
REDIS_URL=redis://redis:6379

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO

# External APIs
PAYMENT_API_KEY=your-payment-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key
```

### Configuration Management
```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "FastAPI Tutorial"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Redis
    redis_url: Optional[str] = None
    
    # Email
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    
    # External APIs
    payment_api_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

settings = Settings()
```

## Monitoring & Logging

### Logging Configuration
```python
# app/logging.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from app.config import settings

def setup_logging():
    # Create logger
    logger = logging.getLogger("fastapi_app")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()
```

### Prometheus Metrics
```python
# app/monitoring.py
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### Health Check Endpoint
```python
# app/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
import redis

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Database health check
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis health check
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # External API health check
    try:
        # Check external APIs
        health_status["services"]["external_apis"] = "healthy"
    except Exception as e:
        health_status["services"]["external_apis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
```

## SSL/HTTPS Setup

### Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

### Self-Signed Certificate (Development)
```bash
# Generate private key
openssl genrsa -out key.pem 2048

# Generate certificate
openssl req -new -x509 -key key.pem -out cert.pem -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Combine for nginx
cat cert.pem key.pem > combined.pem
```

## Load Balancing

### HAProxy Configuration
```haproxy
# haproxy.cfg
global
    daemon
    maxconn 4096
    log 127.0.0.1 local0

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/combined.pem
    redirect scheme https if !{ ssl_fc }
    
    # Rate limiting
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
    
    default_backend http_back

backend http_back
    balance roundrobin
    option httpchk GET /health
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check
```

## CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

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

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: |
        docker build -t fastapi-app:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
        docker tag fastapi-app:${{ github.sha }} ${{ secrets.REGISTRY_URL }}/fastapi-app:${{ github.sha }}
        docker push ${{ secrets.REGISTRY_URL }}/fastapi-app:${{ github.sha }}
    
    - name: Deploy to production
      run: |
        # Deploy to your cloud platform
        # This could be kubectl, docker-compose, or cloud-specific commands
```

### GitLab CI/CD
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pip install pytest pytest-cov
    - pytest --cov=app --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:latest

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - curl -X POST $DEPLOY_WEBHOOK_URL
  only:
    - main
```

## Performance Optimization

### Database Optimization
```python
# app/database/optimization.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

def optimize_database():
    """Apply database optimizations"""
    
    # Connection pooling
    engine = create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.debug
    )
    
    # Query optimization
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        if total > 1.0:  # Log slow queries
            logger.warning(f"Slow query ({total:.2f}s): {statement}")
    
    return engine
```

### Caching Strategy
```python
# app/cache/strategy.py
import redis
from functools import wraps
import json
import hashlib

redis_client = redis.from_url(settings.redis_url)

def cache_result(expire_time: int = 300, key_prefix: str = ""):
    """Cache decorator with custom key generation"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
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

def invalidate_cache(pattern: str):
    """Invalidate cache by pattern"""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
```

## Security Best Practices

### Security Headers
```python
# app/security/headers.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def add_security_middleware(app: FastAPI):
    """Add security middleware to FastAPI app"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["your-domain.com", "www.your-domain.com"]
    )
    
    # Custom security headers
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        
        return response
```

### Rate Limiting
```python
# app/security/rate_limiting.py
from fastapi import HTTPException, Request
import time
from collections import defaultdict

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

def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host
    
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )
    
    return call_next(request)
```

## مثال کامل

```python
# deployment_example.py
from fastapi import FastAPI
from app.config import settings
from app.security.headers import add_security_middleware
from app.monitoring import metrics_middleware
from app.health import router as health_router

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

# Add middleware
add_security_middleware(app)
app.middleware("http")(metrics_middleware)

# Include routers
app.include_router(health_router, prefix="/health", tags=["health"])

# Production configuration
if settings.is_production:
    import uvicorn
    
    if __name__ == "__main__":
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            workers=4,
            log_level=settings.log_level.lower()
        )
```

## نکات مهم

1. **Security First**: همیشه امنیت را در اولویت قرار دهید
2. **Monitoring**: سیستم‌های monitoring و logging را راه‌اندازی کنید
3. **Backup**: استراتژی backup مناسب داشته باشید
4. **Scaling**: برای مقیاس‌پذیری برنامه‌ریزی کنید
5. **Testing**: قبل از deployment تست‌های کامل انجام دهید
6. **Documentation**: مستندات deployment را به‌روز نگه دارید
7. **Rollback Plan**: برنامه rollback برای مواقع اضطراری داشته باشید
