from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.database.connection import database
from app.utils.security import get_current_user  # Importamos la función para obtener el usuario

router = APIRouter(prefix="/products", tags=["Productos Usuario"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def list_products(
    request: Request,
    category: str = None,
    user=Depends(get_current_user)  # Obtener usuario actual
):
    base_query = "SELECT * FROM products"
    values = {}

    # Filtro dinámico por categoría
    if category:
        base_query += " WHERE category = :category"
        values["category"] = category

    # Ejecutar consulta
    productos = await database.fetch_all(base_query, values=values)

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": productos,
            "category": category,
            "user": user  # Pasamos el usuario al template
        }
    )
