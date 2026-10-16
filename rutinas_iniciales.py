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
                _l("y21", "Power snatch", "@40", base=b),
                _l("y22", "Squat clean", "@70", base=b),
                _l("y23", "Clean pull", "@100", base=b),
                _metcon("y24", "Gym / WOD", base=b),
            ]},
            {"id": "d3", "nombre": "Día 3", "lineas": [
                _l("y31", "Back squat", "@125", base=b),
                _l("y32", "Front squat", "@105", base=b),
                _l("y33", "Push press", "@65", base=b),
                _l("y34", "Bench press", "@50", base=b),
                _metcon("y35", "Conditioning", base=b),
            ]},
            {"id": "d4", "nombre": "Día 4", "lineas": [
                _l("y41", "3 hang power snatch + 1 squat snatch", "@40", base=b),
                _l("y42", "3 hang power clean + 1 squat clean", "", base=b),
                _l("y43", "Push press + push jerk + split jerk", "3x(1+1+1)", base=b),
                _l("y44", "Snatch deadlift", "", base=b, parte="B) Accessory"),
            ]},
            {"id": "d5", "nombre": "Día 5", "lineas": [
                _l("y51", "Back squat", "@120", base=b),
                _l("y52", "Front squat", "@100", base=b),
                _l("y53", "Push press", "@60", base=b),
                _l("y54", "Bench press", "", base=b),
                _metcon("y55", "Gym / WOD", base=b),
            ]},
            {"id": "d6", "nombre": "Día 6", "lineas": [
                _l("y61", "Snatch", "3@40 2@45 1@50", base=b),
                _l("y62", "Clean & jerk", "3@60 2@70 1@80", base=b),
                _metcon("y63", "EMOM 40'", "5x (10 thrusters + 5 burpees)", base=b, nota="¿40 min?", parte="B) Conditioning"),
                _l("y64", "Deadlift", "3x6 @140", base=b, parte="C) Accessory"),
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
            {"id": "d1", "nombre": "Día 1", "lineas": [
                _l("p11", "Squat snatch", "3x3 @20"),
                _l("p12", "Snatch pull", "3x3 @45"),
                _l("p13", "Back squat", "", nota="Semana 1: no hecho"),
                _metcon("p14", "WOD"),
            ]},
            {"id": "d2", "nombre": "Día 2", "lineas": [
                _l("p21", "Squat clean", "3x3 @30"),
                _l("p22", "Clean pull", "3x3 @50"),
                _l("p23", "Front squat", "", nota="Semana 1: no hecho"),
                _metcon("p24", "WOD / Gym"),
            ]},
            {"id": "d3", "nombre": "Día 3", "lineas": [
                _l("p31", "Jerk", "3x3 @20"),
                _l("p32", "Push press", "3x3 @25"),
                _metcon("p33", "Conditioning"),
            ]},
        ],
    }


def rutinas_iniciales(atletas: list[str]) -> dict:
    """Asocia por posición: 0 = yo, 1 = Manu, 3 = pareja. El resto empieza sin rutina."""
    fabricas = {0: _yo, 1: _manu, 3: _pareja}
    return {a: fabricas[i]() for i, a in enumerate(atletas) if i in fabricas}
