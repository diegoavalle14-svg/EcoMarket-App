from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel, EmailStr
from app.database.connection import database
from app.database.tables import users
from app.utils.security import hash_password, verify_password

router = APIRouter(
    prefix="/api/users",
    tags=["Usuarios"]
)

# -------------------------------
# MODELOS Pydantic
# -------------------------------
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str | None = None

class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: EmailStr

# -------------------------------
# CREAR USUARIO
# -------------------------------
@router.post("/", response_model=dict)
async def create_user(user: UserCreate):
    # Verificar duplicados
    if await database.fetch_one(users.select().where(users.c.username == user.username)):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if await database.fetch_one(users.select().where(users.c.email == user.email)):
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    query = users.insert().values(
        first_name=user.first_name.strip(),
        last_name=user.last_name.strip(),
        username=user.username.strip(),
        email=user.email.strip(),
        password=hash_password(user.password)
    )
    await database.execute(query)
    return {"status": "success", "message": "Usuario agregado"}

# -------------------------------
# LISTAR USUARIOS
# -------------------------------
@router.get("/", response_model=list[UserOut])
async def list_users():
    result = await database.fetch_all(users.select())
    return [dict(r) for r in result]

# -------------------------------
# OBTENER USUARIO POR ID
# -------------------------------
@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    user = await database.fetch_one(users.select().where(users.c.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user)

# -------------------------------
# ACTUALIZAR USUARIO
# -------------------------------
@router.put("/{user_id}", response_model=dict)
async def update_user(user_id: int, user: UserUpdate):
    db_user = await database.fetch_one(users.select().where(users.c.id == user_id))
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    values = {
        "first_name": user.first_name.strip(),
        "last_name": user.last_name.strip(),
        "username": user.username.strip(),
        "email": user.email.strip()
    }
    if user.password:
        values["password"] = hash_password(user.password)

    query = users.update().where(users.c.id == user_id).values(**values)
    await database.execute(query)
    return {"status": "success", "message": "Usuario actualizado"}

# -------------------------------
# ELIMINAR USUARIO
# -------------------------------
@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: int):
    db_user = await database.fetch_one(users.select().where(users.c.id == user_id))
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {"status": "success", "message": "Usuario eliminado"}
