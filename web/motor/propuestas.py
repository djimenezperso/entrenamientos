"""Rutinas preparadas para un alumno concreto. Diego las ve al entrar en su rutina (modo coach) y decide si aplicarlas.
Clave: nombre del perfil en minúsculas (vale con que empiece así, p. ej. «ruchama»)."""


def _l(i, ejercicio, presc="", sube=0.0, parte="A) Fuerza", nota=""):
    return {"id": i, "ejercicio": ejercicio, "prescripcion": presc, "sube": sube, "nota": nota, "parte": parte}


def _ruchama():
    """Ruchama: no principiante, gym normal. 3 días: WOD en la B y accessory en la C los días 1 y 3;
    el día del medio, fuerza + conditioning largo. Sin snatch con barra: DB snatch ligero."""
    return {
        "id": "ruchama-v1",
        "titulo": "3 días · WOD + accessory · día del medio fuerza + conditioning largo",
        "nivel": "Inter",
        "dias": [
            {"id": "r1", "nombre": "Día 1", "por_ejercicio": True, "lineas": [
                _l("r11", "Back squat", "4x6 @40", 2.5),
                _l("r12", "DB bench press", "4x8 @12"),
                _l("r13", "WOD", "AMRAP 14': 10 DB snatch alternos @10, 12 wall balls 6 kg, 250 m row", parte="B) WOD"),
                _l("r14", "Back extension", "3x12 lento", parte="C) Accessory"),
                _l("r15", "DB row", "3x10 por brazo @12", parte="C) Accessory"),
                _l("r16", "Plank", "3x40\"", parte="C) Accessory"),
            ]},
            {"id": "r2", "nombre": "Día 2", "por_ejercicio": True, "lineas": [
                _l("r21", "Romanian deadlift", "4x8 @40", 2.5),
                _l("r22", "Strict press", "4x6 @20", 2.5),
                _l("r23", "Conditioning", "5 rondas: 500 m row, 1000 m bike, 200 m run · descanso 1:30 (ritmo que aguantes todo)",
                   parte="B) Conditioning"),
            ]},
            {"id": "r3", "nombre": "Día 3", "por_ejercicio": True, "lineas": [
                _l("r31", "Hip thrust", "4x8 @50", 2.5),
                _l("r32", "DB push press", "4x8 @10"),
                _l("r33", "WOD", "For time 4 rondas: 15 KB swings 12 kg, 12 box step ups, 9 DB push press @8, 200 m run · cap 16'",
                   parte="B) WOD"),
                _l("r34", "Bulgarian split squat DB", "3x8 por pierna @8", parte="C) Accessory"),
                _l("r35", "Face pulls con banda", "3x15", parte="C) Accessory"),
                _l("r36", "Hollow hold", "3x30\"", parte="C) Accessory"),
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
