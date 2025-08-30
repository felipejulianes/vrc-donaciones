import os, uuid, httpx

MP_API = "https://api.mercadopago.com"
ACCESS_TOKEN = os.environ["MP_ACCESS_TOKEN"]

def _headers(extra=None):
    h = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h

def mp_post(path, json, idem=True):
    headers = _headers({"X-Idempotency-Key": str(uuid.uuid4())} if idem else None)
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{MP_API}{path}", json=json, headers=headers)
        r.raise_for_status()
        return r.json()

def mp_get(path, params=None):
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{MP_API}{path}", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()

def mp_put(path, json, idem=True):
    headers = _headers({"X-Idempotency-Key": str(uuid.uuid4())} if idem else None)
    with httpx.Client(timeout=30) as c:
        r = c.put(f"{MP_API}{path}", json=json, headers=headers)
        r.raise_for_status()
        return r.json()
