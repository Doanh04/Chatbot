# ChatBot

ChatBot là workspace cho ứng dụng hội thoại AI đang được phát triển. Hiện project có backend xác thực người dùng, API chat thử với mô hình Ollama, các model dữ liệu chat/tài liệu và lớp lưu file trên ổ đĩa hoặc Cloudflare R2. README này mô tả **những phần đã có trong code** và sẽ được cập nhật khi tính năng mới hoàn thành.

## Cấu trúc dự án

| Thư mục / file | Vai trò |
| --- | --- |
| `BackendChatbot/` | Java 21, Spring Boot 4.1.2: đăng ký, đăng nhập, JWT, vai trò người dùng |
| `ChatBot/` | Python >=3.12, FastAPI: chat thử với Ollama, model và repository dữ liệu, lớp lưu file |
| `compose.yaml` | Chạy hai service cùng PostgreSQL 17 |
| `.env.example` | Mẫu cấu hình môi trường; sao chép thành `.env` để chạy |

`FrontendChatbot/` hiện chưa có source ứng dụng. Hai backend dùng chung một PostgreSQL: Spring Boot sở hữu bảng `users` và các bảng auth (Flyway); Python sở hữu bảng chat và tài liệu (Alembic), tham chiếu `users.id` dạng UUID.

## Tính năng hiện có

- **Auth (cổng 8080):** đăng ký, đăng nhập, xác minh và thu hồi JWT khi đăng xuất. Phản hồi nghiệp vụ theo cấu trúc `ApiResponse`.
- **ChatBot API (cổng 8000):** `GET /health` và `POST /chat`. `/chat` hiện gọi **Ollama** trực tiếp, nhận `message` và `reasoning` tùy chọn, trả `reply` cùng tên `model`.
- **Dữ liệu:** model cho thư mục/file kiến thức, phiên chat, tin nhắn và liên kết giữa phiên chat với tài liệu. Repository folder/file có lọc theo `user_id`.
- **Lưu file:** `ObjectStorage` hỗ trợ ổ đĩa local hoặc Cloudflare R2; R2 có presigned URL và multipart upload. Lớp này chưa được nối với HTTP endpoint upload hoặc tự ghi metadata vào database.
- **Gemini:** có hàm tạo client và chuỗi fallback trong `ChatBot/src/chatbot/core/config.py`, nhưng `POST /chat` hiện chưa sử dụng chúng.

## Yêu cầu để chạy

- Docker Desktop và Docker Compose.
- Ollama chạy trên máy host cùng một model đã cài nếu muốn gọi `POST /chat`. Dùng `ollama list` để xem đúng tên model.
- Cổng `8000`, `8080` và `5432` còn trống. PostgreSQL và Python API được Compose publish trên `localhost`; backend publish cổng `8080`.

Chạy các lệnh bên dưới bằng PowerShell **từ thư mục gốc project**.

### 1. Tạo cấu hình

Nếu chưa có `.env`:

```powershell
Copy-Item .env.example .env
```

Mở `.env` và thay ít nhất hai giá trị:

```dotenv
POSTGRES_PASSWORD=<mat-khau-postgres>
AUTH_JWT_SECRET_BASE64=<khoa-ngau-nhien-base64>
```

JWT secret cần ít nhất 32 byte ngẫu nhiên trước khi mã hóa Base64. Có thể tạo bằng PowerShell:

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

Chọn `OLLAMA_MODEL` đúng với kết quả `ollama list`. Khi Ollama chạy trên host và Python chạy trong Docker, đặt `OLLAMA_BASE_URL=http://host.docker.internal:11434` (giá trị trong file mẫu).

R2 và Gemini là cấu hình tùy chọn. Nếu muốn lưu file **local**, để trống cả bốn biến `R2_BUCKET`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` trong `.env`; các placeholder không rỗng trong `.env.example` không phải thông tin R2 thật. Nếu dùng R2, `R2_ENDPOINT` là URL account **không có tên bucket ở cuối**. Không commit `.env` hoặc đưa secret vào tài liệu.

### 2. Khởi động và tạo bảng

```powershell
docker compose up --build -d postgres-db backend
Invoke-RestMethod http://localhost:8080/health
docker compose build app
docker compose run --rm app /app/.venv/bin/alembic upgrade head
docker compose up -d app
```

Đợi `GET /health` của backend thành công trước khi chạy Alembic: Flyway của backend phải tạo `users` trước khi các bảng Python tham chiếu bảng này. Migration Python chạy **thủ công**, không tự chạy khi API khởi động.

Kiểm tra các container và API:

```powershell
docker compose ps
Invoke-RestMethod http://localhost:8000/health
```

### 3. Thử chat

Đảm bảo Ollama đã chạy và model trong `.env` đã được cài. Sau đó gửi request:

```powershell
$body = @{ message = "Xin chào"; reasoning = $false } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/chat -Method Post -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

`reasoning` có thể bỏ qua (mặc định `false`). `GET /health` của Python chỉ xác nhận API đang chạy, không kiểm tra Ollama hay database. Tài liệu HTTP tự sinh của FastAPI ở `http://localhost:8000/docs`.

## API hiện có

| Service | Endpoint | Mục đích |
| --- | --- | --- |
| Backend | `GET /health` | Kiểm tra backend |
| Backend | `POST /auth/register` | Tạo tài khoản; nhận `username`, `email`, `password`, tùy chọn `phone`, `fullName` |
| Backend | `POST /auth/login` | Đăng nhập bằng `usernameOrEmail` và `password`; trả Bearer access token |
| Backend | `GET /auth/verify` | Xác minh Bearer token |
| Backend | `POST /auth/logout` | Thu hồi Bearer token hiện tại |
| ChatBot | `GET /health` | Kiểm tra Python API |
| ChatBot | `POST /chat` | Gửi prompt tới Ollama; nhận `reply` và `model` |

## Phát triển tiếp

Các hướng mở rộng dự kiến như API upload tài liệu, kết nối storage với metadata, hội thoại lưu trong database và RAG cần được triển khai trước khi mô tả là tính năng đang hoạt động. Khi code thay đổi, cập nhật phần tương ứng trong README này, `.env.example` và [hướng dẫn agent](Agent.MD). Chi tiết về model, repository và migration xem [ChatBot/README.md](ChatBot/README.md); chi tiết auth xem [BackendChatbot/README.md](BackendChatbot/README.md).
