from fastapi import APIRouter, Depends, HTTPException, Form
from app.database.connection import database
from app.database.tables import user_points, rewards, points_history, users
from app.utils.security import require_admin

router = APIRouter()


@router.get("/admin/rewards")
async def list_rewards(admin=Depends(require_admin)):
    rows = await database.fetch_all(rewards.select().order_by(rewards.c.id.desc()))
    return [dict(r) for r in rows]


@router.post("/admin/rewards")
async def create_reward(
    nombre: str = Form(...),
    puntos_necesarios: int = Form(...),
    descripcion: str = Form(""),
    activo: bool = Form(True),
    admin=Depends(require_admin),
):
    await database.execute(
        rewards.insert().values(
            nombre=nombre,
            descripcion=descripcion,
            puntos_necesarios=puntos_necesarios,
            activo=activo,
        )
    )
    return {"ok": True}


@router.post("/admin/rewards/{reward_id}")
async def update_reward(
    reward_id: int,
    nombre: str = Form(...),
    puntos_necesarios: int = Form(...),
    descripcion: str = Form(""),
    activo: bool = Form(True),
    admin=Depends(require_admin),
):
    row = await database.fetch_one(rewards.select().where(rewards.c.id == reward_id))
    if not row:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")

    await database.execute(
        rewards.update()
        .where(rewards.c.id == reward_id)
        .values(
            nombre=nombre,
            descripcion=descripcion,
            puntos_necesarios=puntos_necesarios,
            activo=activo,
        )
    )
    return {"ok": True}


@router.delete("/admin/rewards/{reward_id}")
async def delete_reward(reward_id: int, admin=Depends(require_admin)):
    row = await database.fetch_one(rewards.select().where(rewards.c.id == reward_id))
    if not row:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")

    await database.execute(rewards.delete().where(rewards.c.id == reward_id))
    return {"ok": True}


@router.post("/admin/users/{user_id}/ajustar-puntos")
async def ajustar_puntos(
    user_id: int,
    cambio: int = Form(...),
    motivo: str = Form(...),
    admin=Depends(require_admin),
):
    # comprobar usuario
    user_row = await database.fetch_one(users.select().where(users.c.id == user_id))
    if not user_row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # saldo actual
    saldo_row = await database.fetch_one(user_points.select().where(user_points.c.user_id == user_id))
    balance = saldo_row["balance"] if saldo_row else 0
    nuevo_balance = balance + cambio

    if nuevo_balance < 0:
        raise HTTPException(status_code=400, detail="El saldo no puede ser negativo")

    if saldo_row:
        await database.execute(
            user_points.update()
            .where(user_points.c.id == saldo_row["id"])
            .values(balance=nuevo_balance)
        )
    else:
        await database.execute(
            user_points.insert().values(user_id=user_id, balance=nuevo_balance)
        )

    # historial
    await database.execute(
        points_history.insert().values(
            user_id=user_id,
            cambio=cambio,
            motivo=motivo,
            referencia="ajuste_admin",
        )
    )

    return {"ok": True, "nuevo_balance": nuevo_balance}
