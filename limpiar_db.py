# limpiar_db.py
"""
Borra TODOS los segmentos del rastreador automático.
La BD sigue existiendo, solo se vacía la tabla.

⚠️  Detén la app antes de ejecutarlo para que no haya conflictos.
"""

import os
import sqlite3
import sys
from pathlib import Path


# ============================================================
# RUTA DE LA BD (misma que en rastreador.py)
# ============================================================
def _directorio_datos() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "ControlAsistencia"


DB_PATH = _directorio_datos() / "rastreador.db"


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("LIMPIAR BASE DE DATOS DEL RASTREADOR")
    print("=" * 60)
    print(f"BD: {DB_PATH}")

    if not DB_PATH.exists():
        print("La BD no existe. Nada que limpiar.")
        return

    # Contar antes
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row

    try:
        total = con.execute("SELECT COUNT(*) FROM segmentos").fetchone()[0]
    except sqlite3.OperationalError:
        print("La tabla 'segmentos' no existe. Nada que limpiar.")
        con.close()
        return

    print(f"Segmentos actuales: {total}")

    if total == 0:
        print("La BD ya esta vacia.")
        con.close()
        return

    # Confirmación
    print()
    print(">>> ESTO BORRARA TODOS LOS REGISTROS DEL RASTREADOR.")
    print(">>> Asegurate de haber cerrado la app (Stop-Process -Name python*)")
    print()
    respuesta = input("Continuar? (escribe 'si' para confirmar): ").strip().lower()

    if respuesta not in ("si", "sí", "s", "yes", "y"):
        print("Cancelado. No se borro nada.")
        con.close()
        return

    # Borrar
    con.execute("DELETE FROM segmentos")
    con.commit()

    # Compactar (opcional, reduce el archivo)
    con.execute("VACUUM")
    con.commit()

    con.close()

    print()
    print(f"Hecho. Se borraron {total} segmentos.")
    print(f"BD: {DB_PATH}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)