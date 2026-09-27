from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.booking import Booking, BookingStatus
from app.models.centre_test import CentreTest
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre_test = db.query(CentreTest).filter(CentreTest.id == payload.centre_test_id).first()
    if not centre_test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found at this centre")

    booking = Booking(
        user_id=current_user.id,
        centre_test_id=centre_test.id,
        appointment_time=payload.appointment_time,
        amount=centre_test.price,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/", response_model=list[BookingOut])
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Booking).filter(Booking.user_id == current_user.id).all()


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this booking")
    if booking.status == BookingStatus.CONFIRMED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a confirmed booking")

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking