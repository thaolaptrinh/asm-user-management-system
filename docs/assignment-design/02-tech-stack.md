# 02 - CÔNG NGHỆ SỬ DỤNG

---

# PHASE 1: ASM CORE

## Tổng Quan

```
Backend:   FastAPI + SQLAlchemy + JWT + PyOTP
Frontend:  Next.js + TypeScript + Bun
Database:  MySQL
Deploy:    Docker Compose
```

## Xác Thực (Phase 1)
- **Phương pháp**: JWT (Access token only)
- **Thời gian Access Token**: 15 phút
- **Lưu trữ**: Stateless (không lưu token trong database)
- **Refresh**: Không có refresh token (login lại khi expires)

---

## Backend

| Thành phần | Công nghệ | Thư viện |
|------------|-----------|----------|
| Framework | FastAPI | fastapi, uvicorn |
| ORM | SQLAlchemy | sqlalchemy, asyncmy |
| Auth | JWT | python-jose, passlib |
| Validation | Pydantic | pydantic |
| Password Validation | passlib + regex | passlib |
| TOTP | PyOTP | pyotp |
| CORS | middleware | fastapi.middleware.cors |
| Migration | Alembic | alembic |

---

## Frontend

| Thành phần | Công nghệ |
|------------|-----------|
| Framework | Next.js |
| Language | TypeScript |
| Runtime | Bun |
| UI | TailwindCSS |

---

## Infrastructure

| Thành phần | Công nghệ |
|------------|-----------|
| Database | MySQL |
| Container | Docker / Docker Compose |

---

## Project Templates

### Backend
- Template: fastapi/full-stack-fastapi-template
- Ghi chú: Có docker sẵn, nhưng frontend là React -> cần replace thành Next.js

### Frontend
- Template: next.js/with-docker
- Ghi chú: Tham khảo cách viết Docker cho Next.js

---

## Tại Sao Chọn?

### FastAPI
- API-first, phù hợp với Next.js frontend
- Auto-generate OpenAPI/Swagger docs
- Pydantic tích hợp sẵn validation
- Performance cao (async)

### Bun
- Nhanh hơn Node.js
- Thường được sử dụng cho các dự án mới
- Đáng để thử, mặc dù không đảm bảo ổn định như Node

### SQLAlchemy
- Phổ biến nhất với FastAPI
- Hỗ trợ async
- Migration qua Alembic

### JWT
- Chuẩn cho REST API
- Dễ tích hợp với FastAPI

### PyOTP
- Thư viện chuẩn cho TOTP
- Tương thích Google Authenticator, Microsoft Authenticator

---

## Tóm Tắt

| Lớp | Stack |
|-----|-------|
| Backend | FastAPI + SQLAlchemy + JWT + PyOTP |
| Frontend | Next.js + TypeScript + Bun |
| Database | MySQL |
| Deploy | Docker Compose |

---

# PHASE 2: ENHANCEMENTS

## Backend Additional Libraries

| Thành phần | Công nghệ | Thư viện |
|------------|-----------|----------|
| Rate Limiting | SlowAPI | slowapi |

## Infrastructure Additional

| Thành phần | Công nghệ |
|------------|-----------|
| Redis (optional) | Rate limiting, caching |
| Nginx (optional) | Reverse proxy, load balancing |

---

## Phase 1 vs Phase 2 Stack

| Lớp | Phase 1 | Phase 2 (Additional) |
|-----|---------|----------------------|
| Backend | FastAPI + SQLAlchemy + JWT + PyOTP + CORS | SlowAPI |
| Database | MySQL | - |
| Infrastructure | Docker Compose | Redis (optional) + Nginx (optional) |
