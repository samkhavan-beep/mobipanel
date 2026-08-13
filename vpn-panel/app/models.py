import uuid
import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Boolean, BigInteger, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from .database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_super = Column(Boolean, default=False)
    totp_secret = Column(String(64), nullable=True)  # 2FA secret, null = disabled
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64))
    ip_address = Column(String(64))
    user_agent = Column(String(255))
    success = Column(Boolean)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Client(Base):
    """A VPN/proxy end-user (not an admin)."""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(64), unique=True, index=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    group = Column(String(64), default="default")  # plan / group name

    traffic_limit_bytes = Column(BigInteger, default=0)  # 0 = unlimited
    traffic_used_bytes = Column(BigInteger, default=0)

    expire_at = Column(DateTime, nullable=True)  # null = never
    device_limit = Column(Integer, default=0)  # 0 = unlimited concurrent IPs

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    inbounds = relationship("ClientInbound", back_populates="client", cascade="all, delete-orphan")


class Inbound(Base):
    __tablename__ = "inbounds"

    id = Column(Integer, primary_key=True, index=True)
    remark = Column(String(128), nullable=False)
    protocol = Column(String(32), nullable=False)   # vless, vmess, trojan, shadowsocks
    listen_port = Column(Integer, nullable=False, unique=True)
    transport = Column(String(32), default="tcp")   # tcp, ws, grpc, http2
    security = Column(String(16), default="none")   # none, tls, reality
    sni = Column(String(128), nullable=True)
    ws_path = Column(String(128), nullable=True)
    grpc_service_name = Column(String(128), nullable=True)
    reality_dest = Column(String(255), nullable=True)      # e.g. www.microsoft.com:443
    reality_private_key = Column(String(255), nullable=True)
    reality_short_id = Column(String(64), nullable=True)
    fallback_domain = Column(String(255), nullable=True)   # fake site behind TLS
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    clients = relationship("ClientInbound", back_populates="inbound", cascade="all, delete-orphan")


class ClientInbound(Base):
    """Many-to-many: which clients are assigned to which inbounds."""
    __tablename__ = "client_inbounds"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    inbound_id = Column(Integer, ForeignKey("inbounds.id"))

    client = relationship("Client", back_populates="inbounds")
    inbound = relationship("Inbound", back_populates="clients")


class Setting(Base):
    """Generic key-value store for panel-wide settings (domain, telegram bot token, etc)."""
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)
