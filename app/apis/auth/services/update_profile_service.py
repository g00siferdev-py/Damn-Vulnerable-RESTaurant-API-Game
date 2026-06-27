from typing import Union

from apis.auth.utils import get_current_user, get_user_by_username
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


class UserUpdate(BaseModel):
    username: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    phone_number: Union[str, None] = None


@router.put("/profile", response_model=UserUpdate, status_code=status.HTTP_200_OK)
def update_profile(
    user: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    # Users may only update their own profile.
    if user.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    db_user = get_user_by_username(db, user.username)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Only allow a safelist of editable profile fields.
    allowed_fields = {"first_name", "last_name", "phone_number"}
    for var, value in user.dict().items():
        if var not in allowed_fields:
            continue
        setattr(db_user, var, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
