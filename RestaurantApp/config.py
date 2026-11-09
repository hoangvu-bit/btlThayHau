import os
from urllib.parse import quote
from dotenv import load_dotenv

# Tìm và nạp file .env từ thư mục gốc dự án
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENV_FILE = os.path.join(BASE_DIR, '.env')

if os.path.exists(ENV_FILE):
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()

class Config:
    """Quản lý cấu hình tập trung cho ứng dụng RestaurantApp"""

    # 1. Khóa bí mật Flask (Session & Flash message)
    SECRET_KEY = os.getenv("SECRET_KEY", "1234567890!@#$%^&*()")

    # 2. Thông tin tài khoản kết nối MySQL lấy từ file .env
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "restaurantdb")

    # Tạo chuỗi kết nối SQLAlchemy an toàn (URL encode mật khẩu qua quote)
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{quote(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = True

