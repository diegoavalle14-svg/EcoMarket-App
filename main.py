# -------------------------------
# Punto de entrada del sistema
# -------------------------------
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database.connection import metadata, engine, database
from app.routers import auth, clientes, products, puntos, solicitudes, points

metadata.create_all(engine)

app = FastAPI(title="EcoMarket API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# -------------------------------
# Eventos de inicio/cierre
# -------------------------------
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# -------------------------------
# Inclusión de rutas
# -------------------------------
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(clientes.router)
app.include_router(puntos.router)
app.include_router(solicitudes.router)
app.include_router(points.router)


