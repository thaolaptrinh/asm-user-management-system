# 04 - THIẾT KẾT API

Base URL: /api/v1

---

# PHASE 1: ASM CORE (12 ENDPOINTS)

## Tóm Tắt

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| **Auth** | | | |
| POST | /auth/register | Đăng ký user mới | No |
| POST | /auth/login | Đăng nhập (giai đoạn 1) | No |
| POST | /auth/totp/verify | Xác thực TOTP (giai đoạn 2) | No |
| POST | /auth/logout | Đăng xuất | Yes |
| **TOTP** | | | |
| GET | /auth/totp/status | Kiểm tra TOTP đã enable chưa | Yes |
| POST | /auth/totp/enroll | Enroll TOTP - Generate secret + QR | Yes |
| POST | /auth/totp/challenge | Tạo challenge (in-memory, có timeout) | Yes |
| POST | /auth/totp/verify | Verify TOTP code | Yes |
| **User** | | | |
| GET | /users | Danh sách user | Yes (Admin) |
| POST | /users | Tạo user mới | Yes (Admin) |
| DELETE | /users/{id} | Xóa user | Yes (Admin) |
| GET | /users/me | Thông tin user hiện tại | Yes |

---

## Flow

### Register + Login với TOTP

\`\`\`
1. Register -> POST /auth/register
2. Login -> POST /auth/login -> temp_token
3. Check TOTP status -> GET /auth/totp/status
   +- Đã enable -> Challenge + Verify -> access_token
   +- Chưa enable -> Enroll -> Challenge -> Verify -> access_token
\`\`\`

### Enroll TOTP (3-step chuẩn)

\`\`\`
Step 1: POST /auth/totp/enroll
        -> Generate secret + QR code

Step 2: POST /auth/totp/challenge
        -> Tạo challenge (in-memory, timeout 60s)

Step 3: POST /auth/totp/verify
        -> Verify code với challenge -> TOTP enabled
\`\`\`

---

## Chi Tiết

### Auth

#### POST /auth/register
Đăng ký user mới.

**Auth:** No

**Request:**
\`\`\`json
{
  "name": "string",
  "email": "user@example.com",
  "password": "string"
}
\`\`\`

**Response (201):**
\`\`\`json
{
  "id": "uuid",
  "name": "string",
  "email": "user@example.com",
  "is_super_admin": false,
  "created_at": "timestamp"
}
\`\`\`

---

#### POST /auth/login
Đăng nhập - Giai đoạn 1 (Email + Password).

**Auth:** No

**Request:**
\`\`\`json
{
  "email": "user@example.com",
  "password": "string"
}
\`\`\`

**Response (200):**
\`\`\`json
{
  "temp_token": "string",
  "message": "Vui lòng nhập mã TOTP"
}
\`\`\`

**Error (401):** Sai email/password

---

#### POST /auth/totp/verify

Endpoint này dùng cho **hai luồng**. Phân biệt bằng body: có `temp_token` = verify khi đăng nhập; có `challenge_id` = verify khi enroll TOTP.

---

**A. Xác thực TOTP khi đăng nhập (giai đoạn 2)**

**Auth:** No (gửi temp_token trong body)

**Request:**
\`\`\`json
{
  "temp_token": "string",
  "totp_code": "123456"
}
\`\`\`

**Response (200):**
\`\`\`json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "name": "string",
    "email": "user@example.com",
    "is_super_admin": false
  }
}
\`\`\`

**Note:** Access token 15 phút; Phase 1 không có refresh token. Khi token hết hạn, user phải login lại.

**Error (401):** TOTP không hợp lệ hoặc temp_token hết hạn

---

**B. Verify TOTP khi enroll (Step 3)**

**Auth:** Yes (Bearer) hoặc dùng challenge_id từ Step 2

**Request:**
\`\`\`json
{
  "challenge_id": "uuid",
  "code": "123456"
}
\`\`\`

**Response (200):**
\`\`\`json
{
  "message": "TOTP đã được kích hoạt",
  "is_enabled": true
}
\`\`\`

**Error (401):** Mã TOTP không hợp lệ hoặc challenge expired

---

#### POST /auth/logout
Đăng xuất.

**Auth:** Yes

**Response (200):**
\`\`\`json
{
  "message": "Đăng xuất thành công"
}
\`\`\`

---

### TOTP

#### GET /auth/totp/status
Kiểm tra user đã enable TOTP chưa.

**Auth:** Yes

**Response (200):**
\`\`\`json
{
  "is_enabled": false,
  "message": "TOTP chưa được kích hoạt"
}
\`\`\`

---

#### POST /auth/totp/enroll
Enroll TOTP - Step 1: Generate secret + QR code.

**Auth:** Yes

**Response (200):**
\`\`\`json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "otpauth_url": "otpauth://totp/App:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=App"
}
\`\`\`

---

#### POST /auth/totp/challenge
Enroll TOTP - Step 2: Tạo challenge.

**Auth:** Yes

**Response (200):**
\`\`\`json
{
  "challenge_id": "uuid",
  "expires_in": 60
}
\`\`\`

**Note:** Challenge lưu in-memory, có timeout 60 giây.

---

_(Xem mục POST /auth/totp/verify ở trên — luồng B dùng challenge_id + code.)_

---

### User

#### GET /users
Lấy danh sách user (có phân trang). Chỉ trả về user chưa bị xóa (`deleted_at IS NULL`).

**Auth:** Yes (Admin)
**Query:** ?page=1&limit=10

**Response (200):**
\`\`\`json
{
  "users": [
    {
      "id": "uuid",
      "name": "string",
      "email": "user@example.com",
      "is_active": true,
      "is_super_admin": false,
      "created_at": "timestamp"
    }
  ],
  "total": 1
}
\`\`\`

---

#### POST /users
Tạo user mới (Admin tạo cho user).

**Auth:** Yes (Admin)

**Request:**
\`\`\`json
{
  "name": "string",
  "email": "newuser@example.com",
  "password": "string"
}
\`\`\`

**Response (201):**
\`\`\`json
{
  "id": "uuid",
  "name": "string",
  "email": "newuser@example.com",
  "is_super_admin": false,
  "created_at": "timestamp"
}
\`\`\`

---

#### DELETE /users/{id}
Xóa user (soft delete: set `deleted_at`, không xóa row). User đã soft-deleted không xuất hiện trong GET /users.

**Auth:** Yes (Admin)

**Response (204):** No Content

**Error (404):** User không tồn tại

---

#### GET /users/me
Lấy thông tin user hiện tại.

**Auth:** Yes

**Response (200):**
\`\`\`json
{
  "id": "uuid",
  "name": "string",
  "email": "user@example.com",
  "is_active": true,
  "is_super_admin": false,
  "created_at": "timestamp"
}
\`\`\`

---

## Authentication (Phase 1)

### JWT Configuration

Phase 1 sử dụng JWT access token (không có refresh token):

| Setting | Value |
|---------|-------|
| Algorithm | HS256 (HMAC-SHA256) |
| Secret Key | Environment variable (JWT_SECRET) |
| Access Token Lifetime | 15 phút |
| Temp Token Lifetime | 2 phút (sau POST /auth/login, dùng để verify TOTP) |
| Token Type | Bearer |
| Storage | Stateless (không lưu database storage cho tokens) |

### Token Structure

\`\`\`json
{
  "sub": "user_id",
  "exp": 1741265400,
  "iat": 1741261800,
  "iss": "https://api.example.com",
  "aud": "https://example.com"
}
\`\`\`

### Usage

**Request (Client):**
\`\`\`http
GET /users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
\`\`\`

**Response:**
- 200 OK: Token valid, return data
- 401 Unauthorized: Token invalid or expired
- 422 Unprocessable: Token format invalid

### Token Expiration Handling

Khi access token expires (15 phút):

**Phase 1:**
- Client nhận 401 Unauthorized
- User phải login lại (email/password + TOTP)
- Nhận access token mới

**Phase 2:**
- Client dùng refresh token để lấy access token mới
- KHÔNG phải login lại

---

## Security Configuration

### Yêu Cầu Mật Khẩu

| Yêu cầu | Giá trị |
|-------------|-------|
| Độ dài | 8-128 ký tự |
| Bắt buộc | Ít nhất 1 chữ hoa, 1 chữ thường, 1 số |
| Ký tự đặc biệt | Không yêu cầu |
| Blacklist | Check breached passwords |
| Thay đổi định kỳ | Không yêu cầu |

### CORS Configuration

| Setting | Value |
|---------|-------|
| Allowed Origins | http://localhost:3000 (frontend dev) |
| Allowed Methods | GET, POST, PUT, DELETE, OPTIONS |
| Allowed Headers | Authorization, Content-Type |
| Credentials | Supported |
| Preflight | Cached 1 giờ |

---

# PHASE 2: ENHANCEMENTS (ADDITIONAL ENDPOINTS)

## Authentication Changes (Phase 2)

Phase 2 thêm JWT refresh token capability:

### JWT Configuration (Phase 2)

| Token Type | Lifetime | Purpose |
|------------|----------|---------|
| Access Token | 10 phút | API access |
| Refresh Token | 30 ngày | Refresh access token |

### Token Rotation

Phase 2 implements refresh token rotation:

1. Client presents refresh_token_1
2. Server validates refresh_token_1
3. Server issues access_token + refresh_token_2
4. Server marks refresh_token_1 as revoked
5. Client stores refresh_token_2, discards refresh_token_1

### Benefits

- **Better UX**: User không phải login lại mỗi 10 phút
- **Better Security**: Token rotation detect stolen tokens
- **Revocation**: Admin có thể revoke specific tokens

## Overview

Phase 2 bổ sung các endpoint sau để hoàn chỉnh hệ thống:

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| **User** | | |
| PUT | /users/me/password | Đổi mật khẩu |
| **Auth** | | |
| POST | /auth/forgot-password | Request reset password |
| POST | /auth/reset-password | Reset password với token |
| POST | /auth/refresh | Refresh access token |
| **Security** | | |
| (Rate Limiting & Headers) | | Security enhancements |
| **Audit** | | |
| GET | /audit-logs | Xem audit logs (Admin) |
| **TOTP Recovery** (Optional) | | |
| GET | /auth/totp/recovery | Xem recovery codes |
| POST | /auth/totp/recovery | Generate recovery codes |
| POST | /auth/totp/recovery/verify | Verify recovery code |

---

## Auth

### POST /auth/refresh
Refresh access token bằng refresh token.

**Auth:** No (dùng refresh_token)

**Request:**
\`\`\`json
{
  "refresh_token": "string"
}
\`\`\`

**Response (200):**
\`\`\`json
{
  "access_token": "string",
  "refresh_token": "string",
  "expires_in": 600
}
\`\`\`

**Error (401):** Invalid or expired refresh token

---

### POST /auth/forgot-password
Request reset password qua email.

**Auth:** No

**Request:**
\`\`\`json
{
  "email": "user@example.com"
}
\`\`\`

**Response (200):**
\`\`\`json
{
  "message": "Nếu email tồn tại, bạn sẽ nhận được link reset password"
}
\`\`\`

**Note:**
- Luôn trả về 200 để avoid email enumeration
- Gửi email với reset link: \`http://localhost:3000/reset-password?token=xxx\`
- Token expires 30 phút (lưu \`expires_at\` trong DB)
- Token mới sẽ **REPLACE** token cũ (user_id PK, 1 token per user)
- Rate limiting: 3 requests / 15 phút per email

---

### POST /auth/reset-password
Reset password với token từ email.

**Auth:** No

**Request:**
\`\`\`json
{
  "token": "reset_token_string",
  "new_password": "NewSecurePass123"
}
\`\`\`

**Response (204):** No Content

**Error (400):** Invalid or expired token

**Note:**
- Token single-use (DELETE row sau khi reset)
- Check expiry từ DB: \`expires_at < NOW()\`
- Password phải theo Password Requirements
- Auto-login sau khi reset (optional)

---

## User

### PUT /users/me/password
User tự đổi mật khẩu.

**Auth:** Yes

**Request:**
\`\`\`json
{
  "current_password": "string",
  "new_password": "string"
}
\`\`\`

**Response (204):** No Content

**Error (401):** Current password incorrect

---

## Audit Logs

### GET /audit-logs
Xem audit logs (Admin only).

**Auth:** Yes (Admin)
**Query:** ?page=1&limit=20&user_id=uuid&action=LOGIN_SUCCESS&from=2026-03-01&to=2026-03-05

**Response (200):**
\`\`\`json
{
  "logs": [
    {
      "id": "evt_1a2b3c",
      "timestamp": "2026-03-05T10:30:00Z",
      "event_type": "auth.login.success",
      "user_id": "usr_123",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "status": "success"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
\`\`\`

---

## Security Configuration (Phase 2)

### JWT Token Lifetimes

| Token Type | Lifetime | Purpose |
|-------------|----------|---------|
| Access Token | 10 phút | API access |
| Refresh Token | 30 ngày | Refresh access token |
| Temp Token | 2 phút | TOTP verify flow |

### Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Auth endpoints | 10 requests | 15 phút |
| TOTP endpoints | 5 requests | 1 phút |
| API endpoints | 100 requests | 15 phút |

### Security Headers

\`\`\`
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
\`\`\`

---

## Appendix: Phase 1 vs Phase 2 Comparison

| Category | Phase 1 | Phase 2 |
|----------|---------|---------|
| Endpoints | 12 | 17-20 |
| Database Tables | 4 | 6 |
| **JWT Access Token** | [OK] 15 phút | [OK] 10 phút |
| **JWT Refresh Token** | [X] No | [OK] 30 ngày |
| Token Expiry Handling | Login lại | Refresh token |
| Đổi Mật Khẩu | [X] No | [OK] Yes |
| Quên Mật Khẩu | [X] No | [OK] Yes |
| Audit API | [X] No | [OK] Yes |
| Rate Limiting | [X] No | [OK] Yes |
| Security Headers | [X] No | [OK] Yes |
| Recovery Codes | Table only | [OK] Full API |

### JWT Authentication Flow Comparison

**Phase 1:**
\`\`\`
Login → TOTP Verify → Access Token (15phút)
       ↓
   Token expires
       ↓
Login lại (email/password + TOTP)
\`\`\`

**Phase 2:**
\`\`\`
Login → TOTP Verify → Access Token (10phút) + Refresh Token (30 ngày)
       ↓
   Access token expires
       ↓
Refresh với Refresh Token → Access Token mới
       ↓
   Refresh token expires
       ↓
Login lại (email/password + TOTP)
\`\`\`
