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