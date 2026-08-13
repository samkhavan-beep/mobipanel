# پنل مدیریت VPN/پروکسی (MVP)

این یک **نسخه‌ی اولیه‌ی کاربردی** از پنل شماست — مثل هسته‌ی Marzban/3x-ui، اما ساده‌تر.
می‌تونی روش بسازی و بخش‌های بیشتری اضافه کنی.

## چی توش هست؟

- ✅ لاگین با یوزرنیم/پسورد + قفل موقت بعد از تلاش‌های ناموفق + پشتیبانی از 2FA (Google Authenticator)
- ✅ لاگ ورود (IP، User-Agent، زمان)
- ✅ مدیریت کاربران: سقف حجم، تاریخ انقضا، فعال/غیرفعال، ریست حجم، گروه‌بندی
- ✅ لینک اشتراک + QR Code برای هر کاربر (VLESS / VMess / Trojan / Shadowsocks)
- ✅ مدیریت اینباند: چند پورت هم‌زمان، Transport (TCP/WS/gRPC/HTTP2)، Security (None/TLS/Reality)
- ✅ خروجی JSON کانفیگ Xray برای هر اینباند (برای گذاشتن روی سرور واقعی)
- ✅ داشبورد با آمار کلی (تعداد کاربران، مصرف، اینباندهای فعال)
- ✅ دیتابیس واقعی SQLite (فایل `panel.db`, پایدار بین ری‌استارت‌ها)
- ✅ فرانت‌اند ریسپانسیو، فارسی (RTL)، حالت تاریک/روشن

## چی توش نیست (باید بعداً اضافه کنی)؟

- اجرای واقعی Xray-core روی سرور و همگام‌سازی آمار مصرف واقعی (الان `traffic_used_bytes` فقط توسط API قابل ریست/آپدیته، اسکریپت مانیتورینگ جدا لازم داره)
- اتصال به بات تلگرام / Webhook
- چند سرور (Node) و Load Balancing
- Let's Encrypt خودکار و Reverse proxy
- محدودیت IP هم‌زمان به‌صورت واقعی (فیلد `device_limit` ذخیره می‌شه ولی enforce نمی‌شه)

## نصب و اجرا

```bash
cd vpn-panel
pip install -r requirements.txt

# اگر با خطای بروزرسانی نسخه‌ی bcrypt مواجه شدید:
pip install "bcrypt==4.0.1"

# ساخت اولین ادمین (Super Admin)
python create_admin.py admin YOUR_STRONG_PASSWORD

# اجرا
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

بعد از اجرا، پنل روی `http://SERVER_IP:8000` در دسترسه.

## فعال کردن 2FA برای یک ادمین

فعلاً از طریق کد (بعداً می‌تونی UI براش اضافه کنی):

```python
import pyotp
from app.database import SessionLocal
from app.models import Admin

db = SessionLocal()
admin = db.query(Admin).filter(Admin.username == "admin").first()
admin.totp_secret = pyotp.random_base32()
db.commit()
print("Secret:", admin.totp_secret)
print("QR URI:", pyotp.totp.TOTP(admin.totp_secret).provisioning_uri(name="admin", issuer_name="VPN Panel"))
```

QR URI رو با هر ابزار تولید QR (یا سایت‌های آنلاین) به عکس تبدیل کن و با Google Authenticator اسکن کن.

## تنظیم دامنه‌ی سرور برای لینک اشتراک

لینک‌های VLESS/VMess/... به آدرس سرور نیاز دارن. این مقدار رو در جدول `settings` ست کن:

```python
from app.database import SessionLocal
from app.models import Setting

db = SessionLocal()
db.merge(Setting(key="server_address", value="your-domain.com"))
db.commit()
```

## نکات امنیتی مهم قبل از استفاده‌ی واقعی

1. `PANEL_SECRET_KEY` رو به‌صورت متغیر محیطی ست کن (وگرنه هر ری‌استارت یه کلید تصادفی جدید ساخته می‌شه و همه باید دوباره لاگین کنن):
   ```bash
   export PANEL_SECRET_KEY="یک-رشته-تصادفی-طولانی-و-امن"
   ```
2. پنل رو پشت HTTPS (nginx/caddy + TLS) بذار، نه مستقیم HTTP.
3. پورت پنل رو با فایروال محدود کن (فقط IP خودت).
4. پسورد ادمین قوی باشه و 2FA رو فعال کن.
5. از `panel.db` به‌صورت دوره‌ای بک‌آپ بگیر.

## ساختار پروژه

```
vpn-panel/
├── app/
│   ├── main.py              # اپلیکیشن اصلی FastAPI
│   ├── database.py          # اتصال SQLite
│   ├── models.py            # مدل‌های دیتابیس
│   ├── schemas.py           # اسکیمای ورودی/خروجی API
│   ├── auth.py              # JWT، هش پسورد، قفل موقت
│   ├── xray_config.py       # تولید کانفیگ Xray و لینک اشتراک
│   └── routers/
│       ├── auth_router.py
│       ├── clients_router.py
│       ├── inbounds_router.py
│       └── dashboard_router.py
├── static/index.html        # کل فرانت‌اند (تک‌فایل)
├── create_admin.py          # اسکریپت ساخت ادمین اول
└── requirements.txt
```
