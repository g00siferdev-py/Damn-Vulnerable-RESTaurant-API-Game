import secrets
import string

from apis.auth.utils import RolesBasedAuthChecker, get_current_user
from apis.auth.utils.utils import update_user_password
from config import settings
from db.models import User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


# this is a highly sensitive endpoint used only for admin purposes
# it's excluded from the docs to make it more secure
@router.get(
    "/admin/reset-chef-password",
    include_in_schema=False,
    status_code=status.HTTP_200_OK,
)
def get_reset_chef_password(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    auth=Depends(RolesBasedAuthChecker([UserRole.CHEF])),
):
    # The old implementation trusted request.client.host, which is trivially
    # spoofable via X-Forwarded-For. Require a valid Chef token instead.
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_-+=;:[]"

    # generate a random password
    new_password = "".join(secrets.choice(characters) for i in range(32))
    update_user_password(db, settings.CHEF_USERNAME, new_password)

    return {"password": new_password}
