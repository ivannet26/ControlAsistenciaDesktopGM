import base64
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


PREFIJO_TOKEN = "dpapi:"


def _ruta_cuentas() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "ControlAsistencia" / "cuentas.json"


def _proteger_token(token: str) -> str:
    try:
        import win32crypt
    except ImportError as exc:
        raise RuntimeError(
            "No está disponible Windows DPAPI para proteger el token de la cuenta."
        ) from exc

    protegido = win32crypt.CryptProtectData(
        token.encode("utf-8"),
        "ControlAsistencia",
        None,
        None,
        None,
        0,
    )
    return PREFIJO_TOKEN + base64.b64encode(protegido).decode("ascii")


def _descifrar_token(token_protegido: str) -> str:
    if not token_protegido.startswith(PREFIJO_TOKEN):
        raise ValueError("El token guardado no tiene un formato protegido reconocido.")
    try:
        import win32crypt
    except ImportError as exc:
        raise RuntimeError(
            "No está disponible Windows DPAPI para leer el token de la cuenta."
        ) from exc

    datos = base64.b64decode(token_protegido[len(PREFIJO_TOKEN):], validate=True)
    return win32crypt.CryptUnprotectData(
        datos,
        None,
        None,
        None,
        0,
    )[1].decode("utf-8")


def _leer_cuentas() -> list[dict]:
    ruta = _ruta_cuentas()
    if not ruta.exists():
        return []
    with ruta.open("r", encoding="utf-8") as archivo:
        cuentas = json.load(archivo)
    if not isinstance(cuentas, list) or not all(
        isinstance(cuenta, dict) for cuenta in cuentas
    ):
        raise ValueError(f"Formato de cuentas inválido en {ruta}")
    return cuentas


def _guardar_archivo(cuentas: list[dict]) -> None:
    ruta = _ruta_cuentas()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=ruta.parent,
            delete=False,
            suffix=".tmp",
        ) as archivo:
            temporal = Path(archivo.name)
            json.dump(cuentas, archivo, ensure_ascii=False, indent=2)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        if temporal is not None and temporal.exists():
            temporal.unlink()


def listar_cuentas() -> list[dict]:
    cuentas = []
    for cuenta in _leer_cuentas():
        resultado = dict(cuenta)
        resultado["token"] = _descifrar_token(cuenta.get("token", ""))
        token_refresh = cuenta.get("refresh_token")
        resultado["refresh_token"] = (
            _descifrar_token(token_refresh) if token_refresh else None
        )
        cuentas.append(resultado)
    return cuentas


def guardar_cuenta(
    usuario: dict,
    token: str,
    refresh_token: str | None = None,
) -> None:
    email = (usuario.get("email") or usuario.get("correo") or "").strip()
    if not email:
        raise ValueError("No se puede guardar la cuenta sin correo electrónico.")
    if not token:
        raise ValueError("No se puede guardar la cuenta sin un token de acceso.")

    perfil = {
        clave: usuario[clave]
        for clave in (
            "id",
            "nombre",
            "apellido",
            "email",
            "correo",
            "rol",
            "avatar_url",
        )
        if clave in usuario
    }
    registro = {
        "email": email,
        "nombre": usuario.get("nombre", ""),
        "avatar_url": usuario.get("avatar_url"),
        "token": _proteger_token(token),
        "refresh_token": (
            _proteger_token(refresh_token) if refresh_token else None
        ),
        "usuario": perfil,
    }

    cuentas = _leer_cuentas()
    cuentas = [
        cuenta for cuenta in cuentas
        if (cuenta.get("email") or "").casefold() != email.casefold()
    ]
    cuentas.append(registro)
    _guardar_archivo(cuentas)


def actualizar_tokens(
    email: str,
    token: str,
    refresh_token: str | None = None,
) -> None:
    """Actualiza access+refresh de una cuenta sin reescribir su perfil."""
    email = (email or "").strip()
    if not email:
        raise ValueError("No se puede actualizar una cuenta sin correo electrónico.")
    if not token:
        raise ValueError("No se puede actualizar una cuenta sin token de acceso.")

    cuentas = _leer_cuentas()
    for cuenta in cuentas:
        if (cuenta.get("email") or "").casefold() == email.casefold():
            cuenta["token"] = _proteger_token(token)
            if refresh_token:
                cuenta["refresh_token"] = _proteger_token(refresh_token)
            _guardar_archivo(cuentas)
            return

    raise ValueError(f"No existe una cuenta guardada para {email}")


def eliminar_cuenta(email: str) -> None:
    email_normalizado = (email or "").casefold()
    cuentas = [
        cuenta for cuenta in _leer_cuentas()
        if (cuenta.get("email") or "").casefold() != email_normalizado
    ]
    _guardar_archivo(cuentas)
