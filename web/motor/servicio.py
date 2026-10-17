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
)
from repertorio import ELITE
from rutinas_iniciales import migrar, rutinas_iniciales

# ===== personas (igual que en app.py) =====
ATLETAS = ["Yo", "Manu Anel", "Salatti", "Mi esposa", "Dario", "Archchana", "Juan"]
ORDEN_VISTA = ["Yo", "Mi esposa", "Manu Anel", "Salatti", "Dario", "Archchana", "Juan"]
NOMBRE_VISIBLE = {"Yo": "Diego"}
IDIOMA_DEFECTO = {"Archchana": "fr"}
NIVEL_DEFECTO = {"Yo": "RX"}
ALUMNOS = ["Salatti", "Dario", "Juan", "Mi esposa", "Manu Anel"]
ABRE_DIA_PENDIENTE = ("Yo", "Mi esposa")
PROTEGIDOS = ["Yo", "Diego", "Manu Anel", "Salatti", "Mi esposa", "Dario", "Juan", "Archchana"]
CLAVE_INVITADOS = "__invitados__"
PLANTILLAS = {"Salatti": "Rutina de Salatti", "Dario": "Rutina de Dario"}
TIPOS_WOD = ("wod", "emom", "fortime", "amrap")


class Error(Exception):
    def __init__(self, mensaje: str, codigo: int = 400):
        super().__init__(mensaje)
        self.codigo = codigo


def env(nombre: str, defecto: str = "") -> str:
    return (os.environ.get(nombre) or defecto).strip()


def nv(atleta: str) -> str:
    return NOMBRE_VISIBLE.get(atleta, atleta)


# ===== datos =====
class Supabase:
    """La tabla `rutinas` (athlete, data) por la API REST de Supabase."""

    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _pedir(self, metodo: str, ruta: str, cuerpo=None, extra: dict | None = None):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode() if cuerpo is not None else None
        req = urllib.request.Request(self.base + ruta, data=datos, method=metodo, headers={**self.h, **(extra or {})})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                txt = r.read().decode() or "null"
                return json.loads(txt)
        except urllib.error.HTTPError as e:
            raise Error(f"Supabase {e.code}: {e.read().decode()[:300]}", 502)

    def rutinas(self, nombres: list[str]) -> dict:
        lista = ",".join('"' + n.replace('"', '') + '"' for n in nombres)
        filas = self._pedir("GET", "/rutinas?select=athlete,data&athlete=in.(" + urllib.parse.quote(lista) + ")")
        return {f["athlete"]: f["data"] for f in filas or []}

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


def _sesion_para(solo: str | None) -> dict:
    return {"token": firmar({"u": solo or "", "exp": int(time.time()) + 120 * 86400}),
            "solo": solo, "lang": IDIOMA_DEFECTO.get(solo or "", "es")}


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
    if hmac.compare_digest(intento, general):
        return _sesion_para(None)
    for nombre, clave in personales.items():
        if clave and hmac.compare_digest(intento, clave):
            return _sesion_para(nombre)
    inv_clave = env("CONTRASENA_INVITADOS")
    if inv_clave and hmac.compare_digest(intento, inv_clave):
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


def _linea(rut: dict, l: dict, semana: int, parte: str, nivel: str, alumno: bool, sug: dict | None,
           por_ejercicio: bool) -> dict:
    txt, subio, ajuste = prescripcion_semana(l, semana, rut.get("ajustes"))
    tipo = _tipo_ui(parte, l["ejercicio"])
    out = {"id": l["id"], "ejercicio": l["ejercicio"], "nota": l.get("nota") or "", "texto": txt,
           "extra": _etiqueta_extra(l, txt, semana, ajuste, subio), "tipo": tipo,
           "ciclo": l.get("plan") is not None}
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
    }


def vista(sesion: dict, atleta: str | None, semana: int | None, dia_id: str | None) -> dict:
    inv = invitados()
    personas = [sesion["u"]] if sesion.get("u") else todas_las_personas(inv)
    atleta = atleta if atleta in personas else personas[0]
    puede_ver(sesion, atleta)
    alumno = es_alumno(atleta, inv)
    guardadas = datos().rutinas(list({atleta, "Yo"}))
    rut = rutina(atleta, guardadas)
    base = {"atleta": atleta, "nombre": nv(atleta), "solo": sesion.get("u") or None,
            "personas": [{"id": p, "nombre": nv(p)} for p in personas], "lang": IDIOMA_DEFECTO.get(atleta, "es"),
            "app_antigua": env("APP_ANTIGUA_URL")}
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
    grupos = agrupar_por_parte(dia, semana)
    partes_semana = [p for p, _ in grupos]
    partes = [_parte(rut, dia, p, ls, semana, partes_semana, nivel, alumno, sugs) for p, ls in grupos]
    pendientes = []
    nombres = {d["id"]: d for d in rut["dias"]}
    for so, did, parte in pendientes_para(rut, semana, dia["id"]):
        origen = nombres[did]
        grupos_o = agrupar_por_parte(origen)
        lineas = next((ls for p, ls in grupos_o if p == parte), [])
        p = _parte(rut, origen, parte, lineas, so, [x for x, _ in agrupar_por_parte(origen, so)], nivel, alumno,
                   {}, desde=(semana, dia["id"]))
        p["origen"] = f"{origen['nombre']} · semana {so}"
        pendientes.append(p)
    return {**base, "semana": semana, "actual": actual, "nivel": nivel, "niveles": NIVELES, "alumno": alumno,
            "dias": dias, "dia": {"id": dia["id"], "nombre": dia["nombre"], "estado": resumen_dia(rut, semana, dia),
                                  "por_ejercicio": bool(dia.get("por_ejercicio"))},
            "partes": partes, "pendientes": pendientes,
            "faltan": sin_validar(rut, semana) if semana <= actual else []}


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
        valores = [float(v) for v in c.get("valores") or []]
        if not valores or any(v < 0 or v > 1000 for v in valores):
            raise Error("Peso no válido")
        nueva_presc = poner_pesos(c.get("texto") or "", valores)
        rut, tocados = cambiar_pesos(rut, semana, {c["linea"]: nueva_presc}, bool(c.get("solo_semana")),
                                     c.get("propagar", True) is not False)
        aviso = "Peso guardado" + (f" (también en {', '.join(tocados)})" if tocados else "")
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
