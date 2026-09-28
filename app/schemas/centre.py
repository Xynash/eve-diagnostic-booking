from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TestOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CentreTestOut(BaseModel):
    id: int
    price: Decimal
    test: TestOut

    model_config = ConfigDict(from_attributes=True)


class CentreOut(BaseModel):
    id: int
    name: str
    location: str
    tests: list[CentreTestOut] = []

    model_config = ConfigDict(from_attributes=True)