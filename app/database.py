from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# اگه PANEL_DB_PATH ست شده باشه (مثلاً مسیر یه Volume روی Railway)، از همون استفاده می‌شه.
# در غیر این صورت، مثل قبل کنار پروژه panel.db ساخته می‌شه.
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "panel.db")
DB_PATH = os.environ.get("PANEL_DB_PATH", "").strip() or DEFAULT_DB_PATH

# اگه پوشه‌ی مقصد (مثلاً /data روی Volume) هنوز وجود نداشته باشه، خودمون می‌سازیمش
# تا SQLite با خطای "unable to open database file" مواجه نشه.
db_dir = os.path.dirname(os.path.abspath(DB_PATH))
os.makedirs(db_dir, exist_ok=True)

print(f"[database] using DB_PATH = {DB_PATH}", flush=True)

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
