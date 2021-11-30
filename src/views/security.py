from datetime import timedelta, datetime
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from settings import HASH_SECRET_KEY, HASH_ALG

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, HASH_SECRET_KEY, algorithm=HASH_ALG)
    return encoded_jwt


def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)