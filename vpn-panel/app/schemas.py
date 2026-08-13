import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str
    otp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    totp_setup_required: bool = False


# ---------- Client (VPN user) ----------
class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    group: str = "default"
    traffic_limit_gb: float = 0        # 0 = unlimited
    expire_days: Optional[int] = None  # None = never
    device_limit: int = 0
    inbound_ids: List[int] = []


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    group: Optional[str] = None
    traffic_limit_gb: Optional[float] = None
    expire_days: Optional[int] = None
    device_limit: Optional[int] = None
    is_active: Optional[bool] = None
    inbound_ids: Optional[List[int]] = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid: str
    name: str
    email: Optional[str]
    group: str
    traffic_limit_bytes: int
    traffic_used_bytes: int
    expire_at: Optional[dt.datetime]
    device_limit: int
    is_active: bool
    created_at: dt.datetime


# ---------- Inbound ----------
class InboundCreate(BaseModel):
    remark: str
    protocol: str          # vless | vmess | trojan | shadowsocks
    listen_port: int
    transport: str = "tcp"  # tcp | ws | grpc | http2
    security: str = "none"  # none | tls | reality
    sni: Optional[str] = None
    ws_path: Optional[str] = None
    grpc_service_name: Optional[str] = None
    reality_dest: Optional[str] = None
    reality_short_id: Optional[str] = None
    fallback_domain: Optional[str] = None


class InboundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    remark: str
    protocol: str
    listen_port: int
    transport: str
    security: str
    sni: Optional[str]
    ws_path: Optional[str]
    grpc_service_name: Optional[str]
    reality_dest: Optional[str]
    fallback_domain: Optional[str]
    is_active: bool
    created_at: dt.datetime


# ---------- Dashboard ----------
class DashboardStats(BaseModel):
    total_clients: int
    active_clients: int
    expired_clients: int
    total_traffic_used_gb: float
    total_inbounds: int
    active_inbounds: int
