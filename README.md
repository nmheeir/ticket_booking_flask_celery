# Hệ Thống Đặt Vé Sự Kiện

Hệ thống đặt vé sự kiện trực tuyến được xây dựng bằng Flask, cho phép người dùng dễ dàng đặt vé cho các sự kiện và quản lý đơn đặt vé.

## Tính Năng Chính

### Người Dùng
- Đăng ký và xác thực email
- Đăng nhập/Đăng xuất
- Xem danh sách sự kiện
- Tìm kiếm sự kiện theo tên hoặc địa điểm
- Đặt vé và thanh toán trực tuyến
- Xem lịch sử đặt vé
- Hủy đặt vé và nhận hoàn tiền

### Quản Trị Viên
- Quản lý sự kiện (thêm, sửa, xóa)
- Quản lý người dùng
- Xem thống kê và báo cáo
- Gửi email thông báo hàng loạt
- Quản lý đặt vé

### Tính Năng Hệ Thống
- Xử lý thanh toán tự động
- Gửi email xác nhận và nhắc nhở
- Tạo và quản lý mã QR cho vé
- Hủy đặt vé tự động nếu không thanh toán
- Báo cáo doanh thu tự động

## Công Nghệ Sử Dụng

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Task Queue**: Celery + Redis
- **Frontend**: HTML, CSS, JavaScript
- **Email**: Flask-Mail
- **Authentication**: Flask-Login
- **Form Handling**: Flask-WTF
- **Container**: Docker

## Cài Đặt và Chạy

### Yêu Cầu Hệ Thống
- Python 3.11+
- Redis
- Docker (tùy chọn)

### Cài Đặt Thông Thường

1. Clone repository:
```bash
git clone <repository-url>
cd ticket_booking_project
```

2. Tạo môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate   # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file .env từ env.example và cấu hình:
```bash
cp env.example .env
```

5. Khởi tạo database:
```bash
flask db upgrade
```

6. Chạy ứng dụng:
```bash
flask run
```

7. Chạy Celery worker (terminal khác):
```bash
celery -A celery_worker.celery worker --loglevel=info
```

### Cài Đặt Docker

1. Build và chạy containers:
```bash
docker-compose up --build
```

## Cấu Trúc Project

```
app/
├── models/              # Database models
│   ├── user.py         # User model
│   ├── event.py        # Event model
│   ├── booking.py      # Booking model
│   └── ticket.py       # Ticket model
├── routes/             # Route handlers
│   ├── main.py         # Main routes
│   ├── auth.py         # Authentication routes
│   ├── events.py       # Event management
│   ├── booking.py      # Booking management
│   └── admin.py        # Admin panel routes
├── services/           # Business logic
│   ├── auth_service.py # Authentication service
│   ├── booking_service.py # Booking service
│   └── email_service.py  # Email service
├── celery/            # Celery tasks
│   └── tasks/
│       ├── booking_tasks.py    # Booking related tasks
│       └── email_tasks.py      # Email related tasks
├── templates/         # HTML templates
├── static/           # Static files
└── utils/            # Utility functions
```

## Quy Trình Đặt Vé

1. Người dùng chọn sự kiện và số lượng vé
2. Hệ thống tạo đơn đặt vé tạm thời (10 phút)
3. Người dùng thanh toán
4. Sau khi thanh toán thành công:
   - Tạo vé với mã QR
   - Gửi email xác nhận
   - Cập nhật số lượng vé còn lại
5. Nếu không thanh toán trong 10 phút:
   - Hủy đơn đặt vé
   - Hoàn trả số lượng vé vào hệ thống

## Tác Vụ Tự Động (Celery)

- Gửi email nhắc nhở trước sự kiện
- Hủy đơn đặt vé quá hạn thanh toán
- Kiểm tra và thông báo khi vé sắp hết
- Dọn dẹp đơn đặt vé bị bỏ dở

## Phân Quyền

### User (Người Dùng)
- Xem sự kiện
- Đặt vé
- Quản lý đơn đặt vé cá nhân

### Staff (Nhân Viên)
- Quản lý sự kiện
- Xem thống kê cơ bản
- Xử lý đơn đặt vé

### Administrator (Quản Trị Viên)
- Tất cả quyền của Staff
- Quản lý người dùng
- Xem báo cáo chi tiết
- Cấu hình hệ thống