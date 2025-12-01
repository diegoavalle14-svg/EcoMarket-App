from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database.connection import database
from app.database.tables import users
from app.utils.security import require_admin, hash_password
from app.utils.points import add_points

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# GET /register → muestra formulario HTML
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# POST /register-form → procesa formulario de registro
@router.post("/register-form")
@router.post("/register")
async def register_form(
    fullname: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...)
):
    if password != confirmPassword:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    # Validar duplicados
    if await database.fetch_one(users.select().where(users.c.usuario == username)):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if await database.fetch_one(users.select().where(users.c.email == email)):
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    # Guardar usuario y obtener id
    user_id = await database.execute(
        users.insert().values(
            nombre_completo=fullname,
            usuario=username,
            email=email,
            password=hash_password(password),
            role="user",
        )
    )

    # ➕ Puntos por registro
    await add_points(user_id, 20, "Registro de cuenta", "registro")

    return RedirectResponse(url="/auth/login", status_code=303)


# ====== ADMIN: CRUD USUARIOS ======

@router.get("/admin/users")
async def admin_list_users(admin=Depends(require_admin)):
    query = users.select().order_by(users.c.id.desc())
    result = await database.fetch_all(query)
    return [dict(r) for r in result]


@router.post("/admin/users")
async def admin_create_user(
    request: Request,
    nombre_completo: str = Form(...),
    usuario: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    admin=Depends(require_admin),
):
    # Validar duplicados
    if await database.fetch_one(users.select().where(users.c.usuario == usuario)):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if await database.fetch_one(users.select().where(users.c.email == email)):
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    await database.execute(
        users.insert().values(
            nombre_completo=nombre_completo,
            usuario=usuario,
            email=email,
            password=hash_password(password),
            role=role,
        )
    )
    return {"ok": True}


@router.post("/admin/users/{user_id}")
async def admin_update_user(
    user_id: int,
    nombre_completo: str = Form(...),
    usuario: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    password: str = Form(""),
    admin=Depends(require_admin),
):
    # Comprobar que existe
    existing = await database.fetch_one(users.select().where(users.c.id == user_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    valores = {
        "nombre_completo": nombre_completo,
        "usuario": usuario,
        "email": email,
        "role": role,
    }
    if password.strip():
        valores["password"] = hash_password(password)

    # Validar duplicados (usuario/email de otros ids)
    if await database.fetch_one(
        users.select().where(users.c.usuario == usuario, users.c.id != user_id)
    ):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if await database.fetch_one(
        users.select().where(users.c.email == email, users.c.id != user_id)
    ):
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    await database.execute(
        users.update().where(users.c.id == user_id).values(**valores)
    )
    return {"ok": True}


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin=Depends(require_admin)):
    await database.execute(users.delete().where(users.c.id == user_id))
    return {"ok": True}
