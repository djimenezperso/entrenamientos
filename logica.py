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
