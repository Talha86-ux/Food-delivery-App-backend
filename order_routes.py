from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt import JwtAccessBearer
from database import Session, engine
from fastapi.encoders import jsonable_encoder
from schemas import Order as OrderSchema  # Pydantic input schema
from models import Order as OrderModel, User  # SQLAlchemy models


order_router = APIRouter(
    prefix="/order",
)

session = Session(bind=engine)
token_validator = JwtAccessBearer(secret_key="56aed5db5786fd49d7321695fe57dc666627374e42cb3ef3d67466dd7f515c4f")

@order_router.get("/")
async def say_hello(credentials: JwtAccessBearer = Depends()):
    try:
        user = credentials.subject["sub"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    return {"message": f"Hello, {user}!"}

@order_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderSchema, credentials: JwtAccessBearer = Depends(token_validator)):
    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = session.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_order = OrderModel(
        quantity=order.quantity,
        pizza_size=order.pizza_size,
        user_id=user.id
    )

    session.add(new_order)
    session.commit()
    session.refresh(new_order)

    response = {
        "id": new_order.id,
        "quantity": new_order.quantity,
        "pizza_size": new_order.pizza_size,
        "order_status": new_order.order_status,
    }

    return jsonable_encoder(response)

@order_router.get("/orders", status_code=status.HTTP_200_OK)
async def get_orders_list(credentials: JwtAccessBearer = Depends(token_validator)):
    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = session.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.is_staff:
        orders = session.query(OrderModel).all
        return jsonable_encoder(orders)

    # orders = session.query(OrderModel).filter(OrderModel.user_id == user.id).all()
