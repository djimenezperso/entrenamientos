"""Importar entrenos pegados (mensaje de WhatsApp, nota del móvil) o dictados, a los días de la semana.

Para perfiles con programa propio (p. ej. Wendy): reconoce los días («Lundi», «Martes», «Jour 2», «Día 3»…),
dentro de cada día las partes («A) …», «Force», «WOD»…), y quita los restos de WhatsApp (fecha, hora, nombre).
Si no hay ningún día escrito, todo va al día que está abierto.
"""
from __future__ import annotations

import re
import unicodedata

_DIAS = {
    0: ("lunes", "lundi", "monday", "lun"), 1: ("martes", "mardi", "tuesday", "mar"),
    2: ("miercoles", "mercredi", "wednesday", "mie", "mer"), 3: ("jueves", "jeudi", "thursday", "jue", "jeu"),
    4: ("viernes", "vendredi", "friday", "vie", "ven"), 5: ("sabado", "samedi", "saturday", "sab", "sam"),
    6: ("domingo", "dimanche", "sunday", "dom", "dim"),
}
# líneas de WhatsApp exportado: «[22/11/2026, 10:41:03] Wendy: …» o «22/11/2026 10:41 - Wendy: …»
_WA = re.compile(r"^\s*\[?\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\]?\s*(?:-\s*)?[^:\n]{1,40}:\s*")
_RESTOS = re.compile(r"[<‹][^<>\n]{0,60}?(?:modifi|edit|omit|omis|elimin|supprim|delet|borrad)[^<>\n]{0,40}[>›]|[‎‏‪-‮]", re.I)
_PARTE = re.compile(r"^\s*(?:([a-f])\s*[).:-]\s*(.*)|(fuerza|strength|force|wod|metcon|gym|accessory|accessoires?|conditioning|"
                    r"cardio|mobility|movilidad|mobilit[eé]|warm\s*-?\s*up|[eé]chauffement|calentamiento|skill|technique|t[eé]cnica)"
                    r"\s*:?\s*(.*))$", re.I)
_DIA_N = re.compile(r"^(?:d[ií]a|jour|day|j|d)\s*(\d)$", re.I)


def _plano(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _dia_de(linea: str) -> int | None:
    """Si la línea es una cabecera de día, su número (0 = lunes / día 1). Admite «Lundi :», «MARTES 25», «Jour 3 -»."""
    t = _plano(linea).strip(" \t*_~:-–—.!📅🗓")
    t = re.sub(r"\s*\d{1,2}([/.-]\d{1,2}([/.-]\d{2,4})?)?\s*$", "", t) if not _DIA_N.match(t) else t  # «Lundi 24/11»
    t = t.strip(" :-–—.")
    m = _DIA_N.match(t)
    if m:
        return int(m.group(1)) - 1
    for i, nombres in _DIAS.items():
        if t in nombres[:3]:
            return i
    return None


def limpiar(texto: str) -> str:
    lineas = []
    for l in (texto or "").replace("\r", "").split("\n"):
        l = _RESTOS.sub("", _WA.sub("", l)).rstrip()
        lineas.append(l)
    return "\n".join(lineas).strip()


def _partes(bloque: str) -> list[tuple[str, str]]:
    """[(etiqueta, texto)] de un día. Sin cabeceras de parte: una sola parte «WOD» con todo."""
    partes: list[list] = []
    for l in bloque.split("\n"):
        m = _PARTE.match(l)
        if m and (m.group(1) or len(l.strip()) <= 40):
            if m.group(1):  # «A) Back squat 5x5» o «B) WOD»
                resto = (m.group(2) or "").strip()
                eti, texto = (resto, "") if _PARTE.match(resto) and len(resto) <= 25 else ("", resto)
                partes.append([eti.rstrip(":"), texto])
            else:
                partes.append([m.group(3).strip(), (m.group(4) or "").strip()])
            continue
        if not partes:
            partes.append(["", ""])
        partes[-1][1] = (partes[-1][1] + "\n" + l).strip("\n")
    out = []
    for eti, txt in partes:
        txt = txt.strip()
        if not txt and not eti:
            continue
        if not eti:  # sin cabecera: «5x5 @70» es fuerza; lo demás, WOD
            eti = "Force" if re.search(r"\b\d+\s*x\s*\d+", txt) and not re.search(r"(?i)amrap|emom|for time|tours?|rounds?|rondas?", txt) else "WOD"
        eti = eti[:30].strip()
        out.append((eti.upper() if eti.lower() in ("wod", "emom", "amrap", "metcon") else eti[0].upper() + eti[1:], txt or eti))
    return out


def trocear(texto: str) -> dict[int | None, list[tuple[str, str]]]:
    """{número de día (o None si no se dijo): [(etiqueta, texto)…]}."""
    texto = limpiar(texto)
    dias: dict[int | None, list[str]] = {}
    actual: int | None = None
    for l in texto.split("\n"):
        d = _dia_de(l) if l.strip() and len(l.strip()) <= 30 else None
        if d is not None:
            actual = d
            dias.setdefault(actual, [])
            continue
        dias.setdefault(actual, []).append(l)
    out = {}
    for d, ls in dias.items():
        partes = _partes("\n".join(ls).strip())
        if partes:
            out[d] = partes
    return out
