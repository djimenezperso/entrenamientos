"""Rutinas de partida. Solo se usan la primera vez; después se guardan y se editan desde la app.

Cada línea: ejercicio, prescripción (los pesos van tras @), kg que sube cada semana,
semana en la que vale esa prescripción (base) y nota.
"""


def _l(i, ejercicio, presc="", sube=2.5, base=1, nota="", parte="A) Fuerza"):
    return {"id": i, "ejercicio": ejercicio, "prescripcion": presc, "sube": sube, "base": base, "nota": nota,
            "parte": parte}


def _metcon(i, nombre, presc="", base=1, nota="", parte=None):
    return _l(i, nombre, presc, 0, base, nota, parte or f"B) {nombre}")


def _yo():
    b = 2  # Diego pasó estos pesos ya en semana 2
    return {
        "semana_actual": 2,
        "ajustes": {},
        "dias": [
            {"id": "d1", "nombre": "Día 1", "lineas": [
                _l("y11", "Snatch", "3x3 @50", base=b),
                _l("y12", "Power clean + press", "2+2 @65", base=b),
                _l("y13", "Snatch pull", "3x3 @85", base=b),
                _metcon("y14", "WOD", base=b),
                _metcon("y15", "Conditioning", base=b, parte="C) Conditioning"),
            ]},
            {"id": "d2", "nombre": "Día 2", "lineas": [
                _l("y21", "Power snatch", "3x3 @40", base=b),
                _l("y22", "Squat clean", "3x2 @70", base=b),
                _l("y23", "Clean pull", "3x3 @100", base=b),
                _metcon("y24", "Gym / WOD", base=b),
            ]},
            {"id": "d3", "nombre": "Día 3", "por_ejercicio": True, "lineas": [
                _l("y31", "Back squat", "1x10 @125", base=b, nota="dinámico"),
                _l("y32", "Front squat", "1x10 @105", base=b, nota="dinámico"),
                _l("y33", "Push press", "1x10 @65", base=b, nota="dinámico"),
                _l("y34", "Bench press", "1x10 @50", base=b, nota="dinámico"),
                _metcon("y35", "Conditioning", base=b),
            ]},
            {"id": "d4", "nombre": "Día 4", "por_ejercicio": True, "lineas": [
                _l("y41", "3 hang power snatch + 1 squat snatch", "@40", base=b),
                _l("y42", "3 hang power clean + 1 squat clean", "", base=b),
                _l("y43", "Push press + push jerk + split jerk", "3x(1+1+1)", base=b),
                _l("y44", "Snatch deadlift", "", sube=0, base=b, parte="B) Accessory"),
            ]},
            {"id": "d5", "nombre": "Día 5", "por_ejercicio": True, "pasa_a": "d3", "lineas": [
                _l("y51", "Back squat", "1x10 @125", base=b, nota="dinámico"),
                _l("y52", "Front squat", "1x10 @105", base=b, nota="dinámico"),
                _l("y53", "Push press", "1x10 @65", base=b, nota="dinámico"),
                _l("y54", "Bench press", "1x10 @50", base=b, nota="dinámico"),
                _metcon("y55", "Gym / WOD", base=b),
            ]},
            {"id": "d6", "nombre": "Día 6", "lineas": [
                _l("y61", "Snatch", "3@40 2@45 1@50", base=b),
                _l("y62", "Clean & jerk", "3@60 2@70 1@80", base=b),
                _metcon("y63", "EMOM 40'", "5x (10 thrusters + 5 burpees)", base=b, nota="¿40 min?", parte="B) WOD"),
                _l("y64", "Deadlift", "3x6 @140", sube=0, base=b, parte="C) Accessory"),
            ]},
        ],
    }


def _manu():
    return {
        "semana_actual": 2,
        "ajustes": {},
        "dias": [
            {"id": "d1", "nombre": "Lunes", "lineas": [
                _l("m11", "Bench press", "3x6 @30"),
                _l("m12", "Back squat", "3x6 @35"),
                _metcon("m13", "WOD"),
            ]},
            {"id": "d2", "nombre": "Miércoles", "lineas": [
                _l("m21", "Bench press dinámico", "10 @25"),
                _l("m22", "Back squat dinámico", "10 @30"),
                _l("m23", "Front squat dinámico", "10 @25"),
                _l("m24", "Push press dinámico", "10 @25"),
                _metcon("m25", "Conditioning"),
            ]},
            {"id": "d3", "nombre": "Viernes", "lineas": [
                _l("m31", "Bench press", "3@27,5 2@30 1@32,5"),
                _l("m32", "Back squat", "3@32,5 2@35 1@37,5"),
                _l("m33", "Deadlift", "3x5 @50"),
                _metcon("m34", "WOD / Gym"),
            ]},
        ],
    }


def _pareja():
    return {
        "semana_actual": 2,
        "ajustes": {},
        "dias": [
            {"id": "d1", "nombre": "Día 1", "por_ejercicio": True, "lineas": [
                _l("p11", "Squat snatch", "3x3 @20"),
                _l("p12", "Snatch pull", "3x3 @45"),
                _l("p13", "Back squat", "", nota="Semana 1: no hecho"),
                _metcon("p14", "WOD"),
            ]},
            {"id": "d2", "nombre": "Día 2", "por_ejercicio": True, "lineas": [
                _l("p21", "Squat clean", "3x3 @30"),
                _l("p22", "Clean pull", "3x3 @50"),
                _l("p23", "Front squat", "", nota="Semana 1: no hecho"),
                _metcon("p24", "WOD / Gym"),
            ]},
            {"id": "d3", "nombre": "Día 3", "por_ejercicio": True, "lineas": [
                _l("p31", "Jerk", "3x3 @20"),
                _l("p32", "Push press", "3x3 @25"),
                _metcon("p33", "Conditioning"),
            ]},
        ],
    }


def _salatti():
    """Propuesta de 4 días (semana 1). Cambiar con lo que hizo de verdad tocando cada parte."""
    nota = "propuesta: cámbialo por lo que hiciste"
    return {
        "semana_actual": 1,
        "ajustes": {},
        "nivel": "Inter",
        "dias": [
            {"id": "d1", "nombre": "Día 1", "por_ejercicio": True, "lineas": [
                _l("s11", "Back squat", "5x5 @80", nota=nota),
                _l("s12", "Strict press", "4x6 @40", nota=nota),
                _metcon("s13", "WOD", "AMRAP 12': 10 wall balls 9/6 kg, 10 box jumps, 10 KB swings 24/16 kg",
                        nota=nota),
            ]},
            {"id": "d2", "nombre": "Día 2", "por_ejercicio": True, "lineas": [
                _l("s21", "Power clean", "5x3 @60", nota=nota),
                _l("s22", "Front squat", "4x4 @70", nota=nota),
                _metcon("s23", "For time", "For time 3 rondas: 400 m run, 15 thrusters 43/30 kg, 12 pull ups",
                        nota=nota, parte="B) For time"),
            ]},
            {"id": "d3", "nombre": "Día 3", "lineas": [
                _metcon("s31", "EMOM", "EMOM 16': 12 cal row / 10 burpees / 8 DB snatch 22,5/15 / descanso",
                        nota=nota, parte="A) EMOM"),
                _l("s32", "Romanian deadlift", "3x10 @60", sube=0, nota=nota, parte="B) Accessory"),
                _l("s33", "DB row", "3x12 por brazo", sube=0, nota=nota, parte="B) Accessory"),
            ]},
            {"id": "d4", "nombre": "Día 4", "por_ejercicio": True, "lineas": [
                _l("s41", "Deadlift", "5x3 @100", nota=nota),
                _l("s42", "Bench press", "4x6 @60", nota=nota),
                _metcon("s43", "Conditioning", "4x 500 m row · R 1:30", nota=nota, parte="B) Conditioning"),
            ]},
        ],
    }


def _dario():
    """Misma estructura que Salatti, con más carga (está más fuerte) y gym más guiado (le cuesta más).
    Propuesta: que él ajuste los pesos tocándolos."""
    nota = "propuesta: ajusta el peso"
    gym = "propuesta de gym"
    return {
        "semana_actual": 1,
        "ajustes": {},
        "nivel": "Inter",
        "dias": [
            {"id": "d1", "nombre": "Día 1", "por_ejercicio": True, "lineas": [
                _l("r11", "Back squat", "5x5 @100", nota=nota),
                _l("r12", "Strict press", "4x6 @50", nota=nota),
                _metcon("r13", "Gym", "4x: 5 strict pull ups (con banda si hace falta) + 20'' hollow hold · R 1'",
                        nota=gym, parte="B) Gym"),
                _metcon("r14", "WOD", "AMRAP 12': 10 wall balls 9/6 kg, 10 box jumps, 10 KB swings 24/16 kg",
                        parte="C) WOD"),
            ]},
            {"id": "d2", "nombre": "Día 2", "por_ejercicio": True, "lineas": [
                _l("r21", "Power clean", "5x3 @75", nota=nota),
                _l("r22", "Front squat", "4x4 @85", nota=nota),
                _metcon("r23", "Gym", "EMOM 8': 1) 5 toes to bar (o knee raises) 2) 30'' handstand hold en pared",
                        nota=gym, parte="B) Gym"),
                _metcon("r24", "For time", "For time 3 rondas: 400 m run, 15 thrusters 43/30 kg, 12 pull ups",
                        parte="C) For time"),
            ]},
            {"id": "d3", "nombre": "Día 3", "lineas": [
                _metcon("r31", "EMOM", "EMOM 16': 12 cal row / 10 burpees / 8 DB snatch 22,5/15 / descanso",
                        parte="A) EMOM"),
                _l("r32", "Romanian deadlift", "3x10 @80", sube=0, nota=nota, parte="B) Accessory"),
                _l("r33", "DB row", "3x12 por brazo @25", sube=0, nota=nota, parte="B) Accessory"),
            ]},
            {"id": "d4", "nombre": "Día 4", "por_ejercicio": True, "lineas": [
                _l("r41", "Deadlift", "5x3 @130", nota=nota),
                _l("r42", "Bench press", "4x6 @75", nota=nota),
                _metcon("r43", "Gym", "5x: 3 negativas de pull up (5'') + 5 ring rows estrictos · R 1'",
                        nota=gym, parte="B) Gym"),
                _metcon("r44", "Conditioning", "4x 500 m row · R 1:30", parte="C) Conditioning"),
            ]},
        ],
    }


def _juan():
    """Misma rutina que Salatti (4 días). Que la ajuste a sus pesos."""
    return _salatti()


def _archchana():
    """En casa: 2 mancuernas ligeras, gomas y elíptica. En francés, con mucha movilidad. Propuesta para ajustar."""
    def m(i, nombre, txt, parte):
        return _l(i, nombre, txt, sube=0, parte=parte)
    return {
        "semana_actual": 1, "ajustes": {}, "nivel": "RX",
        "material": "2 haltères légers, élastiques, elliptique (pas de barre, pas d'anneaux)",
        "dias": [
            {"id": "d1", "nombre": "Jour 1", "por_ejercicio": True, "lineas": [
                m("a11", "Goblet squat DB", "4x12 tempo 3'' en descente", "A) Force"),
                m("a12", "DB romanian deadlift", "4x12", "A) Force"),
                _metcon("a13", "WOD", "AMRAP 12' : 10 DB thrusters, 10 fentes alternées, 200 m elliptique",
                        parte="B) WOD"),
                m("a14", "Mobilité hanches", "90/90 3x8 par côté + couch stretch 2x60''", "C) Movilidad"),
            ]},
            {"id": "d2", "nombre": "Jour 2", "lineas": [
                _metcon("a21", "Conditioning", "10x 1' rapide / 1' lent elliptique", parte="A) Conditioning"),
                m("a22", "Rowing élastique", "3x15", "B) Accessory"),
                m("a23", "Face pull élastique", "3x15", "B) Accessory"),
                m("a24", "Mobilité épaules", "Dislocates élastique 3x15 + wall slides 3x10", "C) Movilidad"),
            ]},
            {"id": "d3", "nombre": "Jour 3", "por_ejercicio": True, "lineas": [
                m("a31", "Bulgarian split squat DB", "3x10 par jambe", "A) Force"),
                m("a32", "DB push press", "4x10", "A) Force"),
                _metcon("a33", "EMOM", "EMOM 16' : 1) 12 DB snatch alternés 2) 15 squats sautés "
                        "3) 12 rowing élastique 4) repos", parte="B) EMOM"),
                m("a34", "Mobilité dos", "Cat-cow 2x10 + open book 2x10 par côté", "C) Movilidad"),
            ]},
            {"id": "d4", "nombre": "Jour 4", "lineas": [
                _metcon("a41", "Conditioning", "30' elliptique zone 2", parte="A) Conditioning"),
                m("a42", "Flow mobilité", "Flujo de 15' : world's greatest stretch, deep squat hold, pigeon, "
                  "pancake", "B) Movilidad"),
            ]},
        ],
    }


def rutinas_iniciales(atletas: list[str]) -> dict:
    """Asocia por posición: 0 = yo, 1 = Manu, 2 = Salatti, 3 = pareja. El resto empieza sin rutina."""
    fabricas = {0: _yo, 1: _manu, 2: _salatti, 3: _pareja, 4: _dario, 5: _archchana, 6: _juan}
    return {a: fabricas[i]() for i, a in enumerate(atletas) if i in fabricas}


# Cambios aplicados después de que alguien ya guardara su rutina (se aplican al cargar, solo una vez).
DINAMICO_1X10 = {"y31", "y32", "y33", "y34", "y51", "y52", "y53", "y54"}


def migrar(rut: dict, atleta: str, atletas: list[str]) -> dict:
    if len(atletas) > 2 and atleta == atletas[2] and not any(d.get("lineas") for d in rut.get("dias", [])):
        return _salatti()  # tenía una rutina vacía: se pone la propuesta de 4 días
    if len(atletas) > 4 and atleta == atletas[4] and not any(d.get("lineas") for d in rut.get("dias", [])):
        return _dario()
    if len(atletas) > 6 and atleta == atletas[6] and not any(d.get("lineas") for d in rut.get("dias", [])):
        return _juan()
    if len(atletas) > 5 and atleta == atletas[5] and not any(d.get("lineas") for d in rut.get("dias", [])):
        return _archchana()
    if len(atletas) > 3 and atleta == atletas[3]:  # pareja: cada ejercicio de fuerza se puede marcar como no hecho
        hechas = rut.setdefault("migraciones", [])
        if "pareja_por_ejercicio" not in hechas:
            for d in rut.get("dias", []):
                d["por_ejercicio"] = True
            hechas.append("pareja_por_ejercicio")
    if atletas and atleta == atletas[0]:
        for d in rut.get("dias", []):
            ids = {l["id"] for l in d["lineas"]}
            if d["id"] in ("d3", "d5") and ids & DINAMICO_1X10:
                d.setdefault("por_ejercicio", True)
            if d["id"] == "d5" and ids & DINAMICO_1X10:
                d.setdefault("pasa_a", "d3")  # si el día 5 no se hace, va al día 3 de la semana siguiente
            for l in d["lineas"]:
                if l["id"] in DINAMICO_1X10 and "x" not in (l.get("prescripcion") or "").lower():
                    l["prescripcion"] = ("1x10 " + (l.get("prescripcion") or "")).strip()
                    l["nota"] = l.get("nota") or "dinámico"
                    for sem in (rut.get("ajustes") or {}).values():
                        if l["id"] in sem and "x" not in sem[l["id"]].lower():
                            sem[l["id"]] = "1x10 " + sem[l["id"]]
        if "series_d2_y_d4" not in rut.setdefault("migraciones", []):
            series = {"y21": "3x3", "y22": "3x2", "y23": "3x3"}
            for d in rut.get("dias", []):
                if d["id"] == "d4" and any(l["id"].startswith("y4") for l in d["lineas"]):
                    d["por_ejercicio"] = True
                for l in d["lineas"]:
                    if l["id"] in series and "x" not in (l.get("prescripcion") or "").lower():
                        l["prescripcion"] = f"{series[l['id']]} {l.get('prescripcion') or ''}".strip()
                        for e in l.get("historial") or []:
                            if "x" not in (e.get("prescripcion") or "").lower():
                                e["prescripcion"] = f"{series[l['id']]} {e.get('prescripcion') or ''}".strip()
                        for sem in (rut.get("ajustes") or {}).values():
                            if l["id"] in sem and "x" not in sem[l["id"]].lower():
                                sem[l["id"]] = f"{series[l['id']]} {sem[l['id']]}"
            rut["migraciones"].append("series_d2_y_d4")
        if "wods_diego_s2" not in rut.setdefault("migraciones", []):
            # WODs que Diego hizo en la semana 2 (me los contó por el chat): se apuntan y se marcan como hechos
            from logica import partes_del_dia, prescripcion_semana
            hechos_s2 = {"y55": "For time 5 rondas: 5 ring muscle ups, 10 cal AAB, 20 wall balls 9/6 kg",
                         "y35": "5 rondas: 200 m row, 40 DUs, 2x 5 m DB farmer carry walking lunges 2x 32,5/22,5 kg, "
                                "10 T2B"}
            ajustes = rut.setdefault("ajustes", {})
            estados = rut.setdefault("estados", {})
            for d in rut.get("dias", []):
                for l, p in zip(d["lineas"], partes_del_dia(d)):
                    if l["id"] in hechos_s2 and not prescripcion_semana(l, 2, ajustes)[0]:
                        ajustes.setdefault("2", {})[l["id"]] = hechos_s2[l["id"]]
                        estados.setdefault(f"2|{d['id']}|{p}", {"estado": "hecho"})
            rut["migraciones"].append("wods_diego_s2")
        if "diego_s2_dias_1a5" not in rut.setdefault("migraciones", []):
            # Diego ya hizo los días 1 a 5 de la semana 2: se marcan como hechos (lo que ya estuviera marcado se respeta)
            from logica import agrupar_por_parte
            estados = rut.setdefault("estados", {})
            for d in rut.get("dias", []):
                if d["id"] in ("d1", "d2", "d3", "d4", "d5"):
                    for p, _ in agrupar_por_parte(d, 2):
                        estados.setdefault(f"2|{d['id']}|{p}", {"estado": "hecho"})
            rut["migraciones"].append("diego_s2_dias_1a5")
        # El día 5 repite la fuerza del día 3 (mismos pesos y repes): se iguala una vez.
        hechas = rut.setdefault("migraciones", [])
        if "d5_igual_d3" not in hechas:
            lineas = {l["id"]: l for d in rut.get("dias", []) for l in d["lineas"]}
            for de, a in (("y31", "y51"), ("y32", "y52"), ("y33", "y53"), ("y34", "y54")):
                if de in lineas and a in lineas:
                    for campo in ("prescripcion", "base", "sube"):
                        lineas[a][campo] = lineas[de].get(campo)
            hechas.append("d5_igual_d3")
        if "accessory_y_wod_d6" not in hechas:
            from logica import prescripcion_semana, rebasar, renombrar_parte
            actual = int(rut.get("semana_actual") or 1)
            for d in rut.get("dias", []):
                for l in d["lineas"]:
                    if l["id"] in ("y44", "y64") and float(l.get("sube") or 0):
                        rebasar(l, actual, prescripcion_semana(l, actual, None)[0], 0)
            d6 = next((d for d in rut.get("dias", []) if d["id"] == "d6"), None)
            if d6 and any(l["id"] == "y63" and l.get("parte") == "B) Conditioning" for l in d6["lineas"]):
                rut.update(renombrar_parte(rut, "d6", "B) Conditioning", "B) WOD"))
            rut.setdefault("migraciones", []).append("accessory_y_wod_d6")
    return rut
