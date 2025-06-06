# Hệ thống Đặt vé Sự kiện (Ticket Booking System)

Hệ thống đặt vé sự kiện hiện đại được xây dựng bằng Flask, SQLAlchemy và Celery, cung cấp giải pháp toàn diện cho việc quản lý và đặt vé sự kiện.

## Chức năng chính

### 1. Quản lý người dùng
- Đăng ký và đăng nhập tài khoản
- Phân quyền người dùng (Admin, Staff, Customer)
- Quản lý thông tin cá nhân
- Đổi mật khẩu và khôi phục mật khẩu qua email

### 2. Quản lý sự kiện
- Tạo và quản lý sự kiện (dành cho Admin/Staff)
- Phân loại sự kiện theo danh mục
- Tìm kiếm sự kiện theo nhiều tiêu chí
- Lọc sự kiện theo thời gian, địa điểm, giá vé
- Xem chi tiết sự kiện và số lượng vé còn lại

### 3. Đặt vé và thanh toán
- Chọn và đặt vé cho sự kiện
- Chọn vị trí ghế ngồi (nếu có)
- Thanh toán trực tuyến qua Stripe
- Xem lịch sử đặt vé
- Hủy đặt vé (theo chính sách)

### 4. Xử lý background với Celery
- Gửi email xác nhận đặt vé
- Gửi email nhắc nhở sự kiện
- Xử lý hoàn tiền tự động khi hủy vé
- Cập nhật trạng thái vé và số lượng còn lại
- Tạo báo cáo thống kê định kỳ

### 5. Trang Admin
- Quản lý người dùng
- Quản lý sự kiện và vé
- Xem thống kê doanh thu
- Quản lý đơn đặt vé
- Xuất báo cáo

## Yêu cầu hệ thống

- Python 3.8+
- PostgreSQL
- Redis (cho Celery)
- Stripe account (cho thanh toán)

## Cài đặt và Chạy

1. Clone repository:
```bash
git clone <repository-url>
cd ticket_booking
```

2. Tạo và kích hoạt môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Cấu hình môi trường:
Tạo file `.env` với nội dung:
```
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost/ticket_booking
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=your-stripe-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
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

## Cấu trúc Project

```
app/
├── models/          # Database models
│   ├── user.py     # User model
│   ├── event.py    # Event model
│   └── ticket.py   # Ticket model
├── routes/         # Route handlers
│   ├── auth.py     # Authentication routes
│   ├── events.py   # Event management
│   └── tickets.py  # Ticket booking
├── services/       # Business logic
│   ├── email.py    # Email service
│   └── payment.py  # Payment service
├── tasks/          # Celery tasks
│   ├── email.py    # Email tasks
│   └── reports.py  # Report generation
├── templates/      # HTML templates
├── static/         # Static files
└── utils/          # Utility functions
```

## API Endpoints

### Authentication
- POST /api/auth/register - Đăng ký tài khoản
- POST /api/auth/login - Đăng nhập
- POST /api/auth/logout - Đăng xuất
- POST /api/auth/reset-password - Đặt lại mật khẩu

### Events
- GET /api/events - Lấy danh sách sự kiện
- GET /api/events/<id> - Chi tiết sự kiện
- POST /api/events - Tạo sự kiện mới (Admin)
- PUT /api/events/<id> - Cập nhật sự kiện (Admin)
- DELETE /api/events/<id> - Xóa sự kiện (Admin)

### Tickets
- POST /api/tickets/book - Đặt vé
- GET /api/tickets/my-tickets - Xem vé đã đặt
- POST /api/tickets/cancel - Hủy vé
- GET /api/tickets/download/<id> - Tải vé

## Testing

Chạy tests:
```bash
pytest
```

## Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## License

MIT License 