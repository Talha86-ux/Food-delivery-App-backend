from pydantic import BaseModel
from typing import Optional

class SignUp(BaseModel):
    id: Optional[int]
    username: str
    email: str
    password: str
    is_staff: Optional[bool] = False
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "string",
                "email": "string",
                "password": "string",
                "is_staff": True,
                "is_active": True
            }
        }

class Login(BaseModel):
    username: str
    password: str

class Order(BaseModel):
    id: Optional[int]
    quantity: int
    order_status: Optional[str] = 'PENDING'
    pizza_size: Optional[str] = 'SMALL'
    user_id: Optional[int]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "quantity": 1,
                "order_status": "PENDING",
                "pizza_size": "SMALL",
            }
        }