from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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


class CentreCreate(BaseModel):
    name: str = Field(min_length=1)
    location: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class TestCreate(BaseModel):
    name: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class CentreTestCreate(BaseModel):
    test_id: int
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
