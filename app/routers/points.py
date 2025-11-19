# points.py
from fastapi import APIRouter, Form, HTTPException
from app.database.connection import database
from app.database.tables import points

router = APIRouter()

# GET todos los puntos
@router.get("/api/points")
async def get_points():
    result = await database.fetch_all(points.select())
    return {"points": [dict(r) for r in result]}

# POST nuevo punto
@router.post("/api/points")
async def create_point(
    nombre: str = Form(...),
    direccion: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...)
):
    query = points.insert().values(
        nombre=nombre,
        direccion=direccion,
        lat=lat,
        lng=lng
    )
    await database.execute(query)
    return {"status": "success", "message": "Punto agregado"}
