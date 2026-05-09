from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models import LoginRequest, LogoutResponse, TokenResponse, UserResponse
from .utils import USERS, verify_password, create_access_token, revoke_token, is_token_revoked
from jose import jwt, JWTError
from .utils import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, Any]:
    token = credentials.credentials
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Token has been invalidated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email not in USERS:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = USERS[email]
        return {"email": email, **user}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = USERS.get(req.email)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Authentication failed — invalid credentials")
    
    token = create_access_token(data={"sub": req.email, "role": user["role"]})
    return TokenResponse(
        token=token,
        user=UserResponse(name=user["name"], email=req.email, role=user["role"])
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        name=current_user["name"],
        email=current_user["email"],
        role=current_user["role"]
    )

@router.post("/logout", response_model=LogoutResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    revoke_token(credentials.credentials)
    return LogoutResponse(message="Logged out")
