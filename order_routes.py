from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from database import AsyncSessionLocal
from fastapi.encoders import jsonable_encoder
from schemas import Order as OrderSchema, OrderStatusModel, OrderCreate
from models import Order as OrderModel, User


order_router = APIRouter(prefix="/order")


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


token_validator = JwtAccessBearer(secret_key="56aed5db5786fd49d7321695fe57dc666627374e42cb3ef3d67466dd7f515c4f")


@order_router.get("/")
async def say_hello(credentials: JwtAuthorizationCredentials = Depends(token_validator)):
    user = credentials.subject["sub"]
    return {"message": f"Hello, {user}!"}


@order_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    current_user = credentials.subject["sub"]
    result = await db.execute(select(User).filter_by(username=current_user))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_order = OrderModel(
        quantity=order.quantity,
        pizza_size=order.pizza_size,
        user_id=user.id
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    response = {
        "id": new_order.id,
        "quantity": new_order.quantity,
        "pizza_size": new_order.pizza_size,
        "order_status": new_order.order_status,
    }
    return jsonable_encoder(response)


@order_router.get("/orders", status_code=status.HTTP_200_OK)
async def get_orders_list(credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    current_user = credentials.subject["sub"]
    result = await db.execute(select(User).filter_by(username=current_user))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_staff:
        result = await db.execute(select(OrderModel))
    else:
        result = await db.execute(select(OrderModel).filter_by(user_id=user.id))

    orders = result.scalars().all()
    return jsonable_encoder(orders)


@order_router.get("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def get_order_by_id(order_id: int, credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    current_user = credentials.subject["sub"]
    result = await db.execute(select(User).filter_by(username=current_user))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query = select(OrderModel).filter_by(id=order_id)
    if not user.is_staff:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return jsonable_encoder(order)


@order_router.get("/user/orders", status_code=status.HTTP_200_OK)
async def get_user_orders(credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    current_user = credentials.subject["sub"]
    result = await db.execute(select(User).filter_by(username=current_user))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return jsonable_encoder(user.orders)


@order_router.get("/user/orders/{order_id}", status_code=status.HTTP_200_OK)
async def get_user_order_by_id(order_id: int, credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    current_user = credentials.subject["sub"]
    result = await db.execute(select(User).filter_by(username=current_user))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders = user.orders
    for order in orders:
        if order.id == order_id:
            return jsonable_encoder(order)

    raise HTTPException(status_code=404, detail="Order not found")


@order_router.put("/order/update/{id}", status_code=status.HTTP_200_OK)
async def update_order(id: int, order: OrderSchema, credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OrderModel).filter_by(id=id))
    order_to_update = result.scalar_one_or_none()

    if not order_to_update:
        raise HTTPException(status_code=404, detail="Order not found")

    order_to_update.quantity = order.quantity
    order_to_update.pizza_size = order.pizza_size

    await db.commit()
    await db.refresh(order_to_update)

    return jsonable_encoder(order_to_update)


@order_router.patch("/order/update/{id}", status_code=status.HTTP_200_OK)
async def update_order_status(id: int, order: OrderStatusModel, credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    current_user = credentials.subject["sub"]
    result = await db.execute(select(User).filter_by(username=current_user))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_staff:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(OrderModel).filter_by(id=id))
    order_to_update = result.scalar_one_or_none()

    if not order_to_update:
        raise HTTPException(status_code=404, detail="Order not found")

    order_to_update.order_status = order.order_status
    await db.commit()
    await db.refresh(order_to_update)

    response = {
        "message": "Order status updated successfully",
        "order": {
            "id": order_to_update.id,
            "quantity": order_to_update.quantity,
            "order_status": order_to_update.order_status,
            "pizza_size": order_to_update.pizza_size
        }
    }
    return jsonable_encoder(response)


@order_router.delete("/order/delete/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(id: int, credentials: JwtAuthorizationCredentials = Depends(token_validator), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OrderModel).filter_by(id=id))
    order_to_delete = result.scalar_one_or_none()

    if not order_to_delete:
        raise HTTPException(status_code=404, detail="Order not found")

    await db.delete(order_to_delete)
    await db.commit()
    return {"message": "Order deleted successfully"}
