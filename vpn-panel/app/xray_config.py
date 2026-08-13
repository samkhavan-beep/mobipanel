"""
تولید JSON کانفیگ Xray-core و لینک‌های اشتراک (subscription link)
برای هر ترکیب کلاینت + اینباند.
این ماژول فقط کانفیگ تولید می‌کند؛ اجرای واقعی Xray روی سرور خارج از
محدوده‌ی این پنل نمونه است (باید جدا روی سرور نصب و به همین کانفیگ‌ها لینک شود).
"""
import base64
import json
import urllib.parse
from .models import Client, Inbound


def build_stream_settings(inbound: Inbound) -> dict:
    stream = {"network": inbound.transport}

    if inbound.transport == "ws":
        stream["wsSettings"] = {"path": inbound.ws_path or "/"}
    elif inbound.transport == "grpc":
        stream["grpcSettings"] = {"serviceName": inbound.grpc_service_name or "grpc"}

    if inbound.security == "tls":
        stream["security"] = "tls"
        stream["tlsSettings"] = {"serverName": inbound.sni or ""}
    elif inbound.security == "reality":
        stream["security"] = "reality"
        stream["realitySettings"] = {
            "dest": inbound.reality_dest or "www.microsoft.com:443",
            "serverNames": [inbound.sni] if inbound.sni else [],
            "shortIds": [inbound.reality_short_id or ""],
            "privateKey": inbound.reality_private_key or "",
        }
    else:
        stream["security"] = "none"

    return stream


def build_inbound_json(inbound: Inbound, clients: list[Client]) -> dict:
    """Full Xray inbound object including all assigned clients."""
    settings = {"clients": [], "decryption": "none"}

    for c in clients:
        if inbound.protocol == "vless":
            settings["clients"].append({"id": c.uuid, "email": c.email or c.name})
        elif inbound.protocol == "vmess":
            settings["clients"].append({"id": c.uuid, "email": c.email or c.name, "alterId": 0})
        elif inbound.protocol == "trojan":
            settings["clients"].append({"password": c.uuid, "email": c.email or c.name})
        elif inbound.protocol == "shadowsocks":
            settings["clients"].append({
                "password": c.uuid, "method": "aes-128-gcm", "email": c.email or c.name
            })

    return {
        "tag": f"in-{inbound.id}",
        "listen": "0.0.0.0",
        "port": inbound.listen_port,
        "protocol": inbound.protocol,
        "settings": settings,
        "streamSettings": build_stream_settings(inbound),
    }


def build_subscription_link(client: Client, inbound: Inbound, server_address: str) -> str:
    """Builds a shareable URI (vless://, vmess://, trojan://, ss://) for one client+inbound."""
    tag = urllib.parse.quote(f"{inbound.remark}-{client.name}")

    if inbound.protocol == "vless":
        params = {
            "type": inbound.transport,
            "security": inbound.security,
        }
        if inbound.security == "tls":
            params["sni"] = inbound.sni or ""
        if inbound.security == "reality":
            params["sni"] = inbound.sni or ""
            params["pbk"] = inbound.reality_private_key or ""
            params["sid"] = inbound.reality_short_id or ""
        if inbound.transport == "ws":
            params["path"] = inbound.ws_path or "/"
        if inbound.transport == "grpc":
            params["serviceName"] = inbound.grpc_service_name or ""
        query = urllib.parse.urlencode(params)
        return f"vless://{client.uuid}@{server_address}:{inbound.listen_port}?{query}#{tag}"

    elif inbound.protocol == "vmess":
        vmess_obj = {
            "v": "2", "ps": tag, "add": server_address, "port": str(inbound.listen_port),
            "id": client.uuid, "aid": "0", "net": inbound.transport,
            "type": "none", "host": inbound.sni or "", "path": inbound.ws_path or "/",
            "tls": "tls" if inbound.security == "tls" else "",
        }
        encoded = base64.b64encode(json.dumps(vmess_obj).encode()).decode()
        return f"vmess://{encoded}"

    elif inbound.protocol == "trojan":
        query = urllib.parse.urlencode({
            "security": inbound.security, "sni": inbound.sni or "", "type": inbound.transport
        })
        return f"trojan://{client.uuid}@{server_address}:{inbound.listen_port}?{query}#{tag}"

    elif inbound.protocol == "shadowsocks":
        userinfo = base64.b64encode(f"aes-128-gcm:{client.uuid}".encode()).decode()
        return f"ss://{userinfo}@{server_address}:{inbound.listen_port}#{tag}"

    return ""
