# Đặc tả Bài tập Kỹ thuật

**Technical Assignment Specification**

**Hệ thống Quản lý Người dùng với Xác thực TOTP**

---

## 1. Tổng quan

Bài tập này đánh giá khả năng thiết kế và triển khai ứng dụng web với các tính năng quản lý người dùng và xác thực TOTP. Việc đánh giá không tập trung vào mức độ hoàn thành, mà vào cách tiếp cận vấn đề và tiến độ bạn đạt được.

---

## 2. Yêu cầu Kỹ thuật

### 2.1 Công nghệ sử dụng

| Tầng | Công nghệ | Ghi chú |
|------|-----------|---------|
| Frontend | Next.js + TypeScript | Framework dựa trên React |
| Backend | Python | Tự do chọn framework (FastAPI, Flask, Django, v.v.) |
| Cơ sở dữ liệu | MySQL | Bắt buộc |
| Hạ tầng | Docker / Docker Compose | Bắt buộc container hóa |
| Quản lý phiên bản | GitHub | Repository công khai |

---

## 3. Yêu cầu Chức năng

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

## 4. Yêu cầu Phát triển

### 4.1 Thời gian

- **Thời hạn**: 1 tuần (5 ngày làm việc)
- **Ngày bắt đầu**: Thứ Hai, ngày 2 tháng 3 năm 2026
- **Ngày kết thúc**: Thứ Sáu, ngày 6 tháng 3 năm 2026

> ⚠️ **Lưu ý**: Bạn có thể triển khai hoặc nghiên cứu trước ngày bắt đầu. Việc chuẩn bị trước được cho phép.

### 4.2 Quản lý Phiên bản

- Tạo tài khoản GitHub (hoặc sử dụng tài khoản hiện có)
- Quản lý mã nguồn trong repository công khai
- Duy trì các commit message và lịch sử phù hợp
- Bao gồm mô tả dự án cơ bản trong README.md

### 4.3 Kiểm thử

Mã kiểm thử là bắt buộc. Xem xét các khía cạnh sau và tự xác định phạm vi kiểm thử:

- **Unit Tests**: Kiểm thử các hàm và module riêng lẻ
- **Integration Tests**: Kiểm thử các API endpoint và tích hợp cơ sở dữ liệu
- **E2E Tests**: Kiểm thử dựa trên kịch bản người dùng (tùy chọn)

> ⚠️ **Lưu ý**: Tự xác định phạm vi và độ sâu của kiểm thử và ghi lại lý do của bạn.

### 4.4 Tài liệu

Tạo các tài liệu sau bằng tiếng Anh:

- **README.md**: Tổng quan dự án và hướng dẫn cài đặt
- **Hướng dẫn triển khai**: Hướng dẫn chạy trong môi trường Docker
- **Hướng dẫn chạy kiểm thử**: Cách chạy kiểm thử và xác minh kết quả
- **Đặc tả API**: Danh sách các endpoint và cách sử dụng (khuyến nghị Swagger/OpenAPI)

### 4.5 Báo cáo Triển khai

Tạo báo cáo triển khai bao gồm các nội dung sau:

#### A. Phương pháp Tiếp cận và Lý do

- Bạn đã sử dụng phương pháp và quy trình nào để triển khai?
- Tại sao bạn chọn các phương pháp này? (Lý do cho việc lựa chọn công nghệ)
- Các quyết định thiết kế và lý giải của chúng
- Các tài liệu và nguồn tham khảo đã tham khảo

#### B. Phản ánh và Thách thức

- Các tính năng không thể triển khai được, kèm lý do
- Bạn sẽ triển khai như thế nào nếu có thêm thời gian
- Những gì không hoạt động tốt và có thể làm khác đi như thế nào
- Các lĩnh vực cần cải thiện trong tương lai

#### C. Bài học và Nhận thức

- Những gì bạn học được qua bài tập này
- Các công nghệ hoặc công cụ mới đã học được
- Những điểm cần áp dụng khi giải quyết các bài tập tương tự trong tương lai

> ⚠️ **Quan trọng**: Báo cáo này là thành phần đánh giá quan trọng. Chúng tôi ưu tiên chất lượng của quá trình tư duy và tự phân tích hơn là mức độ hoàn thành.

---

## 5. Yêu cầu Docker

Cấu hình ứng dụng để chạy trên Docker:

- docker-compose.yml với cấu hình đa container
- Container hóa các dịch vụ Frontend, Backend và MySQL
- Quản lý cấu hình qua biến môi trường (cung cấp .env.example)
- Khởi tạo cơ sở dữ liệu khi khởi động lần đầu

**Lệnh khởi động mẫu:**

```bash
docker-compose up --build
```

---

## 6. Tiêu chí Đánh giá

> ⚠️ **Quan trọng**: Bài tập này đánh giá không phải bản thân việc hoàn thành, mà là các khía cạnh sau một cách toàn diện.

| Tiêu chí | Trọng tâm Đánh giá |
|----------|-------------------|
| Cách tiếp cận | Triết lý thiết kế, lý do lựa chọn công nghệ |
| Chất lượng mã nguồn | Khả năng đọc, bảo trì, cấu trúc phù hợp |
| Chiến lược kiểm thử | Tính phù hợp của phạm vi kiểm thử, chất lượng mã kiểm thử |
| Tài liệu | Rõ ràng, có thể tái tạo, đầy đủ |
| Quản lý tiến độ | Lịch sử commit, sử dụng Issue/PR (tùy chọn) |
| Khả năng giải quyết vấn đề | Xử lý các điểm không chắc chắn, tính hợp lệ của quyết định |
| Báo cáo triển khai | Sự rõ ràng của quá trình tư duy, chất lượng tự phân tích, độ sâu của phản ánh |

---

## 7. Kiến trúc Khuyến nghị

```
+-------------------------------------------------------------+
|                      Docker Compose                         |
|  +---------------+  +---------------+  +---------------+    |
|  |   Frontend    |  |   Backend     |  |    MySQL      |    |
|  |  (Next.js)    |->|   (Python)    |->|   Database    |    |
|  |  Port: 3000   |  |  Port: 8000   |  |  Port: 3306   |    |
|  +---------------+  +---------------+  +---------------+    |
+-------------------------------------------------------------+
```

**Cấu trúc thư mục khuyến nghị:**

```
project-root/
├── frontend/          # Ứng dụng Next.js
│   ├── src/
│   ├── __tests__/
│   └── Dockerfile
├── backend/           # Server API Python
│   ├── app/
│   ├── tests/
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 8. Lưu ý Quan trọng

- Các câu hỏi liên quan đến tài liệu này sẽ không được chấp nhận
- Tự nghiên cứu các điểm chưa rõ hoặc tự đưa ra quyết định
- Ghi lại các quyết định và lý do trong tài liệu hoặc commit message
- Việc lựa chọn thư viện và công cụ là linh hoạt
- Xem xét các best practice về bảo mật nếu có thể

---

## 9. Sản phẩm Nộp

- GitHub repository URL
- Môi trường Docker hoạt động
- Tài liệu cần thiết (README, hướng dẫn triển khai, hướng dẫn kiểm thử)
- **Báo cáo Triển khai (Bắt buộc)**: Báo cáo bao gồm nội dung từ mục 4.5
- (Tùy chọn) Video demo hoặc ảnh chụp màn hình

---

**Chúc bạn may mắn!**
