# admin_products.py
from fastapi import APIRouter, Depends, HTTPException
from app.database.connection import database
from app.utils.security import require_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin_productos/api", tags=["Productos Admin"])

# -----------------------
#  MODELOS
# -----------------------
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price: float
    stock: int
    status: str
    image_url: Optional[str] = None


# -----------------------
#  GET - todos
# -----------------------
@router.get("/all")
async def get_all_products(user=Depends(require_admin)):
    query = "SELECT * FROM products"
    productos = await database.fetch_all(query)
    return productos


# -----------------------
#  GET - individual
# -----------------------
@router.get("/{id}")
async def get_product(id: int, user=Depends(require_admin)):
    query = "SELECT * FROM products WHERE id = :id"
    producto = await database.fetch_one(query, values={"id": id})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


# -----------------------
#  POST - crear
# -----------------------
@router.post("/create")
async def create_product(data: ProductBase, user=Depends(require_admin)):

    query = """
        INSERT INTO products (name, description, category, price, stock, status, image_url)
        VALUES (:name, :description, :category, :price, :stock, :status, :image_url)
    """

    new_id = await database.execute(query, data.dict())

    return {
        "msg": "Producto creado",
        "id": new_id
    }


# -----------------------
#  PUT - actualizar
# -----------------------
@router.put("/{id}")
async def update_product(id: int, data: ProductBase, user=Depends(require_admin)):

    # Verificar que exista
    existing = await database.fetch_one(
        "SELECT * FROM products WHERE id = :id",
        values={"id": id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    query = """
        UPDATE products
        SET 
            name = :name,
            description = :description,
            category = :category,
            price = :price,
            stock = :stock,
            status = :status,
            image_url = :image_url
        WHERE id = :id
    """

    values = data.dict()
    values["id"] = id

    await database.execute(query, values)

    return {"msg": "Producto actualizado"}


# -----------------------
#  DELETE - eliminar
# -----------------------
@router.delete("/{id}")
async def delete_product(id: int, user=Depends(require_admin)):

    existing = await database.fetch_one(
        "SELECT * FROM products WHERE id = :id",
        values={"id": id}
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    await database.execute(
        "DELETE FROM products WHERE id = :id",
        values={"id": id}
    )

    return {"msg": "Producto eliminado"}
