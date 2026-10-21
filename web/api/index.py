"""Punto de entrada de Vercel: /api/login, /api/vista, /api/accion."""
import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "motor"))

import servicio  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _responder(self, codigo: int, cuerpo: dict):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _sesion(self) -> dict:
        auth = self.headers.get("Authorization", "")
        return servicio.leer_sesion(auth.removeprefix("Bearer ").strip())

    def _cuerpo(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 4_500_000:
            raise servicio.Error("Demasiado grande", 413)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def _manejar(self, metodo: str):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        ruta = q.get("r") or url.path.rstrip("/").split("/")[-1]
        try:
            if metodo == "POST" and ruta not in ("login", "compartir", "crear_perfil", "abonarse", "datos_pago", "contactar", "me_gusta", "chat", "tg_webhook"):
                servicio.solo_lectura(self._sesion())  # la demo no puede guardar nada
            if ruta == "estado" and metodo == "GET":
                return self._responder(200, servicio.estado())
            if ruta == "login" and metodo == "POST":
                return self._responder(200, servicio.login(self._cuerpo()))
            if ruta == "vista" and metodo == "GET":
                return self._responder(200, servicio.vista(self._sesion(), q.get("atleta"),
                                                           int(q["semana"]) if q.get("semana") else None,
                                                           q.get("dia")))
            if ruta == "registrar" and metodo == "POST":
                return self._responder(200, servicio.registrar(self._sesion(), self._cuerpo()))
            if ruta in ("historial", "progreso", "prs") and metodo == "GET":
                return self._responder(200, getattr(servicio, ruta)(self._sesion(), q.get("atleta")))
            if ruta == "borrar_entreno" and metodo == "POST":
                return self._responder(200, servicio.borrar_entreno(self._sesion(), self._cuerpo()))
            if ruta == "guardar_pr" and metodo == "POST":
                return self._responder(200, servicio.guardar_pr(self._sesion(), self._cuerpo()))
            if ruta == "limpiar_biblioteca" and metodo == "POST":
                return self._responder(200, servicio.limpiar_biblioteca(self._sesion(), self._cuerpo()))
            if ruta == "ideas" and metodo == "GET":
                self._sesion()
                return self._responder(200, servicio.ideas())
            if ruta == "fijar_perfil" and metodo == "POST":
                return self._responder(200, servicio.fijar_perfil(self._sesion(), self._cuerpo()))
            if ruta == "crear_perfil" and metodo == "POST":
                return self._responder(200, servicio.crear_perfil(self._sesion(), self._cuerpo()))
            if ruta == "datos_pago" and metodo == "POST":
                try:
                    ses = self._sesion()
                except servicio.Error:
                    ses = None  # vuelve de Stripe sin sesión: vale con el id del pago
                return self._responder(200, servicio.datos_pago(ses, self._cuerpo()))
            if ruta == "chat":
                if metodo == "POST":
                    return self._responder(200, servicio.chat(self._sesion(), self._cuerpo(), "POST"))
                return self._responder(200, servicio.chat(self._sesion(), q, "GET"))
            if ruta == "tg_webhook" and metodo == "POST":
                return self._responder(200, servicio.tg_webhook(self.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), self._cuerpo()))
            if ruta == "portal_abono" and metodo == "POST":
                return self._responder(200, servicio.portal_abono(self._sesion()))
            if ruta == "objetivos" and metodo == "POST":
                return self._responder(200, servicio.objetivos(self._sesion(), self._cuerpo()))
            if ruta == "exento" and metodo == "POST":
                return self._responder(200, servicio.exento(self._sesion(), self._cuerpo()))
            if ruta == "pago_visto" and metodo == "POST":
                return self._responder(200, servicio.pago_visto(self._sesion(), self._cuerpo()))
            if ruta == "telegram" and metodo == "POST":
                return self._responder(200, servicio.telegram(self._sesion(), self._cuerpo()))
            if ruta == "me_gusta" and metodo == "POST":
                return self._responder(200, servicio.me_gusta(self._sesion(), self._cuerpo()))
            if ruta == "contactar" and metodo == "POST":
                return self._responder(200, servicio.contactar(self._sesion(), self._cuerpo()))
            if ruta == "abonarse" and metodo == "POST":
                return self._responder(200, servicio.abonarse(self._sesion(), self._cuerpo()))
            if ruta == "compartir" and metodo == "POST":
                return self._responder(200, servicio.compartir(self._sesion(), self._cuerpo()))
            if ruta == "actividad" and metodo == "GET":
                return self._responder(200, servicio.actividad(self._sesion()))
            if ruta == "coach" and metodo == "POST":
                return self._responder(200, servicio.modo_coach(self._sesion(), self._cuerpo()))
            if ruta == "resolver" and metodo == "POST":
                return self._responder(200, servicio.resolver_solicitud(self._sesion(), self._cuerpo()))
            if ruta == "accion" and metodo == "POST":
                return self._responder(200, servicio.accion(self._sesion(), self._cuerpo()))
            return self._responder(404, {"error": "No existe"})
        except servicio.Error as e:
            return self._responder(e.codigo, {"error": str(e)})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._responder(500, {"error": f"Error del servidor: {e}"})

    def do_GET(self):
        self._manejar("GET")

    def do_POST(self):
        self._manejar("POST")
