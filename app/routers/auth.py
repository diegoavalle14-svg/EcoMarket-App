from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from starlette.status import HTTP_303_SEE_OTHER

from app.database.connection import database
from app.database.tables import users, points_history
from app.utils.security import hash_password, verify_password
from app.utils.points import add_points

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="templates")


# -------------------------------
# Mostrar login
# -------------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -------------------------------
# Procesar login
# -------------------------------
@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    query = users.select().where(users.c.usuario == username)
    user = await database.fetch_one(query)

    if not user:
        return RedirectResponse(
            url="/auth/login?error=UsuarioNoExiste",
            status_code=HTTP_303_SEE_OTHER
        )
    
    if not verify_password(password, user["password"]):
        return RedirectResponse(
            url="/auth/login?error=ContraseñaIncorrecta",
            status_code=HTTP_303_SEE_OTHER
        )

# ➕ Puntos por login diario (+2 puntos si es su primer login del día)
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    last_login_today = await database.fetch_one(
        points_history.select().where(
            (points_history.c.user_id == user["id"]) &
            (points_history.c.motivo == "Login diario") &
            (points_history.c.fecha >= today_start)  # ← CAMBIO AQUÍ
        )
    )
    
    if not last_login_today:
        await add_points(user["id"], 2, "Login diario", "login")

    # Login exitoso → crear cookie
    redirect_url = "/menu" if user["role"] == "admin" else "/"

    response = RedirectResponse(url=redirect_url, status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
    response.set_cookie(key="user_name", value=user["usuario"], httponly=True)
    response.set_cookie(key="role", value=user["role"], httponly=True)
    return response


# -------------------------------
# Mostrar registro
# -------------------------------
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# -------------------------------
# Procesar registro
# -------------------------------
@router.post("/register")
async def register_user(
    nombre_completo: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    email: str = Form(...)
):
    if password != confirmPassword:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    existing_user = await database.fetch_one(
        users.select().where(users.c.usuario == username)
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    existing_email = await database.fetch_one(
        users.select().where(users.c.email == email)
    )
    if existing_email:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    hashed_password = hash_password(password)

    # Guardar usuario y obtener id
    user_id = await database.execute(
        users.insert().values(
            nombre_completo=nombre_completo,
            usuario=username,
            password=hashed_password,
            email=email,
            role="user"
        )
    )

    # ➕ Puntos por registro (+20 puntos)
    await add_points(user_id, 20, "Registro de cuenta", "registro")

    return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)


# -------------------------------
# Logout
# -------------------------------
@router.get("/logout")
async def logout():
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.delete_cookie("user_id")
    redirect.delete_cookie("user_name")
    redirect.delete_cookie("role")
    return redirect
