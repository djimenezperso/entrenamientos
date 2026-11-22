"""Recetas para cada opción del menú (Comida): nombre, tiempo y pasos, en español y francés.

Las cantidades no van aquí: salen de la opción ya ajustada a las calorías y la proteína de cada atleta,
así la receta cuadra siempre con su plan. Inspiradas en recetas clásicas; el enlace «Inspírate» busca
versiones con calorías en FatSecret (la que más se parece a cada plato).
"""
from __future__ import annotations

from urllib.parse import quote_plus

# (alimentos de la opción) → (min, nombre es, nombre fr, [pasos es], [pasos fr])
RECETAS = {
    # ---- desayuno
    ("avena", "leche", "platano"): (8, "Porridge de plátano", "Porridge à la banane", [
        "Pon la avena con la leche en un cazo a fuego medio.",
        "Remueve 3-4 minutos hasta que espese (o 2 minutos al microondas).",
        "Corta el plátano en rodajas por encima. Un poco de canela le va muy bien."], [
        "Mets les flocons d'avoine et le lait dans une casserole à feu moyen.",
        "Remue 3-4 minutes jusqu'à ce que ça épaississe (ou 2 minutes au micro-ondes).",
        "Coupe la banane en rondelles par-dessus. Un peu de cannelle, c'est top."]),
    ("yogur", "cereales", "frutos_rojos"): (3, "Bol de yogur, cereales y frutos rojos", "Bol yaourt, céréales et fruits rouges", [
        "Pon el yogur en un bol.", "Añade los cereales justo antes de comer para que crujan.", "Termina con los frutos rojos."], [
        "Mets le yaourt dans un bol.", "Ajoute les céréales juste avant de manger pour qu'elles restent croustillantes.",
        "Termine avec les fruits rouges."]),
    ("pan", "aguacate", "claras"): (8, "Tostadas de aguacate con claras", "Tartines avocat et blancs d'œufs", [
        "Tuesta el pan.", "Chafa el aguacate con un tenedor, sal, pimienta y unas gotas de limón, y úntalo.",
        "Haz las claras revueltas en una sartén antiadherente (2-3 min) y ponlas encima."], [
        "Fais griller le pain.", "Écrase l'avocat à la fourchette avec sel, poivre et quelques gouttes de citron, puis tartine.",
        "Fais les blancs brouillés dans une poêle antiadhésive (2-3 min) et pose-les dessus."]),
    ("pan", "huevos", "manzana"): (8, "Tostadas con huevos revueltos", "Tartines aux œufs brouillés", [
        "Bate los huevos con una pizca de sal.", "Cuájalos a fuego bajo removiendo, sin que se sequen.",
        "Sírvelos sobre el pan tostado. La fruta, de postre."], [
        "Bats les œufs avec une pincée de sel.", "Fais-les cuire à feu doux en remuant, sans qu'ils sèchent.",
        "Sers-les sur le pain grillé. Le fruit en dessert."]),
    ("avena", "bebida_veg", "frutos_rojos"): (5, "Overnight oats de frutos rojos", "Overnight oats aux fruits rouges", [
        "La noche antes: mezcla la avena con la bebida de soja en un tarro.", "Tápalo y a la nevera.",
        "Por la mañana, frutos rojos por encima y listo."], [
        "La veille : mélange les flocons d'avoine avec la boisson soja dans un bocal.", "Ferme et au frigo.",
        "Le matin, fruits rouges par-dessus et c'est prêt."]),
    ("tortitas", "crema_cacahuete", "platano"): (3, "Tortitas de arroz con cacahuete y plátano", "Galettes de riz cacahuète-banane", [
        "Unta las tortitas con la crema de cacahuete.", "Pon el plátano en rodajas encima."], [
        "Tartine les galettes de beurre de cacahuète.", "Ajoute la banane en rondelles par-dessus."]),
    # ---- comida
    ("arroz", "pollo", "verdura", "aceite"): (20, "Arroz salteado con pollo y verduras", "Riz sauté au poulet et légumes", [
        "Corta el pollo en tiras y la verdura en trozos pequeños.",
        "Dora el pollo en la sartén con el aceite, 5-6 min. Sácalo.",
        "Saltea la verdura 4-5 min a fuego fuerte.",
        "Añade el arroz ya cocido y el pollo, un chorrito de salsa de soja, y 2 min más."], [
        "Coupe le poulet en lanières et les légumes en petits morceaux.",
        "Fais dorer le poulet dans la poêle avec l'huile, 5-6 min. Réserve.",
        "Fais sauter les légumes 4-5 min à feu vif.",
        "Ajoute le riz déjà cuit et le poulet, un trait de sauce soja, et 2 min de plus."]),
    ("patata", "ternera", "ensalada", "aceite"): (25, "Ternera a la plancha con patatas", "Bœuf à la plancha et pommes de terre", [
        "Cuece las patatas en agua con sal 15-20 min (o 8 min al microondas tapadas).",
        "Haz la ternera a la plancha bien caliente, 2-3 min por lado. Sal al final.",
        "Aliña la ensalada con el aceite y sírvelo todo junto."], [
        "Fais cuire les pommes de terre à l'eau salée 15-20 min (ou 8 min au micro-ondes, couvertes).",
        "Saisis le bœuf sur une plancha bien chaude, 2-3 min par côté. Sale à la fin.",
        "Assaisonne la salade avec l'huile et sers le tout."]),
    ("garbanzos", "pollo", "verdura"): (15, "Garbanzos salteados con pollo", "Pois chiches sautés au poulet", [
        "Corta el pollo en dados y dóralo en la sartén 5 min.",
        "Añade la verdura troceada y saltea 4 min.",
        "Echa los garbanzos escurridos, pimentón y comino, y 3 min más."], [
        "Coupe le poulet en dés et fais-le dorer 5 min à la poêle.",
        "Ajoute les légumes coupés et fais sauter 4 min.",
        "Ajoute les pois chiches égouttés, paprika et cumin, et 3 min de plus."]),
    ("pasta", "atun", "ensalada", "aceite"): (15, "Ensalada de pasta con atún", "Salade de pâtes au thon", [
        "Cuece la pasta, escúrrela y pásala por agua fría.",
        "Mézclala con la ensalada troceada y el atún escurrido.",
        "Aliña con el aceite, sal y orégano."], [
        "Fais cuire les pâtes, égoutte-les et passe-les sous l'eau froide.",
        "Mélange-les avec la salade coupée et le thon égoutté.",
        "Assaisonne avec l'huile, du sel et de l'origan."]),
    ("lentejas", "arroz", "verdura"): (15, "Lentejas con arroz y verduras", "Lentilles, riz et légumes", [
        "Saltea la verdura troceada en una cazuela 5 min.",
        "Añade las lentejas cocidas, un vaso de agua y pimentón; 5 min a fuego medio.",
        "Sírvelas con el arroz al lado."], [
        "Fais revenir les légumes coupés dans une cocotte 5 min.",
        "Ajoute les lentilles cuites, un verre d'eau et du paprika ; 5 min à feu moyen.",
        "Sers-les avec le riz à côté."]),
    ("patata", "tofu", "verdura", "aceite"): (25, "Tofu salteado con patatas y verduras", "Tofu sauté, pommes de terre et légumes", [
        "Seca el tofu con papel y córtalo en dados.",
        "Cuece la patata en dados (8 min al microondas tapada).",
        "Dora el tofu en el aceite 6-8 min, añade la verdura y la patata, y saltea 5 min con soja o especias."], [
        "Sèche le tofu avec du papier et coupe-le en dés.",
        "Fais cuire la pomme de terre en dés (8 min au micro-ondes, couverte).",
        "Fais dorer le tofu dans l'huile 6-8 min, ajoute légumes et pommes de terre, et 5 min avec soja ou épices."]),
    # ---- merienda
    ("skyr", "miel", "platano"): (2, "Skyr con miel y plátano", "Skyr, miel et banane", [
        "Pon el skyr en un bol, el plátano en rodajas y la miel por encima."], [
        "Mets le skyr dans un bol, la banane en rondelles et le miel par-dessus."]),
    ("pan", "jamon", "zumo"): (3, "Tostada de jamón con zumo", "Tartine au jambon cru et jus", [
        "Tuesta el pan, frótalo con tomate si quieres y pon el jamón encima.", "Acompáñalo con el zumo."], [
        "Fais griller le pain, frotte-le à la tomate si tu veux et ajoute le jambon.", "Avec le jus à côté."]),
    ("yogur", "frutos_secos", "manzana"): (3, "Yogur con frutos secos y manzana", "Yaourt, fruits secs et pomme", [
        "Corta la manzana en dados.", "Mézclala con el yogur y los frutos secos picados. Canela opcional."], [
        "Coupe la pomme en dés.", "Mélange avec le yaourt et les fruits secs concassés. Cannelle en option."]),
    ("pan", "atun", "manzana"): (3, "Tostada de atún", "Tartine au thon", [
        "Escurre el atún y mézclalo con unas gotas de limón y pimienta.", "Ponlo sobre el pan tostado. La fruta, aparte."], [
        "Égoutte le thon et mélange-le avec quelques gouttes de citron et du poivre.", "Étale-le sur le pain grillé. Le fruit à part."]),
    ("proteina_veg", "bebida_veg", "platano"): (3, "Batido proteico de plátano", "Shake protéiné à la banane", [
        "Pon todo en la batidora con un par de cubitos de hielo.", "30 segundos y listo."], [
        "Mets tout dans le blender avec deux glaçons.", "30 secondes et c'est prêt."]),
    ("tortitas", "crema_cacahuete"): (2, "Tortitas con crema de cacahuete", "Galettes de riz au beurre de cacahuète", [
        "Unta las tortitas con la crema de cacahuete. Una pizca de sal por encima le queda genial."], [
        "Tartine les galettes de beurre de cacahuète. Une pincée de sel par-dessus, c'est top."]),
    # ---- cena
    ("salmon", "boniato", "ensalada"): (30, "Salmón al horno con boniato", "Saumon au four et patate douce", [
        "Horno a 200 °C. Corta el boniato en gajos y hornéalo 15 min.",
        "Añade el salmón con sal, pimienta y limón, y 12-15 min más.",
        "Sírvelo con la ensalada."], [
        "Four à 200 °C. Coupe la patate douce en quartiers et enfourne 15 min.",
        "Ajoute le saumon avec sel, poivre et citron, et 12-15 min de plus.",
        "Sers avec la salade."]),
    ("merluza", "patata", "verdura", "aceite"): (20, "Merluza al vapor con patata y verduras", "Merlu vapeur, pommes de terre et légumes", [
        "Cuece la patata y la verdura al vapor o en el microondas 8-10 min.",
        "Haz la merluza al vapor o a la plancha 4-5 min por lado.",
        "Aliña todo con el aceite, sal y perejil."], [
        "Fais cuire pommes de terre et légumes à la vapeur ou au micro-ondes 8-10 min.",
        "Fais le merlu à la vapeur ou à la plancha 4-5 min par côté.",
        "Assaisonne le tout avec l'huile, du sel et du persil."]),
    ("pavo", "arroz", "verdura", "aceite"): (20, "Pavo salteado con arroz", "Dinde sautée et riz", [
        "Corta el pavo en tiras y dóralo en el aceite 5 min.",
        "Añade la verdura y saltea 4-5 min con ajo y especias.",
        "Sírvelo con el arroz cocido."], [
        "Coupe la dinde en lanières et fais-la dorer dans l'huile 5 min.",
        "Ajoute les légumes et fais sauter 4-5 min avec ail et épices.",
        "Sers avec le riz cuit."]),
    ("huevos", "pan", "verdura", "aceite"): (15, "Tortilla de verduras", "Omelette aux légumes", [
        "Saltea la verdura troceada con el aceite 5 min.",
        "Bate los huevos, échalos sobre la verdura y cuaja a fuego bajo, tapado, 4-5 min.",
        "Con el pan al lado."], [
        "Fais revenir les légumes coupés avec l'huile 5 min.",
        "Bats les œufs, verse-les sur les légumes et fais cuire à feu doux, couvert, 4-5 min.",
        "Avec le pain à côté."]),
    ("tofu", "verdura", "patata", "aceite"): (30, "Tofu al horno con verduras", "Tofu rôti aux légumes", [
        "Horno a 200 °C. Corta tofu, verdura y patata en trozos.",
        "Mézclalo todo con el aceite, sal, pimentón y ajo en polvo.",
        "Hornea 25 min, dándole la vuelta a mitad."], [
        "Four à 200 °C. Coupe tofu, légumes et pommes de terre en morceaux.",
        "Mélange le tout avec l'huile, sel, paprika et ail en poudre.",
        "Enfourne 25 min en retournant à mi-cuisson."]),
    ("garbanzos", "ensalada", "aceite"): (8, "Ensalada de garbanzos", "Salade de pois chiches", [
        "Escurre y enjuaga los garbanzos.",
        "Mézclalos con la ensalada troceada (tomate, pepino, cebolla…).",
        "Aliña con el aceite, limón, sal y comino."], [
        "Égoutte et rince les pois chiches.",
        "Mélange-les avec la salade coupée (tomate, concombre, oignon…).",
        "Assaisonne avec l'huile, citron, sel et cumin."]),
}

EXTRA = ("Para llegar a tu proteína, añade también: {x}.", "Pour atteindre tes protéines, ajoute aussi : {x}.")


def receta(op: list[str], items: list[dict]) -> dict | None:
    """La receta de una opción del menú. `items` son los de la opción ya escalada (por si lleva un extra de proteína)."""
    r = RECETAS.get(tuple(op))
    if not r:
        return None
    minutos, n_es, n_fr, p_es, p_fr = r
    extra = [it["nombre"] for it in items if it["alimento"] not in op]
    return {
        "minutos": minutos, "nombre": n_es, "nombre_fr": n_fr,
        "pasos": p_es + ([EXTRA[0].format(x=", ".join(extra))] if extra else []),
        "pasos_fr": p_fr + ([EXTRA[1].format(x=", ".join(extra))] if extra else []),
        # para inspirarse: versiones de ese plato con sus calorías
        "inspira": "https://www.google.com/search?q=" + quote_plus(f"{n_es} receta calorías fatsecret"),
        "inspira_fr": "https://www.google.com/search?q=" + quote_plus(f"{n_fr} recette calories fatsecret"),
    }
