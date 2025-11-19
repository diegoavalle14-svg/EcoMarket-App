# app/routers/solicitudes.py
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database.connection import database
from app.database.tables import solicitudes, users
from app.routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# -------------------------------
# Página de solicitudes (usuario)
# -------------------------------
@router.get("/solicitudes", response_class=HTMLResponse)
async def solicitudes_page(request: Request, user=Depends(get_current_user)):
    """
    Página de solicitudes con info del usuario autenticado.
    """
    query = solicitudes.select().where(solicitudes.c.usuario_id == user["id"])
    result = await database.fetch_all(query)
    return templates.TemplateResponse(
        "solicitudes.html",
        {"request": request, "solicitudes": result, "usuario": user}
    )

# -------------------------------
# API: Obtener solicitudes del usuario
# -------------------------------
@router.get("/api/solicitudes_usuario")
async def api_solicitudes_usuario(user=Depends(get_current_user)):
    query = solicitudes.select().where(solicitudes.c.usuario_id == user["id"])
    result = await database.fetch_all(query)
    return [dict(r) for r in result]

# -------------------------------
# API: Obtener todas las solicitudes (solo admin)
# -------------------------------
@router.get("/api/solicitudes")
async def api_solicitudes(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede ver todas las solicitudes")
    query = solicitudes.join(users, solicitudes.c.usuario_id == users.c.id)
    result = await database.fetch_all(
        solicitudes.select().with_only_columns(
            solicitudes.c.id,
            solicitudes.c.usuario_id,
            users.c.username,
            solicitudes.c.tipo,
            solicitudes.c.producto_nombre,
            solicitudes.c.descripcion,
            solicitudes.c.estado,
            solicitudes.c.created_at
        ).select_from(query)
    )
    return {"solicitudes": [dict(r) for r in result]}

# -------------------------------
# API: Crear solicitud (desde formulario HTML)
# -------------------------------
@router.post("/api/solicitudes")
async def crear_solicitud(
    tipo: str = Form(...),
    producto_nombre: str = Form(...),
    descripcion: str = Form(None),
    user=Depends(get_current_user)
):
    if not tipo.strip() or not producto_nombre.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo y nombre del producto son requeridos"
        )
    query = solicitudes.insert().values(
        usuario_id=user["id"],
        tipo=tipo.strip(),
        producto_nombre=producto_nombre.strip(),
        descripcion=descripcion.strip() if descripcion else None,
        estado="Pendiente"
    )
    await database.execute(query)
    return {"msg": "Solicitud creada correctamente"}

# -------------------------------
# API: Actualizar estado de solicitud (solo admin)
# -------------------------------
@router.post("/api/solicitudes/update_status")
async def update_status(data: dict = Body(...), user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede cambiar el estado")
    solicitud_id = data.get("solicitud_id")
    new_status = data.get("new_status")
    if new_status not in ["Pendiente", "Aprobada", "Rechazada"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
    query = solicitudes.update().where(solicitudes.c.id == solicitud_id).values(estado=new_status)
    await database.execute(query)
    return {"msg": "Estado actualizado"}

# -------------------------------
# API: Eliminar solicitud (solo admin)
# -------------------------------
@router.post("/api/solicitudes/delete")
async def delete_solicitud(data: dict = Body(...), user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede eliminar solicitudes")
    solicitud_id = data.get("solicitud_id")
    query = solicitudes.delete().where(solicitudes.c.id == solicitud_id)
    await database.execute(query)
    return {"msg": "Solicitud eliminada"}
