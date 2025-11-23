from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database.connection import database
from app.database.tables import users
from app.utils.security import hash_password, verify_password

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ---- Registro ----
@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register_user(
    nombre_completo: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("user")
):
    existing_user = await database.fetch_one(users.select().where(users.c.usuario == username))
    existing_email = await database.fetch_one(users.select().where(users.c.correo == email))
    if existing_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if existing_email:
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    query = users.insert().values(
        nombre_completo=nombre_completo.strip(),
        usuario=username.strip(),
        correo=email.strip(),
        contrasena=hash_password(password),
        rol=role
    )
    await database.execute(query)
    return RedirectResponse("/login", status_code=303)

# ---- Login ----
@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = await database.fetch_one(users.select().where(users.c.usuario == username))
    if not user or not verify_password(password, user["contrasena"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    redirect_url = "/menu" if user["rol"] == "admin" else "/productos_usuario"
    response = RedirectResponse(redirect_url, status_code=302)
    response.set_cookie("user_name", user["usuario"], path="/")
    response.set_cookie("user_role", user["rol"], path="/")
    return response

# ---- Logout ----
@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("user_name", path="/")
    response.delete_cookie("user_role", path="/")
    return response

# ---- Obtener usuario actual ----
async def get_current_user(request: Request):
    username = request.cookies.get("user_name")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    user = await database.fetch_one(users.select().where(users.c.usuario == username))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return dict(user)
