"""Rutinas preparadas para un alumno concreto. Diego las ve al entrar en su rutina (modo coach) y decide si aplicarlas.
Clave: nombre del perfil en minúsculas (vale con que empiece así, p. ej. «ruchama»)."""


def _l(i, ejercicio, presc="", sube=0.0, parte="A) Fuerza", nota=""):
    return {"id": i, "ejercicio": ejercicio, "prescripcion": presc, "sube": sube, "nota": nota, "parte": parte}


def _ruchama():
    """Ruchama: no principiante, gym normal. 3 días: WOD en la B y accessory en la C los días 1 y 3;
    el día del medio, fuerza + conditioning largo. Sin snatch con barra: DB snatch ligero."""
    return {
        "id": "ruchama-v3",
        "sugerir": True,  # le sale a ella: «Diego te sugiere este cambio» → Aceptar / Ahora no
        "titulo": "3 días · WOD + accessory · día del medio fuerza + conditioning largo",
        "nivel": "Inter",
        "dias": [
            {"id": "r1", "nombre": "Jour 1", "por_ejercicio": True, "lineas": [
                _l("r11", "Back squat", "4x6 @40", 2.5),
                _l("r12", "DB bench press", "4x8 @12"),
                _l("r13", "WOD", "AMRAP 14' : 10 DB snatch alternés @10, 12 wall balls 6 kg, 250 m rameur", parte="B) WOD"),
                _l("r14", "Back extension", "4x12 lent", parte="C) Accessory"),
            ]},
            {"id": "r2", "nombre": "Jour 2", "por_ejercicio": True, "lineas": [
                _l("r21", "Romanian deadlift", "4x8 @40", 2.5),
                _l("r22", "Strict press", "4x6 @20", 2.5),
                _l("r23", "Conditioning", "5 tours : 500 m rameur, 1000 m bike, 200 m course · repos 1:30 (un rythme que tu tiens jusqu'au bout)",
                   parte="B) Conditioning"),
            ]},
            {"id": "r3", "nombre": "Jour 3", "por_ejercicio": True, "lineas": [
                _l("r31", "Hip thrust", "4x8 @50", 2.5),
                _l("r32", "DB push press", "4x8 @10"),
                _l("r33", "WOD", "For time 4 tours : 15 KB swings 12 kg, 12 box step ups, 9 DB push press @8, 200 m course · cap 16'",
                   parte="B) WOD"),
                _l("r34", "Bulgarian split squat DB", "4x8 par jambe @8", parte="C) Accessory"),
            ]},
        ],
    }


def manu_villalobos():
    """Manu Villalobos (perfil nuevo que crea Diego). 3 días:
    1) back + front + push press, WOD de halterofilia, accessory · 2) snatch, clean & jerk, conditioning, accessory
    3) back + front + push press, WOD de mancuernas, accessory. Pesos de partida orientativos: Diego los ajusta."""
    return {
        "semana_actual": 1, "ajustes": {}, "nivel": "Inter",
        "dias": [
            {"id": "v1", "nombre": "Día 1", "por_ejercicio": True, "lineas": [
                _l("v11", "Back squat", "5x5 @80", 2.5),
                _l("v12", "Front squat", "3x5 @65", 2.5),
                _l("v13", "Push press", "4x5 @50", 2.5),
                _l("v14", "WOD haltero", "AMRAP 12': 5 power cleans 61/43 kg, 7 front squats 61/43 kg, 9 bar-facing burpees",
                   parte="B) WOD"),
                _l("v15", "Back extension", "4x12 lentas · 1' descanso", parte="C) Accessory"),
            ]},
            {"id": "v2", "nombre": "Día 2", "por_ejercicio": True, "lineas": [
                _l("v21", "Snatch", "5x2 @50", 2.5),
                _l("v22", "Clean and jerk", "5x1+1 @70", 2.5),
                _l("v23", "Conditioning", "5 rondas: 500 m row, 15 cal bike · descanso 1:30 (ritmo que aguantes hasta el final)",
                   parte="B) Conditioning"),
                _l("v24", "Bulgarian split squat DB", "4x10 por pierna @15", parte="C) Accessory"),
            ]},
            {"id": "v3", "nombre": "Día 3", "por_ejercicio": True, "lineas": [
                _l("v31", "Back squat", "3x8 @70", 2.5),
                _l("v32", "Front squat", "4x3 @70", 2.5),
                _l("v33", "Push press", "5x3 @55", 2.5),
                _l("v34", "WOD mancuernas", "AMRAP 14': 10 DB snatch alternos 22,5/15 kg, 10 DB box step-overs 22,5/15 kg, "
                                            "10 DB push press 22,5/15 kg", parte="B) WOD"),
                _l("v35", "Plank con disco", "4x40\" · 1' descanso", parte="C) Accessory"),
            ]},
        ],
    }


PROPUESTAS = {"ruchama": _ruchama}


def claves() -> list[str]:
    return list(PROPUESTAS)


def propuesta_para(nombre: str) -> dict | None:
    n = (nombre or "").strip().lower()
    for clave, f in PROPUESTAS.items():
        if n.startswith(clave):
            return f()
    return None
