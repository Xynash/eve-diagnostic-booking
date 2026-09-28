from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    centre_test_id: int
    appointment_time: datetime


class BookingOut(BaseModel):
    id: int
    user_id: int
    centre_test_id: int
    appointment_time: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)