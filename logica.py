"""Lógica sin Streamlit: tiempos, marcas, series de progresión y consejos."""
from __future__ import annotations

import datetime as dt
import re

TIPOS = {
    "fuerza": ("Fuerza", "#d6312b", "red"),
    "wod": ("WOD", "#1f5fbf", "blue"),
    "gym": ("Gym", "#d9a200", "orange"),
    "endurance": ("Endurance", "#2a8c4a", "green"),
    "otro": ("Otro", "#7f8994", "gray"),
}
UNIDADES = ["tiempo", "kg", "reps", "km", "m", "cal", "rondas"]
MENOS_ES_MEJOR = {"tiempo"}


# ---------- tiempos y valores ----------
def parse_tiempo(txt) -> int | None:
    """'4:35' -> 275, '1:02:10' -> 3730, '45' (minutos) -> 2700."""
    t = str(txt or "").strip().replace(",", ".")
    if not t:
        return None
    if ":" in t:
        try:
            partes = [float(p) for p in t.split(":")]
        except ValueError:
            return None
        total = 0.0
        for p in partes:
            total = total * 60 + p
        return int(round(total))
    try:
        return int(round(float(t) * 60))
    except ValueError:
        return None


def fmt_tiempo(seg) -> str:
    if seg is None:
        return ""
    seg = int(round(float(seg)))
    h, m, s = seg // 3600, seg % 3600 // 60, seg % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_valor(txt, unidad: str):
    if unidad == "tiempo":
        return parse_tiempo(txt)
    t = str(txt or "").strip().replace(",", ".")
    t = re.sub(r"[a-zA-Z\s]+$", "", t)  # admite "100kg" o "12 reps"
    try:
        return float(t)
    except ValueError:
        return None


def fmt_valor(v, unidad: str) -> str:
    if v is None:
        return "—"
    if unidad == "tiempo":
        return fmt_tiempo(v)
    v = float(v)
    num = str(int(v)) if v.is_integer() else f"{v:.1f}".replace(".", ",")
    return f"{num} {unidad}"


def mejor(a, b, unidad: str) -> bool:
    """¿a es mejor que b?"""
    return a < b if unidad in MENOS_ES_MEJOR else a > b


def norm(nombre: str) -> str:
    return re.sub(r"\s+", " ", str(nombre or "").strip().lower())


def a_fecha(d) -> dt.date:
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, dt.date):
        return d
    return dt.date.fromisoformat(str(d)[:10])


# ---------- series ----------
def series_ejercicios(entrenos: list[dict]) -> list[dict]:
    """Agrupa resultados por ejercicio+unidad. Un punto por fecha (el mejor del día)."""
    mapa: dict[str, dict] = {}
    for w in entrenos:
        for e in w.get("entries") or []:
            if not e.get("name") or e.get("value") is None:
                continue
            k = norm(e["name"]) + "|" + e["unit"]
            s = mapa.setdefault(k, {"key": k, "name": e["name"].strip(), "unit": e["unit"], "por_fecha": {}})
            f = a_fecha(w["date"])
            v = e["value"]
            if f not in s["por_fecha"] or mejor(v, s["por_fecha"][f], e["unit"]):
                s["por_fecha"][f] = v
    out = []
    for s in mapa.values():
        s["pts"] = [{"date": f, "v": s["por_fecha"][f]} for f in sorted(s["por_fecha"])]
        del s["por_fecha"]
        out.append(s)
    out.sort(key=lambda s: (-len(s["pts"]), s["name"].lower()))
    return out


def mejor_punto(s: dict) -> dict:
    b = None
    for p in s["pts"]:
        if b is None or mejor(p["v"], b["v"], s["unit"]):
            b = p
    return b


def cambio_pct(s: dict) -> float | None:
    """Mejora desde el primer registro, en % (positivo = mejor)."""
    pts = s["pts"]
    if len(pts) < 2 or not pts[0]["v"]:
        return None
    pct = (pts[-1]["v"] - pts[0]["v"]) / pts[0]["v"] * 100
    return -pct if s["unit"] in MENOS_ES_MEJOR else pct


def ids_con_pr(entrenos: list[dict]) -> set[tuple[str, str]]:
    """(id_entreno, clave_ejercicio) que tienen la mejor marca, solo si hay 2+ registros."""
    orden = sorted(entrenos, key=lambda w: (str(w["date"]), str(w.get("created_at") or "")))
    mejores: dict[str, tuple] = {}
    cuenta: dict[str, int] = {}
    for w in orden:
        for e in w.get("entries") or []:
            if not e.get("name") or e.get("value") is None:
                continue
            k = norm(e["name"]) + "|" + e["unit"]
            cuenta[k] = cuenta.get(k, 0) + 1
            if k not in mejores or mejor(e["value"], mejores[k][0], e["unit"]):
                mejores[k] = (e["value"], w["id"])
    return {(wid, k) for k, (_, wid) in mejores.items() if cuenta[k] > 1}


# ---------- consejos ----------
def consejos(entrenos: list[dict], hoy: dt.date | None = None) -> list[dict]:
    """Lista de avisos {nivel: bueno|aviso|malo|info|tipo, titulo, detalle}."""
    hoy = hoy or dt.date.today()
    out = []
    series = series_ejercicios(entrenos)
    for s in series:
        p = s["pts"]
        if len(p) < 2:
            continue
        ult, prev, best = p[-1], p[-2], mejor_punto(s)
        if ult is best:
            out.append({"nivel": "bueno", "orden": 1, "titulo": f"{s['name']}: nueva mejor marca",
                        "detalle": f"{fmt_valor(ult['v'], s['unit'])} el {ult['date']:%d/%m} (antes {fmt_valor(prev['v'], s['unit'])})."})
            continue
        desde_best = len(p) - 1 - p.index(best)
        peor = prev["v"] and abs(ult["v"] - prev["v"]) / prev["v"] > 0.03 and mejor(prev["v"], ult["v"], s["unit"])
        if desde_best >= 3:
            out.append({"nivel": "malo", "orden": 0, "titulo": f"{s['name']}: estancado",
                        "detalle": f"{desde_best} sesiones sin superar tu mejor marca ({fmt_valor(best['v'], s['unit'])}, "
                                   f"{best['date']:%d/%m}). Prueba a cambiar volumen, técnica o descanso."})
        elif peor:
            out.append({"nivel": "aviso", "orden": 0.5, "titulo": f"{s['name']}: has bajado",
                        "detalle": f"{fmt_valor(ult['v'], s['unit'])} frente a {fmt_valor(prev['v'], s['unit'])} la vez anterior. "
                                   "Revisa las notas de ese día."})
    recientes: dict[str, int] = {}
    for w in entrenos:
        if (hoy - a_fecha(w["date"])).days <= 30:
            recientes[w["type"]] = recientes.get(w["type"], 0) + 1
    if entrenos:
        for k in ["fuerza", "wod", "gym", "endurance"]:
            if not recientes.get(k):
                out.append({"nivel": "tipo", "tipo": k, "orden": 0.8, "titulo": f"Sin {TIPOS[k][0]} en 30 días",
                            "detalle": f"No has registrado ninguna sesión de {TIPOS[k][0].lower()} en el último mes."})
        n4 = sum(1 for w in entrenos if 0 <= (hoy - a_fecha(w["date"])).days < 28)
        out.append({"nivel": "info", "orden": 2, "titulo": f"{n4 / 4:.1f} sesiones por semana".replace(".", ","),
                    "detalle": "Media de las últimas 4 semanas."})
    solos = sum(1 for s in series if len(s["pts"]) == 1)
    if solos:
        out.append({"nivel": "info", "orden": 3,
                    "titulo": f"{solos} {'ejercicio' if solos == 1 else 'ejercicios'} con un solo registro",
                    "detalle": "Repite la misma prueba y escríbela igual para ver su progresión."})
    out.sort(key=lambda c: c["orden"])
    return out


# ---------- semanas ----------
def inicio_semana(d) -> dt.date:
    d = a_fecha(d)
    return d - dt.timedelta(days=d.weekday())


def sesiones_por_semana(entrenos: list[dict], semanas: int = 8, hoy: dt.date | None = None, clave: str = "type"):
    """Devuelve (lista_de_lunes, {valor_clave: [conteo por semana]})."""
    hoy = hoy or dt.date.today()
    lunes = [inicio_semana(hoy) - dt.timedelta(weeks=i) for i in range(semanas - 1, -1, -1)]
    idx = {l: i for i, l in enumerate(lunes)}
    cuentas: dict[str, list[int]] = {}
    for w in entrenos:
        i = idx.get(inicio_semana(w["date"]))
        if i is None:
            continue
        cuentas.setdefault(w[clave], [0] * semanas)[i] += 1
    return lunes, cuentas


# ---------- rutinas ----------
NUM_PESO = re.compile(r"@\s*(\d+(?:[.,]\d+)?)")
PALABRAS_METCON = ("wod", "conditioning", "gym", "emom", "amrap", "metcon", "for time")


def fmt_num(v: float) -> str:
    v = round(float(v) * 100) / 100
    return str(int(v)) if v.is_integer() else f"{v:g}".replace(".", ",")


def progresar(presc: str, delta: float) -> str:
    """Suma `delta` kg a cada peso escrito tras una @ ('3@40 2@45' -> '3@42,5 2@47,5')."""
    if not presc or not delta:
        return presc or ""
    return NUM_PESO.sub(lambda m: "@" + fmt_num(max(0.0, float(m.group(1).replace(",", ".")) + delta)), presc)


def prescripcion_semana(linea: dict, semana: int, ajustes: dict | None) -> tuple[str, bool, bool]:
    """(texto para esa semana, ¿ha subido respecto a la base?, ¿es un ajuste solo de esa semana?)."""
    aj = (ajustes or {}).get(str(semana), {}).get(linea["id"])
    if aj is not None:
        return aj, False, True
    base = linea.get("prescripcion") or ""
    delta = (semana - int(linea.get("base") or 1)) * float(linea.get("sube") or 0)
    return progresar(base, delta), bool(delta) and bool(NUM_PESO.search(base)), False


def peso_principal(presc: str) -> float | None:
    """El último peso escrito (la serie más pesada en '3@40 2@45 1@50')."""
    nums = NUM_PESO.findall(presc or "")
    return float(nums[-1].replace(",", ".")) if nums else None


def es_metcon(nombre: str) -> bool:
    n = norm(nombre)
    return any(p in n for p in PALABRAS_METCON)


def _limpio(v) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return ""
    return str(v).strip()


def _num(v, defecto: float = 0.0) -> float:
    try:
        f = float(str(v).replace(",", "."))
        return defecto if f != f else f
    except (TypeError, ValueError):
        return defecto


def aplicar_edicion(rut: dict, dia_id: str, filas: list[dict], semana: int, solo_esta: bool, nuevo_id) -> dict:
    """Aplica lo editado en la tabla de un día. `filas` = [{id, ejercicio, presc, sube, nota}]."""
    import copy
    rut = copy.deepcopy(rut)
    ajustes = rut.setdefault("ajustes", {})
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    previas = {l["id"]: l for l in dia["lineas"]}
    nuevas = []
    for f in filas:
        ejercicio = _limpio(f.get("ejercicio"))
        presc = _limpio(f.get("presc"))
        sube = _num(f.get("sube"), 0.0)
        nota = _limpio(f.get("nota"))
        lid = _limpio(f.get("id"))
        if not ejercicio and not presc:
            continue
        if lid not in previas:
            sube = _num(f.get("sube"), 0.0 if es_metcon(ejercicio) else 2.5)
            nuevas.append({"id": nuevo_id(), "ejercicio": ejercicio or "Sin nombre", "prescripcion": presc,
                           "sube": sube, "base": semana, "nota": nota})
            continue
        l = dict(previas[lid])
        actual, _, _ = prescripcion_semana(l, semana, ajustes)
        sin_ajuste, _, _ = prescripcion_semana(l, semana, None)
        if sube != float(l.get("sube") or 0):  # nuevo ritmo a partir de esta semana
            l["prescripcion"], l["base"], l["sube"] = sin_ajuste, semana, sube
        l["ejercicio"], l["nota"] = ejercicio or l["ejercicio"], nota
        if presc != actual:
            if solo_esta:
                ajustes.setdefault(str(semana), {})[lid] = presc
            else:
                l["prescripcion"], l["base"] = presc, semana
                for s in list(ajustes):
                    if int(s) >= semana:
                        ajustes[s].pop(lid, None)
        nuevas.append(l)
    dia["lineas"] = nuevas
    rut["ajustes"] = {s: a for s, a in ajustes.items() if a}
    return rut


# ---------- validar días ----------
def clave_dia(semana: int, dia_id: str) -> str:
    return f"{int(semana)}|{dia_id}"


def estado_dia(rut: dict, semana: int, dia_id: str, registrado: bool = False) -> dict:
    """{'estado': 'hecho'|'pospuesto'|'pendiente', 'destino': [semana, dia_id]?}"""
    e = (rut.get("estados") or {}).get(clave_dia(semana, dia_id))
    if registrado or (e and e.get("estado") == "hecho"):
        return {"estado": "hecho", "registrado": registrado}
    return e or {"estado": "pendiente"}


def destino_dia_siguiente(rut: dict, semana: int, dia_id: str) -> list:
    ids = [d["id"] for d in rut["dias"]]
    i = ids.index(dia_id)
    return [semana, ids[i + 1]] if i + 1 < len(ids) else [semana + 1, ids[0]]


def destino_semana_siguiente(semana: int, dia_id: str) -> list:
    return [semana + 1, dia_id]


def marcar_dia(rut: dict, semana: int, dia_id: str, estado: str | None, destino: list | None = None) -> dict:
    """estado: 'hecho', 'pospuesto' (con destino) o None para quitar la marca."""
    import copy
    rut = copy.deepcopy(rut)
    estados = rut.setdefault("estados", {})
    k = clave_dia(semana, dia_id)
    if estado is None:
        estados.pop(k, None)
    elif estado == "pospuesto":
        estados[k] = {"estado": "pospuesto", "destino": list(destino)}
    else:
        estados[k] = {"estado": estado}
    return rut


def pendientes_para(rut: dict, semana: int, dia_id: str, titulos_registrados: set) -> list[tuple[int, str]]:
    """Días pospuestos que caen en (semana, dia_id) y aún no se han hecho."""
    out = []
    nombres = {d["id"]: d["nombre"] for d in rut["dias"]}
    for k, e in (rut.get("estados") or {}).items():
        if e.get("estado") != "pospuesto" or list(e.get("destino") or []) != [semana, dia_id]:
            continue
        s, did = k.split("|", 1)
        if did in nombres and f"Semana {s} · {nombres[did]}" not in titulos_registrados:
            out.append((int(s), did))
    return sorted(out)


def sin_validar(rut: dict, semana: int, titulos_registrados: set) -> list[str]:
    return [d["nombre"] for d in rut["dias"]
            if estado_dia(rut, semana, d["id"], f"Semana {semana} · {d['nombre']}" in titulos_registrados)["estado"] == "pendiente"]
