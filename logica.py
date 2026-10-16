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
    if semana < int(linea.get("desde") or 0):  # añadida más tarde: no existía esa semana
        return "", False, False
    aj = (ajustes or {}).get(str(semana), {}).get(linea["id"])
    if aj is not None:
        return aj, False, True
    p = parametros_semana(linea, semana)
    base = p.get("prescripcion") or ""
    delta = semanas_que_sube(p, semana) * float(p.get("sube") or 0)
    return progresar(base, delta), bool(delta) and bool(NUM_PESO.search(base)), False


def parametros_semana(linea: dict, semana: int) -> dict:
    """Los datos de la línea que valían en esa semana (los cambios nunca reescriben semanas anteriores)."""
    for e in sorted(linea.get("historial") or [], key=lambda e: e["hasta"]):
        if semana <= int(e["hasta"]):
            return {**linea, **e}
    return linea


def rebasar(linea: dict, semana: int, presc: str | None = None, sube: float | None = None) -> None:
    """Empieza un tramo nuevo en `semana` (modifica `linea`). Lo anterior se guarda tal cual en `historial`."""
    hist = [dict(e) for e in sorted(linea.get("historial") or [], key=lambda e: e["hasta"])]
    for e in hist:
        e["hasta"] = min(int(e["hasta"]), semana - 1)
    hist = [e for e in hist if e["hasta"] >= 1]
    tope = max((e["hasta"] for e in hist), default=0)
    if semana - 1 >= 1 and tope < semana - 1:
        hist.append({"hasta": semana - 1, "prescripcion": linea.get("prescripcion") or "",
                     "base": int(linea.get("base") or 1), "sube": float(linea.get("sube") or 0)})
    vistos, limpio = set(), []
    for e in hist:
        if e["hasta"] not in vistos:
            vistos.add(e["hasta"])
            limpio.append(e)
    linea["historial"] = limpio
    if presc is not None:
        linea["prescripcion"] = presc
    if sube is not None:
        linea["sube"] = sube
    linea["base"] = int(semana)


def semanas_que_sube(linea: dict, semana: int) -> int:
    """Semanas de subida desde la base, sin contar las que se repiten por un «no hecho»."""
    b = int(linea.get("base") or 1)
    pausas = sum(1 for p in linea.get("pausas") or [] if b <= int(p) < semana)
    return semana - b - pausas


def se_repite(linea: dict, semana: int) -> bool:
    """¿Esta semana repite pesos porque la anterior no se hizo?"""
    p = parametros_semana(linea, semana)
    return (semana - 1) in [int(x) for x in linea.get("pausas") or []] and float(p.get("sube") or 0) > 0 \
        and int(p.get("base") or 1) <= semana - 1


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
        parte = _limpio(f.get("parte"))
        if not ejercicio and not presc:
            continue
        if lid not in previas:
            sube = _num(f.get("sube"), 0.0 if es_metcon(ejercicio) or "accessor" in parte.lower() else 2.5)
            nuevas.append({"id": nuevo_id(), "ejercicio": ejercicio or "Sin nombre", "prescripcion": presc,
                           "sube": sube, "base": semana, "nota": nota, "parte": parte, "desde": semana})
            continue
        l = dict(previas[lid])
        actual, _, _ = prescripcion_semana(l, semana, ajustes)
        sin_ajuste, _, _ = prescripcion_semana(l, semana, None)
        if sube != float(l.get("sube") or 0):  # nuevo ritmo a partir de esta semana
            rebasar(l, semana, sin_ajuste, sube)
        l["ejercicio"], l["nota"] = ejercicio or l["ejercicio"], nota
        if parte:
            l["parte"] = parte
        if presc != actual:
            if solo_esta:
                ajustes.setdefault(str(semana), {})[lid] = presc
            else:
                rebasar(l, semana, presc)
                for s in list(ajustes):
                    if int(s) >= semana:
                        ajustes[s].pop(lid, None)
        nuevas.append(l)
    dia["lineas"] = nuevas
    for l, p in zip(nuevas, partes_del_dia(dia)):
        l["parte"] = p
    dia["lineas"] = [l for _, l in sorted(enumerate(nuevas), key=lambda t: (_letra(t[1]["parte"]), t[0]))]
    rut["ajustes"] = {s: a for s, a in ajustes.items() if a}
    return rut


# ---------- validar partes de cada día ----------
def clave_parte(semana: int, dia_id: str, parte: str) -> str:
    return f"{int(semana)}|{dia_id}|{parte}"


def estado_parte(rut: dict, semana: int, dia_id: str, parte: str) -> dict:
    """{'estado': 'hecho'|'pospuesto'|'pendiente', 'destino': [semana, dia_id]?}"""
    est = rut.get("estados") or {}
    e = est.get(clave_parte(semana, dia_id, parte)) or est.get(f"{int(semana)}|{dia_id}")  # marca antigua de día entero
    return e or {"estado": "pendiente"}


def resumen_dia(rut: dict, semana: int, dia: dict) -> str:
    """'hecho', 'no_hecho', 'parcial', 'pospuesto' o 'pendiente'."""
    ests = [estado_parte(rut, semana, dia["id"], p)["estado"] for p, _ in agrupar_por_parte(dia)]
    if not ests:
        return "pendiente"
    if all(e == "hecho" for e in ests):
        return "hecho"
    if all(e == "no_hecho" for e in ests):
        return "no_hecho"
    if all(e == "pospuesto" for e in ests):
        return "pospuesto"
    if any(e != "pendiente" for e in ests):
        return "parcial"
    return "pendiente"


def destino_dia_siguiente(rut: dict, semana: int, dia_id: str) -> list:
    ids = [d["id"] for d in rut["dias"]]
    i = ids.index(dia_id)
    return [semana, ids[i + 1]] if i + 1 < len(ids) else [semana + 1, ids[0]]


def destino_semana_siguiente(semana: int, dia_id: str) -> list:
    return [semana + 1, dia_id]


def marcar_parte(rut: dict, semana: int, dia_id: str, parte: str, estado: str | None, destino: list | None = None) -> dict:
    """estado: 'hecho', 'no_hecho' (repite pesos la semana siguiente), 'pospuesto' (con destino) o None."""
    import copy
    rut = copy.deepcopy(rut)
    estados = rut.setdefault("estados", {})
    viejo = f"{int(semana)}|{dia_id}"
    if viejo in estados:  # pasar la marca antigua de día entero a cada parte
        e = estados.pop(viejo)
        dia = next((d for d in rut["dias"] if d["id"] == dia_id), None)
        for p, _ in (agrupar_por_parte(dia) if dia else []):
            estados.setdefault(clave_parte(semana, dia_id, p), dict(e))
    k = clave_parte(semana, dia_id, parte)
    dia = next((d for d in rut["dias"] if d["id"] == dia_id), None)
    lineas = next((ls for p, ls in agrupar_por_parte(dia) if p == parte), []) if dia else []
    previo = (estados.get(k) or {}).get("estado")
    if previo == "no_hecho" or estado == "no_hecho":  # rehacer la repetición de toda la parte
        for l in lineas:
            if semana in [int(x) for x in l.get("pausas") or []]:
                l["pausas"] = [x for x in l["pausas"] if int(x) != semana]
    if estado == "no_hecho":  # la semana siguiente repite pesos
        for l in lineas:
            if float(l.get("sube") or 0) > 0:
                l.setdefault("pausas", []).append(int(semana))
    if estado is None:
        estados.pop(k, None)
    elif estado == "pospuesto":
        estados[k] = {"estado": "pospuesto", "destino": list(destino)}
    else:
        estados[k] = {"estado": estado}
    return rut


def pendientes_para(rut: dict, semana: int, dia_id: str) -> list[tuple[int, str, str]]:
    """Partes pospuestas que caen en (semana, dia_id): [(semana_origen, dia_origen, parte)]."""
    out = []
    ids = {d["id"] for d in rut["dias"]}
    for k, e in (rut.get("estados") or {}).items():
        if e.get("estado") != "pospuesto" or list(e.get("destino") or []) != [semana, dia_id]:
            continue
        trozos = k.split("|", 2)
        if trozos[1] not in ids:
            continue
        if len(trozos) == 3:
            out.append((int(trozos[0]), trozos[1], trozos[2]))
        else:  # marca antigua de día entero
            dia = next(d for d in rut["dias"] if d["id"] == trozos[1])
            out += [(int(trozos[0]), trozos[1], p) for p, _ in agrupar_por_parte(dia)]
    return sorted(out)


def sin_validar(rut: dict, semana: int) -> list[str]:
    out = []
    for d in rut["dias"]:
        faltan = [p.split(")")[0] for p, _ in agrupar_por_parte(d)
                  if estado_parte(rut, semana, d["id"], p)["estado"] == "pendiente"]
        if faltan:
            out.append(f"{d['nombre']} ({', '.join(faltan)})")
    return out


# ---------- partes del día (A, B, C…) ----------
PARTES = ["A) Fuerza", "A) Halterofilia", "B) Fuerza", "B) WOD", "B) Gym", "B) Gym / WOD", "B) Conditioning",
          "B) Accessory", "C) WOD", "C) Conditioning", "C) Accessory", "D) Conditioning", "D) Accessory"]


def _letra(parte: str) -> str:
    p = (parte or "").strip()
    return p[0].upper() if p[:1].isalpha() and p[1:2] in (")", ".", " ", "") else "Z"


def partes_del_dia(dia: dict) -> list[str]:
    """La parte de cada línea; si falta, la deduce (fuerza seguida, cada metcon una letra nueva)."""
    out, ultima = [], None
    for l in dia.get("lineas", []):
        p = (l.get("parte") or "").strip()
        if not p:
            nombre = l["ejercicio"] if es_metcon(l["ejercicio"]) else "Fuerza"
            if ultima and ultima.split(") ", 1)[-1] == nombre:
                p = ultima
            else:
                sig = chr(ord(_letra(ultima)) + 1) if ultima and _letra(ultima) != "Z" else "A"
                p = f"{sig}) {nombre}"
        out.append(p)
        ultima = p
    return out


def agrupar_por_parte(dia: dict) -> list[tuple[str, list[dict]]]:
    """[(parte, [líneas])] ordenado por letra, respetando el orden dentro de cada parte."""
    partes = partes_del_dia(dia)
    orden = sorted(range(len(partes)), key=lambda i: (_letra(partes[i]), i))
    grupos: list[tuple[str, list[dict]]] = []
    for i in orden:
        if grupos and grupos[-1][0] == partes[i]:
            grupos[-1][1].append(dia["lineas"][i])
        else:
            grupos.append((partes[i], [dia["lineas"][i]]))
    return grupos


# ---------- cambiar pesos rápido ----------
def _buscar_linea(rut: dict, lid: str) -> dict | None:
    return next((l for d in rut["dias"] for l in d["lineas"] if l["id"] == lid), None)


def fijar_prescripcion(rut: dict, lid: str, semana: int, presc: str, solo_esta: bool) -> None:
    """Fija la prescripción de una línea en `semana` (modifica `rut`). Desde esa semana sigue subiendo."""
    l = _buscar_linea(rut, lid)
    if l is None:
        return
    ajustes = rut.setdefault("ajustes", {})
    if solo_esta:
        ajustes.setdefault(str(semana), {})[lid] = presc
        return
    rebasar(l, int(semana), presc)
    for s in list(ajustes):
        if int(s) >= semana:
            ajustes[s].pop(lid, None)
    rut["ajustes"] = {s: a for s, a in ajustes.items() if a}


def poner_pesos(presc: str, pesos: list[float]) -> str:
    """Sustituye, en orden, los pesos tras @ por `pesos`. Si no tenía ninguno, añade ' @peso'."""
    if not pesos:
        return presc
    if not NUM_PESO.search(presc or ""):
        return ((presc or "").strip() + f" @{fmt_num(pesos[0])}").strip()
    it = iter(pesos)
    return NUM_PESO.sub(lambda m: "@" + fmt_num(next(it, float(m.group(1).replace(",", ".")))), presc)


def cambiar_pesos(rut: dict, semana: int, cambios: dict, solo_esta: bool, propagar: bool) -> tuple[dict, list[str]]:
    """cambios = {id_linea: nueva_prescripcion}. Con `propagar`, mueve igual el mismo ejercicio en otros días.
    Devuelve (rutina nueva, nombres de los días tocados por propagación)."""
    import copy
    rut = copy.deepcopy(rut)
    tocados = []
    antes = {lid: prescripcion_semana(_buscar_linea(rut, lid), semana, rut.get("ajustes"))[0] for lid in cambios}
    for lid, presc in cambios.items():
        fijar_prescripcion(rut, lid, semana, presc, solo_esta)
    if propagar:
        for lid, presc in cambios.items():
            viejo, nuevo = peso_principal(antes[lid]), peso_principal(presc)
            if viejo is None or nuevo is None or viejo == nuevo:
                continue
            nombre = norm(_buscar_linea(rut, lid)["ejercicio"])
            for d in rut["dias"]:
                for l in d["lineas"]:
                    if l["id"] in cambios or norm(l["ejercicio"]) != nombre:
                        continue
                    actual = prescripcion_semana(l, semana, rut.get("ajustes"))[0]
                    if NUM_PESO.search(actual):
                        fijar_prescripcion(rut, l["id"], semana, progresar(actual, nuevo - viejo), solo_esta)
                        tocados.append(d["nombre"])
    return rut, sorted(set(tocados), key=tocados.index)


def linea_no_hecha(linea: dict, semana: int) -> bool:
    return int(semana) in [int(x) for x in linea.get("pausas") or []]


def marcar_linea(rut: dict, lid: str, semana: int, no_hecha: bool) -> dict:
    """Un ejercicio suelto no hecho: la semana siguiente repite su peso."""
    import copy
    rut = copy.deepcopy(rut)
    l = _buscar_linea(rut, lid)
    if l is not None:
        pausas = [int(x) for x in l.get("pausas") or [] if int(x) != int(semana)]
        if no_hecha:
            pausas.append(int(semana))
        l["pausas"] = sorted(pausas)
    return rut


def no_hechas_en(lineas: list[dict], semana: int) -> int:
    return sum(1 for l in lineas if not es_metcon(l["ejercicio"]) and linea_no_hecha(l, semana))


# ---------- renombrar partes e historial ----------
def renombrar_parte(rut: dict, dia_id: str, vieja: str, nueva: str) -> dict:
    """Cambia la letra/nombre de una parte del día y conserva lo ya validado."""
    import copy
    rut = copy.deepcopy(rut)
    nueva = nueva.strip()
    if not nueva or nueva == vieja:
        return rut
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    for l, p in zip(dia["lineas"], partes_del_dia(dia)):
        l["parte"] = nueva if p == vieja else p
    dia["lineas"] = [l for _, l in sorted(enumerate(dia["lineas"]), key=lambda t: (_letra(t[1]["parte"]), t[0]))]
    estados = rut.get("estados") or {}
    for k in list(estados):
        trozos = k.split("|", 2)
        if len(trozos) == 3 and trozos[1] == dia_id and trozos[2] == vieja:
            estados[f"{trozos[0]}|{dia_id}|{nueva}"] = estados.pop(k)
    return rut


def historial_parte(rut: dict, dia_id: str, parte: str, hasta: int, maximo: int = 6) -> list[tuple[int, str]]:
    """[(semana, estado)] de las últimas semanas hasta `hasta` (incluida)."""
    desde = max(1, hasta - maximo + 1)
    return [(s, estado_parte(rut, s, dia_id, parte)["estado"]) for s in range(desde, hasta + 1)]


def editar_texto_linea(rut: dict, lid: str, semana: int, ejercicio: str, presc: str, nota: str, solo_esta: bool) -> dict:
    """Edición libre de una línea (WOD, conditioning, accessory): nombre y nota para siempre; el texto
    solo esa semana o desde esa semana en adelante."""
    import copy
    rut = copy.deepcopy(rut)
    l = _buscar_linea(rut, lid)
    if l is None:
        return rut
    l["ejercicio"] = ejercicio.strip() or l["ejercicio"]
    l["nota"] = nota.strip()
    actual = prescripcion_semana(l, semana, rut.get("ajustes"))[0]
    if presc.strip() != actual:
        fijar_prescripcion(rut, lid, semana, presc.strip(), solo_esta)
    return rut


# ---------- biblioteca de WODs ----------
import unicodedata

CLAVE_BIBLIOTECA = "__biblioteca_wods__"
CATEGORIAS_WOD = ["Todos", "Gym", "Barbell", "Dumbbell", "Cardio", "🎖️ Hero"]
NOMBRES_HERO = ["murph", "dt", "jt", "randy", "michael", "nate", "josh", "danny", "badger", "jerry", "ryan",
                "hansen", "glen", "holleyman", "nutts", "chad", "luce", "loredo", "whitten", "griff", "tommy v",
                "the seven", "kalsu", "bull", "manion", "wittman", "zimmerman", "hero"]
_PALABRAS = {
    "Dumbbell": ["dumbbell", "dumbell", "db", "dbs", "mancuerna", "mancuernas", "devil press", "man maker"],
    "Barbell": ["barbell", "barra", "thruster", "thrusters", "clean", "cleans", "snatch", "snatches", "jerk", "jerks",
                "deadlift", "deadlifts", "peso muerto", "front squat", "back squat", "overhead squat", "ohs",
                "push press", "sdhp", "c&j", "power clean", "power snatch", "hang clean", "hang snatch"],
    "Cardio": ["run", "running", "correr", "carrera", "row", "remo", "bike", "echo", "assault", "ski", "skierg",
               "swim", "nadar", "cal", "km", "z2", "zona 2", "double under", "double unders", "du", "comba"],
    "Gym": ["pull up", "pull ups", "pullup", "pullups", "dominada", "dominadas", "chest to bar", "c2b", "ctb",
            "toes to bar", "t2b", "ttb", "muscle up", "muscle ups", "mu", "bmu", "rmu", "handstand", "hspu", "pino",
            "rope climb", "rope climbs", "cuerda", "ring", "rings", "anillas", "pistol", "pistols", "dips", "fondos",
            "knees to elbow", "k2e", "double under", "double unders", "du", "dus", "burpee", "burpees", "push up",
            "push ups", "flexiones", "box jump", "box jumps", "sit up", "sit ups", "abmat", "wall walk", "wall walks",
            "lunges", "zancadas", "air squat", "air squats", "ghd", "l sit"],
}


def norm_busqueda(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[-_/·,.;:()\[\]+*']", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _contiene(texto_norm: str, palabra: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(norm_busqueda(palabra)) + r"(?![a-z0-9])", texto_norm) is not None


def es_hero(titulo: str) -> bool:
    t = norm_busqueda(titulo)
    return any(_contiene(t, n) for n in NOMBRES_HERO)


def clasificar_wod(texto: str, titulo: str = "") -> list[str]:
    t = norm_busqueda(texto)
    cats = ["🎖️ Hero"] if es_hero(titulo or texto.splitlines()[0] if texto else titulo) else []
    if any(_contiene(t, p) for p in _PALABRAS["Dumbbell"]):
        cats.append("Dumbbell")
    # Barbell solo si aparece en una línea/movimiento sin mancuerna ("DB hang clean and jerk" no es barra)
    trozos = [norm_busqueda(x) for x in re.split(r"[\n,;+/]", texto or "")]
    if any(any(_contiene(x, p) for p in _PALABRAS["Barbell"]) and not any(_contiene(x, p) for p in _PALABRAS["Dumbbell"])
           for x in trozos):
        cats.append("Barbell")
    if any(_contiene(t, p) for p in _PALABRAS["Gym"]):
        cats.append("Gym")
    if any(_contiene(t, p) for p in _PALABRAS["Cardio"]):
        cats.append("Cardio")
    return cats


def coincide_busqueda(texto: str, consulta: str) -> bool:
    """Todas las palabras buscadas aparecen (sin importar tildes, guiones ni espacios: pull-up = pullup = pull up)."""
    t = norm_busqueda(texto)
    t_junto = t.replace(" ", "")
    for trozo in [x for x in re.split(r"\s*,\s*", consulta or "") if x.strip()] or [""]:
        q = norm_busqueda(trozo)
        if q and q not in t and q.replace(" ", "") not in t_junto:
            return False
    return True


def _es_parte_wod(parte: str, ejercicio: str) -> bool:
    p = norm_busqueda(parte)
    if "accessor" in p or ("conditioning" in p and "wod" not in p):
        return False
    return any(k in p for k in ("wod", "gym", "metcon")) or es_metcon(ejercicio) and "conditioning" not in norm_busqueda(ejercicio)


def _fecha_corta(f) -> str:
    try:
        return f"{a_fecha(f):%d/%m/%Y}"
    except (TypeError, ValueError):
        return str(f or "")


CLAVES_BIBLIO = {"wod": "wods", "conditioning": "conditionings", "accessory": "accessories"}
NOMBRE_BIBLIO = {"wod": "WODs", "conditioning": "Conditioning", "accessory": "Accessories"}


def tipo_de_linea(parte: str, ejercicio: str) -> str | None:
    """'wod', 'conditioning', 'accessory' o None (fuerza)."""
    p, e = norm_busqueda(parte), norm_busqueda(ejercicio)
    if "accessor" in p:
        return "accessory"
    if "conditioning" in p or "conditioning" in e:
        return "conditioning"
    if es_metcon(ejercicio) or any(k in p for k in ("wod", "gym", "metcon")):
        return "wod"
    return None


def anadir_linea(rut: dict, dia_id: str, parte: str, ejercicio: str, presc: str, semana: int) -> dict:
    """Nueva línea en una parte, que existe desde `semana` (no aparece en semanas anteriores)."""
    import copy
    import uuid
    rut = copy.deepcopy(rut)
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    for l, p in zip(dia["lineas"], partes_del_dia(dia)):
        l.setdefault("parte", p)
    nueva = {"id": uuid.uuid4().hex[:8], "ejercicio": ejercicio.strip() or "Sin nombre", "prescripcion": presc.strip(),
             "sube": 0.0, "base": int(semana), "nota": "", "parte": parte, "desde": int(semana)}
    ult = max((i for i, l in enumerate(dia["lineas"]) if l.get("parte") == parte), default=len(dia["lineas"]) - 1)
    dia["lineas"].insert(ult + 1, nueva)
    return rut


def biblioteca(rutinas: dict, atletas: list[str], entrenos: list[dict], manual: dict | None, tipo: str) -> list[dict]:
    """Junta lo hecho de un tipo ('wod', 'conditioning', 'accessory') en las rutinas, en los entrenos registrados
    (solo WOD) y en la lista manual. Devuelve grupos {titulo, texto, categorias, veces:[...]}."""
    veces = []
    for atleta in atletas:
        rut = rutinas.get(atleta)
        if not rut:
            continue
        actual = int(rut.get("semana_actual") or 1)
        for d in rut.get("dias", []):
            for parte, lineas in agrupar_por_parte(d):
                for l in lineas:
                    if tipo_de_linea(parte, l["ejercicio"]) != tipo:
                        continue
                    for sem in range(1, actual + 1):
                        txt = prescripcion_semana(l, sem, rut.get("ajustes"))[0]
                        if not txt:
                            continue
                        estado = estado_parte(rut, sem, d["id"], parte)["estado"]
                        if tipo == "accessory" and l.get("pausas") and sem in [int(x) for x in l["pausas"]]:
                            estado = "no_hecho"
                        generico = es_metcon(l["ejercicio"]) and norm(l["ejercicio"]) in (
                            "wod", "gym / wod", "wod / gym", "gym", "metcon", "conditioning")
                        veces.append({"atleta": atleta, "texto": txt,
                                      "titulo": "" if generico else l["ejercicio"],
                                      "cuando": f"Semana {sem} · {d['nombre']}", "orden": f"S{sem:03d}",
                                      "estado": estado, "resultado": ""})
    if tipo == "wod":
        veces += _veces_de_entrenos(entrenos)
    for item in (manual or {}).get(CLAVES_BIBLIO[tipo], []):
        for q in item.get("quien") or [""]:
            veces.append({"atleta": q, "texto": item.get("texto", ""), "titulo": item.get("nombre", ""),
                          "cuando": "idea guardada" if item.get("idea") else _fecha_corta(item.get("fecha", "")),
                          "orden": item.get("fecha", ""), "estado": "pendiente" if item.get("idea") else "hecho",
                          "resultado": item.get("resultado", ""), "id": item.get("id")})
    grupos = _agrupar_veces(veces, por_titulo=(tipo == "accessory"))
    corregidas = (manual or {}).get("categorias_manual", {})
    for g in grupos:
        if g["clave"] in corregidas:
            g["categorias"] = list(corregidas[g["clave"]])
    return grupos


def _veces_de_entrenos(entrenos: list[dict]) -> list[dict]:
    veces = []
    for w in entrenos:
        if w.get("type") != "wod":
            continue
        resultados = ", ".join(f"{e['name']} {fmt_valor(e.get('value'), e['unit'])}" for e in w.get("entries") or []
                               if e.get("value") is not None)
        texto = "\n".join(x for x in [w.get("notes") or "", ", ".join(e["name"] for e in w.get("entries") or [])] if x)
        veces.append({"atleta": w["athlete"], "texto": texto or (w.get("title") or ""), "titulo": w.get("title") or "",
                      "cuando": _fecha_corta(w["date"]), "orden": str(w["date"]), "estado": "hecho",
                      "resultado": resultados})
    return veces


def _agrupar_veces(veces: list[dict], por_titulo: bool = False) -> list[dict]:
    grupos: dict[str, dict] = {}
    for v in veces:
        k = norm_busqueda((v["titulo"] + " | " if por_titulo else "") + v["texto"]) or norm_busqueda(v["titulo"])
        if not k:
            continue
        g = grupos.setdefault(k, {"titulo": "", "texto": v["texto"], "veces": [], "ids": set(), "clave": k})
        g["titulo"] = g["titulo"] or v["titulo"]
        g["veces"].append(v)
        if v.get("id"):
            g["ids"].add(v["id"])
    out = []
    for g in grupos.values():
        primera = (g["texto"].split(":")[0] if ":" in g["texto"].splitlines()[0] else "") if g["texto"] else ""
        g["categorias"] = clasificar_wod(g["titulo"] + "\n" + g["texto"], g["titulo"] or primera)
        g["veces"].sort(key=lambda v: v["orden"], reverse=True)
        g["ultimo"] = g["veces"][0]["orden"]
        out.append(g)
    out.sort(key=lambda g: g["ultimo"], reverse=True)
    return out


def wods_hechos(rutinas: dict, atletas: list[str], entrenos: list[dict], manual: dict | None) -> list[dict]:
    return biblioteca(rutinas, atletas, entrenos, manual, "wod")
