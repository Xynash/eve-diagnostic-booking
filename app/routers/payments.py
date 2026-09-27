import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.models.webhook_event import WebhookEvent
from app.schemas.payment import PaymentCreate, PaymentOut
from app.schemas.webhook import PaymentWebhookPayload

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def process_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == payload.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to pay for this booking")

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking is not payable in its current status: {booking.status.value}",
        )

    success = random.random() < 0.8

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=PaymentStatus.SUCCESS if success else PaymentStatus.FAILED,
        transaction_id=str(uuid.uuid4()),
    )
    db.add(payment)

    booking.status = BookingStatus.CONFIRMED if success else BookingStatus.FAILED
    db.commit()
    db.refresh(payment)

    return payment


@router.post("/webhook/", status_code=status.HTTP_200_OK)
def payment_webhook(payload: PaymentWebhookPayload, db: Session = Depends(get_db)):
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == payload.event_id).first()
    if existing_event:
        return {"detail": "Event already processed", "event_id": payload.event_id}

    payment = db.query(Payment).filter(Payment.transaction_id == payload.transaction_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found for this transaction")

    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found for this payment")

    payment.status = payload.status
    booking.status = BookingStatus.CONFIRMED if payload.status == PaymentStatus.SUCCESS else BookingStatus.FAILED

    webhook_event = WebhookEvent(event_id=payload.event_id, payload=payload.model_dump_json())
    db.add(webhook_event)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"detail": "Event already processed", "event_id": payload.event_id}

    return {"detail": "Webhook processed", "booking_status": booking.status.value}