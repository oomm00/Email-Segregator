from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.auth.jwt import create_token
from src.common.auth.password import hash_password, verify_password
from src.common.auth.schemas import RegisterRequest, LoginRequest, AuthResponse
from src.common.db.models import User
from src.common.db.session import get_db
from src.common.audit import log_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="email already registered")

    user = User(
        id=uuid4(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role="viewer",
    )
    db.add(user)
    await db.flush()

    await log_audit(db, "user.registered", "user", str(user.id), actor_id=user.id, payload={"email": user.email})

    token = create_token(str(user.id), {"role": user.role})
    return AuthResponse(token=token, user_id=user.id, email=user.email, name=user.name, role=user.role)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    if not user.is_active or user.is_deleted:
        raise HTTPException(status_code=401, detail="account disabled")

    await log_audit(db, "user.login", "user", str(user.id), actor_id=user.id)

    token = create_token(str(user.id), {"role": user.role})
    return AuthResponse(token=token, user_id=user.id, email=user.email, name=user.name, role=user.role)
