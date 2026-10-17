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
  if (v.aviso) aviso(v.aviso);
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
  if (v.sin_rutina) {
    $app.innerHTML = cabecera(v) + `<main><div class="vacio"><p><b>${esc(v.nombre)}</b> todavía no tiene rutina.</p>
      <p class="mini">Créala en la app de siempre y aparecerá aquí.</p></div></main>` + nav();
    enlazar(); return;
  }
  const hechas = v.partes.filter((p) => p.estado === "hecho").length;
  const total = v.partes.length;
  $app.innerHTML = cabecera(v) + `
  <main>
    <div class="titulo-dia"><h2>${esc(v.dia.nombre)}</h2><span>${total ? `${hechas} ${t("de")} ${total} ${t("partes hechas")}` : ""}</span></div>
    <div class="barra"><i style="width:${total ? Math.round(hechas / total * 100) : 0}%"></i></div>
    ${v.faltan.length && v.semana < v.actual ? `<div class="alerta"><b>${t("Sin validar")} · S${v.semana}:</b> ${esc(v.faltan.join("; "))}. ${t("Marca cada parte como hecha o pásala a otro día.")}</div>` : ""}
    ${total ? v.partes.map((p, i) => tarjeta(p, "p" + i)).join("") : `<div class="vacio">${t("Sin ejercicios este día.")}</div>`}
    ${v.pendientes.length ? `<div class="seccion">${ic.ciclo} ${t("Pendiente de")}…</div>` + v.pendientes.map((p, i) => tarjeta(p, "q" + i)).join("") : ""}
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
      <button class="redondo" id="b-ajustes" aria-label="${t("Ajustes")}">${ic.ajustes}</button>
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

function tarjeta(p, k) {
  const letra = p.estado === "hecho" ? ic.ok : esc(p.letra || "·");
  const estadoTxt = { hecho: t("Hecho").toLowerCase(), no_hecho: t("No hecho").toLowerCase(), pospuesto: "→ " + (p.destino_txt || "") }[p.estado];
  const titulo = p.lineas.length === 1 && !p.lineas[0].solo_bloque ? p.lineas[0].ejercicio : p.etiqueta;
  const nombreTit = p.origen || titulo;
  const tagTxt = nombreTit === p.etiqueta ? `${t("Parte")} ${p.letra || ""}`.trim() : `${p.letra ? p.letra + " · " : ""}${p.etiqueta}`;
  return `
  <section class="card ${p.estado === "hecho" ? "hecha" : ""}">
    <div class="card-cab">
      <div class="letra ${p.estado}">${letra}</div>
      <div style="flex:1;min-width:0">
        <div class="tag ${p.estado}">${esc(tagTxt)}${estadoTxt ? " · " + esc(estadoTxt) : ""}</div>
        <div class="nombre">${esc(nombreTit)}</div>
      </div>
      ${p.historial.length ? `<div class="hist" title="Semanas anteriores">${p.historial.map(([s, e]) => `<i class="${e}" title="S${s}"></i>`).join("")}</div>` : ""}
    </div>
    ${p.ciclo ? `<div class="mini" style="padding-left:48px">${ic.ciclo.replace("<svg", '<svg style="display:inline;vertical-align:-2px"')} ${t("Ciclo · semana")} ${p.ciclo.semana}/${p.ciclo.total}</div>` : ""}
    <div class="lineas">${p.lineas.map((l, j) => linea(l, p, k + "_" + j)).join("")}</div>
    ${p.no_hechas ? `<div class="nota-estado no_hecho" style="padding-left:48px">${p.no_hechas} sin hacer · repiten peso</div>` : ""}
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
    const pesos = l.pesos.length ? l.pesos.map((w, i) => `<button class="peso" data-peso="${k}" data-i="${i}">@ ${num(w)}<small>kg</small></button>`).join("")
      : `<button class="peso falta" data-peso="${k}" data-i="0">+ ${t("falta el peso")}</button>`;
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

function nav() {
  return `<nav class="nav" aria-label="Secciones">
    <button class="on" aria-current="page">${ic.calendario}${t("Rutina")}</button>
    <button data-pronto="${t("Registrar")}" aria-label="${t("Registrar")}">${ic.mas}</button>
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
  abrirHoja(`${cabHoja(`${p.letra ? p.letra + " · " : ""}${t("Cambiar peso")}`, l.ejercicio)}
    ${valores.map((w, i) => `<div><div class="paso-etq" style="margin:0 4px 6px">${esc(etiqueta(i))}</div>
      <div class="paso"><button data-d="-2.5" data-i="${i}" aria-label="Menos 2,5">−2,5</button>
      <input inputmode="decimal" data-i="${i}" value="${w == null ? "" : num(w)}" placeholder="kg" aria-label="${esc(etiqueta(i))}">
      <button data-d="2.5" data-i="${i}" aria-label="Más 2,5">+2,5</button></div></div>`).join("")}
    <label class="interruptor"><span>${t("Mover igual el mismo ejercicio en los otros días")}</span><input type="checkbox" id="c-prop" checked></label>
    <label class="interruptor"><span>${t("Solo esta semana")}</span><input type="checkbox" id="c-solo"></label>
    <button class="btn btn-fuego" id="b-guardar-peso">${t("Guardar")}</button>`, (h) => {
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
      cerrarHoja();
      await hacer({ tipo: "peso", semana: p.semana, linea: l.id, texto: l.texto, valores: vals,
        propagar: h.querySelector("#c-prop").checked, solo_semana: h.querySelector("#c-solo").checked });
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
    ${v.app_antigua ? `<a class="btn" href="${esc(v.app_antigua)}" target="_blank" rel="noopener">${t("Abrir la app de siempre")}</a>` : ""}
    <button class="btn btn-negro" id="b-salir">${t("Salir")}</button>`, (h) => {
    h.querySelectorAll("[data-nivel]").forEach((b) => b.onclick = () => { cerrarHoja(); hacer({ tipo: "nivel", nivel: b.dataset.nivel }); });
    h.querySelectorAll("[data-lang]").forEach((b) => b.onclick = () => {
      E.lang = b.dataset.lang; mem.set("lang", E.lang); mem.set("lang_elegido", "1"); cerrarHoja(); pintar();
    });
    h.querySelector("#b-salir").onclick = salir;
  });
}

function hojaPronto(nombre) {
  const v = E.vista;
  abrirHoja(`${cabHoja(t("Pronto"), nombre)}
    <p style="margin:0;font-size:15px">${t("Esto llega en la siguiente fase.")}${v.app_antigua ? " " + t("Mientras, está en la app de siempre:") : ""}</p>
    ${v.app_antigua ? `<a class="btn btn-fuego" href="${esc(v.app_antigua)}" target="_blank" rel="noopener">${t("Abrir la app de siempre")}</a>` : ""}`);
}

// ---------- arranque ----------
if (E.token) cargar(); else pintarEntrar();
