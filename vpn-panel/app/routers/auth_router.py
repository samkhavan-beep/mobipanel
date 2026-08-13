from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import pyotp

from ..database import get_db
from ..models import Admin, LoginLog
from ..schemas import LoginRequest, TokenResponse
from ..auth import (
    verify_password, create_access_token, is_locked_out,
    register_failed_attempt, clear_failed_attempts, get_current_admin
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    remaining = is_locked_out(payload.username)
    if remaining:
        raise HTTPException(
            status_code=429,
            detail=f"تعداد تلاش‌های ناموفق زیاد بود. {remaining} ثانیه دیگر دوباره امتحان کنید."
        )

    admin = db.query(Admin).filter(Admin.username == payload.username).first()
    ok = admin is not None and admin.is_active and verify_password(payload.password, admin.password_hash)

    if ok and admin.totp_secret:
        totp = pyotp.TOTP(admin.totp_secret)
        if not payload.otp_code or not totp.verify(payload.otp_code, valid_window=1):
            ok = False

    log = LoginLog(
        username=payload.username,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        success=ok,
    )
    db.add(log)
    db.commit()

    if not ok:
        register_failed_attempt(payload.username)
        raise HTTPException(status_code=401, detail="نام کاربری، رمز عبور یا کد ۲مرحله‌ای اشتباه است")

    clear_failed_attempts(payload.username)
    token = create_access_token({"sub": admin.username})
    return TokenResponse(access_token=token)


@router.get("/me")
def me(admin: Admin = Depends(get_current_admin)):
    return {"username": admin.username, "is_super": admin.is_super, "totp_enabled": bool(admin.totp_secret)}
