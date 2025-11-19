from fastapi import Request, HTTPException, status, Depends
from app.database.connection import database
from app.database.tables import users

# ------------------------
# Obtener usuario desde cookies
# ------------------------
async def get_current_user(request: Request):
    username = request.cookies.get("user_name")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )

    user = await database.fetch_one(
        users.select().where(users.c.username == username)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    return user


# ------------------------
# Solo admin
# ------------------------
async def admin_required(request: Request):
    username = request.cookies.get("user_name")

    if not username:
        raise HTTPException(status_code=401, detail="No autenticado")

    user = await database.fetch_one(
        users.select().where(users.c.username == username)
    )

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado (solo admin)")

    return user
