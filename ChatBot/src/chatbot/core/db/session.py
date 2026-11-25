"""Database initialization and session management."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from chatbot.core.config import get_settings

# Lấy đối tượng setting để móc tới các biến môi trường gồm hàm URL của database, username, password, host, port và tên database.
settings = get_settings()

# Engine kết nối tới cơ sở dữ liệu PostgreSQL sử dụng SQLAlchemy với các tham số cấu hình như URL của cơ sở dữ liệu, echo, pool_pre_ping, pool_size và max_overflow.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
)

# Bộ tạo session để quản lý các phiên làm việc với cơ sở dữ liệu. Nó sử dụng engine đã tạo và định nghĩa lớp AsyncSession để làm việc với các phiên bất đồng bộ.
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# dùng làm dependency trong FastAPI:
#  - Tạo session
#  - yield session để trả về session cho các route handler sử dụng
#  - Khi endpoit xử lý xong FastAPI tiếp tục hàm để thoát khỏi asyc with đóng session và trên kết nối đã mượn về pool
async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependency for database session injection."""
    async with AsyncSessionLocal() as session:
        yield session

# Hàm init_db() được sử dụng để khởi tạo cơ sở dữ liệu khi ứng dụng khởi động. Nó sử dụng engine để tạo kết nối và chạy lệnh tạo bảng dựa trên các mô hình đã định nghĩa trong Base.metadata.
async def init_db():
    """Initialize database on startup."""
    from chatbot.core.db.models import Base, CHATBOT_TABLES

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=CHATBOT_TABLES)
