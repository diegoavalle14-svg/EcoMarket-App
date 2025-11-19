from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database.connection import database
from app.database.tables import clients
from app.utils.dependencies import admin_required, get_current_user

# -------------------------------
# Router y templates
# -------------------------------
router = APIRouter()
templates = Jinja2Templates(directory="templates")


# -------------------------------
# Página HTML de clientes
# -------------------------------
@router.get("/clientes", response_class=HTMLResponse)
async def clients_page(request: Request, user=Depends(get_current_user)):
    """Muestra la página HTML con la lista de clientes"""
    result = await database.fetch_all(clients.select())
    clients_list = [dict(r) for r in result]

    return templates.TemplateResponse(
        "clientes.html",
        {
            "request": request,
            "clients": clients_list,
            "user": user  # permite saber si es admin
        }
    )


# -------------------------------
# API GET: obtener todos los clientes
# -------------------------------
@router.get("/api/clientes")
async def api_get_clients(user=Depends(get_current_user)):
    result = await database.fetch_all(clients.select())
    return {"clients": [dict(r) for r in result]}


# -------------------------------
# API GET: obtener cliente por ID
# -------------------------------
@router.get("/api/clientes/{client_id}")
async def api_get_client(client_id: int, user=Depends(get_current_user)):
    query = clients.select().where(clients.c.id == client_id)
    result = await database.fetch_one(query)

    if not result:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return dict(result)


# -------------------------------
# API POST: crear cliente (SOLO ADMIN)
# -------------------------------
@router.post("/api/clientes")
async def api_create_client(
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(""),
    user=Depends(admin_required)  # <--- SOLO ADMIN
):
    query = clients.insert().values(
        nombre=nombre.strip(),
        apellido=apellido.strip(),
        email=email.strip(),
        telefono=telefono.strip()
    )
    await database.execute(query)

    return {"status": "success", "message": "Cliente agregado"}


# -------------------------------
# API PUT: editar cliente (SOLO ADMIN)
# -------------------------------
@router.put("/api/clientes/{client_id}")
async def api_update_client(
    client_id: int,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(""),
    user=Depends(admin_required)  # <--- SOLO ADMIN
):
    query = clients.update().where(clients.c.id == client_id).values(
        nombre=nombre.strip(),
        apellido=apellido.strip(),
        email=email.strip(),
        telefono=telefono.strip()
    )
    await database.execute(query)

    return {"status": "success", "message": "Cliente actualizado"}


# -------------------------------
# API DELETE: eliminar cliente (SOLO ADMIN)
# -------------------------------
@router.delete("/api/clientes/{client_id}")
async def api_delete_client(client_id: int, user=Depends(admin_required)):
    query = clients.delete().where(clients.c.id == client_id)
    await database.execute(query)

    return {"status": "success", "message": "Cliente eliminado"}


@router.get("/clientes")
async def clientes_page(request: Request):
    user = await get_current_user(request)  # obtenemos usuario de la cookie
    all_clients = await database.fetch_all(clients.select())
    return templates.TemplateResponse(
        "clientes.html",
        {"request": request, "clientes": all_clients, "usuario": user}
    )