# HỆ THỐNG QUẢN LÝ NGƯỜI DÙNG VỚI TOTP 2FA

**Trạng thái:** Sẵn sàng nộp ASM  
**Phiên bản:** 1.0  
**Cập nhật:** 2026-03-05

## Tổng quan

Hệ thống quản lý người dùng với xác thực hai yếu tố (2FA) sử dụng TOTP (Mật khẩu một lần dựa trên thời gian).

## Quick Start

```bash
docker-compose up --build
```

**Truy cập:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Mục Lục

| STT | Tài liệu | Mô tả |
|-----|----------|-------|
| 00 | [Technical Assignment](./00-technical_assignment_vi.md) | Đặc tả bài tập kỹ thuật |
| 01 | [Functional Requirements](./01-functional-requirements.md) | Yêu cầu chức năng (Phase 1 + Phase 2) |
| 02 | [Tech Stack](./02-tech-stack.md) | Công nghệ sử dụng |
| 03 | [Database Design](./03-database-design.md) | Thiết kế database |
| 04 | [API Design](./04-api-design.md) | Thiết kế API (Phase 1 + Phase 2) |
| - | [Database Schema](./dbdigram.dbml) | Sơ đồ DBML database |

---

## Tổng Quan Dự Án

### Lộ Trình

#### Phase 1: ASM Core (Phải Hoàn Thành)
- Đăng ký người dùng
- Đăng nhập với 2FA (Email/Password + TOTP)
- Quản lý người dùng (Xem, Xóa, Thông tin cá nhân)
- Thiết lập TOTP (3 bước chuẩn)
- Chức năng Admin (Super Admin)
- Ghi log (backend)

#### Phase 2: Mở Rộng (Công Việc Tương Lai)
- Đổi mật khẩu (Tự phục vụ)
- Quên mật khẩu (Gửi link reset qua email)
- JWT Refresh Token (Quản lý token)
- Giới hạn tốc độ & Security Headers
- API Audit Logs (Xem log hệ thống)
- API Mã khôi phục TOTP

---

## Chức Năng

- Đăng ký người dùng với email
- Đăng nhập với 2FA (Password + TOTP)
- Quản lý người dùng (Chỉ Admin)
- Phân quyền (Super Admin)
- Thiết lập TOTP (3 bước: enroll -> challenge -> verify)
- Ghi log hoạt động

## Công Nghệ Sử Dụng

| Lớp | Công nghệ |
|------|-----------|
| Frontend | Next.js + TypeScript + Bun |
| Backend | FastAPI + SQLAlchemy + JWT + PyOTP |
| Database | MySQL |
| Container | Docker Compose |

## Yêu Cầu

- Docker & Docker Compose
- Bun (cho frontend)

---

## Cấu Trúc Dự Án

```
docs/
    README.md
    00-technical_assignment_vi.md
    01-functional-requirements.md
    02-tech-stack.md
    03-database-design.md
    04-api-design.md
    dbdigram.dbml

frontend/
    (Ứng dụng Next.js)

backend/
    (Ứng dụng FastAPI)

docker-compose.yml
.env.example
```

---

## Các Tài Liệu Liên Quan

- [Database Schema](./dbdigram.dbml)

---

## Kiểm Tra Nộp ASM

**Tài liệu:**
- [x] README.md - Tổng quan dự án
- [x] Functional Requirements - Yêu cầu chức năng
- [x] Tech Stack - Công nghệ sử dụng
- [x] Database Design - Thiết kế database
- [x] API Design - Các endpoint API

**Môi trường:**
- [x] docker-compose.yml - Cấu hình đa container
- [x] .env.example - Mẫu biến môi trường

**Tài liệu API:**
- [x] Swagger/OpenAPI (tự động tạo bởi FastAPI)

**Sẵn sàng nộp ASM!**
