import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# MySQL configuration with env override support.
DB_HOST = os.getenv("DB_HOST") or "127.0.0.1"
DB_PORT = os.getenv("DB_PORT") or "3306"
DB_USER = os.getenv("DB_USER") or "root"
DB_PASSWORD = os.getenv("DB_PASSWORD") or "yyr0218..."
DB_NAME = os.getenv("DB_NAME") or "network_management"

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from models import Base  # noqa: E402


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
