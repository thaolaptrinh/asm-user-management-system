# 03 - THIẾT KẾT DATABASE

---

# PHASE 1: ASM CORE (4 TABLES)

## Tables

### users
Lưu thông tin user của hệ thống (email, password, role).

### totp_secrets
Lưu secret key TOTP của user để generate mã xác thực.

### totp_recovery_codes
Lưu mã khôi phục dự phòng khi user mất thiết bị TOTP (table only, optional API).

### audit_logs
Ghi lại các hoạt động (đăng nhập, thao tác) trong hệ thống (backend logs only).

**Lưu ý:** Phase 1 KHÔNG dùng refresh_tokens table. JWT access tokens chỉ valid 15 phút, user phải login lại khi expires.

---

## Database Diagram

Ref: docs/dbdigram.dbml

---

## Columns

### users

| Column | Type | Mô tả |
|--------|------|-------|
| id | char(36) | UUID, PK |
| name | varchar(100) | Tên user |
| email | varchar(255) | Email (unique) |
| password_hash | varchar(255) | Mật khẩu hash |
| is_active | boolean | User có active không. Khi tạo user (đăng ký hoặc Admin tạo): set true |
| is_super_admin | boolean | Có phải super admin không |
| created_at | timestamp | Ngày tạo |
| updated_at | timestamp | Ngày cập nhật |
| deleted_at | timestamp | Soft delete (set khi DELETE /users/{id}, không xóa row) |

### totp_secrets

Row được tạo khi user gọi **POST /auth/totp/enroll** (Step 1), không tạo lúc đăng ký.

| Column | Type | Mô tả |
|--------|------|-------|
| user_id | char(36) | PK, FK -> users.id (1-1 relationship) |
| secret | varchar(64) | Base32 secret key |
| algorithm | varchar(10) | SHA1/SHA256/SHA512 |
| digits | tinyint | 6 hoặc 8 |
| period | tinyint | Thời gian hiệu lực (giây) |
| is_verified | boolean | Đã verify TOTP chưa |
| last_used_at | timestamp | Lần dùng cuối |
| created_at | timestamp | Ngày tạo |
| updated_at | timestamp | Ngày cập nhật |

### totp_recovery_codes

| Column | Type | Mô tả |
|--------|------|-------|
| user_id | char(36) | PK (part of composite PK), FK -> users.id |
| code_hash | char(60) | PK (part of composite PK), Bcrypt hash của recovery code |
| used_at | timestamp | Đã dùng chưa (null = chưa) |
| created_at | timestamp | Ngày tạo |

### audit_logs

| Column | Type | Mô tả |
|--------|------|-------|
| id | bigint | PK, auto increment |
| user_id | char(36) | FK -> users.id (null được) |
| action | varchar(100) | Loại action |
| target_type | varchar(50) | Table bị ảnh hưởng |
| target_id | char(36) | ID bị ảnh hưởng |
| ip_address | varchar(45) | IP |
| user_agent | varchar(512) | Browser/Device |
| status | varchar(20) | SUCCESS/FAILED |
| meta | json | Thông tin thêm |
| created_at | timestamp | Ngày tạo |

---

## Audit log – Các action Phase 1

Backend ghi vào `audit_logs` với các giá trị `action` sau (tham khảo, có thể mở rộng):

| action | Mô tả |
|--------|-------|
| REGISTER | User đăng ký thành công |
| LOGIN_SUCCESS | Đăng nhập thành công (sau verify TOTP) |
| LOGIN_FAILED | Sai email/password |
| TOTP_VERIFY_SUCCESS | Verify TOTP thành công (login hoặc enroll) |
| TOTP_VERIFY_FAILED | Mã TOTP sai hoặc hết hạn |
| TOTP_ENROLLED | User hoàn thành enroll TOTP |
| USER_CREATED | Admin tạo user |
| USER_DELETED | Admin soft-delete user |

---

# PHASE 2: ENHANCEMENTS (ADDITIONAL TABLES)

## refresh_tokens (NEW)

Lưu refresh tokens để refresh access tokens mà không cần login lại.

### refresh_tokens

| Column | Type | Mô tả |
|--------|------|-------|
| id | char(36) | UUID, PK |
| user_id | char(36) | FK -> users.id |
| token_hash | varchar(255) | SHA256 hash của refresh token |
| expires_at | timestamp | Thời gian hết hạn (30 ngày) |
| revoked_at | timestamp | Thời gian revoke (null = active) |
| created_at | timestamp | Ngày tạo |
| last_used_at | timestamp | Lần dùng cuối để refresh |
| device_info | json | Thông tin device (Browser, OS, IP) |

---

## password_reset_tokens (NEW)

Lưu tokens để reset password khi user quên mật khẩu.

### password_reset_tokens

| Column | Type | Mô tả |
|--------|------|-------|
| user_id | char(36) | PK, FK -> users.id (1 token per user) |
| token_hash | varchar(255) | SHA256 hash của reset token |
| expires_at | timestamp | Thời gian hết hạn (30 phút) |

---

## Relationships

### Phase 1 Relationships

| Relationship | Type |
|--------------|------|
| users -> totp_secrets | 1-1 |
| users -> totp_recovery_codes | 1-N |
| users -> audit_logs | 1-N |

### Phase 2 Relationships (Additional)

| Relationship | Type |
|--------------|------|
| users -> refresh_tokens | 1-N |
| users -> password_reset_tokens | 1-1 |

---

## Phase 1 vs Phase 2 Schema

| Table | Phase 1 | Phase 2 |
|-------|---------|---------|
| users | [OK] Core | [OK] Keep |
| totp_secrets | [OK] Core | [OK] Keep |
| totp_recovery_codes | [OK] Table only | [OK] Add API |
| audit_logs | [OK] Backend logs | [OK] Add API |
| refresh_tokens | [X] Not needed | [OK] New table |
| password_reset_tokens | [X] Not needed | [OK] New table |
