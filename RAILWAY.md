# دیپلوی روی Railway

## ۱. آماده‌سازی ریپازیتوری
این پروژه الان ۳ فایل جدید داره که مخصوص Railway اضافه شدن:
- `Procfile` — دستور اجرا: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- `railway.json` — تنظیمات build/start (اختیاریه، Procfile هم کافیه)
- `.gitignore` — جلوگیری از commit شدن `panel.db` و فایل‌های موقت

کل پوشه رو (همراه با این فایل‌های جدید) به یه ریپازیتوری گیت‌هاب پوش کن.

## ۲. ساخت پروژه در Railway
1. وارد https://railway.app بشو → **New Project** → **Deploy from GitHub repo**
2. ریپازیتوری رو انتخاب کن. Railway خودش Python و `requirements.txt` رو تشخیص می‌ده (Nixpacks).
3. بعد از اولین بیلد، از تب **Settings → Networking** یه **Public Domain** بساز (چیزی شبیه `xxx.up.railway.app`، با HTTPS رایگان).

## ۳. متغیرهای محیطی (Variables)
توی تب **Variables** پروژه این‌ها رو اضافه کن:

| Key | مقدار |
|---|---|
| `PANEL_SECRET_KEY` | یه رشته‌ی تصادفی طولانی و امن (مثلاً خروجی `openssl rand -hex 32`) |
| `PANEL_DB_PATH` | `/data/panel.db` (بعد از اضافه کردن Volume در مرحله‌ی بعد) |

⚠️ بدون `PANEL_SECRET_KEY`، با هر ری‌استارت یه کلید تصادفی جدید ساخته می‌شه و همه‌ی توکن‌های JWT باطل می‌شن (همه باید دوباره لاگین کنن).

## ۴. ماندگار کردن دیتابیس (Volume)
فایل‌سیستم پیش‌فرض سرویس‌های Railway **ephemeral** هست — یعنی با هر دیپلوی جدید پاک می‌شه. برای اینکه `panel.db` (کاربرها، اینباندها، تنظیمات) از بین نره:

1. توی صفحه‌ی سرویس، تب **Volumes** رو باز کن → **New Volume**
2. مسیر Mount رو بذار: `/data`
3. متغیر `PANEL_DB_PATH=/data/panel.db` رو ست کن (اگه در مرحله‌ی قبل نزدی)
4. Redeploy کن

کد `app/database.py` از قبل طوری تنظیم شده که اگه `PANEL_DB_PATH` ست باشه از همون استفاده می‌کنه؛ در غیر این صورت مثل قبل کنار پروژه `panel.db` می‌سازه.

## ۵. ساخت اولین ادمین
بعد از اولین دیپلوی موفق، از طریق Railway CLI:

```bash
railway login
railway link          # پروژه رو انتخاب کن
railway run python create_admin.py admin YOUR_STRONG_PASSWORD
```

این دستور با همون متغیرهای محیطی سرویس (از جمله `PANEL_DB_PATH`) اجرا می‌شه، پس روی همون دیتابیسی که پنل واقعی استفاده می‌کنه ادمین می‌سازه.

## ۶. تنظیم آدرس سرور برای لینک‌های اشتراک
چون پنل خودش پشت دامنه‌ی Railway (یا دامنه‌ی اختصاصی‌ت) هست، ولی لینک‌های VLESS/VMess/Trojan باید به **آدرس سرور Xray واقعی‌ت** اشاره کنن (نه به Railway) — این دو تا معمولاً یکی نیستن، چون Railway فقط پنل مدیریتی رو هاست می‌کنه، نه خود Xray-core.

مقدار `server_address` رو طبق راهنمای README اصلی ست کن، اما این بار با `railway run`:

```bash
railway run python -c "
from app.database import SessionLocal
from app.models import Setting
db = SessionLocal()
db.merge(Setting(key='server_address', value='your-real-server.com'))
db.commit()
"
```

## نکات مهم امنیتی که از README اصلی هم صدق می‌کنن
- پورت پنل رو با فایروال Railway (یا خود پلتفرم) محدود کن اگه امکانش هست، یا حداقل 2FA رو روی همه‌ی ادمین‌ها فعال کن.
- به‌صورت دوره‌ای از Volume/`panel.db` بک‌آپ بگیر (Railway به‌صورت پیش‌فرض بک‌آپ خودکار Volume نداره).
- توجه کن Railway خودش Xray-core رو اجرا نمی‌کنه — این پنل فقط مدیریت کانفیگ‌هاست؛ Xray باید روی سرور واقعی خودت جدا نصب و اجرا بشه.
