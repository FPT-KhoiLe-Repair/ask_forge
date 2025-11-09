🧠 Giới thiệu dự án

AskForge Backend là hệ thống lõi cho nền tảng học tập AI hỗ trợ tạo câu hỏi thông minh (Question Generation) và truy xuất tri thức (Retrieval-Augmented Generation – RAG) từ tài liệu PDF.
Mục tiêu là xây dựng một backend modular, mở rộng linh hoạt, dễ tích hợp với frontend (Next.js) và các mô hình AI (Gemini, Qwen, v.v.).


# 🐳 Hướng dẫn Docker cho Ask Forge

## 📋 Yêu cầu hệ thống

- Docker Engine 20.10+
- Docker Compose 2.0+
- Ít nhất 8GB RAM (khuyến nghị 16GB nếu chạy HuggingFace models)
- 20GB dung lượng ổ cứng trống

## 🚀 Cài đặt nhanh

### Bước 1: Clone repository và setup environment

```bash
# Clone dự án
git clone https://github.com/FPT-KhoiLe-Repair/ask_forge.git
cd ask_forge

# Tạo file .env từ template
cp env.example .env

# Chỉnh sửa .env và thêm GEMINI_API_KEY của bạn
nano .env  # hoặc vim/code .env
```

# **⚠️ QUAN TRỌNG**: Bạn PHẢI thêm `GEMINI_API_KEY` vào file `.env`

### Bước 2: Tạo các file .dockerignore

```bash
# Backend .dockerignore
cat > backend/.dockerignore << 'EOF'
__pycache__
*.pyc
*.pyo
.Python
venv/
.pytest_cache/
*.log
.git
node_modules/
EOF

# Frontend .dockerignore
cat > frontend/.dockerignore << 'EOF'
.next/
node_modules/
.git
*.md
.DS_Store
EOF
```

### Bước 3: Build và chạy

```bash
# Build tất cả services
docker-compose build

# Chạy ứng dụng
docker-compose up -d

# Xem logs
docker-compose logs -f
```

### Bước 4: Truy cập ứng dụng

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics

## 📁 Cấu trúc dự án

```
ask-forge/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── ...
├── docker-compose.yml
├── .env
└── .env.example
```

## ⚙️ Cấu hình

### Backend Environment Variables

Chỉnh sửa trong file `.env`:

```bash
# API Keys (BẮT BUỘC)
GEMINI_API_KEY=your-actual-api-key

# Model Settings
GEMINI_MODEL_NAME=gemini-2.5-flash
HF_QUESTION_GENERATOR_CKPT=Qwen/qwen-security-final-question-reformatted

# Performance
HF_PRELOAD_AT_STARTUP=True  # True = tải model khi khởi động
HF_DEVICE_MAP=auto          # auto/cuda/cpu

# Storage
CHROMA_PERSIST_DIR=.chroma
PAGES_JSON_DIR=data/user_db
```

### Sử dụng Redis Queue (Optional)

Nếu muốn dùng Redis thay vì AsyncIO queue:

1. Uncomment Redis service trong `docker-compose.yml`
2. Thay đổi trong `backend/app/core/app_state.py`:

```python
# Thay đổi từ AsyncBackgroundQueue
from ask_forge.backend.app.services.queue.redis_queue import BackgroundQueueUsingRedis

self.bq = BackgroundQueueUsingRedis(redis_url=settings.REDIS_URL)
```

## 🛠️ Lệnh Docker thường dùng

### Quản lý containers

```bash
# Khởi động
docker-compose up -d

# Dừng
docker-compose down

# Dừng và xóa volumes
docker-compose down -v

# Restart một service cụ thể
docker-compose restart backend
docker-compose restart frontend

# Xem logs
docker-compose logs -f                    # Tất cả services
docker-compose logs -f backend            # Chỉ backend
docker-compose logs -f --tail=100 backend # 100 dòng cuối
```

### Build và rebuild

```bash
# Build lại tất cả
docker-compose build

# Build lại một service cụ thể
docker-compose build backend

# Build không cache
docker-compose build --no-cache

# Build và chạy
docker-compose up -d --build
```

### Debug và troubleshooting

```bash
# Vào container backend
docker-compose exec backend bash

# Vào container frontend
docker-compose exec frontend sh

# Kiểm tra health status
docker-compose ps

# Xem resource usage
docker stats
```

## 🐛 Xử lý sự cố

### Backend không khởi động

```bash
# Check logs
docker-compose logs backend

# Kiểm tra biến môi trường
docker-compose exec backend env | grep GEMINI

# Restart backend
docker-compose restart backend
```

### Frontend không kết nối được backend

Kiểm tra `NEXT_PUBLIC_API_BASE` trong frontend:

```bash
# Nếu chạy trên production, thay đổi thành domain thực
NEXT_PUBLIC_API_BASE=https://your-domain.com
```

### ChromaDB lỗi

```bash
# Xóa dữ liệu ChromaDB và rebuild
docker-compose down -v
rm -rf backend/.chroma
docker-compose up -d
```

### Out of memory

```bash
# Giảm model preload
HF_PRELOAD_AT_STARTUP=False

# Hoặc thêm memory limit trong docker-compose.yml
services:
  backend:
    mem_limit: 4g
```

## 🔒 Production deployment

### Sử dụng với Nginx reverse proxy

```nginx
# nginx.conf
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Environment cho production

```bash
# .env.production
DEBUG=False
GEMINI_API_KEY=your-production-key
CORS_ORIGINS=https://your-domain.com
NEXT_PUBLIC_API_BASE=https://your-domain.com
```

### SSL với Let's Encrypt

```bash
# Sử dụng certbot
docker run -it --rm --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  certbot/certbot certonly --standalone \
  -d your-domain.com
```

## 📊 Monitoring

### Prometheus metrics

Backend expose metrics tại `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Health checks

```bash
# Backend health
curl http://localhost:8000/

# Frontend health
curl http://localhost:3000/
```

## 🔄 Cập nhật ứng dụng

```bash
# Pull code mới
git pull origin main

# Rebuild và restart
docker-compose down
docker-compose build
docker-compose up -d

# Hoặc rolling update
docker-compose up -d --build
```

## 💾 Backup và Restore

### Backup dữ liệu

```bash
# Backup ChromaDB
tar -czf chroma-backup-$(date +%Y%m%d).tar.gz backend/.chroma

# Backup user data
tar -czf data-backup-$(date +%Y%m%d).tar.gz backend/data
```

### Restore

```bash
# Restore ChromaDB
tar -xzf chroma-backup-20241108.tar.gz -C backend/

# Restart backend
docker-compose restart backend
```

## ⚡ Performance tuning

### Tối ưu cho GPU

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Tối ưu cho RAM thấp

```bash
# .env
HF_PRELOAD_AT_STARTUP=False
HF_LOW_CPU_MEM=True
HF_DEVICE_MAP=cpu
```

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy:

1. Check logs: `docker-compose logs -f`
2. Kiểm tra health: `docker-compose ps`
3. Xem issues trên GitHub
4. Tạo issue mới với logs đầy đủ

---

Happy coding! 🚀
