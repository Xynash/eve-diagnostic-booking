from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.centre import Centre
from app.models.centre_test import CentreTest
from app.models.test import Test
from app.schemas.centre import CentreCreate, CentreOut, CentreTestCreate, CentreTestOut

router = APIRouter(prefix="/centres", tags=["centres"])


@router.get("/", response_model=list[CentreOut])
def list_centres(db: Session = Depends(get_db)):
    return db.query(Centre).options(joinedload(Centre.tests).joinedload(CentreTest.test)).all()


@router.get("/{centre_id}", response_model=CentreOut)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = (
        db.query(Centre)
        .options(joinedload(Centre.tests).joinedload(CentreTest.test))
        .filter(Centre.id == centre_id)
        .first()
    )
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    return centre


@router.post(
    "/",
    response_model=CentreOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def create_centre(payload: CentreCreate, db: Session = Depends(get_db)):
    centre = Centre(name=payload.name, location=payload.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.post(
    "/{centre_id}/tests",
    response_model=CentreTestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def add_test_to_centre(centre_id: int, payload: CentreTestCreate, db: Session = Depends(get_db)):
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")

    test = db.query(Test).filter(Test.id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    existing = (
        db.query(CentreTest)
        .filter(CentreTest.centre_id == centre_id, CentreTest.test_id == payload.test_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Test already offered at this centre")

    link = CentreTest(centre_id=centre_id, test_id=payload.test_id, price=payload.price)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link
