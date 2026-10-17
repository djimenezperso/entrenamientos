"""Djimenez Prog — servidor de la app nueva.

Usa la MISMA lógica (logica.py, rutinas_iniciales.py…) y los MISMOS datos de Supabase que la app de Streamlit,
así que las dos funcionan a la vez sobre lo mismo. Sin dependencias: solo la librería estándar de Python.

Variables de entorno (en Vercel → Settings → Environment Variables):
  SUPABASE_URL, SUPABASE_KEY      la misma url y clave sb_secret_… que en los secrets de Streamlit
  APP_PASSWORD                    contraseña general (ve a todos)
  CONTRASENA_ARCHCHANA            contraseña solo de Archchana
  CONTRASENA_INVITADOS            contraseña para invitados (nombre + PIN)
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
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from logica import (
    NIVELES, NUM_PESO, _etiqueta_parte, agrupar_por_parte, cambiar_pesos, copiar_rutina, destino_dia_siguiente,
    destino_semana_siguiente, editar_texto_linea, es_metcon, escalar, estado_parte, fmt_num, historial_parte,
    letra_visible, linea_activa, linea_no_hecha, marcar_linea, marcar_parte, no_hechas_en, norm, norm_busqueda,
    parametros_semana, partes_del_dia, pendientes_para, poner_pesos, prescripcion_semana, referencias_elite,
    resumen_dia, se_repite, semanas_que_sube, sin_validar, tipo_de_linea, versiones_por_movimiento,
    TIPOS, UNIDADES, duracion_emom, formato_de, mejores_prs, parse_tiempo, parse_valor, peso_principal, fmt_valor,
    prs_de_entrenos, series_ejercicios, mejor_punto, cambio_pct, ids_con_pr, consejos, sesiones_por_semana,
    CATALOGO_PR, movimiento_pr, fmt_tiempo, a_fecha, anadir_parte, sustituir_parte, deshacer_sustitucion, CLAVE_BIBLIOTECA, CLAVES_BIBLIO,
)
from repertorio import ELITE, REPERTORIO
from rutinas_iniciales import migrar, rutinas_iniciales

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


def rutina(atleta: str, guardadas: dict | None = None) -> dict | None:
    guardadas = datos().rutinas([atleta]) if guardadas is None else guardadas
    return completar(guardadas.get(atleta) or rutinas_iniciales(ATLETAS).get(atleta), atleta)


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


def _sesion_para(solo: str | None, coach: bool = False) -> dict:
    datos_s = {"u": solo or "", "exp": int(time.time()) + 120 * 86400}
    if coach:
        datos_s["c"] = 1
    return {"token": firmar(datos_s), "solo": solo, "lang": IDIOMA_DEFECTO.get(solo or "", "es"), "coach": coach}


def es_coach(sesion: dict) -> bool:
    return bool(sesion.get("c")) and bool(env("COACH_PIN"))


def modo_coach(sesion: dict, c: dict) -> dict:
    """Activa (con el PIN del coach) o quita el modo coach. Devuelve una sesión nueva."""
    if c.get("salir"):
        return _sesion_para(sesion.get("u") or None, False)
    pin = env("COACH_PIN")
    if not pin:
        raise Error("Falta COACH_PIN en las variables de Vercel", 500)
    if not _igual(str(c.get("pin") or ""), pin):
        time.sleep(0.8)  # frena a quien pruebe PINs al azar
        raise Error("PIN incorrecto", 403)
    return _sesion_para(sesion.get("u") or None, True)


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


VERSION = "3.0"
CLAVES_NECESARIAS = ["SUPABASE_URL", "SUPABASE_KEY", "APP_PASSWORD", "CONTRASENA_ARCHCHANA", "CONTRASENA_INVITADOS", "COACH_PIN",
                     "APP_ANTIGUA_URL"]


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
    if _igual(intento, general):
        return _sesion_para(None)
    for nombre, clave in personales.items():
        if _igual(intento, clave):
            return _sesion_para(nombre)
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
    registro[nombre] = {"pin": _hash(nombre, pin), "alta": dt.date.today().isoformat(), "plantilla": plantilla}
    datos().guardar(CLAVE_INVITADOS, registro)
    base = rutina(plantilla)
    if base:
        import uuid
        nueva = copiar_rutina(base, lambda: uuid.uuid4().hex[:8])
        nueva["nivel"] = base.get("nivel") or "Inter"
        datos().guardar(nombre, nueva)
    return _sesion_para(nombre)


def puede_ver(sesion: dict, atleta: str) -> None:
    if sesion.get("u") and sesion["u"] != atleta:
        raise Error("No tienes acceso a esa persona", 403)


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


def es_movilidad(parte: str, lineas: list[dict]) -> bool:
    return tipo_de_linea(parte, "") == "mobility" or any(tipo_de_linea(parte, l["ejercicio"]) == "mobility" for l in lineas)


def movilidad_primero(grupos: list[tuple[str, list[dict]]]) -> list[tuple[str, list[dict]]]:
    """La movilidad, si la hay, siempre al principio del día (las letras se ponen luego por posición)."""
    return [g for g in grupos if es_movilidad(*g)] + [g for g in grupos if not es_movilidad(*g)]


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
    tipo = _tipo_ui(parte, l["ejercicio"])
    out = {"id": l["id"], "ejercicio": l["ejercicio"], "nota": l.get("nota") or "", "texto": txt,
           "extra": _etiqueta_extra(l, txt, semana, ajuste, subio), "tipo": tipo,
           "ciclo": l.get("plan") is not None,
           "texto_sig": prescripcion_semana(l, semana + 1, rut.get("ajustes"))[0]}
    if tipo_de_linea(parte, l["ejercicio"]) is None and l.get("plan") is None:  # fuerza: pesos que se tocan
        pesos = [float(x.replace(",", ".")) for x in NUM_PESO.findall(txt)]
        out.update(kind="peso", pesos=pesos, esquema=NUM_PESO.sub("", txt).replace("  ", " ").strip(" -"))
        if por_ejercicio:
            out["no_hecha"] = linea_no_hecha(l, semana)
        return out
    out["kind"] = "texto"
    if not txt and sug:
        txt = sug["texto"]
        out["sugerencia"] = {"semana": sug["semana"], "dia": sug["dia"], "texto": sug["texto"]}
    escalable = norm_busqueda(_etiqueta_parte(parte)) != "gym"
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


def vista(sesion: dict, atleta: str | None, semana: int | None, dia_id: str | None) -> dict:
    inv = invitados()
    personas = [sesion["u"]] if sesion.get("u") else todas_las_personas(inv)
    atleta = atleta if atleta in personas else personas[0]
    puede_ver(sesion, atleta)
    alumno = es_alumno(atleta, inv)
    guardadas = datos().rutinas(list({atleta, "Yo", CLAVE_SOLICITUDES, CLAVE_NOVEDADES}))
    rut = rutina(atleta, guardadas)
    coach = es_coach(sesion)
    todas_sol = (guardadas.get(CLAVE_SOLICITUDES) or {}).get("lista") or []
    base = {"atleta": atleta, "nombre": nv(atleta), "solo": sesion.get("u") or None,
            "personas": [{"id": p, "nombre": nv(p)} for p in personas], "lang": IDIOMA_DEFECTO.get(atleta, "es"),
            "app_antigua": env("APP_ANTIGUA_URL"), "tipos": {k: v[0] for k, v in TIPOS.items()},
            "unidades": UNIDADES, "con_prs": atleta not in SIN_PRS, "coach": coach,
            "puede_pesos": coach or bool((rut or {}).get("permiso_pesos")),
            "permiso_pesos": bool((rut or {}).get("permiso_pesos")),
            "solicitudes": [x for x in todas_sol if coach and (not sesion.get("u") or x["atleta"] == sesion["u"])],
            "mis_solicitudes": {x["linea"]: x for x in todas_sol if x["atleta"] == atleta}}
    if not rut or not rut.get("dias"):
        return {**base, "sin_rutina": True}
    actual = int(rut.get("semana_actual") or 1)
    semana = int(semana or actual)
    nivel = rut.get("nivel") or NIVEL_DEFECTO.get(atleta, "Inter")
    sugs = sugerencias(rut, semana, wods_de_diego(rutina("Yo", guardadas))) if alumno else {}

    dias = []
    for d in rut["dias"]:
        dias.append({"id": d["id"], "nombre": d["nombre"], "estado": resumen_dia(rut, semana, d),
                     "pendientes": bool(pendientes_para(rut, semana, d["id"]))})
    ids = [d["id"] for d in rut["dias"]]
    por_hacer = ids[0]
    if atleta in ABRE_DIA_PENDIENTE:
        por_hacer = next((d["id"] for d in dias if d["estado"] != "hecho" or d["pendientes"]), ids[0])
    dia_id = dia_id if dia_id in ids else por_hacer
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
    return {**base, "semana": semana, "actual": actual, "nivel": nivel, "niveles": NIVELES, "alumno": alumno,
            "dias": dias, "dia": {"id": dia["id"], "nombre": dia["nombre"], "estado": resumen_dia(rut, semana, dia),
                                  "por_ejercicio": bool(dia.get("por_ejercicio"))},
            "partes": partes, "pendientes": pendientes,
            "novedades": novedades_para(rut, (guardadas.get(CLAVE_NOVEDADES) or {}).get("lista") or []) if alumno else [],
            "registro": {**registro_inicial(rut, dia, semana),
                         "partes": [{"parte": p["parte"], "texto": f"{p['letra']} · {p['etiqueta']}".strip(" ·"),
                                     "warmup": bool(p.get("calentamiento")), "semana": semana, "dia": dia["id"]}
                                    for p in partes]},
            "faltan": sin_validar(rut, semana) if semana <= actual else []}


# ===== biblioteca y novedades =====
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


def ideas() -> dict:
    """Ideas para rellenar una parte: el repertorio + lo ya guardado en la biblioteca."""
    bib = datos().rutinas([CLAVE_BIBLIOTECA]).get(CLAVE_BIBLIOTECA) or {}
    def de_bib(clave):
        return [{"nombre": i.get("nombre") or "", "texto": i.get("texto", "")} for i in reversed(bib.get(clave) or [])][:25]
    rep = lambda k: [{"nombre": n, "texto": t} for n, t in REPERTORIO.get(k, [])]
    return {"volumen": [{"nombre": n, "texto": t} for n, t in VOLUMEN],
            "wod": de_bib("wods") + rep("wod"), "conditioning": de_bib("conditionings") + rep("conditioning"),
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


def _novedad(rut_yo: dict, etiqueta: str, nombre: str, texto: str, semana: int):
    """Lo que Diego se pone a sí mismo, para ofrecérselo a sus alumnos."""
    import uuid
    if not (texto or "").strip():
        return
    reg = datos().rutinas([CLAVE_NOVEDADES]).get(CLAVE_NOVEDADES) or {}
    lista = [x for x in reg.get("lista") or [] if norm_busqueda(x.get("texto", "")) != norm_busqueda(texto)]
    lista.append({"id": uuid.uuid4().hex[:10], "etiqueta": etiqueta, "nombre": nombre or etiqueta, "texto": texto.strip(),
                  "semana": semana, "fecha": dt.date.today().isoformat()})
    datos().guardar(CLAVE_NOVEDADES, {"lista": lista[-30:]})


def novedades_para(rut: dict, novedades: list[dict]) -> list[dict]:
    vistas = set(rut.get("novedades_vistas") or [])
    hace = (dt.date.today() - dt.timedelta(days=21)).isoformat()
    return [x for x in reversed(novedades) if x["id"] not in vistas and x.get("fecha", "") >= hace][:3]


def puede_programar(sesion: dict, rut: dict) -> bool:
    return es_coach(sesion) or bool(rut.get("permiso_pesos"))


CAMBIOS_PROGRAMA = ("editar_texto", "cambiar_parte", "anadir_parte", "deshacer_parte")


def aplicar_programa(rut: dict, tipo: str, c: dict, semana: int, atleta: str) -> tuple[dict, str]:
    """Cambios en lo programado (texto de un WOD, cambiar/añadir/volver una parte). Devuelve (rutina, aviso)."""
    texto = str(c.get("texto") or "").strip()[:3000]
    solo = bool(c.get("solo_esta"))
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
        _novedad(rut, etiqueta, nombre, texto, semana)
    return rut, aviso


def _resumen_cambio(tipo: str, c: dict, rut: dict) -> str:
    if tipo == "editar_texto":
        l = next((x for d in rut["dias"] for x in d["lineas"] if x["id"] == c.get("linea")), {})
        return f"{l.get('ejercicio', 'WOD')}: {c.get('texto', '')}"
    if tipo == "deshacer_parte":
        return f"Volver a lo que había en {c.get('parte', '')}"
    return f"{'Cambiar' if tipo == 'cambiar_parte' else 'Añadir'} {c.get('etiqueta', '')}: {c.get('texto', '')}"


# ===== acciones =====
def accion(sesion: dict, c: dict) -> dict:
    atleta = c.get("atleta")
    puede_ver(sesion, atleta)
    if atleta not in todas_las_personas():
        raise Error("Persona desconocida")
    rut = rutina(atleta)
    if not rut:
        raise Error("Esa persona no tiene rutina")
    tipo = c.get("tipo")
    semana = int(c.get("semana") or rut.get("semana_actual") or 1)
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
        v["aviso"] = f"Enviado a {nv('Yo')}: te avisará cuando lo apruebe"
        return v
    elif tipo in CAMBIOS_PROGRAMA:
        if not puede_programar(sesion, rut):
            import uuid
            reg = datos().rutinas([CLAVE_SOLICITUDES]).get(CLAVE_SOLICITUDES) or {}
            lista = reg.get("lista") or []
            datos_c = {k: c.get(k) for k in ("linea", "texto", "texto_sig", "nombre", "solo_esta", "dia", "parte", "etiqueta")}
            lista.append({"id": uuid.uuid4().hex[:10], "atleta": atleta, "nombre": nv(atleta), "kind": tipo,
                          "linea": c.get("linea") or f"{c.get('dia')}|{c.get('parte')}", "semana": semana,
                          "datos": datos_c, "resumen": _resumen_cambio(tipo, c, rut)[:400], "antes": [], "valores": [],
                          "mensaje": str(c.get("mensaje") or "")[:500], "fecha": dt.datetime.now(dt.timezone.utc).isoformat()})
            datos().guardar(CLAVE_SOLICITUDES, {"lista": lista[-200:]})
            v = vista(sesion, atleta, int(c.get("ver_semana") or semana), c.get("ver_dia"))
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
    elif tipo == "descartar_novedad":
        rut = dict(rut, novedades_vistas=(rut.get("novedades_vistas") or [])[-60:] + [str(c.get("id"))])
        aviso = "Vale, no te la pongo"
    elif tipo == "permiso_pesos":
        if not es_coach(sesion):
            raise Error("Solo el coach puede dar permiso", 403)
        rut = dict(rut, permiso_pesos=bool(c.get("valor")))
        aviso = f"{nv(atleta)} {'ya puede' if c.get('valor') else 'ya no puede'} cambiar sus pesos"
    elif tipo == "linea_no_hecha":
        rut = marcar_linea(rut, c["linea"], semana, bool(c.get("valor")))
    elif tipo == "semana":
        nueva = int(c.get("nueva") or 1)
        if nueva < 1:
            raise Error("Semana no válida")
        rut = dict(rut, semana_actual=nueva)
        aviso = f"Semana {nueva} es ahora la actual"
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
    datos().guardar(atleta, rut)
    v = vista(sesion, atleta, int(c.get("ver_semana") or semana), c.get("ver_dia"))
    v["aviso"] = aviso
    return v


# ===== registrar un entreno =====
def _fmt_pr(valor: float, unidad: str) -> str:
    return fmt_valor(valor, unidad) if unidad == "tiempo" else f"{fmt_num(valor)} {unidad}"


def registrar(sesion: dict, c: dict) -> dict:
    """Guarda un entreno igual que formulario_entreno de app.py (tabla workouts + foto en el bucket «fotos»)."""
    import uuid
    atleta = c.get("atleta")
    puede_ver(sesion, atleta)
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
        datos().guardar(atleta, rut)
    v = vista(sesion, atleta, c.get("ver_semana"), c.get("ver_dia"))
    v["aviso"] = "Entreno guardado" + (f" · {len(hechas)} parte{'s' if len(hechas) != 1 else ''} hecha{'s' if len(hechas) != 1 else ''}" if hechas else "")
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
    if not sol:
        raise Error("Esa solicitud ya no existe")
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
    return {"atleta": atleta, "nombre": nv(atleta), "entrenos": out,
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
    return {"atleta": atleta, "nombre": nv(atleta),
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
    return {"atleta": atleta, "nombre": nv(atleta), "categorias": cats,
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
