from fastapi import APIRouter, HTTPException, status, Depends
from database import Session, engine
from schemas import SignUp, Login
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi.encoders import jsonable_encoder
from fastapi_jwt import JwtAccessBearer, JwtRefreshBearer, JwtAuthorizationCredentials

session = Session(bind=engine)
auth_router = APIRouter(prefix="/auth", tags=["auth"])

access_security = JwtAccessBearer(secret_key="56aed5db5786fd49d7321695fe57dc666627374e42cb3ef3d67466dd7f515c4f")
refresh_security = JwtRefreshBearer(secret_key="56aed5db5786fd49d7321695fe57dc666627374e42cb3ef3d67466dd7f515c4f")

@auth_router.get("/")
async def say_hello(credentials: JwtAuthorizationCredentials = Depends(access_security)):
    try:
        return {"message": "Hello, World!"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@auth_router.post('/signup')
async def signup(user: SignUp, status_code=status.HTTP_201_CREATED):
    if session.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already in use")
    if session.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already in use")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=generate_password_hash(user.password),
        is_staff=user.is_staff,
        is_active=user.is_active
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@auth_router.post('/login', status_code=status.HTTP_200_OK)
async def login(user: Login):
    db_user = session.query(User).filter(User.username == user.username).first()
    if db_user and check_password_hash(db_user.hashed_password, user.password):
        access_token = access_security.create_access_token(subject={"sub": db_user.username})
        refresh_token = refresh_security.create_refresh_token(subject={"sub": db_user.username})
        return jsonable_encoder({"access_token": access_token, "refresh_token": refresh_token})
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password")


#refreshing token
@auth_router.get('/refresh')
async def refresh_token(credentials: JwtAuthorizationCredentials = Depends(refresh_security)):
    try:
        user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    access_token = access_security.create_access_token(subject={"sub": user})
    return jsonable_encoder({"access_token": access_token})
