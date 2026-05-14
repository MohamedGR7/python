
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, AdminCreate, Token
from ..auth import hash_password, verify_password, create_access_token
from ..logger_config import logger

router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()

ADMIN_SECRET = os.getenv("ADMIN_SECRET","number one")

if not ADMIN_SECRET:
    raise RuntimeError("ADMIN_SECRET is missing. Add it to your .env file.")


@router.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    old_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()

    if old_user:
        logger.warning(f"Duplicate registration attempt: {user.username}")
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role="student"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New student registered: {new_user.username}")
    return {"message": "Student registered successfully"}


@router.post("/register-admin", status_code=201)
def register_admin(user: AdminCreate, db: Session = Depends(get_db)):
    if user.admin_secret != ADMIN_SECRET:
        logger.warning(f"Invalid admin secret used for: {user.username}")
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    old_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()

    if old_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    new_admin = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role="admin"
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    logger.info(f"New admin registered: {new_admin.username}")
    return {"message": "Admin registered successfully"}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token({
        "sub": user.username,
        "role": user.role
    })

    logger.info(f"User logged in: {user.username}")

    return {
        "access_token": token,
        "token_type": "bearer"
    }