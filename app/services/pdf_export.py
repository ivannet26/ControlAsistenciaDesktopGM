import base64
import traceback
from datetime import datetime
from pathlib import Path

from jinja2 import Template
from xhtml2pdf import pisa


BASE_DIR = Path(__file__).resolve().parents[1]  # app/
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"


def _img_data_uri(nombre_archivo: str) -> str:
    """
    Convierte una imagen en un data URI base64.
    xhtml2pdf carga mucho mejor las imágenes así.
    """
    ruta = ASSETS_DIR / nombre_archivo
    if not ruta.exists():
        print(f"[PDF] ⚠️  No existe: {ruta}")
        return ""

    extension = ruta.suffix.lower().lstrip(".")
    mime = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml",
    }.get(extension, "image/png")

    try:
        with open(ruta, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{data}"
    except Exception as e:
        print(f"[PDF] ⚠️  Error leyendo {ruta}: {e}")
        return ""


def _limpiar(texto: str) -> str:
    """Quita caracteres que xhtml2pdf no puede dibujar con Helvetica."""
    return (
        (texto or "")
        .replace("\u200b", "")
        .replace("・", "-")
        .replace("●", "")
        .strip()
    )


def _truncar(texto: str, max_chars: int = 60) -> str:
    """Trunca un texto si supera max_chars, añadiendo '…' al final."""
    texto = _limpiar(texto)
    if len(texto) <= max_chars:
        return texto
    return texto[: max_chars - 1].rstrip() + "…"


def _dur_humana(segundos: int) -> str:
    segundos = max(0, int(segundos or 0))
    h, resto = divmod(segundos, 3600)
    m, _ = divmod(resto, 60)
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def _parse_duracion(texto: str) -> int:
    """Convierte 'HH:MM:SS' a segundos."""
    try:
        partes = [int(p) for p in str(texto).split(":")]
    except (ValueError, TypeError):
        return 0
    if len(partes) == 3:
        return partes[0] * 3600 + partes[1] * 60 + partes[2]
    if len(partes) == 2:
        return partes[0] * 3600 + partes[1] * 60
    return 0


def exportar_informe_pdf(
    ruta_salida: str,
    usuario: dict,
    fecha_iso: str,
    registros: list,
    grupo: list,
) -> bool:
    """Genera el PDF. Retorna True si tuvo éxito, False si falló."""

    # --- Datos base ---
    usuario_nombre = (
        f"{usuario.get('nombre', '')} {usuario.get('apellido', '')}".strip()
        or "(sin nombre)"
    )
    usuario_email = usuario.get("email") or "(sin email)"

    # --- Calcular total de segundos ---
    total_segundos = 0
    for r in registros:
        seg = r.get("duracion_seg")
        if seg is None:
            seg = _parse_duracion(r.get("duracion", ""))
        total_segundos += int(seg or 0)

    # --- Preparar datos ---
    datos_app = [
        {
            "nombre": _limpiar(g.get("app", "")),
            "duracion": g.get("total_str", "00:00:00"),
            "porcentaje": f"{g.get('uso_pct', 0):.1f}",
            "color": g.get("color", "#4b5563"),
        }
        for g in grupo
    ]

    datos_reg = [
        {
            "app": _limpiar(r.get("app", "")),
            "descripcion": _truncar(r.get("descripcion", "") or "—", 70),
            "url": _truncar(r.get("url", ""), 55),
            "hora_inicio": r.get("hora_inicio", ""),
            "hora_fin": r.get("hora_fin", ""),
            "duracion": r.get("duracion", "00:00:00"),
            "inactividad": f"{int((r.get('inactividad') or 0) * 100)}%",
        }
        for r in registros
    ]

    # --- Imágenes del encabezado en base64 ---
    logo_data = _img_data_uri("cabecera1.png")
    iso_data = _img_data_uri("cabecera2.jpg")

    # --- Renderizar HTML ---
    template_file = TEMPLATES_DIR / "informe_rastreador.html"
    with open(template_file, "r", encoding="utf-8") as f:
        tpl = Template(f.read())

    html = tpl.render(
        logo_data=logo_data,
        iso_data=iso_data,
        usuario_nombre=usuario_nombre,
        usuario_email=usuario_email,
        fecha=fecha_iso,
        fecha_generacion=datetime.now().strftime("%d/%m/%Y %H:%M"),
        tiempo_total_formateado=_dur_humana(total_segundos),
        total_actividades=len(registros),
        total_apps=len(grupo),
        datos_app=datos_app,
        datos_reg=datos_reg,
    )

    # --- Convertir a PDF ---
    try:
        with open(ruta_salida, "wb") as f:
            status = pisa.CreatePDF(html, dest=f, encoding="utf-8")
    except Exception as e:
        print(f"[PDF] ❌ Excepción al generar: {e}")
        traceback.print_exc()
        return False

    if status.err:
        print(f"[PDF] ❌ xhtml2pdf reportó {status.err} error(es)")
        return False

    print(f"[PDF] ✅ Generado: {ruta_salida}")
    return True