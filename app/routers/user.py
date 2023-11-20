from fastapi import APIRouter, Depends
from ..database import get_db
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from uuid import UUID

router = APIRouter()


@router.get('/me', response_model=schemas.UserResponse)
async def get_me(db: Session = Depends(get_db), user_id: str = Depends(oauth2.require_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user

@router.get('/{user_id}', response_model=schemas.UserResponse)
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user
