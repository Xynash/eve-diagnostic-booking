from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.centre import Centre
from app.models.centre_test import CentreTest
from app.schemas.centre import CentreOut

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