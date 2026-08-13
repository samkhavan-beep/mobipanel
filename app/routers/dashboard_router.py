import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Client, Inbound, Admin
from ..schemas import DashboardStats
from ..auth import get_current_admin

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    clients = db.query(Client).all()
    now = dt.datetime.utcnow()

    total = len(clients)
    active = sum(1 for c in clients if c.is_active and (not c.expire_at or c.expire_at > now))
    expired = sum(1 for c in clients if c.expire_at and c.expire_at <= now)
    traffic_gb = sum(c.traffic_used_bytes for c in clients) / (1024 ** 3)

    inbounds = db.query(Inbound).all()

    return DashboardStats(
        total_clients=total,
        active_clients=active,
        expired_clients=expired,
        total_traffic_used_gb=round(traffic_gb, 2),
        total_inbounds=len(inbounds),
        active_inbounds=sum(1 for i in inbounds if i.is_active),
    )
