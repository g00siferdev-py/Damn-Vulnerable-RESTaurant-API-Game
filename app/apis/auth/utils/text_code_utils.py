import secrets
from datetime import datetime, timedelta

from db.models import User
from sqlalchemy.orm import Session

from .utils import send_code_to_phone_number


def generate_and_send_code_to_user(user: User, db: Session):
    # Use a long enough PIN and short enough expiry to defeat brute-force.
    # 4 digits can be guessed in ~10k attempts; 8 digits raises that to
    # 100 million and the code expires after 10 minutes.
    user.reset_password_code = "".join([str(secrets.randbelow(10)) for _ in range(8)])
    user.reset_password_code_expiry_date = datetime.now() + timedelta(minutes=10)
    db.add(user)
    db.commit()

    success = send_code_to_phone_number(user.phone_number, user.reset_password_code)
    return success
