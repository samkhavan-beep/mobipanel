"""
اجرای این فایل یک ادمین اصلی (Super Admin) در دیتابیس می‌سازد.
استفاده:
    python create_admin.py <username> <password>
"""
import sys
from app.database import Base, engine, SessionLocal
from app.models import Admin
from app.auth import hash_password

Base.metadata.create_all(bind=engine)


def main():
    if len(sys.argv) != 3:
        print("استفاده: python create_admin.py <username> <password>")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]
    db = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.username == username).first()
        if existing:
            print(f"کاربر '{username}' از قبل وجود دارد.")
            return
        admin = Admin(
            username=username,
            password_hash=hash_password(password),
            is_super=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"ادمین '{username}' با موفقیت ساخته شد.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
