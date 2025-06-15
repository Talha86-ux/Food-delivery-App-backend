from fastapi import APIRouter

order_router = APIRouter(
    prefix="/order",
)

@order_router.get("/")
async def say_hello():
    return {"message": "Hello, World!"} 