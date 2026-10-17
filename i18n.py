"""Textos en francés. Lo que no esté aquí se queda en español."""
import streamlit as st

FR = {
    # navegación
    "Personas": "Personnes", "Movilidad": "Mobilité", "Rutina": "Programme", "Registrar": "Enregistrer",
    "Historial": "Historique", "Progreso": "Progrès", "Grupo": "Groupe", "Diario de Entrenos": "Journal d'entraînement",
    "Idioma": "Langue",
    # rutina
    "Semana": "Semaine",
    "Semana {s} ({m}). Los pesos tras @ suben lo indicado en «Sube» cada semana (2,5 kg por defecto).":
        "Semaine {s} ({m}). Les poids après @ montent de ce qui est indiqué dans « Sube » chaque semaine (2,5 kg par défaut).",
    "Terminé la semana {a} → pasar a la {b}": "J'ai fini la semaine {a} → passer à la {b}",
    "Marcar la semana {s} como la actual": "Marquer la semaine {s} comme actuelle",
    "esta semana": "cette semaine", "semana pasada": "semaine passée", "semana que viene": "semaine prochaine",
    "Toca un peso para cambiarlo: se guarda solo y las semanas siguientes se recalculan. ":
        "Touche un poids pour le changer : il s'enregistre seul et les semaines suivantes se recalculent. ",
    "Los WOD, conditionings y accessories se editan tocándolos. ":
        "Les WOD, conditionings, accessoires et la mobilité se modifient en les touchant. ",
    "En las pestañas: ✓ hecho · ◐ a medias · ↷ pasado · ✗ no hecho · • tiene pendientes.":
        "Onglets : ✓ fait · ◐ à moitié · ↷ reporté · ✗ pas fait · • a des séances en attente.",
    "Opciones al cambiar un peso": "Options quand tu changes un poids",
    "Mover igual el mismo ejercicio en los otros días": "Changer pareil le même exercice les autres jours",
    "Cambiar solo esta semana (excepción)": "Changer seulement cette semaine (exception)",
    "Sin validar en la semana {s}: {f}. Marca cada parte como hecha o pásala a otro día.":
        "Pas encore validé semaine {s} : {f}. Marque chaque partie comme faite ou reporte-la.",
    "✓ Hecho": "✓ Fait", "✗ No hecho": "✗ Pas fait", "→ Semana {n}": "→ Semaine {n}",
    ":green[✓ hecho]": ":green[✓ fait]", ":red[✗ no hecho]": ":red[✗ pas fait]",
    ":orange[◐ a medias]": ":orange[◐ à moitié]", ":orange[↷ pasado]": ":orange[↷ reporté]",
    ":gray[○ sin validar]": ":gray[○ pas validé]",
    ":red[✗ no hecho · la semana que viene se repite]": ":red[✗ pas fait · répété la semaine prochaine]",
    "✗ No lo hice (repite peso la semana que viene)": "✗ Pas fait (même poids la semaine prochaine)",
    "Registrar resultados": "Enregistrer les résultats", "Editar ejercicios": "Modifier les exercices",
    "+ Añadir día": "+ Ajouter un jour", "Historial:": "Historique :",
    "falta el peso · toca para ponerlo": "poids manquant · touche pour l'ajouter",
    "por definir": "à définir", "Guardar": "Enregistrer", "Usar este": "Utiliser celui-ci",
    "Aplicar a": "Appliquer à", "Solo esta semana": "Seulement cette semaine",
    "Esta semana y las siguientes": "Cette semaine et les suivantes",
    "✍️ Nuevo": "✍️ Nouveau", "📚 Ya hechos": "📚 Déjà faits", "💡 Repertorio": "💡 Répertoire", "✨ IA": "✨ IA",
    "Nombre": "Nom", "Qué toca": "Au programme", "Nota": "Note", "Buscar por movimiento": "Chercher un mouvement",
    "Elige": "Choisis", "🎲 Al azar": "🎲 Au hasard", "Añadir": "Ajouter", "Ejercicio": "Exercice",
    "+ Añadir accessory": "+ Ajouter un accessoire", "+ Añadir movilidad": "+ Ajouter de la mobilité",
    "Series y peso": "Séries et poids", "Pendiente": "En attente",
    # registrar
    "Tipo": "Type", "Fecha": "Date", "Título": "Titre", "Duración total": "Durée totale", "Resultados": "Résultats",
    "Notas": "Notes", "Foto": "Photo", "Guardar entreno": "Enregistrer la séance",
    "Partes que has hecho (se validan al guardar)": "Parties faites (validées à l'enregistrement)",
    # biblioteca
    "Quién": "Qui", "Todos": "Tous", "Solo los hechos": "Seulement ceux faits", "Solo hechos y guardados": "Faits et enregistrés",
    "Cadera": "Hanches", "Hombros": "Épaules", "Tobillos": "Chevilles", "Espalda": "Dos", "Isquios": "Ischios",
    "📲 Importar de WhatsApp": "📲 Importer depuis WhatsApp", "✨ Inventar con IA": "✨ Inventer avec l'IA",
    "💡 Ideas del repertorio": "💡 Idées du répertoire", "Cambiar tipo": "Changer le type",
    "Buscar en el repertorio": "Chercher dans le répertoire", "Al estilo de": "Dans le style de",
    "Idea (opcional)": "Idée (optionnel)", "Duración": "Durée", "Estilo": "Style",
    "✨ Inventar uno": "✨ En inventer un", "✨ Otro": "✨ Un autre",
}


def lang() -> str:
    return st.session_state.get("lang", "es")


def t(texto: str, **kw) -> str:
    """Traduce si el idioma es francés; con kw, rellena {huecos}."""
    s = FR.get(texto, texto) if lang() == "fr" else texto
    return s.format(**kw) if kw else s
