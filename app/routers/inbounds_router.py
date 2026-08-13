from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Inbound, Admin
from ..schemas import InboundCreate, InboundOut
from ..auth import get_current_admin
from ..xray_config import build_inbound_json

VALID_PROTOCOLS = {"vless", "vmess", "trojan", "shadowsocks"}
VALID_TRANSPORTS = {"tcp", "ws", "grpc", "http2"}
VALID_SECURITY = {"none", "tls", "reality"}

router = APIRouter(prefix="/api/inbounds", tags=["inbounds"])


@router.get("", response_model=list[InboundOut])
def list_inbounds(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    return db.query(Inbound).order_by(Inbound.created_at.desc()).all()


@router.post("", response_model=InboundOut)
def create_inbound(payload: InboundCreate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    if payload.protocol not in VALID_PROTOCOLS:
        raise HTTPException(400, f"پروتکل نامعتبر. یکی از: {VALID_PROTOCOLS}")
    if payload.transport not in VALID_TRANSPORTS:
        raise HTTPException(400, f"transport نامعتبر. یکی از: {VALID_TRANSPORTS}")
    if payload.security not in VALID_SECURITY:
        raise HTTPException(400, f"security نامعتبر. یکی از: {VALID_SECURITY}")

    exists = db.query(Inbound).filter(Inbound.listen_port == payload.listen_port).first()
    if exists:
        raise HTTPException(400, "این پورت قبلاً استفاده شده")

    inbound = Inbound(**payload.model_dump())
    db.add(inbound)
    db.commit()
    db.refresh(inbound)
    return inbound


@router.patch("/{inbound_id}/toggle", response_model=InboundOut)
def toggle_inbound(inbound_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    inbound = db.query(Inbound).get(inbound_id)
    if not inbound:
        raise HTTPException(404, "اینباند پیدا نشد")
    inbound.is_active = not inbound.is_active
    db.commit()
    db.refresh(inbound)
    return inbound


@router.delete("/{inbound_id}")
def delete_inbound(inbound_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    inbound = db.query(Inbound).get(inbound_id)
    if not inbound:
        raise HTTPException(404, "اینباند پیدا نشد")
    db.delete(inbound)
    db.commit()
    return {"ok": True}


@router.get("/{inbound_id}/xray-config")
def get_xray_config(inbound_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    """Returns the raw Xray inbound JSON block (to paste into config.json on the server)."""
    inbound = db.query(Inbound).get(inbound_id)
    if not inbound:
        raise HTTPException(404, "اینباند پیدا نشد")
    clients = [ci.client for ci in inbound.clients]
    return build_inbound_json(inbound, clients)
