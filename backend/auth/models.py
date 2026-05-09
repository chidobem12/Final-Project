from pydantic import BaseModel
from typing import Literal

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    name: str
    email: str
    role: Literal["analyst", "admin"]

class TokenResponse(BaseModel):
    token: str
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str
