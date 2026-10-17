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

const E = { token: mem.get("token"), atleta: mem.get("atleta"), lang: mem.get("lang") || "es", vista: null,
  semana: null, dia: null, ocupado: false };

// ---------- textos ----------
const FR = {
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
  "Solo esa semana": "Seulement cette semaine-là", "Ajustar": "Ajuster", "Semana que viene": "Semaine prochaine",
  "Cambiar esta parte": "Changer cette partie", "Añadir parte": "Ajouter une partie", "Novedad de Diego": "Nouveauté de Diego",
  "Diego se lo ha puesto. ¿Te viene bien hoy?": "Diego l'a fait. Ça te va aujourd'hui ?", "Hoy no": "Pas aujourd'hui",
  "Ponérmelo hoy": "Je le fais aujourd'hui", "Lo programa tu coach": "C'est ton coach qui programme",
  "Ej.: no llegaba a 8+8, he hecho 8+5": "Ex. : je n'arrivais pas à 8+8, j'ai fait 8+5", "Esta y las siguientes": "Celle-ci et les suivantes",
  "Nombre": "Nom", "Esta semana": "Cette semaine", "Ajustar también la semana que viene": "Ajuster aussi la semaine prochaine",
  "ciclo": "cycle", "Escribe qué toca": "Écris le programme", "Volver a lo que había": "Revenir à l'original", "opcional": "optionnel",
  "Qué toca": "Au programme", "Ideas": "Idées", "Sin ideas guardadas para este tipo todavía.": "Pas encore d'idées pour ce type.", "Tiempo total": "Temps total",
};
const t = (s) => (E.lang === "fr" && FR[s]) || s;

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
  const r = await fetch(url, {
    method: metodo, headers: { "Content-Type": "application/json", ...(E.token ? { Authorization: "Bearer " + E.token } : {}) },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  let d = {};
  try { d = await r.json(); } catch { }
  if (r.status === 401 && ruta !== "login") { salir(); throw new Error(d.error || "Entra otra vez"); }
  if (!r.ok) throw new Error(d.error || "Algo ha fallado (" + r.status + ")");
  return d;
}

function salir() {
  E.token = null; E.vista = null; mem.set("token", null); mem.set("atleta", null);
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
        <label for="i-pass">${t("Contraseña")} · Mot de passe</label>
        <input class="campo" id="i-pass" type="password" autocomplete="current-password" required>
      `}
      <p class="error" id="e-entrar" hidden></p>
      <button class="btn btn-fuego" type="submit">${inv && paso.nuevo ? t("Empezar") : t("Entrar")}</button>
      ${inv ? "" : `<p class="ayuda">${t("¿Eres nuevo? Entra con el código que te ha dado Diego")}</p>`}
    </form>
    <div class="fila-chips" style="justify-content:center">
      <button class="chip ${E.lang === "es" ? "on" : ""}" data-lang="es">ES</button>
      <button class="chip ${E.lang === "fr" ? "on" : ""}" data-lang="fr">FR</button>
    </div>
  </section>`;
  $app.querySelectorAll("[data-lang]").forEach((b) => b.onclick = () => { E.lang = b.dataset.lang; mem.set("lang", E.lang); pintarEntrar(paso); });
  const f = document.getElementById("f-entrar");
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    const err = document.getElementById("e-entrar");
    const boton = f.querySelector("button[type=submit]");
    const cuerpo = inv ? { password: paso.password, nombre: f.querySelector("#i-nombre").value, pin: f.querySelector("#i-pin").value,
      plantilla: (f.querySelector("input[name=plantilla]:checked") || {}).value } : { password: f.querySelector("#i-pass").value };
    boton.disabled = true; err.hidden = true;
    try {
      const r = await api("login", { metodo: "POST", cuerpo });
      if (r.invitado) return pintarEntrar({ invitado: true, nuevo: r.nuevo, plantillas: r.plantillas, password: cuerpo.password,
        nombre: cuerpo.nombre, pin: cuerpo.pin });
      E.token = r.token; mem.set("token", r.token);
      if (r.solo) { E.atleta = r.solo; mem.set("atleta", r.solo); }
      E.lang = r.lang || E.lang; mem.set("lang", E.lang);
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
  $app.className = "";
  if (E.pantalla === "registrar") return pintarRegistrar();
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
    <div class="titulo-dia"><h2>${esc(v.dia.nombre)}</h2><span>${total ? `${hechas} ${t("de")} ${total} ${t("partes hechas")}` : ""}</span></div>
    <div class="barra"><i style="width:${total ? Math.round(hechas / total * 100) : 0}%"></i></div>
    ${(v.novedades || []).map((n) => `<section class="novedad">
      <div class="nov-cab">${ic.llama("#FFB400", 22)}<div><small>${t("Novedad de Diego")} · ${esc(n.etiqueta)}</small><b>${esc(n.nombre)}</b></div></div>
      <div class="texto-wod">${esc(n.texto)}</div>
      <div class="mini" style="color:#FFD9BD">${t("Diego se lo ha puesto. ¿Te viene bien hoy?")}</div>
      <div class="nov-botones"><button class="btn" data-nov-no="${esc(n.id)}">${t("Hoy no")}</button>
        <button class="btn btn-fuego" data-nov-si="${esc(n.id)}" style="height:50px">${t("Ponérmelo hoy")}</button></div>
    </section>`).join("")}
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
    ${v.semana ? `<div class="pildora-semana">
      <button id="b-sem-menos" aria-label="Semana anterior" ${v.semana <= 1 ? "disabled style='opacity:.3'" : ""}>${ic.izq}</button>
      <span>${t("Semana")} ${v.semana}${v.semana === v.actual ? ` · <em>${t("de fuego")}</em>` : ""}</span>
      <button id="b-sem-mas" aria-label="Semana siguiente">${ic.der}</button>
    </div>` : ""}
    ${v.dias ? `<div class="dias" role="tablist">${v.dias.map((d) => {
      const n = (d.nombre.match(/\d+/) || [d.nombre.slice(0, 2)])[0];
      return `<button class="dia ${d.id === v.dia.id ? "on" : ""}" role="tab" aria-selected="${d.id === v.dia.id}" data-dia="${esc(d.id)}" aria-label="${esc(d.nombre)}">
        <small>D${esc(n)}</small><span class="punto ${d.estado}"></span>${d.pendientes ? '<span class="pend"></span>' : ""}</button>`;
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
      <div class="pesos">${pesos}</div>${nota}
      ${l.no_hecha !== undefined ? `<label class="check"><input type="checkbox" data-nh="${k}" ${l.no_hecha ? "checked" : ""}> ${t("No lo hice (repite peso la semana que viene)")}</label>` : ""}
    </div>`;
  }
  const visto = l.visto || "";
  const nombre = l.solo_bloque || (p.lineas.length === 1) ? "" : `<b>${esc(l.ejercicio)}</b>`;
  let html = `<div class="linea" data-l="${k}">
    ${nombre || extra || (l.nivel && l.nivel !== "RX") ? `<div class="linea-cab">${nombre}<span>${extra}${l.nivel && l.nivel !== "RX" && visto ? ` <span class="etq nivel">${esc(l.nivel)}</span>` : ""}</span></div>` : ""}
    <div class="texto-wod">${visto ? esc(visto) : `<span class="mini">${t("por definir")}</span>`}</div>${nota}`;
  if (l.sugerencia) html += `<div class="sug">${ic.llama("#8A5E00", 20)}<span>${t("WOD de Diego · semana")} ${l.sugerencia.semana}, ${esc(l.sugerencia.dia)}</span>
    <button data-fijar="${k}">${t("Fijar")}</button></div>`;
  if (l.tabla) html += `<details class="desplegable"><summary>${t("RX · Inter · Scaled por movimiento")} ${ic.abajo}</summary>
    <table class="tabla"><thead><tr><th>RX</th><th>Inter</th><th>Scaled</th></tr></thead><tbody>${l.tabla.map((f) =>
      f.RX === f.Inter && f.Inter === f.Scaled ? `<tr><td colspan="3" style="color:var(--tinta);font-weight:500">${esc(f.RX)}</td></tr>`
        : `<tr><td>${esc(f.RX)}</td><td>${esc(f.Inter)}</td><td>${esc(f.Scaled)}</td></tr>`).join("")}</tbody></table></details>`;
  else if (l.versiones_nivel) html += `<details class="desplegable"><summary>${t("Versiones")} RX · Inter · Scaled · Elite ${ic.abajo}</summary>
    <div class="versiones">${Object.entries(l.versiones_nivel).map(([n, txt]) => `<div><b>${esc(n)}</b><span class="texto-wod">${esc(txt)}</span></div>`).join("")}</div></details>`;
  if (!p.origen) html += `<div class="acciones-linea"><button class="mini-btn" data-editar="${k}">${ic.lapiz} ${t("Ajustar")}</button>${l.texto_sig && l.texto_sig !== l.texto ? `<span class="mini">${t("Semana que viene")}: ${esc(l.texto_sig.split("\n")[0].slice(0, 60))}</span>` : ""}</div>`;
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
    <button data-pronto="${t("Progreso")}" aria-label="${t("Progreso")}">${ic.grafica}</button>
    <button data-pronto="${t("Récords")}" aria-label="${t("Récords")}">${ic.copa}</button>
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
    if (b.dataset.ir === "registrar") abrirRegistrar(null); else { E.pantalla = "rutina"; pintar(); window.scrollTo(0, 0); }
  });
  on("b-registrar-dia", () => abrirRegistrar(v.registro, v.partes.filter((p) => p.estado !== "hecho").map((p) => p.parte)));
  $app.querySelectorAll("[data-reg]").forEach((b) => b.onclick = () => {
    const p = parteDe(b.dataset.reg); abrirRegistrar(p.registro, [p.parte]);
  });
  $app.querySelectorAll("[data-editar]").forEach((b) => b.onclick = () => hojaTexto(b.dataset.editar));
  $app.querySelectorAll("[data-menu]").forEach((b) => b.onclick = () => hojaParte(parteDe(b.dataset.menu)));
  on("b-anadir-parte", () => hojaParte(null));
  $app.querySelectorAll("[data-nov-si]").forEach((b) => b.onclick = () => hacer({ tipo: "ponerme_novedad", id: b.dataset.novSi, dia: E.dia, semana: E.semana }, b));
  $app.querySelectorAll("[data-nov-no]").forEach((b) => b.onclick = () => hacer({ tipo: "descartar_novedad", id: b.dataset.novNo }, b));
  $app.querySelectorAll("[data-crono]").forEach((b) => b.onclick = () => { const { p, l } = lineaDe(b.dataset.crono); abrirCrono(p, l); });
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
function cerrarHoja() { $hoja.hidden = true; $hoja.innerHTML = ""; document.body.style.overflow = ""; }
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
      <span>${t("¿Le has preguntado a Diego si este cambio es pertinente? Si se lo envías, lo aprueba él y se cambia solo.")}</span></div></div>`}
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
        <button class="btn" id="b-coach-salir" style="width:100%;margin-top:10px">${t("Quitar el modo coach en este móvil")}</button>`
      : `<div class="mini" style="margin-bottom:10px">${t("Solo para Diego: con el PIN del coach puedes cambiar los pesos y aprobar los cambios que te piden.")}</div>
        <div style="display:flex;gap:8px"><input class="campo" id="i-pin-coach" type="password" inputmode="numeric" placeholder="PIN" style="height:48px;background:#fff">
        <button class="btn btn-negro" id="b-coach">${t("Activar")}</button></div>`}
    </div>
    ${v.app_antigua ? `<a class="btn" href="${esc(v.app_antigua)}" target="_blank" rel="noopener">${t("Abrir la app de siempre")}</a>` : ""}
    <button class="btn btn-negro" id="b-salir">${t("Salir")}</button>`, (h) => {
    const bc = h.querySelector("#b-coach");
    if (bc) bc.onclick = async () => {
      bc.disabled = true;
      try {
        const r = await api("coach", { metodo: "POST", cuerpo: { pin: h.querySelector("#i-pin-coach").value } });
        E.token = r.token; mem.set("token", r.token); cerrarHoja(); aviso(t("Modo coach activado")); cargar();
      } catch (e) { aviso(e.message, true); bc.disabled = false; }
    };
    const bs = h.querySelector("#b-coach-salir");
    if (bs) bs.onclick = async () => {
      const r = await api("coach", { metodo: "POST", cuerpo: { salir: true } });
      E.token = r.token; mem.set("token", r.token); cerrarHoja(); aviso(t("Modo coach quitado")); cargar();
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

function avisoCoach(v) {
  return v.puede_pesos === false ? `<div class="aviso-coach">${ic.candado}<div><b>${t("Lo programa tu coach")}</b>
    <span>${t("¿Le has preguntado a Diego si este cambio es pertinente? Si se lo envías, lo aprueba él y se cambia solo.")}</span></div></div>` : "";
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
    <div><label class="paso-etq" for="t-nombre" style="display:block;margin:0 4px 6px">${t("Nombre")}</label>
      <input class="campo" id="t-nombre" value="${esc(l.ejercicio)}" style="background:#fff"></div>
    <div><label class="paso-etq" for="t-texto" style="display:block;margin:0 4px 6px">${t("Esta semana")} (S${p.semana})</label>
      <textarea class="campo area grande" id="t-texto">${esc(l.texto || "")}</textarea></div>
    ${alcanceHtml(est.solo)}
    <label class="interruptor"><span>${t("Ajustar también la semana que viene")}${l.ciclo ? ` <small class="mini">(${t("ciclo")})</small>` : ""}</span><input type="checkbox" id="t-con-sig" ${abrirSig ? "checked" : ""}></label>
    <div id="t-sig-caja" ${abrirSig ? "" : "hidden"}><label class="paso-etq" for="t-sig" style="display:block;margin:0 4px 6px">${t("Semana que viene")} (S${p.semana + 1})</label>
      <textarea class="campo area grande" id="t-sig">${esc(l.texto_sig || l.texto || "")}</textarea></div>
    ${msgCoach(v)}
    <button class="btn btn-fuego" id="t-guardar">${v.puede_pesos === false ? t("Enviar a Diego para que lo apruebe") : t("Guardar")}</button>`, (h) => {
    enlazarAlcance(h, est);
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
  abrirHoja(`${cabHoja(cambiar ? `${p.letra ? p.letra + " · " : ""}${etqParte(p.etiqueta)}` : esc(v.dia.nombre), cambiar ? t("Cambiar esta parte") : t("Añadir parte"))}
    ${avisoCoach(v)}
    ${cambiar && p.es_cambio ? `<button class="btn btn-negro" id="p-volver">↩ ${t("Volver a lo que había")}</button>` : ""}
    <div><div class="paso-etq" style="margin:0 4px 8px">${t("Tipo")}</div>
      <div class="fila-chips">${tipos.map((x) => `<button type="button" class="chip ${x === est.tipo ? "on" : ""}" data-tp="${esc(x)}">${esc(x)}</button>`).join("")}</div></div>
    <div><label class="paso-etq" for="p-nombre" style="display:block;margin:0 4px 6px">${t("Nombre")} (${t("opcional")})</label>
      <input class="campo" id="p-nombre" style="background:#fff" placeholder="5 x 400 m"></div>
    <div><label class="paso-etq" for="p-texto" style="display:block;margin:0 4px 6px">${t("Qué toca")}</label>
      <textarea class="campo area grande" id="p-texto" placeholder="5 x 400 m run every 3'"></textarea></div>
    ${alcanceHtml(est.solo)}
    ${msgCoach(v)}
    <button class="btn btn-fuego" id="p-guardar">${v.puede_pesos === false ? t("Enviar a Diego para que lo apruebe") : cambiar ? t("Cambiar") : t("Añadir")}</button>
    <div><div class="paso-etq" style="margin:6px 4px 8px">${t("Ideas")} · <span id="p-tipo-ideas">${esc(est.tipo)}</span></div><div class="ideas" id="p-ideas"></div></div>`, (h) => {
    enlazarAlcance(h, est);
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
      <div class="fila-chips">${Object.entries(tipos).map(([k, n]) => `<button type="button" class="chip ${b.tipo === k ? "on" : ""}" data-tipo="${k}">${esc(n)}</button>`).join("")}</div></div>
    ${b.partes.length ? `<div><div class="lbl">${t("Partes que has hecho")}</div>
      <div class="fila-chips">${b.partes.map((p, i) => `<button type="button" class="chip ${p.on ? "on" : ""}" data-parte="${i}">${p.on ? ic.ok : ""}${esc(p.warmup ? "Warm up" : String(p.texto).split(" · ").map(etqParte).join(" · "))}</button>`).join("")}</div>
      <div class="mini" style="margin-top:6px">${t("Se marcan como hechas al guardar.")}</div></div>` : ""}
    <div><label class="lbl" for="r-titulo">${t("Título")}</label>
      <input class="campo" id="r-titulo" value="${esc(b.titulo)}" placeholder="Fran, Pierna, 10K suave…"></div>
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
            <select class="campo campo-u" data-u aria-label="Unidad">${unidades.map((u) => `<option ${u === f.unit ? "selected" : ""}>${u}</option>`).join("")}</select>
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
  document.body.style.overflow = "";
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

// ---------- arranque ----------
if (E.token) cargar(); else pintarEntrar();
