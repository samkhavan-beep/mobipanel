import os
import datetime as dt
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import Admin

# In production, set SECRET_KEY via environment variable instead of this default.
SECRET_KEY = os.environ.get("PANEL_SECRET_KEY", "CHANGE_ME_" + os.urandom(16).hex())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
_failed_attempts = {}  # username -> (count, locked_until)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def is_locked_out(username: str) -> Optional[int]:
    """Returns remaining lockout seconds, or None if not locked."""
    entry = _failed_attempts.get(username)
    if not entry:
        return None
    count, locked_until = entry
    if locked_until and locked_until > dt.datetime.utcnow():
        return int((locked_until - dt.datetime.utcnow()).total_seconds())
    return None


def register_failed_attempt(username: str):
    count, _ = _failed_attempts.get(username, (0, None))
    count += 1
    locked_until = None
    if count >= MAX_FAILED_ATTEMPTS:
        locked_until = dt.datetime.utcnow() + dt.timedelta(minutes=LOCKOUT_MINUTES)
    _failed_attempts[username] = (count, locked_until)


def clear_failed_attempts(username: str):
    _failed_attempts.pop(username, None)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="اعتبار ورود نامعتبر است",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None or not admin.is_active:
        raise credentials_exception
    return admin


def require_super_admin(admin: Admin = Depends(get_current_admin)) -> Admin:
    if not admin.is_super:
        raise HTTPException(status_code=403, detail="فقط ادمین اصلی اجازه دارد")
    return admin
