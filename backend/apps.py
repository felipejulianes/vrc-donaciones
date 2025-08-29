import hmac, hashlib, base64, os, json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
from mp import create_subscription, get_subscription, update_subscription, search_subscriptions

load_dotenv()
app = FastAPI()

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET")

class InitSubscriptionIn(BaseModel):
    amount: float = Field(gt=0, description="Monto en ARS")
    email: EmailStr
    donor_name: str | None = None
    ambassador: str | None = None
    # Por defecto mensual
    frequency: int = 1
    frequency_type: str = "months"  # "months" | "days"
    reason: str = "Virreyes Rugby Club - Aporte mensual"

class UpdateAmountIn(BaseModel):
    amount: float = Field(gt=0)

@app.post("/api/subscriptions/initiate")
async def initiate_subscription(data: InitSubscriptionIn):
    # Armamos la suscripción SIN plan (se crea un link para que el donante autorice)
    payload = {
        "reason": data.reason,
        "payer_email": data.email,
        "back_url": f"{BASE_URL}/gracias.html",
        "external_reference": json.dumps({
            "ambassador": data.ambassador,
            "donor_name": data.donor_name
        }),
        "auto_recurring": {
            "currency_id": "ARS",
            "transaction_amount": round(data.amount, 2),
            "frequency": data.frequency,
            "frequency_type": data.frequency_type
        },
        # tip: podés setear start_date si querés diferir el primer cobro
    }
    try:
        sub = await create_subscription(payload)
        # MP devuelve init_point para redirigir al flujo de autorización
        return {
            "preapproval_id": sub.get("id"),
            "init_point": sub.get("init_point"),
            "status": sub.get("status")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/subscriptions/{preapproval_id}")
async def get_sub(preapproval_id: str):
    try:
        return await get_subscription(preapproval_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/api/subscriptions/{preapproval_id}/amount")
async def update_amount(preapproval_id: str, body: UpdateAmountIn):
    # Para cambios masivos podés usar /preapproval/search y luego iterar este PUT
    try:
        payload = {
            "auto_recurring": {
                "transaction_amount": round(body.amount, 2),
                "currency_id": "ARS"
            }
        }
        return await update_subscription(preapproval_id, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/subscriptions")
async def search(email: str | None = None, status: str | None = None, ambassador: str | None = None, limit: int = 50, offset: int = 0):
    # MP admite varios filtros; incluimos ambassador usando external_reference (busca substring)
    filters = {"limit": str(limit), "offset": str(offset)}
    if email: filters["payer_email"] = email
    if status: filters["status"] = status
    if ambassador: filters["external_reference"] = ambassador
    try:
        return await search_subscriptions(filters)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def verify_webhook(request_body: bytes, signature: str, request_id: str) -> bool:
    """
    Validación HMAC de webhooks (x-signature) según docs nuevas.
    Manifesto típico: "id:{id};request-id:{x-request-id};ts:{ts};"
    v1 = base64(HMAC_SHA256(secret, manifest))
    """
    if not WEBHOOK_SECRET or not signature or not request_id:
        return False

    parts = dict([p.strip().split("=", 1) for p in signature.split(",") if "=" in p])
    ts = parts.get("ts")
    v1 = parts.get("v1")
    if not ts or not v1:
        return False

    # Leemos el id de la notificación del body
    try:
        data = json.loads(request_body.decode("utf-8"))
        notif_id = str(data.get("data", {}).get("id", ""))  # puede ser pago o preapproval id
    except Exception:
        return False

    manifest = f"id:{notif_id};request-id:{request_id};ts:{ts};"
    digest = hmac.new(WEBHOOK_SECRET.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    # comparación tiempo-constante
    return hmac.compare_digest(expected, v1)

@app.post("/api/webhooks/mercadopago")
async def mercadopago_webhook(request: Request):
    raw = await request.body()
    x_sig = request.headers.get("x-signature")
    x_req = request.headers.get("x-request-id")
    if not verify_webhook(raw, x_sig, x_req):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = json.loads(raw.decode("utf-8"))
    # event["type"] puede ser "preapproval", "authorized_payment", etc.
    # Sugerencia: encolar a una cola (p.ej. Redis) y procesar async
    # Para MVP, log simple:
    print("Webhook OK:", event)

    # TODO: si type == "preapproval", hacer GET /preapproval/{id} y persistir estado
    # TODO: si type == "authorized_payment", leer info de cobro y reflejar en tu base

    return {"received": True}
