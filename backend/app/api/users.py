from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.tokens import current_user
from app.db import get_db
from app.models import User
from app.schemas import UserOut, UserUpdate
from app.zones import profile_for_user

router = APIRouter(tags=["users"])


def user_out(user: User) -> UserOut:
    out = UserOut.model_validate(user)
    out.zones = profile_for_user(user).as_dict()
    return out


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(current_user)):
    return user_out(user)


@router.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_out(user)
