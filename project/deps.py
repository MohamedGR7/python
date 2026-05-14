from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .auth import decode_token
from .models import User
from .logger_config import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)

    if not payload:
        logger.warning("Invalid token validation attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    username = payload.get("sub")

    if not username:
        logger.warning("Token missing subject")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.username == username).first()

    if not user:
        logger.warning(f"Token user not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    logger.debug(f"Token validated for user: {user.username}")
    return user


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        logger.warning(f"Admin access denied for user: {current_user.username}")
        raise HTTPException(status_code=403, detail="Admin only")

    return current_user


def require_student(current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        logger.warning(f"Student access denied for user: {current_user.username}")
        raise HTTPException(status_code=403, detail="Students only")

    return current_user