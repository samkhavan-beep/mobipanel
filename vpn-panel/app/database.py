from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# اگه PANEL_DB_PATH ست شده باشه (مثلاً مسیر یه Volume روی Railway)، از همون استفاده می‌شه.
# در غیر این صورت، مثل قبل کنار پروژه panel.db ساخته می‌شه.
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "panel.db")
DB_PATH = os.environ.get("PANEL_DB_PATH", DEFAULT_DB_PATH)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
