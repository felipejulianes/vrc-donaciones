# backend/mp_client.py
import os
import uuid
import json   # <-- faltaba este import
import httpx

MP_API = "https://api.mercadopago.com"
ACCESS_TOKEN = os.environ["MP_ACCESS_TOKEN"]

def _headers(extra=None):
    h = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if extra:
        h.update(extra)
    return h

def _raise_with_body(resp: httpx.Response):
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    # Levanto una RuntimeError con info clara para que main.py la capture
    msg = f"MP {resp.status_code} {resp.request.method} {resp.request.url} -> {json.dumps(body, ensure_ascii=False)}"
    raise RuntimeError(msg)

def mp_post(path, json_payload, idem=True):
    headers = _headers({"X-Idempotency-Key": str(uuid.uuid4())} if idem else None)
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{MP_API}{path}", json=json_payload, headers=headers)
        if r.status_code >= 400:
            _raise_with_body(r)
        return r.json()

def mp_get(path, params=None):
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{MP_API}{path}", params=params, headers=_headers())
        if r.status_code >= 400:
            _raise_with_body(r)
        return r.json()


def mp_put(path, json_payload, idem=True):
    headers = _headers({"X-Idempotency-Key": str(uuid.uuid4())} if idem else None)
    with httpx.Client(timeout=30) as c:
        r = c.put(f"{MP_API}{path}", json=json_payload, headers=headers)
        if r.status_code >= 400:
            _raise_with_body(r)
        return r.json()
