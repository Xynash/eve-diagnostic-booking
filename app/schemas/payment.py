from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: int


class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    status: PaymentStatus
    transaction_id: str
    created_at: datetime

    class Config:
        from_attributes = True