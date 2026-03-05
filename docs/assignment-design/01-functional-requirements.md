# 01 - PHÂN TÍCH YÊU CẦU CHỨC NĂNG

## (Từ Technical Assignment VI)

---

# PHASE 1: ASM CORE (PHẢI HOÀN THÀNH)

## 1. Yêu Cầu Gốc (ASM)

### 3.1 Quản lý Người dùng

- **Tạo người dùng**: Đăng ký người dùng mới
- **Danh sách người dùng**: Hiển thị danh sách người dùng đã đăng ký
- **Xóa người dùng**: Xóa người dùng khỏi hệ thống
- **Xác thực người dùng**: Chức năng đăng nhập và đăng xuất

### 3.2 Yêu cầu Xác thực

Xác thực phải là xác thực hai yếu tố (2FA) được thực hiện qua hai giai đoạn:

- **Yếu tố thứ nhất**: ID (tên người dùng hoặc email) + Mật khẩu
- **Yếu tố thứ hai**: Xác thực TOTP (Mật khẩu một lần dựa trên thời gian)

Xác thực TOTP phải tương thích với các ứng dụng xác thực phổ biến như Google Authenticator và Microsoft Authenticator.

### 3.3 Kiểm soát Truy cập

Người dùng chưa xác thực không thể thực hiện bất kỳ thao tác nào ở trên. Sau khi xác thực, tất cả người dùng có quyền như nhau (không yêu cầu kiểm soát truy cập dựa trên vai trò).

---

## 2. Phân Tích

### 2.1. Quản Lý Người Dùng

| Chức năng | Yêu cầu | Đánh giá |
|-----------|---------|----------|
| Tạo user | Đăng ký user mới | Không rõ: User tự đăng ký hay chỉ admin? |
| Danh sách user | Hiển thị danh sách | Rõ |
| Xóa user | Xóa user khỏi hệ thống | Không rõ: Xóa được user khác? |
| Xác thực | Đăng nhập/đăng xuất | Rõ |

### 2.2. Xác Thực

| Giai đoạn | Yêu cầu | Đánh giá |
|-----------|---------|----------|
| Giai đoạn 1 | ID + Password | Không rõ: Username hay email? |
| Giai đoạn 2 | TOTP | Rõ |

### 2.3. Kiểm Soát Truy Cập

Vấn đề:
- Ai cũng xóa được ai -> mất kiểm soát
- Không có admin -> không có người quản lý

---

## 3. Các Điểm Chưa Rõ

| # | Vấn đề |
|---|--------|
| 1 | Dùng username hay email làm ID? |
| 2 | User tự đăng ký hay chỉ admin tạo? |
| 3 | User có được xóa user khác? |
| 4 | User có được xóa chính mình? |
| 5 | Ai quản lý user nếu không có admin? |

---

## 4. Thiết Kế Đề Xuất

### 4.1. Xác Thực

| Thành phần | Thiết kế |
|------------|----------|
| ID | Email |
| Password | Password |
| 2FA | TOTP |

#### Yêu Cầu Mật Khẩu

| Yêu cầu | Giá trị |
|---------|---------|
| Độ dài | 8-128 ký tự |
| Bắt buộc | Ít nhất 1 chữ hoa, 1 chữ thường, 1 số |
| Ký tự đặc biệt | Không yêu cầu |
| Blacklist | Check breached passwords |
| Thay đổi định kỳ | Không yêu cầu |

### 4.2. Phân Quyền

| Loại | Quyền User Management |
|------|------------------------|
| Super Admin | Tạo, xem, xóa tất cả |
| User thường | Không truy cập |

### 4.3. Super Admin

| Thành phần | Thiết kế |
|------------|----------|
| Khởi tạo | 1 account khi init (seed) |
| Quyền | Xem, tạo, xóa bất kỳ user |
| Hạn chế | Không xóa được chính mình |
| Thêm mới | Không có UI |

### 4.4. User Thường

| Thành phần | Thiết kế |
|------------|----------|
| Đăng ký | Tự đăng ký công khai |
| Đăng nhập | Email + Password + TOTP |
| User Management | Không truy cập (403) |
| TOTP | Tự setup (3-step chuẩn), bắt buộc trước khi login |

---

## 5. Luồng Hoạt Động

### 5.1. Đăng Ký

```
User -> Đăng ký -> Nhập email/password -> Submit ->
Tạo account (users). Row totp_secrets chưa tồn tại;
tạo khi user gọi POST /auth/totp/enroll (Step 1).
```

### 5.2. Đăng Nhập

```
User -> Nhập email/password ->
+- Sai -> Báo lỗi
+- Đúng -> Check TOTP status ->
            +- Đã enable -> Verify TOTP -> Login OK
            +- Chưa enable -> Enroll TOTP (3-step) -> Login OK
```

### 5.3. Enroll TOTP (3-step chuẩn)

```
Step 1: Enroll -> Generate secret + QR code
Step 2: Challenge -> Tạo challenge (in-memory, timeout 60s)
Step 3: Verify -> Verify code -> TOTP enabled
```

### 5.4. Truy Cập User Management

```
User đăng nhập -> User Management ->
+- Super Admin -> Cho phép
+- User thường -> Từ chối (403)
```

---

## 6. Tóm Tắt Quyền

| Chức năng | Super Admin | User |
|-----------|-------------|------|
| Đăng ký | Có | Có |
| Đăng nhập | Có | Có |
| Xem danh sách | Có | Không |
| Tạo user | Có | Không |
| Xóa user khác | Có | Không |
| Xóa chính mình | Không | Có |

---

## 7. Best Practices

1. Không xóa user cuối cùng - Luôn giữ >=1 super admin
2. Tách đăng ký và quản lý - Đăng ký công khai, quản lý chỉ admin
3. 2FA bắt buộc - Tất cả user phải enroll + verify TOTP
4. Soft delete - Phase 1 dùng soft delete: set deleted_at, không xóa row; GET /users chỉ trả về deleted_at IS NULL
5. MFA 3-step chuẩn - enroll -> challenge -> verify (theo Supabase, Auth0, Okta)
6. Challenge in-memory - Lưu trong memory/cache, không lưu DB, có timeout 60s

---

# PHASE 2: ENHANCEMENTS (FUTURE WORK)

## 8. Tính Năng Bổ Sung

### 8.1. Đổi Mật Khẩu
- User tự đổi password
- Verify current password trước khi đổi
- Bắt buộc theo Password Requirements

### 8.2. Quên Mật Khẩu
- User request reset password qua email
- Gửi reset link với token (expires 30 phút, lưu trong DB)
- User click link → nhập password mới
- Token single-use, delete row sau khi đổi
- Token mới replace token cũ (user_id PK, 1 token per user)
- Rate limiting (tránh spam email)

### 8.3. JWT Refresh Token
- Refresh access token mà không cần login lại
- Token rotation để tăng security
- Lưu refresh tokens trong database
- Access token: 10 phút, Refresh token: 30 ngày

### 8.4. Security Enhancements
- Rate limiting cho API endpoints
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Account lockout policy

### 8.5. Audit Logs API
- Admin xem audit logs
- Filter theo user, action, thời gian
- Phân trang

### 8.6. TOTP Recovery Codes
- Generate backup codes khi mất device
- 10 recovery codes mỗi user
- Single-use, hash với bcrypt

---

## 9. So Sánh Phase 1 vs Phase 2

| Tính năng | Phase 1 | Phase 2 |
|-----------|---------|---------|
| User Registration | [OK] | [OK] |
| Login với 2FA | [OK] | [OK] |
| TOTP Enrollment | [OK] | [OK] |
| User Management | [OK] | [OK] |
| Đổi Mật Khẩu | [X] | [OK] |
| Quên Mật Khẩu | [X] | [OK] |
| JWT Refresh Token | [X] | [OK] |
| Rate Limiting | [X] | [OK] |
| Security Headers | [X] | [OK] |
| Audit Logging | [OK] (Backend) | [OK] (+ API) |
| TOTP Recovery Codes | [X] (Table only) | [OK] (+ API) |
