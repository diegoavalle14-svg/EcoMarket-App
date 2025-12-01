from app.database.connection import database
from app.database.tables import user_points, points_history

async def add_points(user_id: int, cambio: int, motivo: str, referencia: str | None = None):
    """
    Suma (o resta) puntos al usuario y registra el movimiento en el historial.
    cambio: entero (positivo = gana puntos, negativo = gasta puntos).
    """
    # Leer saldo actual
    saldo_row = await database.fetch_one(
        user_points.select().where(user_points.c.user_id == user_id)
    )
    balance = saldo_row["balance"] if saldo_row else 0
    nuevo_balance = balance + cambio

    # Actualizar o crear saldo
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

    # Guardar en historial
    await database.execute(
        points_history.insert().values(
            user_id=user_id,
            cambio=cambio,
            motivo=motivo,
            referencia=referencia,
        )
    )

    return nuevo_balance
