/* Djimenez Prog — app web. Sin librerías: todo el cálculo lo hace el servidor (la misma lógica que Streamlit). */
"use strict";

const $app = document.getElementById("app");
const $hoja = document.getElementById("hoja");
const $aviso = document.getElementById("aviso");

// ---------- guardado en el móvil ----------
const mem = {
  get(k) { try { return localStorage.getItem("dj_" + k); } catch { return null; } },
  set(k, v) { try { v == null ? localStorage.removeItem("dj_" + k) : localStorage.setItem("dj_" + k, v); } catch { } },
};

// idioma del móvil: francés si el teléfono está en francés, si no español
const IDIOMA_MOVIL = (() => { try { const l = (navigator.languages || [navigator.language]).find((x) => /^(fr|es)/i.test(x || "")); return l && /^fr/i.test(l) ? "fr" : "es"; } catch { return "es"; } })();
const E = { token: mem.get("token"), atleta: mem.get("atleta"), lang: mem.get("lang") || IDIOMA_MOVIL, vista: null,
  semana: null, dia: null, ocupado: false };

// ---------- textos ----------
const FR = {
  "¿Quién eres?": "Qui es-tu ?", "Elige tu perfil. Se queda guardado en este móvil y ya no se cambia solo.": "Choisis ton profil. Il reste enregistré sur ce téléphone et ne change plus tout seul.",
  "Perfil guardado en este móvil ✅": "Profil enregistré sur ce téléphone ✅",
  "Código FUNDADOR: 19 €/mes para siempre · solo 20 plazas": "Code FUNDADOR : 19 €/mois à vie · seulement 20 places",
  "7 días gratis · luego 29 €/mes": "7 jours gratuits · puis 29 €/mois",
  "Sin conexión o el servidor ha tardado. Vuelve a intentarlo en unos segundos.": "Pas de connexion ou le serveur a tardé. Réessaie dans quelques secondes.",
  "Avisos por Telegram": "Alertes Telegram", "Enviar prueba": "Envoyer un test", "Conectar": "Connecter",
  "Conoce al creador": "Découvre le créateur",
  "Ver vídeo de técnica": "Voir la vidéo technique", "Añadir vídeo": "Ajouter une vidéo", "Técnica": "Technique",
  "Abrir el vídeo": "Ouvrir la vidéo", "Este ejercicio aún no tiene vídeo.": "Cet exercice n'a pas encore de vidéo.",
  "Vídeo para todos en este ejercicio": "Vidéo pour tous sur cet exercice", "Quitar": "Enlever",
  "Sube el vídeo a YouTube (oculto) o Instagram y pega aquí el enlace.": "Mets la vidéo sur YouTube (non répertoriée) ou Instagram et colle le lien ici.",
  "de muestra": "d'exemple", "🔒 Este día se desbloquea con tu perfil": "🔒 Ce jour se débloque avec ton profil",
  "Se te quedó pendiente esta semana": "Il te reste à faire cette semaine", "Ya la hice": "Déjà fait", "Hacerla hoy": "La faire aujourd'hui",
  "Diego ya lo ha hecho. ¿Te lo pones hoy?": "Diego l'a déjà fait. Tu le fais aujourd'hui ?",
  "Toca repetir para comparar": "C'est le moment de refaire pour comparer", "La otra vez": "La dernière fois", "Lo hiciste el": "Tu l'as fait le",
  "En una semana": "Dans une semaine", "Quitar este retest": "Enlever ce retest", "Retest el": "Retest le",
  "Repetir para comparar": "Refaire pour comparer", "Me gusta": "J'aime", "Tu marca ahora": "Ton résultat actuel",
  "Registra hoy tu resultado para poder comparar.": "Enregistre ton résultat aujourd'hui pour pouvoir comparer.",
  "Te lo volvemos a poner en tu día y verás la otra marca al lado.": "On te le remet dans ta journée avec l'ancien résultat à côté.",
  "En 1 mes": "Dans 1 mois", "En 2 meses": "Dans 2 mois", "WODs que más gustan": "Les WOD les plus aimés",
  "Movimiento": "Mouvement", "Cambiar movimiento / reps": "Changer mouvement / reps",
  "Aquí puedes cambiar el movimiento (por ejemplo «Power clean + push jerk»). Los kilos van en el texto de abajo con @.": "Ici tu peux changer le mouvement (par exemple « Power clean + push jerk »). Les kilos vont dans le texte en dessous avec @.",
  "¡Hola Diego! He visto la app Djimenez Prog y me interesa entrenar contigo 💪": "Salut Diego ! J'ai vu l'appli Djimenez Prog et je voudrais m'entraîner avec toi 💪",
  "Entrena con Diego": "Entraîne-toi avec Diego",
  "Escríbele y te cuenta cómo funciona, precios y cómo empezar.": "Écris-lui : il t'explique comment ça marche, les prix et comment commencer.",
  "Contactar con Diego": "Contacter Diego", "Contacto": "Contact", "veces han pulsado «Contactar»": "clics sur « Contacter »",
  "Fuerza": "Force",
  "Volver": "Retour",
  "¿Ya tienes perfil? Entra con tu nombre y PIN": "Tu as déjà un profil ? Entre avec ton nom et ton code",
  "Abonarse": "S'abonner",
  "¡Gracias por abonarte!": "Merci pour ton abonnement !",
  "Estamos comprobando el pago. Déjanos tu teléfono y tu email para darte de alta y escribirte.": "On vérifie le paiement. Laisse-nous ton téléphone et ton e-mail pour t'inscrire et te contacter.",
  "Teléfono": "Téléphone",
  "Enviar": "Envoyer",
  "¡Recibido!": "Bien reçu !",
  "En cuanto Diego compruebe el pago te escribirá para empezar. ¡Nos vemos entrenando! 🔥": "Dès que Diego aura vérifié le paiement, il t'écrira pour commencer. À bientôt à l'entraînement ! 🔥",
  "Vale": "OK",
  "Bienvenido a Djimenez Prog": "Bienvenue sur Djimenez Prog",
  "Estás viendo una rutina de ejemplo. Puedes mirarlo todo: los entrenos, el cronómetro, el progreso…": "Tu regardes un programme d'exemple. Tu peux tout voir : les séances, le chrono, les progrès…",
  "Crear mi perfil": "Créer mon profil",
  "Seguir viendo gratis": "Continuer à regarder gratuitement",
  "Con tu perfil tienes tu propia rutina y guardas tus marcas.": "Avec ton profil, tu as ton propre programme et tu gardes tes records.",
  "Elige un PIN (4 cifras o más)": "Choisis un code (4 chiffres ou plus)",
  "Con tu nombre y este PIN entrarás la próxima vez.": "Tu entreras la prochaine fois avec ton nom et ce code.",
  "Seguir": "Continuer",
  "¡Perfil creado! Bienvenido 🔥": "Profil créé ! Bienvenue 🔥",
  "Modo demo · solo para mirar": "Mode démo · juste pour regarder",
  "Compartir": "Partager",
  "Compartir este entreno": "Partager cette séance",
  "Entreno de hoy con Djimenez Prog 💪": "Séance du jour avec Djimenez Prog 💪",
  "💪 Mira la app de entrenamiento de Diego (Djimenez Prog)": "💪 Regarde l'appli d'entraînement de Diego (Djimenez Prog)",
  "Mírala aquí (entras directo, solo para ver):": "Regarde ici (tu entres directement, juste pour voir) :",
  "La app:": "L'appli :",
  "¡Compartido! 🔥": "Partagé ! 🔥",
  "Código QR": "QR code",
  "No se ha podido crear el QR": "Impossible de créer le QR code",
  "Que lo escaneen con la cámara del móvil: entran directo a la demo, solo para mirar. Cuenta en «Quién usa la app».": "À scanner avec l'appareil photo : on entre directement dans la démo, juste pour regarder. C'est compté dans « Qui utilise l'appli ».",
  "Escaneándolo se abre la app (para entrar hace falta contraseña).": "En le scannant, l'appli s'ouvre (il faut un mot de passe pour entrer).",
  "Copiar el texto": "Copier le texte",
  "Copiado. Pégalo donde quieras": "Copié. Colle-le où tu veux",
  "No se ha podido copiar": "Impossible de copier",
  "Activado: puedes cambiar los pesos de todos.": "Activé : tu peux changer les poids de tout le monde.",
  "puede cambiar sus pesos sin preguntarte": "peut changer ses poids sans te demander",
  "Quién usa la app": "Qui utilise l'appli",
  "Quitar el modo coach en este móvil": "Quitter le mode coach sur ce téléphone",
  "Solo para Diego: con el PIN del coach puedes cambiar los pesos y aprobar los cambios que te piden.": "Réservé à Diego : avec le code du coach, tu peux changer les poids et valider les demandes.",
  "Compartir la app": "Partager l'appli",
  "Modo coach activado": "Mode coach activé",
  "Modo coach quitado": "Mode coach désactivé",
  "💪 Mira la app con la que entreno con Diego (Djimenez Prog)": "💪 Regarde l'appli avec laquelle je m'entraîne avec Diego (Djimenez Prog)",
  "Todo lo que hay en la biblioteca son entrenos. No hay nada que quitar.": "Tout dans la bibliothèque, ce sont des séances. Rien à enlever.",
  "cosas que no son entrenos": "éléments qui ne sont pas des séances",
  "quitadas de la biblioteca": "retirés de la bibliothèque",
  "Solo para ti": "Rien que pour toi",
  "Últimos 14 días": "14 derniers jours",
  "esta semana": "cette semaine",
  "en 30 días": "en 30 jours",
  "entrenos registrados (30 días)": "séances enregistrées (30 jours)",
  "Sin entrenos registrados en 30 días": "Aucune séance enregistrée en 30 jours",
  "último": "dernière",
  "con el QR": "avec le QR code",
  "la app": "l'appli",
  "Cada cuadrito es un día de las últimas 2 semanas (el último es hoy). Naranja = abrió la app ese día.": "Chaque case est un jour des 2 dernières semaines (la dernière, c'est aujourd'hui). Orange = appli ouverte ce jour-là.",
  "Se empieza a contar desde hoy.": "Le comptage commence aujourd'hui.",
  "veces compartido": "partages",
  "han entrado por un enlace": "sont entrés par un lien",
  "Pagos por comprobar": "Paiements à vérifier",
  "perfil": "profil",
  "Comprobado": "Vérifié",
  "Marcar comprobado": "Marquer vérifié",
  "veces han pulsado «Abonarse»": "clics sur « S'abonner »",
  "Los pagos de verdad los ves en Stripe (cada pago lleva el nombre de quien pulsó).": "Les vrais paiements sont dans Stripe (chaque paiement porte le nom de la personne).",
  "El botón aún no sale: falta poner ABONO_URL en Vercel.": "Le bouton n'apparaît pas encore : il manque ABONO_URL dans Vercel.",
  "entrada en total": "entrée au total",
  "entradas en total": "entrées au total",
  "día esta semana": "jour cette semaine",
  "días esta semana": "jours cette semaine",
  "vez compartido": "partage",
  "entreno": "séance",
  "persona ha entrado con su enlace": "personne est entrée avec son lien",
  "personas han entrado con su enlace": "personnes sont entrées avec son lien",
  "perfil creado desde la demo": "profil créé depuis la démo",
  "perfiles creados desde la demo": "profils créés depuis la démo",
  "Hola,": "Salut,", "Semana": "Semaine", "de fuego": "de feu", "Entrar": "Entrer", "Contraseña": "Mot de passe",
  "Tu entrenamiento, tu progresión": "Ton entraînement, ta progression",
  "¿Eres nuevo? Entra con el código que te ha dado Diego": "Nouveau ? Entre avec le code que Diego t'a donné",
  "partes hechas": "parties faites", "de": "sur", "Hecho": "Fait", "No hecho": "Pas fait",
  "Sin validar": "Pas encore validé", "Marca cada parte como hecha o pásala a otro día.": "Marque chaque partie comme faite ou reporte-la.",
  "Pendiente de": "Reporté de", "Parte": "Partie", "Rutina": "Programme", "Registrar": "Enregistrer", "Progreso": "Progrès",
  "Récords": "Records", "Biblioteca": "Bibliothèque", "Cambiar peso": "Changer le poids", "Guardar": "Enregistrer",
  "Solo esta semana": "Seulement cette semaine", "Mover igual el mismo ejercicio en los otros días": "Changer pareil le même exercice les autres jours",
  "Ajustes": "Réglages", "Nivel en WODs": "Niveau des WOD", "Idioma": "Langue", "Salir": "Se déconnecter",
  "Personas": "Personnes", "por definir": "à définir", "falta el peso": "poids manquant",
  "RX · Inter · Scaled por movimiento": "RX · Inter · Scaled par mouvement", "Versiones": "Versions",
  "No lo hice (repite peso la semana que viene)": "Pas fait (même poids la semaine prochaine)",
  "No lo hice · te lo recuerdo esta semana": "Pas fait · je te le rappelle cette semaine",
  "Terminé la semana": "J'ai fini la semaine", "pasar a la": "passer à la", "Marcar esta semana como la actual": "Marquer cette semaine comme actuelle",
  "Pronto": "Bientôt", "Esto llega en la siguiente fase.": "Ça arrive dans la prochaine étape.",
  "Mientras, está en la app de siempre:": "En attendant, c'est dans l'appli habituelle :", "Abrir la app de siempre": "Ouvrir l'appli habituelle",
  "Sin ejercicios este día.": "Pas d'exercices ce jour-là.", "semana actual": "semaine actuelle",
  "Tu nombre": "Ton prénom", "Tu PIN (4 cifras o más)": "Ton code (4 chiffres ou plus)", "¿Con qué rutina empiezas?": "Quel programme ?",
  "Empezar": "Commencer", "Bienvenida": "Bienvenue", "Bienvenido": "Bienvenue", "Fijar": "Fixer",
  "WOD de Diego · semana": "WOD de Diego · semaine", "Ciclo · semana": "Cycle · semaine",
  "Registrar resultados": "Enregistrer les résultats", "Tipo": "Type", "Partes que has hecho": "Parties faites",
  "Se marcan como hechas al guardar.": "Elles seront marquées comme faites.", "Título": "Titre", "Fecha": "Date",
  "Duración total": "Durée totale", "Resultados": "Résultats", "Ejercicio": "Exercice", "Resultado": "Résultat",
  "Añadir resultado": "Ajouter un résultat", "Notas": "Notes", "Foto": "Photo", "Añadir": "Ajouter", "Cambiar": "Changer",
  "Guardar entreno": "Enregistrer la séance", "Guardando…": "Enregistrement…", "Sensaciones, escalado, qué falló…": "Sensations, adaptations…",
  "Tiempos como 4:35. Escribe cada ejercicio siempre igual para ver su progresión.": "Temps comme 4:35. Écris chaque exercice toujours pareil pour suivre ta progression.",
  "Esa foto no se puede leer. Prueba con otra o haz una captura.": "Impossible de lire cette photo. Essaie avec une autre.",
  "Prepárate": "Prépare-toi", "rondas": "tours", "ronda": "tour", "Minuto": "Minute", "Tope": "Limite",
  "Sin tope": "Sans limite", "cada": "toutes les", "Reiniciar": "Réinitialiser", "Pausa": "Pause", "Empezar": "Démarrer",
  "Sumar ronda": "Ajouter un tour", "Terminar y guardar": "Terminer et enregistrer", "Libre": "Libre",
  "Va en marcha: pulsa otra vez para salir": "Le chrono tourne : appuie encore pour sortir", "Total": "Total", "Cada": "Toutes les", "Reloj": "Chrono", "Cronómetro": "Chronomètre", "Cuenta atrás": "Compte à rebours",
  "Tabata": "Tabata", "Minutos": "Minutes", "Trabajo": "Travail", "Descanso": "Repos", "Rondas": "Tours", "TRABAJO": "TRAVAIL",
  "DESCANSO": "REPOS", "sin tope": "sans limite", "tope": "limite", "total": "total", "¡Terminado!": "Terminé !",
  "Guardar como entreno": "Enregistrer comme séance", "Proponer un cambio": "Proposer un changement",
  "Los pesos los pone tu coach": "C'est ton coach qui fixe les poids",
  "¿Le has preguntado a Diego si este cambio es pertinente? Si se lo envías, lo aprueba él y se cambia solo.": "As-tu demandé à Diego si ce changement est pertinent ? Envoie-le-lui : s'il l'approuve, il se change tout seul.",
  "Pendiente de aprobar": "En attente d'approbation", "Mensaje para Diego (opcional)": "Message pour Diego (optionnel)",
  "Ej.: la semana pasada me salió fácil": "Ex. : la semaine dernière c'était facile", "Enviar a Diego para que lo apruebe": "Envoyer à Diego pour approbation",
  "pendiente": "en attente", "Solicitudes": "Demandes", "Modo coach": "Mode coach", "Activar": "Activer",
  "Cambios que te piden": "Changements demandés", "Rechazar": "Refuser", "Aprobar": "Approuver", "No hay nada pendiente.": "Rien en attente.",
  "Solo esa semana": "Seulement cette semaine-là", "Mis récords": "Mes records", "Resumen": "Résumé", "Historial": "Historique",
  "Evolución": "Évolution", "mejor marca": "meilleure marque", "Entrenos por semana": "Séances par semaine", "sin entrenos": "aucune séance",
  "Semana del": "Semaine du", "entrenos en 30 días": "séances en 30 jours", "partes hechas (4 sem.)": "parties faites (4 sem.)",
  "semana seguida": "semaine d'affilée", "semanas seguidas": "semaines d'affilée", "Dónde mejorar": "Où progresser",
  "Progresión por ejercicio": "Progression par exercice", "Mejor": "Meilleure", "Última": "Dernière", "Desde el inicio": "Depuis le début",
  "registros": "enregistrements", "En tiempos, arriba es más rápido. El punto negro es tu mejor marca.": "Pour les temps, en haut = plus rapide. Le point noir est ta meilleure marque.",
  "Arriba es mejor. El punto negro es tu mejor marca.": "En haut = mieux. Le point noir est ta meilleure marque.",
  "Cuando registres resultados (kg, tiempos, reps…) verás aquí tu progresión.": "Quand tu enregistres des résultats, ta progression apparaît ici.",
  "Aún no hay entrenos. Pulsa + para guardar el primero.": "Pas encore de séances. Appuie sur + pour la première.", "Todos": "Tous",
  "entrenos": "séances", "Ver foto": "Voir la photo", "¿Seguro? Pulsa otra vez": "Sûr ? Appuie encore", "Borrar": "Supprimer",
  "Este perfil no tiene récords.": "Ce profil n'a pas de records.", "Último PR": "Dernier record", "Apuntar un PR": "Noter un record",
  "este mes": "ce mois-ci", "Todavía no hay PRs. Apunta el primero.": "Pas encore de records.", "Récord": "Record",
  "de un registro": "d'un enregistrement", "Cuando tengas más marcas de este movimiento verás aquí su evolución.": "Avec plus de marques, tu verras l'évolution ici.",
  "Movimiento": "Mouvement", "Otro…": "Autre…", "¿Cuál?": "Lequel ?", "Marca": "Marque", "Reps (1 = 1RM)": "Reps (1 = 1RM)",
  "Nota": "Note", "con cinturón…": "avec ceinture…", "Guardar PR": "Enregistrer le record",
  "Salen solos de lo que registras si el ejercicio se llama igual (por ejemplo «Back squat», «RMU» o «5 km run»).": "Ils viennent aussi de tes séances si l'exercice a le même nom.", "¿Eres Diego? Mete tu PIN de coach y lo cambias directamente": "Tu es Diego ? Mets ton PIN de coach", "Ajustar": "Ajuster", "Quitar el cambio de esta semana": "Annuler le changement de cette semaine", "Limpiar la biblioteca": "Nettoyer la bibliothèque", "Quitarlas": "Les supprimer", "Al azar": "Au hasard", "Otro": "Un autre", "Usar este": "Utiliser celui-ci", "Ahora": "Actuel", "No hay más ideas de este tipo todavía": "Pas encore d'autres idées de ce type", "ideas de este tipo (tu biblioteca y el repertorio)": "idées de ce type (ta bibliothèque et le répertoire)", "Último": "Dernier", "Ajustar reps": "Ajuster les reps", "Semana que viene": "Semaine prochaine",
  "Cambiar esta parte": "Changer cette partie", "Añadir parte": "Ajouter une partie", "Novedad de Diego": "Nouveauté de Diego",
  "Diego se lo ha puesto. ¿Te viene bien hoy?": "Diego l'a fait. Ça te va aujourd'hui ?", "Hoy no": "Pas aujourd'hui",
  "Ponérmelo hoy": "Je le fais aujourd'hui", "Lo programa tu coach": "C'est ton coach qui programme",
  "Ej.: no llegaba a 8+8, he hecho 8+5": "Ex. : je n'arrivais pas à 8+8, j'ai fait 8+5", "Esta y las siguientes": "Celle-ci et les suivantes",
  "Nombre": "Nom", "Esta semana": "Cette semaine", "Ajustar también la semana que viene": "Ajuster aussi la semaine prochaine",
  "ciclo": "cycle", "Escribe qué toca": "Écris le programme", "Volver a lo que había": "Revenir à l'original", "opcional": "optionnel",
  "Qué toca": "Au programme", "Ideas": "Idées", "Sin ideas guardadas para este tipo todavía.": "Pas encore d'idées pour ce type.", "Tiempo total": "Temps total",
};
const t = (s) => (E.lang === "fr" && FR[s]) || s;
// datos que vienen escritos en español (nombres de día, fechas, tipos): en francés se traducen al enseñarlos
const MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
const DIAS_SEM = { lun: "lun.", mar: "mar.", "mié": "mer.", jue: "jeu.", vie: "ven.", "sáb": "sam.", dom: "dim." };
const trDia = (x) => E.lang !== "fr" || !x ? x : String(x).replace(/\bD[ií]a\b/g, "Jour").replace(/\bSemana\b/g, "Semaine")
  .replace(/\bDescanso\b/gi, "Repos");
const trFecha = (x) => {
  if (E.lang !== "fr" || !x) return x;
  const mes = (m) => { const i = MESES_ES.indexOf(m); return i < 0 ? m : MESES_FR[i]; };
  let m = String(x).match(/^(lun|mar|mié|jue|vie|sáb|dom) (\d+) (\S+) (\d{4})$/);
  if (m) return `${DIAS_SEM[m[1]]} ${m[2]} ${mes(m[3])} ${m[4]}`;
  m = String(x).match(/^(\d+) (\S+)( \d{4})?$/);
  return m ? `${m[1]} ${mes(m[2])}${m[3] || ""}` : x;
};
const TIPO_FR = { fuerza: "Force", wod: "WOD", gym: "Gym", endurance: "Endurance", otro: "Autre" };
const UNIDAD_FR = { tiempo: "temps", rondas: "tours" };
const trTipo = (k, n) => E.lang === "fr" ? (TIPO_FR[k] || n) : n;
const trUnidad = (u) => E.lang === "fr" ? (UNIDAD_FR[u] || u) : u;

// ---------- utilidades ----------
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = (v) => { const r = Math.round(v * 100) / 100; return Number.isInteger(r) ? String(r) : String(r).replace(".", ","); };
const ic = {
  llama: (c = "#FFB400", s = 54) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="${c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2c1 3.5 5 5.5 5 10a5 5 0 0 1-10 0c0-2.2 1-3.6 2.2-4.8C9.6 9.4 10 11 11 11.6 11 8 11.6 4.6 12 2z"/><path d="M12 22a2.6 2.6 0 0 1-2.6-2.6c0-1.6 1.4-2.4 2.6-4 1.2 1.6 2.6 2.4 2.6 4A2.6 2.6 0 0 1 12 22z"/></svg>`,
  izq: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFB400" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>`,
  der: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFB400" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>`,
  abajo: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>`,
  ok: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>`,
  x: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1F1208" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>`,
  ajustes: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1F1208" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/></svg>`,
  calendario: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="4" y="5" width="16" height="15" rx="3"/><path d="M8 3v4M16 3v4M4 10h16"/></svg>`,
  mas: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>`,
  grafica: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19l5-6 4 3 7-9"/></svg>`,
  copa: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M8 4h8v5a4 4 0 0 1-8 0zM12 13v4M8 20h8M6 5H4a2 2 0 0 0 2 4M18 5h2a2 2 0 0 1-2 4"/></svg>`,
  libros: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M5 4h4v16H5zM10 4h4v16h-4zM15.5 4.5l3.8 1-3.6 14.6-3.8-1z"/></svg>`,
  estrella: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1F1208" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.8z"/></svg>`,
  lapiz: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:inline;vertical-align:-2px"><path d="M4 20h4L19 9l-4-4L4 16zM14 6l4 4"/></svg>`,
  puntos: `<svg width="22" height="22" viewBox="0 0 24 24" fill="#8A6A52" aria-hidden="true"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>`,
  candado: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true" style="display:inline;vertical-align:-3px"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>`,
  campana: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1F1208" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4zM10 21h4"/></svg>`,
  reloj: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6M12 2v3"/></svg>`,
  camara: `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>`,
  play: `<svg width="30" height="30" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z"/></svg>`,
  pausa: `<svg width="28" height="28" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>`,
  reinicio: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 12a8 8 0 1 0 3-6.2M4 4v5h5"/></svg>`,
  ciclo: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 12a8 8 0 0 1 14-5.3M20 12a8 8 0 0 1-14 5.3M18 3v4h-4M6 21v-4h4"/></svg>`,
};
ic.qr = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3M21 14v7h-7M17 21v-1"/></svg>`;
ic.compartir = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>`;
const inicial = (n) => (n || "?").split(/\s+/).map((p) => p[0]).join("").slice(0, 2).toUpperCase();

function aviso(msg, mal = false) {
  $aviso.textContent = msg;
  $aviso.className = "aviso" + (mal ? " mal" : "");
  $aviso.hidden = false;
  clearTimeout(aviso._t);
  aviso._t = setTimeout(() => { $aviso.hidden = true; }, mal ? 4200 : 2200);
}

async function api(ruta, { metodo = "GET", cuerpo, q } = {}) {
  const url = new URL("api/" + ruta, location.href);
  Object.entries(q || {}).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
  let r;
  try { r = await fetch(url, {
    method: metodo, headers: { "Content-Type": "application/json", ...(E.token ? { Authorization: "Bearer " + E.token } : {}) },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  }); } catch (e) {
    throw new Error(t("Sin conexión o el servidor ha tardado. Vuelve a intentarlo en unos segundos."));
  }
  let d = {};
  try { d = await r.json(); } catch { }
  if (r.status === 401 && ruta !== "login") { salir(); throw new Error(d.error || "Entra otra vez"); }
  if (!r.ok) throw new Error(d.error || "Algo ha fallado (" + r.status + ")");
  return d;
}

function salir() {
  E.token = null; E.vista = null; mem.set("token", null); mem.set("atleta", null); mem.set("perfil_fijo", null);
  cerrarHoja(); pintarEntrar();
}

// ---------- entrar ----------
function pintarEntrar(paso = {}) {
  $app.className = "";
  const inv = paso.invitado;
  $app.innerHTML = `
  <section class="entrar">
    <div class="marca">
      <div class="logo">${ic.llama()}</div>
      <h1>Djimenez Prog</h1>
      <p>${t("Tu entrenamiento, tu progresión")}</p>
    </div>
    <form class="tarjeta-entrar" id="f-entrar" autocomplete="on">
      ${inv ? `
        <strong style="font-size:18px">${t("Bienvenido")} · Bienvenue</strong>
        <label for="i-nombre">${t("Tu nombre")}</label>
        <input class="campo" id="i-nombre" autocomplete="given-name" value="${esc(paso.nombre || "")}" required>
        <label for="i-pin">${t("Tu PIN (4 cifras o más)")}</label>
        <input class="campo" id="i-pin" type="password" inputmode="numeric" autocomplete="off" value="${esc(paso.pin || "")}" required>
        ${paso.nuevo ? `<span style="font-weight:600;font-size:14px">${t("¿Con qué rutina empiezas?")}</span>
          <div class="opciones-radio">${Object.entries(paso.plantillas || {}).map(([k, v], i) =>
            `<label class="interruptor"><span>${esc(v)}</span><input type="radio" name="plantilla" value="${esc(k)}" ${i === 0 ? "checked" : ""}></label>`).join("")}</div>` : ""}
      ` : `
        <label for="i-pass">${E.lang === "fr" ? "Mot de passe" : "Contraseña · Mot de passe"}</label>
        <input class="campo" id="i-pass" type="password" autocomplete="current-password" required>
      `}
      <p class="error" id="e-entrar" hidden></p>
      <button class="btn btn-fuego" type="submit">${inv && paso.nuevo ? t("Empezar") : t("Entrar")}</button>
      ${inv ? (paso.conPin ? `<button type="button" class="btn" id="b-volver-entrar" style="height:44px">← ${t("Volver")}</button>` : "") : `<p class="ayuda">${t("¿Eres nuevo? Entra con el código que te ha dado Diego")}</p>
        <button type="button" class="btn" id="b-con-pin" style="height:44px">${t("¿Ya tienes perfil? Entra con tu nombre y PIN")}</button>`}
    </form>
    <div class="fila-chips" style="justify-content:center">
      <button class="chip ${E.lang === "es" ? "on" : ""}" data-lang="es">ES</button>
      <button class="chip ${E.lang === "fr" ? "on" : ""}" data-lang="fr">FR</button>
    </div>
  </section>`;
  $app.querySelectorAll("[data-lang]").forEach((b) => b.onclick = () => { E.lang = b.dataset.lang; mem.set("lang", E.lang); mem.set("lang_elegido", "1"); pintarEntrar(paso); });
  const bcp = document.getElementById("b-con-pin");
  if (bcp) bcp.onclick = () => pintarEntrar({ invitado: true, conPin: true });
  const bve = document.getElementById("b-volver-entrar");
  if (bve) bve.onclick = () => pintarEntrar();
  const f = document.getElementById("f-entrar");
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    const err = document.getElementById("e-entrar");
    const boton = f.querySelector("button[type=submit]");
    const cuerpo = paso.conPin ? { perfil: true, nombre: f.querySelector("#i-nombre").value, pin: f.querySelector("#i-pin").value }
      : inv ? { password: paso.password, nombre: f.querySelector("#i-nombre").value, pin: f.querySelector("#i-pin").value,
      plantilla: (f.querySelector("input[name=plantilla]:checked") || {}).value } : { password: f.querySelector("#i-pass").value };
    boton.disabled = true; err.hidden = true;
    try {
      const r = await api("login", { metodo: "POST", cuerpo });
      if (r.invitado) return pintarEntrar({ invitado: true, nuevo: r.nuevo, plantillas: r.plantillas, password: cuerpo.password,
        nombre: cuerpo.nombre, pin: cuerpo.pin });
      E.token = r.token; mem.set("token", r.token);
      if (r.solo) { E.atleta = r.solo; mem.set("atleta", r.solo); }
      if (!r.demo && !mem.get("lang_elegido")) { E.lang = r.lang || E.lang; mem.set("lang", E.lang); }
      await cargar();
    } catch (e) {
      err.textContent = e.message; err.hidden = false; boton.disabled = false;
    }
  };
  setTimeout(() => (f.querySelector("input") || {}).focus?.(), 50);
}

// ---------- cargar y pintar la rutina ----------
async function cargar(opc = {}) {
  try {
    const v = await api("vista", { q: { atleta: opc.atleta ?? E.atleta, semana: opc.semana ?? E.semana, dia: opc.dia ?? E.dia } });
    poner(v);
  } catch (e) {
    if (E.token) { aviso(e.message, true); if (!E.vista) pintarError(e.message); }
  }
}

function poner(v) {
  E.vista = v; E.atleta = v.atleta; mem.set("atleta", v.atleta);
  E.semana = v.semana; E.dia = v.dia && v.dia.id;
  if (v.solo && v.lang && !mem.get("lang_elegido")) E.lang = v.lang;
  pintar();
  if (v.pr) { aviso("🎉 " + v.pr); confeti(); } else if (v.aviso) aviso(v.aviso);
  if (E.pagoCs !== undefined && !E.pagoMostrado) { E.pagoMostrado = true; E.bienvenidaDemo = true; setTimeout(() => hojaPago(E.pagoCs), 300); }
  if (!v.solo && !v.demo && !v.coach && !mem.get("perfil_fijo") && !E.quienMostrado && $hoja.hidden) { E.quienMostrado = true; setTimeout(hojaQuienEres, 300); }
  if (v.demo && !E.bienvenidaDemo && E.pantalla !== "registrar") { E.bienvenidaDemo = true; setTimeout(hojaBienvenidaDemo, 450); }
}

// ---------- demo: crear tu perfil o seguir mirando ----------
async function abonarse() {
  if (E.vista && !E.vista.abono && E.vista.contacto) return hojaContacto();
  const w = window.open("", "_blank");  // se abre ya (si no, el móvil lo bloquea) y luego se le pone el enlace
  try {
    const r = await api("abonarse", { metodo: "POST", cuerpo: { atleta: E.atleta } });
    if (w) w.location = r.url; else location.href = r.url;
  } catch (e) { if (w) w.close(); aviso(e.message, true); }
}
function hojaContacto() {
  const c = (E.vista || {}).contacto || {};
  const msg = encodeURIComponent(t("¡Hola Diego! He visto la app Djimenez Prog y me interesa entrenar contigo 💪"));
  const ops = [
    c.whatsapp && `<a class="btn btn-wa" data-via="whatsapp" href="https://wa.me/${esc(c.whatsapp)}?text=${msg}" target="_blank" rel="noopener">💬 WhatsApp</a>`,
    c.email && `<a class="btn btn-negro" data-via="email" href="mailto:${esc(c.email)}?subject=${encodeURIComponent("Djimenez Prog")}&body=${msg}">✉️ ${esc(c.email)}</a>`,
    c.instagram && `<a class="btn" data-via="instagram" href="https://instagram.com/${esc(c.instagram)}" target="_blank" rel="noopener">📸 @${esc(c.instagram)}</a>`,
  ].filter(Boolean).join("");
  abrirHoja(`<div class="demo-hola">${ic.llama("#FF6A00", 40)}<h3>${t("Entrena con Diego")}</h3>
      <p>${t("Escríbele y te cuenta cómo funciona, precios y cómo empezar.")}</p></div>${ops}
    <button class="btn" data-cerrar>👀 ${t("Seguir viendo gratis")}</button>`, (h) => {
    h.querySelectorAll("[data-via]").forEach((a) => a.addEventListener("click", () => {
      api("contactar", { metodo: "POST", cuerpo: { via: a.dataset.via, atleta: E.atleta } }).catch(() => { });
    }));
  });
}
const botonContacto = (v, id) => !v.abono && v.contacto ? `<button class="btn btn-abono" id="${id}">💬 ${t("Contactar con Diego")}</button>` : "";
const botonAbono = (v, id, extra = "") => !v.abono ? botonContacto(v, id) : `<button class="btn btn-abono" id="${id}" ${extra}>💳 ${t("Abonarse")}${v.abono.texto ? ` <small>${esc(t(v.abono.texto))}</small>` : ""}</button>
  <p class="promo-fundador">🎟️ ${t("Código FUNDADOR: 19 €/mes para siempre · solo 20 plazas")}</p>`;

function hojaPago(cs) {
  const v = E.vista || {};
  abrirHoja(`<div class="demo-hola"><div class="pago-ok">✓</div>
      <h3>${t("¡Gracias por abonarte!")}</h3>
      <p>${t("Estamos comprobando el pago. Déjanos tu teléfono y tu email para darte de alta y escribirte.")}</p></div>
    <form id="f-pago" style="display:flex;flex-direction:column;gap:10px">
      <label class="paso-etq" for="pg-nombre" style="margin:0 4px">${t("Tu nombre")}</label>
      <input class="campo" id="pg-nombre" autocomplete="name" style="background:#fff" value="${esc(v.demo ? "" : (v.nombre || ""))}" required>
      <label class="paso-etq" for="pg-tel" style="margin:0 4px">${t("Teléfono")}</label>
      <input class="campo" id="pg-tel" type="tel" autocomplete="tel" inputmode="tel" placeholder="+34 600 000 000" style="background:#fff" required>
      <label class="paso-etq" for="pg-email" style="margin:0 4px">Email</label>
      <input class="campo" id="pg-email" type="email" autocomplete="email" inputmode="email" placeholder="tu@email.com" style="background:#fff" required>
      <p class="error" id="pg-error" hidden></p>
      <button class="btn btn-abono" type="submit" style="height:54px">${t("Enviar")}</button>
    </form>`, (h) => {
    const f = h.querySelector("#f-pago");
    f.onsubmit = async (ev) => {
      ev.preventDefault();
      const err = h.querySelector("#pg-error"); const boton = f.querySelector("button");
      boton.disabled = true; err.hidden = true;
      try {
        await api("datos_pago", { metodo: "POST", cuerpo: { cs, nombre: h.querySelector("#pg-nombre").value,
          telefono: h.querySelector("#pg-tel").value, email: h.querySelector("#pg-email").value } });
        mem.set("pago_pendiente", null);
        h.innerHTML = `<div class="asa"></div><div class="demo-hola"><div class="pago-ok">✓</div><h3>${t("¡Recibido!")}</h3>
          <p>${t("En cuanto Diego compruebe el pago te escribirá para empezar. ¡Nos vemos entrenando! 🔥")}</p></div>
          <button class="btn btn-fuego" data-cerrar>${t("Vale")}</button>`;
        h.querySelector("[data-cerrar]").onclick = cerrarHoja;
      } catch (e) { err.textContent = e.message; err.hidden = false; boton.disabled = false; }
    };
  });
}

// página «Conoce al creador» (la de Diego), en el idioma de cada uno
const urlCreador = () => E.lang === "fr" ? "https://conoce-al-creador.vercel.app/?lang=fr#profesor"
  : "https://conoce-al-creador.vercel.app/?lang=es#traductor";
const botonCreador = (extra = "") => `<a class="btn btn-creador" href="${urlCreador()}" target="_blank" rel="noopener" ${extra}>👤 ${t("Conoce al creador")}</a>`;

function hojaBienvenidaDemo() {
  if (!$hoja.hidden) return;
  abrirHoja(`<div class="demo-hola">${ic.llama("#FF6A00", 44)}
      <h3>${t("Bienvenido a Djimenez Prog")}</h3>
      <p>${t("Estás viendo una rutina de ejemplo. Puedes mirarlo todo: los entrenos, el cronómetro, el progreso…")}</p></div>
    <button class="btn btn-fuego" id="d-crear" style="height:56px">✨ ${t("Crear mi perfil")}</button>
    ${botonAbono(E.vista, "d-abono")}
    <button class="btn" id="d-seguir">👀 ${t("Seguir viendo gratis")}</button>
    <p class="mini" style="text-align:center;margin:0">${t("Con tu perfil tienes tu propia rutina y guardas tus marcas.")}</p>
    ${botonCreador()}`, (h) => {
    h.querySelector("#d-crear").onclick = () => hojaCrearPerfil({});
    h.querySelector("#d-seguir").onclick = cerrarHoja;
    const da = h.querySelector("#d-abono"); if (da) da.onclick = abonarse;
  });
}
function hojaCrearPerfil(paso) {
  abrirHoja(`${cabHoja("Djimenez Prog", t("Crear mi perfil"))}
    <form id="f-perfil" style="display:flex;flex-direction:column;gap:10px">
      <label class="paso-etq" for="cp-nombre" style="margin:0 4px">${t("Tu nombre")}</label>
      <input class="campo" id="cp-nombre" autocomplete="given-name" style="background:#fff" value="${esc(paso.nombre || "")}" required>
      <label class="paso-etq" for="cp-pin" style="margin:0 4px">${t("Elige un PIN (4 cifras o más)")}</label>
      <input class="campo" id="cp-pin" type="password" inputmode="numeric" autocomplete="new-password" style="background:#fff" value="${esc(paso.pin || "")}" required>
      <p class="mini" style="margin:0 4px">${t("Con tu nombre y este PIN entrarás la próxima vez.")}</p>
      ${paso.plantillas ? `<span class="paso-etq" style="margin:4px 4px 0">${t("¿Con qué rutina empiezas?")}</span>
        <div class="opciones-radio">${Object.entries(paso.plantillas).map(([k, v], i) =>
          `<label class="interruptor"><span>${esc(v)}</span><input type="radio" name="cp-plantilla" value="${esc(k)}" ${i === 0 ? "checked" : ""}></label>`).join("")}</div>` : ""}
      <p class="error" id="cp-error" hidden></p>
      <button class="btn btn-fuego" type="submit" style="height:54px">${paso.plantillas ? t("Empezar") : t("Seguir")}</button>
    </form>
    <button class="btn" id="cp-volver">👀 ${t("Seguir viendo gratis")}</button>`, (h) => {
    h.querySelector("#cp-volver").onclick = cerrarHoja;
    const f = h.querySelector("#f-perfil");
    f.onsubmit = async (ev) => {
      ev.preventDefault();
      const err = h.querySelector("#cp-error"); const boton = f.querySelector("button[type=submit]");
      const cuerpo = { nombre: h.querySelector("#cp-nombre").value, pin: h.querySelector("#cp-pin").value,
        plantilla: (h.querySelector("input[name=cp-plantilla]:checked") || {}).value };
      boton.disabled = true; err.hidden = true;
      try {
        const r = await api("crear_perfil", { metodo: "POST", cuerpo });
        if (!r.token) return hojaCrearPerfil({ ...cuerpo, plantillas: r.plantillas });
        E.token = r.token; mem.set("token", r.token);
        E.atleta = r.solo; mem.set("atleta", r.solo); E.semana = null; E.dia = null;
        cerrarHoja(); aviso(t("¡Perfil creado! Bienvenido 🔥")); confeti(); cargar();
      } catch (e) { err.textContent = e.message; err.hidden = false; boton.disabled = false; }
    };
    setTimeout(() => h.querySelector(paso.nombre ? "#cp-pin" : "#cp-nombre").focus(), 80);
  });
}

function pintarError(msg) {
  $app.className = "";
  $app.innerHTML = `<div class="vacio" style="padding-top:120px"><p><b>No se ha podido cargar</b></p><p class="mini">${esc(msg)}</p>
    <p><button class="btn btn-fuego" id="b-reint">Reintentar</button></p><p><button class="btn" id="b-salir">${t("Salir")}</button></p></div>`;
  document.getElementById("b-reint").onclick = () => cargar();
  document.getElementById("b-salir").onclick = salir;
}

async function hacer(cuerpo, boton) {
  if (E.ocupado) return;
  E.ocupado = true;
  if (boton) boton.classList.add("espera");
  try {
    const v = await api("accion", { metodo: "POST", cuerpo: { atleta: E.atleta, ver_semana: E.semana, ver_dia: E.dia, ...cuerpo } });
    poner(v);
  } catch (e) {
    aviso(e.message, true);
    if (boton) boton.classList.remove("espera");
  } finally { E.ocupado = false; }
}

function pintar() {
  const v = E.vista;
  const tip = document.getElementById("tip");
  if (tip) tip.hidden = true;
  $app.className = "";
  desbloquearScroll();
  if (E.pantalla === "registrar") return pintarRegistrar();
  if (E.pantalla === "progreso" || E.pantalla === "prs") return pintarPantalla();
  if (v.sin_rutina) {
    $app.innerHTML = cabecera(v) + `<main><div class="vacio"><p><b>${esc(v.nombre)}</b> todavía no tiene rutina.</p>
      <p class="mini">Créala en la app de siempre y aparecerá aquí.</p></div></main>` + nav();
    enlazar(); return;
  }
  const cuentan = v.partes.filter((p) => !p.calentamiento);
  const hechas = cuentan.filter((p) => p.estado === "hecho").length;
  const total = cuentan.length;
  $app.innerHTML = cabecera(v) + `
  <main>
    <div class="titulo-dia"><h2>${esc(trDia(v.dia.nombre))}</h2><span>${total ? `${hechas} ${t("de")} ${total} ${t("partes hechas")}` : ""}</span></div>
    <div class="barra"><i style="width:${total ? Math.round(hechas / total * 100) : 0}%"></i></div>
    ${(v.novedades || []).map((n) => `<section class="novedad">
      <div class="nov-cab">${ic.llama("#FFB400", 22)}<div><small>${t("Novedad de Diego")} · ${esc(n.etiqueta)}</small><b>${esc(n.nombre)}</b></div></div>
      <div class="texto-wod">${esc(n.texto)}</div>
      <div class="mini" style="color:#FFD9BD">${t("Diego ya lo ha hecho. ¿Te lo pones hoy?")}</div>
      <div class="nov-botones"><button class="btn" data-nov-no="${esc(n.id)}">${t("Hoy no")}</button>
        <button class="btn btn-fuego" data-nov-si="${esc(n.id)}" style="height:50px">${t("Ponérmelo hoy")}</button></div>
    </section>`).join("")}
    ${(v.retests || []).map((x) => `<section class="novedad retest">
      <div class="nov-cab"><span style="font-size:22px">🔁</span><div><small>${t("Toca repetir para comparar")} · ${esc(x.etiqueta)}</small><b>${esc(x.nombre)}</b></div></div>
      <div class="texto-wod">${esc(x.texto)}</div>
      <div class="mini" style="color:#FFD9BD">${x.antes ? `${t("La otra vez")} (${esc(trFecha(x.creado))}): <b style="color:#fff">${esc(x.antes.valor)}</b>` : `${t("Lo hiciste el")} ${esc(trFecha(x.creado))}`}</div>
      <div class="nov-botones"><button class="btn" data-rt-semana="${esc(x.id)}">${t("En una semana")}</button>
        <button class="btn btn-fuego" data-rt-si="${esc(x.id)}" style="height:50px">${t("Ponérmelo hoy")}</button></div>
      <button class="mini-btn" data-rt-no="${esc(x.id)}" style="align-self:center;color:#FFD9BD;border-color:transparent;background:transparent;text-decoration:underline">${t("Quitar este retest")}</button>
    </section>`).join("")}
    ${(v.olvidadas || []).length ? `<section class="olvidadas"><b>⏰ ${t("Se te quedó pendiente esta semana")}</b>
      ${v.olvidadas.map((o, i) => `<div class="olv"><span><small>${esc(o.dia_txt)}${o.letra ? " · " + esc(o.letra) : ""}</small>${o.tipo === "linea" ? `${esc(o.nombre)} <small style="display:inline;font-weight:600">${esc((o.texto || "").split("\n")[0].slice(0, 40))}</small>` : `${esc(etqParte(o.etiqueta))}${o.nombre && o.nombre !== o.etiqueta ? ` · ${esc(o.nombre)}` : ""}`}</span>
        <button class="chip" data-olv-hecha="${i}">✓ ${t("Ya la hice")}</button><button class="chip on" data-olv-hoy="${i}">${t("Hacerla hoy")}</button></div>`).join("")}
    </section>` : ""}
    ${v.faltan.length && v.semana < v.actual ? `<div class="alerta"><b>${t("Sin validar")} · S${v.semana}:</b> ${esc(v.faltan.join("; "))}. ${t("Marca cada parte como hecha o pásala a otro día.")}</div>` : ""}
    ${v.partes.length ? v.partes.map((p, i) => tarjeta(p, "p" + i)).join("") : `<div class="vacio">${t("Sin ejercicios este día.")}</div>`}
    ${v.pendientes.length ? `<div class="seccion">${ic.ciclo} ${t("Pendiente de")}…</div>` + v.pendientes.map((p, i) => tarjeta(p, "q" + i)).join("") : ""}
    <button class="btn btn-punteado" id="b-anadir-parte">+ ${t("Añadir parte")}</button>
    ${v.partes.length ? `<button class="btn btn-fuego" id="b-registrar-dia">${ic.mas} ${t("Registrar resultados")}</button>` : ""}
    ${finSemana(v)}
  </main>` + nav();
  enlazar();
}

function cabecera(v) {
  const varias = v.personas.length > 1;
  return `
  <header class="cabecera">
    <div class="fila-cab">
      <button class="quien" id="b-persona" ${varias ? "" : "disabled"} aria-label="${t("Personas")}">
        <span class="avatar">${esc(inicial(v.nombre))}</span>
        <span><small>${t("Hola,")}</small><strong>${esc(v.nombre)} ${varias ? `<span style="color:#fff">${ic.abajo}</span>` : ""}</strong></span>
      </button>
      <div style="display:flex;gap:8px">
        ${v.coach && v.solicitudes && v.solicitudes.length ? `<button class="redondo campana" id="b-solicitudes" aria-label="${t("Solicitudes")}">${ic.campana}<i>${v.solicitudes.length}</i></button>` : ""}
        <button class="redondo" id="b-reloj" aria-label="${t("Reloj")}">${ic.reloj.replace("currentColor", "#1F1208")}</button>
        <button class="redondo" id="b-ajustes" aria-label="${t("Ajustes")}">${ic.ajustes}</button>
      </div>
    </div>
    ${v.demo ? `<div class="banda-demo">👀 ${t("Modo demo · solo para mirar")} <button id="b-crear-demo">✨ ${t("Crear mi perfil")}</button>${v.abono ? `<button id="b-abono-demo">💳 ${t("Abonarse")}</button>` : v.contacto ? `<button id="b-abono-demo">💬 ${t("Contacto")}</button>` : ""}<button id="b-compartir-demo">${ic.compartir} ${t("Compartir")}</button></div>` : ""}
    ${v.semana && v.demo ? `<div class="pildora-semana"><span>${t("Semana")} ${v.semana} · <em>${t("de muestra")}</em></span></div>` : v.semana ? `<div class="pildora-semana">
      <button id="b-sem-menos" aria-label="Semana anterior" ${v.semana <= 1 ? "disabled style='opacity:.3'" : ""}>${ic.izq}</button>
      <span>${t("Semana")} ${v.semana}${v.semana === v.actual ? ` · <em>${t("de fuego")}</em>` : ""}</span>
      <button id="b-sem-mas" aria-label="Semana siguiente">${ic.der}</button>
    </div>` : ""}
    ${v.dias ? `<div class="dias" role="tablist">${v.dias.map((d) => {
      const n = (d.nombre.match(/\d+/) || [d.nombre.slice(0, 2)])[0];
      return `<button class="dia ${d.id === v.dia.id ? "on" : ""} ${d.bloqueado ? "bloq" : ""}" role="tab" aria-selected="${d.id === v.dia.id}" data-dia="${esc(d.id)}" ${d.bloqueado ? 'data-bloq="1"' : ""} aria-label="${esc(trDia(d.nombre))}${d.bloqueado ? " 🔒" : ""}">
        <small>D${esc(n)}</small>${d.bloqueado ? '<span class="candado">🔒</span>' : `<span class="punto ${d.estado}"></span>`}${d.pendientes ? '<span class="pend"></span>' : ""}</button>`;
    }).join("")}</div>` : ""}
  </header>`;
}

const MOBILITY = ["movilidad", "mobilidad", "mobilité", "mobilite", "mobility", "estiramientos", "stretching"];
const ETIQUETA_FR = { "fuerza": "Force" };
const etqParte = (x) => {
  const k = String(x || "").trim().toLowerCase();
  if (MOBILITY.includes(k)) return "Mobility";  // en todos los perfiles e idiomas
  return (E.lang === "fr" && ETIQUETA_FR[k]) || x;
};

function tarjeta(p, k) {
  const letra = p.estado === "hecho" ? ic.ok : p.calentamiento ? ic.llama("currentColor", 20) : esc(p.letra || "·");
  const estadoTxt = { hecho: t("Hecho").toLowerCase(), no_hecho: t("No hecho").toLowerCase(), pospuesto: "→ " + (p.destino_txt || "") }[p.estado];
  const titulo = p.lineas.length === 1 && !p.lineas[0].solo_bloque ? p.lineas[0].ejercicio : etqParte(p.etiqueta);
  const nombreTit = p.origen || titulo;
  const tagTxt = p.calentamiento ? (nombreTit === "Mobility" ? "Warm up" : "Warm up · Mobility")
    : nombreTit === etqParte(p.etiqueta) ? `${t("Parte")} ${p.letra || ""}`.trim() : `${p.letra ? p.letra + " · " : ""}${etqParte(p.etiqueta)}`;
  return `
  <section class="card ${p.estado === "hecho" ? "hecha" : ""} ${p.calentamiento ? "warmup" : ""}">
    <div class="card-cab">
      <div class="letra ${p.estado}">${letra}</div>
      <div style="flex:1;min-width:0">
        <div class="tag ${p.estado}">${esc(tagTxt)}${estadoTxt ? " · " + esc(estadoTxt) : ""}</div>
        <div class="nombre">${esc(nombreTit)}</div>
      </div>
      ${p.historial.length ? `<div class="hist" title="Semanas anteriores">${p.historial.map(([s, e]) => `<i class="${e}" title="S${s}"></i>`).join("")}</div>` : ""}
      <button class="tick ${p.estado === "hecho" ? "on" : ""}" data-tick="${k}" aria-label="${t("Hecho")}" aria-pressed="${p.estado === "hecho"}">✓</button>
      ${p.calentamiento ? "" : `<button class="mas-op gusta-op ${gusta(p) ? "on" : ""}" data-gusta="${k}" aria-label="${t("Me gusta")}" aria-pressed="${gusta(p)}">${gusta(p) ? "❤️" : "🤍"}</button>`}
      <button class="mas-op compartir-op" data-compartir="${k}" aria-label="${t("Compartir este entreno")}">${ic.compartir}</button>
      ${p.origen ? "" : `<button class="mas-op" data-menu="${k}" aria-label="${t("Cambiar esta parte")}">${ic.puntos}</button>`}
    </div>
    ${p.ciclo ? `<div class="mini" style="padding-left:48px">${ic.ciclo.replace("<svg", '<svg style="display:inline;vertical-align:-2px"')} ${t("Ciclo · semana")} ${p.ciclo.semana}/${p.ciclo.total}</div>` : ""}
    <div class="lineas">${p.lineas.map((l, j) => linea(l, p, k + "_" + j)).join("")}</div>
    ${p.no_hechas ? `<div class="nota-estado no_hecho" style="padding-left:48px">${p.no_hechas} sin hacer · repiten peso</div>` : ""}
    ${p.registro ? `<button class="btn btn-negro" data-reg="${k}" style="height:42px">${t("Registrar resultados")}</button>` : ""}
    <div class="estado" data-k="${k}">${p.opciones.map((o) =>
      `<button class="${p.actual === o.clave ? "on " + o.estado : ""}" data-op="${o.clave}" title="${esc(o.texto)}">${esc(corto(o))}</button>`).join("")}</div>
  </section>`;
}

function corto(o) {
  if (o.clave === "hecho" || o.clave === "no_hecho") return t(o.texto);
  if (o.clave === "semana" && /^Semana \d+$/.test(o.texto)) return "→ S" + o.texto.match(/\d+/)[0];
  const [dia, sem] = o.texto.split(" · ");
  const n = (dia.match(/\d+/) || [])[0];
  return "→ " + (n ? "D" + n : dia.slice(0, 6)) + (sem ? " " + sem : "");
}

const videoHtml = (l, k) => l.video ? `<button class="mini-btn video-btn" data-video="${k}">▶️ ${t("Ver vídeo de técnica")}</button>`
  : "";
function hojaVideo(k) {
  const { l } = lineaDe(k);
  const v = l.video || {};
  const directo = v.url && (/\.(mp4|mov|webm|m4v)(\?|$)/i.test(v.url) || !/^https?:/i.test(v.url));
  const yt = v.url && (v.url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([\w-]{6,})/) || [])[1];
  abrirHoja(`${cabHoja(t("Técnica"), l.ejercicio)}
    ${directo ? `<video class="video-tec" src="${esc(v.url)}" ${v.poster ? `poster="${esc(v.poster)}"` : ""} controls playsinline preload="metadata"></video>`
      : yt ? `<div class="video-tec yt"><iframe src="https://www.youtube-nocookie.com/embed/${esc(yt)}" title="${esc(l.ejercicio)}" allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen></iframe></div>`
      : v.url ? `<a class="btn btn-fuego" href="${esc(v.url)}" target="_blank" rel="noopener">▶️ ${t("Abrir el vídeo")}</a>` : `<p class="mini">${t("Este ejercicio aún no tiene vídeo.")}</p>`}
    ${E.vista.coach ? `<div class="caja-coach"><div class="paso-etq" style="margin:0 0 8px">🎥 ${t("Vídeo para todos en este ejercicio")}</div>
      <input class="campo" id="v-url" placeholder="https://youtube.com/… · instagram.com/…" value="${esc(v.url && /^https?:/i.test(v.url) ? v.url : "")}" style="background:#fff">
      <p class="mini" style="margin:6px 2px">${t("Sube el vídeo a YouTube (oculto) o Instagram y pega aquí el enlace.")}</p>
      <div style="display:grid;grid-template-columns:1fr auto;gap:8px"><button class="btn btn-negro" id="v-guardar">${t("Guardar")}</button>
      ${v.url ? `<button class="btn" id="v-quitar">${t("Quitar")}</button>` : ""}</div></div>` : ""}`, (h) => {
    const g = h.querySelector("#v-guardar");
    if (g) g.onclick = () => { const url = h.querySelector("#v-url").value.trim(); cerrarHoja(); hacer({ tipo: "video", ejercicio: l.ejercicio, url, titulo: l.ejercicio }); };
    const q = h.querySelector("#v-quitar");
    if (q) q.onclick = () => { cerrarHoja(); hacer({ tipo: "video", ejercicio: l.ejercicio, url: "" }); };
  });
}
const ultimoHtml = (l) => l.ultimo ? `<div class="ultimo">${ic.reloj.replace('width="22" height="22"', 'width="14" height="14"')}<span>${t("Último")}: <b>${esc(l.ultimo.valor)}</b> · ${esc(trFecha(l.ultimo.fecha))}</span></div>` : "";

function linea(l, p, k) {
  const extra = l.extra ? ` <span class="etq ${l.extra.tono}">${esc(l.extra.texto)}</span>` : "";
  const nota = l.nota ? `<div class="mini">${esc(l.nota)}</div>` : "";
  if (l.kind === "peso") {
    const bloq = E.vista.puede_pesos === false;
    const pend = (E.vista.mis_solicitudes || {})[l.id];
    const pesos = (l.pesos.length ? l.pesos.map((w, i) => `<button class="peso ${bloq ? "bloq" : ""}" data-peso="${k}" data-i="${i}">@ ${num(w)}<small>kg</small></button>`).join("")
      : `<button class="peso falta" data-peso="${k}" data-i="0">+ ${t("falta el peso")}</button>`)
      + (pend ? `<span class="etq aviso">${t("pendiente")} → ${esc(pend.valores.map(num).join(" · "))}</span>` : "");
    return `<div class="linea" data-l="${k}">
      ${p.lineas.length > 1 || extra ? `<div class="linea-cab"><b>${p.lineas.length > 1 ? esc(l.ejercicio) : ""}${extra}</b></div>` : ""}
      ${l.esquema ? `<div class="esquema">${esc(l.esquema)}</div>` : ""}
      <div class="pesos">${pesos}</div>${nota}${ultimoHtml(l)}${videoHtml(l, k)}
      ${p.origen ? "" : `<div class="acciones-linea"><button class="mini-btn" data-editar="${k}">${ic.lapiz} ${t(l.kind === "peso" ? "Cambiar movimiento / reps" : "Ajustar reps")}</button>${l.texto_sig && l.texto_sig !== l.texto ? `<span class="mini">${t("Semana que viene")}: ${esc(l.texto_sig.slice(0, 60))}</span>` : ""}</div>`}
      ${l.no_hecha !== undefined ? `<label class="check"><input type="checkbox" data-nh="${k}" ${l.no_hecha ? "checked" : ""}> ${t("No lo hice · te lo recuerdo esta semana")}</label>` : ""}
    </div>`;
  }
  const visto = l.visto || "";
  const nombre = l.solo_bloque || (p.lineas.length === 1) ? "" : `<b>${esc(l.ejercicio)}</b>`;
  let html = `<div class="linea" data-l="${k}">
    ${nombre || extra || (l.nivel && l.nivel !== "RX") ? `<div class="linea-cab">${nombre}<span>${extra}${l.nivel && l.nivel !== "RX" && visto ? ` <span class="etq nivel">${esc(l.nivel)}</span>` : ""}</span></div>` : ""}
    <div class="texto-wod">${visto ? esc(visto) : `<span class="mini">${t("por definir")}</span>`}</div>${nota}${ultimoHtml(l)}${videoHtml(l, k)}`;
  if (l.sugerencia) html += `<div class="sug">${ic.llama("#8A5E00", 20)}<span>${t("WOD de Diego · semana")} ${l.sugerencia.semana}, ${esc(l.sugerencia.dia)}</span>
    <button data-fijar="${k}">${t("Fijar")}</button></div>`;
  if (l.tabla) html += `<details class="desplegable"><summary>${t("RX · Inter · Scaled por movimiento")} ${ic.abajo}</summary>
    <table class="tabla"><thead><tr><th>RX</th><th>Inter</th><th>Scaled</th></tr></thead><tbody>${l.tabla.map((f) =>
      f.RX === f.Inter && f.Inter === f.Scaled ? `<tr><td colspan="3" style="color:var(--tinta);font-weight:500">${esc(f.RX)}</td></tr>`
        : `<tr><td>${esc(f.RX)}</td><td>${esc(f.Inter)}</td><td>${esc(f.Scaled)}</td></tr>`).join("")}</tbody></table></details>`;
  else if (l.versiones_nivel) html += `<details class="desplegable"><summary>${t("Versiones")} RX · Inter · Scaled · Elite ${ic.abajo}</summary>
    <div class="versiones">${Object.entries(l.versiones_nivel).map(([n, txt]) => `<div><b>${esc(n)}</b><span class="texto-wod">${esc(txt)}</span></div>`).join("")}</div></details>`;
  if (!p.origen) html += `<div class="acciones-linea"><button class="mini-btn" data-editar="${k}">${ic.lapiz} ${t("Ajustar")}</button>${l.tipo !== "fuerza" ? `<button class="mini-btn azar" data-azar="${k}">🎲 ${t("Al azar")}</button>` : ""}${["wod", "emom", "fortime", "amrap", "conditioning"].includes(l.tipo) ? ((E.vista.retest_lineas || {})[l.id]
      ? `<span class="etq ok">🔁 ${t("Retest el")} ${esc(trFecha(E.vista.retest_lineas[l.id]))}</span>`
      : `<button class="mini-btn" data-retest="${k}">🔁 ${t("Repetir para comparar")}</button>`) : ""}${l.texto_sig && l.texto_sig !== l.texto ? `<span class="mini">${t("Semana que viene")}: ${esc(l.texto_sig.split("\n")[0].slice(0, 60))}</span>` : ""}</div>`;
  if (l.crono && visto) html += `<button class="btn-crono" data-crono="${k}">${ic.reloj}<span>${t("Cronómetro")}<small>${esc(etiquetaCrono(l.crono))}</small></span>${ic.der.replace(/#FFB400/g, "currentColor")}</button>`;
  if (l.elite) html += `<div class="elite"><span class="ico">${ic.estrella}</span><span><b>${esc(l.elite.quien)}: ${esc(l.elite.marca)}</b> · ${esc(l.elite.detalle)}</span></div>`;
  return html + "</div>";
}

function finSemana(v) {
  if (v.semana === v.actual) {
    const todo = v.dias.every((d) => d.estado !== "pendiente");
    return `<button class="btn ${todo ? "btn-fuego" : "btn-negro"} fin-semana" id="b-fin">${t("Terminé la semana")} ${v.actual} → ${t("pasar a la")} ${v.actual + 1}</button>`;
  }
  return `<button class="btn btn-negro fin-semana" id="b-actual">${t("Marcar esta semana como la actual")} (${v.semana})</button>`;
}

function nav(activo = "rutina") {
  const b = (id, icono, txt, extra = "") => activo === id
    ? `<button class="on" aria-current="page" ${extra}>${icono}${txt}</button>`
    : `<button aria-label="${txt}" ${extra}>${icono}</button>`;
  return `<nav class="nav" aria-label="Secciones">
    ${b("rutina", ic.calendario, t("Rutina"), 'data-ir="rutina"')}
    ${b("registrar", ic.mas, t("Registrar"), 'data-ir="registrar"')}
    ${b("progreso", ic.grafica, t("Progreso"), 'data-ir="progreso"')}
    ${E.vista && E.vista.con_prs === false ? "" : b("prs", ic.copa, t("Récords"), 'data-ir="prs"')}
    <button data-pronto="${t("Biblioteca")}" aria-label="${t("Biblioteca")}">${ic.libros}</button>
  </nav>`;
}

// ---------- eventos ----------
function parteDe(k) {
  const v = E.vista;
  return k[0] === "p" ? v.partes[+k.slice(1)] : v.pendientes[+k.slice(1)];
}
function lineaDe(k) {
  const [pk, j] = k.split("_");
  return { p: parteDe(pk), l: parteDe(pk).lineas[+j] };
}

function enlazar() {
  const v = E.vista;
  const on = (id, f) => { const el = document.getElementById(id); if (el) el.onclick = f; };
  on("b-persona", hojaPersonas);
  on("b-ajustes", hojaAjustes);
  on("b-reloj", () => abrirCrono(null, null));
  on("b-solicitudes", hojaSolicitudes);
  on("b-sem-menos", () => cargar({ semana: v.semana - 1, dia: null }).then(() => window.scrollTo(0, 0)));
  on("b-sem-mas", () => cargar({ semana: v.semana + 1, dia: null }).then(() => window.scrollTo(0, 0)));
  on("b-fin", (ev) => hacer({ tipo: "semana", nueva: v.actual + 1, ver_semana: v.actual + 1, ver_dia: null }, ev.currentTarget).then(() => window.scrollTo(0, 0)));
  on("b-actual", (ev) => hacer({ tipo: "semana", nueva: v.semana }, ev.currentTarget));
  $app.querySelectorAll("[data-dia]").forEach((b) => b.onclick = () => {
    if (b.dataset.bloq) { aviso(t("🔒 Este día se desbloquea con tu perfil")); return setTimeout(hojaBienvenidaDemo, 400); }
    if (b.dataset.dia === E.dia) return;
    $app.querySelectorAll(".dia").forEach((x) => x.classList.toggle("on", x === b));
    cargar({ dia: b.dataset.dia });
  });
  $app.querySelectorAll(".estado").forEach((g) => g.querySelectorAll("button").forEach((b) => b.onclick = () => {
    const p = parteDe(g.dataset.k);
    const o = p.opciones.find((x) => x.clave === b.dataset.op);
    const quitar = p.actual === o.clave;
    g.querySelectorAll("button").forEach((x) => x.classList.toggle("on", !quitar && x === b));
    hacer({ tipo: "marcar", semana: p.semana, dia: p.dia_id, parte: p.parte, estado: quitar ? null : o.estado,
      destino: quitar ? null : o.destino }, b);
  }));
  $app.querySelectorAll("[data-peso]").forEach((b) => b.onclick = () => hojaPeso(b.dataset.peso, +b.dataset.i));
  $app.querySelectorAll("[data-nh]").forEach((c) => c.onchange = () => {
    const { p, l } = lineaDe(c.dataset.nh);
    hacer({ tipo: "linea_no_hecha", semana: p.semana, linea: l.id, valor: c.checked });
  });
  $app.querySelectorAll("[data-fijar]").forEach((b) => b.onclick = () => {
    const { p, l } = lineaDe(b.dataset.fijar);
    hacer({ tipo: "fijar", semana: p.semana, linea: l.id, texto: l.sugerencia.texto }, b);
  });
  $app.querySelectorAll("[data-pronto]").forEach((b) => b.onclick = () => hojaPronto(b.dataset.pronto));
  $app.querySelectorAll("[data-ir]").forEach((b) => b.onclick = () => {
    const ir = b.dataset.ir;
    if (ir === "registrar") abrirRegistrar(null);
    else if (ir === "progreso" || ir === "prs") irA(ir);
    else { E.pantalla = "rutina"; pintar(); window.scrollTo(0, 0); }
  });
  on("b-registrar-dia", () => abrirRegistrar(v.registro, v.partes.filter((p) => p.estado !== "hecho").map((p) => p.parte)));
  $app.querySelectorAll("[data-reg]").forEach((b) => b.onclick = () => {
    const p = parteDe(b.dataset.reg); abrirRegistrar(p.registro, [p.parte]);
  });
  $app.querySelectorAll("[data-editar]").forEach((b) => b.onclick = () => hojaTexto(b.dataset.editar));
  $app.querySelectorAll("[data-azar]").forEach((b) => b.onclick = () => hojaAzar(b.dataset.azar));
  $app.querySelectorAll("[data-menu]").forEach((b) => b.onclick = () => hojaParte(parteDe(b.dataset.menu)));
  $app.querySelectorAll("[data-compartir]").forEach((b) => b.onclick = () => {
    const x = textoParte(parteDe(b.dataset.compartir));
    compartir("entreno", `${x.texto}\n\n${t("Entreno de hoy con Djimenez Prog 💪")}`, x.titulo);
  });
  const bad = document.getElementById("b-abono-demo");
  if (bad) bad.onclick = abonarse;
  const bcp = document.getElementById("b-crear-demo");
  if (bcp) bcp.onclick = () => hojaCrearPerfil({});
  const bcd = document.getElementById("b-compartir-demo");
  if (bcd) bcd.onclick = () => compartir("app", t("💪 Mira la app de entrenamiento de Diego (Djimenez Prog)"), "app");
  on("b-anadir-parte", () => hojaParte(null));
  $app.querySelectorAll("[data-video]").forEach((b) => b.onclick = () => hojaVideo(b.dataset.video));
  $app.querySelectorAll("[data-tick]").forEach((b) => b.onclick = () => {
    const p = parteDe(b.dataset.tick); const on = p.estado !== "hecho";
    b.classList.toggle("on", on);
    hacer({ tipo: "marcar", semana: p.semana, dia: p.dia_id, parte: p.parte, estado: on ? "hecho" : null }, b);
  });
  $app.querySelectorAll("[data-olv-hecha]").forEach((b) => b.onclick = () => {
    const o = E.vista.olvidadas[+b.dataset.olvHecha];
    if (o.tipo === "linea") return hacer({ tipo: "linea_no_hecha", linea: o.linea, semana: E.semana, valor: false }, b);
    hacer({ tipo: "marcar", semana: E.semana, dia: o.dia, parte: o.parte, estado: "hecho" }, b);
  });
  $app.querySelectorAll("[data-olv-hoy]").forEach((b) => b.onclick = () => {
    const o = E.vista.olvidadas[+b.dataset.olvHoy];
    if (o.tipo === "linea") return hacer({ tipo: "linea_hoy", linea: o.linea, dia: E.dia, semana: E.semana }, b);
    hacer({ tipo: "marcar", semana: E.semana, dia: o.dia, parte: o.parte, estado: "pospuesto", destino: [E.semana, E.dia] }, b);
  });
  $app.querySelectorAll("[data-rt-si]").forEach((b) => b.onclick = () => hacer({ tipo: "retest_poner", id: b.dataset.rtSi, dia: E.dia, semana: E.semana }, b));
  $app.querySelectorAll("[data-rt-semana]").forEach((b) => b.onclick = () => hacer({ tipo: "retest_semana", id: b.dataset.rtSemana }, b));
  $app.querySelectorAll("[data-rt-no]").forEach((b) => b.onclick = () => hacer({ tipo: "retest_quitar", id: b.dataset.rtNo }, b));
  $app.querySelectorAll("[data-retest]").forEach((b) => b.onclick = () => hojaRetest(b.dataset.retest));
  $app.querySelectorAll("[data-gusta]").forEach((b) => b.onclick = () => alternarGusta(parteDe(b.dataset.gusta), b));
  $app.querySelectorAll("[data-nov-si]").forEach((b) => b.onclick = () => hacer({ tipo: "ponerme_novedad", id: b.dataset.novSi, dia: E.dia, semana: E.semana }, b));
  $app.querySelectorAll("[data-nov-no]").forEach((b) => b.onclick = () => hacer({ tipo: "descartar_novedad", id: b.dataset.novNo }, b));
  $app.querySelectorAll("[data-crono]").forEach((b) => b.onclick = () => { const { p, l } = lineaDe(b.dataset.crono); abrirCrono(p, l); });
}

// ---------- me gusta ----------
const claveParte = (p) => { const x = textoParte(p); return (x.titulo + " " + x.texto).toLowerCase().replace(/\s+/g, " ").slice(0, 120); };
function gustos() { try { return JSON.parse(mem.get("gustos_" + E.atleta) || "[]"); } catch { return []; } }
const gusta = (p) => gustos().includes(claveParte(p));
function idDisp() { let d = mem.get("disp"); if (!d) { d = Math.random().toString(36).slice(2, 12); mem.set("disp", d); } return d; }
async function alternarGusta(p, b) {
  const k = claveParte(p), lista = gustos(), on = !lista.includes(k);
  mem.set("gustos_" + E.atleta, JSON.stringify(on ? [...lista, k].slice(-200) : lista.filter((x) => x !== k)));
  b.classList.toggle("on", on); b.textContent = on ? "❤️" : "🤍"; b.setAttribute("aria-pressed", on);
  if (on) { b.classList.remove("late"); void b.offsetWidth; b.classList.add("late"); }
  const x = textoParte(p);
  api("me_gusta", { metodo: "POST", cuerpo: { clave: k, on, nombre: x.titulo, texto: x.texto.slice(0, 200), atleta: E.atleta, disp: idDisp() } }).catch(() => { });
}

// ---------- repetir un WOD más adelante ----------
function hojaRetest(k) {
  const { p, l } = lineaDe(k);
  abrirHoja(`${cabHoja(`${p.letra ? p.letra + " · " : ""}${etqParte(p.etiqueta)}`, t("Repetir para comparar"))}
    <div class="texto-wod" style="background:#fff;border-radius:14px;padding:12px">${esc(l.visto || l.texto || "")}</div>
    <p class="mini" style="margin:0 4px">${l.ultimo ? `${t("Tu marca ahora")}: <b>${esc(l.ultimo.valor)}</b> (${esc(trFecha(l.ultimo.fecha))}). ` : `${t("Registra hoy tu resultado para poder comparar.")} `}${t("Te lo volvemos a poner en tu día y verás la otra marca al lado.")}</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
      <button class="btn btn-fuego" data-meses="1">${t("En 1 mes")}</button>
      <button class="btn btn-negro" data-meses="2">${t("En 2 meses")}</button></div>`, (h) => {
    h.querySelectorAll("[data-meses]").forEach((b) => b.onclick = () => { cerrarHoja(); hacer({ tipo: "retest", linea: l.id, meses: b.dataset.meses, semana: p.semana }); });
  });
}

// ---------- compartir ----------
async function compartir(tipo, texto, que) {
  let inv = null;
  try { inv = (await api("compartir", { metodo: "POST", cuerpo: { tipo, que, atleta: E.atleta, contar: false } })).inv; } catch { }
  const url = location.origin + "/" + (inv ? "?inv=" + encodeURIComponent(inv) : "");
  const msg = `${texto}\n\n${inv ? t("Mírala aquí (entras directo, solo para ver):") : t("La app:")} ${url}`;
  const contar = () => api("compartir", { metodo: "POST", cuerpo: { tipo, que, atleta: E.atleta } }).catch(() => { });
  if (navigator.share) {
    try { await navigator.share({ title: "Djimenez Prog", text: msg }); contar(); aviso(t("¡Compartido! 🔥")); }
    catch (e) { if (e && e.name !== "AbortError") hojaCompartir(msg, contar); }
    return;
  }
  hojaCompartir(msg, contar);
}
function cargarQR() {
  if (window.qrcode) return Promise.resolve();
  return new Promise((ok, mal) => { const sc = document.createElement("script"); sc.src = "qrcode.js?v=1"; sc.onload = ok; sc.onerror = mal; document.head.appendChild(sc); });
}
async function hojaQR() {
  abrirHoja(`${cabHoja("Djimenez Prog", t("Código QR"))}<div class="cargador" style="margin:40px auto"></div>`);
  let inv = null;
  try {
    [inv] = await Promise.all([api("compartir", { metodo: "POST", cuerpo: { tipo: "app", via: "qr", atleta: E.atleta, contar: false } }).then((r) => r.inv), cargarQR()]);
  } catch (e) { cerrarHoja(); return aviso(t("No se ha podido crear el QR"), true); }
  if ($hoja.hidden) return;
  const url = location.origin + "/" + (inv ? "?inv=" + encodeURIComponent(inv) : "");
  const qr = qrcode(0, "M"); qr.addData(url); qr.make();
  $hoja.firstElementChild.innerHTML = `<div class="asa"></div>${cabHoja("Djimenez Prog", t("Código QR"))}
    <div class="qr-caja">${qr.createSvgTag({ cellSize: 8, margin: 2, scalable: true, alt: "QR Djimenez Prog" })}
      <div class="qr-pie">${ic.llama("#FF6A00", 22)}<b>Djimenez Prog</b></div></div>
    <p class="mini" style="text-align:center;margin:0 8px">${inv ? t("Que lo escaneen con la cámara del móvil: entran directo a la demo, solo para mirar. Cuenta en «Quién usa la app».")
      : t("Escaneándolo se abre la app (para entrar hace falta contraseña).")}</p>`;
  $hoja.querySelectorAll("[data-cerrar]").forEach((b) => b.onclick = cerrarHoja);
}
function hojaCompartir(msg, contar) {
  abrirHoja(`${cabHoja("Djimenez Prog", t("Compartir"))}
    <div class="texto-wod" style="background:#fff;border-radius:14px;padding:12px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px">${esc(msg)}</div>
    <a class="btn btn-fuego" id="c-wa" href="https://wa.me/?text=${encodeURIComponent(msg)}" target="_blank" rel="noopener">WhatsApp</a>
    <button class="btn btn-negro" id="c-copiar">${t("Copiar el texto")}</button>`, (h) => {
    h.querySelector("#c-wa").onclick = () => { contar(); setTimeout(cerrarHoja, 300); };
    h.querySelector("#c-copiar").onclick = async () => {
      try { await navigator.clipboard.writeText(msg); contar(); aviso(t("Copiado. Pégalo donde quieras")); cerrarHoja(); }
      catch { aviso(t("No se ha podido copiar"), true); }
    };
  });
}
function textoParte(p) {
  const nombreTit = p.lineas.length === 1 && !p.lineas[0].solo_bloque ? p.lineas[0].ejercicio : etqParte(p.etiqueta);
  const lineas = p.lineas.map((l) => {
    const txt = (l.visto || l.texto || "").trim();
    return l.solo_bloque || p.lineas.length === 1 ? txt : `• ${l.ejercicio}${txt ? ": " + txt : ""}`;
  }).filter(Boolean).join("\n");
  return { titulo: nombreTit, texto: `🔥 ${nombreTit}\n${lineas}` };
}

// ---------- hojas ----------
function abrirHoja(html, alAbrir) {
  $hoja.innerHTML = `<div class="hoja" role="dialog" aria-modal="true"><div class="asa"></div>${html}</div>`;
  $hoja.hidden = false;
  document.body.style.overflow = "hidden";
  $hoja.onclick = (ev) => { if (ev.target === $hoja) cerrarHoja(); };
  $hoja.querySelectorAll("[data-cerrar]").forEach((b) => b.onclick = cerrarHoja);
  if (alAbrir) alAbrir($hoja.firstElementChild);
}
function cerrarHoja() { $hoja.hidden = true; $hoja.innerHTML = ""; desbloquearScroll(); }
// Si no hay ninguna ventana abierta, la página tiene que poder bajar siempre (algunos Android dejaban el bloqueo puesto).
function desbloquearScroll() {
  const crono = document.getElementById("crono");
  if ($hoja.hidden && (!crono || crono.hidden)) { document.body.style.overflow = ""; document.documentElement.style.overflow = ""; }
}
window.addEventListener("pageshow", desbloquearScroll);
document.addEventListener("visibilitychange", () => { if (!document.hidden) desbloquearScroll(); });
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && !$hoja.hidden) cerrarHoja(); });
const cabHoja = (pre, titulo) => `<div class="hoja-cab"><div><small>${esc(pre)}</small><h3>${esc(titulo)}</h3></div>
  <button class="cerrar" data-cerrar aria-label="Cerrar">${ic.x}</button></div>`;

const PREF = /(\S*?)\s*@\s*\d+(?:[.,]\d+)?/g;
function hojaPeso(k, foco) {
  const { p, l } = lineaDe(k);
  const prefijos = [...(l.texto || "").matchAll(PREF)].map((m) => m[1]);
  const valores = l.pesos.length ? [...l.pesos] : [null];
  const etiqueta = (i) => {
    const pr = prefijos[i];
    if (valores.length === 1) return l.esquema || "Peso";
    return pr ? (/^\d+$/.test(pr) ? `${pr} reps` : pr) : `Carga ${i + 1}`;
  };
  const v = E.vista;
  const libre = v.puede_pesos !== false;
  const pend = (v.mis_solicitudes || {})[l.id];
  abrirHoja(`${cabHoja(`${p.letra ? p.letra + " · " : ""}${libre ? t("Cambiar peso") : t("Proponer un cambio")}`, l.ejercicio)}
    ${libre ? "" : `<div class="aviso-coach">${ic.candado}<div><b>${t("Los pesos los pone tu coach")}</b>
      <span>${t("¿Le has preguntado a Diego si este cambio es pertinente? Si se lo envías, lo aprueba él y se cambia solo.")}</span></div></div>${pinInline(v)}`}
    ${pend ? `<div class="alerta"><b>${t("Pendiente de aprobar")}:</b> ${esc(pend.antes.map(num).join(" · ") || "—")} → ${esc(pend.valores.map(num).join(" · "))} kg</div>` : ""}
    ${valores.map((w, i) => `<div><div class="paso-etq" style="margin:0 4px 6px">${esc(etiqueta(i))}</div>
      <div class="paso"><button data-d="-2.5" data-i="${i}" aria-label="Menos 2,5">−2,5</button>
      <input inputmode="decimal" data-i="${i}" value="${w == null ? "" : num(w)}" placeholder="kg" aria-label="${esc(etiqueta(i))}">
      <button data-d="2.5" data-i="${i}" aria-label="Más 2,5">+2,5</button></div></div>`).join("")}
    <label class="interruptor"><span>${t("Mover igual el mismo ejercicio en los otros días")}</span><input type="checkbox" id="c-prop" checked></label>
    <label class="interruptor"><span>${t("Solo esta semana")}</span><input type="checkbox" id="c-solo"></label>
    ${libre ? "" : `<div><label class="paso-etq" for="c-msg" style="display:block;margin:0 4px 6px">${t("Mensaje para Diego (opcional)")}</label>
      <textarea class="campo area" id="c-msg" placeholder="${t("Ej.: la semana pasada me salió fácil")}"></textarea></div>`}
    <button class="btn btn-fuego" id="b-guardar-peso">${libre ? t("Guardar") : t("Enviar a Diego para que lo apruebe")}</button>`, (h) => {
    enlazarPin(h, () => hojaPeso(k, foco));
    const inputs = [...h.querySelectorAll("input[data-i]")];
    const leer = (inp) => parseFloat(String(inp.value).replace(",", "."));
    h.querySelectorAll("button[data-d]").forEach((b) => b.onclick = () => {
      const inp = inputs[+b.dataset.i];
      const actual = isNaN(leer(inp)) ? 0 : leer(inp);
      inp.value = num(Math.max(0, actual + parseFloat(b.dataset.d)));
    });
    const i0 = inputs[Math.min(foco, inputs.length - 1)];
    if (i0 && i0.value === "") setTimeout(() => i0.focus(), 120);
    if (inputs.length > 1) h.classList.add("muchos");
    h.querySelector("#b-guardar-peso").onclick = async (ev) => {
      const vals = inputs.map(leer);
      if (vals.some((x) => isNaN(x) || x < 0)) return aviso("Pon un peso válido", true);
      ev.currentTarget.disabled = true;
      const msg = (h.querySelector("#c-msg") || {}).value;
      cerrarHoja();
      await hacer({ tipo: libre ? "peso" : "solicitar_peso", semana: p.semana, linea: l.id, texto: l.texto, valores: vals,
        propagar: h.querySelector("#c-prop").checked, solo_semana: h.querySelector("#c-solo").checked,
        mensaje: libre ? undefined : msg });
    };
  });
}

// Con la contraseña general, cada móvil dice quién es una vez; si es un alumno, la sesión queda fijada a su perfil
function hojaQuienEres() {
  const v = E.vista;
  abrirHoja(`<div class="demo-hola">${ic.llama("#FF6A00", 40)}<h3>${t("¿Quién eres?")}</h3>
      <p>${t("Elige tu perfil. Se queda guardado en este móvil y ya no se cambia solo.")}</p></div>
    <div class="lista-personas">${v.personas.map((p) => `<button class="persona" data-yo="${esc(p.id)}">
      <span class="avatar">${esc(inicial(p.nombre))}</span>${esc(p.nombre)}</button>`).join("")}</div>`, (h) => {
    h.querySelectorAll("[data-yo]").forEach((b) => b.onclick = async () => {
      const quien = b.dataset.yo;
      mem.set("perfil_fijo", quien);
      if (quien === "Yo") { cerrarHoja(); return cargar({ atleta: "Yo" }); }  // Diego sigue viendo a todos
      try {
        const r = await api("fijar_perfil", { metodo: "POST", cuerpo: { atleta: quien } });
        E.token = r.token; mem.set("token", r.token); E.atleta = quien; mem.set("atleta", quien);
        E.semana = null; E.dia = null; cerrarHoja(); aviso(t("Perfil guardado en este móvil ✅")); cargar({ atleta: quien });
      } catch (e) { aviso(e.message, true); }
    });
  });
}

function hojaPersonas() {
  const v = E.vista;
  abrirHoja(`${cabHoja("Djimenez Prog", t("Personas"))}
    <div class="lista-personas">${v.personas.map((p) => `<button class="persona ${p.id === v.atleta ? "on" : ""}" data-p="${esc(p.id)}">
      <span class="avatar">${esc(inicial(p.nombre))}</span>${esc(p.nombre)}</button>`).join("")}</div>`, (h) => {
    h.querySelectorAll("[data-p]").forEach((b) => b.onclick = () => {
      cerrarHoja();
      E.semana = null; E.dia = null;
      cargar({ atleta: b.dataset.p, semana: null, dia: null }).then(() => window.scrollTo(0, 0));
    });
  });
}

function hojaAjustes() {
  const v = E.vista;
  abrirHoja(`${cabHoja(v.nombre, t("Ajustes"))}
    ${v.niveles ? `<div><div class="paso-etq" style="margin:0 4px 8px">${t("Nivel en WODs")}</div>
      <div class="fila-chips">${v.niveles.map((n) => `<button class="chip ${n === v.nivel ? "on" : ""}" data-nivel="${n}">${n}</button>`).join("")}</div></div>` : ""}
    <div><div class="paso-etq" style="margin:0 4px 8px">${t("Idioma")}</div>
      <div class="fila-chips"><button class="chip ${E.lang === "es" ? "on" : ""}" data-lang="es">Español</button>
      <button class="chip ${E.lang === "fr" ? "on" : ""}" data-lang="fr">Français</button></div></div>
    <div class="caja-coach"><div class="paso-etq" style="margin:0 0 8px">${ic.candado} ${t("Modo coach")}</div>
      ${v.coach ? `<div class="mini" style="margin-bottom:10px">${t("Activado: puedes cambiar los pesos de todos.")}</div>
        ${v.atleta !== "Yo" ? `<label class="interruptor"><span>${esc(v.nombre)} ${t("puede cambiar sus pesos sin preguntarte")}</span><input type="checkbox" id="c-permiso" ${v.permiso_pesos ? "checked" : ""}></label>` : ""}
        <div class="tg-caja">${v.telegram
          ? `<b>📲 ${t("Avisos por Telegram")}: ✅</b><div style="display:grid;grid-template-columns:1fr auto;gap:8px;margin-top:8px"><button class="btn" id="b-tg-probar">${t("Enviar prueba")}</button><button class="btn" id="b-tg-quitar">${t("Quitar")}</button></div>`
          : `<b>📲 ${t("Avisos por Telegram")}</b>
            <ol class="mini" style="margin:6px 0 8px;padding-left:18px">
              <li>${t("En Telegram abre")} <a href="https://t.me/BotFather" target="_blank" rel="noopener">@BotFather</a>, ${t("escribe /newbot y ponle un nombre (p. ej. Djimenez Avisos).")}</li>
              <li>${t("Abre tu bot nuevo y pulsa INICIAR.")}</li>
              <li>${t("Copia el token que te da BotFather y pégalo aquí:")}</li></ol>
            <div style="display:flex;gap:8px"><input class="campo" id="i-tg" placeholder="123456789:AAH…" autocomplete="off" style="height:46px;background:#fff">
            <button class="btn btn-negro" id="b-tg">${t("Conectar")}</button></div>`}</div>
        <button class="btn btn-fuego" id="b-actividad" style="width:100%;margin-top:10px;height:50px">📊 ${t("Quién usa la app")}</button>
        <button class="btn" id="b-limpiar" style="width:100%;margin-top:10px">🧹 ${t("Limpiar la biblioteca")}</button>
        <div id="limpiar-res"></div>
        <button class="btn" id="b-coach-salir" style="width:100%;margin-top:10px">${t("Quitar el modo coach en este móvil")}</button>`
      : `<div class="mini" style="margin-bottom:10px">${t("Solo para Diego: con el PIN del coach puedes cambiar los pesos y aprobar los cambios que te piden.")}</div>
        <div style="display:flex;gap:8px"><input class="campo" id="i-pin-coach" type="password" autocapitalize="off" autocomplete="off" placeholder="PIN o clave" style="height:48px;background:#fff">
        <button class="btn btn-negro" id="b-coach">${t("Activar")}</button></div>`}
    </div>
    ${v.coach ? "" : botonAbono(v, "b-abono")}
    <div style="display:grid;grid-template-columns:1fr auto;gap:8px">
      <button class="btn btn-fuego" id="b-compartir-app">${ic.compartir} ${t("Compartir la app")}</button>
      <button class="btn btn-negro" id="b-qr" style="padding:0 18px">${ic.qr} QR</button></div>
    ${botonCreador()}
    ${v.app_antigua ? `<a class="btn" href="${esc(v.app_antigua)}" target="_blank" rel="noopener">${t("Abrir la app de siempre")}</a>` : ""}
    <button class="btn btn-negro" id="b-salir">${t("Salir")}</button>`, (h) => {
    const bc = h.querySelector("#b-coach");
    if (bc) bc.onclick = async () => {
      bc.disabled = true;
      try {
        const r = await api("coach", { metodo: "POST", cuerpo: { pin: h.querySelector("#i-pin-coach").value } });
        E.token = r.token; mem.set("token", r.token);
      cerrarHoja(); aviso(t("Modo coach activado")); cargar();
      } catch (e) { aviso(e.message, true); bc.disabled = false; }
    };
    const bs = h.querySelector("#b-coach-salir");
    if (bs) bs.onclick = async () => {
      const r = await api("coach", { metodo: "POST", cuerpo: { salir: true } });
      E.token = r.token; mem.set("token", r.token);
      cerrarHoja(); aviso(t("Modo coach quitado")); cargar();
    };
    h.querySelector("#b-compartir-app").onclick = () => { cerrarHoja(); compartir("app", t("💪 Mira la app con la que entreno con Diego (Djimenez Prog)"), "app"); };
    h.querySelector("#b-qr").onclick = () => hojaQR();
    const bab = h.querySelector("#b-abono"); if (bab) bab.onclick = abonarse;
    const tg = async (cuerpo, b) => { if (b) b.disabled = true; try { const r = await api("telegram", { metodo: "POST", cuerpo }); cerrarHoja(); aviso(r.aviso); cargar(); } catch (e) { aviso(e.message, true); if (b) b.disabled = false; } };
    const btg = h.querySelector("#b-tg"); if (btg) btg.onclick = () => tg({ token: h.querySelector("#i-tg").value }, btg);
    const btp = h.querySelector("#b-tg-probar"); if (btp) btp.onclick = () => tg({ probar: true }, btp);
    const btq = h.querySelector("#b-tg-quitar"); if (btq) btq.onclick = () => tg({ quitar: true }, btq);
    const ba = h.querySelector("#b-actividad");
    if (ba) ba.onclick = () => hojaActividad();
    const bl = h.querySelector("#b-limpiar");
    if (bl) bl.onclick = async () => {
      bl.disabled = true;
      const caja = h.querySelector("#limpiar-res");
      try {
        const r = await api("limpiar_biblioteca", { metodo: "POST", cuerpo: { probar: true } });
        if (!r.quitados) { caja.innerHTML = `<p class="mini">${t("Todo lo que hay en la biblioteca son entrenos. No hay nada que quitar.")}</p>`; return; }
        caja.innerHTML = `<div class="alerta" style="margin-top:10px"><b>${r.quitados} ${t("cosas que no son entrenos")}:</b> ${esc(r.ejemplos.join(" · "))}${r.quitados > r.ejemplos.length ? "…" : ""}</div>
          <button class="btn btn-negro" id="b-limpiar-ok" style="width:100%;margin-top:8px">${t("Quitarlas")}</button>`;
        caja.querySelector("#b-limpiar-ok").onclick = async (ev) => {
          ev.currentTarget.disabled = true;
          const r2 = await api("limpiar_biblioteca", { metodo: "POST", cuerpo: {} });
          E.ideas = null;
          caja.innerHTML = `<p class="mini">✓ ${r2.quitados} ${t("quitadas de la biblioteca")}</p>`;
        };
      } catch (e) { aviso(e.message, true); bl.disabled = false; }
    };
    const cp = h.querySelector("#c-permiso");
    if (cp) cp.onchange = () => { cerrarHoja(); hacer({ tipo: "permiso_pesos", valor: cp.checked }); };
    h.querySelectorAll("[data-nivel]").forEach((b) => b.onclick = () => { cerrarHoja(); hacer({ tipo: "nivel", nivel: b.dataset.nivel }); });
    h.querySelectorAll("[data-lang]").forEach((b) => b.onclick = () => {
      E.lang = b.dataset.lang; mem.set("lang", E.lang); mem.set("lang_elegido", "1"); cerrarHoja(); pintar();
    });
    h.querySelector("#b-salir").onclick = salir;
  });
}

function pinInline(v) {
  // Diego sin el modo coach activado: lo activa aquí mismo y sigue cambiando
  if (v.coach || v.solo) return "";
  return `<div class="pin-inline"><span>${t("¿Eres Diego? Mete tu PIN de coach y lo cambias directamente")}</span>
    <div style="display:flex;gap:8px"><input class="campo" id="pin-in" type="password" autocapitalize="off" autocomplete="off" placeholder="PIN o clave" style="height:46px;background:#fff">
    <button type="button" class="btn btn-negro" id="pin-ok">${t("Activar")}</button></div></div>`;
}
function enlazarPin(h, reabrir) {
  const b = h.querySelector("#pin-ok");
  if (!b) return;
  const ir = async () => {
    b.disabled = true;
    try {
      const r = await api("coach", { metodo: "POST", cuerpo: { pin: h.querySelector("#pin-in").value } });
      E.token = r.token; mem.set("token", r.token);
      cerrarHoja(); await cargar(); aviso(t("Modo coach activado")); reabrir();
    } catch (e) { aviso(e.message, true); b.disabled = false; }
  };
  b.onclick = ir;
  h.querySelector("#pin-in").onkeydown = (ev) => { if (ev.key === "Enter") { ev.preventDefault(); ir(); } };
}
function avisoCoach(v) {
  return v.puede_pesos === false ? `<div class="aviso-coach">${ic.candado}<div><b>${t("Lo programa tu coach")}</b>
    <span>${t("¿Le has preguntado a Diego si este cambio es pertinente? Si se lo envías, lo aprueba él y se cambia solo.")}</span></div></div>` + pinInline(v) : "";
}
const msgCoach = (v) => v.puede_pesos === false ? `<div><label class="paso-etq" for="c-msg" style="display:block;margin:0 4px 6px">${t("Mensaje para Diego (opcional)")}</label>
  <textarea class="campo area" id="c-msg" placeholder="${t("Ej.: no llegaba a 8+8, he hecho 8+5")}"></textarea></div>` : "";
const alcanceHtml = (solo) => `<div class="fila-chips"><button type="button" class="chip ${solo ? "on" : ""}" data-alc="1">${t("Solo esta semana")}</button>
  <button type="button" class="chip ${solo ? "" : "on"}" data-alc="0">${t("Esta y las siguientes")}</button></div>`;
function enlazarAlcance(h, estado) {
  h.querySelectorAll("[data-alc]").forEach((b) => b.onclick = () => {
    estado.solo = b.dataset.alc === "1";
    h.querySelectorAll("[data-alc]").forEach((x) => x.classList.toggle("on", x === b));
  });
}

function hojaTexto(k) {
  const v = E.vista;
  const { p, l } = lineaDe(k);
  const est = { solo: ["wod", "emom", "fortime", "amrap", "conditioning"].includes(l.tipo) && !l.ciclo };
  const abrirSig = !!l.ciclo || (l.texto_sig && l.texto_sig !== l.texto);
  abrirHoja(`${cabHoja(`${p.letra ? p.letra + " · " : ""}${etqParte(p.etiqueta)}`, t("Ajustar"))}
    ${avisoCoach(v)}
    ${l.extra && l.extra.texto === "solo esta semana" ? `<button class="btn btn-negro" id="t-quitar">↩ ${t("Quitar el cambio de esta semana")}</button>` : ""}
    <div><label class="paso-etq" for="t-nombre" style="display:block;margin:0 4px 6px">${l.kind === "peso" ? t("Movimiento") : t("Nombre")}</label>
      <input class="campo" id="t-nombre" value="${esc(l.ejercicio)}" style="background:#fff">
      ${l.kind === "peso" ? `<p class="mini" style="margin:6px 4px 0">${t("Aquí puedes cambiar el movimiento (por ejemplo «Power clean + push jerk»). Los kilos van en el texto de abajo con @.")}</p>` : ""}</div>
    <div><label class="paso-etq" for="t-texto" style="display:block;margin:0 4px 6px">${t("Esta semana")} (S${p.semana})</label>
      <textarea class="campo area grande" id="t-texto">${esc(l.texto || "")}</textarea></div>
    ${alcanceHtml(est.solo)}
    <label class="interruptor"><span>${t("Ajustar también la semana que viene")}${l.ciclo ? ` <small class="mini">(${t("ciclo")})</small>` : ""}</span><input type="checkbox" id="t-con-sig" ${abrirSig ? "checked" : ""}></label>
    <div id="t-sig-caja" ${abrirSig ? "" : "hidden"}><label class="paso-etq" for="t-sig" style="display:block;margin:0 4px 6px">${t("Semana que viene")} (S${p.semana + 1})</label>
      <textarea class="campo area grande" id="t-sig">${esc(l.texto_sig || l.texto || "")}</textarea></div>
    ${msgCoach(v)}
    <button class="btn btn-fuego" id="t-guardar">${v.puede_pesos === false ? t("Enviar a Diego para que lo apruebe") : t("Guardar")}</button>`, (h) => {
    enlazarAlcance(h, est);
    enlazarPin(h, () => hojaTexto(k));
    const tq = h.querySelector("#t-quitar");
    if (tq) tq.onclick = () => { cerrarHoja(); hacer({ tipo: "quitar_ajuste", semana: p.semana, linea: l.id, mensaje: (h.querySelector("#c-msg") || {}).value }); };
    h.querySelector("#t-con-sig").onchange = (ev) => { h.querySelector("#t-sig-caja").hidden = !ev.target.checked; };
    h.querySelector("#t-guardar").onclick = (ev) => {
      const texto = h.querySelector("#t-texto").value.trim();
      if (!texto) return aviso(t("Escribe qué toca"), true);
      const conSig = h.querySelector("#t-con-sig").checked;
      const cuerpo = { tipo: "editar_texto", semana: p.semana, linea: l.id, nombre: h.querySelector("#t-nombre").value, texto,
        solo_esta: est.solo, texto_sig: conSig ? h.querySelector("#t-sig").value : undefined, mensaje: (h.querySelector("#c-msg") || {}).value };
      ev.currentTarget.disabled = true; cerrarHoja(); hacer(cuerpo);
    };
  });
}

const TIPO_IDEAS = { "Conditioning & Volume": "volumen", "Conditioning": "conditioning", "Accessory": "accessory", "Mobility": "mobility",
  "Fuerza": "accessory", "WOD": "wod", "EMOM": "wod", "For time": "wod", "AMRAP": "wod", "Gym": "wod" };
const TIPOS_DEF = ["WOD", "EMOM", "For time", "AMRAP", "Conditioning", "Conditioning & Volume", "Accessory", "Mobility", "Fuerza", "Gym"];

async function hojaParte(p) {
  const v = E.vista;
  const kParte = p ? "p" + v.partes.indexOf(p) : null;
  const cambiar = !!p;
  const est = { tipo: cambiar ? "Conditioning" : "Conditioning & Volume", solo: true };
  if (!E.ideas) { try { E.ideas = await api("ideas"); } catch { E.ideas = {}; } }
  const tipos = (E.ideas && E.ideas.tipos) || TIPOS_DEF;
  const pintarIdeas = (h) => {
    const lista = (E.ideas[TIPO_IDEAS[est.tipo]] || []).slice(0, 30);
    h.querySelector("#p-ideas").innerHTML = lista.length ? lista.map((x, i) => `<button type="button" class="idea" data-idea="${i}"><b>${esc(x.nombre || x.texto.split("\n")[0])}</b><span>${esc(x.texto)}</span></button>`).join("")
      : `<div class="mini">${t("Sin ideas guardadas para este tipo todavía.")}</div>`;
    h.querySelectorAll("[data-idea]").forEach((b) => b.onclick = () => {
      const x = lista[+b.dataset.idea];
      h.querySelector("#p-nombre").value = x.nombre || ""; h.querySelector("#p-texto").value = x.texto;
      h.querySelector("#p-texto").scrollIntoView({ block: "center", behavior: "smooth" });
    });
  };
  abrirHoja(`${cabHoja(cambiar ? `${p.letra ? p.letra + " · " : ""}${etqParte(p.etiqueta)}` : esc(trDia(v.dia.nombre)), cambiar ? t("Cambiar esta parte") : t("Añadir parte"))}
    ${avisoCoach(v)}
    ${cambiar && p.es_cambio ? `<button class="btn btn-negro" id="p-volver">↩ ${t("Volver a lo que había")}</button>` : ""}
    <div><div class="paso-etq" style="margin:0 4px 8px">${t("Tipo")}</div>
      <div class="fila-chips">${tipos.map((x) => `<button type="button" class="chip ${x === est.tipo ? "on" : ""}" data-tp="${esc(x)}">${esc(x === "Fuerza" ? t("Fuerza") : x)}</button>`).join("")}</div></div>
    <div><label class="paso-etq" for="p-nombre" style="display:block;margin:0 4px 6px">${t("Nombre")} (${t("opcional")})</label>
      <input class="campo" id="p-nombre" style="background:#fff" placeholder="5 x 400 m"></div>
    <div><label class="paso-etq" for="p-texto" style="display:block;margin:0 4px 6px">${t("Qué toca")}</label>
      <textarea class="campo area grande" id="p-texto" placeholder="5 x 400 m run every 3'"></textarea></div>
    ${alcanceHtml(est.solo)}
    ${msgCoach(v)}
    <button class="btn btn-fuego" id="p-guardar">${v.puede_pesos === false ? t("Enviar a Diego para que lo apruebe") : cambiar ? t("Cambiar") : t("Añadir")}</button>
    <div><div class="paso-etq" style="margin:6px 4px 8px">${t("Ideas")} · <span id="p-tipo-ideas">${esc(est.tipo)}</span></div><div class="ideas" id="p-ideas"></div></div>`, (h) => {
    enlazarAlcance(h, est);
    enlazarPin(h, () => hojaParte(kParte && kParte !== "p-1" ? parteDe(kParte) : null));
    pintarIdeas(h);
    h.querySelectorAll("[data-tp]").forEach((b) => b.onclick = () => {
      est.tipo = b.dataset.tp;
      h.querySelectorAll("[data-tp]").forEach((x) => x.classList.toggle("on", x === b));
      h.querySelector("#p-tipo-ideas").textContent = est.tipo; pintarIdeas(h);
    });
    const volver = h.querySelector("#p-volver");
    if (volver) volver.onclick = () => { cerrarHoja(); hacer({ tipo: "deshacer_parte", dia: p.dia_id, parte: p.parte, semana: p.semana, mensaje: (h.querySelector("#c-msg") || {}).value }); };
    h.querySelector("#p-guardar").onclick = (ev) => {
      const texto = h.querySelector("#p-texto").value.trim();
      if (!texto) return aviso(t("Escribe qué toca"), true);
      const cuerpo = { tipo: cambiar ? "cambiar_parte" : "anadir_parte", dia: cambiar ? p.dia_id : E.dia, parte: cambiar ? p.parte : undefined,
        semana: cambiar ? p.semana : E.semana, etiqueta: est.tipo, nombre: h.querySelector("#p-nombre").value, texto, solo_esta: est.solo,
        mensaje: (h.querySelector("#c-msg") || {}).value };
      ev.currentTarget.disabled = true; cerrarHoja(); hacer(cuerpo);
    };
  });
}

// ---------- al azar ----------
function poolAzar(p, l) {
  const I = E.ideas || {};
  const etq = String(p.etiqueta || "").toLowerCase();
  let pool;
  if (/volume/.test(etq)) pool = I.volumen;
  else if (l.tipo === "conditioning") pool = I.conditioning;
  else if (l.tipo === "accessory") pool = I.accessory;
  else if (l.tipo === "mobility") pool = I.mobility;
  else {
    pool = I.wod || [];
    const quien = `${p.etiqueta} ${l.ejercicio} ${l.texto || ""}`;
    const FORM = { emom: /\b(e\d?mom|every|cada \d)/i, amrap: /\bamrap\b/i, fortime: /for time|\brft\b|por tiempo/i };
    const clave = FORM[l.tipo] ? l.tipo : Object.keys(FORM).find((f) => FORM[f].test(quien));
    const formato = FORM[clave];
    if (formato) { const f = pool.filter((x) => formato.test(x.nombre + " " + x.texto)); if (f.length) pool = f; }
  }
  const actual = String(l.texto || "").trim().toLowerCase();
  const vistos = new Set();
  return (pool || []).filter((x) => {
    const k = String(x.texto || "").trim().toLowerCase();
    if (!k || k === actual || vistos.has(k)) return false;
    vistos.add(k); return true;
  });
}

async function hojaAzar(k) {
  const v = E.vista;
  const { p, l } = lineaDe(k);
  if (!E.ideas) { try { E.ideas = await api("ideas"); } catch { E.ideas = {}; } }
  const pool = poolAzar(p, l);
  if (!pool.length) return aviso(t("No hay más ideas de este tipo todavía"), true);
  const est = { solo: true, i: Math.floor(Math.random() * pool.length), usados: new Set() };
  const pintarIdea = (h) => {
    const x = pool[est.i];
    h.querySelector("#az-nombre").textContent = x.nombre || etqParte(p.etiqueta);
    h.querySelector("#az-texto").textContent = x.texto;
  };
  abrirHoja(`${cabHoja(`${p.letra ? p.letra + " · " : ""}${etqParte(p.etiqueta)}`, "🎲 " + t("Al azar"))}
    ${avisoCoach(v)}
    <div class="mini">${t("Ahora")}: ${esc((l.texto || "").split("\n")[0].slice(0, 80) || t("por definir"))}</div>
    <div class="card azar-card"><b id="az-nombre"></b><div class="texto-wod" id="az-texto"></div></div>
    <button class="btn" id="az-otro">🎲 ${t("Otro")}</button>
    ${alcanceHtml(est.solo)}
    ${msgCoach(v)}
    <button class="btn btn-fuego" id="az-usar">${v.puede_pesos === false ? t("Enviar a Diego para que lo apruebe") : t("Usar este")}</button>
    <div class="mini">${pool.length} ${t("ideas de este tipo (tu biblioteca y el repertorio)")}</div>`, (h) => {
    pintarIdea(h);
    enlazarAlcance(h, est);
    enlazarPin(h, () => hojaAzar(k));
    h.querySelector("#az-otro").onclick = () => {
      est.usados.add(est.i);
      if (est.usados.size >= pool.length) est.usados.clear();
      let j; do { j = Math.floor(Math.random() * pool.length); } while ((est.usados.has(j) || j === est.i) && pool.length > 1);
      est.i = j; pintarIdea(h);
    };
    h.querySelector("#az-usar").onclick = (ev) => {
      const x = pool[est.i];
      ev.currentTarget.disabled = true; cerrarHoja();
      hacer({ tipo: "editar_texto", semana: p.semana, linea: l.id, nombre: x.nombre || l.ejercicio, texto: x.texto,
        solo_esta: est.solo, mensaje: (h.querySelector("#c-msg") || {}).value });
    };
  });
}

async function hojaActividad() {
  abrirHoja(`${cabHoja(t("Solo para ti"), t("Quién usa la app"))}<div class="cargador" style="margin:30px auto"></div>`);
  let d;
  try { d = await api("actividad"); } catch (e) { cerrarHoja(); return aviso(e.message, true); }
  if ($hoja.hidden) return;
  const filas = d.personas.map((p) => {
    const activo = p.dias7 > 0 ? "on" : p.dias30 > 0 ? "medio" : "";
    const racha = `<div class="act-racha" aria-label="${t("Últimos 14 días")}">${p.racha.map((x) => `<i class="${x ? "si" : ""}"></i>`).join("")}</div>`;
    const datos = p.demo
      ? `${p.entradas} ${t(p.entradas === 1 ? "entrada en total" : "entradas en total")} · ${p.entradas7} ${t("esta semana")}`
      : `${p.dias7} ${t(p.dias7 === 1 ? "día esta semana" : "días esta semana")} · ${p.dias30} ${t("en 30 días")}<br>${p.registros30 ? `🏋️ ${p.registros30} ${t("entrenos registrados (30 días)")}` : t("Sin entrenos registrados en 30 días")}${p.ultimo_registro ? ` · ${t("último")}: ${esc(p.ultimo_registro)}` : ""}`;
    const nComp = (p.comp_app || 0) + (p.comp_entreno || 0);
    const comp = nComp || p.llegadas ? `<div class="act-comp">📤 ${nComp} ${t(nComp === 1 ? "vez compartido" : "veces compartido")}${nComp ? ` (${p.comp_app} app · ${p.comp_entreno} ${t(p.comp_entreno === 1 ? "entreno" : "entrenos")})` : ""}
      ${p.llegadas ? `<br>👋 ${p.llegadas} ${t(p.llegadas === 1 ? "persona ha entrado con su enlace" : "personas han entrado con su enlace")}${p.llegadas_qr ? ` (${p.llegadas_qr} ${t("con el QR")})` : ""}` : ""}
      ${p.comp_lista && p.comp_lista.length ? `<small>${p.comp_lista.map((x) => esc(x.tipo === "app" ? t("la app") : x.que)).join(" · ")}</small>` : ""}</div>` : "";
    return `<div class="act-fila ${activo}"><div class="act-cab"><span class="avatar">${p.demo ? "👀" : esc(inicial(p.nombre))}</span>
      <div><b>${esc(p.nombre)}</b><small>${esc(p.hace)}</small></div></div>
      ${racha}<div class="mini">${datos}</div>${comp}</div>`;
  }).join("");
  $hoja.firstElementChild.innerHTML = `<div class="asa"></div>${cabHoja(t("Solo para ti"), t("Quién usa la app"))}
    <p class="mini" style="margin:0 4px">${t("Cada cuadrito es un día de las últimas 2 semanas (el último es hoy). Naranja = abrió la app ese día.")}
    ${d.desde ? "" : `<br><b>${t("Se empieza a contar desde hoy.")}</b>`}</p>
    <div class="act-totales"><div><b>${d.total_compartidos || 0}</b><span>${t("veces compartido")}</span></div>
      <div><b>${d.total_llegadas || 0}</b><span>${t("han entrado por un enlace")}</span></div></div>
    ${d.pagos && d.pagos.length ? `<div class="act-pagos"><b>🧾 ${t("Pagos por comprobar")} (${d.pagos.filter((x) => !x.visto).length})</b>
      ${d.pagos.map((x) => `<div class="pago ${x.visto ? "visto" : ""}"><div><b>${esc(x.nombre)}</b> <small>${esc(x.hace)}${x.perfil ? " · " + t("perfil") + ": " + esc(x.perfil) : ""}</small><br>
        <a href="tel:${esc(x.telefono)}">📞 ${esc(x.telefono)}</a> · <a href="mailto:${esc(x.email)}">${esc(x.email)}</a>
        ${x.cs ? `<br><small>Stripe: ${esc(x.cs.slice(0, 24))}…</small>` : ""}</div>
        <button class="chip ${x.visto ? "on" : ""}" data-pago="${esc(x.id)}" data-visto="${x.visto ? 1 : 0}">${x.visto ? "✓ " + t("Comprobado") : t("Marcar comprobado")}</button></div>`).join("")}</div>` : ""}
    ${d.likes && d.likes.length ? `<div class="act-altas" style="border-left-color:#e0245e"><b>❤️ ${t("WODs que más gustan")}</b>
      ${d.likes.map((x) => `<span><b>${x.n}</b> · ${esc(x.nombre)} <small>(${esc(x.quien.join(", "))})</small></span>`).join("")}</div>` : ""}
    ${d.contactos && d.contactos.length ? `<div class="act-altas" style="border-left-color:#25D366"><b>💬 ${d.contactos.reduce((a, x) => a + x.n, 0)} ${t("veces han pulsado «Contactar»")}</b>
      <span>${d.contactos.map((x) => `${esc(x.nombre)} <small>(${x.n > 1 ? x.n + "× · " : ""}${esc(x.hace)})</small>`).join(" · ")}</span></div>` : ""}
    <div class="act-altas" style="border-left-color:#1baf7a"><b>💳 ${d.abonos.reduce((a, x) => a + x.n, 0)} ${t("veces han pulsado «Abonarse»")}</b>
      ${d.abonos.length ? `<span>${d.abonos.map((x) => `${esc(x.nombre)} <small>(${x.n > 1 ? x.n + "× · " : ""}${esc(x.hace)})</small>`).join(" · ")}</span>` : ""}
      <small>${d.abono_activo ? t("Los pagos de verdad los ves en Stripe (cada pago lleva el nombre de quien pulsó).") : t("El botón aún no sale: falta poner ABONO_URL en Vercel.")}</small></div>
    ${d.altas && d.altas.length ? `<div class="act-altas"><b>✨ ${d.altas.length} ${t(d.altas.length === 1 ? "perfil creado desde la demo" : "perfiles creados desde la demo")}</b>
      <span>${d.altas.map((a) => `${esc(a.nombre)} <small>(${esc(a.hace)})</small>`).join(" · ")}</span></div>` : ""}
    <div class="act-lista">${filas}</div>`;
  $hoja.querySelectorAll("[data-cerrar]").forEach((b) => b.onclick = cerrarHoja);
  $hoja.querySelectorAll("[data-pago]").forEach((b) => b.onclick = async () => {
    b.disabled = true;
    try { await api("pago_visto", { metodo: "POST", cuerpo: { id: b.dataset.pago, deshacer: b.dataset.visto === "1" } }); hojaActividad(); }
    catch (e) { aviso(e.message, true); b.disabled = false; }
  });
}

function hojaSolicitudes() {
  const v = E.vista;
  const fecha = (iso) => { try { return new Date(iso).toLocaleDateString(E.lang === "fr" ? "fr-FR" : "es-ES", { day: "numeric", month: "short" }); } catch { return ""; } };
  abrirHoja(`${cabHoja(t("Modo coach"), t("Cambios que te piden"))}
    ${v.solicitudes.length ? v.solicitudes.map((x) => `<div class="solicitud">
      <div class="sol-cab"><span class="avatar">${esc(inicial(x.nombre))}</span><div><b>${esc(x.nombre)}</b><small>${esc(x.ejercicio)} · S${x.semana} · ${fecha(x.fecha)}</small></div></div>
      ${x.kind ? `<div class="sol-texto">${esc(x.resumen || "")}</div>` : `<div class="sol-pesos"><span>${esc(x.antes.map(num).join(" · ") || "—")}</span>${ic.der.replace(/#FFB400/g, "#D93A00")}<b>${esc(x.valores.map(num).join(" · "))} kg</b></div>`}
      ${x.solo_semana ? `<div class="mini">${t("Solo esa semana")}</div>` : ""}
      ${x.mensaje ? `<div class="sol-msg">«${esc(x.mensaje)}»</div>` : ""}
      <div class="dos"><button class="btn" data-rechazar="${esc(x.id)}">${t("Rechazar")}</button><button class="btn btn-fuego" data-aprobar="${esc(x.id)}" style="height:50px">${t("Aprobar")}</button></div>
    </div>`).join("") : `<p>${t("No hay nada pendiente.")}</p>`}`, (h) => {
    const resolver = async (id, aprobar, b) => {
      b.disabled = true;
      try {
        const r = await api("resolver", { metodo: "POST", cuerpo: { id, aprobar, atleta: E.atleta, ver_semana: E.semana, ver_dia: E.dia } });
        poner(r);
        if (r.solicitudes && r.solicitudes.length) hojaSolicitudes(); else cerrarHoja();
      } catch (e) { aviso(e.message, true); b.disabled = false; }
    };
    h.querySelectorAll("[data-aprobar]").forEach((b) => b.onclick = () => resolver(b.dataset.aprobar, true, b));
    h.querySelectorAll("[data-rechazar]").forEach((b) => b.onclick = () => resolver(b.dataset.rechazar, false, b));
  });
}

function hojaPronto(nombre) {
  const v = E.vista;
  abrirHoja(`${cabHoja(t("Pronto"), nombre)}
    <p style="margin:0;font-size:15px">${t("Esto llega en la siguiente fase.")}${v.app_antigua ? " " + t("Mientras, está en la app de siempre:") : ""}</p>
    ${v.app_antigua ? `<a class="btn btn-fuego" href="${esc(v.app_antigua)}" target="_blank" rel="noopener">${t("Abrir la app de siempre")}</a>` : ""}`);
}

// ---------- registrar ----------
const hoyISO = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };

function abrirRegistrar(reg, partesMarcadas, extra = {}) {
  const v = E.vista;
  const base = reg || { tipo: "wod", titulo: "", filas: [], partes: [] };
  const marcadas = new Set(partesMarcadas || (base.partes || []).map((p) => p.parte));
  E.borrador = {
    tipo: extra.tipo || base.tipo || "wod", titulo: base.titulo || "", fecha: hoyISO(), duracion: extra.duracion || "",
    notas: "", foto: null,
    filas: (base.filas && base.filas.length ? base.filas : [{ name: "", valor: "", unit: "tiempo" }, { name: "", valor: "", unit: "kg" }])
      .map((f) => ({ ...f, valor: extra.filas && extra.filas[f.id] ? extra.filas[f.id].valor : f.valor,
        unit: extra.filas && extra.filas[f.id] ? extra.filas[f.id].unit : f.unit })),
    partes: (base.partes || []).map((p) => ({ ...p, on: marcadas.has(p.parte) })),
  };
  E.pantalla = "registrar";
  pintar();
  window.scrollTo(0, 0);
  if (!v) return;
}

function leerBorrador() {
  const b = E.borrador;
  const f = document.getElementById("f-registro");
  if (!b || !f) return b;
  b.titulo = f.querySelector("#r-titulo").value;
  b.fecha = f.querySelector("#r-fecha").value || hoyISO();
  b.duracion = f.querySelector("#r-duracion").value;
  b.notas = f.querySelector("#r-notas").value;
  b.filas = [...f.querySelectorAll(".fila-res")].map((el) => ({ id: el.dataset.id || undefined,
    name: el.querySelector("[data-n]").value, valor: el.querySelector("[data-v]").value, unit: el.querySelector("[data-u]").value }));
  return b;
}

function pintarRegistrar() {
  const v = E.vista;
  const b = E.borrador || (abrirRegistrar(null), E.borrador);
  const tipos = v.tipos || { fuerza: "Fuerza", wod: "WOD", gym: "Gym", endurance: "Endurance", otro: "Otro" };
  const unidades = v.unidades || ["tiempo", "kg", "reps", "km", "m", "cal", "rondas"];
  $app.innerHTML = `
  <header class="cabecera registro-cab">
    <div class="fila-cab">
      <div><small class="sobre">${esc(v.nombre)}</small><h1 class="titulo-pant">${t("Registrar")}</h1></div>
      <button class="redondo" id="r-cerrar" aria-label="Volver">${ic.x}</button>
    </div>
  </header>
  <main>
  <form id="f-registro" class="registro" novalidate>
    <div><div class="lbl">${t("Tipo")}</div>
      <div class="fila-chips">${Object.entries(tipos).map(([k, n]) => `<button type="button" class="chip ${b.tipo === k ? "on" : ""}" data-tipo="${k}">${esc(trTipo(k, n))}</button>`).join("")}</div></div>
    ${b.partes.length ? `<div><div class="lbl">${t("Partes que has hecho")}</div>
      <div class="fila-chips">${b.partes.map((p, i) => `<button type="button" class="chip ${p.on ? "on" : ""}" data-parte="${i}">${p.on ? ic.ok : ""}${esc(p.warmup ? "Warm up" : String(p.texto).split(" · ").map(etqParte).join(" · "))}</button>`).join("")}</div>
      <div class="mini" style="margin-top:6px">${t("Se marcan como hechas al guardar.")}</div></div>` : ""}
    <div><label class="lbl" for="r-titulo">${t("Título")}</label>
      <input class="campo" id="r-titulo" value="${esc(trDia(b.titulo))}" placeholder="Fran, Pierna, 10K suave…"></div>
    <div class="dos">
      <div><label class="lbl" for="r-fecha">${t("Fecha")}</label><input class="campo" type="date" id="r-fecha" value="${esc(b.fecha)}" max="${hoyISO()}"></div>
      <div><label class="lbl" for="r-duracion">${t("Duración total")}</label><input class="campo" id="r-duracion" value="${esc(b.duracion)}" placeholder="mm:ss" inputmode="numeric"></div>
    </div>
    <div><div class="lbl">${t("Resultados")}</div>
      <div class="resultados">${b.filas.map((f, i) => `
        <div class="fila-res" data-id="${esc(f.id || "")}">
          <input class="campo campo-n" data-n value="${esc(f.name)}" placeholder="${t("Ejercicio")}" aria-label="${t("Ejercicio")}">
          <div class="fila-res-b">
            <input class="campo campo-v" data-v value="${esc(f.valor)}" placeholder="${f.unit === "tiempo" ? "4:35" : "0"}" inputmode="${f.unit === "tiempo" ? "numeric" : "decimal"}" aria-label="${t("Resultado")}">
            <select class="campo campo-u" data-u aria-label="Unidad">${unidades.map((u) => `<option value="${u}" ${u === f.unit ? "selected" : ""}>${trUnidad(u)}</option>`).join("")}</select>
            <button type="button" class="quitar" data-quitar="${i}" aria-label="Quitar">${ic.x}</button>
          </div>
        </div>`).join("")}</div>
      <button type="button" class="btn" id="r-fila" style="margin-top:8px;width:100%">+ ${t("Añadir resultado")}</button>
      <div class="mini" style="margin-top:6px">${t("Tiempos como 4:35. Escribe cada ejercicio siempre igual para ver su progresión.")}</div></div>
    <div><label class="lbl" for="r-notas">${t("Notas")}</label>
      <textarea class="campo area" id="r-notas" placeholder="${t("Sensaciones, escalado, qué falló…")}">${esc(b.notas)}</textarea></div>
    <div><div class="lbl">${t("Foto")}</div>
      <div class="fotos">
        ${b.foto ? `<div class="miniatura" style="background-image:url('${b.foto}')"><button type="button" class="quitar" id="r-sin-foto" aria-label="Quitar foto">${ic.x}</button></div>` : ""}
        <label class="anadir-foto">${ic.camara}<span>${b.foto ? t("Cambiar") : t("Añadir")}</span>
          <input type="file" accept="image/*" id="r-foto" hidden></label>
      </div></div>
    <p class="error" id="r-error" hidden></p>
    <button type="submit" class="btn btn-fuego" id="r-guardar">${t("Guardar entreno")}</button>
  </form>
  </main>` + nav("registrar");
  enlazar();
  const f = document.getElementById("f-registro");
  document.getElementById("r-cerrar").onclick = () => { E.pantalla = "rutina"; E.borrador = null; pintar(); };
  f.querySelectorAll("[data-tipo]").forEach((x) => x.onclick = () => { leerBorrador(); b.tipo = x.dataset.tipo; pintar(); });
  f.querySelectorAll("[data-parte]").forEach((x) => x.onclick = () => { leerBorrador(); b.partes[+x.dataset.parte].on = !b.partes[+x.dataset.parte].on; pintar(); });
  f.querySelectorAll("[data-quitar]").forEach((x) => x.onclick = () => { leerBorrador(); b.filas.splice(+x.dataset.quitar, 1); pintar(); });
  document.getElementById("r-fila").onclick = () => {
    leerBorrador(); b.filas.push({ name: "", valor: "", unit: b.tipo === "fuerza" ? "kg" : "tiempo" }); pintar();
    const ns = $app.querySelectorAll("[data-n]"); ns[ns.length - 1].focus();
  };
  f.querySelectorAll("[data-u]").forEach((x) => x.onchange = () => { leerBorrador(); pintar(); });
  const sinFoto = document.getElementById("r-sin-foto");
  if (sinFoto) sinFoto.onclick = () => { leerBorrador(); b.foto = null; pintar(); };
  document.getElementById("r-foto").onchange = async (ev) => {
    const archivo = ev.target.files && ev.target.files[0];
    if (!archivo) return;
    leerBorrador();
    try { b.foto = await comprimir(archivo); pintar(); } catch { aviso(t("Esa foto no se puede leer. Prueba con otra o haz una captura."), true); }
  };
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    leerBorrador();
    const err = document.getElementById("r-error");
    const boton = document.getElementById("r-guardar");
    if (E.ocupado) return;
    E.ocupado = true; boton.disabled = true; boton.textContent = t("Guardando…"); err.hidden = true;
    try {
      const r = await api("registrar", { metodo: "POST", cuerpo: {
        atleta: E.atleta, tipo: b.tipo, titulo: b.titulo, fecha: b.fecha, duracion: b.duracion, notas: b.notas,
        filas: b.filas, foto: b.foto, partes: b.partes.filter((p) => p.on), ver_semana: E.semana, ver_dia: E.dia } });
      E.pantalla = "rutina"; E.borrador = null;
      poner(r);
      window.scrollTo(0, 0);
    } catch (e) {
      err.textContent = e.message; err.hidden = false; boton.disabled = false; boton.textContent = t("Guardar entreno");
      err.scrollIntoView({ block: "center", behavior: "smooth" });
    } finally { E.ocupado = false; }
  };
}

function comprimir(archivo, lado = 1600, calidad = 0.82) {
  return new Promise((ok, mal) => {
    const url = URL.createObjectURL(archivo);
    const img = new Image();
    img.onload = () => {
      const k = Math.min(1, lado / Math.max(img.naturalWidth, img.naturalHeight));
      const c = document.createElement("canvas");
      c.width = Math.round(img.naturalWidth * k); c.height = Math.round(img.naturalHeight * k);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      ok(c.toDataURL("image/jpeg", calidad));
    };
    img.onerror = () => { URL.revokeObjectURL(url); mal(new Error("imagen")); };
    img.src = url;
  });
}

function confeti() {
  const caja = document.createElement("div");
  caja.className = "confeti";
  const colores = ["#FF6A00", "#FFB400", "#1F1208", "#D93A00", "#1E9E5A"];
  caja.innerHTML = Array.from({ length: 60 }, (_, i) => `<i style="left:${Math.random() * 100}%;background:${colores[i % 5]};animation-delay:${Math.random() * 0.6}s;animation-duration:${1.6 + Math.random() * 1.4}s;transform:rotate(${Math.random() * 360}deg)"></i>`).join("");
  document.body.appendChild(caja);
  setTimeout(() => caja.remove(), 3600);
}

// ---------- reloj (cronómetro, cuenta atrás, For time, AMRAP, EMOM, Tabata) ----------
const MODOS = { libre: "Cronómetro", cuenta: "Cuenta atrás", fortime: "For time", amrap: "AMRAP", emom: "EMOM", tabata: "Tabata" };
const fmtSeg = (s) => {
  s = Math.max(0, Math.round(s));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}` : `${m}:${String(r).padStart(2, "0")}`;
};
const fmtCorto = (s) => (s % 60 === 0 ? `${s / 60}'` : s < 60 ? `${s}"` : fmtSeg(s));

function etiquetaCrono(c) {
  if (!c) return "";
  if (c.modo === "emom") return `EMOM ${c.minutos}'` + (c.intervalo && c.intervalo !== 60 ? ` · ${t("cada")} ${fmtSeg(c.intervalo)}` : "");
  if (c.modo === "amrap") return `AMRAP ${c.minutos}'`;
  if (c.modo === "cuenta") return `${t("Cuenta atrás")} ${c.minutos}'`;
  if (c.modo === "fortime") return "For time" + (c.minutos ? ` · ${t("tope")} ${c.minutos}'` : "");
  if (c.modo === "tabata") return `${fmtCorto(c.trabajo || 20)} / ${fmtCorto(c.descanso ?? 10)} × ${c.rondasTab || c.rondas || 8}`;
  return t("Cronómetro");
}

const C = { el: null, timer: null, audio: null, lock: null };

function sonido(frec = 880, ms = 140, vol = 0.25) {
  try {
    C.audio = C.audio || new (window.AudioContext || window.webkitAudioContext)();
    if (C.audio.state === "suspended") C.audio.resume();
    const o = C.audio.createOscillator(), g = C.audio.createGain();
    o.frequency.value = frec; o.type = "square"; g.gain.value = vol;
    o.connect(g); g.connect(C.audio.destination);
    o.start(); o.stop(C.audio.currentTime + ms / 1000);
  } catch { }
  try { navigator.vibrate && navigator.vibrate(ms > 300 ? [300, 100, 300] : 60); } catch { }
}

async function pantallaEncendida(si) {
  try {
    if (si && "wakeLock" in navigator && !C.lock) { C.lock = await navigator.wakeLock.request("screen"); C.lock.addEventListener?.("release", () => { C.lock = null; }); }
    if (!si && C.lock) { await C.lock.release(); C.lock = null; }
  } catch { }
}

function abrirCrono(p, l) {
  const guardado = (() => { try { return JSON.parse(mem.get("reloj") || "null"); } catch { return null; } })() || {};
  const cr = (l && l.crono) || { modo: guardado.modo || "libre" };
  C.p = p; C.l = l;
  C.s = { modo: cr.modo === "libre" && l ? "fortime" : cr.modo,
    minutos: cr.minutos ?? (l ? (cr.modo === "fortime" ? null : 12) : guardado.minutos ?? 12),
    intervalo: cr.intervalo || guardado.intervalo || 60,
    trabajo: cr.trabajo || guardado.trabajo || 20, descanso: cr.descanso ?? guardado.descanso ?? 10, rondasTab: cr.rondas || guardado.rondasTab || 8,
    estado: "parado", acumulado: 0, inicio: 0, rondas: 0, prep: 0, ultimoAviso: -1, fase: null,
    nivel: (l && l.nivel) || "RX", salir: 0 };
  if (!l && guardado.modo === "fortime") C.s.minutos = guardado.minutos ?? null;
  if (!C.el) { C.el = document.createElement("div"); C.el.id = "crono"; C.el.className = "crono"; document.body.appendChild(C.el); }
  C.el.hidden = false;
  document.body.style.overflow = "hidden";
  pintarCrono();
  clearInterval(C.timer);
  C.timer = setInterval(tick, 200);
  document.addEventListener("visibilitychange", alVolver);
}

function recordarAjustes() {
  if (C.l) return; // solo el reloj suelto recuerda lo último que usaste
  const s = C.s;
  mem.set("reloj", JSON.stringify({ modo: s.modo, minutos: s.minutos, intervalo: s.intervalo, trabajo: s.trabajo, descanso: s.descanso, rondasTab: s.rondasTab }));
}

function alVolver() { if (!document.hidden && C.s && C.s.estado === "corre") pantallaEncendida(true); }

function cerrarCrono() {
  clearInterval(C.timer); C.timer = null;
  pantallaEncendida(false);
  document.removeEventListener("visibilitychange", alVolver);
  if (C.el) { C.el.hidden = true; C.el.innerHTML = ""; }
  desbloquearScroll();
}

const transcurrido = () => C.s.acumulado + (C.s.estado === "corre" ? Date.now() - C.s.inicio : 0);

// Intervalos: EMOM = trabajo «intervalo» sin descanso; Tabata = trabajo + descanso
function intervalos(s) {
  if (s.modo === "emom") { const iv = s.intervalo || 60; return { trabajo: iv, descanso: 0, rondas: Math.max(1, Math.round((s.minutos || 1) * 60 / iv)) }; }
  return { trabajo: s.trabajo || 20, descanso: s.descanso || 0, rondas: s.rondasTab || 8 };
}

function totalSeg(s) {
  if (s.modo === "emom" || s.modo === "tabata") { const iv = intervalos(s); return iv.rondas * (iv.trabajo + iv.descanso) - (s.modo === "tabata" ? iv.descanso : 0); }
  if (s.modo === "amrap" || s.modo === "cuenta") return (s.minutos || 0) * 60;
  if (s.modo === "fortime") return s.minutos ? s.minutos * 60 : 0;
  return 0;
}

function datosCrono() {
  const s = C.s, seg = transcurrido() / 1000, total = totalSeg(s);
  if (s.estado === "prep") {
    const quedan = Math.max(0, Math.ceil((s.prep - Date.now()) / 1000));
    return { grande: String(quedan), sub: t("Prepárate"), prog: 1 - quedan / 10, fase: "prep" };
  }
  if ((s.modo === "emom" || s.modo === "tabata") && s.estado === "fin") {
    return { grande: fmtSeg(total), sub: t("Tiempo total"), prog: 1, fin: true, fase: "trabajo" };
  }
  if (s.modo === "emom" || s.modo === "tabata") {
    const iv = intervalos(s), ciclo = iv.trabajo + iv.descanso;
    const idx = Math.min(iv.rondas - 1, Math.floor(seg / ciclo));
    const dentro = seg - idx * ciclo;
    const trabajo = dentro < iv.trabajo || !iv.descanso;
    const queda = trabajo ? iv.trabajo - dentro : ciclo - dentro;
    const fase = s.modo === "emom" ? "trabajo" : (trabajo ? "trabajo" : "descanso");
    const etiqueta = s.modo === "emom" ? `${t("Minuto")} ${idx + 1} ${t("de")} ${iv.rondas}`
      : `${trabajo ? t("TRABAJO") : t("DESCANSO")} · ${idx + 1}/${iv.rondas}`;
    return { grande: fmtSeg(Math.max(0, queda)), sub: etiqueta, prog: trabajo ? dentro / iv.trabajo : (dentro - iv.trabajo) / iv.descanso,
      fin: seg >= total, fase, queda, idx };
  }
  if (s.modo === "amrap" || s.modo === "cuenta") {
    return { grande: fmtSeg(total - seg), sub: s.modo === "amrap" ? `${s.rondas} ${t("rondas")}` : (s.rondas ? `${s.rondas} ${t("rondas")}` : `${t("de")} ${s.minutos}'`),
      prog: total ? seg / total : 0, fin: total && seg >= total, queda: total - seg, fase: "trabajo" };
  }
  const tope = s.modo === "fortime" && s.minutos ? s.minutos * 60 : 0;
  return { grande: fmtSeg(seg), sub: s.rondas ? `${s.rondas} ${t("rondas")}` : (tope ? `${t("Tope")} ${s.minutos}'` : ""),
    prog: tope ? seg / tope : (seg % 60) / 60, fin: tope && seg >= tope, queda: tope ? tope - seg : null, fase: "trabajo" };
}

function tick() {
  const s = C.s;
  if (!s || !C.el || C.el.hidden) return;
  if (s.estado === "prep") {
    const quedan = Math.ceil((s.prep - Date.now()) / 1000);
    if (quedan !== s.ultimoAviso) { s.ultimoAviso = quedan; if (quedan <= 3 && quedan > 0) sonido(660); }
    if (Date.now() >= s.prep) { s.estado = "corre"; s.inicio = Date.now(); s.ultimoAviso = -1; s.fase = "trabajo"; sonido(990, 500); pintarCrono(); return; }
  }
  if (s.estado === "corre") {
    const d = datosCrono();
    if (d.fin) {
      s.acumulado = totalSeg(s) * 1000; s.estado = "fin"; sonido(990, 900); pantallaEncendida(false); pintarCrono(); return;
    }
    if (d.fase !== s.fase) { // cambio de trabajo a descanso o al revés
      s.fase = d.fase; sonido(d.fase === "trabajo" ? 990 : 520, 450);
      C.el.querySelector(".crono-cab")?.classList.toggle("descanso", d.fase === "descanso");
    } else if (s.modo === "emom" && d.idx !== s.idx) {
      if (s.idx != null) sonido(990, 450);
    } else if (d.queda != null) {
      const q = Math.ceil(d.queda);
      const clave = Math.round(transcurrido() / 1000 + d.queda) + "|" + q;
      if (q <= 3 && q > 0 && clave !== s.ultimoAviso) { s.ultimoAviso = clave; sonido(660); }
    }
    s.idx = d.idx;
  }
  actualizarCrono();
}

function actualizarCrono() {
  const d = datosCrono();
  const g = C.el.querySelector("#c-grande"), sub = C.el.querySelector("#c-sub"), anillo = C.el.querySelector("#c-anillo");
  if (g) g.textContent = d.grande;
  if (sub) sub.textContent = d.sub;
  if (anillo) anillo.style.strokeDashoffset = String(CIRC * (1 - Math.min(1, Math.max(0, d.prog || 0))));
  const tot = C.el.querySelector("#c-total");
  if (tot) tot.textContent = fmtSeg(transcurrido() / 1000);
}
const CIRC = 2 * Math.PI * 96;

function ajuste(etq, clave, valor, txt) {
  return `<div class="crono-min"><small>${etq}</small>
    <button data-aj="${clave}" data-d="-1" aria-label="${etq} −">−</button><span>${txt}</span>
    <button data-aj="${clave}" data-d="1" aria-label="${etq} +">+</button></div>`;
}

function pintarCrono() {
  const s = C.s, p = C.p, l = C.l;
  const parado = s.estado === "parado";
  const corre = s.estado === "corre" || s.estado === "prep";
  const d = datosCrono();
  const tituloCr = l ? (p.lineas.length === 1 && l.solo_bloque ? p.etiqueta : l.ejercicio) : t("Reloj");
  const norm = (x) => String(x || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  const versiones = l ? (l.versiones_nivel || { RX: l.visto }) : null;
  const texto = l ? (versiones[s.nivel] || l.visto || "") : "";
  const conRondas = !["emom", "tabata"].includes(s.modo);
  const ajustes = !parado ? "" : {
    libre: "",
    cuenta: ajuste(t("Minutos"), "minutos", s.minutos, `${s.minutos}'`),
    amrap: ajuste(t("Minutos"), "minutos", s.minutos, `${s.minutos}'`),
    fortime: ajuste(t("Tope"), "minutos", s.minutos, s.minutos ? `${s.minutos}'` : t("sin tope")),
    emom: ajuste(t("Total"), "minutos", s.minutos, `${s.minutos}'`) +
      `<div class="fila-chips cada" style="justify-content:center"><small class="cada-etq">${t("Cada")}</small>${[60, 90, 120, 180].map((iv) => `<button class="chip oscuro ${s.intervalo === iv ? "on" : ""}" data-iv="${iv}">${fmtSeg(iv)}</button>`).join("")}</div>`,
    tabata: ajuste(t("Trabajo"), "trabajo", s.trabajo, fmtCorto(s.trabajo)) + ajuste(t("Descanso"), "descanso", s.descanso, s.descanso ? fmtCorto(s.descanso) : "0") +
      ajuste(t("Rondas"), "rondasTab", s.rondasTab, String(s.rondasTab)),
  }[s.modo];
  C.el.innerHTML = `
  <div class="crono-cab ${d.fase === "descanso" ? "descanso" : ""}">
    <div class="crono-barra">
      <button class="redondo oscuro" id="c-cerrar" aria-label="Cerrar">${ic.izq.replace(/#FFB400/g, "#fff")}</button>
      <span class="crono-donde">${l ? `${esc(E.vista.dia ? E.vista.dia.nombre : "")}${p.letra ? " · " + t("Parte") + " " + esc(p.letra) : ""}` : "Djimenez Prog"}</span>
      <span class="crono-total" title="${t("Tiempo total")}">${!parado && (s.modo === "emom" || s.modo === "tabata") ? `<span id="c-total">${fmtSeg(transcurrido() / 1000)}</span>` : ""}</span>
    </div>
    <div class="crono-tit">
      <span class="etq-modo">${esc(t(MODOS[s.modo] || s.modo))}</span>
      <h2>${esc(tituloCr)}</h2>
      ${norm(etiquetaCrono(s)) !== norm(tituloCr) ? `<p>${esc(etiquetaCrono(s))}${s.modo === "tabata" || s.modo === "emom" ? ` · ${t("total")} ${fmtSeg(totalSeg(s))}` : ""}</p>` : ""}
    </div>
    ${parado ? `<div class="crono-modos">
      <div class="modos-scroll">${Object.entries(MODOS).map(([k, n]) => `<button class="chip oscuro ${s.modo === k ? "on" : ""}" data-modo="${k}">${t(n)}</button>`).join("")}</div>
      ${ajustes}
      ${s.modo === "tabata" ? `<div class="fila-chips" style="justify-content:center">${[[20, 10, 8, "Tabata 20/10"], [40, 20, 10, "40/20"], [30, 30, 10, "30/30"], [45, 15, 8, "45/15"]].map(([a, b, r, n]) =>
        `<button class="chip oscuro ${s.trabajo === a && s.descanso === b && s.rondasTab === r ? "on" : ""}" data-pre="${a},${b},${r}">${n}</button>`).join("")}</div>` : ""}
    </div>` : ""}
    <div class="crono-centro ${parado ? "compacto" : ""}">
      <div class="crono-reloj">
        <svg width="236" height="236" viewBox="0 0 236 236" aria-hidden="true">
          <circle cx="118" cy="118" r="96" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="14"/>
          <circle id="c-anillo" cx="118" cy="118" r="96" fill="none" stroke="url(#gc)" stroke-width="14" stroke-linecap="round"
            stroke-dasharray="${CIRC}" stroke-dashoffset="${CIRC * (1 - Math.min(1, Math.max(0, d.prog || 0)))}" transform="rotate(-90 118 118)"/>
          <defs><linearGradient id="gc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFB400"/><stop offset="1" stop-color="#FF5A1F"/></linearGradient></defs>
        </svg>
        <div class="crono-num"><b id="c-grande">${esc(d.grande)}</b><span id="c-sub">${esc(d.sub)}</span></div>
      </div>
      <div class="crono-botones">
        <button class="c-btn c-sec" id="c-reset" aria-label="${t("Reiniciar")}" ${parado ? "disabled" : ""}>${ic.reinicio}</button>
        <button class="c-btn c-main" id="c-play" aria-label="${corre ? t("Pausa") : t("Empezar")}">${corre ? ic.pausa : ic.play}</button>
        <button class="c-btn c-sec c-ronda" id="c-ronda" aria-label="${t("Sumar ronda")}" ${conRondas ? "" : "disabled"}><b>+1</b><small>${t("ronda")}</small></button>
      </div>
      ${s.estado === "fin" ? `<div class="crono-fin">${t("¡Terminado!")}</div>` : ""}
      ${l && (s.estado === "fin" || (s.estado === "pausa" && transcurrido() > 0)) ? `<button class="btn btn-fuego" id="c-guardar" style="width:100%">${t("Terminar y guardar")}</button>` : ""}
      ${!l && (s.estado === "fin" || (s.estado === "pausa" && transcurrido() > 0)) ? `<button class="btn btn-fuego" id="c-guardar" style="width:100%">${t("Guardar como entreno")}</button>` : ""}
    </div>
  </div>
  ${l ? `<div class="crono-cuerpo">
    ${l.versiones_nivel ? `<div class="pestanas">${Object.keys(l.versiones_nivel).map((n) => `<button class="${n === s.nivel ? "on" : ""}" data-nivel="${n}">${n}</button>`).join("")}</div>` : ""}
    <div class="card"><div class="texto-wod">${esc(texto)}</div></div>
    ${l.elite ? `<div class="elite"><span class="ico">${ic.estrella}</span><span><b>${esc(l.elite.quien)}: ${esc(l.elite.marca)}</b> · ${esc(l.elite.detalle)}</span></div>` : ""}
  </div>` : ""}`;
  const q = (id) => C.el.querySelector(id);
  q("#c-cerrar").onclick = () => {
    if (s.estado === "corre" && Date.now() - s.salir > 2500) { s.salir = Date.now(); return aviso(t("Va en marcha: pulsa otra vez para salir")); }
    cerrarCrono();
  };
  C.el.querySelectorAll("[data-modo]").forEach((b) => b.onclick = () => {
    s.modo = b.dataset.modo;
    if (["cuenta", "amrap", "emom"].includes(s.modo) && !s.minutos) s.minutos = s.modo === "emom" ? 10 : 12;
    recordarAjustes(); pintarCrono();
  });
  C.el.querySelectorAll("[data-aj]").forEach((b) => b.onclick = () => {
    const k = b.dataset.aj, dd = +b.dataset.d;
    if (k === "minutos") {
      const n = (s.minutos || 0) + dd;
      s.minutos = s.modo === "fortime" ? (n <= 0 ? null : n) : Math.max(1, n);
    } else if (k === "trabajo") s.trabajo = Math.max(5, s.trabajo + dd * 5);
    else if (k === "descanso") s.descanso = Math.max(0, s.descanso + dd * 5);
    else if (k === "rondasTab") s.rondasTab = Math.max(1, s.rondasTab + dd);
    recordarAjustes(); pintarCrono();
  });
  C.el.querySelectorAll("[data-pre]").forEach((b) => b.onclick = () => {
    const [a, bb, r] = b.dataset.pre.split(",").map(Number); s.trabajo = a; s.descanso = bb; s.rondasTab = r; recordarAjustes(); pintarCrono();
  });
  C.el.querySelectorAll("[data-iv]").forEach((b) => b.onclick = () => { s.intervalo = +b.dataset.iv; recordarAjustes(); pintarCrono(); });
  C.el.querySelectorAll("[data-nivel]").forEach((b) => b.onclick = () => { s.nivel = b.dataset.nivel; pintarCrono(); });
  q("#c-play").onclick = () => {
    if (s.estado === "parado" || s.estado === "fin") {
      if (s.estado === "fin") { s.acumulado = 0; s.rondas = 0; }
      sonido(440, 60, 0.05); // desbloquea el sonido en el móvil
      s.estado = "prep"; s.prep = Date.now() + 10000; s.ultimoAviso = -1; s.fase = null; s.idx = null; pantallaEncendida(true);
    } else if (s.estado === "prep") { s.estado = "parado"; pantallaEncendida(false); }
    else if (s.estado === "corre") { s.acumulado = transcurrido(); s.estado = "pausa"; pantallaEncendida(false); }
    else if (s.estado === "pausa") { s.inicio = Date.now(); s.estado = "corre"; pantallaEncendida(true); }
    pintarCrono();
  };
  q("#c-reset").onclick = () => { Object.assign(s, { estado: "parado", acumulado: 0, rondas: 0, fase: null }); pantallaEncendida(false); pintarCrono(); };
  q("#c-ronda").onclick = () => { if (conRondas && (s.estado === "corre" || s.estado === "pausa")) { s.rondas++; sonido(770, 60, 0.12); actualizarCrono(); } };
  const g = q("#c-guardar");
  if (g) g.onclick = () => guardarDesdeCrono();
}

function guardarDesdeCrono() {
  const s = C.s, p = C.p, l = C.l;
  const seg = Math.round(transcurrido() / 1000);
  if (!l) {
    cerrarCrono();
    const fila = s.modo === "amrap" || (s.rondas && ["cuenta", "libre"].includes(s.modo))
      ? { name: etiquetaCrono(s), valor: String(s.rondas || ""), unit: "rondas" }
      : { name: etiquetaCrono(s), valor: ["fortime", "libre"].includes(s.modo) ? fmtSeg(seg) : "", unit: "tiempo" };
    abrirRegistrar({ tipo: "wod", titulo: etiquetaCrono(s), filas: [fila], partes: [] }, [], { duracion: fmtSeg(seg) });
    return;
  }
  const reg = p.registro || E.vista.registro;
  const filas = {};
  if (s.modo === "amrap" || (s.modo === "cuenta" && s.rondas)) filas[l.id] = { valor: String(s.rondas || ""), unit: "rondas" };
  else if (s.modo === "fortime" || s.modo === "libre") filas[l.id] = { valor: fmtSeg(seg), unit: "tiempo" };
  const marcadas = p.registro ? [p.parte] : E.vista.partes.filter((x) => x.estado !== "hecho" || x.parte === p.parte).map((x) => x.parte);
  cerrarCrono();
  abrirRegistrar(reg, marcadas, { filas, duracion: fmtSeg(seg), tipo: "wod" });
  if (s.nivel && s.nivel !== "RX") setTimeout(() => { const n = document.getElementById("r-notas"); if (n && !n.value) n.value = `Versión ${s.nivel}`; }, 0);
}

// ---------- progreso, historial y PRs ----------
async function irA(pantalla, extra = {}) {
  E.pantalla = pantalla;
  if (extra.sub) E.sub = extra.sub;
  window.scrollTo(0, 0);
  $app.innerHTML = cabeceraPantalla(pantalla) + `<main><div class="vacio"><div class="cargador oscuro"></div></div></main>` + nav(pantalla);
  enlazar();
  const ruta = pantalla === "prs" ? "prs" : (E.sub === "historial" ? "historial" : "progreso");
  try {
    E.datos = await api(ruta, { q: { atleta: E.atleta } });
    if (E.pantalla === pantalla) pintar();
  } catch (e) { aviso(e.message, true); }
}

function cabeceraPantalla(pantalla) {
  const v = E.vista || {};
  const titulo = pantalla === "prs" ? t("Mis récords") : t("Progreso");
  const varias = (v.personas || []).length > 1;
  return `<header class="cabecera registro-cab">
    <div class="fila-cab">
      <button class="quien" id="b-persona" ${varias ? "" : "disabled"} aria-label="${t("Personas")}">
        <span class="avatar">${esc(inicial(v.nombre))}</span>
        <span><small>${esc(v.nombre || "")} ${varias ? ic.abajo : ""}</small><strong class="titulo-pant">${titulo}</strong></span>
      </button>
      <button class="redondo" id="b-reloj" aria-label="${t("Reloj")}">${ic.reloj.replace("currentColor", "#1F1208")}</button>
    </div>
    ${pantalla === "progreso" ? `<div class="pestanas pest-cab"><button class="${E.sub !== "historial" ? "on" : ""}" data-sub="resumen">${t("Resumen")}</button>
      <button class="${E.sub === "historial" ? "on" : ""}" data-sub="historial">${t("Historial")}</button></div>` : ""}
  </header>`;
}

function pintarPantalla() {
  const d = E.datos;
  const p = E.pantalla;
  let cuerpo = "";
  if (!d || d.atleta !== E.atleta) return irA(p);
  if (p === "prs") cuerpo = pintarPrs(d);
  else if (E.sub === "historial") { if (!d.entrenos) return irA(p); cuerpo = pintarHistorial(d); }
  else { if (!d.kpis) return irA(p); cuerpo = pintarProgreso(d); }
  $app.innerHTML = cabeceraPantalla(p) + `<main>${cuerpo}</main>` + nav(p);
  enlazar();
  enlazarPantalla();
}

// --- gráficas (SVG a mano: línea fina, puntos ≥8px, rejilla tenue, una sola escala) ---
const fechaCorta = (iso) => { const [y, m, d] = iso.split("-"); return `${+d}/${+m}`; };

function graficaLinea(pts, unidad, mejorF) {
  if (!pts.length) return "";
  const W = 326, H = 170, L = 44, R = 12, T = 16, B = 26;
  const vs = pts.map((p) => p.v);
  let lo = Math.min(...vs), hi = Math.max(...vs);
  if (lo === hi) { lo -= 1; hi += 1; }
  const pad = (hi - lo) * 0.12; lo -= pad; hi += pad;
  const inv = unidad === "tiempo"; // en tiempos menos es mejor: arriba = más rápido
  const x = (i) => pts.length === 1 ? (L + W - R) / 2 : L + i * (W - L - R) / (pts.length - 1);
  const y = (v) => { const r = (v - lo) / (hi - lo); return T + (inv ? r : 1 - r) * (H - T - B); };
  const etq = (v) => unidad === "tiempo" ? fmtSeg(v) : num(Math.round(v * 10) / 10);
  const ticks = [lo + pad, (lo + hi) / 2, hi - pad];
  const linea = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");
  const area = `${linea} L${x(pts.length - 1).toFixed(1)},${H - B} L${x(0).toFixed(1)},${H - B} Z`;
  return `<svg class="graf" viewBox="0 0 ${W} ${H}" role="img" aria-label="${t("Evolución")}">
    <defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eb6834" stop-opacity=".22"/><stop offset="1" stop-color="#eb6834" stop-opacity="0"/></linearGradient></defs>
    ${ticks.map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="rejilla"/><text x="${L - 6}" y="${y(v) + 4}" class="eje" text-anchor="end">${etq(v)}</text>`).join("")}
    <path d="${area}" fill="url(#ga)"/>
    <path d="${linea}" fill="none" stroke="#D93A00" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    ${pts.map((p, i) => {
      const best = p.f === mejorF;
      return `<g class="pt" data-tip="${esc(fechaCorta(p.f))}: ${esc(p.txt)}${best ? " · " + t("mejor marca") : ""}">
        <circle cx="${x(i)}" cy="${y(p.v)}" r="16" fill="transparent"/>
        <circle cx="${x(i)}" cy="${y(p.v)}" r="${best ? 7 : 4.5}" fill="${best ? "#1F1208" : "#D93A00"}" stroke="#fff" stroke-width="2"/></g>`;
    }).join("")}
    <text x="${x(0)}" y="${H - 6}" class="eje" text-anchor="${pts.length === 1 ? "middle" : "start"}">${fechaCorta(pts[0].f)}</text>
    ${pts.length > 1 ? `<text x="${x(pts.length - 1)}" y="${H - 6}" class="eje" text-anchor="end">${fechaCorta(pts[pts.length - 1].f)}</text>` : ""}
  </svg>`;
}

function graficaSemanas(sem) {
  const W = 326, H = 150, L = 6, R = 6, T = 20, B = 24;
  const n = sem.lunes.length;
  const tot = sem.lunes.map((_, i) => sem.tipos.reduce((a, tp) => a + tp.n[i], 0));
  const max = Math.max(1, ...tot);
  const ancho = (W - L - R) / n, bw = Math.min(26, ancho * 0.62);
  const alto = (c) => c / max * (H - T - B);
  return `<svg class="graf" viewBox="0 0 ${W} ${H}" role="img" aria-label="${t("Entrenos por semana")}">
    <line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" class="base"/>
    ${sem.lunes.map((lu, i) => {
      const cx = L + ancho * i + ancho / 2;
      let yAc = H - B;
      const seg = sem.tipos.filter((tp) => tp.n[i]).map((tp, j, arr) => {
        const h = alto(tp.n[i]);
        const ultimo = j === arr.length - 1;
        yAc -= h;
        const gap = j ? 2 : 0; // separación de 2px entre tramos
        const r = ultimo ? 4 : 0;
        const y0 = yAc, h0 = h - gap;
        return ultimo
          ? `<path d="M${cx - bw / 2},${y0 + h0} V${y0 + r} Q${cx - bw / 2},${y0} ${cx - bw / 2 + r},${y0} H${cx + bw / 2 - r} Q${cx + bw / 2},${y0} ${cx + bw / 2},${y0 + r} V${y0 + h0} Z" fill="${tp.color}"/>`
          : `<rect x="${cx - bw / 2}" y="${y0}" width="${bw}" height="${Math.max(0, h0)}" fill="${tp.color}"/>`;
      }).join("");
      const detalle = sem.tipos.filter((tp) => tp.n[i]).map((tp) => `${tp.n[i]} ${tp.nombre}`).join(", ") || t("sin entrenos");
      return `<g class="pt" data-tip="${t("Semana del")} ${lu}: ${esc(detalle)}">
        <rect x="${cx - ancho / 2}" y="${T - 10}" width="${ancho}" height="${H - T - B + 10}" fill="transparent"/>
        ${seg}${tot[i] ? `<text x="${cx}" y="${H - B - alto(tot[i]) - 5}" class="eje fuerte" text-anchor="middle">${tot[i]}</text>` : ""}
        <text x="${cx}" y="${H - 7}" class="eje ${i === n - 1 ? "fuerte" : ""}" text-anchor="middle">${lu}</text></g>`;
    }).join("")}
  </svg>
  <div class="leyenda">${sem.tipos.map((tp) => `<span><i style="background:${tp.color}"></i>${esc(tp.nombre)}</span>`).join("")}</div>`;
}

const ICONO_NIVEL = { bueno: ["ok", "bien"], malo: ["x", "mal"], aviso: ["aviso", "aviso"], info: ["info", "info"], tipo: ["info", "info"] };

function pintarProgreso(d) {
  const k = d.kpis;
  const sel = d.series.find((s) => s.key === E.serie) || d.series[0];
  if (sel) E.serie = sel.key;
  return `
  <div class="kpis">
    <div class="kpi"><b>${k.mes}</b><span>${t("entrenos en 30 días")}</span></div>
    <div class="kpi oscuro"><b>${k.partes == null ? "—" : k.partes + "%"}</b><span>${t("partes hechas (4 sem.)")}</span></div>
    <div class="kpi"><b>${k.seguidas}</b><span>${k.seguidas === 1 ? t("semana seguida") : t("semanas seguidas")}</span></div>
  </div>
  ${k.total ? `<section class="card"><div class="lbl" style="margin:0">${t("Entrenos por semana")}</div>${graficaSemanas(d.semanas)}</section>` : ""}
  ${d.consejos.length ? `<section class="card"><div class="lbl" style="margin:0">${t("Dónde mejorar")}</div>
    <div class="consejos">${d.consejos.map((c) => `<div class="consejo ${ICONO_NIVEL[c.nivel][1]}"><span class="c-ico">${icNivel(c.nivel)}</span>
      <div><b>${esc(c.titulo)}</b><span>${esc(c.detalle)}</span></div></div>`).join("")}</div></section>` : ""}
  ${sel ? `<section class="card">
    <div class="lbl" style="margin:0">${t("Progresión por ejercicio")}</div>
    <select class="campo sel-serie" id="sel-serie" aria-label="${t("Ejercicio")}">${d.series.map((s) => `<option value="${esc(s.key)}" ${s.key === sel.key ? "selected" : ""}>${esc(s.nombre)} (${esc(s.unidad)}) · ${s.n}</option>`).join("")}</select>
    <div class="stats">
      <div><small>${t("Mejor")}</small><b>${esc(sel.mejor.txt)}</b><span>${fechaCorta(sel.mejor.fecha)}</span></div>
      <div><small>${t("Última")}</small><b>${esc(sel.ultima.txt)}</b><span>${fechaCorta(sel.ultima.fecha)}</span></div>
      <div><small>${t("Desde el inicio")}</small><b class="${sel.pct > 0 ? "sube" : sel.pct < 0 ? "baja" : ""}">${sel.pct == null ? "—" : (sel.pct > 0 ? "+" : "") + num(sel.pct) + "%"}</b><span>${sel.n} ${t("registros")}</span></div>
    </div>
    ${graficaLinea(sel.pts, sel.unidad, sel.mejor.fecha)}
    <div class="mini">${sel.unidad === "tiempo" ? t("En tiempos, arriba es más rápido. El punto negro es tu mejor marca.") : t("Arriba es mejor. El punto negro es tu mejor marca.")}</div>
  </section>` : `<div class="vacio">${t("Cuando registres resultados (kg, tiempos, reps…) verás aquí tu progresión.")}</div>`}`;
}

function icNivel(n) {
  if (n === "bueno") return ic.ok;
  if (n === "malo") return ic.x.replace("#1F1208", "currentColor");
  return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true">${n === "aviso" ? '<path d="M12 4l9 16H3zM12 10v4M12 17v.5"/>' : '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.5"/>'}</svg>`;
}

function pintarHistorial(d) {
  const tipos = [...new Set(d.entrenos.map((w) => w.tipo))];
  const lista = d.entrenos.filter((w) => !E.filtroTipo || w.tipo === E.filtroTipo);
  if (!d.entrenos.length) return `<div class="vacio">${t("Aún no hay entrenos. Pulsa + para guardar el primero.")}</div>`;
  return `
  <div class="fila-chips">${[["", t("Todos")], ...tipos.map((k) => [k, d.tipos[k] || k])].map(([k, n]) =>
    `<button class="chip ${(E.filtroTipo || "") === k ? "on" : ""}" data-filtro="${k}">${k ? `<i class="punto-tipo" style="background:${d.colores[k] || "#999"}"></i>` : ""}${esc(n)}</button>`).join("")}</div>
  <div class="mini" style="padding:0 4px">${lista.length} ${t("de")} ${d.entrenos.length} ${t("entrenos")}</div>
  ${lista.map((w) => `<article class="card entreno">
    <div class="ent-cab"><span class="etq-tipo" style="--c:${d.colores[w.tipo] || "#999"}">${esc(w.tipo_txt)}</span>
      <span class="mini">${esc(trFecha(w.fecha_txt))}${w.duracion ? " · " + esc(w.duracion) : ""}</span></div>
    <div class="ent-cuerpo">
      ${w.foto ? `<button class="ent-foto" data-foto="${esc(w.foto)}" style="background-image:url('${esc(w.foto)}')" aria-label="${t("Ver foto")}"></button>` : ""}
      <div style="flex:1;min-width:0">
        ${w.titulo ? `<b class="ent-tit">${esc(w.titulo)}</b>` : ""}
        ${w.resultados.length ? `<ul class="ent-res">${w.resultados.map((r) => `<li><span>${esc(r.nombre)}</span><b>${esc(r.valor)}</b>${r.pr ? `<i class="pr">PR</i>` : ""}</li>`).join("")}</ul>` : ""}
        ${w.notas ? `<div class="mini">${esc(w.notas)}</div>` : ""}
      </div>
    </div>
    <div class="ent-pie"><button class="mini-btn" data-borrar="${esc(w.id)}">${E.confirmar === w.id ? t("¿Seguro? Pulsa otra vez") : t("Borrar")}</button></div>
  </article>`).join("")}`;
}

function pintarPrs(d) {
  if (d.sin_prs) return `<div class="vacio">${t("Este perfil no tiene récords.")}</div>`;
  const cats = d.categorias;
  const cat = cats.find((c) => c.cat === E.catPr) || cats[0];
  return `
  ${d.ultimo ? `<section class="pr-hero"><span class="pr-ico">${ic.copa.replace("currentColor", "#1F1208")}</span>
    <div><small>${t("Último PR")} · ${esc(trFecha(d.ultimo.fecha))}</small><b>${esc(d.ultimo.mov)}${d.ultimo.reps && d.ultimo.reps > 1 ? ` · ${d.ultimo.reps}RM` : ""}</b><span>${esc(d.ultimo.valor)}</span></div></section>` : ""}
  <button class="btn btn-fuego" id="b-nuevo-pr">+ ${t("Apuntar un PR")}</button>
  ${cats.length ? `<div class="fila-chips">${cats.map((c) => `<button class="chip ${c === cat ? "on" : ""}" data-cat="${esc(c.cat)}">${esc(c.cat.replace(/^\S+\s/, ""))}</button>`).join("")}</div>
  <div class="prs">${cat.filas.map((f, i) => `<button class="pr-card" data-pr="${i}">
    <span class="n">${esc(f.mov)}${f.reps && f.reps > 1 ? ` · ${f.reps}RM` : ""}</span>
    <span class="v">${esc(f.valor)}</span>
    <span class="d">${f.nuevo ? `<i class="nuevo">${t("este mes")}</i>` : ""}${esc(f.fecha.replace(/^\S+ /, ""))}</span>
  </button>`).join("")}</div>
  <div class="mini" style="padding:0 4px">${t("Salen solos de lo que registras si el ejercicio se llama igual (por ejemplo «Back squat», «RMU» o «5 km run»).")}</div>`
  : `<div class="vacio">${t("Todavía no hay PRs. Apunta el primero.")}</div>`}`;
}

function enlazarPantalla() {
  const d = E.datos;
  $app.querySelectorAll("[data-sub]").forEach((b) => b.onclick = () => { if ((E.sub || "resumen") !== b.dataset.sub) irA("progreso", { sub: b.dataset.sub }); });
  const sel = document.getElementById("sel-serie");
  if (sel) sel.onchange = () => { E.serie = sel.value; pintar(); };
  $app.querySelectorAll("[data-filtro]").forEach((b) => b.onclick = () => { E.filtroTipo = b.dataset.filtro || null; pintar(); });
  $app.querySelectorAll("[data-borrar]").forEach((b) => b.onclick = async () => {
    if (E.confirmar !== b.dataset.borrar) { E.confirmar = b.dataset.borrar; pintar(); return; }
    E.confirmar = null; b.disabled = true;
    try { E.datos = await api("borrar_entreno", { metodo: "POST", cuerpo: { atleta: E.atleta, id: b.dataset.borrar } }); pintar(); aviso(E.datos.aviso); }
    catch (e) { aviso(e.message, true); b.disabled = false; }
  });
  $app.querySelectorAll("[data-foto]").forEach((b) => b.onclick = () => abrirHoja(`${cabHoja(t("Foto"), "")}<img class="foto-grande" src="${esc(b.dataset.foto)}" alt="">`));
  $app.querySelectorAll("[data-cat]").forEach((b) => b.onclick = () => { E.catPr = b.dataset.cat; pintar(); });
  $app.querySelectorAll("[data-pr]").forEach((b) => b.onclick = () => {
    const cat = d.categorias.find((c) => c.cat === E.catPr) || d.categorias[0];
    hojaPr(cat.filas[+b.dataset.pr]);
  });
  const np = document.getElementById("b-nuevo-pr");
  if (np) np.onclick = hojaNuevoPr;
  // toque en un punto o barra: muestra su valor
  $app.querySelectorAll(".graf .pt").forEach((g) => g.onclick = (ev) => mostrarTip(ev, g.dataset.tip));
}

function mostrarTip(ev, txt) {
  let tip = document.getElementById("tip");
  if (!tip) { tip = document.createElement("div"); tip.id = "tip"; tip.className = "tip"; document.body.appendChild(tip); }
  tip.textContent = txt;
  tip.hidden = false;
  const x = Math.min(window.innerWidth - 12, Math.max(12, ev.clientX));
  tip.style.left = x + "px"; tip.style.top = (ev.clientY - 14) + "px";
  clearTimeout(mostrarTip._t);
  mostrarTip._t = setTimeout(() => { tip.hidden = true; }, 2600);
}

function hojaPr(f) {
  abrirHoja(`${cabHoja(t("Récord"), f.mov + (f.reps && f.reps > 1 ? ` · ${f.reps}RM` : ""))}
    <div class="pr-grande">${esc(f.valor)}<small>${esc(trFecha(f.fecha))}${f.registro ? " · " + t("de un registro") : ""}</small></div>
    ${f.nota ? `<div class="mini">${esc(f.nota)}</div>` : ""}
    ${f.evol.length > 1 ? `<div class="card" style="box-shadow:none">${graficaLinea(f.evol, f.unidad, f.evol.reduce((b, x) => (f.unidad === "tiempo" ? x.v < b.v : x.v > b.v) ? x : b, f.evol[0]).f)}</div>
      <div class="lista-evol">${[...f.evol].reverse().map((x) => `<div><span>${fechaCorta(x.f)}</span><b>${esc(x.txt)}</b></div>`).join("")}</div>`
      : `<div class="mini">${t("Cuando tengas más marcas de este movimiento verás aquí su evolución.")}</div>`}`, (h) => {
    h.querySelectorAll(".graf .pt").forEach((g) => g.onclick = (ev) => mostrarTip(ev, g.dataset.tip));
  });
}

function hojaNuevoPr() {
  const d = E.datos;
  const cats = Object.keys(d.catalogo);
  const est = { cat: E.catPr && d.catalogo[E.catPr] ? E.catPr : cats[1] || cats[0] };
  const unidadDe = (cat, mov) => (d.catalogo[cat].find((m) => m.mov === mov) || {}).unidad
    || (/Halter|Fuerza/.test(cat) ? "kg" : /Carrera/.test(cat) ? "tiempo" : "reps");
  const pintarForm = (h) => {
    const movs = d.catalogo[est.cat];
    h.querySelector("#pr-movs").innerHTML = movs.map((m, i) => `<option ${i === 0 ? "selected" : ""}>${esc(m.mov)}</option>`).join("") + `<option value="__otro">${t("Otro…")}</option>`;
    actualizar(h);
  };
  const actualizar = (h) => {
    const mov = h.querySelector("#pr-movs").value;
    h.querySelector("#pr-otro-caja").hidden = mov !== "__otro";
    const u = unidadDe(est.cat, mov);
    h.querySelector("#pr-valor").placeholder = { kg: "120", reps: "15", tiempo: "21:30" }[u];
    h.querySelector("#pr-unidad").textContent = { kg: "kg", reps: "reps", tiempo: "min:seg" }[u];
    h.querySelector("#pr-reps-caja").hidden = u !== "kg";
  };
  abrirHoja(`${cabHoja(t("Récords"), t("Apuntar un PR"))}
    <div class="fila-chips">${cats.map((c) => `<button type="button" class="chip ${c === est.cat ? "on" : ""}" data-pc="${esc(c)}">${esc(c.replace(/^\S+\s/, ""))}</button>`).join("")}</div>
    <div><label class="paso-etq" for="pr-movs" style="display:block;margin:0 4px 6px">${t("Movimiento")}</label>
      <select class="campo" id="pr-movs" style="background:#fff"></select></div>
    <div id="pr-otro-caja" hidden><input class="campo" id="pr-otro" placeholder="${t("¿Cuál?")}" style="background:#fff"></div>
    <div class="dos">
      <div><label class="paso-etq" for="pr-valor" style="display:block;margin:0 4px 6px">${t("Marca")} (<span id="pr-unidad"></span>)</label>
        <input class="campo campo-v" id="pr-valor" inputmode="decimal" style="background:#fff"></div>
      <div id="pr-reps-caja"><label class="paso-etq" for="pr-reps" style="display:block;margin:0 4px 6px">${t("Reps (1 = 1RM)")}</label>
        <input class="campo campo-v" id="pr-reps" type="number" min="1" max="20" value="1" style="background:#fff"></div>
    </div>
    <div class="dos">
      <div><label class="paso-etq" for="pr-fecha" style="display:block;margin:0 4px 6px">${t("Fecha")}</label><input class="campo" type="date" id="pr-fecha" value="${hoyISO()}" max="${hoyISO()}" style="background:#fff"></div>
      <div><label class="paso-etq" for="pr-nota" style="display:block;margin:0 4px 6px">${t("Nota")}</label><input class="campo" id="pr-nota" placeholder="${t("con cinturón…")}" style="background:#fff"></div>
    </div>
    <button class="btn btn-fuego" id="pr-guardar">${t("Guardar PR")}</button>`, (h) => {
    pintarForm(h);
    h.querySelector("#pr-movs").onchange = () => actualizar(h);
    h.querySelectorAll("[data-pc]").forEach((b) => b.onclick = () => {
      est.cat = b.dataset.pc; h.querySelectorAll("[data-pc]").forEach((x) => x.classList.toggle("on", x === b)); pintarForm(h);
    });
    h.querySelector("#pr-guardar").onclick = async (ev) => {
      const boton = ev.currentTarget;
      const sel = h.querySelector("#pr-movs").value;
      const mov = sel === "__otro" ? h.querySelector("#pr-otro").value.trim() : sel;
      boton.disabled = true;
      try {
        const r = await api("guardar_pr", { metodo: "POST", cuerpo: { atleta: E.atleta, cat: est.cat, mov, valor: h.querySelector("#pr-valor").value,
          reps: h.querySelector("#pr-reps").value, fecha: h.querySelector("#pr-fecha").value, nota: h.querySelector("#pr-nota").value } });
        cerrarHoja(); E.datos = r; E.catPr = est.cat; pintar();
        aviso((r.pr ? "🎉 " : "") + r.aviso); if (r.pr) confeti();
      } catch (e) { aviso(e.message, true); boton.disabled = false; }
    };
  });
}

// ---------- arranque ----------
(async () => {
  const qs = new URLSearchParams(location.search);
  const inv = qs.get("inv");
  if (qs.get("pago") === "ok") { E.pagoCs = qs.get("cs") || ""; mem.set("pago_pendiente", E.pagoCs || "-"); }
  else if (mem.get("pago_pendiente")) E.pagoCs = mem.get("pago_pendiente") === "-" ? "" : mem.get("pago_pendiente");
  if (inv || qs.get("pago")) history.replaceState(null, "", location.pathname);
  if (E.pagoCs !== undefined && !E.token) { pintarEntrar(); E.pagoMostrado = true; return hojaPago(E.pagoCs); }
  if (inv && !E.token) {
    try {
      const r = await api("login", { metodo: "POST", cuerpo: { inv } });
      E.token = r.token; mem.set("token", r.token);
      if (r.solo) { E.atleta = r.solo; mem.set("atleta", r.solo); }
    } catch (e) { pintarEntrar(); return aviso(e.message, true); }
  }
  if (E.token) cargar(); else pintarEntrar();
})();
