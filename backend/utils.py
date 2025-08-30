import hmac, hashlib, base64, os
from typing import Optional

WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET")

def verify_signature(x_signature: Optional[str], x_request_id: Optional[str], data_id: str) -> bool:
    """
    Validación HMAC para webhooks MP con 'x-signature' y 'x-request-id'.
    Esquema típicamente documentado:
      manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
      v1 = base64(HMAC_SHA256(secret, manifest))
    x-signature suele venir "ts=...,v1=...".
    """
    if not (WEBHOOK_SECRET and x_signature and x_request_id and data_id):
        return False
    try:
        parts = dict([kv.strip().split("=", 1) for kv in x_signature.split(",") if "=" in kv])
        ts = parts.get("ts"); v1 = parts.get("v1")
        if not ts or not v1:
            return False
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};".encode("utf-8")
        digest = hmac.new(WEBHOOK_SECRET.encode("utf-8"), manifest, hashlib.sha256).digest()
        expected = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, v1)
    except Exception:
        return False
