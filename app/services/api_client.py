import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "https://backendcontrolasistenciagm.onrender.com")


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    """Cliente HTTP para el backend de Control de Asistencia GM."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        self.usuario: dict | None = None

    # ---------------- helpers internos ----------------
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            resp = requests.request(method, url, headers=self._headers(), timeout=15, **kwargs)
        except requests.exceptions.RequestException as e:
            raise ApiError(f"No se pudo conectar con el servidor: {e}")

        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            raise ApiError(detail, status_code=resp.status_code)

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ---------------- auth ----------------
    def login(self, email: str, password: str) -> dict:
        data = self._request("POST", "/auth/login", json={"email": email, "password": password})
        self.token = data["access_token"]
        self.usuario = data["usuario"]
        return data["usuario"]

    def logout(self):
        self.token = None
        self.usuario = None

    # ---------------- proyectos ----------------
    def listar_proyectos(self, estado: str | None = "activo"):
        """GET /proyectos?estado=activo|archivado|todo"""
        params = {"estado": estado} if estado else {}
        return self._request("GET", "/proyectos", params=params)

    # ---------------- etiquetas ----------------
    def listar_etiquetas(self, estado: str = "activo"):
        """GET /etiquetas?estado=activo|archivado|todo"""
        params = {"estado": estado}
        return self._request("GET", "/etiquetas", params=params)

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

    # ---------------- rastreador: tareas ----------------
    def listar_tareas(self, proyecto_id: int):
        return self._request("GET", "/rastreador/tareas", params={"proyecto_id": proyecto_id})

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
        # ---------------- crear tarea ----------------
    def crear_tarea(self, titulo: str, proyecto_id: int,
                    estado: str = "PENDIENTE",
                    prioridad: str = "MEDIA"):
        body = {
            "titulo": titulo,
            "proyecto_id": proyecto_id,
            "estado": estado,
            "prioridad": prioridad,
            "horas": 0.0,
            "etiqueta_ids": [],
        }
        return self._request("POST", "/rastreador/tareas", json=body)

    # ---------------- crear etiqueta ----------------
    def crear_etiqueta(self, nombre: str, color: str = "#10a5f5"):
        body = {
            "nombre": nombre,
            "color": color,
        }
        return self._request("POST", "/etiquetas", json=body)