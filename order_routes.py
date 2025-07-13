from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from database import Session, engine
from fastapi.encoders import jsonable_encoder
from schemas import Order as OrderSchema, OrderStatusModel, OrderCreate
from models import Order as OrderModel, User


order_router = APIRouter(
    prefix="/order",
)

session = Session(bind=engine)
token_validator = JwtAccessBearer(secret_key="56aed5db5786fd49d7321695fe57dc666627374e42cb3ef3d67466dd7f515c4f")

@order_router.get("/")
async def say_hello(credentials: JwtAccessBearer = Depends()):
    """
    A simple endpoint that greets the authenticated user.

    Args:
        credentials (JwtAccessBearer): The JWT access token.

    Returns:
        A JSON response with a greeting message.

    Raises:
        HTTPException: 401 if token is invalid.
    """
    try:
        user = credentials.subject["sub"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    return {"message": f"Hello, {user}!"}

@order_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, credentials: JwtAuthorizationCredentials = Depends(token_validator)):
    """
    Create an order.

    Args:
        order (OrderSchema): The order data.
        credentials (JwtAccessBearer): The JWT access token.

    Returns:
        A JSON response with the order details.

    Raises:
        HTTPException: 401 if token is invalid, 404 if user is not found.
    """
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
    """
    Retrieve a list of orders. Staff users can retrieve all orders, while normal users can only retrieve their own orders.

    Args:
        credentials: The JWT access token.

    Returns:
        A JSON response with a list of orders if found.

    Raises:
        HTTPException: 401 if token is invalid, 404 if user is not found.
    """
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

@order_router.get("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def get_order_by_id(order_id: int, credentials: JwtAccessBearer = Depends(token_validator)):
    """
    Retrieve an order by its ID.

    Args:
        order_id: The ID of the order to retrieve.
        credentials: The JWT access token.

    Returns:
        A JSON response with the order details if found.

    Raises:
        HTTPException: 401 if token is invalid or user is unauthorized, 404 if user or order is not found.
    """

    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = session.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.is_staff:
        order = session.query(OrderModel).get(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return jsonable_encoder(order)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

@order_router.get("/user/orders", status_code=status.HTTP_200_OK)
async def get_user_orders(credentials: JwtAccessBearer = Depends(token_validator)):
    """
    Retrieve a list of orders made by the currently authenticated user.

    Args:
        credentials: The JWT access token.

    Returns:
        A JSON response with a list of orders if found.

    Raises:
        HTTPException: 401 if token is invalid or user is unauthorized, 404 if user is not found.
    """
    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = session.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return jsonable_encoder(user.orders)

@order_router.get("/user/orders/{order_id}", status_code=status.HTTP_200_OK)
async def get_user_order_by_id(order_id: int, credentials: JwtAccessBearer = Depends(token_validator)):
    """
    Retrieve an order made by the currently authenticated user by its ID.

    Args:
        order_id: The ID of the order to retrieve.
        credentials: The JWT access token.

    Returns:
        A JSON response with the order details if found.

    Raises:
        HTTPException: 401 if token is invalid or user is unauthorized, 404 if user or order is not found.
    """
    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = session.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    orders = user.orders
    for order in orders:
        if order.id == order_id:
            return jsonable_encoder(order)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
@order_router.put("/order/update/{id}", status_code=status.HTTP_200_OK)
async def update_order(id: int, order: OrderSchema, credentials: JwtAccessBearer = Depends(token_validator)):
    """
    Update an order.

    Args:
        id: The ID of the order to update.
        order: The updated order data.
        credentials: The JWT access token.

    Returns:
        A JSON response with a success message and the updated order.

    Raises:
        HTTPException: 401 if token is invalid, 404 if order not found.
    """
    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    order_to_update = session.query(OrderModel).filter(OrderModel.id == id).first()
    if not order_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order_to_update.quantity = order.quantity
    order_to_update.pizza_size = order.pizza_size
    session.commit()
    session.refresh(order_to_update)
    return jsonable_encoder(order_to_update)

@order_router.patch("/order/update/{id}", status_code=status.HTTP_200_OK)
async def update_order_status(id: int, order: OrderStatusModel, credentials: JwtAccessBearer = Depends(token_validator)):
    """
    Update an order status.

    Args:
        id: The ID of the order to update.
        order: The updated order status.
        credentials: The JWT access token.

    Returns:
        A JSON response with a success message and the updated order.

    Raises:
        HTTPException: 401 if token is invalid, 404 if order not found.
    """
    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    username = credentials.sub["sub"]
    current_user = session.query(User).filter(User.username == username).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if current_user.is_staff:
        order_to_update = session.query(OrderModel).filter(OrderModel.id == id).first()
        if not order_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        order_to_update.order_status = order.order_status
        session.commit()
        session.refresh(order_to_update)
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
async def delete_orderf(id: int, credentials: JwtAccessBearer = Depends(token_validator)):
    """
    Delete an order by ID.

    Args:
        id: The ID of the order to delete.
        credentials: The JWT access token.

    Returns:
        A JSON response with the deleted order and a success message.

    Raises:
        HTTPException: 401 if token is invalid, 404 if order not found.
    """
    try:
        current_user = credentials.subject["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    order_to_delete = session.query(OrderModel).filter(OrderModel.id == id).first()
    if not order_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    session.delete(order_to_delete)
    session.commit()
    return {"order": order_to_delete, "message": "Order deleted successfully"}