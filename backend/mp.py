import httpx
import os

MP_API = "https://api.mercadopago.com"
ACCESS_TOKEN = os.environ["MP_ACCESS_TOKEN"]

def mp_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

async def create_subscription(payload: dict) -> dict:
    url = f"{MP_API}/preapproval"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=mp_headers(), json=payload)
        r.raise_for_status()
        return r.json()

async def get_subscription(preapproval_id: str) -> dict:
    url = f"{MP_API}/preapproval/{preapproval_id}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=mp_headers())
        r.raise_for_status()
        return r.json()

async def update_subscription(preapproval_id: str, payload: dict) -> dict:
    url = f"{MP_API}/preapproval/{preapproval_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.put(url, headers=mp_headers(), json=payload)
        r.raise_for_status()
        return r.json()

async def search_subscriptions(filters: dict) -> dict:
    # Ej: {"payer_email":"foo@bar.com", "status":"authorized"}
    url = f"{MP_API}/preapproval/search"
    async with httpx.AsyncClient(timeout=30, params=filters) as client:
        r = await client.get(url, headers=mp_headers())
        r.raise_for_status()
        return r.json()
