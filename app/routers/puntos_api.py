from fastapi import APIRouter, Form, Depends, HTTPException
from app.database.connection import database
from app.database.tables import points
from app.utils.security import require_admin

router = APIRouter()

# GET todos los puntos → usuarios y admin
@router.get("/puntos", tags=["Puntos"])
async def get_points():
    result = await database.fetch_all(points.select())
    return {"points": [dict(r) for r in result]}

# POST crear punto → solo admin
@router.post("/puntos", tags=["Puntos"])
async def create_point(
    nombre: str = Form(...),
    direccion: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    user=Depends(require_admin)
):
    query = points.insert().values(nombre=nombre, direccion=direccion, lat=lat, lng=lng)
    last_id = await database.execute(query)
    return {"id": last_id, "nombre": nombre, "direccion": direccion, "lat": lat, "lng": lng}

# PUT actualizar punto → solo admin
@router.put("/puntos/{point_id}", tags=["Puntos"])
async def update_point(
    point_id: int,
    nombre: str = Form(...),
    direccion: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    user=Depends(require_admin)
):
    query = points.update().where(points.c.id == point_id).values(
        nombre=nombre, direccion=direccion, lat=lat, lng=lng
    )
    result = await database.execute(query)
    if not result:
        raise HTTPException(status_code=404, detail="Punto no encontrado")
    return {"msg": "Punto actualizado"}

# DELETE → solo admin
@router.delete("/puntos/{point_id}", tags=["Puntos"])
async def delete_point(point_id: int, user=Depends(require_admin)):
    query = points.delete().where(points.c.id == point_id)
    result = await database.execute(query)
    if not result:
        raise HTTPException(status_code=404, detail="Punto no encontrado")
    return {"msg": "Punto eliminado"}
