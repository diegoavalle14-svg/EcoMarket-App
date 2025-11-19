# -------------------------------
# Rutas principales del menú
# -------------------------------
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database.connection import database
from app.database.tables import products, puntos, clients
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# -------------------------------
# Menú principal
# -------------------------------
@router.get("/menu", response_class=HTMLResponse)
async def menu_page(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# -------------------------------
# Puntos de Recolección
# -------------------------------
@router.get("/puntos_recoleccion-page", response_class=HTMLResponse)
async def puntos_page(request: Request):
    result = await database.fetch_all(puntos.select())
    return templates.TemplateResponse("puntos_recoleccion.html", {"request": request, "puntos": result})

@router.get("/api/puntos_recoleccion")
async def api_puntos():
    result = await database.fetch_all(puntos.select())
    return {"puntos": [dict(r) for r in result]}


# -------------------------------
# Puntos de Usuario
# -------------------------------
@router.get("/puntos_usuario", response_class=HTMLResponse)
async def puntos_usuario_page(request: Request):
    result = await database.fetch_all(puntos.select())  # si quieres pasar los puntos
    return templates.TemplateResponse("puntos_usuario.html", {"request": request, "puntos": result})


from fastapi import Request
from fastapi.responses import HTMLResponse

@router.get("/ecomarket", response_class=HTMLResponse)
async def ecomarket_user(request: Request):
    return templates.TemplateResponse("ecomarket.html", {"request": request})


# -------------------------------
# Sistema de Solicitudes
# -------------------------------
@router.get("/solicitudes_usuario", response_class=HTMLResponse)
async def solicitudes_usuario_page(request: Request):
    # Aquí podrías traer las solicitudes del usuario desde la DB
    return templates.TemplateResponse("solicitudes_usuario.html", {"request": request})

