"""Cuestionario de objetivos del abonado nuevo → rutina de inicio a su medida.

Parte de una de las rutinas de referencia (la de Diego, Salatti, Manu o Archchana), recorta o añade días,
ajusta los pesos a su nivel, avisa de lo que no puede hacer con su material y le mete hasta 2 ciclos
(un movimiento que quiere aprender o lo que quiere priorizar).
"""
from __future__ import annotations

import re

from ciclos import CICLOS
from logica import _letra, copiar_rutina, norm, partes_del_dia, tipo_de_linea
from repertorio import CONDITIONING, MOVILIDAD

REFERENCIAS = ("Yo", "Salatti", "Manu Anel", "Archchana")
NIVEL_REF = {"Yo": 1.0, "Salatti": 0.8, "Manu Anel": 0.5}  # lo fuerte que es cada rutina de referencia
NIVEL_PERSONA = {"empiezo": 0.45, "menos1": 0.6, "1a3": 0.8, "mas3": 1.0}
NIVEL_WOD = {"empiezo": "Scaled", "menos1": "Scaled", "1a3": "Inter", "mas3": "RX"}

OBJETIVOS = {"fuerza": "Ponerme fuerte", "halterofilia": "Halterofilia", "crossfit": "CrossFit completo / competir",
             "forma": "Ponerme en forma y salud", "grasa": "Perder grasa"}
NIVELES_TXT = {"empiezo": "Empiezo de cero", "menos1": "Menos de 1 año", "1a3": "1–3 años", "mas3": "Más de 3 años"}
MATERIAL_TXT = {"barra": "barra y discos", "rack": "rack", "mancuernas": "mancuernas", "kettlebell": "kettlebell",
                "dominadas": "barra de dominadas", "anillas": "anillas", "maquinas": "remo/bike/ski",
                "comba": "comba", "gomas": "gomas", "cajon": "cajón"}
PRIORIDADES_TXT = {"fuerza": "Fuerza", "halterofilia": "Halterofilia", "gym": "Gimnásticos", "motor": "Motor / cardio",
                   "movilidad": "Movilidad"}
APRENDER_TXT = {"pullups": "Pull ups", "hspu": "HSPU", "t2b": "Toes to bar", "du": "Double unders",
                "muscleup": "Muscle up", "pistols": "Pistols", "halterofilia": "Snatch / clean & jerk"}
TIPO_TXT = {"Yo": "Progresión Diego Compite (tu rutina)", "Salatti": "fuerza + WOD (Salatti)", "Manu Anel": "base de fuerza (Manu)",
            "Archchana": "en casa (Archchana)"}

# (ciclo, material que necesita: basta con uno de la lista; vacío = nada)
APRENDER_CICLO = {"pullups": ("strict-pullups", ("dominadas", "anillas")), "hspu": ("hspu", ()),
                  "t2b": ("toes-to-bar", ("dominadas", "anillas")), "du": ("double-unders", ("comba",)),
                  "muscleup": ("muscle-up", ("dominadas", "anillas")), "pistols": ("pistols", ()),
                  "halterofilia": ("halterofilia-tecnica", ("barra",))}
PRIORIDAD_CICLO = {"fuerza": [("back-squat-pct", ("rack",))], "halterofilia": [("halterofilia-tecnica", ("barra",))],
                   "gym": [("strict-pullups", ("dominadas", "anillas")), ("hspu", ())],
                   "motor": [("engine-z2", ("maquinas",))], "movilidad": [("movilidad-cadera-hombro", ())]}

MAQUINA = re.compile(r"\b(row|rower|bike|ski|remo|elliptique|eliptica|elíptica)\b", re.I)
BARRA_DOM = re.compile(r"pull ?ups?|chest to bar|c2b|toes to bar|t2b|muscle ups?|ring rows?", re.I)
COMBA = re.compile(r"double unders?|\bdu\b|singles", re.I)


def _lista(v, validas) -> list[str]:
    return [x for x in (v if isinstance(v, list) else []) if x in validas]


def limpiar(c: dict) -> dict:
    """Solo lo que entendemos, con límites de tamaño."""
    r = {
        "objetivo": c.get("objetivo") if c.get("objetivo") in OBJETIVOS else "crossfit",
        "nivel": c.get("nivel") if c.get("nivel") in NIVEL_PERSONA else "menos1",
        "categoria": "mujer" if c.get("categoria") == "mujer" else "hombre",
        "dias": min(6, max(2, int(c.get("dias") or 4))) if str(c.get("dias") or "4").isdigit() else 4,
        "material": _lista(c.get("material"), MATERIAL_TXT),
        "prioridades": _lista(c.get("prioridades"), PRIORIDADES_TXT)[:2],
        "aprender": _lista(c.get("aprender"), APRENDER_TXT)[:3],
        "aprender_otro": str(c.get("aprender_otro") or "").strip()[:120],
        "tipo": c.get("tipo") if c.get("tipo") in REFERENCIAS else "auto",
        "lesiones": str(c.get("lesiones") or "").strip()[:300],
        "comentario": str(c.get("comentario") or "").strip()[:500],
        "lang": "fr" if c.get("lang") == "fr" else "es",
    }
    if "rack" in r["material"] and "barra" not in r["material"]:
        r["material"].append("barra")
    return r


def elegir_referencia(r: dict) -> tuple[str, str]:
    """Qué rutina de referencia le va mejor, y por qué (para Diego)."""
    mat = set(r["material"])
    if r["tipo"] != "auto":
        if r["tipo"] != "Archchana" and "barra" not in mat:
            return "Archchana", f"pidió {TIPO_TXT[r['tipo']]} pero no tiene barra → en casa"
        return r["tipo"], "la eligió él/ella"
    if "barra" not in mat:
        return "Archchana", "no tiene barra: rutina de casa"
    halte = r["objetivo"] == "halterofilia" or "halterofilia" in r["prioridades"]
    if halte and r["nivel"] in ("1a3", "mas3") and r["dias"] >= 5:
        return "Yo", "halterofilia, con experiencia y 5+ días"
    if r["nivel"] == "empiezo" or r["dias"] <= 3:
        return "Manu Anel", "empieza o tiene pocos días"
    return "Salatti", "fuerza + WOD de 4 días"


def _escalar_texto(texto: str, factor: float) -> str:
    def cambio(m):
        kg = float(m.group(1).replace(",", "."))
        nuevo = max(15.0, round(kg * factor / 2.5) * 2.5)
        return "@" + (f"{nuevo:.1f}".rstrip("0").rstrip(".").replace(".", ","))
    return re.sub(r"@\s*(\d+(?:[.,]\d+)?)(?!\s*%)", cambio, texto)


def fmt_kg(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".").replace(".", ",")


def _nota(l: dict, txt: str) -> None:
    l["nota"] = (l.get("nota", "") + " · " + txt).strip(" ·") if txt not in (l.get("nota") or "") else l["nota"]


SIN_MAQUINA = [("Carrera Z2", "25' carrera suave (puedes hablar)"),
               ("Intervalos de carrera", "8x 1' rápido / 1' andando"),
               ("EMOM burpees + air squats", "EMOM 16': impar 10 burpees · par 20 air squats")]


def _dia_extra(i: int, r: dict, nuevo_id, fr: bool) -> dict:
    mat = set(r["material"])
    cond = [c for c in CONDITIONING if "maquinas" in mat or not MAQUINA.search(c[1])] + SIN_MAQUINA
    c = cond[i % len(cond)]
    m1, m2 = MOVILIDAD[(2 * i) % len(MOVILIDAD)], MOVILIDAD[(2 * i + 1) % len(MOVILIDAD)]
    return {"id": nuevo_id(), "nombre": f"{'Jour' if fr else 'Día'} {i}", "por_ejercicio": False, "lineas": [
        {"id": nuevo_id(), "ejercicio": c[0], "prescripcion": c[1], "sube": 0.0, "base": 1, "nota": "",
         "parte": "A) Conditioning"},
        {"id": nuevo_id(), "ejercicio": m1[0], "prescripcion": m1[1], "sube": 0.0, "base": 1, "nota": "",
         "parte": "B) Movilidad"},
        {"id": nuevo_id(), "ejercicio": m2[0], "prescripcion": m2[1], "sube": 0.0, "base": 1, "nota": "",
         "parte": "B) Movilidad"},
    ]}


def _elegir_ciclos(r: dict, referencia: str) -> tuple[list[str], list[str]]:
    mat = set(r["material"])
    tiene = lambda req: not req or any(x in mat for x in req)  # noqa: E731
    elegidos, avisos = [], []
    for a in r["aprender"]:
        cid, req = APRENDER_CICLO[a]
        if a == "halterofilia" and referencia == "Yo":
            continue  # la de Diego ya es de halterofilia
        if not tiene(req):
            avisos.append(f"quiere aprender {APRENDER_TXT[a]} pero le falta material ({' o '.join(MATERIAL_TXT[x] for x in req)})")
        elif cid not in elegidos:
            elegidos.append(cid)
    for p in r["prioridades"]:
        for cid, req in PRIORIDAD_CICLO[p]:
            if p == "halterofilia" and referencia == "Yo":
                break
            if tiene(req) and cid not in elegidos:
                elegidos.append(cid)
                break
    if not elegidos and r["objetivo"] == "grasa" and "maquinas" in mat:
        elegidos.append("engine-z2")
    return elegidos[:2], avisos


def _meter_ciclo(rut: dict, ciclo: dict, desfase: int, nuevo_id) -> list[str]:
    """Una parte «X) Ciclo: …» en días repartidos por la semana, con la letra siguiente de cada día."""
    dias = rut["dias"]
    semanas = ciclo["semanas"]
    k = min(len(dias), max(len(s["sesiones"]) for s in semanas))
    usados = []
    for s_idx in range(k):
        dia = dias[(s_idx * len(dias) // k + desfase) % len(dias)]
        for l, p in zip(dia["lineas"], partes_del_dia(dia)):
            l.setdefault("parte", p)
        letras = [_letra(l["parte"]) for l in dia["lineas"] if _letra(l["parte"]) != "Z"]
        letra = chr(ord(max(letras)) + 1) if letras else "A"
        n = max((len(s["sesiones"][s_idx]) for s in semanas if s_idx < len(s["sesiones"])), default=0)
        for j in range(n):
            plan, ejercicio = {}, ""
            for w, s in enumerate(semanas):
                if s_idx < len(s["sesiones"]) and j < len(s["sesiones"][s_idx]):
                    plan[str(1 + w)] = s["sesiones"][s_idx][j]["prescripcion"]
                    ejercicio = ejercicio or s["sesiones"][s_idx][j]["ejercicio"]
            dia["lineas"].append({"id": nuevo_id(), "ejercicio": ejercicio or ciclo["nombre"],
                                  "prescripcion": next(iter(plan.values()), ""), "sube": 0.0, "base": 1, "nota": "",
                                  "parte": f"{letra}) Ciclo: {ciclo['nombre']}", "desde": 1, "hasta": len(semanas),
                                  "plan": plan, "ciclo": ciclo["id"]})
        usados.append(dia["nombre"])
    return usados


def construir(base: dict, referencia: str, r: dict, nuevo_id) -> tuple[dict, list[str]]:
    """Rutina nueva a partir de la de referencia y las respuestas. Devuelve (rutina, notas para Diego)."""
    fr = r["lang"] == "fr"
    mat = set(r["material"])
    notas = []
    rut = copiar_rutina(base, nuevo_id)
    rut["dias"] = [d for d in rut["dias"] if d["lineas"]]
    for d in rut["dias"]:
        for l in d["lineas"]:  # las notas de la rutina de referencia («propuesta…») no son para él/ella
            l["nota"] = "" if norm(l.get("nota", "")).startswith("propuesta") or "no hecho" in norm(l.get("nota", "")) else l.get("nota", "")
    # días por semana
    if len(rut["dias"]) > r["dias"]:
        notas.append(f"recortada de {len(rut['dias'])} a {r['dias']} días")
        rut["dias"] = rut["dias"][:r["dias"]]
    n0 = len(rut["dias"])
    for i in range(n0 + 1, r["dias"] + 1):
        rut["dias"].append(_dia_extra(i, r, nuevo_id, fr))
    if r["dias"] > n0:
        notas.append(f"+{r['dias'] - n0} día(s) de conditioning y movilidad")
    # sin snatch con barra si no es avanzado (y no ha pedido aprenderlo): con mancuerna y ligero al principio
    cambiados = set()
    if r["nivel"] != "mas3" and "halterofilia" not in r["aprender"] and "halterofilia" not in r["prioridades"]:
        kg_db = 7.5 if r["categoria"] == "mujer" or r["nivel"] == "empiezo" else 12.5
        nota_db = "avec haltère, léger au début" if fr else "con mancuerna, ligero al principio"
        n_snatch = 0
        for d in rut["dias"]:
            for l in d["lineas"]:
                nom = norm(l["ejercicio"])
                if "snatch" not in nom or re.search(r"\b(db|dumbbell|mancuerna|kb|kettlebell)\b", nom) \
                        or tipo_de_linea(l.get("parte", ""), l["ejercicio"]) not in (None, "accessory"):
                    continue
                n_snatch += 1
                pesos = re.findall(r"@\s*(\d+(?:[.,]\d+)?)", l["prescripcion"])
                if "pull" in nom or "deadlift" in nom:
                    l["ejercicio"] = "Romanian deadlift"
                    l["prescripcion"] = f"3x8 @{pesos[0]}" if pesos else "3x8"
                else:
                    l["ejercicio"] = "DB snatch alterno" if not fr else "DB snatch alterné"
                    l["prescripcion"] = f"4x8 (4+4) @{fmt_kg(kg_db)}"
                    l["sube"] = 0.0
                    _nota(l, nota_db)
                    cambiados.add(l["id"])
        if n_snatch:
            notas.append(f"snatch con barra → DB snatch ligero ({n_snatch} línea(s)), no es avanzado/a")
    # pesos a su nivel
    factor = None
    if referencia in NIVEL_REF:
        factor = NIVEL_PERSONA[r["nivel"]] / NIVEL_REF[referencia] * (0.7 if r["categoria"] == "mujer" else 1.0)
        factor = min(1.2, factor)
        if abs(factor - 1) < 0.05:
            factor = None
    aviso_peso = "poids indicatif : ajuste-le" if fr else "peso orientativo: ajústalo"
    aviso_maq = "pas de machine : remplace par course ou burpees" if fr else "sin máquina: cámbialo por carrera o burpees"
    aviso_dom = "sans barre de traction : ring rows élastique / sit ups" if fr else "sin barra de dominadas: remo con goma / sit ups"
    aviso_comba = "sans corde : sauts sur place" if fr else "sin comba: saltos sin cuerda"
    sin = {"maq": 0, "dom": 0, "comba": 0}
    for d in rut["dias"]:
        for l in d["lineas"]:
            texto = f"{l['ejercicio']} {l['prescripcion']}"
            if factor and l["id"] not in cambiados and tipo_de_linea(l.get("parte", ""), l["ejercicio"]) is None and "@" in l["prescripcion"]:
                nuevo = _escalar_texto(l["prescripcion"], factor)
                if nuevo != l["prescripcion"]:
                    l["prescripcion"] = nuevo
                    _nota(l, aviso_peso)
            if "maquinas" not in mat and MAQUINA.search(texto):
                _nota(l, aviso_maq); sin["maq"] += 1
            if not ({"dominadas", "anillas"} & mat) and BARRA_DOM.search(texto):
                _nota(l, aviso_dom); sin["dom"] += 1
            if "comba" not in mat and COMBA.search(texto):
                _nota(l, aviso_comba); sin["comba"] += 1
    if factor:
        notas.append(f"pesos x{factor:.2f} ({NIVELES_TXT[r['nivel']]}, {r['categoria']})")
    for k, txt in (("maq", "sin remo/bike/ski"), ("dom", "sin barra de dominadas"), ("comba", "sin comba")):
        if sin[k]:
            notas.append(f"⚠️ {txt}: {sin[k]} línea(s) marcadas para cambiar")
    # ciclos
    ciclos_id, avisos = _elegir_ciclos(r, referencia)
    notas += ["⚠️ " + a for a in avisos]
    por_id = {c["id"]: c for c in CICLOS}
    for i, cid in enumerate(ciclos_id):
        dias = _meter_ciclo(rut, por_id[cid], i, nuevo_id)
        notas.append(f"🔁 ciclo {por_id[cid]['nombre']} ({por_id[cid]['semanas'].__len__()} sem) en {', '.join(dias)}")
    if referencia == "Archchana" and not fr:
        notas.append("⚠️ la rutina de casa está en francés: tradúcesela")
    if r["aprender_otro"]:
        notas.append(f"⚠️ quiere aprender: {r['aprender_otro']} (no hay ciclo automático)")
    rut["semana_actual"] = 1
    rut["nivel"] = NIVEL_WOD[r["nivel"]]
    rut["material"] = ", ".join(MATERIAL_TXT[x] for x in r["material"]) or "sin material"
    rut["objetivos"] = r
    return rut, notas


def resumen(nombre: str, r: dict, referencia: str, porque: str, notas: list[str]) -> str:
    """Mensaje de Telegram para Diego."""
    lineas = [f"🎯 Objetivos de {nombre}",
              f"• Objetivo: {OBJETIVOS[r['objetivo']]}",
              f"• Nivel: {NIVELES_TXT[r['nivel']]} · {r['categoria']} · {r['dias']} días/semana",
              f"• Material: {', '.join(MATERIAL_TXT[x] for x in r['material']) or 'nada'}",
              f"• Prioriza: {', '.join(PRIORIDADES_TXT[x] for x in r['prioridades']) or '—'}",
              f"• Quiere aprender: {', '.join([APRENDER_TXT[x] for x in r['aprender']] + ([r['aprender_otro']] if r['aprender_otro'] else [])) or '—'}"]
    if r["lesiones"]:
        lineas.append(f"• 🩹 Lesiones/molestias: {r['lesiones']}")
    if r["comentario"]:
        lineas.append(f"• 💬 {r['comentario']}")
    lineas.append(f"\n📋 Rutina de inicio: basada en {TIPO_TXT[referencia]} — {porque}")
    lineas += [f"   · {n}" for n in notas]
    lineas.append("Revísala y ajústala cuando puedas.")
    return "\n".join(lineas)
