from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import AsyncSessionLocal
from schemas import SignUp, Login
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi.encoders import jsonable_encoder
from fastapi_jwt import JwtAccessBearer, JwtRefreshBearer, JwtAuthorizationCredentials


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


auth_router = APIRouter(prefix="/auth", tags=["auth"])

access_security = JwtAccessBearer(secret_key="56aed5db5786fd49d7321695fe57dc666627374e42cb3ef3d67466dd7f515c4f")
refresh_security = JwtRefreshBearer(secret_key="56aed5db5786fd49d7321695fe57dc666627374e42cb3ef3d67466dd7f515c4f")


@auth_router.get("/")
async def say_hello(credentials: JwtAuthorizationCredentials = Depends(access_security)):
    user = credentials.subject["sub"]
    return {"message": f"Hello, {user}!"}


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: SignUp, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter_by(email=user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already in use")

    result = await db.execute(select(User).filter_by(username=user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already in use")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=generate_password_hash(user.password),
        is_staff=user.is_staff,
        is_active=user.is_active
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return jsonable_encoder({
        "username": new_user.username,
        "email": new_user.email,
        "is_staff": new_user.is_staff,
        "is_active": new_user.is_active
    })


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(user: Login, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter_by(username=user.username))
    db_user = result.scalar_one_or_none()

    if db_user and check_password_hash(db_user.hashed_password, user.password):
        access_token = access_security.create_access_token(subject={"sub": db_user.username})
        refresh_token = refresh_security.create_refresh_token(subject={"sub": db_user.username})
        return jsonable_encoder({"access_token": access_token, "refresh_token": refresh_token})

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password")


@auth_router.get("/refresh")
async def refresh_token(credentials: JwtAuthorizationCredentials = Depends(refresh_security)):
    user = credentials.subject["sub"]
    access_token = access_security.create_access_token(subject={"sub": user})
    return jsonable_encoder({"access_token": access_token})
