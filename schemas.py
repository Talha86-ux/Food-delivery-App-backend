from pydantic import BaseModel
from typing import Optional

class SignUp(BaseModel):
  id: Optional[int]
  username: str
  email: str
  password: str
  is_staff: Optional[bool] = bool
  is_active: Optional[bool] = bool

  class Config:
    orm_mode = True
    schema_extra = {
      "example": {
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