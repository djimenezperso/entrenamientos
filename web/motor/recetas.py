"""Recetas para cada opción del menú (Comida): nombre, tiempo, su salsa o toque, y pasos, en español y francés.

Las cantidades de los alimentos no van aquí: salen de la opción ya ajustada a las calorías y la proteína de cada
atleta, así la receta cuadra con su plan. Cada receta lleva una salsa o toque con lo que suele haber en casa
(especias, limón, ajo, soja, mostaza, yogur…), con sus kcal aproximadas para que no descuadre.
El enlace «Inspírate» busca más versiones de ese plato con sus calorías en FatSecret.
"""
from __future__ import annotations

from urllib.parse import quote_plus


def _r(minutos, nombre, nom_fr, salsa, salsa_fr, kcal_salsa, pasos, pasos_fr):
    return {"minutos": minutos, "nombre": nombre, "nombre_fr": nom_fr, "salsa": salsa, "salsa_fr": salsa_fr,
            "kcal_salsa": kcal_salsa, "pasos": pasos, "pasos_fr": pasos_fr}


RECETAS = {
    # ---------- desayuno
    ("avena", "leche", "platano"): _r(
        8, "Porridge de plátano caramelizado", "Porridge à la banane caramélisée",
        "Canela, una pizca de sal y vainilla", "Cannelle, une pincée de sel et vanille", 5, [
            "Calienta la avena con la leche, la canela y la pizca de sal, removiendo 3-4 min hasta que esté cremosa.",
            "Mientras, dora medio plátano en rodajas en una sartén sin aceite, 1 min por lado: se carameliza solo.",
            "Sirve el porridge, el resto del plátano chafado dentro y las rodajas doradas encima."], [
            "Fais chauffer les flocons avec le lait, la cannelle et la pincée de sel, en remuant 3-4 min jusqu'à ce que ce soit crémeux.",
            "Pendant ce temps, dore la moitié de la banane en rondelles dans une poêle sans huile, 1 min par face : elle caramélise toute seule.",
            "Sers le porridge, le reste de la banane écrasée dedans et les rondelles dorées par-dessus."]),
    ("yogur", "cereales", "frutos_rojos"): _r(
        4, "Parfait de yogur y frutos rojos", "Parfait yaourt et fruits rouges",
        "Coulis exprés: frutos rojos chafados con unas gotas de limón", "Coulis express : fruits rouges écrasés avec quelques gouttes de citron", 0, [
            "Chafa la mitad de los frutos rojos con el limón: ese es tu coulis.",
            "En un vaso, por capas: yogur, coulis, cereales, y repite.",
            "Corona con los frutos rojos enteros. Los cereales al final, para que crujan."], [
            "Écrase la moitié des fruits rouges avec le citron : c'est ton coulis.",
            "Dans un verre, en couches : yaourt, coulis, céréales, et recommence.",
            "Termine avec les fruits rouges entiers. Les céréales à la fin, pour qu'elles restent croustillantes."]),
    ("pan", "aguacate", "claras"): _r(
        8, "Tostadas de aguacate con revuelto y chili", "Toasts avocat, œufs brouillés et piment",
        "Limón, escamas de chili y un toque de comino", "Citron, piment en flocons et une pointe de cumin", 0, [
            "Tuesta el pan.",
            "Chafa el aguacate con limón, sal y una pizca de comino, y úntalo.",
            "Haz las claras revueltas a fuego bajo con pimienta (2-3 min, que queden jugosas).",
            "Ponlas encima y termina con escamas de chili."], [
            "Fais griller le pain.",
            "Écrase l'avocat avec citron, sel et une pincée de cumin, puis tartine.",
            "Brouille les blancs à feu doux avec du poivre (2-3 min, qu'ils restent moelleux).",
            "Pose-les dessus et termine avec des flocons de piment."]),
    ("pan", "huevos", "manzana"): _r(
        8, "Huevos turcos exprés sobre tostada", "Œufs à la turque express sur toast",
        "Pimentón ahumado, ajo en polvo y un hilo de limón", "Paprika fumé, ail en poudre et un filet de citron", 5, [
            "Bate los huevos con sal y ajo en polvo, y cuájalos a fuego bajo removiendo: cremosos, no secos.",
            "Ponlos sobre el pan tostado.",
            "Pimentón ahumado por encima y unas gotas de limón. La fruta, de postre."], [
            "Bats les œufs avec sel et ail en poudre, et fais-les cuire à feu doux en remuant : crémeux, pas secs.",
            "Pose-les sur le pain grillé.",
            "Paprika fumé par-dessus et quelques gouttes de citron. Le fruit en dessert."]),
    ("avena", "bebida_veg", "frutos_rojos"): _r(
        5, "Overnight oats de tarta de frutos rojos", "Overnight oats façon tarte aux fruits rouges",
        "Vainilla, ralladura de limón y una pizca de sal", "Vanille, zeste de citron et une pincée de sel", 0, [
            "La noche antes: mezcla la avena, la bebida de soja, la vainilla, la ralladura de limón y la sal en un tarro.",
            "Tápalo y a la nevera.",
            "Por la mañana, frutos rojos chafados por encima: sabe a tarta."], [
            "La veille : mélange flocons, boisson soja, vanille, zeste de citron et sel dans un bocal.",
            "Ferme et au frigo.",
            "Le matin, fruits rouges écrasés par-dessus : on dirait une tarte."]),
    ("tortitas", "crema_cacahuete", "platano"): _r(
        3, "Tortitas «sándwich» de cacahuete y plátano", "Galettes « sandwich » cacahuète-banane",
        "Canela y unas escamas de sal", "Cannelle et quelques cristaux de sel", 0, [
            "Unta las tortitas con la crema de cacahuete.",
            "Pon el plátano en rodajas, canela y una pizca de sal por encima.",
            "Tapa con otra tortita y aprieta: crujiente y dulce."], [
            "Tartine les galettes de beurre de cacahuète.",
            "Ajoute la banane en rondelles, la cannelle et une pincée de sel.",
            "Referme avec une autre galette et presse : croquant et sucré."]),
    # ---------- comida
    ("arroz", "pollo", "verdura", "aceite"): _r(
        20, "Bowl de pollo teriyaki", "Bowl de poulet teriyaki",
        "Teriyaki ligera: 2 cdas de soja, 1 cdta de miel, ajo y jengibre rallados, un chorrito de agua",
        "Teriyaki léger : 2 c. à s. de soja, 1 c. à c. de miel, ail et gingembre râpés, un trait d'eau", 35, [
            "Mezcla la salsa en un vaso.",
            "Dora el pollo en tiras con el aceite, 5-6 min a fuego fuerte.",
            "Echa la salsa y deja que reduzca 1-2 min hasta que brille y se pegue al pollo.",
            "Saltea la verdura 3-4 min, que quede crujiente.",
            "Monta el bowl: arroz, verdura, pollo con su salsa. Sésamo o cebolleta si tienes."], [
            "Mélange la sauce dans un verre.",
            "Fais dorer le poulet en lanières avec l'huile, 5-6 min à feu vif.",
            "Verse la sauce et laisse réduire 1-2 min jusqu'à ce qu'elle nappe le poulet.",
            "Fais sauter les légumes 3-4 min, qu'ils restent croquants.",
            "Monte le bowl : riz, légumes, poulet et sa sauce. Sésame ou cébette si tu en as."]),
    ("patata", "ternera", "ensalada", "aceite"): _r(
        25, "Ternera con patatas bravas al horno", "Bœuf et patatas bravas au four",
        "Brava ligera: tomate triturado, pimentón picante, ajo y vinagre", "Sauce brava légère : tomate concassée, paprika fort, ail et vinaigre", 20, [
            "Corta las patatas en dados, mézclalas con la mitad del aceite, sal y pimentón, y al horno a 220 °C 20 min (o airfryer 15).",
            "Para la brava: 3 cdas de tomate triturado, pimentón picante, ajo en polvo y un chorrito de vinagre, 2 min al fuego.",
            "Ternera a la plancha muy caliente, 2-3 min por lado; sal al final y deja reposar 2 min.",
            "Ensalada con el resto del aceite. Brava por encima de las patatas."], [
            "Coupe les pommes de terre en dés, mélange avec la moitié de l'huile, sel et paprika, et au four à 220 °C 20 min (ou airfryer 15).",
            "Pour la brava : 3 c. à s. de tomate concassée, paprika fort, ail en poudre et un trait de vinaigre, 2 min sur le feu.",
            "Bœuf sur plancha très chaude, 2-3 min par face ; sel à la fin et 2 min de repos.",
            "Salade avec le reste de l'huile. Brava sur les pommes de terre."]),
    ("garbanzos", "pollo", "verdura"): _r(
        15, "Pollo con garbanzos al curry exprés", "Poulet et pois chiches au curry express",
        "Curry, comino, ajo, tomate triturado y un toque de limón", "Curry, cumin, ail, tomate concassée et une touche de citron", 20, [
            "Dora el pollo en dados 5 min.",
            "Añade la verdura, 1 cda de curry, comino y ajo; 1 min removiendo para que suelte el aroma.",
            "Echa 4 cdas de tomate triturado y los garbanzos; 5 min a fuego medio.",
            "Unas gotas de limón al final y cilantro o perejil si tienes."], [
            "Fais dorer le poulet en dés 5 min.",
            "Ajoute les légumes, 1 c. à s. de curry, cumin et ail ; 1 min en remuant pour libérer les arômes.",
            "Verse 4 c. à s. de tomate concassée et les pois chiches ; 5 min à feu moyen.",
            "Quelques gouttes de citron à la fin, et coriandre ou persil si tu en as."]),
    ("pasta", "atun", "ensalada", "aceite"): _r(
        15, "Pasta fría mediterránea con atún", "Salade de pâtes méditerranéenne au thon",
        "Vinagreta: el aceite, limón, mostaza, orégano y alcaparras", "Vinaigrette : l'huile, citron, moutarde, origan et câpres", 10, [
            "Cuece la pasta, escúrrela y enfríala con agua.",
            "Vinagreta: el aceite, zumo de medio limón, 1 cdta de mostaza, orégano y unas alcaparras; bate con un tenedor.",
            "Mezcla la pasta con la ensalada troceada (tomate cherry, pepino, cebolla morada) y el atún.",
            "Aliña y, si puedes, 10 min de nevera: está aún mejor."], [
            "Fais cuire les pâtes, égoutte-les et refroidis-les à l'eau.",
            "Vinaigrette : l'huile, le jus d'un demi-citron, 1 c. à c. de moutarde, origan et quelques câpres ; fouette à la fourchette.",
            "Mélange les pâtes avec la salade coupée (tomates cerises, concombre, oignon rouge) et le thon.",
            "Assaisonne et, si tu peux, 10 min au frigo : c'est encore meilleur."]),
    ("lentejas", "arroz", "verdura"): _r(
        15, "Lentejas dal con arroz", "Dal de lentilles et riz",
        "Cúrcuma, comino, ajo, jengibre y un chorrito de leche de coco light", "Curcuma, cumin, ail, gingembre et un trait de lait de coco light", 30, [
            "Saltea la verdura picada con ajo y jengibre 4 min.",
            "Añade cúrcuma y comino, 30 segundos.",
            "Echa las lentejas, medio vaso de agua y 2 cdas de leche de coco; 6-8 min hasta que espese.",
            "Sírvelo con el arroz y un poco de limón."], [
            "Fais revenir les légumes hachés avec ail et gingembre 4 min.",
            "Ajoute curcuma et cumin, 30 secondes.",
            "Verse les lentilles, un demi-verre d'eau et 2 c. à s. de lait de coco ; 6-8 min jusqu'à ce que ça épaississe.",
            "Sers avec le riz et un peu de citron."]),
    ("patata", "tofu", "verdura", "aceite"): _r(
        25, "Tofu crujiente con salsa de cacahuete", "Tofu croustillant sauce cacahuète",
        "Salsa satay ligera: 1 cdta de crema de cacahuete, soja, lima y un toque de picante",
        "Sauce satay légère : 1 c. à c. de beurre de cacahuète, soja, citron vert et une pointe de piment", 40, [
            "Seca bien el tofu, córtalo en dados y pásalo por una cucharadita de maicena: así cruje.",
            "Cuece la patata en dados (8 min al microondas tapada).",
            "Dora el tofu en el aceite 6-8 min, añade la verdura y la patata, 4 min más.",
            "Salsa: crema de cacahuete, soja, lima y un poco de agua caliente; por encima."], [
            "Sèche bien le tofu, coupe-le en dés et passe-le dans 1 c. à c. de maïzena : il croustille.",
            "Fais cuire la pomme de terre en dés (8 min au micro-ondes, couverte).",
            "Dore le tofu dans l'huile 6-8 min, ajoute légumes et pommes de terre, 4 min de plus.",
            "Sauce : beurre de cacahuète, soja, citron vert et un peu d'eau chaude ; par-dessus."]),
    # ---------- merienda
    ("skyr", "miel", "platano"): _r(
        2, "Skyr «banoffee»", "Skyr façon banoffee",
        "Canela y unas gotas de vainilla", "Cannelle et quelques gouttes de vanille", 0, [
            "Mezcla el skyr con la vainilla.",
            "Plátano en rodajas, la miel por encima y canela: sabe a postre."], [
            "Mélange le skyr avec la vanille.",
            "Banane en rondelles, le miel par-dessus et cannelle : on dirait un dessert."]),
    ("pan", "jamon", "zumo"): _r(
        3, "Pan con tomate y jamón", "Pan con tomate au jambon cru",
        "Tomate rallado, ajo y un hilo de aceite", "Tomate râpée, ail et un filet d'huile", 25, [
            "Tuesta el pan y frótalo con medio diente de ajo.",
            "Ralla un tomate, sal, y úntalo; un hilito de aceite.",
            "El jamón encima. El zumo, aparte."], [
            "Fais griller le pain et frotte-le avec une demi-gousse d'ail.",
            "Râpe une tomate, sale-la et étale-la ; un petit filet d'huile.",
            "Le jambon par-dessus. Le jus à côté."]),
    ("yogur", "frutos_secos", "manzana"): _r(
        5, "Yogur con manzana asada exprés", "Yaourt et pomme rôtie express",
        "Canela y una pizca de jengibre", "Cannelle et une pincée de gingembre", 0, [
            "Manzana en dados con canela y jengibre, 2 min al microondas: queda como asada.",
            "Sobre el yogur, con los frutos secos picados por encima."], [
            "Pomme en dés avec cannelle et gingembre, 2 min au micro-ondes : comme rôtie.",
            "Sur le yaourt, avec les fruits secs concassés par-dessus."]),
    ("pan", "atun", "manzana"): _r(
        4, "Tostada de atún con mayo de yogur", "Toast au thon et mayo de yaourt",
        "Mayo ligera: 1 cda de yogur, mostaza, limón y pimienta", "Mayo légère : 1 c. à s. de yaourt, moutarde, citron et poivre", 15, [
            "Mezcla el yogur con la mostaza, el limón y la pimienta.",
            "Añade el atún escurrido y mezcla.",
            "Sobre el pan tostado, con pepinillo o cebolla si tienes. La fruta, aparte."], [
            "Mélange le yaourt avec la moutarde, le citron et le poivre.",
            "Ajoute le thon égoutté et mélange.",
            "Sur le pain grillé, avec cornichon ou oignon si tu en as. Le fruit à part."]),
    ("proteina_veg", "bebida_veg", "platano"): _r(
        3, "Batido de plátano y café", "Smoothie banane-café",
        "Un chupito de café frío, canela y hielo", "Un shot de café froid, cannelle et glaçons", 2, [
            "Todo a la batidora: la proteína, la bebida, el plátano, el café, la canela y 3-4 hielos.",
            "30 segundos y a beber bien frío."], [
            "Tout dans le blender : protéine, boisson, banane, café, cannelle et 3-4 glaçons.",
            "30 secondes et à boire bien frais."]),
    ("tortitas", "crema_cacahuete"): _r(
        2, "Tortitas de cacahuete y cacao", "Galettes cacahuète-cacao",
        "Cacao puro en polvo y escamas de sal", "Cacao pur en poudre et cristaux de sel", 10, [
            "Unta las tortitas con la crema de cacahuete.",
            "Espolvorea cacao puro y una pizca de sal: sabe a bombón."], [
            "Tartine les galettes de beurre de cacahuète.",
            "Saupoudre de cacao pur et d'une pincée de sel : on dirait un chocolat."]),
    # ---------- cena
    ("salmon", "boniato", "ensalada"): _r(
        30, "Salmón glaseado con miel y mostaza", "Saumon laqué miel-moutarde",
        "Glaseado: 1 cdta de miel, 1 cdta de mostaza antigua, soja y limón", "Laquage : 1 c. à c. de miel, 1 c. à c. de moutarde à l'ancienne, soja et citron", 30, [
            "Horno a 200 °C. Boniato en gajos con sal y pimentón, 15 min.",
            "Mezcla el glaseado y píntalo sobre el salmón.",
            "Salmón al horno con el boniato, 12-15 min más.",
            "Sírvelo con la ensalada y un poco de limón."], [
            "Four à 200 °C. Patate douce en quartiers avec sel et paprika, 15 min.",
            "Mélange le laquage et badigeonne le saumon.",
            "Saumon au four avec la patate douce, 12-15 min de plus.",
            "Sers avec la salade et un peu de citron."]),
    ("merluza", "patata", "verdura", "aceite"): _r(
        20, "Merluza al ajillo con patatas", "Merlu à l'ail et pommes de terre",
        "Ajillo: el aceite con ajo laminado, guindilla y perejil", "Sauce à l'ail : l'huile avec ail émincé, piment et persil", 0, [
            "Patata y verdura al vapor o microondas, 8-10 min.",
            "En la sartén, el aceite con 2 ajos laminados y guindilla a fuego bajo hasta que doren.",
            "Saca el ajo, haz la merluza en ese aceite 3-4 min por lado.",
            "Vuelve a echar el ajillo por encima, con perejil y limón."], [
            "Pommes de terre et légumes à la vapeur ou au micro-ondes, 8-10 min.",
            "À la poêle, l'huile avec 2 gousses d'ail émincées et du piment à feu doux jusqu'à ce qu'elles dorent.",
            "Retire l'ail, fais cuire le merlu dans cette huile 3-4 min par face.",
            "Remets l'ail par-dessus, avec persil et citron."]),
    ("pavo", "arroz", "verdura", "aceite"): _r(
        20, "Pavo al limón y ajo con arroz", "Dinde citron-ail et riz",
        "Limón, ajo, tomillo y un chorrito de soja", "Citron, ail, thym et un trait de soja", 5, [
            "Pavo en tiras con ralladura y zumo de medio limón, ajo y tomillo (aunque sean 5 min, mejor).",
            "Dóralo en el aceite a fuego fuerte 4-5 min.",
            "Añade la verdura y un chorrito de soja, 3-4 min.",
            "Con el arroz y más limón por encima."], [
            "Dinde en lanières avec zeste et jus d'un demi-citron, ail et thym (même 5 min, c'est mieux).",
            "Fais-la dorer dans l'huile à feu vif 4-5 min.",
            "Ajoute les légumes et un trait de soja, 3-4 min.",
            "Avec le riz et encore du citron par-dessus."]),
    ("huevos", "pan", "verdura", "aceite"): _r(
        15, "Shakshuka exprés", "Shakshuka express",
        "Tomate triturado, comino, pimentón y una pizca de picante", "Tomate concassée, cumin, paprika et une pointe de piment", 25, [
            "Saltea la verdura picada (pimiento, cebolla) en el aceite 5 min.",
            "Añade medio vaso de tomate triturado, comino, pimentón y picante; 3 min.",
            "Haz dos huecos, casca los huevos dentro, tapa y 5-6 min a fuego bajo.",
            "Moja el pan en la salsa: es lo mejor."], [
            "Fais revenir les légumes hachés (poivron, oignon) dans l'huile 5 min.",
            "Ajoute un demi-verre de tomate concassée, cumin, paprika et piment ; 3 min.",
            "Fais deux creux, casse les œufs dedans, couvre et 5-6 min à feu doux.",
            "Trempe le pain dans la sauce : c'est le meilleur."]),
    ("tofu", "verdura", "patata", "aceite"): _r(
        30, "Tofu a la barbacoa al horno", "Tofu barbecue au four",
        "BBQ casera: tomate concentrado, pimentón ahumado, soja, unas gotas de miel y vinagre",
        "BBQ maison : concentré de tomate, paprika fumé, soja, quelques gouttes de miel et vinaigre", 25, [
            "Horno a 200 °C. Patata y verdura en trozos con el aceite y sal, 15 min.",
            "Mezcla la salsa BBQ y embadurna el tofu en dados.",
            "Añade el tofu a la bandeja y 12-15 min más, hasta que se caramelice."], [
            "Four à 200 °C. Pommes de terre et légumes en morceaux avec l'huile et le sel, 15 min.",
            "Mélange la sauce BBQ et enrobe le tofu en dés.",
            "Ajoute le tofu sur la plaque et 12-15 min de plus, jusqu'à ce qu'il caramélise."]),
    ("garbanzos", "ensalada", "aceite"): _r(
        10, "Ensalada de garbanzos crujientes con tahini", "Salade de pois chiches croustillants au tahini",
        "Tahini ligero: 1 cdta de tahini, limón, ajo y agua", "Tahini léger : 1 c. à c. de tahini, citron, ail et eau", 30, [
            "Seca los garbanzos y dóralos en la sartén con la mitad del aceite, pimentón y comino, 5-6 min: quedan crujientes.",
            "Salsa: tahini, limón, una pizca de ajo y agua hasta que quede cremosa.",
            "Ensalada troceada, garbanzos calientes por encima y la salsa."], [
            "Sèche les pois chiches et fais-les dorer à la poêle avec la moitié de l'huile, paprika et cumin, 5-6 min : ils croustillent.",
            "Sauce : tahini, citron, une pincée d'ail et de l'eau jusqu'à ce que ce soit crémeux.",
            "Salade coupée, pois chiches chauds par-dessus et la sauce."]),
}

EXTRA = ("Para llegar a tu proteína, añade también: {x}.", "Pour atteindre tes protéines, ajoute aussi : {x}.")


def receta(op: list[str], items: list[dict]) -> dict | None:
    """La receta de una opción del menú. `items` son los de la opción ya escalada (por si lleva un extra de proteína)."""
    r = RECETAS.get(tuple(op))
    if not r:
        return None
    extra = [it["nombre"] for it in items if it["alimento"] not in op]
    return {
        **r,
        "pasos": r["pasos"] + ([EXTRA[0].format(x=", ".join(extra))] if extra else []),
        "pasos_fr": r["pasos_fr"] + ([EXTRA[1].format(x=", ".join(extra))] if extra else []),
        # para inspirarse: versiones de ese plato con sus calorías
        "inspira": "https://www.google.com/search?q=" + quote_plus(f"{r['nombre']} receta calorías fatsecret"),
        "inspira_fr": "https://www.google.com/search?q=" + quote_plus(f"{r['nombre_fr']} recette calories fatsecret"),
    }
