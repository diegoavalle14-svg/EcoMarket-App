from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database.connection import database
from app.database.tables import solicitudes, users
from app.utils.security import require_login, require_admin
from app.utils.points import add_points


router = APIRouter(tags=["Solicitudes"])


class SolicitudCreate(BaseModel):
    producto: str
    cantidad: int
    descripcion: str | None = None
    tipo: str  # donar, intercambiar, comprar


# -----------------------
# GET mis solicitudes
# -----------------------
@router.get("/mis-solicitudes")
async def mis_solicitudes(user=Depends(require_login)):
    query = """
        SELECT id, producto, cantidad, descripcion, tipo, estado
        FROM solicitudes
        WHERE user_id = :user_id
        ORDER BY id DESC
    """
    result = await database.fetch_all(query, values={"user_id": user["id"]})
    return result


# -----------------------
# POST crear solicitud (+5 puntos)
# -----------------------
@router.post("/crear")
async def crear_solicitud(
    solicitud_data: SolicitudCreate,
    user=Depends(require_login),
):
    if solicitud_data.cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor que cero.")

    if solicitud_data.tipo not in ["donar", "intercambiar", "comprar"]:
        raise HTTPException(status_code=400, detail="Tipo inválido.")

    # Insertar solicitud y obtener id
    solicitud_id = await database.execute(
        solicitudes.insert().values(
            user_id=user["id"],
            producto=solicitud_data.producto,
            cantidad=solicitud_data.cantidad,
            descripcion=solicitud_data.descripcion,
            tipo=solicitud_data.tipo,
            estado="pendiente",
        )
    )

    # ➕ Puntos por crear solicitud (+5 puntos)
    await add_points(user["id"], 5, "Creación de solicitud", str(solicitud_id))

    return {
        "message": "Solicitud enviada",
        "solicitud_id": solicitud_id,
        "puntos_ganados": 5
    }


# -----------------------
# ADMIN - listar solicitudes
# -----------------------
@router.get("/admin/all")
async def todas_solicitudes_admin(admin=Depends(require_admin)):
    query = """
        SELECT s.id, u.email, s.producto, s.cantidad, s.descripcion, s.tipo, s.estado
        FROM solicitudes s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.id DESC
    """
    return await database.fetch_all(query)


# -----------------------
# ADMIN - cambiar estado (+10 puntos si se aprueba)
# -----------------------
@router.put("/admin/estado/{id}")
async def cambiar_estado(id: int, data: dict, admin=Depends(require_admin)):
    nuevo_estado = data.get("estado")
    if nuevo_estado not in ["pendiente", "aprobado", "rechazado"]:
        raise HTTPException(status_code=400, detail="Estado inválido")

    # Obtener solicitud actual (con user_id y estado anterior)
    solicitud_actual = await database.fetch_one(
        solicitudes.select().where(solicitudes.c.id == id)
    )
    if not solicitud_actual:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # Obtener email del usuario
    q_user = """
        SELECT u.email
        FROM solicitudes s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = :id
    """
    result = await database.fetch_one(q_user, {"id": id})
    if not result:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # Cambiar estado
    await database.execute(
        solicitudes.update().where(solicitudes.c.id == id).values(estado=nuevo_estado)
    )

    # ➕ Puntos solo si se APRUEBA (y no estaba aprobada antes)
    puntos_ganados = 0
    if nuevo_estado == "aprobado" and solicitud_actual["estado"] != "aprobado":
        await add_points(
            solicitud_actual["user_id"],
            10,
            "Solicitud aprobada",
            str(id)
        )
        puntos_ganados = 10

    return {
        "message": "Estado actualizado",
        "solicitud_id": id,
        "nuevo_estado": nuevo_estado,
        "puntos_ganados": puntos_ganados,
        "usuario_email": result["email"]
    }
