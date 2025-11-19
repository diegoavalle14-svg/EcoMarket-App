# -------------------------------
# Rutas: Productos (CRUD)
# -------------------------------
from typing import Optional, List

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from app.database.connection import database
from app.database.tables import products

from app.routers.auth import get_current_user
router = APIRouter(tags=["products"])
templates = Jinja2Templates(directory="templates")

# ========= Esquemas Pydantic =========
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price: float
    stock: int
    status: Optional[str] = "disponible"
    owner_id: Optional[int] = None  # opcional, si tu tabla permite NULL
    image_url: Optional[HttpUrl] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    image_url: Optional[HttpUrl] = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str
    price: float
    stock: int
    status: Optional[str] = "disponible"
    owner_id: Optional[int] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None  # Pydantic convertirá datetime a string

    class Config:
        orm_mode = True

# ========= Página HTML =========
@router.get("/products-page", response_class=HTMLResponse)
async def products_page(request: Request):
    """
    Devuelve la plantilla de productos.
    El JS de la página llama a la API /products.
    """
    return templates.TemplateResponse("products.html", {"request": request})

# ========= API CRUD =========
# LISTAR PRODUCTOS
@router.get("/products", response_model=List[ProductOut])
async def list_products(category: Optional[str] = None):
    query = products.select()
    if category:
        query = query.where(products.c.category == category)
    rows = await database.fetch_all(query)
    return rows

# OBTENER UN PRODUCTO
@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int):
    row = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return row

# CREAR PRODUCTO
@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    new_product = {
        "name": product.name.strip(),
        "description": product.description.strip() if product.description else None,
        "category": product.category.strip(),
        "price": product.price,
        "stock": product.stock,
        "status": product.status or "disponible",
        "owner_id": product.owner_id,
        "image_url": product.image_url
    }

    insert_query = products.insert().values(**new_product)
    last_id = await database.execute(insert_query)

    row = await database.fetch_one(products.select().where(products.c.id == last_id))
    if not row:
        raise HTTPException(status_code=500, detail="No se pudo crear el producto")
    return row

# ACTUALIZAR PRODUCTO
@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, product: ProductUpdate):
    existing = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    update_data = product.dict(exclude_unset=True)
    for field in ["name", "description", "category"]:
        if field in update_data and update_data[field] is not None:
            update_data[field] = update_data[field].strip()

    if update_data:
        await database.execute(products.update().where(products.c.id == product_id).values(**update_data))

    row = await database.fetch_one(products.select().where(products.c.id == product_id))
    return row

# ELIMINAR PRODUCTO
@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int):
    existing = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    await database.execute(products.delete().where(products.c.id == product_id))
    return


@router.get("/productos_usuario")
async def productos_usuario_page(request: Request, user=Depends(get_current_user)):
    """
    Página principal del usuario: lista todos los productos
    """
    query = products.select()
    all_products = await database.fetch_all(query)
    return templates.TemplateResponse(
        "ecomarket.html",
        {"request": request, "productos": all_products, "usuario": user}
    )



@router.get("/api/productos")
async def api_productos():
    """
    Devuelve todos los productos en formato JSON
    """
    query = products.select()
    all_products = await database.fetch_all(query)
    return {"productos": [dict(p) for p in all_products]}