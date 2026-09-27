from pydantic import BaseModel

from app.models.payment import PaymentStatus


class PaymentWebhookPayload(BaseModel):
    event_id: str
    transaction_id: str
    status: PaymentStatus