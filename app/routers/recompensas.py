from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database.connection import database
from app.database.tables import user_points, rewards, points_history
from app.utils.security import require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


PUNTOS_POR_SOLICITUD_APROBADA = 10  # lo usarás luego en solicitudes_admin si quieres


@router.get("/recompensas", response_class=HTMLResponse)
async def recompensas_page(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse(
        "recompensas.html",
        {"request": request, "user": user},
    )


@router.get("/recompensas/mis-datos")
async def mis_datos_recompensas(user=Depends(require_login)):
    user_id = user["id"]

    # saldo actual
    saldo_query = user_points.select().where(user_points.c.user_id == user_id)
    saldo_row = await database.fetch_one(saldo_query)
    balance = saldo_row["balance"] if saldo_row else 0

    # historial (últimos 20 movimientos)
    hist_query = (
        points_history
        .select()
        .where(points_history.c.user_id == user_id)
        .order_by(points_history.c.fecha.desc())
        .limit(20)
    )
    historial = await database.fetch_all(hist_query)

    # catálogo de recompensas activas
    rewards_query = rewards.select().where(rewards.c.activo == True).order_by(rewards.c.puntos_necesarios)
    catalogo = await database.fetch_all(rewards_query)

    return {
        "balance": balance,
        "historial": [dict(r) for r in historial],
        "rewards": [dict(r) for r in catalogo],
    }


@router.post("/recompensas/canjear/{reward_id}")
async def canjear_recompensa(reward_id: int, user=Depends(require_login)):
    user_id = user["id"]

    # verificar recompensa
    reward_row = await database.fetch_one(
        rewards.select().where(rewards.c.id == reward_id, rewards.c.activo == True)
    )
    if not reward_row:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")

    puntos_necesarios = reward_row["puntos_necesarios"]

    # saldo actual
    saldo_row = await database.fetch_one(user_points.select().where(user_points.c.user_id == user_id))
    balance = saldo_row["balance"] if saldo_row else 0

    if balance < puntos_necesarios:
        raise HTTPException(status_code=400, detail="No tienes puntos suficientes")

    # restar puntos (transacción simple)
    nuevo_balance = balance - puntos_necesarios
    if saldo_row:
        await database.execute(
            user_points.update()
            .where(user_points.c.id == saldo_row["id"])
            .values(balance=nuevo_balance)
        )
    else:
        # por seguridad, aunque si no hay fila no debería tener puntos
        await database.execute(
            user_points.insert().values(user_id=user_id, balance=nuevo_balance)
        )

    # guardar en historial
    await database.execute(
        points_history.insert().values(
            user_id=user_id,
            cambio=-puntos_necesarios,
            motivo=f"Canje de recompensa #{reward_id}",
            referencia=str(reward_id),
        )
    )

    return {"ok": True, "nuevo_balance": nuevo_balance}
