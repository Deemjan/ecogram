from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException
from jose import JWTError, jwt

from db.crud import *
from db.dispatcher import get_session
from settings import HASH_ALG, HASH_SECRET_KEY
from db.base_models import TokenData, UserCreate
from src.views.security import get_password_hash, create_access_token, verify_password

auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
logger = logging.getLogger(__name__)


async def get_current_user(session: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, HASH_SECRET_KEY, algorithms=[HASH_ALG])
        phone: str = payload.get("sub")
        exp = payload.get("exp")
        logger.debug(f"current user phone: {phone}")
        if not phone:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token_data = TokenData(phone=phone, expires=exp)
        logger.debug(f"token_data: {token_data}")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = await get_user(session, phone=token_data.phone)
    if user:
        return user
    if any([user is None, exp is None, datetime.utcnow() > token_data.expires]):
        logger.debug(f"{user}, {exp}, {datetime.utcnow() > token_data.expires}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


@auth_router.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    phone = form_data.username
    password = form_data.password
    user = await auth_user(session, phone=phone, password=password)
    if user is None:
        raise InvalidCredentialsException
    access_token = create_access_token(data={"sub": phone})
    return {"access_token": access_token, "token_type": "bearer"}


async def auth_user(session: AsyncSession, phone: str, password: str):
    user = await get_user(session, phone=phone)
    logger.debug(user)
    if user and verify_password(password, user.password):
        return user


@auth_router.post("/register")
async def register(create_data: UserCreate,
                   session: AsyncSession = Depends(get_session)):
    user = await get_user(session, phone=create_data.phone_number)
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    create_data.password = get_password_hash(create_data.password)
    user = await create_user(session, create_data)
    if not user:
        raise HTTPException(status_code=500, detail="Couldn't create user")
    return JSONResponse(status_code=201, content="Created")
