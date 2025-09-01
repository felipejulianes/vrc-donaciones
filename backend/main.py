import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import SubscriptionCreateNoPlan, SubscriptionUpdate
from mp_client import mp_post, mp_get, mp_put
from utils import verify_signature

load_dotenv()

app = FastAPI(title="VRC Suscripciones (auto_recurring)")

origins = (os.getenv("ALLOWED_ORIGINS") or "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Salud ----------
@app.get("/health")
def health():
    return {"ok": True}

# ---------- SUSCRIPCIONES (sin plan) ----------
@app.post("/subscriptions", summary="Crear suscripción (auto_recurring, sin plan)")
def create_subscription_no_plan(body: SubscriptionCreateNoPlan):
    # Armamos el payload que va a POST /preapproval
    payload = body.model_dump()

    # back_url por default si no viene desde el front
    if not payload.get("back_url"):
        base_url = os.getenv("BASE_URL", "")
        if base_url:
            payload["back_url"] = f"{base_url.rstrip('/')}/gracias.html"

    # Llamada a MP con manejo de errores (muestra el detalle real de MP)
    try:
        return mp_post("/preapproval", payload)
    except Exception as e:
        # Evita 500 y te devuelve el mensaje que vino de MP (qué campo falló, etc.)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/subscriptions/{preapproval_id}", summary="Obtener suscripción por ID")
def get_subscription(preapproval_id: str):
    return mp_get(f"/preapproval/{preapproval_id}")  # :contentReference[oaicite:3]{index=3}

@app.put("/subscriptions/{preapproval_id}", summary="Actualizar suscripción (monto/estado)")
def update_subscription(preapproval_id: str, body: SubscriptionUpdate):
    payload = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    return mp_put(f"/preapproval/{preapproval_id}", payload)  # :contentReference[oaicite:4]{index=4}

@app.get("/subscriptions", summary="Buscar suscripciones por email/status")
def search_subscriptions(email: str | None = None, status: str | None = None, limit: int = 50, offset: int = 0):
    params = {"limit": limit, "offset": offset}
    if email: params["payer_email"] = email
    if status: params["status"] = status
    return mp_get("/preapproval/search", params)  # :contentReference[oaicite:5]{index=5}

@app.get("/subscriptions/{preapproval_id}/payments", summary="Lista 'invoices' de la suscripción")
def list_subscription_payments(preapproval_id: str, status: str | None = None):
    params = {"preapproval_id": preapproval_id}
    if status: params["status"] = status
    return mp_get("/authorized_payments/search", params)  # :contentReference[oaicite:6]{index=6}

# ---------- WEBHOOKS ----------
@app.post("/webhooks/mp", summary="Webhook de Mercado Pago")
async def mp_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    body = await request.json()
    topic = body.get("type") or body.get("topic")
    data_id = (body.get("data") or {}).get("id")

    # Validar firma (si aplica) y SIEMPRE reconsultar por ID
    sig_ok = verify_signature(x_signature, x_request_id, str(data_id) if data_id else "")

    if topic == "preapproval" and data_id:
        sub = mp_get(f"/preapproval/{data_id}")  # reconsulta oficial
        # TODO: persistir sub en DB

    elif topic in {"authorized_payment", "invoice"} and data_id:
        # Detalle puntual de un cobro recurrente (invoice)
        # Puedes también usar /authorized_payments/search con preapproval_id
        # o /authorized_payments/{id} si el webhook trae ID puntual.
        # En varias docs aparece el search como recurso recomendado.
        # Acá usamos search para ilustrar:
        payments = mp_get("/authorized_payments/search", {"preapproval_id": data_id})
        # TODO: persistir cobro(s) en DB

    # Devolvé 200 si lo procesaste
    return {"received": True, "signature_ok": bool(sig_ok)}
