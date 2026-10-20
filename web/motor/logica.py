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
PALABRAS_METCON = ("wod", "conditioning", "gym", "emom", "amrap", "metcon", "for time", "movilidad", "mobility",
                   "mobilite", "estiramientos", "stretching")


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
    if semana < int(linea.get("desde") or 0) or (linea.get("hasta") is not None and semana > int(linea["hasta"])) \
            or int(semana) in [int(x) for x in linea.get("saltar") or []]:
        return "", False, False  # aún no existía, ya se quitó o esa semana se cambió por otra cosa
    aj = (ajustes or {}).get(str(semana), {}).get(linea["id"])
    if aj is not None:
        return aj, False, True
    if linea.get("plan") is not None:  # ciclo: texto fijado semana a semana
        return linea["plan"].get(str(semana), ""), False, False
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
    ests = [estado_parte(rut, semana, dia["id"], p)["estado"] for p, _ in agrupar_por_parte(dia, semana)]
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
        faltan = [p.split(")")[0] for p, _ in agrupar_por_parte(d, semana)
                  if estado_parte(rut, semana, d["id"], p)["estado"] == "pendiente"]
        if faltan:
            out.append(f"{d['nombre']} ({', '.join(faltan)})")
    return out


# ---------- partes del día (A, B, C…) ----------
PARTES = ["A) Fuerza", "A) Halterofilia", "B) Fuerza", "B) WOD", "B) Gym", "B) Gym / WOD", "B) Conditioning",
          "B) Accessory", "C) WOD", "C) Conditioning", "C) Accessory", "C) Movilidad", "D) Conditioning",
          "D) Accessory", "D) Movilidad"]


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


def agrupar_por_parte(dia: dict, semana: int | None = None) -> list[tuple[str, list[dict]]]:
    """[(parte, [líneas])] ordenado por letra, respetando el orden dentro de cada parte.
    Con `semana`, solo las líneas que existen esa semana (los ciclos duran unas semanas concretas)."""
    partes = partes_del_dia(dia)
    orden = sorted(range(len(partes)), key=lambda i: (_letra(partes[i]), i))
    if semana is not None:
        orden = [i for i in orden if linea_activa(dia["lineas"][i], semana)]
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
    if l.get("plan") is not None:
        l["plan"][str(semana)] = presc
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
                "push press", "sdhp", "c&j", "power clean", "power snatch", "hang clean", "hang snatch", "rdl",
                "romanian deadlift", "good morning", "good mornings", "bench press", "press banca"],
    "Cardio": ["run", "running", "correr", "carrera", "course", "rameur", "velo", "row", "remo", "bike", "echo", "assault", "ski", "skierg",
               "swim", "nadar", "cal", "km", "z2", "zona 2", "double under", "double unders", "du", "comba"],
    "Gym": ["pompes", "tractions", "fentes", "gainage", "abdos", "pull up", "pull ups", "pullup", "pullups", "dominada", "dominadas", "chest to bar", "c2b", "ctb",
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


CLAVES_BIBLIO = {"wod": "wods", "conditioning": "conditionings", "accessory": "accessories", "mobility": "movilidad"}
NOMBRE_BIBLIO = {"wod": "WODs", "conditioning": "Conditioning", "accessory": "Accessories", "mobility": "Movilidad"}
CATEGORIAS_MOVILIDAD = ["Todos", "Cadera", "Hombros", "Tobillos", "Espalda", "Isquios"]
_ZONAS = {
    "Cadera": ["cadera", "hip", "hips", "90 90", "pigeon", "paloma", "frog", "rana", "couch stretch", "cossack",
               "psoas", "gluteo", "glute", "aductor", "adductor", "pancake", "hanche"],
    "Hombros": ["hombro", "hombros", "shoulder", "shoulders", "dislocates", "wall slides", "pec", "pectoral",
                "lat stretch", "overhead", "epaule", "epaules"],
    "Tobillos": ["tobillo", "tobillos", "ankle", "ankles", "knee to wall", "calf", "gemelo", "gemelos", "cheville"],
    "Espalda": ["espalda", "thoracic", "toracica", "columna", "spine", "cat cow", "jefferson", "rotations",
                "rotaciones", "dos", "lumbar"],
    "Isquios": ["isquio", "isquios", "hamstring", "hamstrings", "pancake", "jefferson", "floss", "ischio"],
}


def clasificar_movilidad(texto: str) -> list[str]:
    t = norm_busqueda(texto)
    return [z for z, ps in _ZONAS.items() if any(_contiene(t, p) for p in ps)]


def tipo_de_linea(parte: str, ejercicio: str) -> str | None:
    """'wod', 'conditioning', 'accessory' o None (fuerza)."""
    p, e = norm_busqueda(parte), norm_busqueda(ejercicio)
    if any(w in p or w in e for w in ("movilidad", "mobility", "mobilite", "estiramiento", "stretch")):
        return "mobility"
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
    grupos = _agrupar_veces(veces, por_titulo=(tipo in ("accessory", "mobility")), tipo=tipo)
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


def _agrupar_veces(veces: list[dict], por_titulo: bool = False, tipo: str = "wod") -> list[dict]:
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
        if tipo == "mobility":
            g["categorias"] = clasificar_movilidad(g["titulo"] + "\n" + g["texto"])
        else:
            g["categorias"] = clasificar_wod(g["titulo"] + "\n" + g["texto"], g["titulo"] or primera)
        g["veces"].sort(key=lambda v: v["orden"], reverse=True)
        g["ultimo"] = g["veces"][0]["orden"]
        out.append(g)
    out.sort(key=lambda g: g["ultimo"], reverse=True)
    return out


def wods_hechos(rutinas: dict, atletas: list[str], entrenos: list[dict], manual: dict | None) -> list[dict]:
    return biblioteca(rutinas, atletas, entrenos, manual, "wod")


# ---------- importar de WhatsApp ----------
_RE_IOS = re.compile(r"^\[(\d{1,2})/(\d{1,2})/(\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::\d{2})?\]\s+([^:]+?):\s?(.*)$")
_RE_ANDROID = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2,4}),?\s+(\d{1,2}):(\d{2})\s+-\s+([^:]+?):\s?(.*)$")
_RUIDO = ("omitido", "omitted", "omitida", "este mensaje fue eliminado", "this message was deleted",
          "los mensajes y las llamadas están cifrados", "messages and calls are end-to-end encrypted",
          "<adjunto:", "<attached:", "mensaje editado", "<this message was edited>", "<se editó este mensaje.>")


def parse_whatsapp(texto: str) -> list[dict]:
    """Mensajes de un chat exportado (iPhone o Android): [{fecha, autor, texto}]."""
    mensajes = []
    for linea in (texto or "").replace("\r\n", "\n").split("\n"):
        limpia = linea.replace("‎", "").replace("‏", "").replace(" ", " ").replace("\xa0", " ")
        m = _RE_IOS.match(limpia) or _RE_ANDROID.match(limpia)
        if m:
            d, mes, a, _, _, autor, cuerpo = m.groups()
            a = int(a) + (2000 if len(a) == 2 else 0)
            try:
                fecha = dt.date(a, int(mes), int(d))
            except ValueError:
                try:
                    fecha = dt.date(a, int(d), int(mes))  # por si el móvil está en formato mes/día
                except ValueError:
                    continue
            mensajes.append({"fecha": fecha, "autor": autor.strip(), "texto": cuerpo})
        elif mensajes:
            mensajes[-1]["texto"] += "\n" + limpia
    for m in mensajes:
        lineas = [l for l in m["texto"].split("\n") if not any(r in l.lower() for r in _RUIDO)]
        m["texto"] = "\n".join(lineas).strip()
    return [m for m in mensajes if m["texto"]]


_FORMATOS = ["amrap", "emom", "e2mom", "e3mom", "every", "for time", "ft", "rft", "rondas", "rounds", "ronda", "round",
             "rnd", "rnds", "tabata", "cap", "time cap", "intervalos", "intervals", "chipper", "max", "reps", "cals",
             "metros", "series", "x", "tours", "tour", "repos", "repetitions", "minutes"]


def _tipo_probable(texto: str) -> str:
    t = norm_busqueda(texto)
    cats = clasificar_wod(texto)
    lineas = [l for l in texto.split("\n") if l.strip()]
    if cats == ["Cardio"]:
        return "conditioning"
    if re.search(r"\b\d+\s*x\s*\d+", t) and len(lineas) <= 3 and not any(_contiene(t, f) for f in
                                                                           ("amrap", "emom", "for time", "rondas", "rounds")):
        return "accessory"
    if cats == ["Cardio"]:
        return "conditioning"
    return "wod"


_DIAS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6,
         "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4, "samedi": 5, "dimanche": 6,
         "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def fecha_del_entreno(texto: str, fecha_mensaje: dt.date) -> dt.date:
    """La fecha a la que se refiere el mensaje: «mañana», «ayer», «el lunes», «12/10»… o la del propio mensaje."""
    t = norm_busqueda(" ".join(texto.split("\n")[:3]))
    m = re.search(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?![\d/])", " ".join(texto.split("\n")[:3]))
    if m:
        d, mes, a = int(m.group(1)), int(m.group(2)), m.group(3)
        anio = (int(a) + (2000 if len(a) == 2 else 0)) if a else fecha_mensaje.year
        try:
            f = dt.date(anio, mes, d)
            if abs((f - fecha_mensaje).days) <= 60:
                return f
        except ValueError:
            pass
    if any(_contiene(t, w) for w in ("pasado manana", "apres demain")):
        return fecha_mensaje + dt.timedelta(days=2)
    if any(_contiene(t, w) for w in ("manana", "demain", "tomorrow")) and not _contiene(t, "esta manana"):
        return fecha_mensaje + dt.timedelta(days=1)
    if any(_contiene(t, w) for w in ("ayer", "hier", "yesterday")):
        return fecha_mensaje - dt.timedelta(days=1)
    for nombre, wd in _DIAS.items():
        if _contiene(t, nombre):
            return fecha_mensaje + dt.timedelta(days=(wd - fecha_mensaje.weekday()) % 7)
    return fecha_mensaje


_INTRO = ("hoy", "manana", "wod", "toca", "aqui", "ahi", "va", "os paso", "el de", "entreno", "training")


def _separar_nombre(texto: str) -> tuple[str, str]:
    """Quita líneas de introducción ("Hoy toca:") y toma como nombre una primera línea corta sin números."""
    lineas = [l.strip() for l in texto.split("\n")]
    while lineas and (not lineas[0] or (lineas[0].endswith(":") and len(lineas[0]) <= 30)
                      or norm_busqueda(lineas[0]) in _INTRO):
        lineas.pop(0)
    if lineas and len(lineas) > 1 and len(lineas[0]) <= 30 and not re.search(r"\d", lineas[0]) \
            and not any(_contiene(norm_busqueda(lineas[0]), p) for p in ("amrap", "emom", "for time")):
        return lineas[0], "\n".join(lineas[1:]).strip()
    return "", "\n".join(lineas).strip()


def detectar_entrenos(mensajes: list[dict]) -> list[dict]:
    """Mensajes que parecen un WOD, conditioning o accessory, con una puntuación de confianza."""
    todas = [p for lista in _PALABRAS.values() for p in lista]
    out = []
    for m in mensajes:
        t = norm_busqueda(m["texto"])
        if len(t) < 12 or not re.search(r"\d", t):
            continue
        movs = {p for p in todas if len(p) > 2 and _contiene(t, p)}
        formatos = {f for f in _FORMATOS if _contiene(t, f)}
        lineas = len([l for l in m["texto"].split("\n") if l.strip()])
        puntos = len(movs) * 2 + len(formatos) * 2 + min(lineas, 6) + len(re.findall(r"(?<![a-z0-9])\d+(?![a-z0-9])", t)) // 3
        puntos += 3 * bool(re.search(r"\d+\s*x\s*\d+", t)) + 2 * bool(re.search(r"@\s*\d", m["texto"]))
        puntos += 3 * bool(re.search(r"\d+\s*-\s*\d+\s*-\s*\d+", m["texto"])) + bool(re.search(r"\d\s*kg", t))
        puntos += 2 * any(_contiene(t, w) for w in ("descanso", "rest", "repos", "accesorio", "accesorios", "accessory",
                                                    "rx", "movilidad", "mobilite", "estiramientos", "etirements"))
        zonas = clasificar_movilidad(m["texto"])
        if (movs or zonas) and puntos >= 7:
            nombre, cuerpo = _separar_nombre(m["texto"])
            tipo = "mobility" if zonas and (not movs or any(_contiene(t, w) for w in (
                "movilidad", "mobility", "mobilite", "estiramientos", "etirements", "stretch"))) else _tipo_probable(m["texto"])
            out.append({**m, "puntos": puntos, "tipo": tipo, "nombre": nombre, "cuerpo": cuerpo,
                        "fecha_entreno": fecha_del_entreno(m["texto"], m["fecha"])})
    return out


def emparejar_autor(autor: str, atletas: list[str]) -> str | None:
    """'Manu' -> 'Manu Anel'. None si no se parece a ninguno."""
    a = norm_busqueda(autor)
    for at in atletas:
        n = norm_busqueda(at)
        if a == n or (a and (a in n.split() or n.split()[0] == a.split()[0])):
            return at
    return None


# ---------- copiar rutina y rutina desde IA ----------
def copiar_rutina(origen: dict, nuevo_id) -> dict:
    """Copia la estructura y los pesos actuales de otra rutina, empezando en la semana 1 y sin marcas."""
    actual = int(origen.get("semana_actual") or 1)
    dias = []
    for d in origen.get("dias", []):
        lineas = []
        for l, p in zip(d["lineas"], partes_del_dia(d)):
            if actual < int(l.get("desde") or 0):
                continue
            lineas.append({"id": nuevo_id(), "ejercicio": l["ejercicio"],
                           "prescripcion": prescripcion_semana(l, actual, origen.get("ajustes"))[0],
                           "sube": float(l.get("sube") or 0), "base": 1, "nota": l.get("nota", ""), "parte": p})
        dias.append({"id": nuevo_id(), "nombre": d["nombre"], "lineas": lineas,
                     "por_ejercicio": bool(d.get("por_ejercicio"))})
    return {"semana_actual": 1, "ajustes": {}, "dias": dias}


def rutina_desde_json(data: dict, nuevo_id) -> dict:
    """Convierte la propuesta de la IA ({dias:[{nombre, lineas:[{parte, ejercicio, prescripcion, sube?}]}]})."""
    dias = []
    for i, d in enumerate(data.get("dias") or [], start=1):
        lineas = []
        for l in d.get("lineas") or []:
            ejercicio = str(l.get("ejercicio") or "").strip()
            presc = str(l.get("prescripcion") or "").strip()
            if not ejercicio and not presc:
                continue
            parte = str(l.get("parte") or "A) Fuerza").strip()
            tipo = tipo_de_linea(parte, ejercicio)
            sube = l.get("sube")
            sube = float(sube) if isinstance(sube, (int, float)) else (2.5 if tipo is None and NUM_PESO.search(presc) else 0.0)
            lineas.append({"id": nuevo_id(), "ejercicio": ejercicio or "Sin nombre", "prescripcion": presc,
                           "sube": sube, "base": 1, "nota": str(l.get("nota") or ""), "parte": parte})
        dias.append({"id": nuevo_id(), "nombre": str(d.get("nombre") or f"Día {i}"), "lineas": lineas})
    return {"semana_actual": 1, "ajustes": {}, "dias": dias}


def carga_maxima(texto: str) -> float | None:
    """La carga más alta escrita en un bloque (tras @ o antes de kg), para ver progresiones."""
    nums = []
    for grupo in re.findall(r"@\s*([\d.,]+(?:\s*[-/]\s*[\d.,]+)*)", texto):
        nums += re.findall(r"[\d]+(?:[.,]\d+)?", grupo)
    nums += re.findall(r"(\d+(?:[.,]\d+)?)\s*kg", texto, flags=re.I)
    vals = [float(n.replace(",", ".")) for n in nums]
    vals = [v for v in vals if 20 <= v <= 350]
    return max(vals) if vals else None


# ---------- EMOMs por duración ----------
TRAMOS_EMOM = ["≤10'", "11-20'", "21-30'", "31-40'", "40'+"]


def es_emom(texto: str) -> bool:
    t = norm_busqueda(texto)
    return bool(re.search(r"\be\d*mom\b|\bevery\s*\d|\btoutes les\s*\d|\bcada\s*\d+\s*(min|')", t))


def duracion_emom(texto: str) -> int | None:
    """Minutos totales de un EMOM/E2MOM/Every: «EMOM 12'», «E2MOM x8» (16), «Every 2' x7» (14), «Every 1:30 x8» (12)."""
    t = (texto or "").lower().replace("’", "'").replace("′", "'")
    m = re.search(r"\be(\d)\s*mom\s*(?:for\s*)?(x\s*)?(\d+)", t)
    if m:
        n = int(m.group(3))
        return int(m.group(1)) * n if m.group(2) else n
    m = re.search(r"\bemom\s*(?:for\s*)?(\d+)\s*(?:'|min|’)?", t)
    if m and not re.search(r"\bemom\s*x", t):
        return int(m.group(1))
    m = re.search(r"\b(?:every|toutes les|cada)\s*(\d+)(?::(\d{2}))?\s*(?:'|min|minutes?|mn)?\s*(?:x|for)\s*(\d+)\s*('|min)?", t)
    if m:
        intervalo = int(m.group(1)) + (int(m.group(2)) / 60 if m.group(2) else 0)
        n = int(m.group(3))
        return n if m.group(4) else round(intervalo * n)
    m = re.search(r"\((\d+)\s*(?:'|min)\)", t)  # «SNATCH (19')»: total escrito por el coach
    if m:
        return int(m.group(1))
    bloques = re.findall(r"\bemom\s*x\s*(\d+)", t)  # varios «EMOM x4» seguidos: se suman
    if bloques:
        return sum(int(n) for n in bloques)
    return None


def tramo_emom(minutos: int | None) -> str | None:
    if not minutos:
        return None
    if minutos <= 10:
        return TRAMOS_EMOM[0]
    if minutos <= 20:
        return TRAMOS_EMOM[1]
    if minutos <= 30:
        return TRAMOS_EMOM[2]
    if minutos <= 40:
        return TRAMOS_EMOM[3]
    return TRAMOS_EMOM[4]


# ---------- ciclos (programas de varias semanas) ----------
def _firma_progresion(texto: str) -> str:
    t = norm_busqueda(texto)
    t = re.sub(r"\d+(?:[.,]\d+)?\s*(kg|%)?", "#", t)
    t = re.sub(r"[#\s@x-]+", " ", t)
    return " ".join(t.split()[:8])


def ciclos_desde_coach(items: list[dict]) -> list[dict]:
    """Progresiones de 3+ semanas seguidas (mismo bloque con cargas que cambian), agrupadas en paquetes."""
    fuerza = sorted([i for i in items if i["tipo"] in ("fuerza", "halterofilia") and i.get("autor", "Coach") == "Coach"],
                    key=lambda i: i["fecha"])
    cadenas, usados = [], set()
    for n, a in enumerate(fuerza):
        if a["id"] in usados or len(_firma_progresion(a["texto"])) < 4:
            continue
        f, cadena = _firma_progresion(a["texto"]), [a]
        for b in fuerza[n + 1:]:
            if b["id"] in usados or _firma_progresion(b["texto"]) != f:
                continue
            gap = (dt.date.fromisoformat(b["fecha"]) - dt.date.fromisoformat(cadena[-1]["fecha"])).days
            if 4 <= gap <= 12:
                cadena.append(b)
            elif gap > 12:
                break
        if len(cadena) >= 3:
            usados |= {c["id"] for c in cadena}
            cadenas.append(cadena)
    # cadenas que empiezan la misma semana y duran lo mismo = un mismo programa (cada una, una sesión)
    paquetes: list[list[list[dict]]] = []
    for c in sorted(cadenas, key=lambda c: c[0]["fecha"]):
        ini = dt.date.fromisoformat(c[0]["fecha"])
        for p in paquetes:
            ini_p = dt.date.fromisoformat(p[0][0]["fecha"])
            if abs((ini - ini_p).days) <= 6 and len(p[0]) == len(c):
                p.append(c)
                break
        else:
            paquetes.append([c])
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    ciclos = []
    for p in paquetes:
        n = len(p[0])
        ini = dt.date.fromisoformat(p[0][0]["fecha"])
        levs = list(dict.fromkeys(c[0]["levantamiento"] or "Fuerza" for c in p))
        es_fuerza = all(c[0]["tipo"] == "fuerza" for c in p)
        ciclos.append({
            "id": "coach-" + p[0][0]["id"],
            "nombre": f"{' + '.join(levs)} · {n} semanas ({meses[ini.month - 1]} {ini.year})",
            "categoria": "Fuerza (coach)" if es_fuerza else "Halterofilia (coach)", "privado": True,
            "descripcion": f"Progresión del coach de {n} semanas con {len(p)} "
                           f"{'sesión' if len(p) == 1 else 'sesiones'} por semana.",
            "semanas": [{"sesiones": [[{"ejercicio": c[0]["levantamiento"] or "Fuerza", "prescripcion": c[w]["texto"]}]
                                      for c in p]} for w in range(n)],
        })
    return ciclos


def empezar_ciclo(rut: dict, ciclo: dict, semana_inicio: int, dias: list[str], letra: str, nuevo_id) -> dict:
    """Mete el ciclo en la rutina: una parte «X) Ciclo: …» en los días elegidos (uno por sesión), activa N semanas."""
    import copy
    rut = copy.deepcopy(rut)
    semanas = ciclo["semanas"]
    parte = f"{letra}) Ciclo: {ciclo['nombre']}"
    for s_idx, dia_id in enumerate(dias):
        dia = next((d for d in rut["dias"] if d["id"] == dia_id), None)
        if dia is None:
            continue
        for l, p in zip(dia["lineas"], partes_del_dia(dia)):
            l.setdefault("parte", p)
        n_lineas = max((len(s["sesiones"][s_idx]) for s in semanas if s_idx < len(s["sesiones"])), default=0)
        for j in range(n_lineas):
            plan, ejercicio = {}, ""
            for w, s in enumerate(semanas):
                if s_idx < len(s["sesiones"]) and j < len(s["sesiones"][s_idx]):
                    linea = s["sesiones"][s_idx][j]
                    plan[str(semana_inicio + w)] = linea["prescripcion"]
                    ejercicio = ejercicio or linea["ejercicio"]
            dia["lineas"].append({
                "id": nuevo_id(), "ejercicio": ejercicio or ciclo["nombre"], "prescripcion": next(iter(plan.values()), ""),
                "sube": 0.0, "base": semana_inicio, "nota": "", "parte": parte, "desde": semana_inicio,
                "hasta": semana_inicio + len(semanas) - 1, "plan": plan, "ciclo": ciclo["id"]})
        dia["lineas"] = [l for _, l in sorted(enumerate(dia["lineas"]), key=lambda t: (_letra(t[1]["parte"]), t[0]))]
    return rut


def quitar_ciclo(rut: dict, ciclo_id: str) -> dict:
    import copy
    rut = copy.deepcopy(rut)
    for d in rut["dias"]:
        d["lineas"] = [l for l in d["lineas"] if l.get("ciclo") != ciclo_id]
    return rut


def ciclos_en_marcha(rut: dict) -> list[dict]:
    vistos = {}
    for d in rut.get("dias", []):
        for l in d["lineas"]:
            if l.get("ciclo"):
                c = vistos.setdefault(l["ciclo"], {"id": l["ciclo"], "parte": l["parte"], "desde": l["desde"],
                                                   "hasta": l["hasta"], "dias": []})
                if d["nombre"] not in c["dias"]:
                    c["dias"].append(d["nombre"])
    return list(vistos.values())


def linea_activa(linea: dict, semana: int) -> bool:
    if semana < int(linea.get("desde") or 0):
        return False
    if linea.get("hasta") is not None and semana > int(linea["hasta"]):
        return False
    if int(semana) in [int(x) for x in linea.get("saltar") or []]:
        return False
    if linea.get("plan") is not None and str(semana) not in linea["plan"]:
        return False
    return True


# ---------- partes libres: añadir, borrar, letras por posición ----------
LETRAS = "ABCDEFGHIJ"


def _etiqueta_parte(parte: str) -> str:
    return parte.split(") ", 1)[1] if re.match(r"^[A-Za-z]\)\s", parte or "") else parte


def letra_visible(partes_semana: list[str], parte: str) -> str:
    """La parte tal como se ve esa semana: letra según su posición (A, B, C…) + su nombre."""
    i = partes_semana.index(parte) if parte in partes_semana else 0
    return f"{LETRAS[min(i, len(LETRAS) - 1)]}) {_etiqueta_parte(parte).rstrip(' ·')}"


def renumerar_partes(rut: dict, dia_id: str) -> dict:
    """Pone las letras A, B, C… según el orden de las partes en el día (conserva lo validado)."""
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    actuales = [p for p, _ in agrupar_por_parte(dia)]
    destino = [f"{LETRAS[i]}) {_etiqueta_parte(p)}" for i, p in enumerate(actuales)]
    if actuales == destino:
        return rut
    # dos pasos para no pisar nombres que se intercambian
    for i, p in enumerate(actuales):
        rut = renombrar_parte(rut, dia_id, p, f"{LETRAS[i]}~ {_etiqueta_parte(p)}")
    for i, p in enumerate(actuales):
        rut = renombrar_parte(rut, dia_id, f"{LETRAS[i]}~ {_etiqueta_parte(p)}", destino[i])
    return rut


def anadir_parte(rut: dict, dia_id: str, etiqueta: str, ejercicio: str, presc: str, semana: int,
                 solo_esta: bool, sube: float = 0.0) -> dict:
    """Parte nueva al final del día. Solo esta semana o desde esta semana en adelante."""
    import copy
    import uuid
    rut = copy.deepcopy(rut)
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    for l, p in zip(dia["lineas"], partes_del_dia(dia)):
        l.setdefault("parte", p)
    usadas = [_letra(p) for p, _ in agrupar_por_parte(dia)]
    sig = max((LETRAS.index(x) for x in usadas if x in LETRAS), default=-1) + 1
    parte = f"{LETRAS[min(sig, len(LETRAS) - 1)]}) {etiqueta}"
    linea = {"id": uuid.uuid4().hex[:8], "ejercicio": ejercicio.strip() or etiqueta, "prescripcion": presc.strip(),
             "sube": float(sube), "base": int(semana), "nota": "", "parte": parte, "desde": int(semana)}
    if solo_esta:
        linea["plan"] = {str(int(semana)): presc.strip()}
        linea["hasta"] = int(semana)
    dia["lineas"].append(linea)
    return rut


def quitar_parte(rut: dict, dia_id: str, parte: str, semana: int) -> dict:
    """Quita la parte desde `semana` (las semanas anteriores se quedan como estaban)."""
    import copy
    rut = copy.deepcopy(rut)
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    nuevas = []
    for l, p in zip(dia["lineas"], partes_del_dia(dia)):
        if p != parte:
            nuevas.append(l)
        elif int(l.get("desde") or 1) < semana:
            l["hasta"] = min(int(l.get("hasta") or 10 ** 6), semana - 1)
            if l.get("plan") is not None:
                l["plan"] = {k: v for k, v in l["plan"].items() if int(k) < semana}
            nuevas.append(l)
    dia["lineas"] = nuevas
    return rut


def sustituir_parte(rut: dict, dia_id: str, parte: str, semana: int, etiqueta: str, ejercicio: str, presc: str,
                    solo_esta: bool, sube: float = 0.0) -> dict:
    """Cambia una parte por otra cosa en el mismo hueco: solo esta semana (vuelve la siguiente) o desde esta semana."""
    import copy
    import uuid
    rut = copy.deepcopy(rut)
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    for l, p in zip(dia["lineas"], partes_del_dia(dia)):
        l.setdefault("parte", p)
        if p == parte:
            if solo_esta:
                l["saltar"] = sorted({int(x) for x in l.get("saltar") or []} | {int(semana)})
            elif int(l.get("desde") or 1) < semana:
                l["hasta"] = min(int(l.get("hasta") or 10 ** 6), semana - 1)
            else:
                l["_borrar"] = True
    dia["lineas"] = [l for l in dia["lineas"] if not l.pop("_borrar", False)]
    nueva = f"{parte[:1]}) {etiqueta}"
    if nueva == parte:
        nueva = f"{parte[:1]}) {etiqueta} ·"
    linea = {"id": uuid.uuid4().hex[:8], "ejercicio": ejercicio.strip() or etiqueta, "prescripcion": presc.strip(),
             "sube": float(sube), "base": int(semana), "nota": "", "parte": nueva, "desde": int(semana),
             "sustituye": parte}
    if solo_esta:
        linea["plan"], linea["hasta"] = {str(int(semana)): presc.strip()}, int(semana)
    dia["lineas"].append(linea)
    dia["lineas"] = [l for _, l in sorted(enumerate(dia["lineas"]), key=lambda t: (_letra(t[1]["parte"]), t[0]))]
    return rut


def deshacer_sustitucion(rut: dict, dia_id: str, parte_nueva: str, semana: int) -> dict:
    import copy
    rut = copy.deepcopy(rut)
    dia = next(d for d in rut["dias"] if d["id"] == dia_id)
    nuevas = [l for l in dia["lineas"] if l.get("parte") == parte_nueva and l.get("sustituye")]
    if not nuevas:
        return rut
    original = nuevas[0]["sustituye"]
    dia["lineas"] = [l for l in dia["lineas"] if l not in nuevas]
    for l in dia["lineas"]:
        if l.get("parte") == original:
            l["saltar"] = [x for x in l.get("saltar") or [] if int(x) != int(semana)]
            if l.get("hasta") is not None and int(l["hasta"]) == semana - 1 and l.get("plan") is None:
                l.pop("hasta")
    return rut


# ---------- versiones RX / Inter / Scaled / Elite ----------
NIVELES = ["RX", "Inter", "Scaled", "Elite"]
_DB = [5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 40, 45, 50]
_KB = [8, 12, 16, 20, 24, 28, 32, 40]
_WB = {"Inter": {9: 6, 6: 4, 14: 9, 10: 6}, "Scaled": {9: 4, 6: 3, 14: 6, 10: 4}, "Elite": {9: 9, 6: 6, 14: 14}}
_FACTOR = {"Inter": 0.75, "Scaled": 0.55, "Elite": 1.15}

_SUSTITUCIONES = {
    "Inter": [
        (r"(?:ring |bar )?muscle[ -]?ups?(?: ring)?|(?<![a-z])[br]?mu'?s?\b(?: ring)?", "C2B pull ups"),
        (r"strict hspu|strict handstand push ?ups?", "HSPU con abmat"),
        (r"\bhspu'?s?\b|handstand push ?ups?", "HSPU con abmat"),
        (r"handstand walks?|\bhw\b", "wall walks"),
        (r"\bpistols?(?: squats?)?\b", "pistols a caja"),
        (r"\bc2b\b|chest to bar(?: pull ups?)?", "pull ups"),
        (r"legless rope climbs?", "rope climbs"),
    ],
    "Scaled": [
        (r"(?:ring |bar )?muscle[ -]?ups?(?: ring)?|(?<![a-z])[br]?mu'?s?\b(?: ring)?", "pull ups con banda"),
        (r"\bc2b\b|chest to bar(?: pull ups?)?", "pull ups con banda"),
        (r"(?<!weighted )(?:butterfly |kipping |strict )?pull ?ups?", "ring rows"),
        (r"strict hspu|strict handstand push ?ups?|\bhspu'?s?\b|handstand push ?ups?", "pike push ups"),
        (r"handstand walks?|\bhw\b", "bear crawl"),
        (r"wall walks?|\bww\b", "inchworms"),
        (r"double[ -]?unders?|\bdu'?s?\b|dble du'?s?", "single unders (x2)"),
        (r"toes[ -]?to[ -]?bar|\bt2b\b|\bttb\b", "knee raises"),
        (r"\bpistols?(?: squats?)?\b", "air squats"),
        (r"(?:legless )?rope climbs?", "rope pulls desde el suelo"),
        (r"burpees? box jump overs?", "burpees + step ups"),
        (r"box jump overs?|box jumps?", "box step ups"),
        (r"ring dips?|(?<![a-z])r ?dips?\b", "box dips"),
        (r"ghd sit[ -]?ups?", "abmat sit ups"),
    ],
    "Elite": [
        (r"\bc2b\b|chest to bar(?: pull ups?)?", "bar muscle ups"),
        (r"(?<!strict )(?<!weighted )(?<!butterfly )pull ?ups?", "C2B pull ups"),
        (r"(?<!strict )\bhspu'?s?\b", "strict HSPU"),
    ],
}


_MU_CON_REPS = re.compile(r"(?<![\d.,])(?P<n>\d+)\s*(?:x\s*)?(?:ring |bar )?(?:muscle[ -]?ups?|(?<![a-z])[rb]?mus?\b)(?: ring)?", re.I)
_MU_A = {"Inter": lambda n: f"{n * 2} C2B pull ups",               # Inter: casi nunca muscle ups → C2B (x2)
         "Scaled": lambda n: f"{n * 3} pull ups (con banda si hace falta)"}  # Scaled: nunca muscle ups


def _redondear(v: float, tipo: str) -> float:
    if tipo == "db":
        return min(_DB, key=lambda x: abs(x - v))
    if tipo == "kb":
        return min(_KB, key=lambda x: abs(x - v))
    return max(2.5, round(v / 2.5) * 2.5)


def _escalar_linea(linea: str, nivel: str) -> str:
    bajo = linea.lower()
    tipo = "db" if re.search(r"\bdb|dbs\b|dumbb?ell|mancuerna|dble", bajo) else (
        "kb" if re.search(r"\bkb\b|kettlebell", bajo) else ("wb" if re.search(r"wall ?balls?|\bwb\b", bajo) else "bar"))
    f = _FACTOR[nivel]

    def esc(txt: str) -> str:
        v = float(txt.replace(",", "."))
        if tipo == "wb":
            nuevo = _WB[nivel].get(int(v), v * (f if nivel != "Elite" else 1))
        else:
            nuevo = _redondear(v * f, tipo)
        return fmt_num(nuevo)

    num = r"\d+(?:[.,]\d+)?"
    no_sigue = r"(?![\d.,])"
    patron = re.compile(
        rf"@\s*(?P<arr>{num}(?:\s*-\s*{num})*){no_sigue}(?!\s*%)"            # @60 / @60-65-70 (no %)
        rf"|(?P<a>{num})\s*/\s*(?P<b>{num}){no_sigue}(?!\s*(?:cal|''|\"|in\b|m\b|’’|%))"  # 43/30 (no cal/alturas)
        rf"|(?P<kg>{num})(?=\s*kg)"                                              # 60kg
        rf"|(?<=\b2x )(?P<dos>{num}){no_sigue}(?!\s*/)",                         # dble db 2x 22,5
        re.I)

    def cambio(m):
        if m.group("arr"):
            return "@" + "-".join(esc(x) for x in re.findall(num, m.group("arr")))
        if m.group("a"):
            peso = tipo != "bar" or "kg" in bajo or "@" in bajo or float(m.group("a").replace(",", ".")) >= 20
            return f"{esc(m.group('a'))}/{esc(m.group('b'))}" if peso else m.group(0)
        if m.group("kg"):
            return esc(m.group("kg"))
        if m.group("dos") and tipo in ("db", "kb", "wb"):
            return esc(m.group("dos"))
        return m.group(0)

    linea = patron.sub(cambio, linea)
    return linea


def escalar(texto: str, nivel: str) -> str:
    """Versión del texto para un nivel. El texto se toma como RX."""
    if not texto or nivel == "RX":
        return texto or ""
    # cada movimiento por separado (una línea puede tener wall balls y KB swings, con pesos distintos)
    lineas = ["".join(_escalar_linea(trozo, nivel) if i % 2 == 0 else trozo
                      for i, trozo in enumerate(re.split(r"(,\s+|\s\+\s|;\s*|\s/\s)", l)))
              for l in texto.split("\n")]
    out = "\n".join(lineas)
    # muscle ups con número delante («3x 1RMU», «5 bar muscle ups»): se cambian con más reps de un movimiento más fácil
    guardados = []

    def _mu(m):
        n = int(m.group("n"))
        nuevo = _MU_A[nivel](n) if nivel in _MU_A else m.group(0)
        guardados.append(nuevo)
        return f"\x00{len(guardados) - 1}\x00"
    out = _MU_CON_REPS.sub(_mu, out)
    reglas = _SUSTITUCIONES.get(nivel, [])
    if reglas:
        grande = re.compile("|".join(f"(?P<r{i}>{p})" for i, (p, _) in enumerate(reglas)), re.I)
        out = grande.sub(lambda m: next(reglas[int(k[1:])][1] for k, v in m.groupdict().items() if v is not None), out)
    out = re.sub("\x00(\\d+)\x00", lambda m: guardados[int(m.group(1))], out)
    if nivel == "Elite":
        out += "\n🎯 Elite: todo unbroken siempre que se pueda"
    return out


def referencias_elite(titulo_y_texto: str, elite: dict) -> list[dict]:
    """Referencias de atletas de élite si el WOD es un benchmark conocido (Fran, Grace, Open 24.1…)."""
    t = norm_busqueda(titulo_y_texto[:200])
    return [r for clave, refs in elite.items() if _contiene(t, clave) for r in refs]


# ---------- formatos: EMOM / For time / AMRAP ----------
FORMATOS = {"emom": "⏱️ EMOM", "fortime": "🏁 For time", "amrap": "🔁 AMRAP"}


def formato_de(texto: str) -> set[str]:
    t = norm_busqueda(texto)
    out = set()
    if es_emom(texto):
        out.add("emom")
    if re.search(r"\bfor time\b|\bft\b|\brft\b|\bpour le temps\b|\bpor tiempo\b|\bchrono\b", t):
        out.add("fortime")
    if re.search(r"\bamrap\b", t):
        out.add("amrap")
    return out


# ---------- PRs ----------
CATALOGO_PR = {
    "🏋️ Halterofilia": [("Snatch", "kg"), ("Clean & Jerk", "kg"), ("Power snatch", "kg"), ("Power clean", "kg"),
                        ("Squat clean", "kg"), ("Clean", "kg"), ("Jerk", "kg"), ("Overhead squat", "kg")],
    "💪 Fuerza": [("Back squat", "kg"), ("Front squat", "kg"), ("Deadlift", "kg"), ("Bench press", "kg"),
                 ("Strict press", "kg"), ("Push press", "kg")],
    "🤸 Gym": [("Pull ups seguidos", "reps"), ("Strict pull ups", "reps"), ("C2B pull ups", "reps"),
              ("Bar muscle ups", "reps"), ("Ring muscle ups", "reps"), ("HSPU", "reps"), ("Toes to bar", "reps"),
              ("Double unders", "reps")],
    "🏃 Carrera y remo": [("400 m run", "tiempo"), ("1 km run", "tiempo"), ("1 milla", "tiempo"), ("5 km run", "tiempo"),
                         ("10 km run", "tiempo"), ("500 m row", "tiempo"), ("2000 m row", "tiempo")],
}
_ALIAS_PR = {
    "Clean & Jerk": ["c&j", "clean & jerk", "clean and jerk", "squat clean & jerk", "cj"],
    "Pull ups seguidos": ["pull ups", "pull up", "dominadas", "kipping pull ups", "butterfly pull ups"],
    "Bar muscle ups": ["bar muscle up", "bmu", "bar mu"], "Ring muscle ups": ["ring muscle up", "rmu", "ring mu",
                                                                              "muscle ups"],
    "HSPU": ["handstand push ups", "hspu"], "Toes to bar": ["t2b", "ttb", "toes to bar"],
    "Double unders": ["du", "dus", "double unders"], "C2B pull ups": ["c2b", "chest to bar"],
    "Strict press": ["shoulder press", "press", "strict press"], "Bench press": ["bench", "press banca"],
    "Deadlift": ["dl", "peso muerto", "deadlift"], "400 m run": ["400m", "400 m"], "1 km run": ["1km", "1000 m run"],
    "5 km run": ["5k", "5km"], "10 km run": ["10k", "10km"], "2000 m row": ["2k row", "remo 2000 m", "2000m row"],
    "500 m row": ["500m row", "remo 500 m"],
}


def movimiento_pr(nombre: str) -> tuple[str, str, str] | None:
    """(categoría, movimiento, unidad) del catálogo al que corresponde un nombre libre, o None."""
    n = norm_busqueda(nombre)
    for cat, movs in CATALOGO_PR.items():
        for mov, unidad in movs:
            if n == norm_busqueda(mov) or n in {norm_busqueda(a) for a in _ALIAS_PR.get(mov, [])}:
                return cat, mov, unidad
    return None


def mejores_prs(registros: list[dict]) -> dict:
    """{(movimiento, reps): mejor registro}. kg y reps: más es mejor; tiempo: menos es mejor."""
    mejor = {}
    for r in sorted(registros, key=lambda r: str(r.get("fecha", ""))):
        k = (r["movimiento"], int(r.get("reps") or 1) if r["unidad"] == "kg" else 0)
        actual = mejor.get(k)
        if actual is None or (r["valor"] < actual["valor"] if r["unidad"] == "tiempo" else r["valor"] > actual["valor"]):
            mejor[k] = r
    return mejor


def prs_de_entrenos(entrenos: list[dict]) -> list[dict]:
    """Resultados registrados que son de un movimiento del catálogo (para detectar PRs solos)."""
    out = []
    for w in entrenos:
        for e in w.get("entries") or []:
            m = movimiento_pr(e.get("name", ""))
            if not m or e.get("value") is None:
                continue
            cat, mov, unidad = m
            if (unidad == "kg") != (e.get("unit") == "kg") or (unidad == "tiempo") != (e.get("unit") == "tiempo"):
                continue
            out.append({"categoria": cat, "movimiento": mov, "unidad": unidad, "valor": float(e["value"]), "reps": 1,
                        "fecha": str(w["date"])[:10], "nota": w.get("title") or "", "origen": "registro"})
    return out


def versiones_por_movimiento(texto: str, niveles=("RX", "Inter", "Scaled")) -> list[dict]:
    """Cada movimiento del WOD con su versión en cada nivel: [{RX: …, Inter: …, Scaled: …}].
    Los trozos que no cambian (descansos, rondas…) salen solo una vez."""
    out = []
    for linea in (texto or "").split("\n"):
        for trozo in re.split(r",\s+|\s\+\s|;\s*|\s/\s", linea):
            trozo = trozo.strip()
            if not trozo:
                continue
            fila = {n: escalar(trozo, n).split("\n")[0].strip() for n in niveles}
            out.append(fila)
    return out
