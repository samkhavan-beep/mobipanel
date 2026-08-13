import datetime as dt
import io
import base64
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Client, ClientInbound, Inbound, Admin, Setting
from ..schemas import ClientCreate, ClientUpdate, ClientOut
from ..auth import get_current_admin
from ..xray_config import build_subscription_link

router = APIRouter(prefix="/api/clients", tags=["clients"])

GB = 1024 ** 3


@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    return db.query(Client).order_by(Client.created_at.desc()).all()


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    expire_at = None
    if payload.expire_days:
        expire_at = dt.datetime.utcnow() + dt.timedelta(days=payload.expire_days)

    client = Client(
        name=payload.name,
        email=payload.email,
        group=payload.group,
        traffic_limit_bytes=int(payload.traffic_limit_gb * GB),
        expire_at=expire_at,
        device_limit=payload.device_limit,
    )
    db.add(client)
    db.flush()

    for inbound_id in payload.inbound_ids:
        db.add(ClientInbound(client_id=client.id, inbound_id=inbound_id))

    db.commit()
    db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(404, "کاربر پیدا نشد")

    if payload.name is not None:
        client.name = payload.name
    if payload.email is not None:
        client.email = payload.email
    if payload.group is not None:
        client.group = payload.group
    if payload.traffic_limit_gb is not None:
        client.traffic_limit_bytes = int(payload.traffic_limit_gb * GB)
    if payload.expire_days is not None:
        client.expire_at = dt.datetime.utcnow() + dt.timedelta(days=payload.expire_days) if payload.expire_days > 0 else None
    if payload.device_limit is not None:
        client.device_limit = payload.device_limit
    if payload.is_active is not None:
        client.is_active = payload.is_active
    if payload.inbound_ids is not None:
        db.query(ClientInbound).filter(ClientInbound.client_id == client.id).delete()
        for inbound_id in payload.inbound_ids:
            db.add(ClientInbound(client_id=client.id, inbound_id=inbound_id))

    db.commit()
    db.refresh(client)
    return client


@router.post("/{client_id}/reset-traffic", response_model=ClientOut)
def reset_traffic(client_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(404, "کاربر پیدا نشد")
    client.traffic_used_bytes = 0
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(404, "کاربر پیدا نشد")
    db.delete(client)
    db.commit()
    return {"ok": True}


@router.get("/{client_id}/subscription")
def get_subscription(client_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(404, "کاربر پیدا نشد")

    server_setting = db.query(Setting).filter(Setting.key == "server_address").first()
    server_address = server_setting.value if server_setting else "YOUR_SERVER_DOMAIN"

    links = []
    for ci in client.inbounds:
        inbound = ci.inbound
        if inbound.is_active:
            links.append(build_subscription_link(client, inbound, server_address))

    combined = "\n".join(links)
    b64 = base64.b64encode(combined.encode()).decode()

    qr_images = []
    for link in links:
        img = qrcode.make(link)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_images.append("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())

    return {"links": links, "subscription_base64": b64, "qr_codes": qr_images}
