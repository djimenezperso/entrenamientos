"""Comida: calorías y macros del día con datos fijos (tabla de alimentos propia, sin IA).

Cada atleta tiene su dieta (peso, objetivo, tipo de dieta y lo que no come) y su diario del día.
Es de pago: la ven Diego, los coach, la demo, los abonados que pagan y quien Diego desbloquee.
Se guarda en la tabla `rutinas` con la clave «__comida__·<atleta>».
"""
from __future__ import annotations

import datetime as dt
import uuid

import recetas
import servicio as s

PREFIJO = "__comida__·"
DIAS_GUARDADOS = 35

OBJETIVOS = {"perder": ("Perder grasa", 28), "mantener": ("Mantener", 32), "ganar": ("Ganar músculo", 36)}
# proteína y grasa en g por kg de peso; el resto de calorías van a hidratos
DIETAS = {
    "equilibrada": ("Equilibrada", 1.8, 1.0),
    "proteina": ("Más proteína", 2.2, 0.9),
    "menos_hc": ("Menos hidratos", 2.0, 1.4),
    "vegetariana": ("Vegetariana", 1.8, 1.0),
}
DESCANSO_MENOS = 300  # kcal menos los días sin entreno (salen de los hidratos)
COMIDAS = [("desayuno", "Desayuno", .25), ("comida", "Comida", .35), ("merienda", "Merienda", .15), ("cena", "Cena", .25)]
EXCLUSIONES = {"carne": "Carne", "pescado": "Pescado", "marisco": "Marisco", "lacteos": "Lácteos", "huevo": "Huevo",
               "gluten": "Gluten", "frutos_secos": "Frutos secos"}

# alimento: (nombre, ración, kcal, proteína, hidratos, grasa, grupo, etiquetas)
ALIMENTOS = {
    "avena": ("Copos de avena", "60 g", 225, 8, 36, 4, "Cereales", ("gluten",)),
    "pan": ("Pan integral", "2 rebanadas · 60 g", 150, 6, 26, 2, "Cereales", ("gluten",)),
    "arroz": ("Arroz cocido", "1 plato · 200 g", 260, 5, 56, 1, "Cereales", ()),
    "pasta": ("Pasta cocida", "1 plato · 200 g", 300, 11, 60, 2, "Cereales", ("gluten",)),
    "patata": ("Patata cocida", "250 g", 200, 5, 43, 0, "Cereales", ()),
    "boniato": ("Boniato asado", "200 g", 180, 3, 41, 0, "Cereales", ()),
    "tortitas": ("Tortitas de arroz", "4 unidades", 140, 3, 30, 1, "Cereales", ()),
    "pollo": ("Pechuga de pollo", "150 g", 165, 35, 0, 3, "Proteína", ("carne",)),
    "pavo": ("Pavo en filetes", "150 g", 160, 34, 0, 2, "Proteína", ("carne",)),
    "ternera": ("Ternera magra", "150 g", 220, 32, 0, 10, "Proteína", ("carne",)),
    "salmon": ("Salmón", "150 g", 300, 30, 0, 20, "Proteína", ("pescado",)),
    "atun": ("Atún al natural", "1 lata · 80 g", 90, 20, 0, 1, "Proteína", ("pescado",)),
    "merluza": ("Merluza", "200 g", 170, 36, 0, 2, "Proteína", ("pescado",)),
    "gambas": ("Gambas", "150 g", 150, 30, 0, 2, "Proteína", ("marisco",)),
    "huevos": ("Huevos", "2 unidades", 150, 13, 1, 10, "Proteína", ("huevo",)),
    "claras": ("Claras de huevo", "200 ml", 100, 22, 1, 0, "Proteína", ("huevo",)),
    "tofu": ("Tofu firme", "150 g", 190, 20, 3, 11, "Proteína", ()),
    "lentejas": ("Lentejas cocidas", "1 plato · 250 g", 290, 22, 45, 1, "Proteína", ()),
    "garbanzos": ("Garbanzos cocidos", "1 plato · 250 g", 340, 18, 50, 6, "Proteína", ()),
    "proteina": ("Batido de proteína", "1 cacito · 30 g", 120, 24, 3, 2, "Proteína", ("lacteos",)),
    "proteina_veg": ("Proteína vegetal", "1 cacito · 30 g", 115, 22, 4, 2, "Proteína", ()),
    "yogur": ("Yogur griego natural", "125 g", 120, 10, 5, 7, "Lácteos", ("lacteos",)),
    "skyr": ("Skyr o yogur proteico", "150 g", 95, 16, 6, 0, "Lácteos", ("lacteos",)),
    "leche": ("Leche semidesnatada", "1 vaso · 250 ml", 115, 8, 12, 4, "Lácteos", ("lacteos",)),
    "bebida_veg": ("Bebida de soja", "1 vaso · 250 ml", 85, 8, 3, 4, "Lácteos", ()),
    "queso_fresco": ("Queso fresco batido", "150 g", 70, 12, 5, 0, "Lácteos", ("lacteos",)),
    "platano": ("Plátano", "1 mediano", 105, 1, 27, 0, "Fruta y verdura", ()),
    "manzana": ("Manzana", "1 mediana", 80, 0, 21, 0, "Fruta y verdura", ()),
    "frutos_rojos": ("Frutos rojos", "150 g", 70, 1, 15, 0, "Fruta y verdura", ()),
    "verdura": ("Verdura variada", "1 plato · 250 g", 80, 4, 12, 1, "Fruta y verdura", ()),
    "ensalada": ("Ensalada con tomate", "1 bol", 60, 2, 8, 2, "Fruta y verdura", ()),
    "aguacate": ("Aguacate", "½ unidad · 70 g", 115, 1, 6, 10, "Grasas", ()),
    "aceite": ("Aceite de oliva", "1 cucharada · 10 ml", 90, 0, 0, 10, "Grasas", ()),
    "frutos_secos": ("Frutos secos", "1 puñado · 30 g", 180, 6, 6, 15, "Grasas", ("frutos_secos",)),
    "crema_cacahuete": ("Crema de cacahuete", "1 cucharada · 15 g", 95, 4, 3, 8, "Grasas", ("frutos_secos",)),
    "chocolate": ("Chocolate negro 85 %", "2 onzas · 20 g", 120, 2, 4, 10, "Grasas", ()),
    "miel": ("Miel", "1 cucharada · 20 g", 60, 0, 16, 0, "Grasas", ()),
    "cereales": ("Cereales de desayuno", "40 g", 150, 3, 33, 1, "Cereales", ("gluten",)),
    "galletas": ("Galletas", "4 unidades · 40 g", 190, 3, 28, 7, "Cereales", ("gluten",)),
    "zumo": ("Zumo de naranja", "1 vaso · 200 ml", 90, 1, 20, 0, "Fruta y verdura", ()),
    "jamon": ("Jamón serrano", "40 g", 95, 13, 0, 5, "Proteína", ("carne",)),
    "york": ("Jamón cocido", "60 g", 70, 11, 1, 2, "Proteína", ("carne",)),
    "queso": ("Queso curado", "30 g", 120, 8, 0, 10, "Lácteos", ("lacteos",)),
    "pizza": ("Pizza", "½ pizza · 200 g", 520, 22, 62, 20, "Otros", ("gluten", "lacteos")),
    "hamburguesa": ("Hamburguesa con pan", "1 unidad", 550, 28, 40, 30, "Otros", ("carne", "gluten")),
    "cafe_leche": ("Café con leche", "1 taza", 60, 4, 6, 2, "Lácteos", ("lacteos",)),
}
# ideas fijas por comida: lista de alimentos; se usa la primera que no choque con lo que no come
IDEAS = {
    "desayuno": [["avena", "leche", "platano"], ["yogur", "cereales", "frutos_rojos"], ["pan", "aguacate", "claras"], ["pan", "huevos", "manzana"], ["avena", "bebida_veg", "frutos_rojos"], ["tortitas", "crema_cacahuete", "platano"]],
    "comida": [["arroz", "pollo", "verdura", "aceite"], ["patata", "ternera", "ensalada", "aceite"], ["garbanzos", "pollo", "verdura"], ["pasta", "atun", "ensalada", "aceite"], ["lentejas", "arroz", "verdura"], ["patata", "tofu", "verdura", "aceite"]],
    "merienda": [["skyr", "miel", "platano"], ["pan", "jamon", "zumo"], ["yogur", "frutos_secos", "manzana"], ["pan", "atun", "manzana"], ["proteina_veg", "bebida_veg", "platano"], ["tortitas", "crema_cacahuete"]],
    "cena": [["salmon", "boniato", "ensalada"], ["merluza", "patata", "verdura", "aceite"], ["pavo", "arroz", "verdura", "aceite"], ["huevos", "pan", "verdura", "aceite"], ["tofu", "verdura", "patata", "aceite"], ["garbanzos", "ensalada", "aceite"]],
}


# gramos o mililitros de una ración, para entender «200 g de arroz»; y unidades por ración («un huevo» = ½ ración)
GRAMOS = {"avena": 60, "pan": 60, "arroz": 200, "pasta": 200, "patata": 250, "boniato": 200, "pollo": 150, "pavo": 150,
          "ternera": 150, "salmon": 150, "atun": 80, "merluza": 200, "gambas": 150, "claras": 200, "tofu": 150, "lentejas": 250,
          "garbanzos": 250, "proteina": 30, "proteina_veg": 30, "yogur": 125, "skyr": 150, "leche": 250, "bebida_veg": 250,
          "queso_fresco": 150, "frutos_rojos": 150, "verdura": 250, "aguacate": 70, "aceite": 10, "frutos_secos": 30,
          "crema_cacahuete": 15, "chocolate": 20, "ensalada": 200, "miel": 20, "cereales": 40, "galletas": 40, "zumo": 200, "jamon": 40,
          "york": 60, "queso": 30, "pizza": 200}
UNIDADES = {"huevos": 2, "pan": 2, "tortitas": 4, "galletas": 4, "platano": 1, "manzana": 1}
# palabras que se dicen → alimento (se busca la más larga primero)
SINONIMOS = {
    "avena": ["copos de avena", "avena", "porridge", "flocons d'avoine"],
    "pan": ["tostadas", "tostada", "pan integral", "pan", "rebanadas de pan", "rebanada", "bocadillo", "pain", "tartine"],
    "arroz": ["arroz", "riz"], "pasta": ["pasta", "macarrones", "espaguetis", "spaghetti", "fideos", "pâtes"],
    "patata": ["patatas", "patata", "papas", "pommes de terre"], "boniato": ["boniato", "batata", "patate douce"],
    "tortitas": ["tortitas de arroz", "tortitas", "galettes de riz"],
    "pollo": ["pechuga de pollo", "pollo", "poulet"], "pavo": ["pavo", "dinde"], "ternera": ["ternera", "filete", "carne picada", "carne", "bœuf", "steak"],
    "salmon": ["salmón", "salmon", "saumon"], "atun": ["atún", "atun", "thon"], "merluza": ["merluza", "pescado blanco", "pescado", "poisson", "cabillaud"],
    "gambas": ["gambas", "langostinos", "crevettes"], "huevos": ["tortilla francesa", "huevos", "huevo", "œufs", "oeufs", "œuf"],
    "claras": ["claras de huevo", "claras", "blancs d'œuf"], "tofu": ["tofu"], "lentejas": ["lentejas", "lentilles"],
    "garbanzos": ["garbanzos", "hummus", "pois chiches"], "proteina": ["batido de proteína", "batido de proteinas", "batido", "proteína", "proteina", "whey", "shaker"],
    "proteina_veg": ["proteína vegetal", "proteina vegetal"], "yogur": ["yogur griego", "yogures", "yogur", "yaourt"],
    "skyr": ["skyr", "yogur proteico"], "leche": ["vaso de leche", "leche", "lait"], "bebida_veg": ["bebida de soja", "leche de soja", "bebida vegetal", "leche de avena", "lait d'amande"],
    "queso_fresco": ["queso fresco batido", "queso batido", "queso fresco", "fromage blanc"], "platano": ["plátanos", "plátano", "platano", "banana", "banane"],
    "manzana": ["manzanas", "manzana", "fruta", "pera", "naranja", "pomme", "fruit"], "frutos_rojos": ["frutos rojos", "fresas", "arándanos", "fruits rouges"],
    "verdura": ["verduras", "verdura", "brócoli", "brocoli", "judías verdes", "espinacas", "légumes"], "ensalada": ["ensalada", "salade"],
    "aguacate": ["aguacate", "avocat"], "aceite": ["aceite de oliva", "aceite", "huile"], "frutos_secos": ["frutos secos", "nueces", "almendras", "noix", "amandes"],
    "crema_cacahuete": ["crema de cacahuete", "mantequilla de cacahuete", "beurre de cacahuète"], "chocolate": ["chocolate", "chocolat"], "miel": ["miel"],
    "cereales": ["cereales", "muesli", "granola", "céréales"], "galletas": ["galletas", "biscuits"], "zumo": ["zumo", "jugo", "jus d'orange", "jus"],
    "jamon": ["jamón serrano", "jamón", "jamon", "jambon cru"], "york": ["jamón york", "jamón cocido", "jambon"], "queso": ["queso", "fromage"],
    "pizza": ["pizza"], "hamburguesa": ["hamburguesa", "burger"], "cafe_leche": ["café con leche", "cortado", "café au lait", "café crème"],
}
NUMEROS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "medio": .5, "media": .5,
           "un par de": 2, "unos": 2, "unas": 2, "un": 1, "une": 1, "deux": 2, "trois": 3, "demi": .5, "doble": 2, "mucho": 1.5, "mucha": 1.5,
           "poco": .5, "poca": .5, "grande": 1.5, "pequeño": .7, "pequeña": .7}
PALABRAS_COMIDA = {"desayuno": "desayuno", "desayuno:": "desayuno", "por la mañana": "desayuno", "petit-déjeuner": "desayuno", "petit déjeuner": "desayuno",
                   "almuerzo": "comida", "comida": "comida", "mediodía": "comida", "a mediodía": "comida", "déjeuner": "comida",
                   "merienda": "merienda", "antes de entrenar": "merienda", "pre entreno": "merienda", "goûter": "merienda",
                   "cena": "cena", "por la noche": "cena", "dîner": "cena"}


ENVASES = {"de", "plato", "platos", "vaso", "vasos", "bol", "boles", "taza", "tazas", "lata", "latas", "puñado", "puñados", "cucharada",
           "cucharadas", "cacito", "cacitos", "trozo", "trozos", "loncha", "lonchas", "ración", "raciones", "pieza", "piezas", "con", "y"}


def _normal(txt: str) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", (txt or "").lower().replace(",", " , ").replace(".", " . ").replace(";", " , ")).strip()


def interpretar(texto: str, comida_def: str | None = None) -> dict:
    """De lo que se dice («dos huevos y una tostada; a mediodía arroz con pollo») a alimentos y raciones, por comida."""
    import re as _re
    txt = " " + _normal(texto) + " "
    # cortar por comidas
    marcas = []
    for w, cid in sorted(PALABRAS_COMIDA.items(), key=lambda x: -len(x[0])):
        for m in _re.finditer(r"(?<![\w])" + _re.escape(w) + r"(?![\w])", txt):
            if not any(a <= m.start() < b for a, b, _ in marcas):
                marcas.append((m.start(), m.end(), cid))
    marcas.sort()
    trozos = []
    if not marcas or marcas[0][0] > 3:
        trozos.append((comida_def or "comida", txt[: marcas[0][0]] if marcas else txt))
    for i, (a, b, cid) in enumerate(marcas):
        trozos.append((cid, txt[b: marcas[i + 1][0] if i + 1 < len(marcas) else len(txt)]))
    lista = sorted(((w, k) for k, ws in SINONIMOS.items() for w in ws), key=lambda x: -len(x[0]))
    out, entendidos = [], 0
    for cid, trozo in trozos:
        usado = [False] * len(trozo)
        for w, k in lista:
            for m in _re.finditer(r"(?<![\w])" + _re.escape(w) + r"(?![\w])", trozo):
                if any(usado[m.start():m.end()]):
                    continue
                for i in range(m.start(), m.end()):
                    usado[i] = True
                antes = trozo[max(0, m.start() - 28): m.start()]
                rac = 1.0
                g = _re.search(r"(\d+(?:[.,]\d+)?)\s*(g|gr|gramos|ml|grammes)\b(?:\s+de)?\s*$", antes)
                n = _re.search(r"(\d+(?:[.,]\d+)?)\s*(?:\w+\s+de\s+)?$", antes)
                palabra = _re.search(r"(un par de|\w+)\s+(?:(?:plato|vaso|bol|taza|lata|puñado|cucharada|cacito|trozo|loncha|lonchas)s?\s+(?:de\s+)?)?(?:\w+\s+)?$", antes)
                if g and k in GRAMOS:
                    rac = float(g.group(1).replace(",", ".")) / GRAMOS[k]
                elif n:
                    v = float(n.group(1).replace(",", "."))
                    rac = v / UNIDADES.get(k, 1) if k in UNIDADES else v
                else:
                    ws = antes.replace(",", " ").split()
                    while ws and ws[-1] in ENVASES:
                        ws.pop()
                    w2 = "un par de" if antes.rstrip().endswith("un par de") else (ws[-1] if ws else "")
                    if w2 in NUMEROS:
                        v = NUMEROS[w2]
                        rac = v / UNIDADES[k] if k in UNIDADES and v >= 1 else v
                if _re.search(r"\b(grande|doble|mucho|mucha)\b", trozo[m.end(): m.end() + 14]):
                    rac *= 1.5
                rac = max(.25, min(6, round(rac * 4) / 4))
                out.append({"comida": cid, "alimento": k, "raciones": rac, "nombre": ALIMENTOS[k][0], "racion": ALIMENTOS[k][1]})
                entendidos += 1
    for it in out:
        it.update(_sumar([it]))
    return {"items": out, "entendidos": entendidos}


NOM_FR = {"desayuno": "petit-déjeuner", "comida": "repas", "merienda": "goûter", "cena": "dîner"}
_A_FR = {"desayuno": "au petit-déjeuner", "comida": "au repas", "merienda": "au goûter", "cena": "au dîner"}


def _f(nombre: str) -> str:
    """Nombre de alimento para el texto en francés: la app lo traduce (⟨…⟩ → t(…))."""
    return f"⟨{nombre}⟩"


def consejos(items: list[dict], obj: dict, entreno: bool, dieta: dict) -> list[dict]:
    """Reparto y recomendaciones fijas a partir de lo que suele comer (en español y en francés)."""
    if not obj or not items:
        return []
    ex = _excluidos(dieta)
    por = {cid: _sumar([i for i in items if i["comida"] == cid]) for cid, _, _ in COMIDAS}
    tot = _sumar(items)
    nom = {cid: n for cid, n, _ in COMIDAS}
    out = []

    def add(tipo, tit, txt, tit_fr, txt_fr):
        out.append({"tipo": tipo, "titulo": tit, "texto": txt, "titulo_fr": tit_fr, "texto_fr": txt_fr})

    dif = tot["kcal"] - obj["kcal"]
    if abs(dif) > obj["kcal"] * .1:
        n_ = abs(round(dif / 50) * 50)
        add("aviso", f"Comes unas {n_} kcal {'de más' if dif > 0 else 'de menos'}",
            "Para tu objetivo te sobran: quita media ración de hidratos en la cena o el aceite de más." if dif > 0 else
            "Te quedas corto: suma una ración de hidratos en la comida o una merienda más completa.",
            f"Tu manges environ {n_} kcal {'de trop' if dif > 0 else 'de moins'}",
            "C'est trop pour ton objectif : enlève une demi-portion de glucides au dîner ou l'huile en trop." if dif > 0 else
            "Il t'en manque : ajoute une portion de glucides au repas ou un goûter plus complet.")
    else:
        add("ok", "Las calorías te cuadran", f"Unas {tot['kcal']} kcal para {obj['kcal']} que te tocan.",
            "Tes calories sont bonnes", f"Environ {tot['kcal']} kcal sur les {obj['kcal']} prévues.")
    if tot["p"] < obj["p"] * .85:
        falta = round((obj["p"] - tot["p"]) / 5) * 5
        baja = min((cid for cid, _, _ in COMIDAS), key=lambda c: por[c]["p"])
        sug = next((a for a in (["skyr", "yogur", "claras", "proteina_veg"] if baja in ("desayuno", "merienda") else ["pollo", "atun", "tofu", "lentejas"])
                    if not set(ALIMENTOS[a][7]) & ex), None)
        add("aviso", f"Te faltan unos {falta} g de proteína",
            f"Donde menos llevas es en {nom[baja].lower()}" + (f": añade {ALIMENTOS[sug][0].lower()} ({ALIMENTOS[sug][1]})." if sug else "."),
            f"Il te manque environ {falta} g de protéines",
            f"C'est {_A_FR[baja]} que tu en as le moins" + (f" : ajoute {_f(ALIMENTOS[sug][0])} ({ALIMENTOS[sug][1]})." if sug else "."))
    else:
        add("ok", "Proteína bien", f"{tot['p']} g de {obj['p']} g.", "Protéines au top", f"{tot['p']} g sur {obj['p']} g.")
    for cid, n, parte in COMIDAS:
        k = por[cid]["kcal"]
        if not k:
            idea = _idea(cid, ex)
            kc = round(obj['kcal'] * parte / 10) * 10
            add("aviso", f"No haces {n.lower()}", f"Te tocarían unas {kc} kcal." + (f" Idea: {', '.join(idea).lower()}." if idea else ""),
                f"Pas de {NOM_FR[cid]}", f"Il te faudrait environ {kc} kcal." + (f" Idée : {', '.join(_f(x) for x in idea)}." if idea else ""))
        elif tot["kcal"] and k > tot["kcal"] * .45:
            add("aviso", f"{n} se lleva casi la mitad del día",
                f"Pasa parte a {'la merienda' if cid != 'merienda' else 'la cena'}: llegarás con más energía y sin pesadez.",
                f"Le {NOM_FR[cid]} prend presque la moitié de la journée",
                f"Passe-en une partie {'au goûter' if cid != 'merienda' else 'au dîner'} : tu auras plus d'énergie et moins de lourdeur.")
    if entreno and por["merienda"]["h"] < 25:
        sug = next((a for a in ("platano", "tortitas", "pan", "miel") if not set(ALIMENTOS[a][7]) & ex), None)
        add("aviso", "Antes de entrenar, más hidratos", f"En la merienda llevas {por['merienda']['h']} g." + (f" Suma {ALIMENTOS[sug][0].lower()}." if sug else ""),
            "Avant l'entraînement, plus de glucides", f"Au goûter tu en as {por['merienda']['h']} g." + (f" Ajoute {_f(ALIMENTOS[sug][0])}." if sug else ""))
    if tot["g"] > obj["g"] * 1.3:
        add("aviso", "Mucha grasa", "Mide el aceite con cuchara y deja los frutos secos en un puñado.",
            "Beaucoup de lipides", "Mesure l'huile à la cuillère et limite les fruits secs à une poignée.")
    if dieta.get("tipo") == "menos_hc" and tot["h"] > obj["h"] * 1.2:
        add("aviso", "Muchos hidratos para tu dieta", "Cambia el pan o la pasta de la cena por verdura y algo de proteína.",
            "Beaucoup de glucides pour ton régime", "Remplace le pain ou les pâtes du dîner par des légumes et un peu de protéines.")
    return out


def _cantidad(k: str, rac: float) -> str:
    """Cómo decir la cantidad: «150 g», «2 huevos», «1 vaso · 250 ml»."""
    if k in UNIDADES:
        n = rac * UNIDADES[k]
        nombre = {"huevos": "huevo", "pan": "rebanada", "tortitas": "tortita", "galletas": "galleta", "platano": "plátano", "manzana": "pieza de fruta"}[k]
        if k == "manzana" and n != 1:
            return f"{n:g} piezas de fruta".replace(".", ",")
        return f"{n:g} {nombre}{'s' if n != 1 else ''}".replace(".", ",")
    if k in GRAMOS:
        ml = k in ("leche", "bebida_veg", "zumo", "claras", "aceite")
        g = round(GRAMOS[k] * rac / 5) * 5
        return f"{g} {'ml' if ml else 'g'}"
    txt = {.5: "media ración", 1: "1 ración", 1.5: "ración y media", 2: "2 raciones"}.get(rac) or f"{rac:g} raciones".replace(".", ",")
    return f"{txt} ({ALIMENTOS[k][1]})"


def _escalar(op: list[str], cid: str, meta_kcal: float, meta_p: float, ex: set[str]) -> dict:
    base = sum(ALIMENTOS[a][2] for a in op)
    f = meta_kcal / base if base else 1
    items = []
    for a in op:
        fa = f if ALIMENTOS[a][6] != "Grasas" else min(f, 1.5)  # el aceite y los frutos secos no se disparan
        rac = max(.5, min(3, round(fa * 4) / 4))
        if a in UNIDADES:  # unidades enteras: nada de «1,5 huevos»
            rac = max(1, round(rac * UNIDADES[a])) / UNIDADES[a]
        items.append({"comida": cid, "alimento": a, "raciones": rac})
    p = _sumar(items)["p"]
    if p < meta_p * .7:  # se queda corta de proteína: se le suma algo proteico que pueda comer
        extra = next((a for a in (("skyr", "proteina", "claras", "proteina_veg") if cid in ("desayuno", "merienda")
                                  else ("pollo", "atun", "tofu", "claras")) if a not in op and not set(ALIMENTOS[a][7]) & ex), None)
        if extra:
            items.append({"comida": cid, "alimento": extra, "raciones": max(.5, min(2, round((meta_p - p) / ALIMENTOS[extra][3] * 2) / 2))})
    for it in items:
        it.update(_sumar([it]), nombre=ALIMENTOS[it["alimento"]][0], cantidad=_cantidad(it["alimento"], it["raciones"]), grupo=ALIMENTOS[it["alimento"]][6])
    return {"items": items, **_sumar(items), "titulo": ", ".join(ALIMENTOS[a][0] for a in op[:2]),
            "receta": recetas.receta(op, items)}


def plan_dia(dieta: dict, obj: dict) -> list[dict]:
    """Ideas de menú orientativas: varias opciones por comida, con cantidades ajustadas a sus calorías y proteína.
    No es una dieta de dietista: es una guía con datos fijos."""
    if not obj:
        return []
    ex = _excluidos(dieta)
    hoy = dt.date.today().weekday()
    plan = []
    for cid, nombre, parte in COMIDAS:
        ops = [op for op in IDEAS.get(cid, []) if not any(set(ALIMENTOS[a][7]) & ex for a in op)]
        if not ops:
            continue
        ops = ops[hoy % len(ops):] + ops[:hoy % len(ops)]  # cada día empieza por una distinta
        plan.append({"id": cid, "nombre": nombre, "kcal_meta": round(obj["kcal"] * parte),
                     "opciones": [_escalar(op, cid, obj["kcal"] * parte, obj["p"] * parte, ex) for op in ops]})
    return plan


def _clave(atleta: str) -> str:
    return PREFIJO + atleta


def _hoy() -> str:
    return dt.date.today().isoformat()


def _doc(atleta: str) -> dict:
    return s.datos().rutinas([_clave(atleta)]).get(_clave(atleta)) or {}


def _permitido(sesion: dict, atleta: str, doc: dict) -> bool:
    """Es de pago: entran Diego, el coach, la demo (solo mirar), quien paga su abono y a quien Diego se lo da."""
    if s.es_demo(sesion) or s.es_coach(sesion) or sesion.get("y") or atleta == "Yo":
        return True
    return _paga(atleta, doc)


def _paga(atleta: str, doc: dict) -> bool:
    if doc.get("permitido") or atleta == "Yo":
        return True
    try:
        inv = s.invitados()
        x = inv.get(atleta) or {}
        if x.get("stripe_estado") in s.ESTADOS_PAGANDO:
            return True
        p = s.estado_prueba(atleta, inv)
        if p and p.get("pagando"):
            return True
        return s.paga_fijo(atleta)
    except Exception:  # noqa: BLE001
        return False


def _excluidos(dieta: dict) -> set[str]:
    ex = set(dieta.get("no_come") or [])
    if dieta.get("tipo") == "vegetariana":
        ex |= {"carne", "pescado", "marisco"}
    return ex


def _objetivo_dia(dieta: dict, entreno: bool) -> dict:
    peso = float(dieta.get("peso") or 0)
    if peso <= 0:
        return {}
    obj = OBJETIVOS.get(dieta.get("objetivo") or "mantener", OBJETIVOS["mantener"])
    _, gp, gg = DIETAS.get(dieta.get("tipo") or "equilibrada", DIETAS["equilibrada"])
    kcal = peso * obj[1] - (0 if entreno else DESCANSO_MENOS)
    p, g = round(peso * gp), round(peso * gg)
    h = max(50, round((kcal - p * 4 - g * 9) / 4))
    return {"kcal": round(p * 4 + h * 4 + g * 9), "p": p, "h": h, "g": g}


def _sumar(items: list[dict]) -> dict:
    tot = {"kcal": 0.0, "p": 0.0, "h": 0.0, "g": 0.0}
    for it in items:
        a = ALIMENTOS.get(it.get("alimento"))
        if not a:
            continue
        r = float(it.get("raciones") or 1)
        tot["kcal"] += a[2] * r
        tot["p"] += a[3] * r
        tot["h"] += a[4] * r
        tot["g"] += a[5] * r
    return {k: round(v) for k, v in tot.items()}


def _idea(comida: str, ex: set[str]) -> list[str]:
    for op in IDEAS.get(comida, []):
        if not any(set(ALIMENTOS[a][7]) & ex for a in op):
            return [ALIMENTOS[a][0] for a in op]
    return []


def comida(sesion: dict, atleta: str | None, variante: int = 0) -> dict:  # variante: ya no se usa
    atleta = atleta or sesion.get("u") or "Yo"
    s.puede_ver(sesion, atleta)
    doc = _doc(atleta)
    if not _permitido(sesion, atleta, doc):
        return {"atleta": atleta, "acceso": False, "abono": bool(s._abono_url())}
    dieta = doc.get("dieta") or {}
    if not dieta.get("peso") and s.es_demo(sesion):  # la demo enseña una dieta de ejemplo para que se vea todo
        dieta = {"peso": 75, "objetivo": "mantener", "tipo": "equilibrada", "no_come": []}
    dia = (doc.get("dias") or {}).get(_hoy()) or {}
    entreno = dia.get("entreno", True)
    items = dia.get("items") or []
    obj = _objetivo_dia(dieta, entreno)
    ex = _excluidos(dieta)
    comidas = []
    for cid, nombre, parte in COMIDAS:
        its = [{**it, "nombre": ALIMENTOS[it["alimento"]][0], "racion": ALIMENTOS[it["alimento"]][1],
                **_sumar([it])} for it in items if it.get("comida") == cid and it.get("alimento") in ALIMENTOS]
        comidas.append({"id": cid, "nombre": nombre, "items": its, **_sumar(its),
                        "objetivo": round(obj["kcal"] * parte) if obj else None, "idea": _idea(cid, ex)})
    hab = doc.get("habitual") or {}
    hab_items = [{**i, "nombre": ALIMENTOS[i["alimento"]][0], "racion": ALIMENTOS[i["alimento"]][1], **_sumar([i])}
                 for i in hab.get("items") or [] if i.get("alimento") in ALIMENTOS]
    return {
        "atleta": atleta, "acceso": True, "solo_mirar": s.es_demo(sesion),
        "coach": s.es_coach(sesion) and atleta != "Yo",
        "paga": _paga(atleta, doc), "permitido": bool(doc.get("permitido")),
        "fecha": _hoy(), "entreno": entreno, "dieta": dieta, "objetivo": obj, "llevas": _sumar(items), "comidas": comidas,
        "plan": plan_dia(dieta, obj),
        "habitual": {"texto": hab.get("texto", ""), "items": hab_items, "total": _sumar(hab_items),
                     "consejos": consejos(hab_items, obj, entreno, dieta)} if hab_items else None,
        "opciones": {"objetivos": {k: v[0] for k, v in OBJETIVOS.items()}, "dietas": {k: v[0] for k, v in DIETAS.items()},
                     "exclusiones": EXCLUSIONES},
        "alimentos": [{"id": k, "nombre": v[0], "racion": v[1], "kcal": v[2], "p": v[3], "h": v[4], "g": v[5], "grupo": v[6]}
                      for k, v in ALIMENTOS.items() if not set(v[7]) & ex],
    }


def comida_accion(sesion: dict, c: dict) -> dict:
    atleta = c.get("atleta") or sesion.get("u") or "Yo"
    s.puede_ver(sesion, atleta)
    doc = _doc(atleta)
    que = c.get("accion")
    if que == "permiso":  # Diego desbloquea (o quita) la comida a un atleta sin abono
        if not s.es_coach(sesion):
            raise s.Error("Solo el coach puede hacer esto", 403)
        doc["permitido"] = bool(c.get("valor"))
    else:
        if not _permitido(sesion, atleta, doc):
            raise s.Error("La comida es para abonados. Abónate para usarla.", 402)
        dias = doc.setdefault("dias", {})
        dia = dias.setdefault(_hoy(), {"entreno": True, "items": []})
        if que == "dieta":
            d = c.get("dieta") or {}
            try:
                peso = float(str(d.get("peso") or 0).replace(",", "."))
            except ValueError:
                peso = 0
            if not 30 <= peso <= 250:
                raise s.Error("Pon tu peso en kg (entre 30 y 250)", 400)
            doc["dieta"] = {"peso": round(peso, 1),
                            "objetivo": d.get("objetivo") if d.get("objetivo") in OBJETIVOS else "mantener",
                            "tipo": d.get("tipo") if d.get("tipo") in DIETAS else "equilibrada",
                            "no_come": [x for x in (d.get("no_come") or []) if x in EXCLUSIONES]}
        elif que == "entreno":
            dia["entreno"] = bool(c.get("valor"))
        elif que == "anadir":
            if c.get("alimento") not in ALIMENTOS or c.get("comida") not in {x[0] for x in COMIDAS}:
                raise s.Error("Alimento no válido", 400)
            r = float(c.get("raciones") or 1)
            if not 0 < r <= 6:
                raise s.Error("Raciones no válidas", 400)
            dia.setdefault("items", []).append({"id": uuid.uuid4().hex[:8], "comida": c["comida"],
                                                "alimento": c["alimento"], "raciones": r})
        elif que == "interpretar":  # no guarda nada: devuelve lo entendido para confirmar
            r = interpretar(str(c.get("texto") or "")[:2000], c.get("comida"))
            return {"interpretado": r}
        elif que == "anadir_varios":
            for it in (c.get("items") or [])[:40]:
                if it.get("alimento") in ALIMENTOS and it.get("comida") in {x[0] for x in COMIDAS}:
                    r = max(.25, min(6, float(it.get("raciones") or 1)))
                    dia.setdefault("items", []).append({"id": uuid.uuid4().hex[:8], "comida": it["comida"], "alimento": it["alimento"], "raciones": r})
        elif que == "habitual":
            its = [{"comida": it["comida"], "alimento": it["alimento"], "raciones": max(.25, min(6, float(it.get("raciones") or 1)))}
                   for it in (c.get("items") or [])[:40] if it.get("alimento") in ALIMENTOS and it.get("comida") in {x[0] for x in COMIDAS}]
            doc["habitual"] = {"texto": str(c.get("texto") or "")[:2000], "items": its} if its else {}
        elif que == "como_siempre":
            hab = (doc.get("habitual") or {}).get("items") or []
            if not hab:
                raise s.Error("Primero cuéntanos lo que sueles comer", 400)
            dia["items"] = [x for x in dia.get("items") or [] if not x.get("habitual")] + [
                {**x, "id": uuid.uuid4().hex[:8], "habitual": True} for x in hab]
        elif que == "quitar":
            dia["items"] = [x for x in dia.get("items") or [] if x.get("id") != c.get("id")]
        else:
            raise s.Error("Acción no válida", 400)
        for f in sorted(dias)[:-DIAS_GUARDADOS]:
            dias.pop(f, None)
    s.datos().guardar(_clave(atleta), doc)
    return comida(sesion, atleta)
