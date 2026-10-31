# app/services/api_client.py
import base64
import json
import os
import threading
import time

import requests
from dotenv import load_dotenv

from app.services import cuentas_store

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "https://backendcontrolasistenciagm.onrender.com")


def _tiempos_desde_token(token: str | None) -> tuple[float | None, float | None]:
    """Devuelve (exp, iat) del JWT sin verificar la firma."""
    if not token:
        return None, None
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        datos = json.loads(base64.urlsafe_b64decode(payload))
        exp = datos.get("exp")
        iat = datos.get("iat")
        return (
            float(exp) if exp is not None else None,
            float(iat) if iat is not None else None,
        )
    except Exception:
        return None, None


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class NetworkError(ApiError):
    """Error de conexión o timeout; no significa sesión inválida."""


class SessionExpired(ApiError):
    """El access/refresh ya no sirve; requiere reautenticación."""


class ApiClient:
    """Cliente HTTP para el backend de Control de Asistencia GM."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        self.refresh_token: str | None = None
        self.token_expira_en: float | None = None
        self.token_vida_seg: float | None = None
        self.usuario: dict | None = None
        self._refresh_lock = threading.Lock()

    # ---------------- helpers internos ----------------
    @staticmethod
    def _detalle_error(resp):
        detail = resp.text
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            pass
        return detail

    def _aplicar_tokens(self, access_token, refresh_token=None, expires_in=None):
        self.token = access_token
        self.refresh_token = refresh_token
        exp, iat = _tiempos_desde_token(access_token)
        self.token_expira_en = exp
        self.token_vida_seg = None

        if expires_in:
            try:
                vida = float(expires_in)
            except (TypeError, ValueError):
                vida = 0.0
            if vida > 0:
                self.token_vida_seg = vida
                if self.token_expira_en is None:
                    self.token_expira_en = time.time() + vida
        elif exp is not None and iat is not None and exp > iat:
            self.token_vida_seg = exp - iat

    def cargar_tokens(self, access_token, refresh_token=None):
        """Carga tokens de una cuenta guardada, sin persistir."""
        self._aplicar_tokens(access_token, refresh_token)

    def _limpiar_tokens(self):
        self.token = None
        self.refresh_token = None
        self.token_expira_en = None
        self.token_vida_seg = None

    def _margen_renovacion(self) -> float:
        if self.token_vida_seg and self.token_vida_seg > 0:
            return min(120.0, self.token_vida_seg * 0.25)
        return 120.0

    def _token_por_vencer(self) -> bool:
        return bool(
            self.token
            and self.token_expira_en is not None
            and time.time() >= self.token_expira_en - self._margen_renovacion()
        )

    def _renovar_si_hace_falta(self):
        if self.token and self.refresh_token and self._token_por_vencer():
            self.refresh()

    def _persistir_tokens(self):
        email = ""
        if isinstance(self.usuario, dict):
            email = (
                self.usuario.get("email")
                or self.usuario.get("correo")
                or ""
            )
        if not email or not self.token:
            return
        try:
            cuentas_store.actualizar_tokens(
                email, self.token, self.refresh_token
            )
        except Exception as exc:
            try:
                cuentas_store.guardar_cuenta(
                    self.usuario, self.token, self.refresh_token
                )
            except Exception:
                print(f"[Auth] No se pudieron persistir los tokens: {exc}")

    def refresh(
        self,
        forzar: bool = False,
        token_que_fallo: str | None = None,
    ):
        """Renueva access+refresh. Un solo refresh a la vez."""
        with self._refresh_lock:
            # Otro hilo ya renovó mientras esperábamos el lock.
            if token_que_fallo is not None and self.token != token_que_fallo:
                return
            if not forzar and not self._token_por_vencer():
                return
            if not self.refresh_token:
                raise SessionExpired(
                    "Sesión expirada: no hay refresh token",
                    status_code=401,
                )

            try:
                resp = requests.post(
                    f"{self.base_url}/auth/refresh",
                    json={"refresh_token": self.refresh_token},
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
            except requests.exceptions.RequestException as exc:
                raise NetworkError(
                    f"No se pudo conectar con el servidor: {exc}"
                ) from exc

            if resp.status_code in (401, 403):
                detail = self._detalle_error(resp)
                self._limpiar_tokens()
                raise SessionExpired(detail, status_code=resp.status_code)
            if resp.status_code >= 400:
                raise ApiError(
                    self._detalle_error(resp),
                    status_code=resp.status_code,
                )

            data = resp.json()
            access = data.get("access_token")
            if not access:
                self._limpiar_tokens()
                raise SessionExpired(
                    "Respuesta de refresh inválida", status_code=401
                )

            self._aplicar_tokens(
                access,
                data.get("refresh_token") or self.refresh_token,
                data.get("expires_in"),
            )
            # CRÍTICO: dentro del lock, antes de liberarlo.
            self._persistir_tokens()

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs):
        if path not in ("/auth/login", "/auth/refresh"):
            if not self.token:
                raise SessionExpired(
                    "Sesión expirada: no hay access token",
                    status_code=401,
                )
            self._renovar_si_hace_falta()

        url = f"{self.base_url}{path}"
        for intento in range(2):
            token_usado = self.token
            try:
                resp = requests.request(
                    method, url,
                    headers=self._headers(),
                    timeout=60,
                    **kwargs,
                )
            except requests.exceptions.RequestException as e:
                raise NetworkError(
                    f"No se pudo conectar con el servidor: {e}"
                ) from e

            if (
                resp.status_code == 401
                and intento == 0
                and path not in ("/auth/login", "/auth/refresh")
            ):
                self.refresh(forzar=True, token_que_fallo=token_usado)
                continue

            if resp.status_code >= 400:
                detail = self._detalle_error(resp)
                if (
                    resp.status_code == 401
                    and path not in ("/auth/login", "/auth/refresh")
                ):
                    self._limpiar_tokens()
                    raise SessionExpired(detail, status_code=401)
                raise ApiError(detail, status_code=resp.status_code)

            if resp.status_code == 204 or not resp.content:
                return None
            return resp.json()

        self._limpiar_tokens()
        raise SessionExpired("Sesión expirada", status_code=401)

    # ---------------- auth ----------------
    def login(self, email: str, password: str) -> dict:
        data = self._request("POST", "/auth/login", json={"email": email, "password": password})
        self._aplicar_tokens(
            data["access_token"],
            data.get("refresh_token"),
            data.get("expires_in"),
        )
        self.usuario = data["usuario"]
        return data["usuario"]

    def logout(self):
        self._limpiar_tokens()
        self.usuario = None

    def cambiar_mi_password(self, password_actual, password_nueva):
        """PUT /usuarios/me/password — cambia la contraseña del usuario autenticado."""
        return self._request(
            "PUT",
            "/usuarios/me/password",
            json={
                "password_actual": password_actual,
                "password_nueva": password_nueva,
            },
        )

    def construir_url_avatar(self, avatar_url):
        if not avatar_url:
            return None
        if avatar_url.startswith("http"):
            return avatar_url
        return f"{self.base_url}{avatar_url}"

    def registrar(self, nombre: str, apellido: str, email: str, password: str):
        """POST /auth/registro — crea una cuenta nueva."""
        body = {
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "password": password,
        }
        return self._request("POST", "/auth/registro", json=body)

    # ---------------- proyectos ----------------
    def listar_proyectos(self, estado: str | None = "activo"):
        """GET /proyectos?estado=activo|archivado|todo"""
        params = {"estado": estado} if estado else {}
        return self._request("GET", "/proyectos", params=params)

    def crear_proyecto(
        self,
        nombre: str,
        descripcion: str | None = None,
        cliente_id: int | None = None,
        color: str | None = "#10a878",
    ):
        """POST /proyectos"""
        body = {
            "nombre": nombre,
            "descripcion": descripcion,
            "cliente_id": cliente_id,
            "estado": "ACTIVO",
            "color": color,
        }
        return self._request("POST", "/proyectos", json=body)

    # ---------------- etiquetas ----------------
    def listar_etiquetas(self, estado: str = "activo"):
        """GET /etiquetas?estado=activo|archivado|todo"""
        params = {"estado": estado}
        return self._request("GET", "/etiquetas", params=params)

    def crear_etiqueta(self, nombre: str, color: str = "#10a5f5"):
        body = {
            "nombre": nombre,
            "color": color,
        }
        return self._request("POST", "/etiquetas", json=body)

    # ---------------- rastreador: temporizador ----------------
    def obtener_temporizador_activo(self):
        return self._request("GET", "/rastreador/tiempo/activo")

    def iniciar_temporizador(
        self,
        proyecto_id: int,
        descripcion: str = "",
        tarea_id: int | None = None,
        etiquetas_ids: list[int] | None = None,
    ):
        body = {
            "proyecto_id": proyecto_id,
            "descripcion": descripcion,
            "tarea_id": tarea_id,
            "etiquetas_ids": etiquetas_ids or [],
        }
        return self._request("POST", "/rastreador/tiempo/iniciar", json=body)

    def detener_temporizador(self):
        return self._request("POST", "/rastreador/tiempo/detener")

    def historial_tiempos(
        self,
        proyecto_id: int | None = None,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
    ):
        params = {}
        if proyecto_id is not None:
            params["proyecto_id"] = proyecto_id
        if fecha_desde is not None:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta is not None:
            params["fecha_hasta"] = fecha_hasta
        return self._request("GET", "/rastreador/tiempo/historial", params=params)

    def eliminar_registro(self, registro_id: int):
        return self._request("DELETE", f"/rastreador/tiempo/{registro_id}")

    def resumen(self):
        return self._request("GET", "/rastreador/resumen")

    def ajustar_tiempo(self, registro_id: int, segundos_descontar: int):
        """Descuenta segundos de un registro activo (por inactividad)."""
        return self._request(
            "POST",
            "/rastreador/tiempo/ajustar",
            params={
                "registro_id": registro_id,
                "segundos_descontar": segundos_descontar,
            },
        )

    # ---------------- rastreador: tareas ----------------
    def listar_tareas(self, proyecto_id: int):
        return self._request("GET", "/rastreador/tareas", params={"proyecto_id": proyecto_id})

    def crear_tarea(
        self,
        titulo: str,
        proyecto_id: int,
        estado: str = "PENDIENTE",
        prioridad: str = "MEDIA",
    ):
        body = {
            "titulo": titulo,
            "proyecto_id": proyecto_id,
            "estado": estado,
            "prioridad": prioridad,
            "horas": 0.0,
            "etiqueta_ids": [],
        }
        return self._request("POST", "/rastreador/tareas", json=body)

    # ---------------- rastreador: entrada manual ----------------
    def crear_entrada_manual(
        self,
        proyecto_id: int,
        inicio: str,
        fin: str,
        tarea_id: int | None = None,
        descripcion: str | None = None,
        etiqueta_id: int | None = None,
    ):
        body = {
            "proyecto_id": proyecto_id,
            "tarea_id": tarea_id,
            "descripcion": descripcion,
            "inicio": inicio,
            "fin": fin,
            "etiqueta_id": etiqueta_id,
        }
        return self._request("POST", "/rastreador/tiempo/manual", json=body)

    # ---------------- rastreador: actividad automática ----------------
    def enviar_actividad(self, registros: list) -> dict:
        """POST /rastreador/actividad/lote — envía un lote de segmentos del rastreador."""
        return self._request(
            "POST",
            "/rastreador/actividad/lote",
            json={"registros": registros},
        )

    def obtener_actividad_dia(self, fecha_iso, page=1, limit=50):
        return self._request(
            "GET",
            "/rastreador/actividad/dia",
            params={"fecha": fecha_iso, "page": page, "limit": limit},
        )
        # ---------------- usuarios (Para el Admin) ----------------
    def listar_usuarios(self):
        """
        GET /usuarios
        Devuelve la lista de todos los usuarios (requiere ser admin).
        """
        return self._request("GET", "/usuarios")
    def obtener_actividad_dia_admin(self, usuario_id, fecha_iso, page=1, limit=50):
        """Para que un Admin vea la actividad de otro usuario (paginado)."""
        return self._request(
            "GET",
            f"/rastreador/actividad/dia/{usuario_id}",
            params={"fecha": fecha_iso, "page": page, "limit": limit},
        )