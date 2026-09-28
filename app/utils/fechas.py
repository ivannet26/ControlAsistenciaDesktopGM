# app/utils/fechas.py
from datetime import date, timedelta


def lunes_de_semana(fecha: date) -> date:
    """Devuelve el lunes de la semana a la que pertenece `fecha`."""
    return fecha - timedelta(days=fecha.weekday())


def nombre_dia(fecha: date) -> str:
    """Ej: 'lun, 5 may'"""
    dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{dias[fecha.weekday()]}, {fecha.day} {meses[fecha.month - 1]}"


def etiqueta_dia(fecha: date) -> str:
    """Devuelve 'HOY', 'AYER', 'ANTEAYER' o el nombre del día en mayúsculas."""
    hoy = date.today()
    if fecha == hoy:
        return "HOY"
    if fecha == hoy - timedelta(days=1):
        return "AYER"
    if fecha == hoy - timedelta(days=2):
        return "ANTEAYER"
    return nombre_dia(fecha).upper()


def etiqueta_semana(lunes: date) -> str:
    """Devuelve 'ESTA SEMANA', 'LA SEMANA PASADA' o 'SEMANA DEL x MES'."""
    hoy = date.today()
    lunes_actual = lunes_de_semana(hoy)
    lunes_anterior = lunes_actual - timedelta(days=7)

    if lunes == lunes_actual:
        return "ESTA SEMANA"
    if lunes == lunes_anterior:
        return "LA SEMANA PASADA"

    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"SEMANA DEL {lunes.day} {meses[lunes.month - 1].upper()}"