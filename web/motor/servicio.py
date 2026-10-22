"""Djimenez Prog — servidor de la app nueva.

Usa la MISMA lógica (logica.py, rutinas_iniciales.py…) y los MISMOS datos de Supabase que la app de Streamlit,
así que las dos funcionan a la vez sobre lo mismo. Sin dependencias: solo la librería estándar de Python.

Variables de entorno (en Vercel → Settings → Environment Variables):
  SUPABASE_URL, SUPABASE_KEY      la misma url y clave sb_secret_… que en los secrets de Streamlit
  APP_PASSWORD                    contraseña general (ve a todos)
  CONTRASENA_DIEGO                opcional: la de Diego. Si está puesta, con la general cada uno elige su perfil y no puede ser «Diego»
  CONTRASENA_ARCHCHANA            contraseña solo de Archchana
  CONTRASENA_INVITADOS            contraseña para invitados (nombre + PIN)
  CONTRASENA_DEMO                 opcional: contraseña de "solo mirar" para enseñar la app (no puede cambiar nada)
  DEMO_ATLETAS                    opcional: qué rutinas se ven en la demo, separadas por comas (por defecto "Yo,Archchana,Manu Anel,Salatti")
  ABONO_URL                       opcional: enlace de pago de Stripe (Payment Link) para el botón «Abonarse»
  ABONO_TEXTO                     opcional: precio que se enseña en el botón, p. ej. "30 €/mes"
  CONTACTO_WHATSAPP / CONTACTO_EMAIL / CONTACTO_INSTAGRAM   opcional: tu contacto (sale mientras no haya pago)
  ACCESOS_PERSONALES              opcional, JSON {"Salatti": "su-clave", …}
  SESION_SECRETO                  opcional; si falta se deriva de las otras claves
  APP_ANTIGUA_URL                 opcional: enlace a la app de Streamlit (para lo que aún no está aquí)
"""
from __future__ import annotations

import base64
import copy
import datetime as dt
import hashlib
import hmac
import json
import re
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from logica import (
    NIVELES, NUM_PESO, _etiqueta_parte, agrupar_por_parte, quitar_parte, cambiar_pesos, copiar_rutina, destino_dia_siguiente,
    destino_semana_siguiente, editar_texto_linea, es_metcon, escalar, estado_parte, fmt_num, historial_parte,
    letra_visible, linea_activa, linea_no_hecha, marcar_linea, marcar_parte, no_hechas_en, norm, norm_busqueda,
    parametros_semana, partes_del_dia, pendientes_para, poner_pesos, prescripcion_semana, referencias_elite,
    resumen_dia, se_repite, semanas_que_sube, sin_validar, tipo_de_linea, versiones_por_movimiento,
    TIPOS, UNIDADES, duracion_emom, tope_db_alumno, formato_de, mejores_prs, parse_tiempo, parse_valor, peso_principal, fmt_valor,
    prs_de_entrenos, series_ejercicios, mejor_punto, cambio_pct, ids_con_pr, consejos, sesiones_por_semana,
    CATALOGO_PR, movimiento_pr, mover_parte, fmt_tiempo, a_fecha, anadir_parte, sustituir_parte, deshacer_sustitucion, CLAVE_BIBLIOTECA, CLAVES_BIBLIO,
)
from repertorio import CASA, ELITE, PRINCIPIANTE, REPERTORIO
from rutinas_iniciales import migrar, rutinas_iniciales, _yo as _rutina_base_yo, _manu, _salatti, _archchana
import cuestionario
from propuestas import propuesta_para
import propuestas as _propuestas
from ciclos import CICLOS

# ===== personas (igual que en app.py) =====
ATLETAS = ["Yo", "Manu Anel", "Salatti", "Mi esposa", "Dario", "Archchana", "Juan"]
ORDEN_VISTA = ["Yo", "Mi esposa", "Manu Anel", "Salatti", "Dario", "Archchana", "Juan"]
NOMBRE_VISIBLE = {"Yo": "Diego"}
IDIOMA_DEFECTO = {"Archchana": "fr"}
NIVEL_DEFECTO = {"Yo": "RX"}
ALUMNOS = ["Salatti", "Dario", "Juan", "Mi esposa", "Manu Anel"]
ABRE_DIA_PENDIENTE = ("Yo", "Mi esposa")
MOVILIDAD_ES_PARTE = ["Archchana"]  # para ella la movilidad es una parte más (A, B…); para el resto es el Warm up
SIN_PRS = ["Archchana"]
CLAVE_PRS = "__prs__"
CLAVE_SOLICITUDES = "__solicitudes__"
CLAVE_NOVEDADES = "__novedades__"
TIPOS_PARTE = ["WOD", "EMOM", "For time", "AMRAP", "Conditioning", "Conditioning & Volume", "Accessory", "Mobility",
               "Fuerza", "Gym"]
# Conditioning & Volume: motor largo y suave + un skill en poca cantidad cada X minutos (se acumula mucho volumen)
VOLUMEN = [
    ("40' bike + T2B", "40' bike suave (Z2)\nEvery 2': 2-4 toes to bar"),
    ("40' bike + rings", "40' bike suave (Z2)\nEvery 2': 1-2 ring muscle ups (o 3 strict dips + 3 ring rows)"),
    ("40' bike + DB", "40' bike suave (Z2)\nEvery 2': 4 DB snatch alternos"),
    ("30' row + HSPU", "30' row suave (Z2)\nEvery 2': 2-3 HSPU (o 5 pike push ups)"),
    ("45' mix + DU", "45' alternando 5' bike / 5' row / 5' ski\nEvery 3': 20 double unders"),
    ("36' ski + pull ups", "36' ski suave\nEvery 3': 3 strict pull ups"),
    ("40' run/bike + pistols", "40' (10' run, 10' bike, x2) suave\nEvery 4': 3+3 pistols"),
    ("30' bike + C2B", "30' bike suave\nEvery 2': 2 chest to bar"),
]
PROTEGIDOS = ["Yo", "Diego", "Manu Anel", "Salatti", "Mi esposa", "Dario", "Juan", "Archchana"]
CLAVE_INVITADOS = "__invitados__"
CLAVE_ACTIVIDAD = "__actividad__"
CLAVE_CONFIG = "__config__"  # ajustes privados del coach (p. ej. el bot de Telegram); nunca se mandan al navegador
CLAVE_VIDEOS = "__videos__"  # {ejercicio normalizado: {"url", "titulo"}} que pone el coach
VIDEOS_BASE: dict = {}  # quién abre la app y cuándo (solo lo ve el coach)
PLANTILLAS = {"Salatti": "Rutina de Salatti", "Dario": "Rutina de Dario"}
TIPOS_WOD = ("wod", "emom", "fortime", "amrap")


class Error(Exception):
    def __init__(self, mensaje: str, codigo: int = 400):
        super().__init__(mensaje)
        self.codigo = codigo


def env(nombre: str, defecto: str = "") -> str:
    v = (os.environ.get(nombre) or defecto).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":  # si se pegó con comillas, como en los secrets de Streamlit
        v = v[1:-1].strip()
    return v


def nv(atleta: str) -> str:
    return NOMBRE_VISIBLE.get(atleta, atleta)


# ===== datos =====
class Supabase:
    """La tabla `rutinas` (athlete, data) por la API REST de Supabase."""

    def __init__(self, url: str, key: str):
        u = urllib.parse.urlparse(url.strip() if "://" in url else "https://" + url.strip())
        self.base = f"{u.scheme}://{u.netloc}/rest/v1"  # solo el dominio, aunque se pegue con /rest/v1 u otra cosa detrás
        self.h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _pedir(self, metodo: str, ruta: str, cuerpo=None, extra: dict | None = None):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode() if cuerpo is not None else None
        req = urllib.request.Request(self.base + ruta, data=datos, method=metodo, headers={**self.h, **(extra or {})})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                txt = r.read().decode() or "null"
                return json.loads(txt)
        except urllib.error.HTTPError as e:
            raise Error(f"Supabase {e.code} en {self.base}{ruta.split('?')[0]}: {e.read().decode()[:300]}", 502)

    def rutinas(self, nombres: list[str]) -> dict:
        lista = ",".join('"' + n.replace('"', '') + '"' for n in nombres)
        filas = self._pedir("GET", "/rutinas?select=athlete,data&athlete=in.(" + urllib.parse.quote(lista) + ")")
        return {f["athlete"]: f["data"] for f in filas or []}

    def entrenos(self, atleta: str, limite: int = 400) -> list[dict]:
        return self._pedir("GET", "/workouts?select=*&athlete=eq." + urllib.parse.quote(atleta)
                           + f"&order=date.desc,created_at.desc&limit={limite}") or []

    def insertar_entreno(self, w: dict):
        self._pedir("POST", "/workouts", w, {"Prefer": "return=minimal"})

    def borrar_entreno(self, w: dict):
        self._pedir("DELETE", "/workouts?id=eq." + urllib.parse.quote(str(w["id"])), None, {"Prefer": "return=minimal"})
        if w.get("photo_path"):
            host = self.base.rsplit("/rest/v1", 1)[0]
            try:
                req = urllib.request.Request(f"{host}/storage/v1/object/fotos/{urllib.parse.quote(w['photo_path'])}",
                                             method="DELETE", headers=self.h)
                urllib.request.urlopen(req, timeout=15).read()
            except Exception:  # noqa: BLE001
                pass

    def url_foto(self, ruta: str) -> str:
        return self.base.rsplit("/rest/v1", 1)[0] + "/storage/v1/object/public/fotos/" + urllib.parse.quote(ruta)

    def subir_foto(self, ruta: str, jpg: bytes) -> str:
        host = self.base.rsplit("/rest/v1", 1)[0]
        req = urllib.request.Request(f"{host}/storage/v1/object/fotos/{urllib.parse.quote(ruta)}", data=jpg,
                                     method="POST", headers={**self.h, "Content-Type": "image/jpeg"})
        try:
            urllib.request.urlopen(req, timeout=30).read()
        except urllib.error.HTTPError as e:
            raise Error(f"No se pudo subir la foto ({e.code}): {e.read().decode()[:200]}", 502)
        return ruta

    def borrar_fila(self, atleta: str):
        self._pedir("DELETE", "/rutinas?athlete=eq." + urllib.parse.quote(atleta), None, {"Prefer": "return=minimal"})

    def guardar(self, atleta: str, data: dict):
        self._pedir("POST", "/rutinas", {"athlete": atleta, "data": data,
                                         "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()},
                    {"Prefer": "resolution=merge-duplicates,return=minimal"})


class Local:
    """Para probar sin Supabase: un JSON en disco."""

    def __init__(self, ruta: str):
        self.ruta = Path(ruta)

    def _todo(self) -> dict:
        return json.loads(self.ruta.read_text()) if self.ruta.exists() else {}

    def rutinas(self, nombres: list[str]) -> dict:
        t = self._todo()
        return {n: t[n] for n in nombres if n in t}

    def guardar(self, atleta: str, data: dict):
        t = self._todo()
        t[atleta] = data
        self.ruta.write_text(json.dumps(t, ensure_ascii=False))

    def borrar_fila(self, atleta: str):
        t = self._todo()
        t.pop(atleta, None)
        self.ruta.write_text(json.dumps(t, ensure_ascii=False))

    def entrenos(self, atleta: str, limite: int = 400) -> list[dict]:
        ws = [w for w in self._todo().get("__workouts__", []) if w["athlete"] == atleta]
        return sorted(ws, key=lambda w: (w["date"], w["created_at"]), reverse=True)[:limite]

    def insertar_entreno(self, w: dict):
        t = self._todo()
        t.setdefault("__workouts__", []).append(w)
        self.ruta.write_text(json.dumps(t, ensure_ascii=False))

    def borrar_entreno(self, w: dict):
        t = self._todo()
        t["__workouts__"] = [x for x in t.get("__workouts__", []) if x["id"] != w["id"]]
        self.ruta.write_text(json.dumps(t, ensure_ascii=False))

    def url_foto(self, ruta: str) -> str:
        return ""

    def subir_foto(self, ruta: str, jpg: bytes) -> str:
        carpeta = self.ruta.parent / "fotos-local"
        (carpeta / ruta).parent.mkdir(parents=True, exist_ok=True)
        (carpeta / ruta).write_bytes(jpg)
        return ruta


_DATOS = None


def datos():
    global _DATOS
    if _DATOS is None:
        if env("SUPABASE_URL") and env("SUPABASE_KEY"):
            _DATOS = Supabase(env("SUPABASE_URL"), env("SUPABASE_KEY"))
        else:
            _DATOS = Local(env("DATOS_LOCALES", "/tmp/djimenez-datos.json"))
    return _DATOS


def invitados() -> dict:
    return datos().rutinas([CLAVE_INVITADOS]).get(CLAVE_INVITADOS) or {}


def todas_las_personas(inv: dict | None = None) -> list[str]:
    inv = invitados() if inv is None else inv
    return ORDEN_VISTA + [n for n in inv if n not in ATLETAS]


def completar(rut: dict | None, atleta: str) -> dict | None:
    """Igual que _completar_partes de app.py: migraciones + partes que faltan."""
    if not rut:
        return rut
    rut = migrar(copy.deepcopy(rut), atleta, ATLETAS)
    semilla = {l["id"]: l.get("parte") for d in (rutinas_iniciales(ATLETAS).get(atleta) or {}).get("dias", [])
               for l in d["lineas"]}
    for d in rut["dias"]:
        for l in d["lineas"]:
            if not l.get("parte") and semilla.get(l["id"]):
                l["parte"] = semilla[l["id"]]
        for l, p in zip(d["lineas"], partes_del_dia(d)):
            l.setdefault("parte", p)
    return rut


LIMPIAR_EXTRA = {"ruchama": "C"}  # perfiles que no deben tener partes más allá de esa letra (limpieza única)


def _limpiar_extra(rut: dict | None, atleta: str) -> dict | None:
    """Quita (desde la semana actual) las partes añadidas después de la C a quien solo debe tener A-C."""
    tope = next((v for k, v in LIMPIAR_EXTRA.items() if (atleta or "").strip().lower().startswith(k)), None)
    if not rut or not tope or rut.get("limpio_extra") == tope or not rut.get("dias"):
        return rut
    sem = int(rut.get("semana_actual") or 1)
    for d in list(rut["dias"]):
        for p, _ in agrupar_por_parte(d):
            if (p[:1].upper() > tope) and p[1:2] == ")":
                rut = quitar_parte(rut, d["id"], p, sem)
    rut = dict(rut, limpio_extra=tope)
    datos().guardar(atleta, rut)
    return rut


# Cambios puntuales que pide Diego para la semana en curso de alguien (se ponen una sola vez, «solo esta semana»).
# partes: letra → (etiqueta, nombre, texto). dia: posición del día (0 = día 1). Caduca en `hasta` si no se ha aplicado.
CAMBIOS_PUNTUALES = [
    {"id": "salatti-d3-v3-2026-10", "atleta": "Salatti", "dia": 2, "hasta": "2026-10-29",
     "reemplaza": (("salatti-d3-gym-2026-10", "salatti-d3-v2-2026-10"),
                   ("EMOM gym", "Conditioning", "WOD mancuernas", "Mini conditioning")), "partes": {
        "A": ("Gym", "EMOM gym", "EMOM 10': 3 pull ups + 2 toes to bar cada minuto", {
            "RX": "EMOM 10': 3 pull ups + 2 toes to bar cada minuto",
            "Inter": "EMOM 10': 2 pull ups + 2 toes to bar cada minuto",
            "Scaled": "EMOM 10': 2 jumping pull ups + 2 hanging knee raises cada minuto"}),
        "B": ("WOD", "WOD mancuernas", "AMRAP 12': 10 DB snatch alternos 22,5/15 kg, 10 DB goblet squats 22,5/15 kg, "
                                       "8 burpees sobre la mancuerna"),
        "C": ("Conditioning", "Mini conditioning", "20' (4 vueltas): 3' row + 2' bike · ritmo constante, que puedas hablar"),
    }},
    {"id": "salatti-d4-wod40-2026-10", "atleta": "Salatti", "dia": 3, "hasta": "2026-10-29", "partes": {
        "B": ("WOD", "WOD largo 40'", "AMRAP 40' (ritmo constante, sin parar): 400 m run, 20 wall balls 9/6 kg, "
                                      "15 KB swings 24/16 kg, 12 box jumps, 8 pull ups"),
    }},
]


def _cambios_puntuales(rut: dict | None, atleta: str) -> dict | None:
    if not rut or not rut.get("dias"):
        return rut
    hechos = set(rut.get("puntuales") or [])
    pend = [x for x in CAMBIOS_PUNTUALES if x["atleta"] == atleta and x["id"] not in hechos
            and dt.date.today().isoformat() <= x["hasta"] and x["dia"] < len(rut["dias"])]
    if not pend:
        return rut
    sem = int(rut.get("semana_actual") or 1)
    for x in pend:
        dia_id = rut["dias"][x["dia"]]["id"]
        sem_x = sem
        viejos, nombres = x.get("reemplaza") or ((), ())
        if set(viejos) & hechos:  # deshace el cambio puntual anterior (en la semana en que se puso)
            dia = next(d for d in rut["dias"] if d["id"] == dia_id)
            for l in [l for l in dia["lineas"] if l.get("sustituye") and l.get("ejercicio") in nombres]:
                sem_x = int(l.get("desde") or sem)
                rut = deshacer_sustitucion(rut, dia_id, l["parte"], sem_x)
            dia = next(d for d in rut["dias"] if d["id"] == dia_id)
            dia["lineas"] = [l for l in dia["lineas"] if not (l.get("ejercicio") in nombres and l.get("plan") and not l.get("sustituye"))]
        for letra, (etq, nombre, texto, *niveles) in x["partes"].items():
            actual = next((p for p, _ in agrupar_por_parte(next(d for d in rut["dias"] if d["id"] == dia_id))
                           if p[:1].upper() == letra), None)
            if actual:
                rut = sustituir_parte(rut, dia_id, actual, sem_x, etq, nombre, texto, True)
            else:
                rut = anadir_parte(rut, dia_id, etq, nombre, texto, sem_x, True)
            if niveles:  # versiones a mano para la pestaña RX · Inter · Scaled
                dia = next(d for d in rut["dias"] if d["id"] == dia_id)
                dia["lineas"][-1 if not actual else next(i for i, l in enumerate(dia["lineas"])
                                                         if l.get("ejercicio") == nombre and l.get("desde") == sem_x)]["niveles_txt"] = niveles[0]
        rut = dict(rut, puntuales=sorted(set(rut.get("puntuales") or []) | {x["id"]}))
    datos().guardar(atleta, rut)
    return rut


def rutina(atleta: str, guardadas: dict | None = None) -> dict | None:
    guardadas = datos().rutinas([atleta]) if guardadas is None else guardadas
    r = _cambios_puntuales(_limpiar_extra(guardadas.get(atleta), atleta), atleta)
    return completar(r or rutinas_iniciales(ATLETAS).get(atleta), atleta)


# ===== sesión =====
def _secreto() -> bytes:
    s = env("SESION_SECRETO") or (env("APP_PASSWORD") + "|" + env("SUPABASE_KEY") + "|djimenez")
    return hashlib.sha256(s.encode()).digest()


def firmar(datos_sesion: dict) -> str:
    cuerpo = base64.urlsafe_b64encode(json.dumps(datos_sesion).encode()).decode().rstrip("=")
    firma = hmac.new(_secreto(), cuerpo.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{cuerpo}.{firma}"


def leer_sesion(token: str) -> dict:
    try:
        cuerpo, firma = (token or "").split(".", 1)
        ok = hmac.compare_digest(firma, hmac.new(_secreto(), cuerpo.encode(), hashlib.sha256).hexdigest()[:32])
        s = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
    except Exception:
        raise Error("Sesión no válida", 401)
    if not ok or s.get("exp", 0) < time.time():
        raise Error("La sesión ha caducado, entra otra vez", 401)
    return s


def _sesion_para(solo: str | None, coach: bool = False, demo: bool = False, diego: bool = False) -> dict:
    datos_s = {"u": solo or "", "exp": int(time.time()) + (14 if demo else 120) * 86400}
    if diego:
        datos_s["y"] = 1
    if coach:
        datos_s["c"] = 1
    if demo:
        datos_s["d"] = 1
    lang = IDIOMA_DEFECTO.get(solo or "")
    if not lang and solo:
        try:
            lang = (invitados().get(solo) or {}).get("lang")
        except Exception:  # noqa: BLE001
            lang = None
    # sin idioma guardado → None: la app se queda en el idioma del móvil (antes forzaba español)
    return {"token": firmar(datos_s), "solo": solo, "lang": lang, "coach": coach, "demo": demo}


MENSAJE_DEMO = "👀 Esto es una demo: aquí solo se puede mirar. Si te gusta, ¡díselo a Diego!"


def es_demo(sesion: dict) -> bool:
    return bool(sesion.get("d"))


def solo_lectura(sesion: dict) -> None:
    """La demo puede mirarlo todo pero no cambia nada (ni pesos, ni registros, ni modo coach)."""
    if es_demo(sesion):
        raise Error(MENSAJE_DEMO, 403)


def es_coach(sesion: dict) -> bool:
    return bool(sesion.get("c")) and bool(env("COACH_PIN"))


def modo_coach(sesion: dict, c: dict) -> dict:
    """Activa (con el PIN del coach) o quita el modo coach. Devuelve una sesión nueva."""
    solo_lectura(sesion)
    if c.get("salir"):
        return _sesion_para(sesion.get("u") or None, False, diego=bool(sesion.get("y")))
    pin = env("COACH_PIN")
    if not pin:
        raise Error("Falta COACH_PIN en las variables de Vercel", 500)
    if not _igual(str(c.get("pin") or ""), pin):
        time.sleep(0.8)  # frena a quien pruebe PINs al azar
        raise Error("PIN incorrecto", 403)
    return _sesion_para(sesion.get("u") or None, True, diego=bool(sesion.get("y")))


def _limpia(txt: str) -> str:
    """Para comparar contraseñas: sin comillas alrededor, sin espacios de más, mismos acentos."""
    import unicodedata
    v = unicodedata.normalize("NFC", str(txt or "")).replace("\u00a0", " ").strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return " ".join(v.split())


def _igual(a: str, b: str) -> bool:
    a, b = _limpia(a), _limpia(b)
    return bool(a) and bool(b) and hmac.compare_digest(a.encode(), b.encode())


VERSION = "11.16"
CLAVES_NECESARIAS = ["CONTRASENA_DIEGO", "SUPABASE_URL", "SUPABASE_KEY", "APP_PASSWORD", "CONTRASENA_ARCHCHANA", "CONTRASENA_INVITADOS", "COACH_PIN",
                     "APP_ANTIGUA_URL", "CONTRASENA_DEMO"]


def estado() -> dict:
    """Qué variables le llegan al servidor (nunca su valor) y si los datos responden."""
    out = {"version": VERSION}
    for k in CLAVES_NECESARIAS:
        crudo = os.environ.get(k)
        if crudo is None:
            out[k] = "FALTA"
            continue
        avisos = []
        if crudo != crudo.strip():
            avisos.append("espacios al principio o al final")
        if crudo.strip()[:1] in "\"'" and crudo.strip()[-1:] == crudo.strip()[:1]:
            avisos.append("tiene comillas")
        out[k] = "ok" + (" · " + ", ".join(avisos) if avisos else "")
    if isinstance(datos(), Supabase):
        out["SUPABASE_URL"] += " · se usa " + datos().base
    try:
        n = len(datos().rutinas(ATLETAS))
        out["datos"] = f"ok · {n} rutinas en {'Supabase' if isinstance(datos(), Supabase) else 'modo local (faltan claves de Supabase)'}"
    except Exception as e:  # noqa: BLE001
        out["datos"] = f"ERROR: {e}"[:300]
    return out


def _hash(nombre: str, pin: str) -> str:
    return hashlib.sha256(f"{nombre.lower()}|{pin}".encode()).hexdigest()


def login(cuerpo: dict) -> dict:
    if cuerpo.get("perfil"):
        return _login_perfil(cuerpo)
    if cuerpo.get("inv"):
        return _login_invitacion(str(cuerpo["inv"]))
    if cuerpo.get("origen") == "instagram":  # enlace fijo de la bio de Instagram: entra directo a la demo (solo mirar)
        if not env("CONTRASENA_DEMO"):
            raise Error("La demo no está activa ahora mismo. Escríbele a Diego.", 401)
        _apuntar_actividad(lambda act: _sumar(act.setdefault("llegadas", {}), "Instagram"))
        _apuntar(None, {"d": 1}, "Demo", entrada=True)
        return _sesion_para(demo_personas()[0], demo=True)
    intento = str(cuerpo.get("password") or "").strip()
    if not intento:
        raise Error("Escribe la contraseña")
    general = env("APP_PASSWORD")
    if not general:
        raise Error("Falta APP_PASSWORD en las variables de Vercel", 500)
    personales = {}
    try:
        personales = {k: str(v).strip() for k, v in json.loads(env("ACCESOS_PERSONALES") or "{}").items()}
    except ValueError:
        pass
    if env("CONTRASENA_ARCHCHANA"):
        personales["Archchana"] = env("CONTRASENA_ARCHCHANA")
    if _igual(intento, env("CONTRASENA_DIEGO")):
        return _sesion_para(None, diego=True)
    if _igual(intento, general):
        return _sesion_para(None)
    for nombre, clave in personales.items():
        if _igual(intento, clave):
            return _sesion_para(nombre)
    if _igual(intento, env("CONTRASENA_DEMO")):
        _apuntar(None, {"d": 1}, "Demo", entrada=True)
        return _sesion_para(demo_personas()[0], demo=True)
    inv_clave = env("CONTRASENA_INVITADOS")
    if _igual(intento, inv_clave):
        return _login_invitado(cuerpo)
    raise Error("Contraseña incorrecta · Mot de passe incorrect", 401)


def _login_invitado(cuerpo: dict) -> dict:
    nombre = " ".join(str(cuerpo.get("nombre") or "").split()).title()
    pin = str(cuerpo.get("pin") or "").strip()
    if not nombre or not pin:
        return {"invitado": True, "plantillas": PLANTILLAS}
    if norm_busqueda(nombre) in {norm_busqueda(p) for p in PROTEGIDOS + ["Diego"]}:
        raise Error("Ese nombre no está disponible. Usa otro, por ejemplo con tu apellido.")
    if len(pin) < 4:
        raise Error("El PIN tiene que tener al menos 4 cifras.")
    registro = dict(invitados())
    existente = next((n for n in registro if norm_busqueda(n) == norm_busqueda(nombre)), None)
    if existente:
        if not hmac.compare_digest(registro[existente].get("pin", ""), _hash(existente, pin)):
            raise Error("PIN incorrecto para ese nombre · Code incorrect", 401)
        return _sesion_para(existente)
    plantilla = cuerpo.get("plantilla")
    if plantilla not in PLANTILLAS:
        return {"invitado": True, "nuevo": True, "plantillas": PLANTILLAS}
    if not cuerpo.get("acepta"):
        raise Error("Tienes que aceptar la política de privacidad y las condiciones para crear tu perfil · "
                    "Accepte la politique de confidentialité et les conditions pour créer ton profil")
    registro[nombre] = {"pin": _hash(nombre, pin), "alta": dt.date.today().isoformat(), "plantilla": plantilla,
                        "revision": "pendiente",  # no ve su rutina hasta que Diego la aprueba
                        "consentimiento": {"fecha": _ahora().isoformat(timespec="minutes"), "version": VERSION_LEGAL,
                                           "salud": bool(cuerpo.get("salud"))},
                        **({"lang": cuerpo["lang"]} if cuerpo.get("lang") in ("es", "fr") else {})}
    datos().guardar(CLAVE_INVITADOS, registro)
    _rutina_inicio(nombre, plantilla)
    return _sesion_para(nombre)


def _rutina_inicio(nombre: str, plantilla: str | None) -> dict | None:
    """Copia la rutina de partida (plantilla) para un perfil nuevo. Si algo falló al crearlo, se vuelve a llamar sola."""
    import uuid
    resp = (invitados().get(nombre) or {}).get("cuestionario")
    if resp:
        try:
            return _rutina_cuestionario(nombre, resp)[0]
        except Exception:  # noqa: BLE001
            pass
    base = rutina(plantilla if plantilla in PLANTILLAS else next(iter(PLANTILLAS)))
    if not base:
        return None
    nueva = copiar_rutina(base, lambda: uuid.uuid4().hex[:8])
    nueva["nivel"] = base.get("nivel") or "Inter"
    nueva["semana_actual"] = 1
    nueva.pop("estados", None)
    nueva.pop("permiso_pesos", None)
    datos().guardar(nombre, nueva)
    return nueva


def _propuesta_pendiente(atleta: str, rut: dict | None) -> dict | None:
    p = propuesta_para(atleta)
    if not p or (rut or {}).get("propuesta_aplicada") == p["id"] or p["id"] in ((rut or {}).get("propuestas_descartadas") or []):
        return None
    return {"id": p["id"], "titulo": p["titulo"],
            "dias": [{"nombre": d["nombre"], "partes": list(dict.fromkeys(l["parte"] for l in d["lineas"])),
                      "lineas": [f"{l['ejercicio']}: {l['prescripcion']}" for l in d["lineas"]]} for d in p["dias"]]}


def _sugerencia_alumno(sesion: dict, atleta: str, rut: dict | None) -> dict:
    """Al propio alumno: «Diego te sugiere este cambio» (si la rutina preparada es para sugerírsela)."""
    if es_demo(sesion) or es_coach(sesion) or sesion.get("u") != atleta:
        return {}
    p = propuesta_para(atleta)
    if not p:
        return {}
    pend = _propuesta_pendiente(atleta, rut) if p.get("sugerir") else None
    if pend:
        return {"sugerencia_diego": pend}
    if (rut or {}).get("propuesta_aplicada") == p["id"] and (rut or {}).get("propuesta_vista") != p["id"]:
        return {"programa_actualizado": True}
    return {}


def propuestas_pendientes(inv: dict | None = None) -> list[dict]:
    """Rutinas preparadas que Diego aún no ha aplicado ni descartado (para la lista del coach y el aviso)."""
    inv = invitados() if inv is None else inv
    gente = [p for p in todas_las_personas(inv) if propuesta_para(p)]
    if not gente:
        return []
    ruts = datos().rutinas(gente)
    out = []
    for n in gente:
        x = _propuesta_pendiente(n, completar(ruts.get(n), n) if ruts.get(n) else None)
        if x:
            out.append({"atleta": n, "nombre": nv(n), "titulo": x["titulo"], "id": x["id"]})
    return out


def _avisar_propuestas(guardadas: dict) -> None:
    """Una vez por rutina preparada: «Diego, tienes una rutina lista para X»."""
    try:
        cfg = dict(guardadas.get(CLAVE_CONFIG) or {})
        hechas = set(cfg.get("propuestas_avisadas") or [])
        nuevas = [x for x in propuestas_pendientes() if f"{x['atleta']}:{x['id']}" not in hechas]
        if not nuevas:
            return
        for x in nuevas:
            notificar(f"📋 Rutina nueva preparada para {x['nombre']}: {x['titulo']}\n"
                      "Ábrela en la app (modo coach → su rutina) y dale a ✅ Aplicar si te convence.")
        reg = dict(datos().rutinas([CLAVE_CONFIG]).get(CLAVE_CONFIG) or {})
        reg["propuestas_avisadas"] = sorted(hechas | {f"{x['atleta']}:{x['id']}" for x in nuevas})
        datos().guardar(CLAVE_CONFIG, reg)
    except Exception:  # noqa: BLE001
        pass


def aplicar_propuesta(rut: dict | None, atleta: str, descartar: bool = False) -> tuple[dict, str]:
    """Pone la rutina preparada (empieza en la semana en la que está; las marcas anteriores se quedan)."""
    p = propuesta_para(atleta)
    if not p:
        raise Error("No hay ninguna rutina preparada para esta persona")
    rut = copy.deepcopy(rut or {"semana_actual": 1, "ajustes": {}, "dias": []})
    if descartar:
        rut["propuestas_descartadas"] = list(set((rut.get("propuestas_descartadas") or []) + [p["id"]]))
        return rut, "Vale, no la aplico"
    sem = int(rut.get("semana_actual") or 1)
    anterior = {"dias": rut.get("dias"), "fecha": dt.date.today().isoformat()}
    dias = copy.deepcopy(p["dias"])
    for d in dias:
        d["id"] = f"{p['id']}-{d['id']}"
        for l in d["lineas"]:
            l["id"] = f"{p['id']}-{l['id']}"
            l["base"] = sem
    rut.update(dias=dias, nivel=p.get("nivel") or rut.get("nivel"), propuesta_aplicada=p["id"], rutina_anterior=anterior)
    return rut, "Rutina nueva aplicada ✅ (empieza esta semana)"


def _info_abono(sesion: dict, atleta: str, inv: dict) -> dict:
    """Para el propio abonado: estado de su abono y si puede gestionarlo (portal de Stripe)."""
    if es_demo(sesion) or sesion.get("u") != atleta or atleta not in inv:
        return {}
    if not inv[atleta].get("stripe_sub") and inv[atleta].get("email") and inv[atleta].get("abonado") and env("STRIPE_SECRET_KEY") \
            and time.time() - float(inv[atleta].get("stripe_buscado") or 0) > 6 * 3600:
        try:
            _vincular_por_email(atleta, inv[atleta]["email"])
            inv = invitados()
        except Exception:  # noqa: BLE001
            pass
    if not inv[atleta].get("stripe_sub"):
        return {}
    try:
        estado = _estado_abono(atleta, inv)
    except Exception:  # noqa: BLE001
        estado = inv[atleta].get("stripe_estado")
    return {"abono_estado": estado, "abono_estado_txt": ESTADOS_ABONO.get(estado, estado),
            "abono_problema": estado in ABONO_PROBLEMA, "abono_gestion": bool(inv[atleta].get("stripe_customer")),
            "abono_fin_prueba": dt.datetime.fromtimestamp(inv[atleta]["stripe_fin_prueba"]).date().isoformat()
            if estado == "trialing" and inv[atleta].get("stripe_fin_prueba") else None,
            "abono_cancela": bool(inv[atleta].get("stripe_cancela"))}


def _rutina_cuestionario(nombre: str, r: dict) -> tuple[dict, str, str, list[str]]:
    import uuid
    ref, porque = cuestionario.elegir_referencia(r)
    base = rutina(ref)
    if not base or not base.get("dias"):
        ref, porque = next(iter(PLANTILLAS)), porque + " (la de referencia no estaba, uso otra)"
        base = rutina(ref)
    nueva, notas = cuestionario.construir(base, ref, r, lambda: uuid.uuid4().hex[:8])
    datos().guardar(nombre, nueva)
    return nueva, ref, porque, notas


def objetivos(sesion: dict, c: dict) -> dict:
    """Cuestionario del abonado: con sus respuestas se le hace la rutina de inicio (si aún no ha entrenado nada)
    y a Diego le llega todo por Telegram."""
    quien = sesion.get("u")
    reg = dict(invitados())
    if es_demo(sesion) or not quien or quien not in reg:
        raise Error("Esto es para los perfiles de abonado", 403)
    r = cuestionario.limpiar(c)
    if not (reg[quien].get("consentimiento") or {}).get("salud"):
        r["lesiones"] = ""  # sin consentimiento expreso no se guardan datos de salud
    reg[quien] = {**reg[quien], "cuestionario": r, "cuestionario_fecha": dt.date.today().isoformat(), "lang": r["lang"]}
    datos().guardar(CLAVE_INVITADOS, reg)
    try:
        ya_entreno = bool(datos().entrenos(quien, 1))
    except Exception:  # noqa: BLE001
        ya_entreno = False
    if ya_entreno and not c.get("rehacer"):
        notificar(cuestionario.resumen(quien, r, *cuestionario.elegir_referencia(r),
                                       ["ya ha entrenado: NO le he cambiado la rutina, ajústasela tú"]))
        return {"ok": True, "rehecha": False}
    _, ref, porque, notas = _rutina_cuestionario(quien, r)
    notificar(cuestionario.resumen(quien, r, ref, porque, notas))
    return {"ok": True, "rehecha": True}


def demo_personas() -> list[str]:
    lista = [x.strip() for x in (env("DEMO_ATLETAS") or env("DEMO_ATLETA") or "Yo,Archchana,Manu Anel,Salatti").split(",")]
    lista = [x for x in lista if x in ATLETAS]
    return lista or ["Yo"]


def nombre_demo(p: str) -> str:
    """En la demo cada rutina sale como un programa («Prog Principiante»…), sin el nombre del alumno."""
    if p in NOMBRES_DEMO:
        return NOMBRES_DEMO[p][0]
    otros = [x for x in demo_personas() if x != "Yo"]
    return f"Cliente {otros.index(p) + 1}" if p in otros else "Cliente"


VERSION_LEGAL = "2026-10-21"  # versión de la política de privacidad y las CGV aceptadas


def consentimiento(sesion: dict, c: dict) -> dict:
    """El alumno acepta (o cambia) la política, o da/retira el consentimiento de datos de salud."""
    quien = sesion.get("u")
    reg = dict(invitados())
    if es_demo(sesion) or not quien or quien not in reg:
        raise Error("Solo para perfiles", 403)
    x = dict(reg[quien])
    cons = dict(x.get("consentimiento") or {})
    if c.get("acepta"):
        cons.update(fecha=_ahora().isoformat(timespec="minutes"), version=VERSION_LEGAL)
    if "salud" in c:
        cons["salud"] = bool(c["salud"])
        if not c["salud"]:  # retirada: se borran lesiones/molestias del cuestionario
            if x.get("cuestionario"):
                x["cuestionario"] = {**x["cuestionario"], "lesiones": ""}
    x["consentimiento"] = cons
    reg[quien] = x
    datos().guardar(CLAVE_INVITADOS, reg)
    return {"ok": True, "consentimiento": cons}


def mis_datos(sesion: dict) -> dict:
    """Portabilidad (RGPD): todo lo que la app guarda de esta persona, en un JSON."""
    quien = sesion.get("u")
    reg = invitados()
    if es_demo(sesion) or not quien or quien not in reg:
        raise Error("Solo para perfiles", 403)
    perfil = {k: v for k, v in reg[quien].items() if k not in ("pin",)}
    chat_ = [{k: m.get(k) for k in ("de", "texto", "cuando")} for m in
             ((datos().rutinas([CLAVE_CHAT]).get(CLAVE_CHAT) or {}).get(quien) or [])]
    try:
        ents = datos().entrenos(quien, 2000)
    except Exception:  # noqa: BLE001
        ents = []
    return {"app": "Djimenez Prog", "exportado": _ahora().isoformat(timespec="minutes"), "nombre": quien,
            "perfil": perfil, "rutina": rutina(quien), "entrenos": ents, "chat": chat_}


def borrar_cuenta(sesion: dict, c: dict) -> dict:
    """Derecho de supresión (RGPD): borra perfil, rutina, entrenos, chat y actividad. El abono de Stripe se cancela aparte."""
    quien = sesion.get("u")
    reg = dict(invitados())
    if es_demo(sesion) or not quien or quien not in reg:
        raise Error("Solo para perfiles", 403)
    if norm_busqueda(str(c.get("confirmar") or "")) != norm_busqueda(quien):
        raise Error("Escribe tu nombre tal cual para confirmar · Écris ton nom pour confirmer")
    x = reg[quien]
    if x.get("stripe_estado") in ("trialing", "active", "past_due"):
        raise Error("Primero cancela tu abono en «Gestionar mi abono» y luego borra la cuenta · "
                    "Annule d'abord ton abonnement dans « Gérer mon abonnement »", 409)
    try:
        for w in datos().entrenos(quien, 5000):
            datos().borrar_entreno(w)
    except Exception:  # noqa: BLE001
        pass
    try:
        datos().borrar_fila(quien)
    except Exception:  # noqa: BLE001
        datos().guardar(quien, {})
    todo = dict(datos().rutinas([CLAVE_CHAT]).get(CLAVE_CHAT) or {})
    if quien in todo:
        todo.pop(quien, None)
        todo["_tg"] = {k: v for k, v in (todo.get("_tg") or {}).items() if v != quien}
        datos().guardar(CLAVE_CHAT, todo)

    def cambio(act):
        (act.get("personas") or {}).pop(quien, None)
        act["altas"] = [a for a in act.get("altas", []) if a.get("nombre") != quien]
        for p in act.get("pagos", []):
            if p.get("perfil") == quien:
                p.update(telefono="", email="", nombre="(cuenta borrada)", perfil=None)
    _apuntar_actividad(cambio)
    reg.pop(quien, None)
    datos().guardar(CLAVE_INVITADOS, reg)
    notificar(f"🗑️ {quien} ha borrado su cuenta y sus datos (RGPD).")
    return {"ok": True}


DIAS_PRUEBA = 7  # perfiles creados desde la demo: 7 días gratis y luego tienen que abonarse
ESTADOS_PAGANDO = ("trialing", "active", "past_due")


def _altas_demo() -> set[str]:
    try:
        act = datos().rutinas([CLAVE_ACTIVIDAD]).get(CLAVE_ACTIVIDAD) or {}
        return {a.get("nombre") for a in act.get("altas", [])}
    except Exception:  # noqa: BLE001
        return set()


def estado_prueba(nombre: str, inv: dict | None = None, altas: set | None = None) -> dict | None:
    """Para perfiles que se crearon solos desde la demo: si están en su semana gratis, si ya pagan o si toca pagar.
    None = no aplica (alumnos de Diego, entran con su código)."""
    inv = invitados() if inv is None else inv
    x = inv.get(nombre)
    if not x:
        return None
    desde_demo = x.get("origen") == "demo" or nombre in (altas if altas is not None else _altas_demo())
    if not desde_demo or x.get("exento"):
        return None
    est = x.get("stripe_estado")
    pagando = est in ESTADOS_PAGANDO or (bool(x.get("abonado")) and est is None)
    try:
        if x.get("revision") == "pendiente":  # aún no la ha visto: la semana gratis no ha empezado
            return {"pagando": False, "fin": None, "dias": DIAS_PRUEBA, "bloqueado": False, "en_prueba": False,
                    "cancelado": False, "en_revision": True}
        fin = dt.date.fromisoformat((x.get("aprobado") or x.get("alta", ""))[:10]) + dt.timedelta(days=DIAS_PRUEBA)
    except ValueError:
        fin = dt.date.today()
    quedan = (fin - dt.date.today()).days
    return {"pagando": pagando, "fin": fin.isoformat(), "dias": max(0, quedan),
            "bloqueado": not pagando and quedan <= 0, "en_prueba": not pagando and quedan > 0,
            "cancelado": est in ABONO_PROBLEMA}


def exigir_pago(sesion: dict, atleta: str) -> None:
    """Se acabó la semana gratis y no se ha abonado: no puede usar la app (sí puede pagar o escribir a Diego)."""
    if es_coach(sesion) or es_demo(sesion) or sesion.get("u") != atleta:
        return
    if (invitados().get(atleta) or {}).get("revision") == "pendiente":
        raise Error("Diego está revisando tu programa. En cuanto lo apruebe, podrás empezar 💪", 403)
    p = estado_prueba(atleta)
    if p and p["bloqueado"]:
        raise Error("Tu semana gratis ha terminado. Abónate para seguir con tu rutina 💪", 402)


def puede_ver(sesion: dict, atleta: str) -> None:
    if es_demo(sesion):
        if atleta not in demo_personas():
            raise Error("No tienes acceso a esa persona", 403)
        return
    if sesion.get("u") and sesion["u"] != atleta:
        raise Error("No tienes acceso a esa persona", 403)


# ===== compartir: enlaces que entran directos a la demo =====
def _login_invitacion(token: str) -> dict:
    """Un enlace compartido entra directo a la demo (solo mirar). Se apaga quitando CONTRASENA_DEMO."""
    if not env("CONTRASENA_DEMO"):
        raise Error("Este enlace ya no funciona. Pídele a Diego uno nuevo.", 401)
    try:
        cuerpo, firma = token.split(".", 1)
        ok = hmac.compare_digest(firma, hmac.new(_secreto(), cuerpo.encode(), hashlib.sha256).hexdigest()[:32])
        d = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
    except Exception:
        raise Error("Enlace no válido", 401)
    if not ok or "i" not in d or d.get("exp", 0) < time.time():
        raise Error("Este enlace ha caducado. Pídele a Diego uno nuevo.", 401)
    def cambio(act):
        x = _sumar(act.setdefault("llegadas", {}), str(d["i"]))
        if d.get("v") == "qr":
            x["qr"] = x.get("qr", 0) + 1
    _apuntar_actividad(cambio)
    _apuntar(None, {"d": 1}, "Demo", entrada=True)
    return _sesion_para(demo_personas()[0], demo=True)


def _sumar(donde: dict, quien: str, campo: str = "n") -> dict:
    x = donde.setdefault(quien, {})
    x[campo] = x.get(campo, 0) + 1
    x["ultimo"] = _ahora().isoformat(timespec="minutes")
    return x


def _apuntar_actividad(cambio) -> None:
    try:
        act = copy.deepcopy(datos().rutinas([CLAVE_ACTIVIDAD]).get(CLAVE_ACTIVIDAD) or {})
        cambio(act)
        datos().guardar(CLAVE_ACTIVIDAD, act)
    except Exception:  # noqa: BLE001
        pass


def compartir(sesion: dict, c: dict) -> dict:
    """Apunta que alguien comparte la app o un entreno y devuelve el enlace (entra directo a la demo)."""
    if es_demo(sesion):
        quien = "Demo"
    else:
        quien = sesion.get("u") or (c.get("atleta") if c.get("atleta") in todas_las_personas() else "Yo")
    tipo = "entreno" if c.get("tipo") == "entreno" else "app"
    que = " ".join(str(c.get("que") or "").split())[:80]

    def cambio(act):
        x = _sumar(act.setdefault("compartidos", {}), quien, tipo)
        lista = x.setdefault("lista", [])
        lista.insert(0, {"cuando": x["ultimo"], "tipo": tipo, "que": que})
        del lista[20:]
    if c.get("contar", True):
        _apuntar_actividad(cambio)
    enlace = None
    if env("CONTRASENA_DEMO"):
        cuerpo = base64.urlsafe_b64encode(json.dumps({"i": quien, "exp": int(time.time()) + 60 * 86400, **({"v": "qr"} if c.get("via") == "qr" else {})}).encode()).decode().rstrip("=")
        enlace = f"{cuerpo}.{hmac.new(_secreto(), cuerpo.encode(), hashlib.sha256).hexdigest()[:32]}"
    return {"inv": enlace}


def _login_perfil(cuerpo: dict) -> dict:
    """Entrar con nombre + PIN a un perfil que ya existe (los creados desde la demo no saben la contraseña de invitados)."""
    nombre = " ".join(str(cuerpo.get("nombre") or "").split()).title()
    pin = str(cuerpo.get("pin") or "").strip()
    registro = invitados()
    existente = next((n for n in registro if norm_busqueda(n) == norm_busqueda(nombre)), None)
    if not nombre or not pin or not existente or not hmac.compare_digest(registro[existente].get("pin", ""), _hash(existente, pin)):
        time.sleep(0.8)
        raise Error("Nombre o PIN incorrectos", 401)
    return _sesion_para(existente)


DEMO_ACCESSORY = [("GHD lateral crunch", "4x10 por lado")]  # C del día 2 de la demo: un solo ejercicio, 4 series
# nombre e icono de cada rutina en la demo (el francés lo pone la app)
CUESTIONARIO_DESDE = "2026-10-15"  # perfiles nuevos desde esta fecha: les sale el cuestionario de objetivos (pagando o no)
NOMBRES_DEMO = {"Yo": ("Prog Competidor · Diego", "🏆"), "Archchana": ("Prog Casa y Movilidad", "🏠"),
                "Manu Anel": ("Prog Principiante", "🌱"), "Salatti": ("Prog Fuerza + WOD", "💪")}
DEMO_PESOS_YO = [(r"pull", 150), (r"clean", 110), (r"^power snatch$", 80), (r"^snatch$", 85)]  # demo · Prog Competidor: pesos de muestra
DEMO_NIVEL = {"Manu Anel": "Scaled", "Archchana": "Scaled", "Salatti": "Inter"}
DEMO_CASA = ("Archchana",)
DEMO_PRINCIPIANTE = ("Manu Anel",)
DEMO_WOD_PRINCIPIANTE = ("21-15-9", "For time 21-15-9: thrusters 30/20 kg + burpees over the bar")  # B fijo del Prog Débutant  # en la demo, el Prog Débutant lleva siempre WOD de principiante  # en la demo, este programa usa WOD de casa (mancuernas, gomas, elíptica)
DEMO_DIAS_CERRADOS_YO = {1, 3, 4, 5, 6}  # Prog Competidor: en la demo solo se abre el día 2
DEMO_DIAS_CERRADOS_POR = {"Yo": DEMO_DIAS_CERRADOS_YO, "Manu Anel": {2, 3, 4, 5, 6},  # Débutant: solo el día 1
                          "Salatti": {2, 3, 4, 5, 6}, "Archchana": {2, 3, 4, 5, 6}}
DEMO_PESOS = {"Yo": DEMO_PESOS_YO, "Manu Anel": [(r"^bench press", 30)]}
DEMO_C_YO = "4x: 10 T2B direct into 1' L-sit on bar · 1' rest"
DEMO_CICLO_EN = "Salatti"  # en la demo, este cliente enseña el ciclo de handstand push ups
DEMO_DIAS_CERRADOS = {3, 4, 5, 6}  # en la demo, solo se pueden abrir los días 1 y 2
PLANTILLAS_DEMO = {"Salatti": "Rutina 1 · fuerza + WOD", "Dario": "Rutina 2 · fuerza + WOD"}


def fijar_perfil(sesion: dict, c: dict) -> dict:
    """Con la contraseña general: «soy Salatti» → la sesión queda solo para Salatti (no puede saltar a otros)."""
    if es_demo(sesion) or sesion.get("u"):
        raise Error("Esta sesión ya tiene perfil", 403)
    atleta = c.get("atleta")
    if atleta not in todas_las_personas():
        raise Error("Persona desconocida")
    if atleta == "Yo" and env("CONTRASENA_DIEGO") and not sesion.get("y"):
        raise Error("Diego entra con su propia contraseña", 403)
    return _sesion_para(atleta)


def crear_perfil(sesion: dict, c: dict) -> dict:
    """Desde la demo: crear tu propio perfil (nombre + PIN + rutina de partida) sin la contraseña de invitados."""
    if not es_demo(sesion):
        raise Error("Esto solo se usa desde la demo", 403)
    if not env("CONTRASENA_DEMO"):
        raise Error("Ahora mismo no se pueden crear perfiles. Pídeselo a Diego.", 403)
    r = _login_invitado(c)
    if "plantillas" in r:
        r["plantillas"] = {k: PLANTILLAS_DEMO.get(k, f"Rutina {i + 1}") for i, k in enumerate(r["plantillas"])}
    if r.get("token"):
        nombre = " ".join(str(c.get("nombre") or "").split()).title()
        reg = dict(invitados())
        if r.get("solo") in reg and not reg[r["solo"]].get("origen"):
            reg[r["solo"]] = {**reg[r["solo"]], "origen": "demo"}
            datos().guardar(CLAVE_INVITADOS, reg)

        def cambio(act):
            altas = act.setdefault("altas", [])
            if not any(a.get("nombre") == nombre for a in altas):
                altas.insert(0, {"nombre": nombre, "cuando": _ahora().isoformat(timespec="minutes")})
                del altas[50:]
        _apuntar_actividad(cambio)
        notificar(f"✨ Perfil nuevo desde la demo: {nombre}\n🕐 Está esperando a que revises y apruebes su programa (modo coach → su rutina → ✅ Aprobar).\n🎁 Al aprobarlo empiezan sus {DIAS_PRUEBA} días gratis; después la app le pedirá abonarse.")
    return r


ABONO_DEFECTO = {"url": "https://buy.stripe.com/8x2dRadT91922iqgZz7ok03", "texto": "7 días gratis · luego 29 €/mes"}  # se cambia con ABONO_URL / ABONO_TEXTO
def _abono_url() -> str:
    return env("ABONO_URL") or ABONO_DEFECTO["url"]


CONTACTO_DEFECTO = {"whatsapp": "+33675987599", "email": "djimenezpenapro@gmail.com"}  # se cambia con las variables CONTACTO_*


def _contacto() -> dict | None:
    tel = "".join(ch for ch in (env("CONTACTO_WHATSAPP") or CONTACTO_DEFECTO["whatsapp"]) if ch.isdigit())
    if tel and len(tel) == 9:
        tel = "34" + tel  # número español sin prefijo
    out = {k: v for k, v in {"whatsapp": tel, "email": env("CONTACTO_EMAIL") or CONTACTO_DEFECTO["email"],
                             "instagram": env("CONTACTO_INSTAGRAM").lstrip("@")}.items() if v}
    return out or None


def contactar(sesion: dict, c: dict) -> dict:
    """Apunta que alguien quiere contactar (mientras no hay pago) para verlo en «Quién usa la app»."""
    quien = "Demo" if es_demo(sesion) else (sesion.get("u") or (c.get("atleta") if c.get("atleta") in todas_las_personas() else "Yo"))
    via = c.get("via") if c.get("via") in ("whatsapp", "email", "instagram") else "whatsapp"

    def cambio(act):
        x = _sumar(act.setdefault("contactos", {}), quien)
        x[via] = x.get(via, 0) + 1
        x.setdefault("nombre", nv(quien) if quien != "Demo" else "Demo (solo mirar)")
    _apuntar_actividad(cambio)
    return {"ok": True}


def abonarse(sesion: dict, c: dict) -> dict:
    """Apunta que alguien pulsa «Abonarse» y devuelve el enlace de pago (Stripe), con su nombre para reconocerle."""
    url = _abono_url()
    if not url:
        raise Error("El pago todavía no está activado. Escríbele a Diego.", 404)
    quien = "Demo" if es_demo(sesion) else (sesion.get("u") or (c.get("atleta") if c.get("atleta") in todas_las_personas() else "Yo"))

    def cambio(act):
        x = _sumar(act.setdefault("abonos", {}), quien)
        x.setdefault("nombre", nv(quien) if quien != "Demo" else "Demo (solo mirar)")
    _apuntar_actividad(cambio)
    ref = re.sub(r"[^A-Za-z0-9_-]", "_", quien)[:60]
    sep = "&" if "?" in url else "?"
    return {"url": f"{url}{sep}client_reference_id={ref}" if "stripe.com" in url else url}


# ===== Stripe (clave limitada en STRIPE_SECRET_KEY; solo lectura + portal de clientes) =====
ESTADOS_ABONO = {"trialing": "prueba", "active": "activo", "past_due": "pago pendiente", "unpaid": "impagado",
                 "canceled": "cancelado", "incomplete": "incompleto", "incomplete_expired": "caducado", "paused": "pausado"}
ABONO_PROBLEMA = ("past_due", "unpaid", "canceled", "incomplete_expired", "paused")


def _stripe(metodo: str, ruta: str, params: dict | None = None, timeout: float = 4) -> dict | None:
    """Llama a la API de Stripe. Devuelve None si no hay clave o falla (la app sigue funcionando sin Stripe)."""
    clave = env("STRIPE_SECRET_KEY")
    if not clave:
        return None
    datos_url = urllib.parse.urlencode(params or {}, doseq=True)
    url = f"https://api.stripe.com/v1/{ruta}" + (f"?{datos_url}" if metodo == "GET" and datos_url else "")
    req = urllib.request.Request(url, data=datos_url.encode() if metodo != "GET" else None, method=metodo,
                                 headers={"Authorization": f"Bearer {clave}", "Stripe-Version": "2024-06-20"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return {"error": json.loads(e.read() or b"{}").get("error", {})}
        except ValueError:
            return {"error": {"message": str(e)}}
    except Exception as e:  # noqa: BLE001
        return {"error": {"message": str(e)}}


def _comprobar_pago_stripe(cs: str) -> dict | None:
    """¿Esta sesión de Checkout está pagada (o en prueba)? → {ok, estado, customer, sub, email, fin_prueba}."""
    if not cs or not cs.startswith("cs_"):
        return None
    x = _stripe("GET", f"checkout/sessions/{cs}", {"expand[]": "subscription"})
    if not x or x.get("error"):
        return None
    sub = x.get("subscription") if isinstance(x.get("subscription"), dict) else {}
    pagado = x.get("status") == "complete" and x.get("payment_status") in ("paid", "no_payment_required")
    return {"ok": pagado, "estado": sub.get("status") or ("active" if pagado else x.get("status")),
            "customer": x.get("customer"), "sub": sub.get("id") or x.get("subscription"),
            "email": (x.get("customer_details") or {}).get("email"), "fin_prueba": sub.get("trial_end")}


def _estado_abono(nombre: str, reg: dict | None = None, forzar: bool = False) -> str | None:
    """Estado del abono en Stripe (cacheado 6 h). Avisa a Diego si pasa a cancelado / impagado."""
    reg = dict(invitados()) if reg is None else reg
    x = reg.get(nombre) or {}
    if not x.get("stripe_sub") or not env("STRIPE_SECRET_KEY"):
        return x.get("stripe_estado")
    if not forzar and time.time() - float(x.get("stripe_mirado") or 0) < 6 * 3600:
        return x.get("stripe_estado")
    sub = _stripe("GET", f"subscriptions/{x['stripe_sub']}")
    if not sub or sub.get("error"):
        return x.get("stripe_estado")
    nuevo, antes = sub.get("status"), x.get("stripe_estado")
    reg = dict(invitados())
    reg[nombre] = {**reg.get(nombre, x), "stripe_estado": nuevo, "stripe_mirado": time.time(),
                   "stripe_fin_prueba": sub.get("trial_end"), "stripe_cancela": bool(sub.get("cancel_at_period_end"))}
    datos().guardar(CLAVE_INVITADOS, reg)
    if nuevo != antes and antes:
        icono = "⚠️" if nuevo in ABONO_PROBLEMA else "✅"
        notificar(f"{icono} Abono de {nombre}: {ESTADOS_ABONO.get(antes, antes)} → {ESTADOS_ABONO.get(nuevo, nuevo)}")
    return nuevo


def _vincular_por_email(nombre: str, email: str) -> None:
    """Abonados de antes de conectar Stripe: se busca su cliente y su abono por el email que dejaron."""
    reg = dict(invitados())
    x = dict(reg.get(nombre) or {})
    x["stripe_buscado"] = time.time()
    cli = _stripe("GET", "customers", {"email": email, "limit": 3}) or {}
    for c in cli.get("data") or []:
        subs = _stripe("GET", "subscriptions", {"customer": c["id"], "status": "all", "limit": 3}) or {}
        sub = next(iter(subs.get("data") or []), None)
        x["stripe_customer"] = c["id"]
        if sub:
            x.update(stripe_sub=sub["id"], stripe_estado=sub["status"], stripe_mirado=time.time(),
                     stripe_fin_prueba=sub.get("trial_end"), stripe_cancela=bool(sub.get("cancel_at_period_end")))
            break
    reg[nombre] = x
    datos().guardar(CLAVE_INVITADOS, reg)


def portal_abono(sesion: dict) -> dict:
    """Enlace al portal de clientes de Stripe: cambiar tarjeta, ver facturas o darse de baja."""
    quien = sesion.get("u")
    x = (invitados().get(quien) or {}) if quien and not es_demo(sesion) else {}
    if not x.get("stripe_customer"):
        raise Error("No encuentro tu abono. Escríbele a Diego.", 404)
    r = _stripe("POST", "billing_portal/sessions", {"customer": x["stripe_customer"],
                                                   "return_url": "https://entrenamientos-web-two.vercel.app/"})
    if not r or r.get("error") or not r.get("url"):
        raise Error("Ahora mismo no se puede abrir la gestión del abono. Prueba en un rato.", 502)
    try:
        _estado_abono(quien, forzar=True)
    except Exception:  # noqa: BLE001
        pass
    return {"url": r["url"]}


def datos_pago(sesion: dict | None, c: dict) -> dict:
    """Después de pagar en Stripe: la persona deja su teléfono y email para que Diego compruebe el pago y le dé de alta."""
    import uuid
    nombre = " ".join(str(c.get("nombre") or "").split())[:60]
    tel = "".join(ch for ch in str(c.get("telefono") or "") if ch.isdigit() or ch in "+ ").strip()[:20]
    digitos = "".join(ch for ch in tel if ch.isdigit())
    if tel.startswith("+33") and digitos.startswith("330") and len(digitos) == 12:
        tel = "+33 " + digitos[3:]  # «+33 06…» → «+33 6…»
    email = str(c.get("email") or "").strip()[:120]
    cs = re.sub(r"[^A-Za-z0-9_]", "", str(c.get("cs") or ""))[:120]
    if not nombre:
        raise Error("Escribe tu nombre")
    if len("".join(ch for ch in tel if ch.isdigit())) < 9:
        raise Error("Escribe un teléfono válido")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise Error("Escribe un email válido")
    quien = None
    if sesion and not es_demo(sesion):
        quien = sesion.get("u") or None
    respuesta = {"ok": True}
    try:
        stripe = _comprobar_pago_stripe(cs)
    except Exception:  # noqa: BLE001
        stripe = None
    pin = str(c.get("pin") or "").strip()
    if not quien and pin:  # abonado nuevo: se le crea su perfil al momento con una rutina de inicio
        if len(pin) < 4:
            raise Error("El PIN tiene que tener al menos 4 cifras")
        r_alta = _login_invitado({"nombre": nombre, "pin": pin, "plantilla": c.get("plantilla") or next(iter(PLANTILLAS)),
                                  "acepta": c.get("acepta"), "salud": c.get("salud"), "lang": c.get("lang")})
        if not r_alta.get("token"):
            raise Error("No se ha podido crear tu perfil")
        quien = r_alta["solo"]
        reg_inv = dict(invitados())
        if quien in reg_inv:
            reg_inv[quien] = {**reg_inv[quien], "abonado": dt.date.today().isoformat(), "telefono": tel, "email": email,
                              **({"lang": c["lang"]} if c.get("lang") in ("es", "fr") else {}),
                              **({"stripe_customer": stripe["customer"], "stripe_sub": stripe["sub"],
                                  "stripe_estado": stripe["estado"], "stripe_mirado": time.time(),
                                  "stripe_fin_prueba": stripe.get("fin_prueba")} if stripe and stripe["ok"] else {})}
            datos().guardar(CLAVE_INVITADOS, reg_inv)
        respuesta = {"ok": True, **r_alta, "nuevo_abonado": True}

    def cambio(act):
        pagos = act.setdefault("pagos", [])
        if cs and any(x.get("cs") == cs for x in pagos):
            for x in pagos:
                if x.get("cs") == cs:
                    x.update(nombre=nombre, telefono=tel, email=email)
            return
        pagos.insert(0, {"id": uuid.uuid4().hex[:10], "cuando": _ahora().isoformat(timespec="minutes"), "nombre": nombre,
                         "telefono": tel, "email": email, "cs": cs, "perfil": quien,
                         "visto": bool(stripe and stripe["ok"]),  # confirmado por Stripe: no hace falta comprobarlo a mano
                         "stripe": (stripe or {}).get("estado") if stripe else None})
        del pagos[300:]
    _apuntar_actividad(cambio)
    if stripe and quien and not respuesta.get("nuevo_abonado") and stripe["ok"]:
        reg_inv = dict(invitados())  # alumno que ya existía y se abona: se le apunta su abono
        if quien in reg_inv:
            reg_inv[quien] = {**reg_inv[quien], "stripe_customer": stripe["customer"], "stripe_sub": stripe["sub"],
                              "stripe_estado": stripe["estado"], "stripe_mirado": time.time(),
                              "abonado": reg_inv[quien].get("abonado") or dt.date.today().isoformat()}
            datos().guardar(CLAVE_INVITADOS, reg_inv)
    verif = ("\n✅ Stripe lo confirma: " + ESTADOS_ABONO.get(stripe["estado"], str(stripe["estado"]))) if stripe and stripe["ok"] else \
        ("\n⚠️ Stripe NO confirma este pago: revísalo" if stripe else "")
    notificar(f"💳 {'Nuevo abonado (semana gratis)' if respuesta.get('nuevo_abonado') else ('Pago nuevo' if stripe and stripe['ok'] else 'Pago nuevo por comprobar')}{verif}\n"
              f"{nombre} · {tel} · {email}" + (f"\n👤 Perfil creado: {quien} · rutina de inicio, ajústasela" if respuesta.get("nuevo_abonado") else "")
              + (f"\nStripe: {cs}" if cs else ""))
    return respuesta


def me_gusta(sesion: dict, c: dict) -> dict:
    """❤️ a un WOD. Se cuenta quién (o «Demo») para que Diego vea qué entrenos gustan más."""
    clave = re.sub(r"[^a-z0-9]+", " ", norm(str(c.get("clave") or ""))).strip()[:80]
    if not clave:
        raise Error("Falta el entreno")
    quien = "Demo:" + re.sub(r"[^A-Za-z0-9]", "", str(c.get("disp") or ""))[:12] if es_demo(sesion) else \
        (sesion.get("u") or (c.get("atleta") if c.get("atleta") in todas_las_personas() else "Yo"))
    on = bool(c.get("on"))

    def cambio(act):
        x = act.setdefault("likes", {}).setdefault(clave, {"nombre": str(c.get("nombre") or "")[:80],
                                                         "texto": str(c.get("texto") or "")[:200], "por": []})
        por = [q for q in x["por"] if q != quien]
        if on:
            por.append(quien)
        x["por"] = por[-200:]
        x["ultimo"] = _ahora().isoformat(timespec="minutes")
    _apuntar_actividad(cambio)
    return {"ok": True}


def exento(sesion: dict, c: dict) -> dict:
    """El coach deja entrar gratis a alguien (p. ej. paga en mano) o se lo quita."""
    if not es_coach(sesion):
        raise Error("Solo el coach", 403)
    reg = dict(invitados())
    n = c.get("nombre")
    if n not in reg:
        raise Error("No encuentro ese perfil")
    reg[n] = {**reg[n], "exento": bool(c.get("on"))}
    datos().guardar(CLAVE_INVITADOS, reg)
    return {"ok": True, "aviso": f"{n}: entra gratis ✅" if c.get("on") else f"{n}: tendrá que abonarse"}


def pago_visto(sesion: dict, c: dict) -> dict:
    if not es_coach(sesion):
        raise Error("Solo el coach", 403)
    pid = str(c.get("id") or "")

    def cambio(act):
        for x in act.get("pagos", []):
            if x.get("id") == pid:
                x["visto"] = not c.get("deshacer")
    _apuntar_actividad(cambio)
    return {"ok": True}


def _resumen_dia_registro(rut: dict, semana: int, dia_id: str, resultados: list[dict], atleta: str = "") -> list[str]:
    """Resumen del día para Telegram: si lo ha hecho todo, qué TOCABA en cada parte (el WOD entero, la fuerza con
    sus series y pesos), qué hizo y qué cambió respecto a lo programado."""
    dia = next((d for d in rut["dias"] if d["id"] == dia_id), None)
    if not dia:
        return []
    por_nombre = {norm(e["name"]): e for e in resultados}
    usados = set()
    grupos = [(p, ls) for p, ls in agrupar_por_parte(dia, semana)]
    cuentan = [(p, ls) for p, ls in grupos if not (es_movilidad(p, ls) and atleta not in MOVILIDAD_ES_PARTE)]
    ests = {p: estado_parte(rut, semana, dia_id, p)["estado"] for p, _ in grupos}
    hechas_n = sum(1 for p, _ in cuentan if ests[p] == "hecho")
    faltan = [p.split(")", 1)[-1].strip() for p, _ in cuentan if ests[p] != "hecho"]
    out = [f"📅 {dia['nombre']} · semana {semana}",
           "✅ HA HECHO TODO EL DÍA" if cuentan and not faltan
           else f"⏳ {hechas_n} de {len(cuentan)} partes hechas · falta: {', '.join(faltan)}"]
    cambios = []
    ICON = {"hecho": "✅", "no_hecho": "❌", "pospuesto": "➡️", "pendiente": "⬜"}
    aj = ((rut.get("ajustes") or {}).get(str(semana)) or {})
    nivel = rut.get("nivel") or NIVEL_DEFECTO.get(atleta, "Inter")
    try:
        sugs = sugerencias(rut, semana, wods_de_diego(rutina("Yo")))
    except Exception:  # noqa: BLE001
        sugs = {}
    for p, ls in grupos:
        out.append(f"\n{ICON.get(ests[p], '⬜')} {p.replace(')', ' ·', 1)}")
        for l in ls:
            txt = prescripcion_semana(l, semana, rut.get("ajustes"))[0] or l.get("prescripcion", "")
            if not txt and sugs.get(l["id"]):
                txt = sugs[l["id"]]["texto"]  # el WOD de Diego que le salía ese día
            fuerza = tipo_de_linea(p, l["ejercicio"]) is None and l.get("plan") is None
            e = por_nombre.get(norm(l["ejercicio"]))
            if e is None and len(ls) == 1:  # el WOD se suele apuntar con el nombre de la parte
                e = next((x for k, x in por_nombre.items() if k not in usados and (k in norm(p) or norm(p) in k or k in ("wod", "resultado"))), None)
            if e is not None:
                usados.add(norm(e["name"]))
            res = fmt_valor(e["value"], e.get("unit", "")) if e and e.get("value") is not None else None
            no_hecha = linea_no_hecha(l, semana)
            marca = "❌ no lo hizo" if no_hecha else (f"✅ {res}" if res else ("✅ hecho" if ests[p] == "hecho" else "— sin resultado"))
            if fuerza:
                tocaba = " ".join(txt.split()) or "sin pesos"
                out.append(f"  • {l['ejercicio']}: tocaba {tocaba} → {marca}")
            else:
                escalable = norm_busqueda(_etiqueta_parte(p)) != "gym" and _tipo_ui(p, l["ejercicio"]) in TIPOS_WOD + ("conditioning", "accessory")
                visto = escalar(txt, nivel) if txt and escalable and nivel != "RX" else txt
                if l["ejercicio"] and norm(l["ejercicio"]) not in norm(p):
                    out.append(f"  • {l['ejercicio']}")
                if visto:
                    out.append("    📋 Tocaba" + (f" ({nivel})" if escalable else "") + ":")
                    out += [f"    {x.strip()}" for x in visto.splitlines() if x.strip()][:12]
                else:
                    out.append("    📋 Tocaba: (sin escribir)")
                out.append(f"    → {marca}")
            if no_hecha:
                cambios.append(f"{l['ejercicio']}: marcado como no hecho")
            pesos = [float(x.replace(",", ".")) for x in NUM_PESO.findall(txt)]
            if e and e.get("unit") == "kg" and e.get("value") is not None and pesos and abs(float(e["value"]) - max(pesos)) >= 0.5:
                cambios.append(f"{l['ejercicio']}: hizo {fmt_valor(e['value'], 'kg')} (tocaba {fmt_num(max(pesos))} kg)")
            if l.get("sustituye"):
                cambios.append(f"{p.split(')')[0]}: cambió la parte por «{l['ejercicio']}»")
            elif l["id"] in aj:
                cambios.append(f"{l['ejercicio']}: ajustado solo esta semana")
    extra = [x for k, x in por_nombre.items() if k not in usados and x.get("value") is not None
             and not any(norm(l["ejercicio"]) == k for _, ls in grupos for l in ls)]
    for x in extra[:5]:
        out.append(f"  • {x['name']} → {fmt_valor(x['value'], x.get('unit', ''))} (extra)")
    if cambios:
        out.append("\n🔧 Cambios respecto a lo programado:")
        out += [f"  • {c}" for c in dict.fromkeys(cambios)]
    else:
        out.append("\n👌 Sin cambios respecto a lo programado")
    return out


# ===== avisos a Diego por Telegram =====
def _telegram() -> dict:
    if env("TELEGRAM_TOKEN") and env("TELEGRAM_CHAT_ID"):
        return {"token": env("TELEGRAM_TOKEN"), "chat_id": env("TELEGRAM_CHAT_ID")}
    try:
        return (datos().rutinas([CLAVE_CONFIG]).get(CLAVE_CONFIG) or {}).get("telegram") or {}
    except Exception:  # noqa: BLE001
        return {}


def _tg(token: str, metodo: str, cuerpo: dict | None = None, timeout: float = 5) -> dict:
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metodo}",
                                 data=json.dumps(cuerpo or {}).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as x:
            return json.loads(x.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read() or b"{}")
        except ValueError:
            return {"ok": False}


def notificar(texto: str) -> None:
    """Manda un aviso a Diego por Telegram (si está conectado). Nunca rompe nada."""
    try:
        cfg = _telegram()
        if cfg.get("token") and cfg.get("chat_id"):
            _tg(cfg["token"], "sendMessage", {"chat_id": cfg["chat_id"], "text": texto[:3500],
                                              "disable_web_page_preview": True}, timeout=2.5)
    except Exception:  # noqa: BLE001
        pass


def notificar_botones(texto: str, botones: list[list[dict]]) -> None:
    """Aviso a Diego con botones (inline keyboard). Nunca rompe nada."""
    try:
        cfg = _telegram()
        if cfg.get("token") and cfg.get("chat_id"):
            _asegurar_webhook(cfg)
            _tg(cfg["token"], "sendMessage", {"chat_id": cfg["chat_id"], "text": texto[:3500], "disable_web_page_preview": True,
                                              "reply_markup": {"inline_keyboard": botones}}, timeout=3)
    except Exception:  # noqa: BLE001
        pass


# ===== planificación: semanas preparadas por adelantado =====
SEMANAS_ADELANTO = 2  # Diego quiere tener hechas las 2 semanas siguientes a la actual


def _boton_lista(atleta: str, semana: int) -> dict:
    return {"text": f"✅ {nv(atleta)} S{semana} lista", "callback_data": f"lista|{semana}|{atleta}"[:64]}


def por_preparar(guardadas: dict | None = None, inv: dict | None = None) -> list[dict]:
    """Semanas (actual+1 … actual+2) que Diego aún no ha marcado como listas, de la gente que entrena ahora."""
    inv = invitados() if inv is None else inv
    gente = [p for p in todas_las_personas(inv) if p != "Yo" and (inv.get(p) or {}).get("revision") != "pendiente"]
    ruts = datos().rutinas(gente + [CLAVE_ACTIVIDAD])
    act = (ruts.get(CLAVE_ACTIVIDAD) or {}).get("personas") or {}
    corte = (_ahora() - dt.timedelta(days=21)).isoformat()
    out = []
    for n in gente:
        r = ruts.get(n)
        if not r or not r.get("dias") or (act.get(n) or {}).get("ultimo", "") < corte:
            continue  # sin rutina o sin entrar en 3 semanas: no cuenta
        actual = int(r.get("semana_actual") or 1)
        listas = {int(x) for x in r.get("semanas_listas") or []}
        for w in range(actual + 1, actual + 1 + SEMANAS_ADELANTO):
            if w not in listas:
                out.append({"atleta": n, "nombre": nv(n), "semana": w, "urgente": w == actual + 1})
    return out


def marcar_semana_lista(atleta: str, semana: int, lista: bool = True) -> dict:
    rut = datos().rutinas([atleta]).get(atleta)
    if not rut:
        raise Error("Esa persona no tiene rutina")
    listas = {int(x) for x in rut.get("semanas_listas") or []}
    listas = (listas | {int(semana)}) if lista else (listas - {int(semana)})
    actual = int(rut.get("semana_actual") or 1)
    rut = dict(rut, semanas_listas=sorted(x for x in listas if x >= actual - 4))
    datos().guardar(atleta, rut)
    return rut


def _avisar_semana_sin_preparar(atleta: str, antes: int, despues: int, rut: dict) -> None:
    """Un alumno pasa de semana y la nueva (o la siguiente) no está marcada como lista → aviso con botón."""
    if atleta == "Yo" or despues <= antes:
        return
    listas = {int(x) for x in rut.get("semanas_listas") or []}
    faltan = [w for w in range(despues, despues + SEMANAS_ADELANTO) if w not in listas]
    if not faltan:
        return
    txt = (f"⚠️ {nv(atleta)} pasa a la semana {despues} y no la has marcado como lista" if despues in faltan else
           f"📝 {nv(atleta)} empieza la semana {despues}. Te queda por preparar la {faltan[0]}")
    notificar_botones(txt + "\nSi no la tocas, le sale la progresión automática.",
                      [[_boton_lista(atleta, w)] for w in faltan] + [[{"text": "📲 Abrir la app", "url": URL_APP}]])


def resumen_planificacion(forzar: bool = False) -> dict:
    """Resumen de lo que queda por preparar (lo lanza el cron del domingo). Como mucho uno al día."""
    reg = dict(datos().rutinas([CLAVE_CONFIG]).get(CLAVE_CONFIG) or {})
    hoy = _ahora().date().isoformat()
    if reg.get("resumen_plan") == hoy and not forzar:
        return {"ok": True, "ya": True}
    lista = por_preparar()
    if lista:
        lineas = [f"{'⚠️' if x['urgente'] else '•'} {x['nombre']}: semana {x['semana']}" for x in lista]
        notificar_botones("📝 Te queda por preparar:\n" + "\n".join(lineas) +
                          "\n\nToca cuando tengas una lista ✅ (si no, sale la progresión automática).",
                          [[_boton_lista(x["atleta"], x["semana"])] for x in lista[:20]] + [[{"text": "📲 Abrir la app", "url": URL_APP}]])
    else:
        notificar("✅ Planificación al día: tienes listas las 2 semanas siguientes de todos. 🔥")
    reg["resumen_plan"] = hoy
    datos().guardar(CLAVE_CONFIG, reg)
    return {"ok": True, "pendientes": len(lista)}


def telegram(sesion: dict, c: dict) -> dict:
    """Conecta (con el token de @BotFather), prueba o quita los avisos por Telegram. Solo el coach."""
    if not es_coach(sesion):
        raise Error("Solo el coach", 403)
    reg = dict(datos().rutinas([CLAVE_CONFIG]).get(CLAVE_CONFIG) or {})
    if c.get("quitar"):
        reg.pop("telegram", None)
        datos().guardar(CLAVE_CONFIG, reg)
        return {"ok": True, "aviso": "Avisos de Telegram quitados"}
    if c.get("probar"):
        cfg = _telegram()
        if not cfg.get("chat_id"):
            raise Error("Telegram no está conectado")
        r = _tg(cfg["token"], "sendMessage", {"chat_id": cfg["chat_id"], "text": "🔥 Djimenez Prog: los avisos funcionan. Aquí te llegarán las solicitudes, los pagos, los perfiles nuevos y los mensajes del chat (respóndelos aquí mismo)."})
        try:
            _asegurar_webhook(cfg)
        except Exception:  # noqa: BLE001
            pass
        if not r.get("ok"):
            raise Error("Telegram no ha aceptado el mensaje: " + str(r.get("description", ""))[:120])
        return {"ok": True, "aviso": "Mensaje de prueba enviado 📲"}
    token = "".join(str(c.get("token") or "").split())
    if not re.fullmatch(r"\d{5,}:[A-Za-z0-9_-]{20,}", token):
        raise Error("Eso no parece un token de bot. Cópialo entero de @BotFather (números:letras)")
    yo = _tg(token, "getMe")
    if not yo.get("ok"):
        raise Error("Telegram no reconoce ese token")
    _tg(token, "deleteWebhook")  # si ya tenía webhook, getUpdates no funciona
    ups = _tg(token, "getUpdates", {"limit": 50, "timeout": 0}).get("result") or []
    chat = next((u["message"]["chat"]["id"] for u in reversed(ups) if (u.get("message") or {}).get("chat", {}).get("type") == "private"), None)
    if not chat:
        raise Error(f"Casi: abre tu bot @{yo['result'].get('username')} en Telegram, pulsa INICIAR (o escribe /start) y vuelve a pulsar Conectar")
    reg["telegram"] = {"token": token, "chat_id": chat, "bot": yo["result"].get("username")}
    datos().guardar(CLAVE_CONFIG, reg)
    _tg(token, "sendMessage", {"chat_id": chat, "text": "✅ Conectado con Djimenez Prog. Te avisaré aquí de solicitudes, pagos y perfiles nuevos."})
    try:
        _asegurar_webhook({"token": token, "chat_id": chat})
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "aviso": f"Telegram conectado (@{yo['result'].get('username')}) ✅"}


# ===== chat con Diego (llega por Telegram; si Diego responde al mensaje, le sale al alumno en la app) =====
CLAVE_CHAT = "__chat__"
URL_APP = "https://entrenamientos-web-two.vercel.app"


def _secreto_tg() -> str:
    return hmac.new(_secreto(), b"telegram-webhook", hashlib.sha256).hexdigest()[:48]


def _asegurar_webhook(cfg: dict | None = None) -> bool:
    """Que Telegram mande a la app lo que Diego escribe al bot (para las respuestas del chat)."""
    cfg = cfg or _telegram()
    if not cfg.get("token"):
        return False
    reg = dict(datos().rutinas([CLAVE_CONFIG]).get(CLAVE_CONFIG) or {})
    tg = dict(reg.get("telegram") or {})
    url = (env("APP_URL") or URL_APP).rstrip("/") + "/api/tg_webhook"
    if tg.get("webhook") == url + "|cb":
        return True
    r = _tg(cfg["token"], "setWebhook", {"url": url, "secret_token": _secreto_tg(),
                                         "allowed_updates": ["message", "callback_query"]}, timeout=4)
    if r.get("ok") and tg:
        tg["webhook"] = url + "|cb"
        reg["telegram"] = tg
        datos().guardar(CLAVE_CONFIG, reg)
    return bool(r.get("ok"))


def _clave_chat(sesion: dict, c: dict) -> tuple[str, str]:
    """(clave de la conversación, nombre para Diego). En la demo, cada móvil tiene su propia conversación."""
    if es_demo(sesion):
        disp = re.sub(r"[^A-Za-z0-9]", "", str(c.get("disp") or ""))[:16]
        if len(disp) < 6:
            raise Error("Falta el identificador del móvil")
        return f"Demo·{disp}", f"Visitante de la demo ({disp[:4]})"
    atleta = c.get("atleta") or sesion.get("u") or "Yo"
    puede_ver(sesion, atleta)
    return atleta, nv(atleta)


def chat(sesion: dict, c: dict, metodo: str = "GET") -> dict:
    clave, nombre = _clave_chat(sesion, c)
    coach_contesta = es_coach(sesion) and clave != "Yo" and not es_demo(sesion)
    todo = dict(datos().rutinas([CLAVE_CHAT]).get(CLAVE_CHAT) or {})
    hilo = list(todo.get(clave) or [])
    if metodo == "POST":
        import uuid
        texto = " ".join(str(c.get("texto") or "").split(" ")).strip()[:1500]
        if not texto:
            raise Error("Escribe un mensaje")
        msg = {"id": uuid.uuid4().hex[:10], "de": "diego" if coach_contesta else "alumno", "texto": texto,
               "cuando": _ahora().isoformat(timespec="minutes"), "leido": False}
        if not coach_contesta:
            cfg = _telegram()
            if cfg.get("token") and cfg.get("chat_id"):
                try:
                    _asegurar_webhook(cfg)
                except Exception:  # noqa: BLE001
                    pass
                extra = f"\nEmail: {c.get('email')}" if es_demo(sesion) and c.get("email") else ""
                r = _tg(cfg["token"], "sendMessage", {
                    "chat_id": cfg["chat_id"], "text": f"💬 {nombre}:\n{texto}{extra}\n\n↩️ Responde a este mensaje para contestarle en la app"[:3500]},
                    timeout=3)
                if r.get("ok"):
                    msg["tg"] = r["result"]["message_id"]
                    mapa = dict(todo.get("_tg") or {})
                    mapa[str(msg["tg"])] = clave
                    if len(mapa) > 2000:
                        mapa = dict(list(mapa.items())[-1500:])
                    todo["_tg"] = mapa
        hilo.append(msg)
        todo[clave] = hilo[-200:]
        datos().guardar(CLAVE_CHAT, todo)
        return {"mensajes": _vista_hilo(todo[clave], coach_contesta), "telegram": bool(msg.get("tg")) or coach_contesta}
    # leer: lo que ha contestado la otra parte queda como leído
    otro = "alumno" if coach_contesta else "diego"
    if any(m.get("de") == otro and not m.get("leido") for m in hilo):
        for m in hilo:
            if m.get("de") == otro:
                m["leido"] = True
        todo[clave] = hilo
        datos().guardar(CLAVE_CHAT, todo)
    return {"mensajes": _vista_hilo(hilo, coach_contesta)}


def _vista_hilo(hilo: list[dict], coach: bool) -> list[dict]:
    return [{"id": m["id"], "mio": (m["de"] == "diego") == coach, "de": m["de"], "texto": m["texto"], "cuando": m["cuando"]}
            for m in hilo[-100:]]


def chat_no_leidos(clave: str, guardadas: dict | None = None) -> int:
    try:
        todo = (guardadas or {}).get(CLAVE_CHAT) if guardadas and CLAVE_CHAT in guardadas else \
            datos().rutinas([CLAVE_CHAT]).get(CLAVE_CHAT)
        return sum(1 for m in (todo or {}).get(clave) or [] if m.get("de") == "diego" and not m.get("leido"))
    except Exception:  # noqa: BLE001
        return 0


def tg_webhook(secreto: str, update: dict) -> dict:
    """Telegram nos manda lo que Diego escribe al bot. Si responde a un mensaje del chat, se lo pasamos al alumno."""
    if not hmac.compare_digest(secreto or "", _secreto_tg()):
        raise Error("No autorizado", 401)
    cfg = _telegram()
    cq = update.get("callback_query")
    if cq:  # botón «✅ X Sn lista»
        msg = cq.get("message") or {}
        if str((msg.get("chat") or {}).get("id")) != str(cfg.get("chat_id")):
            return {"ok": True}
        partes = str(cq.get("data") or "").split("|", 2)
        texto_resp = "No entendí ese botón"
        if len(partes) == 3 and partes[0] == "lista" and partes[1].isdigit():
            try:
                marcar_semana_lista(partes[2], int(partes[1]))
                texto_resp = f"✅ {nv(partes[2])}: semana {partes[1]} lista"
                teclado = (msg.get("reply_markup") or {}).get("inline_keyboard") or []
                teclado = [fila for fila in teclado if not any(b.get("callback_data") == cq.get("data") for b in fila)]
                _tg(cfg["token"], "editMessageReplyMarkup", {"chat_id": cfg["chat_id"], "message_id": msg.get("message_id"),
                                                            "reply_markup": {"inline_keyboard": teclado}}, timeout=3)
            except Error as e:
                texto_resp = str(e)
        _tg(cfg["token"], "answerCallbackQuery", {"callback_query_id": cq.get("id"), "text": texto_resp}, timeout=3)
        return {"ok": True}
    m = update.get("message") or {}
    if not m or str((m.get("chat") or {}).get("id")) != str(cfg.get("chat_id")):
        return {"ok": True}
    texto = (m.get("text") or m.get("caption") or "").strip()
    resp = (m.get("reply_to_message") or {}).get("message_id")
    todo = dict(datos().rutinas([CLAVE_CHAT]).get(CLAVE_CHAT) or {})
    clave = (todo.get("_tg") or {}).get(str(resp)) if resp else None
    if not clave:
        if texto and not texto.startswith("/"):
            _tg(cfg["token"], "sendMessage", {"chat_id": cfg["chat_id"], "reply_to_message_id": m.get("message_id"),
                                              "text": "Para contestar a alguien, mantén pulsado su mensaje 💬 → Responder."}, timeout=3)
        return {"ok": True}
    if not texto:
        return {"ok": True}
    import uuid
    hilo = list(todo.get(clave) or [])
    hilo.append({"id": uuid.uuid4().hex[:10], "de": "diego", "texto": texto[:1500],
                 "cuando": _ahora().isoformat(timespec="minutes"), "leido": False})
    todo[clave] = hilo[-200:]
    datos().guardar(CLAVE_CHAT, todo)
    _tg(cfg["token"], "setMessageReaction", {"chat_id": cfg["chat_id"], "message_id": m.get("message_id"),
                                             "reaction": [{"type": "emoji", "emoji": "👍"}]}, timeout=3)
    return {"ok": True}


# ===== actividad: quién entra y cuándo =====
def _ahora() -> dt.datetime:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Madrid"))
    except Exception:  # noqa: BLE001  (sin datos de zonas horarias: hora de España en verano)
        return dt.datetime.now(dt.timezone(dt.timedelta(hours=2)))


def _apuntar(guardadas: dict | None, sesion: dict, atleta: str, entrada: bool = False) -> None:
    """Apunta que alguien ha abierto la app. Como mucho una vez cada 10 minutos por persona, y nunca rompe nada."""
    try:
        if es_coach(sesion) and atleta != "Yo":
            return  # Diego mirando la rutina de otro no cuenta como que esa persona entra
        quien = "Demo" if es_demo(sesion) else atleta
        act = (guardadas.get(CLAVE_ACTIVIDAD) if guardadas is not None
               else datos().rutinas([CLAVE_ACTIVIDAD]).get(CLAVE_ACTIVIDAD)) or {}
        act = copy.deepcopy(act)
        p = act.setdefault("personas", {}).setdefault(quien, {})
        ahora = _ahora()
        if not entrada and p.get("ultimo"):
            try:
                if ahora - dt.datetime.fromisoformat(p["ultimo"]) < dt.timedelta(minutes=10):
                    return
            except ValueError:
                pass
        p["ultimo"] = ahora.isoformat(timespec="minutes")
        dias = p.setdefault("dias", {})
        hoy = ahora.date().isoformat()
        dias[hoy] = dias.get(hoy, 0) + 1
        corte = (ahora.date() - dt.timedelta(days=90)).isoformat()
        p["dias"] = {d: n for d, n in dias.items() if d >= corte}
        if entrada:
            p["entradas"] = p.get("entradas", 0) + 1
        datos().guardar(CLAVE_ACTIVIDAD, act)
    except Exception:  # noqa: BLE001
        pass


def _hace(iso: str | None, ahora: dt.datetime) -> str:
    if not iso:
        return "Nunca"
    try:
        t = dt.datetime.fromisoformat(iso)
    except ValueError:
        return "—"
    dias = (ahora.date() - t.date()).days
    if dias <= 0:
        return f"Hoy {t:%H:%M}"
    if dias == 1:
        return f"Ayer {t:%H:%M}"
    return f"Hace {dias} días"


def _lista_abonados() -> list[dict]:
    """Abonados con su estado en Stripe (refresca hasta 8 por visita para no tardar)."""
    reg = dict(invitados())
    out, mirados = [], 0
    altas = _altas_demo()
    for n, x in sorted(reg.items(), key=lambda kv: kv[1].get("abonado") or kv[1].get("alta", ""), reverse=True):
        prueba = estado_prueba(n, reg, altas)
        if not x.get("abonado") and not prueba and not x.get("exento"):
            continue
        if not x.get("stripe_sub") and x.get("email") and env("STRIPE_SECRET_KEY") and mirados < 8 \
                and time.time() - float(x.get("stripe_buscado") or 0) > 6 * 3600:
            mirados += 1
            try:
                _vincular_por_email(n, x["email"])
                x = dict(invitados()).get(n, x)
            except Exception:  # noqa: BLE001
                pass
        estado = x.get("stripe_estado")
        if x.get("stripe_sub") and mirados < 8 and time.time() - float(x.get("stripe_mirado") or 0) > 6 * 3600:
            mirados += 1
            try:
                estado = _estado_abono(n, forzar=True)
            except Exception:  # noqa: BLE001
                pass
        prueba = estado_prueba(n, dict(invitados()), altas) if prueba else None
        txt = ESTADOS_ABONO.get(estado, estado) if estado else "sin comprobar"
        if x.get("exento"):
            txt = "gratis (lo decides tú)"
        elif prueba and prueba["en_prueba"]:
            txt = f"prueba en la app · {prueba['dias']} días"
        elif prueba and prueba["bloqueado"]:
            txt = "prueba terminada · sin pagar"
        out.append({"nombre": n, "desde": x.get("abonado") or x.get("alta"), "estado": estado, "estado_txt": txt,
                    "problema": estado in ABONO_PROBLEMA or bool(prueba and prueba["bloqueado"]),
                    "exento": bool(x.get("exento")), "de_demo": bool(prueba) or x.get("origen") == "demo",
                    "telefono": x.get("telefono"), "email": x.get("email")})
    return out[:60]


def actividad(sesion: dict) -> dict:
    """Para el coach: quién entra a la app, cuántos días y si registra entrenos."""
    if not es_coach(sesion):
        raise Error("Solo el coach puede ver esto", 403)
    todo = datos().rutinas([CLAVE_ACTIVIDAD]).get(CLAVE_ACTIVIDAD) or {}
    act = todo.get("personas", {})
    comp, lleg = todo.get("compartidos", {}), todo.get("llegadas", {})
    ahora = _ahora()
    hoy = ahora.date()
    ult14 = [(hoy - dt.timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    def dias_en(dias: dict, n: int) -> int:
        corte = (hoy - dt.timedelta(days=n - 1)).isoformat()
        return sum(1 for d in dias if d >= corte)
    filas = []
    for p in todas_las_personas() + ["Demo"]:
        a = act.get(p, {})
        dias = a.get("dias", {})
        fila = {"id": p, "nombre": nv(p) if p != "Demo" else "Demo (solo mirar)", "ultimo": a.get("ultimo"),
                "hace": _hace(a.get("ultimo"), ahora), "dias7": dias_en(dias, 7), "dias30": dias_en(dias, 30),
                "racha": [1 if d in dias else 0 for d in ult14], "demo": p == "Demo",
                "comp_app": comp.get(p, {}).get("app", 0), "comp_entreno": comp.get(p, {}).get("entreno", 0),
                "comp_lista": comp.get(p, {}).get("lista", [])[:5], "llegadas": lleg.get(p, {}).get("n", 0),
                "llegadas_qr": lleg.get(p, {}).get("qr", 0)}
        if p == "Demo":
            fila["entradas"] = a.get("entradas", 0)
            fila["entradas7"] = sum(n for d, n in dias.items() if d >= ult14[7])
        else:
            try:
                ws = datos().entrenos(p, 120)
            except Exception:  # noqa: BLE001
                ws = []
            corte = (hoy - dt.timedelta(days=30)).isoformat()
            fila["registros30"] = sum(1 for w in ws if str(w.get("date", ""))[:10] >= corte)
            fila["ultimo_registro"] = _fecha_txt(ws[0]["date"]) if ws else None
        filas.append(fila)
    filas.sort(key=lambda f: f["ultimo"] or "", reverse=True)
    return {"personas": filas, "desde": min((d for a in act.values() for d in a.get("dias", {})), default=None),
            "total_compartidos": sum(x.get("app", 0) + x.get("entreno", 0) for x in comp.values()),
            "total_llegadas": sum(x.get("n", 0) for x in lleg.values()),
            "llegadas_instagram": lleg.get("Instagram", {}).get("n", 0),
            "abonos": [{"nombre": x.get("nombre", k), "n": x.get("n", 0), "hace": _hace(x.get("ultimo"), ahora)}
                       for k, x in sorted(todo.get("abonos", {}).items(), key=lambda kv: kv[1].get("ultimo", ""), reverse=True)],
            "abono_activo": bool(_abono_url()),
            "likes": sorted([{"nombre": x.get("nombre") or k, "texto": x.get("texto", ""), "n": len(x.get("por", [])),
                              "quien": [nv(q) if not q.startswith("Demo") else "Demo" for q in x.get("por", [])][-8:]}
                             for k, x in todo.get("likes", {}).items() if x.get("por")], key=lambda y: -y["n"])[:15],
            "contactos": [{"nombre": x.get("nombre", k), "n": x.get("n", 0), "hace": _hace(x.get("ultimo"), ahora)}
                          for k, x in sorted(todo.get("contactos", {}).items(), key=lambda kv: kv[1].get("ultimo", ""), reverse=True)],
            "pagos": [dict(x, hace=_hace(x.get("cuando"), ahora)) for x in todo.get("pagos", [])][:50],
            "abonados": _lista_abonados(),
            "propuestas": propuestas_pendientes(),
            "revisiones": [{"atleta": n, "nombre": nv(n), "desde": x.get("alta"), "cuestionario": bool(x.get("cuestionario"))}
                           for n, x in invitados().items() if x.get("revision") == "pendiente"],
            "stripe": bool(env("STRIPE_SECRET_KEY")),
            "altas": [{"nombre": a["nombre"], "hace": _hace(a.get("cuando"), ahora)} for a in todo.get("altas", [])][:20]}


# ===== vista de la rutina =====
def es_alumno(atleta: str, inv: dict) -> bool:
    return atleta in ALUMNOS or atleta in inv


def _tipo_ui(parte: str, ejercicio: str = "") -> str:
    e = norm_busqueda(_etiqueta_parte(parte))
    if "emom" in e:
        return "emom"
    if "for time" in e:
        return "fortime"
    if "amrap" in e:
        return "amrap"
    return tipo_de_linea(parte, ejercicio) or "fuerza"


def olvidadas(rut: dict, semana: int, dia_id: str, atleta: str) -> list[dict]:
    """Partes de días anteriores de esta semana que siguen sin marcar: para recordarlas y encajarlas."""
    ids = [d["id"] for d in rut["dias"]]
    if dia_id not in ids:
        return []
    out = []
    for d in rut["dias"][:ids.index(dia_id)]:
        for p, ls in agrupar_por_parte(d, semana):
            if atleta not in MOVILIDAD_ES_PARTE and es_movilidad(p, ls):
                continue  # el warm up no se recuerda
            if not (tipo_de_linea(p, ls[0]["ejercicio"]) == "accessory" or (atleta in MOVILIDAD_ES_PARTE and es_movilidad(p, ls))):
                continue  # fuerza, WOD y conditioning se pasan de día; solo se recuerdan los accessory
            m = re.search(r"\d+", d["nombre"])
            n = m.group(0) if m else d["nombre"][:2]
            letra = p.split(")")[0].strip() if ")" in p else ""
            est = estado_parte(rut, semana, d["id"], p)["estado"]
            if est == "pendiente":
                out.append({"tipo": "parte", "dia": d["id"], "dia_txt": f"D{n}", "parte": p, "letra": letra,
                            "etiqueta": _etiqueta_parte(p), "nombre": ls[0]["ejercicio"] if len(ls) == 1 else _etiqueta_parte(p)})
            elif est == "hecho":  # parte hecha pero con algún ejercicio sin hacer (p. ej. se olvidó el snatch pull)
                for l in ls:
                    if linea_no_hecha(l, semana):
                        out.append({"tipo": "linea", "dia": d["id"], "dia_txt": f"D{n}", "parte": p, "letra": letra,
                                    "etiqueta": _etiqueta_parte(p), "nombre": l["ejercicio"], "linea": l["id"],
                                    "texto": prescripcion_semana(l, semana, rut.get("ajustes"))[0] or l.get("prescripcion", "")})
    return out[:6]


def es_movilidad(parte: str, lineas: list[dict]) -> bool:
    return tipo_de_linea(parte, "") == "mobility" or any(tipo_de_linea(parte, l["ejercicio"]) == "mobility" for l in lineas)


def movilidad_primero(grupos: list[tuple[str, list[dict]]]) -> list[tuple[str, list[dict]]]:
    """La movilidad, si la hay, siempre al principio del día (las letras se ponen luego por posición)."""
    return [g for g in grupos if es_movilidad(*g)] + [g for g in grupos if not es_movilidad(*g)]


def semana_completa(rut: dict, semana: int) -> bool:
    """Todas las partes de la semana validadas (hechas, no hechas o pasadas) y sin pendientes por hacer en ella."""
    if not rut.get("dias") or not any(agrupar_por_parte(d, semana) for d in rut["dias"]):
        return False
    return not sin_validar(rut, semana) and not any(pendientes_para(rut, semana, d["id"]) for d in rut["dias"])


def avanzar_si_completa(atleta: str, rut: dict) -> tuple[dict, str | None]:
    """Si con este cambio queda validada toda la semana actual, pasa a la siguiente (solo Diego y su mujer)."""
    actual = int(rut.get("semana_actual") or 1)
    if atleta in ABRE_DIA_PENDIENTE and semana_completa(rut, actual):
        return dict(rut, semana_actual=actual + 1), f"¡Semana {actual} completada! La próxima vez se abre la {actual + 1} 🔥"
    return rut, None


def ultimos_resultados(atleta: str) -> dict:
    """{ejercicio normalizado: {valor, fecha}} con lo último que registró de cada ejercicio."""
    try:
        ws = datos().entrenos(atleta, 120)
    except Error:
        return {}
    out = {}
    for w in ws:  # vienen de más nuevo a más viejo
        for e in w.get("entries") or []:
            k = norm(e.get("name", ""))
            if k and k not in out and e.get("value") is not None:
                d = a_fecha(w["date"])
                out[k] = {"valor": fmt_valor(e["value"], e.get("unit", "")), "fecha": f"{d.day} {MESES_ES[d.month - 1]}"}
    return out


def wods_de_diego(rut_yo: dict | None) -> list[dict]:
    """Los WODs que Diego marcó como hechos: primero su semana anterior, luego la actual y después el resto."""
    if not rut_yo:
        return []
    actual = int(rut_yo.get("semana_actual") or 1)
    vistos, por_semana = set(), {}
    for sem in range(actual, 0, -1):
        for d in rut_yo["dias"]:
            for parte, lineas in agrupar_por_parte(d, sem):
                if estado_parte(rut_yo, sem, d["id"], parte)["estado"] != "hecho":
                    continue
                for l in lineas:
                    if _tipo_ui(parte, l["ejercicio"]) not in TIPOS_WOD + ("conditioning",):
                        continue
                    txt = prescripcion_semana(l, sem, rut_yo.get("ajustes"))[0]
                    if txt and norm_busqueda(txt) not in vistos:
                        vistos.add(norm_busqueda(txt))
                        por_semana.setdefault(sem, []).append({"texto": txt, "semana": sem, "dia": d["nombre"],
                                                               "nombre": l["ejercicio"]})
    orden = [actual - 1, actual] + list(range(actual - 2, 0, -1))
    return [w for sem in orden for w in por_semana.get(sem, [])]


def sugerencias(rut: dict, semana: int, de_diego: list[dict]) -> dict:
    out, i = {}, 0
    if not de_diego:
        return out
    for d in rut["dias"]:
        for parte, lineas in agrupar_por_parte(d, semana):
            for l in lineas:
                if _tipo_ui(parte, l["ejercicio"]) in TIPOS_WOD and not prescripcion_semana(l, semana, rut.get("ajustes"))[0]:
                    out[l["id"]] = de_diego[i % len(de_diego)]
                    i += 1
    return out


def _etiqueta_extra(l: dict, txt: str, semana: int, ajuste: bool, subio: bool) -> dict | None:
    if ajuste:
        return {"texto": "solo esta semana", "tono": "aviso"}
    if txt and se_repite(l, semana):
        return {"texto": "se repite", "tono": "gris"}
    p = parametros_semana(l, semana)
    if subio and semanas_que_sube(p, semana) > 0:
        return {"texto": f"+{fmt_num(semanas_que_sube(p, semana) * float(p['sube']))} kg", "tono": "bien"}
    return None


def crono_de(texto: str, parte: str, ejercicio: str) -> dict | None:
    """Cómo se cronometra: {modo: fortime|amrap|emom|libre, minutos, intervalo (seg, EMOM)}."""
    import re
    todo = f"{_etiqueta_parte(parte)} {ejercicio}\n{texto or ''}"
    t = todo.lower().replace("’", "'").replace("′", "'")
    fmts = formato_de(todo)
    m = re.search(r"(\d+)\s*(?:''|\"|s|seg|sec)?\s*(?:on|trabajo|work)\b[\s/,:-]*(\d+)\s*(?:''|\"|s|seg|sec)?\s*(?:off|descanso|rest)\b", t)
    if "tabata" in t or m:
        r = re.search(r"\bx\s*(\d+)\b|(\d+)\s*(?:rondas|rounds|sets|series)", t)
        return {"modo": "tabata", "trabajo": int(m.group(1)) if m else 20, "descanso": int(m.group(2)) if m else 10,
                "rondas": int(r.group(1) or r.group(2)) if r else 8}
    if "emom" in fmts:
        total = duracion_emom(todo)
        m = re.search(r"\be(\d)\s*mom", t)
        intervalo = int(m.group(1)) * 60 if m else 60
        m = re.search(r"\b(?:every|toutes les|cada)\s*(\d+)(?::(\d{2}))?", t)
        if m:
            intervalo = int(m.group(1)) * 60 + int(m.group(2) or 0)
        if not total:
            n = re.search(r"\b(\d+)\s*x\b", t)
            mins = [int(x) for x in re.findall(r"\b(\d{2,3})\s*(?:'|min)", t)]
            total = round(int(n.group(1)) * intervalo / 60) if n else (max(mins) if mins else None)
        return {"modo": "emom", "minutos": total or 12, "intervalo": intervalo}
    if "amrap" in fmts:
        m = re.search(r"\bamrap\s*(?:de\s*)?(\d+)", t) or re.search(r"(\d+)\s*(?:'|min)\s*amrap", t)
        return {"modo": "amrap", "minutos": int(m.group(1)) if m else 12}
    if "fortime" in fmts or re.search(r"\brondas?\b|\brounds?\b|\d+\s*x\s*\(", t):
        m = re.search(r"(?:time\s*cap|cap|tope|tc)\s*:?\s*(\d+)", t)
        return {"modo": "fortime", "minutos": int(m.group(1)) if m else None}
    return {"modo": "libre", "minutos": None}


def registro_inicial(rut: dict, dia: dict, semana: int, lineas: list[dict] | None = None, titulo: str = "") -> dict:
    """Lo mismo que _inicial_desde_dia de app.py: qué filas sugerir al registrar."""
    filas, fuerza = [], False
    for l in [x for x in (dia["lineas"] if lineas is None else lineas) if linea_activa(x, semana)]:
        txt, _, _ = prescripcion_semana(l, semana, rut.get("ajustes"))
        if es_metcon(l["ejercicio"]):
            filas.append({"id": l["id"], "name": l["ejercicio"], "valor": "", "unit": "tiempo"})
        else:
            fuerza = True
            p = peso_principal(txt)
            filas.append({"id": l["id"], "name": l["ejercicio"], "valor": fmt_num(p) if p is not None else "",
                          "unit": "kg"})
    return {"tipo": "fuerza" if fuerza else "wod", "titulo": titulo or f"Semana {semana} · {dia['nombre']}",
            "filas": filas}


def _linea(rut: dict, l: dict, semana: int, parte: str, nivel: str, alumno: bool, sug: dict | None,
           por_ejercicio: bool) -> dict:
    txt, subio, ajuste = prescripcion_semana(l, semana, rut.get("ajustes"))
    if alumno and tipo_de_linea(parte, l["ejercicio"]) is not None:
        txt = tope_db_alumno(txt)  # su RX de mancuerna es 22,5/15 (el 32,5 es del ciclo de Diego)
    tipo = _tipo_ui(parte, l["ejercicio"])
    out = {"id": l["id"], "ejercicio": l["ejercicio"], "nota": l.get("nota") or "", "texto": txt,
           "extra": _etiqueta_extra(l, txt, semana, ajuste, subio), "tipo": tipo,
           "ciclo": l.get("plan") is not None,
           "texto_sig": prescripcion_semana(l, semana + 1, rut.get("ajustes"))[0]}
    if tipo_de_linea(parte, l["ejercicio"]) is None and l.get("plan") is None:  # fuerza: pesos que se tocan
        pesos = [float(x.replace(",", ".")) for x in NUM_PESO.findall(txt)]
        out.update(kind="peso", pesos=pesos, esquema=NUM_PESO.sub("", txt).replace("  ", " ").strip(" -"))
        out["no_hecha"] = linea_no_hecha(l, semana)  # cada ejercicio de fuerza se puede marcar como no hecho
        return out
    out["kind"] = "texto"
    if not txt and sug:
        txt = tope_db_alumno(sug["texto"]) if alumno else sug["texto"]
        out["sugerencia"] = {"semana": sug["semana"], "dia": sug["dia"], "texto": sug["texto"]}
    escalable = norm_busqueda(_etiqueta_parte(parte)) != "gym"
    a_mano = l.get("niveles_txt") if txt and isinstance(l.get("niveles_txt"), dict) else None
    if a_mano:  # versiones por nivel escritas por Diego: salen en la pestaña y cada uno ve la suya
        nv_ = nivel if nivel in a_mano else "RX"
        out.update(visto=a_mano.get(nv_) or txt, nivel=nv_, versiones_nivel=a_mano, solo_bloque=False)
        return out
    nv_ = nivel if escalable and tipo in TIPOS_WOD + ("conditioning", "accessory") else "RX"
    out["visto"] = escalar(txt, nv_) if txt and nv_ != "RX" else txt
    out["nivel"] = nv_
    out["solo_bloque"] = es_metcon(l["ejercicio"]) and norm(l["ejercicio"]) in norm(parte)
    if txt and escalable and tipo in TIPOS_WOD + ("conditioning", "accessory"):
        out["versiones_nivel"] = {n: escalar(txt, n) for n in NIVELES}
        if alumno:
            filas = versiones_por_movimiento(txt)
            if filas and not all(f["RX"] == f["Inter"] == f["Scaled"] for f in filas):
                out["tabla"] = filas
        out["crono"] = crono_de(txt, parte, l["ejercicio"]) if tipo in TIPOS_WOD + ("conditioning",) else None
        refs = referencias_elite(f"{l['ejercicio']}\n{txt}", ELITE)
        if refs:
            out["elite"] = refs[0]
    return out


def _opciones(rut: dict, dia: dict, sem_aqui: int, dia_aqui: str) -> list[dict]:
    nombres = {d["id"]: d["nombre"] for d in rut["dias"]}
    sig = destino_dia_siguiente(rut, sem_aqui, dia_aqui)
    destino_sem = dia.get("pasa_a") if dia.get("pasa_a") and dia.get("pasa_a") != dia["id"] else None
    return [
        {"clave": "hecho", "texto": "Hecho", "estado": "hecho", "destino": None},
        {"clave": "no_hecho", "texto": "No hecho", "estado": "no_hecho", "destino": None},
        {"clave": "dia", "texto": nombres[sig[1]] + (f" · S{sig[0]}" if sig[0] != sem_aqui else ""),
         "estado": "pospuesto", "destino": sig},
        {"clave": "semana", "texto": (f"{nombres.get(destino_sem, 'Otro día')} · S{sem_aqui + 1}" if destino_sem
                                      else f"Semana {sem_aqui + 1}"),
         "estado": "pospuesto", "destino": destino_semana_siguiente(sem_aqui, dia.get("pasa_a") or dia["id"])},
    ]


_CICLO_CAT = {c["id"]: c["categoria"] for c in CICLOS}


def _titulo_ciclo(ciclo_id, nombre: str) -> str:
    """Título de la parte de un ciclo según lo que trabaja: fuerza, conditioning, movilidad o accessory."""
    cat = norm_busqueda(_CICLO_CAT.get(ciclo_id or "", ""))
    n = norm_busqueda(nombre)
    if cat == "fuerza" or (not cat and any(w in n for w in ("squat", "deadlift", "press", "bench"))):
        return "Fuerza"
    if cat == "engine" or (not cat and any(w in n for w in ("motor", "engine", "row", "bike", "run"))):
        return "Conditioning"
    if cat == "movilidad" or (not cat and "movilidad" in n):
        return "Movilidad"
    return "Accessory"


def _parte(rut, dia, parte, lineas, semana, partes_semana, nivel, alumno, sugs, desde=None) -> dict:
    est = estado_parte(rut, semana, dia["id"], parte)
    sem_aqui, dia_aqui = desde or (semana, dia["id"])
    opciones = _opciones(rut, dia, sem_aqui, dia_aqui)
    actual = next((o["clave"] for o in opciones if o["estado"] == est["estado"]
                   and (o["destino"] is None or list(o["destino"]) == list(est.get("destino") or []))), None)
    destino_txt = None
    if est["estado"] == "pospuesto":
        s_, did = est["destino"]
        destino_txt = next((d["nombre"] for d in rut["dias"] if d["id"] == did), "otro día") + \
            (f", semana {s_}" if s_ != semana else "")
    ciclo = None
    if lineas and lineas[0].get("ciclo") and lineas[0].get("hasta") is not None:
        l0 = lineas[0]
        ciclo = {"semana": semana - int(l0["desde"]) + 1, "total": int(l0["hasta"]) - int(l0["desde"]) + 1}
    visible = letra_visible(partes_semana, parte) if parte in partes_semana else parte
    letra, _, etiqueta = visible.partition(") ")
    if re.match(r"(?i)ciclo\s*:", etiqueta or ""):  # «C) Ciclo: HSPU» → título «Accessory» y debajo «Ciclo HSPU»
        nombre_ciclo = etiqueta.split(":", 1)[1].strip()
        etiqueta = _titulo_ciclo(lineas[0].get("ciclo") if lineas else None, nombre_ciclo)
        ciclo = {**(ciclo or {}), "nombre": nombre_ciclo}
    return {
        "parte": parte, "letra": letra if etiqueta else "", "etiqueta": etiqueta or visible,
        "tipo": _tipo_ui(parte, lineas[0]["ejercicio"] if lineas else ""),
        "estado": est["estado"], "destino_txt": destino_txt, "actual": actual, "opciones": opciones,
        "no_hechas": no_hechas_en(lineas, semana) if est["estado"] != "no_hecho" else 0,
        "historial": historial_parte(rut, dia["id"], parte, semana - 1), "ciclo": ciclo,
        "lineas": [_linea(rut, l, semana, parte, nivel, alumno, sugs.get(l["id"]), bool(dia.get("por_ejercicio")))
                   for l in lineas if linea_activa(l, semana)],
        "semana": semana, "dia_id": dia["id"],
        "es_cambio": any(l.get("sustituye") and l.get("parte") == parte for l in dia["lineas"]),
    }


_FORMATO_WOD = re.compile(r"(?i)\b(amrap|emom|e\dmom|for time|rondas?|rounds?|rft|tabata|chipper|every|cada|ladder|escalera|"
                          r"intervalos?|zona ?2|z2)\b|\d+\s*-\s*\d+\s*-\s*\d+|\d+\s*x\s*\d+|\d+\s*(?:'|min)")
_PALABRAS_COMENTARIO = re.compile(r"(?i)\b(no puedo|quitamos|he hecho|me duele|mejor|hoy no|je ne peux|j'ai)\b")


def _parece_entreno(texto: str) -> bool:
    """¿El texto es un entreno de verdad (y no vacío o un comentario del alumno)? Para la demo."""
    t = (texto or "").strip()
    if not t:
        return False
    if _PALABRAS_COMENTARIO.search(t):
        return False
    return bool(_FORMATO_WOD.search(t)) or len(re.findall(r"\d+", t)) >= 3


def _demo_accessory(partes: list[dict], semilla: int, acc: list | None = None, ciclo: dict | None = None) -> None:
    """Parte «Accessory» de ejemplo para la demo (la siguiente letra libre). Con `ciclo`, sale como parte de un ciclo."""
    molde = next((p for p in partes if p["lineas"]), None)
    if not molde:
        return
    acc = acc or DEMO_ACCESSORY
    letras = [(x.get("letra") or "").upper() for x in partes if (x.get("letra") or "")[:1].isalpha()]
    letra = chr(ord(max(letras)) + 1) if letras else "A"
    p = copy.deepcopy(molde)
    p.update(parte=f"{letra}) Accessory", letra=letra, etiqueta="Accessory", tipo="accessory", historial=[], ciclo=ciclo,
             no_hechas=0, es_cambio=False)
    base_l = copy.deepcopy(next((l for l in molde["lineas"] if l.get("kind") == "texto"), molde["lineas"][0]))
    lineas = []
    for j in range(len(acc)):
        nombre, txt = acc[j]
        l = {k: v for k, v in base_l.items() if k not in ("pesos", "esquema", "no_hecha", "crono", "elite", "tabla", "versiones_nivel", "sugerencia", "ultimo", "video")}
        l.update(id=f"demo-acc-{j}", ejercicio=nombre, texto=txt, visto=txt, kind="texto", tipo="accessory", nivel="RX",
                 nota="", extra=None, texto_sig=None, solo_bloque=False, ciclo=bool(ciclo))
        lineas.append(l)
    p["lineas"] = lineas
    partes.append(p)


def _novedad_a_su_nivel(x: dict, nivel: str) -> dict:
    """La novedad de Diego, adaptada al alumno: mancuerna como mucho 22,5/15 y escalada a su nivel."""
    txt = tope_db_alumno(str(x.get("texto") or ""))
    return {**x, "texto": escalar(txt, nivel) if nivel != "RX" else txt}


DEMO_FIJAS = {"Yo": _rutina_base_yo, "Manu Anel": _manu, "Salatti": _salatti, "Archchana": _archchana}


def _rut_demo(atleta: str) -> dict:
    """Muestra fija de cada programa de la demo: el día que se puede abrir sale hecho; el resto, con candado."""
    rut = completar(DEMO_FIJAS[atleta](), atleta)
    if atleta != "Yo":
        rut["semana_actual"] = 1  # los pesos tal cual están escritos
    for d in rut["dias"]:
        for l in d["lineas"]:
            if l["ejercicio"].lower().replace(" ", "") == "powerclean+press":
                l["ejercicio"] = "Power clean + push jerk"
            if norm_busqueda(l.get("nota", "")).startswith("propuesta"):
                l["nota"] = ""  # notas internas de la plantilla, no para la demo
    sem = int(rut.get("semana_actual") or 1)
    cerrados = DEMO_DIAS_CERRADOS_POR.get(atleta, DEMO_DIAS_CERRADOS)
    for i, d in enumerate(rut["dias"]):
        if i + 1 not in cerrados:
            for p, _ in agrupar_por_parte(d, sem):
                rut = marcar_parte(rut, sem, d["id"], p, "hecho")
    return rut


def _rellenar_demo(partes: list[dict], dia_id: str, semana: int, nivel: str, numero: int = 1, atleta: str = "") -> None:
    """En la demo no puede salir nada «por definir»: la B vacía lleva siempre un WOD y la C un conditioning
    (de verdad, distintos, con sus niveles y su cronómetro). Otras partes vacías, lo que encaje con su nombre."""
    semilla = int(hashlib.sha256(f"{dia_id}|{semana}".encode()).hexdigest(), 16)
    wods = [w for w in REPERTORIO["wod"] if "(Diego)" not in w[0]
            and (crono_de(w[1], "B) WOD", "WOD") or {}).get("modo") not in (None, "libre")] \
        or [w for w in REPERTORIO["wod"] if "(Diego)" not in w[0]]
    cond = [w for w in REPERTORIO["conditioning"]
            if (crono_de(w[1], "B) Conditioning", "Conditioning") or {}).get("modo") not in (None, "libre")] \
        or REPERTORIO["conditioning"]
    gym_mov = ("pull up", "toes to bar", "t2b", "hspu", "muscle up", "double unders", "chest to bar", "pistols", "ring dips", "handstand")
    gym = [w for w in wods if any(m in norm_busqueda(w[1]) for m in gym_mov)] or wods
    if numero == 2 and partes and atleta != "Yo" and not any((p.get("letra") or "").upper() == "C" for p in partes):
        _demo_accessory(partes, semilla)
    if atleta == DEMO_CICLO_EN and numero == 1 and partes:  # un cliente con el ciclo de HSPU en marcha
        c = next(x for x in CICLOS if x["id"] == "hspu")
        w = min(2, len(c["semanas"]))
        lineas = [(x["ejercicio"], x["prescripcion"]) for x in c["semanas"][w - 1]["sesiones"][0]]
        _demo_accessory(partes, semilla, lineas, {"semana": w, "total": len(c["semanas"]), "nombre": c["nombre"]})
    if atleta in DEMO_PESOS:  # pesos de muestra fijos (Competidor: pesos de competidor; Débutant: bench 30…)
        for p in partes:
            for l in p["lineas"]:
                if l.get("kind") != "peso":
                    continue
                n = norm_busqueda(l.get("ejercicio", ""))
                kg = next((v for patron, v in DEMO_PESOS[atleta] if re.search(patron, n)), None)
                if kg is None:
                    continue
                l["pesos"] = [float(kg)] * max(1, len(l.get("pesos") or [1]))
                l["texto"] = re.sub(r"@\s*\d+(?:[.,]\d+)?", f"@{fmt_num(kg)}", l.get("texto") or "") or f"@{fmt_num(kg)}"
                if l.get("texto_sig"):
                    l["texto_sig"] = re.sub(r"@\s*\d+(?:[.,]\d+)?", f"@{fmt_num(kg + 2.5)}", l["texto_sig"])
        if atleta == "Yo" and numero == 2 and not any((p.get("letra") or "").upper() == "C" for p in partes):  # C del día 2
            _demo_accessory(partes, semilla, [("T2B + L-sit", DEMO_C_YO)])
    for p in partes:  # fuerza sin peso puesto → uno ligero de ejemplo (mancuerna 8 kg, lo demás 10 kg)
        for l in p["lineas"]:
            if l.get("kind") == "peso" and not l.get("pesos"):
                kg = 8 if re.search(r"(?i)\b(db|dumbbell|halt[eè]re|mancuerna|goblet|kb|kettlebell)\b", l.get("ejercicio", "")) else 10
                l["pesos"] = [float(kg)]
                l["texto"] = f"{(l.get('texto') or '').strip()} @{kg}".strip()
                if l.get("texto_sig") and "@" not in l["texto_sig"]:
                    l["texto_sig"] = f"{l['texto_sig'].strip()} @{kg}"
    for i, p in enumerate(partes):
        vacias = [l for l in p["lineas"] if l.get("kind") == "texto" and (
            atleta in DEMO_PRINCIPIANTE and tipo_de_linea(p.get("parte", ""), l.get("ejercicio", "")) in ("wod", "conditioning")
            or not _parece_entreno(l.get("visto") or l.get("texto") or ""))]
        if not vacias:
            continue
        letra = (p.get("letra") or "").upper()
        etq = norm_busqueda(p.get("etiqueta") or "")
        if atleta in DEMO_PRINCIPIANTE:
            es_cond = "conditioning" in etq or letra == "C"
            lista = PRINCIPIANTE["conditioning"] if es_cond else ([DEMO_WOD_PRINCIPIANTE] if letra == "B" else PRINCIPIANTE["wod"])
            titulo = "Conditioning" if es_cond else "WOD"
        elif atleta in DEMO_CASA:
            lista = CASA["conditioning"] if ("conditioning" in etq or letra == "C") else CASA["wod"]
            titulo = "Conditioning" if lista is CASA["conditioning"] else "WOD"
        elif numero == 2 and letra == "B":
            lista, titulo = gym, "Gym / WOD"
        elif letra == "B" or (letra != "C" and "conditioning" not in etq):
            lista, titulo = wods, "WOD"
        else:
            lista, titulo = cond, "Conditioning"
        if letra in ("B", "C"):
            p["etiqueta"] = titulo
            p["tipo"] = "wod" if titulo == "WOD" else "conditioning"
        for j, l in enumerate(vacias):
            nombre, txt = lista[(semilla + i * 7 + j * 3) % len(lista)]
            nv_ = l.get("nivel") or nivel
            ya_a_medida = atleta in DEMO_PRINCIPIANTE or atleta in DEMO_CASA  # estos ya vienen a su nivel
            l["texto"] = txt
            l["visto"] = txt if ya_a_medida or nv_ == "RX" else escalar(txt, nv_)
            l["versiones_nivel"] = None if ya_a_medida else {n: escalar(txt, n) for n in NIVELES}
            if ya_a_medida:
                l["nivel"] = "RX"
            l["crono"] = crono_de(txt, f"{letra}) {titulo}", titulo)
            l["texto_sig"] = None
            l.pop("ultimo", None)
            l["extra"] = None
            l["nota"] = ""
            for k in ("tabla", "sugerencia", "elite"):
                l.pop(k, None)
            if len(p["lineas"]) == 1:
                l["ejercicio"] = nombre
                l["solo_bloque"] = False
        if vacias and letra in ("B", "C"):
            p["es_cambio"] = False


def vista(sesion: dict, atleta: str | None, semana: int | None, dia_id: str | None) -> dict:
    inv = invitados()
    personas = demo_personas() if es_demo(sesion) else [sesion["u"]] if sesion.get("u") else todas_las_personas(inv)
    atleta = atleta if atleta in personas else personas[0]
    puede_ver(sesion, atleta)
    alumno = es_alumno(atleta, inv)
    guardadas = datos().rutinas(list({atleta, "Yo", CLAVE_SOLICITUDES, CLAVE_NOVEDADES, CLAVE_ACTIVIDAD, CLAVE_VIDEOS, CLAVE_CONFIG}))
    rut = rutina(atleta, guardadas)
    if es_demo(sesion) and atleta in DEMO_FIJAS:
        rut = _rut_demo(atleta)  # la muestra de la demo es siempre la misma, cambie lo que cambie la rutina real
    if not es_demo(sesion):
        prop = propuesta_para(atleta)
        if prop and prop.get("auto") and _propuesta_pendiente(atleta, rut):  # autorizada por Diego: se aplica sola
            try:
                rut, _ = aplicar_propuesta(rut, atleta)
                datos().guardar(atleta, rut)
                rut = completar(rut, atleta)
                notificar(f"✅ Programa nuevo aplicado a {nv(atleta)}: {prop['titulo']}")
            except Exception:  # noqa: BLE001
                pass
    _apuntar(guardadas, sesion, atleta)
    if _propuestas.claves() and not es_demo(sesion):
        _avisar_propuestas(guardadas)
    coach = es_coach(sesion)
    todas_sol = (guardadas.get(CLAVE_SOLICITUDES) or {}).get("lista") or []
    if coach:  # los movimientos de partes se describen con el orden actual: «Ahora … / Quedaría …»
        for x in todas_sol:
            if x.get("kind") == "mover_parte" and "Quedaría" not in (x.get("resumen") or ""):
                try:
                    r_ = rutina(x["atleta"])
                    if r_:
                        x["resumen"] = _resumen_cambio("mover_parte", {**(x.get("datos") or {}), "semana": x.get("semana")}, r_)[:400]
                except Exception:
                    pass
    nombre_de = nombre_demo if es_demo(sesion) else nv  # en la demo, los alumnos salen como «Cliente 1, 2…»
    base = {"atleta": atleta, "nombre": nombre_de(atleta), "solo": None if es_demo(sesion) else sesion.get("u") or None,
            "personas": [{"id": p, "nombre": nombre_de(p), **({"icono": NOMBRES_DEMO.get(p, ("", "👤"))[1],
                                                                 "ciclo": p == DEMO_CICLO_EN} if es_demo(sesion) else {})}
                         for p in personas], "lang": IDIOMA_DEFECTO.get(atleta) or (inv.get(atleta) or {}).get("lang") or (None if atleta in inv else "es"),
            "app_antigua": env("APP_ANTIGUA_URL"), "tipos": {k: v[0] for k, v in TIPOS.items()},
            "unidades": UNIDADES, "con_prs": atleta not in SIN_PRS, "coach": coach, "demo": es_demo(sesion),
            "abono": {"texto": (env("ABONO_TEXTO") or ABONO_DEFECTO["texto"])} if _abono_url() else None,
            "contacto": _contacto() if not _abono_url() else None,
            "es_diego": bool(sesion.get("y")), "diego_aparte": bool(env("CONTRASENA_DIEGO")),
            "invitado": bool(sesion.get("u") == atleta and atleta in inv and not es_demo(sesion)),
            "consentimiento": (inv.get(atleta) or {}).get("consentimiento") if sesion.get("u") == atleta and not es_demo(sesion) else None,
            "objetivos_pendientes": bool(sesion.get("u") == atleta and atleta in inv and not es_demo(sesion)
                                         and ((inv.get(atleta) or {}).get("abonado") or (inv.get(atleta) or {}).get("alta", "") >= CUESTIONARIO_DESDE)
                                         and not (inv.get(atleta) or {}).get("cuestionario")),
            "objetivos": (inv.get(atleta) or {}).get("cuestionario") if sesion.get("u") == atleta else None,
            **_info_abono(sesion, atleta, inv),
            "propuesta": _propuesta_pendiente(atleta, rut) if es_coach(sesion) and not es_demo(sesion) else None,
            **_sugerencia_alumno(sesion, atleta, rut),
            "chat_no_leidos": chat_no_leidos(atleta) if not es_demo(sesion) and (sesion.get("u") == atleta or not sesion.get("u")) and not es_coach(sesion) else 0,
            "chat_activo": bool(_telegram().get("chat_id")) or es_coach(sesion),
            "abonado_nuevo": bool(sesion.get("u") == atleta and (inv.get(atleta) or {}).get("abonado", "") >=
                                  (dt.date.today() - dt.timedelta(days=3)).isoformat()),
            "telegram": (bool(env("TELEGRAM_CHAT_ID")) or bool(((guardadas.get(CLAVE_CONFIG) or {}).get("telegram") or {}).get("chat_id")))
                        if es_coach(sesion) else None,
            "puede_pesos": coach or bool((rut or {}).get("permiso_pesos")),
            "permiso_pesos": bool((rut or {}).get("permiso_pesos")),
            "solicitudes": [x for x in todas_sol if coach and (not sesion.get("u") or x["atleta"] == sesion["u"])],
            "semanas_listas": sorted(int(x) for x in (rut or {}).get("semanas_listas") or []) if coach else [],
            "mis_solicitudes": {x["linea"]: x for x in todas_sol if x["atleta"] == atleta}}
    if coach and not es_demo(sesion) and not sesion.get("u"):
        try:
            base["por_preparar"] = por_preparar(inv=inv)
        except Exception:  # noqa: BLE001
            base["por_preparar"] = []
    en_revision = (inv.get(atleta) or {}).get("revision") == "pendiente"
    if en_revision and coach:
        base["revision_pendiente"] = True
    if en_revision and sesion.get("u") == atleta and not coach and not es_demo(sesion):
        return {**base, "en_revision": True}
    if sesion.get("u") == atleta and not coach and not es_demo(sesion) and (inv.get(atleta) or {}).get("aprobado_visto") is False:
        base["recien_aprobado"] = True
    if sesion.get("u") == atleta and not coach and not es_demo(sesion):
        altas = {a.get("nombre") for a in ((guardadas.get(CLAVE_ACTIVIDAD) or {}).get("altas") or [])}
        prueba = estado_prueba(atleta, inv, altas)
        if prueba:
            base["prueba"] = prueba
            if prueba["bloqueado"]:
                return {**base, "pago_requerido": True}
    if (not rut or not rut.get("dias")) and atleta in inv and not es_demo(sesion):
        try:  # perfil nuevo al que no se le llegó a guardar la rutina de inicio (p. ej. se cortó la conexión)
            rut = completar(_rutina_inicio(atleta, inv[atleta].get("plantilla")), atleta)
        except Exception:  # noqa: BLE001
            rut = None
    if not rut or not rut.get("dias"):
        return {**base, "sin_rutina": True}
    actual = int(rut.get("semana_actual") or 1)
    aviso_semana = None
    if semana is None and atleta in ABRE_DIA_PENDIENTE and semana_completa(rut, actual):
        rut = dict(rut, semana_actual=actual + 1)  # semana validada entera: se pasa sola a la siguiente
        if not es_demo(sesion):
            datos().guardar(atleta, rut)
        aviso_semana = f"¡Semana {actual} completada! Empiezas la {actual + 1} 🔥"
        actual += 1
    semana = int(semana or actual)
    demo = es_demo(sesion)
    if demo:  # la demo solo enseña una semana: la actual, o la anterior si en la actual aún no hay ningún día completo
        def _completos(sem):
            return [d["id"] for d in rut["dias"] if resumen_dia(rut, sem, d) == "hecho"]
        semana = actual if (_completos(actual) or actual == 1) else actual - 1
        abiertos = _completos(semana) or [rut["dias"][0]["id"]]
        cerrados = {d["id"] for i, d in enumerate(rut["dias"]) if i + 1 in DEMO_DIAS_CERRADOS_POR.get(atleta, DEMO_DIAS_CERRADOS)}
        abiertos = [x for x in abiertos if x not in cerrados] or [d["id"] for d in rut["dias"] if d["id"] not in cerrados][:1] or abiertos
    nivel = rut.get("nivel") or NIVEL_DEFECTO.get(atleta, "Inter")
    if demo:
        nivel = DEMO_NIVEL.get(atleta, nivel)  # Débutant y Maison en Scaled, Renforcement en Inter
    sugs = sugerencias(rut, semana, wods_de_diego(rutina("Yo", guardadas))) if alumno else {}

    dias = []
    for d in rut["dias"]:
        dias.append({"id": d["id"], "nombre": d["nombre"], "estado": resumen_dia(rut, semana, d),
                     "pendientes": bool(pendientes_para(rut, semana, d["id"]))})
    ids = [d["id"] for d in rut["dias"]]
    # al abrir, el primer día que aún tenga alguna parte sin marcar (hecha, no hecha o movida cuenta como marcada)
    def _sin_marcar(d):
        return any(estado_parte(rut, semana, d["id"], p)["estado"] == "pendiente" for p, _ in agrupar_por_parte(d, semana))
    por_hacer = next((d["id"] for d, x in zip(rut["dias"], dias) if _sin_marcar(d) or x["pendientes"]), ids[-1])
    dia_id = dia_id if dia_id in ids else por_hacer
    if demo:  # en la demo solo se abren los días completos; el resto lleva candado
        for d in dias:
            d["bloqueado"] = d["id"] not in abiertos
        dia_id = dia_id if dia_id in abiertos else abiertos[0]
        base["demo_semana"] = semana
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    grupos = movilidad_primero(agrupar_por_parte(dia, semana))
    calentar = atleta not in MOVILIDAD_ES_PARTE
    partes_semana = [p for p, ls in grupos if not (calentar and es_movilidad(p, ls))]
    partes = []
    for p_, ls in grupos:
        x = _parte(rut, dia, p_, ls, semana, partes_semana, nivel, alumno, sugs)
        if calentar and es_movilidad(p_, ls):  # Warm up: va antes de la A y no lleva letra
            x.update(letra="", etiqueta="Mobility", calentamiento=True)
        partes.append(x)
    pendientes = []
    nombres = {d["id"]: d for d in rut["dias"]}
    for so, did, parte in pendientes_para(rut, semana, dia["id"]):
        origen = nombres[did]
        grupos_o = agrupar_por_parte(origen)
        lineas = next((ls for p, ls in grupos_o if p == parte), [])
        p = _parte(rut, origen, parte, lineas, so, [x for x, _ in movilidad_primero(agrupar_por_parte(origen, so))], nivel, alumno,
                   {}, desde=(semana, dia["id"]))
        p["origen"] = f"{origen['nombre']} · semana {so}"
        p["registro"] = {**registro_inicial(rut, origen, so, lineas, f"Semana {so} · {origen['nombre']} · {parte}"),
                         "partes": [{"parte": parte, "texto": p["etiqueta"], "semana": so, "dia": did}]}
        pendientes.append(p)
    ultimos = ultimos_resultados(atleta)
    videos = {**VIDEOS_BASE, **(guardadas.get(CLAVE_VIDEOS) or {})}
    for p_ in partes + pendientes:
        for l in p_["lineas"]:
            u = ultimos.get(norm(l["ejercicio"]))
            if u:
                l["ultimo"] = u
            vid = videos.get(norm(l["ejercicio"]))
            if vid and vid.get("url"):
                l["video"] = vid
    if demo:  # en la demo no puede salir nada «por definir»: cada parte vacía lleva un WOD de verdad (distinto en B y C)
        _rellenar_demo(partes, dia["id"], semana, nivel, 1 + [d["id"] for d in rut["dias"]].index(dia["id"]), atleta)
    if aviso_semana:
        base["aviso"] = aviso_semana
    return {**base, "semana": semana, "actual": actual, "nivel": nivel, "niveles": NIVELES, "alumno": alumno,
            "dias": dias, "dia": {"id": dia["id"], "nombre": dia["nombre"], "estado": resumen_dia(rut, semana, dia),
                                  "por_ejercicio": bool(dia.get("por_ejercicio"))},
            "partes": partes, "pendientes": pendientes,
            "novedades": [_novedad_a_su_nivel(x, nivel) for x in novedades_para(
                rut, (guardadas.get(CLAVE_NOVEDADES) or {}).get("lista") or [], rutina("Yo", guardadas))]
                if alumno and not demo else [],
            "retests": [_retest_ui(x) for x in rut.get("retests") or []
                        if x.get("estado") == "pendiente" and x.get("fecha", "9") <= dt.date.today().isoformat()],
            "retest_lineas": {x["linea"]: _fecha_corta(x["fecha"]) for x in rut.get("retests") or []
                              if x.get("estado") == "pendiente" and x.get("linea")},
            "registro": {**registro_inicial(rut, dia, semana),
                         "partes": [{"parte": p["parte"], "texto": f"{p['letra']} · {p['etiqueta']}".strip(" ·"),
                                     "warmup": bool(p.get("calentamiento")), "semana": semana, "dia": dia["id"]}
                                    for p in partes]},
            "faltan": sin_validar(rut, semana) if semana <= actual else [],
            "olvidadas": olvidadas(rut, semana, dia["id"], atleta) if semana == actual else []}


# ===== biblioteca y novedades =====
# Más ideas para «Al azar» (se suman al repertorio y a la biblioteca)
EXTRA_WODS = [
    ("EMOM 12' cleans", "EMOM 12': 3 power cleans @70%"),
    ("EMOM 14' engine", "EMOM 14':\nmin 1: 14/12 cal row\nmin 2: 12 burpees"),
    ("EMOM 20' 4 estaciones", "EMOM 20':\nmin 1: 15 wall balls\nmin 2: 12 T2B\nmin 3: 14/11 cal bike\nmin 4: descanso"),
    ("EMOM 16' gym", "EMOM 16':\nimpar: 5 strict pull ups\npar: 10 HSPU (o 15 pike push ups)"),
    ("E2MOM x6 thrusters", "E2MOM x6: 10 thrusters @43/30 + 20 DU"),
    ("EMOM 18' DB", "EMOM 18':\nmin 1: 12 DB snatch alternos\nmin 2: 10 DB box step overs\nmin 3: 30\" plank"),
    ("E3MOM x5 run", "E3MOM x5: 400 m run + 10 burpees"),
    ("EMOM 10' snatch", "EMOM 10': 2 squat snatch @75%"),
    ("AMRAP 12' clásico", "AMRAP 12': 9 KB swings, 12 box jumps, 15 wall balls"),
    ("AMRAP 15' run", "AMRAP 15': 200 m run, 10 T2B, 15 air squats"),
    ("AMRAP 10' DB", "AMRAP 10': 8 DB thrusters, 8 DB renegade rows, 8 burpees"),
    ("AMRAP 20' chipper", "AMRAP 20': 5 pull ups, 10 push ups, 15 air squats, 20 DU"),
    ("For time 21-15-9 DB", "For time 21-15-9: DB snatch @22,5 + burpees over DB"),
    ("For time 5 rondas", "5 rondas for time: 15 cal row, 12 deadlifts @60, 9 bar facing burpees"),
    ("For time pirámide", "For time 10-9-8…1: KB swings + goblet squats"),
    ("For time 1000 m", "For time: 1000 m row, 50 thrusters @20 kg, 30 pull ups · cap 15'"),
]


def guardar_en_biblioteca(tipo: str, nombre: str, texto: str, atleta: str):
    """Igual que en app.py: lo creado a mano en la rutina se guarda también en su sección para reutilizarlo."""
    tipo = {"emom": "wod", "fortime": "wod", "amrap": "wod"}.get(tipo, tipo)
    if tipo not in CLAVES_BIBLIO or not (texto or "").strip():
        return
    try:
        import uuid
        bib = dict(datos().rutinas([CLAVE_BIBLIOTECA]).get(CLAVE_BIBLIOTECA) or {})
        clave = CLAVES_BIBLIO[tipo]
        if any(norm_busqueda(i.get("texto", "")) == norm_busqueda(texto) for i in bib.get(clave, [])):
            return
        generico = norm(nombre) in {norm(x) for x in TIPOS_PARTE} | {"wod", "gym / wod", "conditioning"}
        bib[clave] = bib.get(clave, []) + [{
            "id": uuid.uuid4().hex[:8], "nombre": "" if generico else nombre.strip(), "texto": texto.strip(),
            "quien": [atleta], "fecha": dt.date.today().isoformat(), "resultado": "", "idea": True, "origen": "rutina"}]
        datos().guardar(CLAVE_BIBLIOTECA, bib)
    except Error:
        pass


_MOVIMIENTOS = ("squat", "deadlift", "clean", "snatch", "jerk", "press", "thruster", "burpee", "pull", "push", "row", "remo",
                "bike", "ski", "run", "correr", "carrera", "wall ball", "wb", "kb", "db", "dumbbell", "mancuerna", "swing",
                "lunge", "zancada", "box", "du ", "double", "t2b", "toes", "muscle", "rmu", "bmu", "hspu", "sit up", "situp",
                "plank", "plancha", "cal ", "cals", "amrap", "emom", "e2mom", "e3mom", "for time", "ronda", "round", "tabata",
                "every", "stretch", "mobility", "movilidad", "mobilite", "hip", "couch", "pigeon", "90/90", "banded", "hold",
                "carry", "farmer", "rope", "pistol", "dip", "ring", "handstand", "step", "jump", "sprint", "metros", " m ",
                "km", "rest", "descanso", "reps", "series", "x10", "x5", "@", "rm", "goblet", "hollow", "elliptique",
                "elíptica", "eliptica", "haltere", "fente", "gainage", "pont", "etirement", "étirement", "squats", "curl",
                "dislocate", "pancake", "bridge", "raise", "extension", "flexion", "abs", "core")
_NO_ENTRENO = ("niña", "nina", "perro", "ruta ", "rutas", "planning", "granada", "cueva", "embalse", "planes", "plan ",
               "playa", "restaurante", "vistas", "excursion", "excursión", "alhambra", "hotel", "viaje", "cumpleaños",
               "te preparo", "si quieres", "¿prefieres", "prefieres", "jaja", "jeje")


def parece_entreno(texto: str, nombre: str = "") -> bool:
    """¿Es un entreno (WOD, conditioning, accessory, movilidad) y no una conversación o un plan cualquiera?"""
    import re
    t = f"{nombre}\n{texto or ''}".lower()
    if not texto or len(texto) > 900 or not re.search(r"\d", t):
        return False
    malas = sum(1 for w in _NO_ENTRENO if w in t)
    emojis = len(re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", t))
    if malas >= 2 or emojis > 4 or t.count("?") > 2:
        return False
    buenas = sum(1 for w in _MOVIMIENTOS if w in f" {t} ") + len(re.findall(r"\b\d+\s*x\s*\d+", t))
    return buenas >= 1 and buenas > malas


_MOVS_NOMBRE = [  # (palabras que lo detectan, nombre que se ve), en orden de prioridad
    (("muscle up", "rmu", "bmu", "ring mu"), "Muscle ups"), (("thruster",), "Thrusters"), (("wall ball", "wb"), "Wall balls"),
    (("burpee",), "Burpees"), (("toes to bar", "t2b", "ttb"), "T2B"), (("c2b", "chest to bar"), "C2B"),
    (("pull up", "pull-up", "pullup", "dominada"), "Pull ups"), (("hspu", "handstand push"), "HSPU"),
    (("double under", "dus", " du "), "DU"), (("db snatch",), "DB snatch"), (("kb swing", "swing"), "KB swings"),
    (("box jump", "box step"), "Box jumps"), (("deadlift", "peso muerto"), "Deadlift"), (("squat clean", "power clean", "clean"), "Cleans"),
    (("snatch",), "Snatch"), (("lunge", "zancada", "fente"), "Lunges"), (("farmer",), "Farmer carry"),
    (("push up", "flexion"), "Push ups"), (("air squat", "squats"), "Squats"), (("sit up", "situp"), "Sit ups"),
    (("rope climb", "cuerda"), "Rope climbs"), (("run", "correr", "corriendo", "milla", "mile", "carrera"), "Run"),
    (("row", "remo"), "Row"), (("ski",), "Ski"), (("bike", "bici", "assault", "echo", "aab"), "Bike"),
]
_CARDIO = {"Run", "Row", "Ski", "Bike"}
_GENERICOS = {"wod", "conditioning", "accessory", "mobility", "movilidad", "emom", "amrap", "for time", "gym", "metcon", "cardio"}


def _limpia_texto_idea(texto: str) -> str:
    """Quita las frases de chat que haya antes del entreno («Mañana me haces solo cardio»…)."""
    import re
    lineas = [l.rstrip() for l in (texto or "").split("\n")]
    while lineas and lineas[0].strip() and not re.search(r"\d", lineas[0]) and \
            not any(w in lineas[0].lower() for w in ("emom", "amrap", "for time", "every", "tabata", "rondas", "rounds")):
        lineas.pop(0)
    while lineas and not lineas[0].strip():
        lineas.pop(0)
    return "\n".join(lineas).strip() or (texto or "").strip()


def nombre_idea(texto: str, nombre: str = "") -> str:
    """Un nombre corto y útil: el que tenía si es bueno; si no, formato + movimientos principales."""
    import re
    t = " " + (texto or "").lower().replace("’", "'").replace("′", "'") + " "
    primera = (texto or "").strip().split("\n")[0].strip().lower()
    n = (nombre or "").strip()
    charla = re.search(r"\b(me|te|mañana|manana|hoy|haces|hacemos|quieres|vamos)\b|\?", n.lower())
    if n and n.lower() != primera and norm(n) not in _GENERICOS and not charla and len(n) <= 40:
        return n
    formato = ""
    m = re.search(r"\bevery\s*(\d+(?::\d{2})?)\s*'?\s*x\s*(\d+)", t) or re.search(r"\bcada\s*(\d+(?::\d{2})?)\s*'?\s*x\s*(\d+)", t)
    if m:
        formato = f"Every {m.group(1)}' x{m.group(2)}"
    elif re.search(r"\be(\d)mom", t):
        k = re.search(r"\be(\d)mom\s*x?\s*(\d+)?", t)
        formato = f"E{k.group(1)}MOM" + (f" x{k.group(2)}" if k.group(2) else "")
    elif "emom" in t:
        k = re.search(r"emom\s*(\d+)", t)
        formato = f"EMOM {k.group(1)}'" if k else "EMOM"
    elif "amrap" in t:
        k = re.search(r"amrap\s*(\d+)", t)
        formato = f"AMRAP {k.group(1)}'" if k else "AMRAP"
    elif "tabata" in t:
        formato = "Tabata"
    elif re.search(r"for time|\brft\b|por tiempo", t):
        k = re.search(r"(\d+)\s*(?:rondas|rounds|rft)", t)
        formato = f"{k.group(1)} RFT" if k else "For time"
    else:
        k = re.search(r"\b(\d+)\s*(?:rondas|rounds)\b", t)
        if k:
            formato = f"{k.group(1)} rondas"
        elif re.match(r"\s*\d+-\d+-\d+", t.strip()):
            formato = re.match(r"\s*(\d+(?:-\d+)+)", t.strip()).group(1)
    if not formato or formato == "For time":
        k = re.match(r"\s*(?:for time\s*)?(\d+)\s*x\s", t.strip() + " ")
        if k:
            formato = f"{k.group(1)} RFT" if formato == "For time" or "for time" in t else f"{k.group(1)} rondas"
    resto, encontrados = t, []
    for claves, visto in _MOVS_NOMBRE:  # de más concreto a más general: «DB snatch» antes que «snatch»
        pos = [resto.find(c) for c in claves if c in resto]
        if pos and visto not in [v for _, v in encontrados]:
            encontrados.append((min(pos), visto))
            for c in claves:
                resto = resto.replace(c, " " * len(c))
    movs = [v for _, v in sorted(encontrados)]
    if not movs:
        return n or ((texto or "").strip().split("\n")[0][:40])
    if not formato:
        formato = "Cardio" if set(movs) <= _CARDIO else ("Chipper" if len(movs) >= 4 else "")
    cuerpo = " · ".join(movs[:4]) + (" …" if len(movs) > 4 else "")
    return f"{formato}: {cuerpo}" if formato else cuerpo


def limpiar_biblioteca(sesion: dict, c: dict) -> dict:
    """Quita de la biblioteca lo que no sea un entreno. Con «probar» solo cuenta lo que quitaría."""
    if not es_coach(sesion):
        raise Error("Solo el coach puede limpiar la biblioteca", 403)
    bib = dict(datos().rutinas([CLAVE_BIBLIOTECA]).get(CLAVE_BIBLIOTECA) or {})
    quitados, nuevo = [], {}
    for clave, val in bib.items():
        if clave in CLAVES_BIBLIO.values() and isinstance(val, list):
            buenos = [i for i in val if parece_entreno(i.get("texto", ""), i.get("nombre", ""))]
            quitados += [(i.get("nombre") or i.get("texto", "")[:60]).strip() for i in val if i not in buenos]
            nuevo[clave] = buenos
        else:
            nuevo[clave] = val
    if not c.get("probar") and quitados:
        datos().guardar(CLAVE_BIBLIOTECA, nuevo)
    return {"quitados": len(quitados), "ejemplos": quitados[:8], "hecho": not c.get("probar")}


def ideas() -> dict:
    """Ideas para rellenar una parte: el repertorio + lo ya guardado en la biblioteca."""
    bib = datos().rutinas([CLAVE_BIBLIOTECA]).get(CLAVE_BIBLIOTECA) or {}
    def de_bib(clave):
        out, vistos = [], set()
        for i in reversed(bib.get(clave) or []):
            if not parece_entreno(i.get("texto", ""), i.get("nombre", "")):
                continue
            texto = _limpia_texto_idea(i.get("texto", ""))
            if norm_busqueda(texto) in vistos:
                continue
            vistos.add(norm_busqueda(texto))
            out.append({"nombre": nombre_idea(texto, i.get("nombre", "")), "texto": texto})
        return out[:40]
    rep = lambda k: [{"nombre": n, "texto": t} for n, t in REPERTORIO.get(k, [])]
    return {"volumen": [{"nombre": n, "texto": t} for n, t in VOLUMEN],
            "wod": de_bib("wods") + rep("wod") + [{"nombre": n, "texto": t} for n, t in EXTRA_WODS], "conditioning": de_bib("conditionings") + rep("conditioning"),
            "accessory": de_bib("accessories") + rep("accessory"), "mobility": de_bib("movilidad") + rep("mobility"),
            "tipos": TIPOS_PARTE}


def _tipo_de_etiqueta(etiqueta: str) -> str:
    e = norm_busqueda(etiqueta)
    if "volume" in e or "conditioning" in e:
        return "conditioning"
    if "mobil" in e or "movil" in e:
        return "mobility"
    if "accessor" in e:
        return "accessory"
    if "fuerza" in e:
        return "fuerza"
    return "wod"


def _novedad(rut_yo: dict, etiqueta: str, nombre: str, texto: str, semana: int, dia: str | None = None):
    """Lo que Diego se pone a sí mismo, para ofrecérselo a sus alumnos."""
    import uuid
    if not _novedad_valida({"texto": texto}):
        return
    reg = datos().rutinas([CLAVE_NOVEDADES]).get(CLAVE_NOVEDADES) or {}
    lista = [x for x in reg.get("lista") or [] if norm_busqueda(x.get("texto", "")) != norm_busqueda(texto)]
    lista.append({"id": uuid.uuid4().hex[:10], "etiqueta": etiqueta, "nombre": nombre or etiqueta, "texto": texto.strip(),
                  "semana": semana, "dia": dia, "fecha": dt.date.today().isoformat()})
    datos().guardar(CLAVE_NOVEDADES, {"lista": lista[-30:]})


def _fecha_corta(iso: str) -> str:
    try:
        d = dt.date.fromisoformat(iso[:10])
    except ValueError:
        return iso
    return f"{d.day} {MESES_ES[d.month - 1]}"


def _retest_ui(x: dict) -> dict:
    return {"id": x["id"], "nombre": x["nombre"], "etiqueta": x.get("etiqueta", "WOD"), "texto": x["texto"],
            "antes": x.get("antes"), "creado": _fecha_corta(x.get("creado", ""))}


def _novedad_hecha(rut_yo: dict | None, nov: dict) -> bool:
    """Lo que Diego se pone solo se ofrece a los alumnos cuando él lo ha marcado como hecho."""
    if not nov.get("dia"):
        return True  # novedades antiguas (antes de este cambio)
    if not rut_yo:
        return False
    sem = int(nov.get("semana") or 1)
    dia = next((d for d in rut_yo.get("dias") or [] if d["id"] == nov["dia"]), None)
    if not dia:
        return False
    objetivo = norm_busqueda(nov.get("texto", ""))
    for l in dia["lineas"]:
        txt = prescripcion_semana(l, sem, rut_yo.get("ajustes"))[0] or l.get("prescripcion", "")
        if norm_busqueda(txt) == objetivo and l.get("parte"):
            return estado_parte(rut_yo, sem, dia["id"], l["parte"])["estado"] == "hecho"
    return False


def novedades_para(rut: dict, novedades: list[dict], rut_yo: dict | None = None) -> list[dict]:
    vistas = set(rut.get("novedades_vistas") or [])
    hace = (dt.date.today() - dt.timedelta(days=21)).isoformat()
    return [x for x in reversed(novedades) if x["id"] not in vistas and x.get("fecha", "") >= hace
            and _novedad_valida(x) and _novedad_hecha(rut_yo, x)][:1]  # solo una cada vez (la más nueva); al decir sí/no, sale la siguiente


def _novedad_valida(x: dict) -> bool:
    """Fuera las de prueba o vacías (p. ej. texto «0»)."""
    txt = str(x.get("texto") or "").strip()
    return len(txt) >= 6 and bool(re.search(r"[A-Za-zÀ-ÿ]{3}", txt))


def puede_programar(sesion: dict, rut: dict) -> bool:
    return es_coach(sesion) or bool(rut.get("permiso_pesos"))


CAMBIOS_PROGRAMA = ("editar_texto", "cambiar_parte", "anadir_parte", "deshacer_parte", "quitar_ajuste", "mover_parte")


def aplicar_programa(rut: dict, tipo: str, c: dict, semana: int, atleta: str) -> tuple[dict, str]:
    """Cambios en lo programado (texto de un WOD, cambiar/añadir/volver una parte). Devuelve (rutina, aviso)."""
    texto = str(c.get("texto") or "").strip()[:3000]
    solo = bool(c.get("solo_esta"))
    if tipo == "mover_parte":
        dia_ = next(d for d in rut["dias"] if d["id"] == c.get("dia"))
        antes = [p for p, _ in agrupar_por_parte(dia_)]
        if c.get("con") in antes and c.get("parte") in antes:  # arrastrada: se queda donde estaba la parte «con»
            c = {**c, "hasta": antes.index(c["con"])}
        if c.get("hasta") is not None and c.get("parte") in antes:  # arrastrada: hasta la posición elegida
            desde, hasta = antes.index(c["parte"]), max(0, min(len(antes) - 1, int(c["hasta"])))
            etq = _etiqueta_parte(c["parte"])
            paso = 1 if hasta > desde else -1
            for i in range(desde, hasta, paso):
                orden = [p for p, _ in agrupar_por_parte(next(d for d in rut["dias"] if d["id"] == c.get("dia")))]
                actual = orden[i] if _etiqueta_parte(orden[i]) == etq else next((x for x in orden if _etiqueta_parte(x) == etq), None)
                if not actual:
                    break
                rut = mover_parte(rut, c.get("dia"), actual, paso)
        else:
            rut = mover_parte(rut, c.get("dia"), c.get("parte"), int(c.get("direccion") or 1))
        despues = [p for p, _ in agrupar_por_parte(next(d for d in rut["dias"] if d["id"] == c.get("dia")))]
        return rut, ("Parte movida ↕️" if antes != despues else "Esa parte ya está al límite")
    if tipo == "quitar_ajuste":  # deshace el cambio «solo esta semana» de una línea
        rut = copy.deepcopy(rut)
        aj = (rut.get("ajustes") or {}).get(str(semana)) or {}
        aj.pop(c.get("linea"), None)
        rut["ajustes"] = {k: v for k, v in (rut.get("ajustes") or {}).items() if v}
        return rut, "Quitado el cambio de esta semana: vuelve lo que había"
    if tipo == "editar_texto":
        l = next((x for d in rut["dias"] for x in d["lineas"] if x["id"] == c.get("linea")), None)
        if not l:
            raise Error("No se encontró esa parte")
        nombre = str(c.get("nombre") or l["ejercicio"]).strip()[:120]
        antes = prescripcion_semana(l, semana, rut.get("ajustes"))[0]
        rut = editar_texto_linea(rut, l["id"], semana, nombre, texto, l.get("nota", ""), solo)
        sig = c.get("texto_sig")
        if sig is not None and str(sig).strip() != prescripcion_semana(
                next(x for d in rut["dias"] for x in d["lineas"] if x["id"] == l["id"]), semana + 1, rut.get("ajustes"))[0]:
            rut = editar_texto_linea(rut, l["id"], semana + 1, nombre, str(sig).strip(), l.get("nota", ""), True)
        if texto != antes:
            guardar_en_biblioteca(_tipo_ui(l.get("parte", ""), l["ejercicio"]), nombre, texto, atleta)
        return rut, ("Guardado solo para esta semana" if solo else f"Guardado desde la semana {semana}") + \
            (" (y ajustada la que viene)" if sig is not None else "")
    etiqueta = str(c.get("etiqueta") or "WOD").strip()[:40] or "WOD"
    nombre = str(c.get("nombre") or "").strip()[:120] or etiqueta
    if tipo in ("cambiar_parte", "anadir_parte") and not texto:
        raise Error("Escribe qué toca")
    sube = 2.5 if _tipo_de_etiqueta(etiqueta) == "fuerza" and not solo and "@" in texto else 0.0
    if tipo == "cambiar_parte":
        rut = sustituir_parte(rut, c["dia"], c["parte"], semana, etiqueta, nombre, texto, solo, sube)
        aviso = f"Cambiado por {etiqueta}" + (" solo esta semana" if solo else f" desde la semana {semana}")
    elif tipo == "anadir_parte":
        rut = anadir_parte(rut, c["dia"], etiqueta, nombre, texto, semana, solo, sube)
        aviso = f"{etiqueta} añadido" + (" solo esta semana" if solo else f" desde la semana {semana}")
    else:
        dia = next((d for d in rut["dias"] if d["id"] == c.get("dia")), {"lineas": []})
        quitados = {norm_busqueda(prescripcion_semana(l, semana, rut.get("ajustes"))[0] or l.get("prescripcion", ""))
                    for l in dia["lineas"] if l.get("parte") == c.get("parte") and l.get("sustituye")}
        rut = deshacer_sustitucion(rut, c["dia"], c["parte"], semana)
        if atleta == "Yo" and quitados:  # lo que deshace Diego deja de ofrecerse a los alumnos
            reg = datos().rutinas([CLAVE_NOVEDADES]).get(CLAVE_NOVEDADES) or {}
            datos().guardar(CLAVE_NOVEDADES, {"lista": [x for x in reg.get("lista") or []
                                                        if norm_busqueda(x.get("texto", "")) not in quitados]})
        return rut, "Vuelve lo que había"
    guardar_en_biblioteca(_tipo_de_etiqueta(etiqueta), nombre, texto, atleta)
    if atleta == "Yo":
        _novedad(rut, etiqueta, nombre, texto, semana, c.get("dia"))
    return rut, aviso


def _resumen_cambio(tipo: str, c: dict, rut: dict) -> str:
    if tipo == "editar_texto":
        l = next((x for d in rut["dias"] for x in d["lineas"] if x["id"] == c.get("linea")), {})
        return f"{l.get('ejercicio', 'WOD')}: {c.get('texto', '')}"
    if tipo == "deshacer_parte":
        return f"Volver a lo que había en {c.get('parte', '')}"
    if tipo == "quitar_ajuste":
        return "Quitar el cambio de esta semana"
    if tipo == "mover_parte":
        try:
            import copy
            dia = next(d for d in rut["dias"] if d["id"] == c.get("dia"))
            antes = [p for p, _ in agrupar_por_parte(dia)]
            sim, _ = aplicar_programa(copy.deepcopy(rut), tipo, c, int(c.get("semana") or rut.get("semana_actual") or 1), "")
            dia2 = next(d for d in sim["dias"] if d["id"] == c.get("dia"))
            despues = [p for p, _ in agrupar_por_parte(dia2)]
            if c.get("con"):
                accion_ = f"Mover {c.get('parte', '')} al sitio de {c['con']}"
            else:
                accion_ = f"{'Bajar' if int(c.get('direccion') or 1) > 0 else 'Subir'} la parte {c.get('parte', '')}"
            return (f"{accion_} · {dia.get('nombre') or c.get('dia')}\nAhora: " + " · ".join(antes)
                    + "\nQuedaría: " + " · ".join(despues))
        except Exception:
            return f"{'Bajar' if int(c.get('direccion') or 1) > 0 else 'Subir'} la parte {c.get('parte', '')}"
    return f"{'Cambiar' if tipo == 'cambiar_parte' else 'Añadir'} {c.get('etiqueta', '')}: {c.get('texto', '')}"


# ===== acciones =====
def accion(sesion: dict, c: dict) -> dict:
    atleta = c.get("atleta")
    puede_ver(sesion, atleta)
    exigir_pago(sesion, atleta)
    if atleta not in todas_las_personas():
        raise Error("Persona desconocida")
    rut = rutina(atleta)
    if not rut:
        raise Error("Esa persona no tiene rutina")
    tipo = c.get("tipo")
    semana = int(c.get("semana") or rut.get("semana_actual") or 1)
    semana_antes = int(rut.get("semana_actual") or 1)
    aviso = "Guardado"
    if tipo == "marcar":
        estado = c.get("estado")
        if estado not in ("hecho", "no_hecho", "pospuesto", None):
            raise Error("Estado no válido")
        rut = marcar_parte(rut, semana, c["dia"], c["parte"], estado, c.get("destino"))
        aviso = {"hecho": "¡Hecho!", "no_hecho": "Apuntado: la semana que viene repite peso",
                 "pospuesto": "Pasado a otro día", None: "Quitada la marca"}[estado]
    elif tipo == "peso":
        if not (es_coach(sesion) or rut.get("permiso_pesos")):
            raise Error("Los pesos los decide tu coach. Envíale el cambio para que lo apruebe.", 403)
        valores = [float(v) for v in c.get("valores") or []]
        if not valores or any(v < 0 or v > 1000 for v in valores):
            raise Error("Peso no válido")
        nueva_presc = poner_pesos(c.get("texto") or "", valores)
        rut, tocados = cambiar_pesos(rut, semana, {c["linea"]: nueva_presc}, bool(c.get("solo_semana")),
                                     c.get("propagar", True) is not False)
        aviso = "Peso guardado" + (f" (también en {', '.join(tocados)})" if tocados else "")
    elif tipo == "solicitar_peso":
        valores = [float(v) for v in c.get("valores") or []]
        if not valores or any(v < 0 or v > 1000 for v in valores):
            raise Error("Peso no válido")
        l = next((x for d in rut["dias"] for x in d["lineas"] if x["id"] == c.get("linea")), None)
        if not l:
            raise Error("No se encontró ese ejercicio")
        import uuid
        reg = datos().rutinas([CLAVE_SOLICITUDES]).get(CLAVE_SOLICITUDES) or {}
        lista = [x for x in reg.get("lista") or [] if not (x["atleta"] == atleta and x["linea"] == l["id"])]
        lista.append({"id": uuid.uuid4().hex[:10], "atleta": atleta, "nombre": nv(atleta), "linea": l["id"],
                      "ejercicio": l["ejercicio"], "semana": semana, "texto": c.get("texto") or "",
                      "antes": [float(x.replace(",", ".")) for x in NUM_PESO.findall(c.get("texto") or "")],
                      "valores": valores, "solo_semana": bool(c.get("solo_semana")),
                      "propagar": c.get("propagar", True) is not False, "mensaje": str(c.get("mensaje") or "")[:500],
                      "fecha": dt.datetime.now(dt.timezone.utc).isoformat()})
        datos().guardar(CLAVE_SOLICITUDES, {"lista": lista[-200:]})
        v = vista(sesion, atleta, int(c.get("ver_semana") or semana), c.get("ver_dia"))
        notificar(f"⚖️ {nv(atleta)} pide cambiar peso\n{l['ejercicio']}: {c.get('texto') or ''} → {', '.join(str(x) for x in valores)} kg"
                  + (f"\n💬 {c.get('mensaje')}" if c.get("mensaje") else "") + "\nÁbrelo en la app → 🔔")
        v["aviso"] = f"Enviado a {nv('Yo')}: te avisará cuando lo apruebe"
        return v
    elif tipo == "ponerme_novedad" and not puede_programar(sesion, rut):
        # sin permiso para programar, la novedad no se añade sola (saldría una D, E, F…): va a Diego como solicitud
        reg = datos().rutinas([CLAVE_NOVEDADES]).get(CLAVE_NOVEDADES) or {}
        nov = next((x for x in reg.get("lista") or [] if x["id"] == c.get("id")), None)
        if not nov:
            raise Error("Esa novedad ya no está")
        datos().guardar(atleta, dict(rut, novedades_vistas=(rut.get("novedades_vistas") or [])[-60:] + [nov["id"]]))
        return accion(sesion, {**c, "tipo": "anadir_parte", "etiqueta": nov["etiqueta"], "nombre": nov["nombre"],
                               "texto": nov["texto"], "solo_esta": not c.get("adelante"),
                               "mensaje": "Quiere probar esta novedad"})
    elif tipo in CAMBIOS_PROGRAMA:
        if not puede_programar(sesion, rut):
            import uuid
            reg = datos().rutinas([CLAVE_SOLICITUDES]).get(CLAVE_SOLICITUDES) or {}
            lista = reg.get("lista") or []
            datos_c = {k: c.get(k) for k in ("linea", "texto", "texto_sig", "nombre", "solo_esta", "dia", "parte", "etiqueta", "direccion", "hasta", "con")}
            lista.append({"id": uuid.uuid4().hex[:10], "atleta": atleta, "nombre": nv(atleta), "kind": tipo,
                          "linea": c.get("linea") or f"{c.get('dia')}|{c.get('parte')}", "semana": semana,
                          "datos": datos_c, "resumen": _resumen_cambio(tipo, c, rut)[:400], "antes": [], "valores": [],
                          "mensaje": str(c.get("mensaje") or "")[:500], "fecha": dt.datetime.now(dt.timezone.utc).isoformat()})
            datos().guardar(CLAVE_SOLICITUDES, {"lista": lista[-200:]})
            v = vista(sesion, atleta, int(c.get("ver_semana") or semana), c.get("ver_dia"))
            notificar(f"✏️ {nv(atleta)} pide un cambio en su rutina\n{_resumen_cambio(tipo, c, rut)[:300]}"
                      + (f"\n💬 {c.get('mensaje')}" if c.get("mensaje") else "") + "\nÁbrelo en la app → 🔔")
            v["aviso"] = f"Enviado a {nv('Yo')} para que lo apruebe"
            return v
        rut, aviso = aplicar_programa(rut, tipo, c, semana, atleta)
    elif tipo == "ponerme_novedad":
        reg = datos().rutinas([CLAVE_NOVEDADES]).get(CLAVE_NOVEDADES) or {}
        nov = next((x for x in reg.get("lista") or [] if x["id"] == c.get("id")), None)
        if not nov:
            raise Error("Esa novedad ya no está")
        rut = anadir_parte(rut, c["dia"], nov["etiqueta"], nov["nombre"], nov["texto"], semana, not c.get("adelante"))
        rut = dict(rut, novedades_vistas=(rut.get("novedades_vistas") or [])[-60:] + [nov["id"]])
        aviso = f"{nov['etiqueta']} añadido a tu día"
    elif tipo == "retest":
        import uuid
        l = next((x for d in rut["dias"] for x in d["lineas"] if x["id"] == c.get("linea")), None)
        if not l:
            raise Error("No se encontró ese entreno")
        meses = 2 if str(c.get("meses")) == "2" else 1
        fecha = dt.date.today() + dt.timedelta(days=28 * meses)
        texto = prescripcion_semana(l, semana, rut.get("ajustes"))[0] or l.get("prescripcion", "")
        antes = ultimos_resultados(atleta).get(norm(l["ejercicio"]))
        lista = [x for x in rut.get("retests") or [] if not (x.get("linea") == l["id"] and x.get("estado") == "pendiente")]
        lista.append({"id": uuid.uuid4().hex[:8], "linea": l["id"], "nombre": l["ejercicio"],
                      "etiqueta": _etiqueta_parte(l.get("parte", "")) or "WOD", "texto": texto, "antes": antes,
                      "creado": dt.date.today().isoformat(), "fecha": fecha.isoformat(), "estado": "pendiente"})
        rut = dict(rut, retests=lista[-40:])
        aviso = f"🔁 Te lo vuelvo a poner el {_fecha_corta(fecha.isoformat())} para comparar"
    elif tipo in ("retest_poner", "retest_quitar", "retest_semana"):
        lista = [dict(x) for x in rut.get("retests") or []]
        x = next((y for y in lista if y["id"] == c.get("id")), None)
        if not x:
            raise Error("Ese retest ya no está")
        if tipo == "retest_poner":
            nota = f"\n🔁 Retest · la otra vez ({_fecha_corta(x.get('creado', ''))}): {x['antes']['valor']}" if x.get("antes") else \
                f"\n🔁 Retest de {_fecha_corta(x.get('creado', ''))}"
            rut = anadir_parte(rut, c["dia"], x.get("etiqueta") or "WOD", f"🔁 {x['nombre']}", x["texto"] + nota, semana, True)
            x["estado"] = "puesto"
            aviso = "🔁 Retest añadido a tu día. ¡A batir la marca!"
        elif tipo == "retest_semana":
            x["fecha"] = (dt.date.today() + dt.timedelta(days=7)).isoformat()
            aviso = "Vale, te lo recuerdo en una semana"
        else:
            x["estado"] = "quitado"
            aviso = "Retest quitado"
        rut = dict(rut, retests=lista)
    elif tipo == "descartar_novedad":
        rut = dict(rut, novedades_vistas=(rut.get("novedades_vistas") or [])[-60:] + [str(c.get("id"))])
        aviso = "Vale, no te la pongo"
    elif tipo == "aprobar_programa":
        if not es_coach(sesion):
            raise Error("Solo Diego puede aprobar el programa", 403)
        reg = dict(invitados())
        if atleta in reg:
            reg[atleta] = {**reg[atleta], "revision": "ok", "aprobado": dt.date.today().isoformat(), "aprobado_visto": False}
            datos().guardar(CLAVE_INVITADOS, reg)
        aviso = f"Programa de {nv(atleta)} aprobado ✅ Ya lo puede ver"
    elif tipo == "aprobado_visto":
        reg = dict(invitados())
        if atleta in reg:
            reg[atleta] = {**reg[atleta], "aprobado_visto": True}
            datos().guardar(CLAVE_INVITADOS, reg)
        aviso = None
    elif tipo in ("aceptar_sugerencia", "rechazar_sugerencia"):
        p = propuesta_para(atleta)
        if not p or not p.get("sugerir"):
            raise Error("No hay ninguna sugerencia de Diego")
        rut, _ = aplicar_propuesta(rut, atleta, descartar=tipo == "rechazar_sugerencia")
        if tipo == "aceptar_sugerencia":
            rut["propuesta_vista"] = p["id"]
            aviso = "¡Programa nuevo puesto! 💪"
            notificar(f"✅ {nv(atleta)} ha aceptado tu programa nuevo: {p['titulo']}")
        else:
            aviso = "Vale, sigues con tu programa de ahora"
            notificar(f"🙅 {nv(atleta)} prefiere seguir con su programa de ahora (no aceptó: {p['titulo']}). Escríbele por el chat si quieres.")
    elif tipo == "programa_visto":
        p = propuesta_para(atleta)
        rut = dict(rut, propuesta_vista=(p or {}).get("id"))
        aviso = None
    elif tipo in ("aplicar_propuesta", "descartar_propuesta"):
        if not es_coach(sesion):
            raise Error("Solo Diego puede cambiar la rutina", 403)
        rut, aviso = aplicar_propuesta(rut, atleta, descartar=tipo == "descartar_propuesta")
    elif tipo == "permiso_pesos":
        if not es_coach(sesion):
            raise Error("Solo el coach puede dar permiso", 403)
        rut = dict(rut, permiso_pesos=bool(c.get("valor")))
        aviso = f"{nv(atleta)} {'ya puede' if c.get('valor') else 'ya no puede'} cambiar sus pesos"
    elif tipo == "video":  # el coach pone (o quita) un vídeo de técnica a un ejercicio, para todos
        if not es_coach(sesion):
            raise Error("Solo el coach puede poner vídeos", 403)
        ej = norm(str(c.get("ejercicio") or ""))
        url = str(c.get("url") or "").strip()[:500]
        if not ej:
            raise Error("Falta el ejercicio")
        if url and not re.match(r"^https?://", url):
            raise Error("El enlace tiene que empezar por https://")
        reg = dict(datos().rutinas([CLAVE_VIDEOS]).get(CLAVE_VIDEOS) or {})
        if url:
            reg[ej] = {"url": url, "titulo": str(c.get("titulo") or c.get("ejercicio"))[:80]}
        else:
            reg[ej] = {"url": ""}  # quitado (también tapa el vídeo de serie)
        datos().guardar(CLAVE_VIDEOS, reg)
        aviso = "Vídeo guardado: lo verán todos en ese ejercicio" if url else "Vídeo quitado"
    elif tipo == "linea_hoy":  # el ejercicio que se quedó sin hacer, a hoy (solo esta semana)
        l = next((x for d in rut["dias"] for x in d["lineas"] if x["id"] == c.get("linea")), None)
        if not l:
            raise Error("No se encontró ese ejercicio")
        txt = prescripcion_semana(l, semana, rut.get("ajustes"))[0] or l.get("prescripcion", "")
        rut = anadir_parte(rut, c["dia"], _etiqueta_parte(l.get("parte", "")) or "Fuerza", l["ejercicio"], txt, semana, True)
        rut = marcar_linea(rut, l["id"], semana, False)
        aviso = f"{l['ejercicio']} añadido a hoy"
    elif tipo == "linea_no_hecha":
        rut = marcar_linea(rut, c["linea"], semana, bool(c.get("valor")))
    elif tipo == "semana":
        nueva = int(c.get("nueva") or 1)
        if nueva < 1:
            raise Error("Semana no válida")
        rut = dict(rut, semana_actual=nueva)
        aviso = f"Semana {nueva} es ahora la actual"
    elif tipo == "semana_lista":
        if not es_coach(sesion):
            raise Error("Solo el coach", 403)
        listas = {int(x) for x in rut.get("semanas_listas") or []}
        lista = c.get("lista") is not False
        listas = (listas | {semana}) if lista else (listas - {semana})
        rut = dict(rut, semanas_listas=sorted(listas))
        aviso = f"✅ Semana {semana} lista" if lista else f"Semana {semana} vuelve a pendiente"
    elif tipo == "nivel":
        if c.get("nivel") not in NIVELES:
            raise Error("Nivel no válido")
        rut = dict(rut, nivel=c["nivel"])
        aviso = f"Nivel {c['nivel']}"
    elif tipo == "fijar":
        l = next((x for d in rut["dias"] for x in d["lineas"] if x["id"] == c.get("linea")), None)
        if not l or not c.get("texto"):
            raise Error("No se encontró ese WOD")
        rut = editar_texto_linea(rut, l["id"], semana, l["ejercicio"], c["texto"], l.get("nota", ""), True)
        aviso = "WOD de Diego fijado"
    else:
        raise Error("Acción desconocida")
    rut, fin_semana = avanzar_si_completa(atleta, rut)
    datos().guardar(atleta, rut)
    if not es_coach(sesion) and not es_demo(sesion):
        _avisar_semana_sin_preparar(atleta, semana_antes, int(rut.get("semana_actual") or 1), rut)
    v = vista(sesion, atleta, int(c.get("ver_semana") or semana), c.get("ver_dia"))
    v["aviso"] = fin_semana or aviso
    return v


# ===== registrar un entreno =====
def _fmt_pr(valor: float, unidad: str) -> str:
    return fmt_valor(valor, unidad) if unidad == "tiempo" else f"{fmt_num(valor)} {unidad}"


def registrar(sesion: dict, c: dict) -> dict:
    """Guarda un entreno igual que formulario_entreno de app.py (tabla workouts + foto en el bucket «fotos»)."""
    import uuid
    atleta = c.get("atleta")
    puede_ver(sesion, atleta)
    exigir_pago(sesion, atleta)
    if atleta not in todas_las_personas():
        raise Error("Persona desconocida")
    tipo = c.get("tipo") if c.get("tipo") in TIPOS else "otro"
    try:
        fecha = dt.date.fromisoformat(str(c.get("fecha") or dt.date.today().isoformat())[:10])
    except ValueError:
        raise Error("La fecha no es válida")
    errores, resultados = [], []
    dur = None
    if str(c.get("duracion") or "").strip():
        dur = parse_tiempo(c["duracion"])
        if dur is None:
            errores.append("La duración no se entiende. Usa h:mm:ss, mm:ss o minutos.")
    for f in c.get("filas") or []:
        nombre = str(f.get("name") or "").strip()[:120]
        bruto = str(f.get("valor") or "").strip()
        unidad = f.get("unit") if f.get("unit") in UNIDADES else "tiempo"
        if not nombre and not bruto:
            continue
        valor = parse_valor(bruto, unidad) if bruto else None
        if bruto and valor is None:
            errores.append(f"Revisa «{nombre or bruto}»: los tiempos van como 4:35 y el resto como número.")
        resultados.append({"name": nombre or "Sin nombre", "value": valor, "unit": unidad})
    if errores:
        raise Error(" ".join(errores))
    if not resultados and not str(c.get("titulo") or "").strip() and not c.get("foto"):
        raise Error("Apunta al menos un resultado, un título o una foto.")
    w = {"id": str(uuid.uuid4()), "athlete": atleta, "date": fecha.isoformat(), "type": tipo,
         "title": str(c.get("titulo") or "").strip()[:200], "duration_sec": dur, "entries": resultados,
         "notes": str(c.get("notas") or "").strip()[:4000], "photo_path": None,
         "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}

    aviso_pr = None
    if atleta not in SIN_PRS:
        try:
            previos = datos().entrenos(atleta)
            guardados = (datos().rutinas([CLAVE_PRS]).get(CLAVE_PRS) or {}).get(atleta, [])
            antes = mejores_prs(guardados + prs_de_entrenos(previos))
            for r in prs_de_entrenos([w]):
                p = antes.get((r["movimiento"], 1 if r["unidad"] == "kg" else 0))
                mejor = p is not None and (r["valor"] < p["valor"] if r["unidad"] == "tiempo" else r["valor"] > p["valor"])
                if mejor:
                    aviso_pr = f"¡Nuevo PR en {r['movimiento']}: {_fmt_pr(r['valor'], r['unidad'])}!"
        except Error:
            pass

    if c.get("foto"):
        try:
            jpg = base64.b64decode(str(c["foto"]).split(",", 1)[-1])
        except ValueError:
            raise Error("La foto no se ha podido leer")
        if len(jpg) > 4_000_000:
            raise Error("La foto es demasiado grande")
        carpeta = norm(atleta).replace(" ", "-") or "sin-nombre"
        w["photo_path"] = datos().subir_foto(f"{carpeta}/{uuid.uuid4().hex}.jpg", jpg)
    datos().insertar_entreno(w)

    hechas = [p for p in c.get("partes") or [] if p.get("parte") and p.get("dia")]
    if hechas:
        rut = rutina(atleta)
        for p in hechas:
            rut = marcar_parte(rut, int(p.get("semana") or rut.get("semana_actual") or 1), p["dia"], p["parte"], "hecho")
        rut, fin_semana = avanzar_si_completa(atleta, rut)
        datos().guardar(atleta, rut)
    else:
        fin_semana = None
    if atleta != "Yo" and not es_demo(sesion):  # a Diego le llega por Telegram lo que registran sus alumnos
        try:  # ¿es una corrección de algo que acaba de registrar?
            previos = [x for x in datos().entrenos(atleta, 5) if x["id"] != w["id"] and x.get("title") == w["title"]
                       and str(x.get("date", ""))[:10] == w["date"]]
        except Exception:  # noqa: BLE001
            previos = []
        lineas = [f"{'✏️' if previos else '🏋️'} {nv(atleta)} {'corrige su registro' if previos else 'ha registrado'}"
                  + (f": {w['title']}" if w["title"] else "")]
        resumen = None
        if hechas:
            try:
                resumen = _resumen_dia_registro(rut, int(hechas[0].get("semana") or rut.get("semana_actual") or 1),
                                                hechas[0]["dia"], resultados, atleta)
            except Exception:  # noqa: BLE001
                resumen = None
        if resumen:
            lineas += resumen
        else:
            con_valor = [e for e in resultados if e.get("value") is not None]
            for e in con_valor[:8]:
                lineas.append(f"• {e['name']}: {fmt_valor(e['value'], e.get('unit', ''))}")
            sin = [e["name"] for e in resultados if e.get("value") is None]
            if sin:
                lineas.append(f"• Sin resultado: {', '.join(sin[:6])}")
        if w.get("notes"):
            lineas.append(f"💬 {w['notes'][:600]}")
        if aviso_pr:
            lineas.append(f"🎉 {aviso_pr}")
        if w.get("photo_path"):
            lineas.append(f"📸 {datos().url_foto(w['photo_path'])}")
        if fin_semana:
            lineas.append(f"✅ {fin_semana}")
        notificar("\n".join(lineas))
    v = vista(sesion, atleta, c.get("ver_semana"), c.get("ver_dia"))
    v["aviso"] = fin_semana or "Entreno guardado" + (f" · {len(hechas)} parte{'s' if len(hechas) != 1 else ''} hecha{'s' if len(hechas) != 1 else ''}" if hechas else "")
    if aviso_pr:
        v["pr"] = aviso_pr
    return v


def resolver_solicitud(sesion: dict, c: dict) -> dict:
    """El coach aprueba (aplica el cambio) o rechaza una solicitud de cambio de peso."""
    if not es_coach(sesion):
        raise Error("Solo el coach puede aprobar cambios", 403)
    reg = datos().rutinas([CLAVE_SOLICITUDES]).get(CLAVE_SOLICITUDES) or {}
    lista = reg.get("lista") or []
    sol = next((x for x in lista if x["id"] == c.get("id")), None)
    if not sol:  # p. ej. se aprobó pero se cortó la conexión antes de ver la respuesta
        v = vista(sesion, c.get("atleta"), c.get("ver_semana"), c.get("ver_dia"))
        v["aviso"] = "Esa solicitud ya estaba resuelta ✅"
        return v
    aviso = f"Rechazado el cambio de {sol['nombre']}"
    if c.get("aprobar") and sol.get("kind") in CAMBIOS_PROGRAMA:
        rut = rutina(sol["atleta"])
        if not rut:
            raise Error("Esa persona no tiene rutina")
        rut, _ = aplicar_programa(rut, sol["kind"], sol.get("datos") or {}, int(sol["semana"]), sol["atleta"])
        datos().guardar(sol["atleta"], rut)
        aviso = f"Aprobado el cambio de {sol['nombre']}"
    elif c.get("aprobar"):
        rut = rutina(sol["atleta"])
        if not rut:
            raise Error("Esa persona no tiene rutina")
        presc = poner_pesos(sol["texto"], sol["valores"])
        rut, _ = cambiar_pesos(rut, int(sol["semana"]), {sol["linea"]: presc}, sol["solo_semana"], sol["propagar"])
        datos().guardar(sol["atleta"], rut)
        aviso = f"Aprobado: {sol['ejercicio']} de {sol['nombre']}"
    datos().guardar(CLAVE_SOLICITUDES, {"lista": [x for x in lista if x["id"] != sol["id"]]})
    v = vista(sesion, c.get("atleta"), c.get("ver_semana"), c.get("ver_dia"))
    v["aviso"] = aviso
    return v


# ===== historial, progreso y PRs =====
DIAS_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
COLOR_TIPO = {"wod": "#2a78d6", "fuerza": "#eb6834", "endurance": "#1baf7a", "gym": "#eda100", "otro": "#e87ba4"}
ORDEN_TIPO = ["wod", "fuerza", "endurance", "gym", "otro"]


def _fecha_txt(d) -> str:
    d = a_fecha(d)
    return f"{DIAS_ES[d.weekday()]} {d.day} {MESES_ES[d.month - 1]} {d.year}"


def _entrenos_de(sesion: dict, atleta: str) -> list[dict]:
    puede_ver(sesion, atleta)
    if atleta not in todas_las_personas():
        raise Error("Persona desconocida")
    return datos().entrenos(atleta)


def historial(sesion: dict, atleta: str) -> dict:
    ws = _entrenos_de(sesion, atleta)
    prs = ids_con_pr(ws)
    out = []
    for w in ws:
        out.append({"id": w["id"], "fecha": str(w["date"])[:10], "fecha_txt": _fecha_txt(w["date"]), "tipo": w["type"],
                    "tipo_txt": TIPOS.get(w["type"], TIPOS["otro"])[0], "titulo": w.get("title") or "",
                    "duracion": fmt_tiempo(w["duration_sec"]) if w.get("duration_sec") else "",
                    "notas": w.get("notes") or "",
                    "foto": datos().url_foto(w["photo_path"]) if w.get("photo_path") else "",
                    "resultados": [{"nombre": e.get("name", ""), "valor": fmt_valor(e.get("value"), e.get("unit", "")),
                                    "pr": (w["id"], norm(e.get("name", "")) + "|" + e.get("unit", "")) in prs}
                                   for e in w.get("entries") or []]})
    return {"atleta": atleta, "nombre": nombre_demo(atleta) if es_demo(sesion) else nv(atleta), "entrenos": out,
            "tipos": {k: TIPOS[k][0] for k in ORDEN_TIPO}, "colores": COLOR_TIPO}


def borrar_entreno(sesion: dict, c: dict) -> dict:
    atleta = c.get("atleta")
    ws = _entrenos_de(sesion, atleta)
    w = next((x for x in ws if str(x["id"]) == str(c.get("id"))), None)
    if not w:
        raise Error("Ese entreno ya no está")
    datos().borrar_entreno(w)
    h = historial(sesion, atleta)
    h["aviso"] = "Entreno borrado"
    return h


def _semanas_seguidas(ws: list[dict]) -> int:
    from logica import inicio_semana
    semanas = {inicio_semana(w["date"]) for w in ws}
    n, lunes = 0, inicio_semana(dt.date.today())
    if lunes not in semanas:  # esta semana aún puede no tener entreno: se cuenta desde la anterior
        lunes -= dt.timedelta(weeks=1)
    while lunes in semanas:
        n += 1
        lunes -= dt.timedelta(weeks=1)
    return n


def _pct_partes(atleta: str) -> int | None:
    """% de partes hechas en las 4 últimas semanas de la rutina (hasta la actual)."""
    rut = rutina(atleta)
    if not rut or not rut.get("dias"):
        return None
    actual = int(rut.get("semana_actual") or 1)
    total = hechas = 0
    for sem in range(max(1, actual - 3), actual + 1):
        for d in rut["dias"]:
            for p_, ls in agrupar_por_parte(d, sem):
                e = estado_parte(rut, sem, d["id"], p_)["estado"]
                if sem == actual and e == "pendiente":
                    continue  # lo que aún no toca no cuenta
                total += 1
                hechas += e == "hecho"
    return round(hechas / total * 100) if total else None


def progreso(sesion: dict, atleta: str) -> dict:
    ws = _entrenos_de(sesion, atleta)
    hoy = dt.date.today()
    series = []
    for s_ in series_ejercicios(ws)[:60]:
        best, ult, pct = mejor_punto(s_), s_["pts"][-1], cambio_pct(s_)
        series.append({"key": s_["key"], "nombre": s_["name"], "unidad": s_["unit"], "n": len(s_["pts"]),
                       "mejor": {"txt": fmt_valor(best["v"], s_["unit"]), "fecha": best["date"].isoformat()},
                       "ultima": {"txt": fmt_valor(ult["v"], s_["unit"]), "fecha": ult["date"].isoformat()},
                       "pct": None if pct is None else round(pct, 1),
                       "pts": [{"f": p_["date"].isoformat(), "v": p_["v"], "txt": fmt_valor(p_["v"], s_["unit"])}
                               for p_ in s_["pts"]]})
    lunes, cuentas = sesiones_por_semana(ws, 8)
    return {"atleta": atleta, "nombre": nombre_demo(atleta) if es_demo(sesion) else nv(atleta),
            "kpis": {"mes": sum(1 for w in ws if (hoy - a_fecha(w["date"])).days < 30),
                     "partes": _pct_partes(atleta), "seguidas": _semanas_seguidas(ws), "total": len(ws)},
            "consejos": [{"nivel": c_["nivel"], "titulo": c_["titulo"], "detalle": c_["detalle"]} for c_ in consejos(ws)],
            "series": series,
            "semanas": {"lunes": [f"{l.day}/{l.month}" for l in lunes],
                        "tipos": [{"tipo": k, "nombre": TIPOS[k][0], "color": COLOR_TIPO[k], "n": cuentas.get(k, [0] * len(lunes))}
                                  for k in ORDEN_TIPO if k in cuentas]}}


def _prs_guardados() -> dict:
    return datos().rutinas([CLAVE_PRS]).get(CLAVE_PRS) or {}


def prs(sesion: dict, atleta: str) -> dict:
    ws = _entrenos_de(sesion, atleta)
    if atleta in SIN_PRS:
        return {"atleta": atleta, "sin_prs": True}
    todos = _prs_guardados().get(atleta, []) + prs_de_entrenos(ws)
    mejores = mejores_prs(todos)
    hace_30 = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    cats = []
    for cat in CATALOGO_PR:
        filas = [(k, r) for k, r in mejores.items() if r.get("categoria") == cat
                 or (r.get("categoria") is None and movimiento_pr(k[0]) and movimiento_pr(k[0])[0] == cat)]
        if not filas:
            continue
        orden = [m for m, _ in CATALOGO_PR[cat]]
        filas.sort(key=lambda x: (orden.index(x[0][0]) if x[0][0] in orden else 99, x[0][1]))
        hist = [r for r in todos if r.get("categoria") == cat or (movimiento_pr(r["movimiento"]) or ("",))[0] == cat]
        cats.append({"cat": cat, "filas": [{
            "mov": mov, "reps": reps if r["unidad"] == "kg" else None, "valor": _fmt_pr(r["valor"], r["unidad"]),
            "fecha": _fecha_txt(r["fecha"]), "nuevo": str(r["fecha"]) >= hace_30, "registro": r.get("origen") == "registro",
            "nota": r.get("nota") or "",
            "evol": [{"f": str(x["fecha"])[:10], "v": x["valor"], "txt": _fmt_pr(x["valor"], x["unidad"])}
                     for x in sorted(hist, key=lambda x: str(x["fecha"])) if x["movimiento"] == mov
                     and (x["unidad"] != "kg" or int(x.get("reps") or 1) == (reps or 1))],
            "unidad": r["unidad"]} for (mov, reps), r in filas]})
    ultimo = max(mejores.values(), key=lambda r: str(r["fecha"]), default=None)
    return {"atleta": atleta, "nombre": nombre_demo(atleta) if es_demo(sesion) else nv(atleta), "categorias": cats,
            "ultimo": {"mov": ultimo["movimiento"], "valor": _fmt_pr(ultimo["valor"], ultimo["unidad"]),
                       "fecha": _fecha_txt(ultimo["fecha"]), "reps": ultimo.get("reps") if ultimo["unidad"] == "kg" else None}
            if ultimo else None,
            "catalogo": {cat: [{"mov": m, "unidad": u} for m, u in movs] for cat, movs in CATALOGO_PR.items()}}


def guardar_pr(sesion: dict, c: dict) -> dict:
    atleta = c.get("atleta")
    ws = _entrenos_de(sesion, atleta)
    if atleta in SIN_PRS:
        raise Error("Este perfil no tiene PRs")
    cat = c.get("cat") if c.get("cat") in CATALOGO_PR else None
    if not cat:
        raise Error("Elige el tipo")
    nombre = str(c.get("mov") or "").strip()[:80]
    unidad = dict(CATALOGO_PR[cat]).get(nombre) or ("kg" if "Halter" in cat or "Fuerza" in cat else
                                                    "tiempo" if "Carrera" in cat else "reps")
    valor = parse_tiempo(c.get("valor")) if unidad == "tiempo" else parse_valor(c.get("valor"), "kg")
    if not valor or not nombre:
        raise Error("Pon el movimiento y la marca (los tiempos como 21:30).")
    reps = max(1, min(20, int(c.get("reps") or 1))) if unidad == "kg" else 1
    try:
        fecha = dt.date.fromisoformat(str(c.get("fecha") or dt.date.today().isoformat())[:10])
    except ValueError:
        raise Error("La fecha no es válida")
    todos = _prs_guardados()
    previo = mejores_prs(todos.get(atleta, []) + prs_de_entrenos(ws)).get((nombre, reps if unidad == "kg" else 0))
    mejora = previo is None or (valor < previo["valor"] if unidad == "tiempo" else valor > previo["valor"])
    todos = dict(todos)
    todos[atleta] = todos.get(atleta, []) + [{"categoria": cat, "movimiento": nombre, "unidad": unidad, "valor": float(valor),
                                              "reps": reps, "fecha": fecha.isoformat(),
                                              "nota": str(c.get("nota") or "").strip()[:200], "origen": "manual"}]
    datos().guardar(CLAVE_PRS, todos)
    r = prs(sesion, atleta)
    r["aviso"] = "¡Nuevo PR!" if mejora and previo is not None else ("PR apuntado" if mejora else "Marca guardada (no supera tu PR)")
    r["pr"] = mejora and previo is not None
    return r
