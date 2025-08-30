from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any

class AutoRecurring(BaseModel):
    currency_id: str = Field(..., description="ARS/BRL/MXN/etc.")
    transaction_amount: float
    frequency: int = 1
    frequency_type: str = Field(..., description="'days' o 'months'")
    start_date: Optional[str] = None  # ISO 8601 opcional
    end_date: Optional[str] = None    # ISO 8601 opcional
    free_trial: Optional[Dict[str, Any]] = None  # {"frequency": 1, "frequency_type": "months"}

class SubscriptionCreateNoPlan(BaseModel):
    payer_email: EmailStr
    reason: str
    auto_recurring: AutoRecurring
    back_url: Optional[str] = None
    external_reference: Optional[str] = None
    card_token_id: Optional[str] = None  # opcional si usás tokenización

class SubscriptionUpdate(BaseModel):
    status: Optional[str] = Field(None, description="authorized|paused|cancelled")
    card_token_id: Optional[str] = None
    payer_email: Optional[EmailStr] = None
    back_url: Optional[str] = None
    reason: Optional[str] = None
    external_reference: Optional[str] = None
    auto_recurring: Optional[AutoRecurring] = None
