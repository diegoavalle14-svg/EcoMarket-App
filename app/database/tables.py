from datetime import datetime
from sqlalchemy import DateTime, Float, Table, Column, Integer, String, ForeignKey
import sqlalchemy
from .connection import metadata

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre_completo", String(150), nullable=False),
    Column("usuario", String(50), unique=True),
    Column("correo", String(100), unique=True),
    Column("contrasena", String(255)),
    Column("rol", String(20), default="user"),
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("description", String(255)),
    Column("category", String(50), nullable=False),
    Column("price", Float, nullable=False),
    Column("stock", Integer, nullable=False, default=0),
    Column("status", String(50), default="disponible"),
    Column("owner_id", Integer),
    Column("image_url", String(255)),
    Column("created_at", DateTime, default=datetime.utcnow)  # corregido
)

clients = Table(
    "clients",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(100)),
    Column("apellido", String(100)),
    Column("email", String(100)),
    Column("telefono", String(50)),
)

puntos = Table(
    "puntos_recoleccion",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(255)),
    Column("direccion", String(255)),
    Column("telefono", String(50)),
    Column("horario", String(255)),
)

solicitudes = Table(
    "solicitudes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("usuario_id", Integer, ForeignKey("users.id")),
    Column("tipo", String(50), nullable=False),
    Column("producto_nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("estado", String(50), default="pendiente"),
    Column("created_at", DateTime, default=datetime.utcnow),
    extend_existing=True  # evita error si ya está definida
)

points = Table(
    "points",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(100)),
    Column("direccion", String(200)),
    Column("lat", Float),
    Column("lng", Float),
)
