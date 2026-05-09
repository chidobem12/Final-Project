from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Any

SECRET_KEY = "super-secret-aegis-key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
REVOKED_TOKENS: set[str] = set()

USERS = {
    "analyst@keystone.bank": {
        "password": pwd_context.hash("aegis2026"),
        "role": "analyst",
        "name": "SOC Analyst"
    },
    "admin@keystone.bank": {
        "password": pwd_context.hash("aegisadmin"),
        "role": "admin",
        "name": "Security Administrator"
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def revoke_token(token: str) -> None:
    REVOKED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    return token in REVOKED_TOKENS
