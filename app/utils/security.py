from passlib.context import CryptContext
from fastapi import Request
from app.database.connection import database
from app.database.tables import users

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_PASSWORD_LENGTH = 72  # límite de bcrypt en caracteres


def hash_password(password: str) -> str:
    if len(password) > MAX_PASSWORD_LENGTH:
        password = password[:MAX_PASSWORD_LENGTH]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password) > MAX_PASSWORD_LENGTH:
        plain_password = plain_password[:MAX_PASSWORD_LENGTH]
    return pwd_context.verify(plain_password, hashed_password)


class RequiresLogin(Exception):
    """Se lanza cuando la ruta requiere login y no hay usuario."""
    pass


async def get_current_user(request: Request):
    username = request.cookies.get("user_name")

    if not username or username == "None":
        return None

    query = users.select().where(users.c.usuario == username)
    user = await database.fetch_one(query)

    return user if user else None


async def require_login(request: Request):
    user = await get_current_user(request)
    if not user:
        raise RequiresLogin()
    return user


async def require_admin(request: Request):
    user = await get_current_user(request)
    if not user or user["role"] != "admin":
        raise RequiresLogin()
    return user
