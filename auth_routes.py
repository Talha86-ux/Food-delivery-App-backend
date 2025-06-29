from fastapi import APIRouter
from database import Session, engine
from schemas import SignUp
from models import User
from fastapi import HTTPException, status
from werkzeug.security import generate_password_hash, check_password_hash

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

session=Session(bind=engine)

@auth_router.get("/")
async def say_hello():
    return {"message": "Hello, World!"} 

@auth_router.post('/signup')
async def signup(user: SignUp, status_code=status.HTTP_201_CREATED): 
    db_email = session.query(User).filter(User.email == user.email).first()
    if db_email is not None:
        raise HTTPException(status_code=400, detail="Email already in use")
    db_user = session.query(User).filter(User.username == user.username).first()
    if db_user is not None:
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