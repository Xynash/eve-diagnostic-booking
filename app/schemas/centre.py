from decimal import Decimal

from pydantic import BaseModel


class TestOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CentreTestOut(BaseModel):
    id: int
    price: Decimal
    test: TestOut

    class Config:
        from_attributes = True


class CentreOut(BaseModel):
    id: int
    name: str
    location: str
    tests: list[CentreTestOut] = []

    class Config:
        from_attributes = True