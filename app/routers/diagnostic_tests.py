from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.test import Test
from app.schemas.centre import TestCreate, TestOut

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("/", response_model=list[TestOut])
def list_tests(db: Session = Depends(get_db)):
    return db.query(Test).all()


@router.post(
    "/",
    response_model=TestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def create_test(payload: TestCreate, db: Session = Depends(get_db)):
    test = Test(name=payload.name)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test
