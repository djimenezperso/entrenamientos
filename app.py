"""Diario de Entrenos — Streamlit.

Un apartado por persona, con foto, tiempos, notas, progresión y consejos.
Datos en Supabase si hay credenciales en los secrets; si no, en local (SQLite).
"""
from __future__ import annotations

import datetime as dt
import io
import json
from collections import Counter
import random
import re
import sqlite3
import uuid
import zipfile
from urllib.parse import quote
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageOps

from logica import (
    MENOS_ES_MEJOR, TIPOS, UNIDADES, a_fecha, aplicar_edicion, cambio_pct, consejos, es_metcon, fmt_num,
    fmt_tiempo, fmt_valor, ids_con_pr, mejor_punto, norm, parse_tiempo, parse_valor, peso_principal,
    prescripcion_semana, series_ejercicios, sesiones_por_semana,
    PARTES, agrupar_por_parte, destino_dia_siguiente, destino_semana_siguiente, estado_parte, marcar_parte,
    partes_del_dia, pendientes_para, resumen_dia, se_repite, semanas_que_sube, sin_validar,
    NUM_PESO, cambiar_pesos, poner_pesos, linea_no_hecha, marcar_linea, no_hechas_en,
    historial_parte, renombrar_parte, parametros_semana, editar_texto_linea,
    CATEGORIAS_WOD, CLAVE_BIBLIOTECA, coincide_busqueda, wods_hechos,
    CLAVES_BIBLIO, NOMBRE_BIBLIO, anadir_linea, biblioteca, tipo_de_linea,
    detectar_entrenos, emparejar_autor, norm_busqueda, parse_whatsapp, CATEGORIAS_MOVILIDAD,
    TRAMOS_EMOM, carga_maxima, copiar_rutina, duracion_emom, es_emom, rutina_desde_json, tramo_emom,
)
from repertorio import COMPETICION, HEROES, REPERTORIO
from i18n import lang, t
from rutinas_iniciales import migrar, rutinas_iniciales

try:  # fotos HEIC del iPhone
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass

# ===== Cambia aquí los nombres =====
ATLETAS = ["Yo", "Manu Anel", "Salatti", "Mi esposa", "Dario", "Archchana", "Juan"]
IDIOMA_DEFECTO = {"Archchana": "fr"}  # el resto, español
COLORES_ATLETA = ["#16202b", "#d6312b", "#1f5fbf", "#2a8c4a", "#d9a200", "#8e44ad", "#e67e22", "#7f8994"]
# ===================================

st.set_page_config(page_title="Diario de Entrenos", page_icon="🏋️", layout="centered")


# ---------------------------------------------------------------- almacenamiento
class LocalStore:
    """SQLite + carpeta de fotos. Para probar en tu ordenador."""

    def __init__(self, root: Path = Path("data")):
        self.root = root
        (root / "fotos").mkdir(parents=True, exist_ok=True)
        self.db = root / "entrenos.db"
        with sqlite3.connect(self.db) as c:
            c.execute("""create table if not exists workouts(
                id text primary key, athlete text, date text, type text, title text,
                duration_sec integer, entries text, notes text, photo_path text, created_at text)""")
            c.execute("create table if not exists rutinas(athlete text primary key, data text, updated_at text)")

    def rutinas(self) -> dict:
        with sqlite3.connect(self.db) as c:
            return {a: json.loads(d) for a, d in c.execute("select athlete, data from rutinas")}

    def guardar_rutina(self, atleta: str, data: dict):
        with sqlite3.connect(self.db) as c:
            c.execute("insert or replace into rutinas values (?,?,?)",
                      (atleta, json.dumps(data, ensure_ascii=False), dt.datetime.now().isoformat()))

    def listar(self) -> list[dict]:
        with sqlite3.connect(self.db) as c:
            c.row_factory = sqlite3.Row
            filas = c.execute("select * from workouts order by date desc, created_at desc").fetchall()
        out = []
        for f in filas:
            d = dict(f)
            d["entries"] = json.loads(d["entries"] or "[]")
            out.append(d)
        return out

    def guardar(self, w: dict, foto: bytes | None):
        if foto:
            nombre = f"{uuid.uuid4().hex}.jpg"
            (self.root / "fotos" / nombre).write_bytes(foto)
            w["photo_path"] = nombre
        with sqlite3.connect(self.db) as c:
            c.execute("insert into workouts values (?,?,?,?,?,?,?,?,?,?)", (
                w["id"], w["athlete"], w["date"], w["type"], w["title"], w["duration_sec"],
                json.dumps(w["entries"], ensure_ascii=False), w["notes"], w.get("photo_path"), w["created_at"]))

    def borrar(self, w: dict):
        with sqlite3.connect(self.db) as c:
            c.execute("delete from workouts where id=?", (w["id"],))
        if w.get("photo_path"):
            (self.root / "fotos" / w["photo_path"]).unlink(missing_ok=True)

    def foto(self, w: dict):
        p = self.root / "fotos" / w["photo_path"]
        return str(p) if p.exists() else None


class SupabaseStore:
    """Tabla `workouts` + bucket público `fotos` en Supabase."""

    BUCKET = "fotos"

    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.c = create_client(url, key)

    def listar(self) -> list[dict]:
        r = self.c.table("workouts").select("*").order("date", desc=True).order("created_at", desc=True).execute()
        return r.data or []

    def guardar(self, w: dict, foto: bytes | None):
        if foto:
            carpeta = norm(w["athlete"]).replace(" ", "-") or "sin-nombre"
            ruta = f"{carpeta}/{uuid.uuid4().hex}.jpg"
            self.c.storage.from_(self.BUCKET).upload(ruta, foto, {"content-type": "image/jpeg"})
            w["photo_path"] = ruta
        self.c.table("workouts").insert(w).execute()

    def borrar(self, w: dict):
        self.c.table("workouts").delete().eq("id", w["id"]).execute()
        if w.get("photo_path"):
            try:
                self.c.storage.from_(self.BUCKET).remove([w["photo_path"]])
            except Exception:
                pass

    def foto(self, w: dict):
        return self.c.storage.from_(self.BUCKET).get_public_url(w["photo_path"])

    def rutinas(self) -> dict:
        r = self.c.table("rutinas").select("athlete,data").execute()
        return {f["athlete"]: f["data"] for f in (r.data or [])}

    def guardar_rutina(self, atleta: str, data: dict):
        self.c.table("rutinas").upsert({"athlete": atleta, "data": data,
                                        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}).execute()


def secreto(nombre, defecto=None):
    try:
        return st.secrets.get(nombre, defecto)
    except Exception:  # no hay secrets.toml
        return defecto


@st.cache_resource
def store():
    cfg = secreto("supabase")
    if cfg and cfg.get("url") and cfg.get("key"):
        return SupabaseStore(cfg["url"], cfg["key"])
    return LocalStore()


@st.cache_data(ttl=60, show_spinner=False)
def cargar_todo() -> list[dict]:
    return store().listar()


def refrescar():
    cargar_todo.clear()


@st.cache_data(ttl=60, show_spinner=False)
def cargar_rutinas() -> dict:
    return store().rutinas()


def guardar_rutina(atleta: str, data: dict):
    store().guardar_rutina(atleta, data)
    cargar_rutinas.clear()


# ---------------------------------------------------------------- utilidades UI
def preparar_foto(archivo) -> bytes:
    img = Image.open(archivo)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1600, 1600))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82)
    return buf.getvalue()


def etiqueta_tipo(k: str) -> str:
    nombre, _, color = TIPOS.get(k, TIPOS["otro"])
    return f":{color}[●] **{nombre}**"


def fecha_larga(d) -> str:
    dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    d = a_fecha(d)
    return f"{dias[d.weekday()]} {d.day} {meses[d.month - 1]} {d.year}"


def control_contrasena():
    """Contraseña general (todo) o contraseña personal (solo el perfil de esa persona)."""
    clave = secreto("APP_PASSWORD")
    if not clave or st.session_state.get("dentro"):
        return
    st.title("Diario de Entrenos")
    intento = st.text_input("Contraseña / Mot de passe", type="password").strip()  # el móvil a veces añade espacios
    personales = {nombre: str(c).strip() for nombre, c in (secreto("accesos_personales") or {}).items()}
    if intento and intento == str(clave).strip():
        st.session_state.dentro, st.session_state.solo = True, None
        st.rerun()
    elif intento and intento in personales.values():
        nombre = next(n for n, c in personales.items() if c == intento)
        st.session_state.dentro, st.session_state.solo = True, nombre
        st.session_state.lang = IDIOMA_DEFECTO.get(nombre, "es")
        st.rerun()
    elif intento:
        st.error("Contraseña incorrecta. / Mot de passe incorrect.")
    st.stop()


def solo() -> str | None:
    """Si se entró con una contraseña personal, el nombre de esa persona."""
    return st.session_state.get("solo")


def visibles() -> list[str]:
    return [solo()] if solo() else ATLETAS


def eje_tiempo(fig: go.Figure, valores: list[float], eje: str = "yaxis"):
    lo, hi = min(valores), max(valores)
    paso = max(5, round((hi - lo) / 4 / 5) * 5) if hi > lo else 15
    inicio = int(lo // paso * paso)
    ticks = list(range(inicio, int(hi) + paso + 1, paso))
    fig.update_layout(**{eje: dict(tickvals=ticks, ticktext=[fmt_tiempo(t) for t in ticks])})


# ---------------------------------------------------------------- pestañas
def formulario_entreno(atleta: str, entrenos: list[dict], clave: str, inicial: dict | None = None,
                       partes: list[str] | None = None, al_guardar=None):
    """Formulario de entreno. `inicial` = {tipo, titulo, filas:[{Ejercicio, Resultado, Unidad}]}.
    Con `partes`, pregunta qué partes se hicieron y llama a `al_guardar(partes_hechas)` tras guardar."""
    inicial = inicial or {}
    n = st.session_state.setdefault(f"form_n_{clave}", 0)
    usados = sorted({e["name"].strip() for w in entrenos for e in (w.get("entries") or []) if e.get("name")}, key=str.lower)
    filas = inicial.get("filas") or [{"Ejercicio": "", "Resultado": "", "Unidad": "tiempo"} for _ in range(3)]
    tipos = list(TIPOS)

    with st.form(f"form_{clave}_{n}"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox(t("Tipo"), tipos, index=tipos.index(inicial.get("tipo", "fuerza")),
                            format_func=lambda k: TIPOS[k][0])
        fecha = c2.date_input(t("Fecha"), dt.date.today(), format="DD/MM/YYYY")
        c3, c4 = st.columns([2, 1])
        titulo = c3.text_input(t("Título"), value=inicial.get("titulo", ""), placeholder="Fran, Pierna, 10K suave…")
        duracion = c4.text_input(t("Duración total"), placeholder="h:mm:ss o min")

        st.markdown(f"**{t('Resultados')}**")
        tabla = st.data_editor(
            pd.DataFrame(filas, columns=["Ejercicio", "Resultado", "Unidad"]),
            num_rows="dynamic", hide_index=True, use_container_width=True, key=f"tabla_{clave}_{n}",
            column_config={
                "Ejercicio": st.column_config.TextColumn(width="medium"),
                "Resultado": st.column_config.TextColumn(help="Tiempo como 4:35 o 1:02:10; el resto, un número"),
                "Unidad": st.column_config.SelectboxColumn(options=UNIDADES, required=True),
            },
        )
        st.caption("Tiempo como 4:35 o 1:02:10. Escribe cada ejercicio siempre igual para seguir su progresión."
                   + (f" Ya usados: {', '.join(usados[:12])}." if usados and not inicial else ""))
        notas = st.text_area(t("Notas"), placeholder="Sensaciones, escalado, qué falló…")
        hechas = st.multiselect(t("Partes que has hecho (se validan al guardar)"), partes, default=partes) if partes else []
        foto = st.file_uploader(t("Foto"), type=["jpg", "jpeg", "png", "webp", "heic", "heif"])
        enviado = st.form_submit_button(t("Guardar entreno"), type="primary", use_container_width=True)

    if not enviado:
        return

    errores, resultados = [], []
    dur = None
    if duracion.strip():
        dur = parse_tiempo(duracion)
        if dur is None:
            errores.append("La duración no se entiende. Usa h:mm:ss, mm:ss o minutos.")
    for _, fila in tabla.iterrows():
        nombre = str(fila.get("Ejercicio") or "").strip()
        bruto = str(fila.get("Resultado") or "").strip()
        unidad = fila.get("Unidad") or "tiempo"
        if not nombre and not bruto:
            continue
        valor = parse_valor(bruto, unidad) if bruto else None
        if bruto and valor is None:
            errores.append(f"Revisa el resultado de «{nombre or bruto}»: los tiempos van como 4:35 y el resto como número.")
        resultados.append({"name": nombre or "Sin nombre", "value": valor, "unit": unidad})
    if errores:
        for e in errores:
            st.error(e)
        st.info("No se ha guardado nada. Corrige y vuelve a pulsar Guardar.")
        return

    w = {
        "id": str(uuid.uuid4()), "athlete": atleta, "date": fecha.isoformat(), "type": tipo,
        "title": titulo.strip(), "duration_sec": dur, "entries": resultados, "notes": notas.strip(),
        "photo_path": None, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    try:
        with st.spinner("Guardando…"):
            store().guardar(w, preparar_foto(foto) if foto else None)
    except Exception as ex:
        st.error(f"No se pudo guardar: {ex}")
        return
    refrescar()
    if al_guardar and hechas:
        al_guardar(hechas)
    st.session_state[f"form_n_{clave}"] = n + 1
    st.session_state["aviso"] = "Entreno guardado"
    st.rerun()


def tab_registrar(atleta: str, entrenos: list[dict]):
    formulario_entreno(atleta, entrenos, f"libre_{atleta}")


SQL_RUTINAS = """create table if not exists public.rutinas (
  athlete    text primary key,
  data       jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.rutinas enable row level security;"""


def _nuevo_id() -> str:
    return uuid.uuid4().hex[:8]


def _titulo_dia(semana: int, dia: dict) -> str:
    return f"Semana {semana} · {dia['nombre']}"


def _inicial_desde_dia(rut: dict, dia: dict, semana: int, lineas: list[dict] | None = None, titulo: str = "") -> dict:
    filas, fuerza = [], False
    for l in (dia["lineas"] if lineas is None else lineas):
        txt, _, _ = prescripcion_semana(l, semana, rut.get("ajustes"))
        if es_metcon(l["ejercicio"]):
            filas.append({"Ejercicio": l["ejercicio"], "Resultado": "", "Unidad": "tiempo"})
        else:
            fuerza = True
            p = peso_principal(txt)
            filas.append({"Ejercicio": l["ejercicio"], "Resultado": fmt_num(p) if p is not None else "", "Unidad": "kg"})
    return {"tipo": "fuerza" if fuerza else "wod", "titulo": titulo or _titulo_dia(semana, dia), "filas": filas}


def _cambiar_semana(atleta: str, rut: dict, nueva: int):
    rut = dict(rut, semana_actual=nueva)
    guardar_rutina(atleta, rut)
    st.session_state[f"sem_{atleta}"] = nueva


CHIP_DIA = {"hecho": ":green[✓ hecho]", "no_hecho": ":red[✗ no hecho]", "parcial": ":orange[◐ a medias]",
            "pospuesto": ":orange[↷ pasado]", "pendiente": ":gray[○ sin validar]"}  # se traducen con t()


def _chip_parte(est: dict, semana: int, dias: dict) -> str:
    if est["estado"] == "hecho":
        return ":green[✓]"
    if est["estado"] == "no_hecho":
        return t(":red[✗ no hecho · la semana que viene se repite]")
    if est["estado"] == "pospuesto":
        s_, did = est["destino"]
        nombre = dias.get(did, {}).get("nombre", "otro día")
        return f":orange[↷ {nombre}" + (f", semana {s_}]" if s_ != semana else "]")
    return ""


PREFIJO_CARGA = re.compile(r"(\S*?)\s*@\s*\d+(?:[.,]\d+)?")


def _etiqueta_extra(l: dict, txt: str, semana: int, ajuste: bool, subio: bool) -> str:
    if ajuste:
        return " :orange[(solo esta semana)]"
    if txt and se_repite(l, semana):
        return " :gray[(se repite)]"
    p = parametros_semana(l, semana)
    if subio and semanas_que_sube(p, semana) > 0:
        return f" :green[+{fmt_num(semanas_que_sube(p, semana) * float(p['sube']))}]"
    return ""


# ---------------------------------------------------------------- IA (opcional)
def ia_disponible() -> bool:
    return bool(secreto("ANTHROPIC_API_KEY"))


@st.cache_resource
def _cliente_ia():
    import anthropic
    return anthropic.Anthropic(api_key=secreto("ANTHROPIC_API_KEY"))


QUE_ES = {"wod": "WOD de CrossFit", "conditioning": "sesión de conditioning (motor, cardio, intervalos)",
          "mobility": "bloque de movilidad o estiramientos con su duración o repeticiones",
          "accessory": "ejercicio accesorio de fuerza con sus series y repeticiones"}


def inventar_con_ia(tipo: str, ejemplos: list[tuple[str, str]], idea: str, duracion: str, estilo: str) -> tuple[str, str]:
    lista = "\n".join(f"- {n}: {t}" if n else f"- {t}" for n, t in ejemplos[:25]) or "(todavía no hay ejemplos)"
    prompt = (
        f"Inventa un {QUE_ES[tipo]} nuevo y original para un grupo de amigos que entrena CrossFit.\n"
        f"Inspírate en el estilo, el volumen y los movimientos de estos (no los copies):\n{lista}\n\n"
        f"Duración: {duracion}. Estilo: {estilo}.\n"
        + ("Escribe en francés.\n" if lang() == "fr" else "")
        + (f"Lo que pide el atleta: {idea}\n" if idea else "")
        + "Usa pesos RX hombre/mujer en kg cuando haya carga. Escribe en español, con los nombres de los movimientos "
          "en inglés como en los ejemplos, y en una o dos líneas.\n"
          'Responde SOLO con JSON: {"nombre": "...", "texto": "..."}. '
          'En accessories, "nombre" es el ejercicio y "texto" las series, por ejemplo "3x10 @40".'
    )
    msg = _cliente_ia().messages.create(model=secreto("ANTHROPIC_MODEL", "claude-sonnet-5-5"), max_tokens=500,
                                        messages=[{"role": "user", "content": prompt}])
    texto = "".join(getattr(b, "text", "") for b in msg.content)
    m = re.search(r"\{.*\}", texto, re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        data = {}
    return str(data.get("nombre", "")).strip(), str(data.get("texto", texto)).strip()


def _ia_panel(tipo: str, k: str):
    """Pide a la IA uno nuevo al estilo de lo hecho. Devuelve (nombre, texto) o None."""
    if not ia_disponible():
        st.caption("La IA no está activada. Añade ANTHROPIC_API_KEY en los Secrets de Streamlit (lo explica el README).")
        return None
    idea = st.text_input(t("Idea (opcional)"), key=f"ii_{k}", placeholder="thrusters y pull ups, algo corto e intenso…")
    c1, c2, c3 = st.columns(3)
    dur = c1.selectbox(t("Duración"), ["Corto (menos de 10')", "Medio (10-20')", "Largo (más de 20')"], index=1,
                       key=f"id_{k}")
    estilos = ["Como los nuestros", "Competición (tipo Open)", "Hero WOD"] if tipo == "wod" else ["Como los nuestros"]
    estilo = c2.selectbox(t("Estilo"), estilos, key=f"ie_{k}")
    persona = c3.selectbox(t("Al estilo de"), (["Todos"] if not solo() else []) + visibles(), key=f"ip_{k}",
                           format_func=t)
    hay_coach = bool(_datos_coach())
    con_coach = st.checkbox("Inspirarse también en el coach", value=hay_coach, key=f"ic_{k}") if hay_coach else False
    if st.button(t("✨ Inventar uno") if not st.session_state.get(f"ir_{k}") else t("✨ Otro"), key=f"ib_{k}"):
        grupos = _bib(tipo)
        if persona != "Todos":
            grupos = [g for g in grupos if any(v["atleta"] == persona for v in g["veces"])] or grupos
            estilo += f" (el de {persona})"
        ejemplos = [(g["titulo"], g["texto"]) for g in grupos]
        if con_coach:
            del_coach = [i for i in _datos_coach()["items"] if i["tipo"] in COACH_PARA_LINEA.get(tipo, [tipo])]
            ejemplos = random.sample([(i["nombre"], i["texto"][:400]) for i in del_coach], min(12, len(del_coach))) + ejemplos
            estilo += " (más exigente, como un coach de competición)"
        if estilo.startswith("Competición") or estilo == "Hero WOD":
            ejemplos = COMPETICION + ejemplos
        elif len(ejemplos) < 5:
            ejemplos += REPERTORIO[tipo]
        with st.spinner("Pensando…"):
            try:
                st.session_state[f"ir_{k}"] = inventar_con_ia(tipo, ejemplos, idea, dur, estilo)
            except Exception as ex:
                st.error(f"La IA no ha podido responder: {ex}")
    res = st.session_state.get(f"ir_{k}")
    if res:
        st.markdown(f"**{res[0] or 'Propuesta'}** · {res[1]}")
    return res


_BIB_RUN: dict = {}


def _bib(tipo: str) -> list[dict]:
    """Lo ya hecho de un tipo (todos los atletas), calculado una vez por pantalla."""
    if tipo not in _BIB_RUN:
        try:
            guardadas = cargar_rutinas()
        except Exception:
            guardadas = {}
        rutinas = {a: _completar_partes(guardadas.get(a) or rutinas_iniciales(ATLETAS).get(a), a) for a in ATLETAS}
        try:
            entrenos = cargar_todo()
        except Exception:
            entrenos = []
        grupos = biblioteca(rutinas, ATLETAS, entrenos, guardadas.get(CLAVE_BIBLIOTECA), tipo)
        if solo():
            for g in grupos:
                g["veces"] = [v for v in g["veces"] if v["atleta"] == solo()]
            grupos = [g for g in grupos if g["veces"]]
        _BIB_RUN[tipo] = grupos
    return _BIB_RUN[tipo]


def _titulo_grupo(g: dict) -> str:
    if g["titulo"] and g["texto"] and norm(g["texto"]) != norm(g["titulo"]):
        return f"{g['titulo']} · {g['texto'].splitlines()[0]}"
    return g["titulo"] or g["texto"].splitlines()[0]


def _elegir_contenido(tipo: str, k: str, atleta: str | None = None):
    """✍️ Nuevo / 📚 Ya hechos / 💡 Repertorio / ✨ IA / 🔒 Coach. Devuelve (modo, (nombre, texto) | None)."""
    con_coach = coach_abierto() and atleta in ACCESO_COACH and bool(_datos_coach())
    modos = ["✍️ Nuevo", "📚 Ya hechos", "💡 Repertorio", "✨ IA"] + (["🔒 Coach"] if con_coach else [])
    modo = st.segmented_control("Origen", modos, default="✍️ Nuevo",
                                key=f"om_{k}", label_visibility="collapsed", format_func=t) or "✍️ Nuevo"
    if modo == "🔒 Coach" and con_coach:
        tipos = COACH_PARA_LINEA.get(tipo, [tipo])
        q = st.text_input(t("Buscar por movimiento"), key=f"cq_{k}", placeholder="snatch, MU, bike…")
        ops = [i for i in _datos_coach()["items"] if i["tipo"] in tipos
               and (not q or coincide_busqueda(i["nombre"] + "\n" + i["texto"], q))][::-1]
        if not ops:
            st.caption("Nada del coach con eso.")
            return modo, None
        i = st.selectbox(t("Elige"), range(len(ops)), key=f"cs_{k}",
                         format_func=lambda i: f"{ops[i]['fecha'][:10]} · {ops[i]['nombre']}"[:80])
        it = ops[min(i, len(ops) - 1)]
        st.caption(it["texto"].replace("\n", "  \n"))
        return modo, ("", it["texto"])
    if modo == "✨ IA":
        return modo, _ia_panel(tipo, k)
    if modo == "📚 Ya hechos":
        q = st.text_input(t("Buscar por movimiento"), key=f"oq_{k}", placeholder="thruster, row, pull up…")
        ops = [g for g in _bib(tipo) if any(v["estado"] == "hecho" for v in g["veces"])
               and (not q or coincide_busqueda(g["titulo"] + "\n" + g["texto"], q))]
        if not ops:
            st.caption("Todavía no hay nada de este tipo hecho por ninguno. Prueba el repertorio.")
            return modo, None
        i = st.selectbox(t("Elige"), range(len(ops)), key=f"os_{k}",
                         format_func=lambda i: f"{_titulo_grupo(ops[i])[:70]} ({len(ops[i]['veces'])}x)")
        g = ops[min(i, len(ops) - 1)]
        st.caption(g["texto"].replace("\n", "  \n") + "  \n" +
                   "Hecho por: " + ", ".join(sorted({v['atleta'] for v in g['veces'] if v['atleta']})))
        return modo, (g["titulo"], g["texto"])
    if modo == "💡 Repertorio":
        q = st.text_input(t("Buscar por movimiento"), key=f"rq_{k}", placeholder="thruster, row, pull up…")
        ops = [x for x in REPERTORIO[tipo] if not q or coincide_busqueda(x[0] + "\n" + x[1], q)]
        if not ops:
            st.caption("Nada en el repertorio con eso.")
            return modo, None
        clave = f"rs_{k}"
        if st.button(t("🎲 Al azar"), key=f"rz_{k}"):
            st.session_state[clave] = random.randrange(len(ops))
        if st.session_state.get(clave, 0) >= len(ops):
            st.session_state[clave] = 0
        i = st.selectbox(t("Elige"), range(len(ops)), key=clave, format_func=lambda i: f"{ops[i][0]} · {ops[i][1]}"[:80])
        st.caption(f"**{ops[i][0]}** · {ops[i][1]}")
        return modo, ops[i]
    return modo, None


def _contenido_elegido(tipo: str, l: dict, sel: tuple) -> tuple[str, str]:
    """(ejercicio, prescripción) a guardar en la línea a partir de lo elegido."""
    titulo, texto = sel
    if tipo in ("accessory", "mobility"):
        return (titulo or l["ejercicio"]), texto
    if not titulo or norm(texto).startswith(norm(titulo)):
        return l["ejercicio"], texto
    return l["ejercicio"], f"{titulo}: {texto}"


def _linea_texto_editable(atleta: str, rut: dict, l: dict, txt: str, semana: int, metcon: bool, nombre: str,
                          extra: str, tipo: str = "wod"):
    """WOD, conditioning o accessory: se ve el texto y al tocarlo se edita o se elige de lo hecho / el repertorio."""
    resumen = (txt or t("por definir")).replace("\n", " / ")
    if len(resumen) > 80:
        resumen = resumen[:77] + "…"
    k = f"{atleta}_{semana}_{l['id']}"
    with st.popover(f"{nombre}{resumen} ✏️", use_container_width=True):
        modo, sel = _elegir_contenido(tipo, k, atleta)
        if modo == "✍️ Nuevo":
            nuevo_nombre = st.text_input(t("Nombre"), l["ejercicio"], key=f"tn_{k}")
            nuevo_txt = st.text_area(t("Qué toca"), txt, height=120, key=f"tt_{k}",
                                     placeholder="AMRAP 12': 10 thrusters @40 + 5 burpees")
            nueva_nota = st.text_input(t("Nota"), l.get("nota", ""), key=f"to_{k}")
        alcance = st.radio(t("Aplicar a"), ["Solo esta semana", "Esta semana y las siguientes"], format_func=t,
                           index=0 if metcon else 1, key=f"ta_{k}", horizontal=True)
        if st.button(t("Guardar") if modo == "✍️ Nuevo" else t("Usar este"), type="primary", key=f"tg_{k}",
                     disabled=(modo != "✍️ Nuevo" and sel is None)):
            rut_act = _rutina_actual(atleta)
            if modo == "✍️ Nuevo":
                nueva = editar_texto_linea(rut_act, l["id"], semana, nuevo_nombre, nuevo_txt, nueva_nota,
                                           alcance == "Solo esta semana")
            else:
                ejercicio, presc = _contenido_elegido(tipo, l, sel)
                nueva = editar_texto_linea(rut_act, l["id"], semana, ejercicio, presc, l.get("nota", ""),
                                           alcance == "Solo esta semana")
            guardar_rutina(atleta, nueva)
            st.session_state["aviso"] = "Guardado"
            st.rerun()
    if "\n" in (txt or ""):
        st.caption(txt.replace("\n", "  \n"))
    if extra.strip():
        st.caption(extra.strip())


def _anadir_a_parte(atleta: str, dia: dict, parte: str, semana: int, tipo: str = "accessory"):
    """Botón para añadir un accessory o movilidad (nuevo, ya hecho o del repertorio) a esta parte, desde esta semana."""
    k = f"add_{atleta}_{semana}_{dia['id']}_{parte}"
    with st.popover(t("+ Añadir movilidad") if tipo == "mobility" else t("+ Añadir accessory")):
        modo, sel = _elegir_contenido(tipo, k, atleta)
        if modo == "✍️ Nuevo":
            nombre = st.text_input(t("Ejercicio"), key=f"an_{k}",
                                   placeholder="Couch stretch" if tipo == "mobility" else "Romanian deadlift")
            texto = st.text_input(t("Series y peso"), key=f"at_{k}",
                                  placeholder="2x90\" por lado" if tipo == "mobility" else "3x10 @60")
            sel = (nombre, texto) if nombre.strip() else None
        if st.button(t("Añadir"), type="primary", key=f"ag_{k}", disabled=sel is None):
            nombre, texto = sel
            nombre = nombre or texto.split("\n")[0][:40]
            guardar_rutina(atleta, anadir_linea(_rutina_actual(atleta), dia["id"], parte, nombre, texto, semana))
            st.session_state["aviso"] = f"{nombre} añadido desde la semana {semana}"
            st.rerun()


def _cambiar_peso(atleta: str, semana: int, lid: str, txt: str, claves: list[str]):
    """Callback al tocar un peso: guarda desde esta semana (o solo esta) y mueve el mismo ejercicio si toca."""
    vals = [st.session_state.get(k) for k in claves]
    if any(v is None for v in vals):
        return
    rut = _rutina_actual(atleta)
    solo_semana = st.session_state.get(f"solo_sem_{atleta}", False)
    propagar = st.session_state.get(f"propagar_{atleta}", True)
    nueva, tocados = cambiar_pesos(rut, semana, {lid: poner_pesos(txt, [float(v) for v in vals])}, solo_semana, propagar)
    guardar_rutina(atleta, nueva)
    st.session_state["aviso"] = "Peso guardado" + (f" (también en {', '.join(tocados)})" if tocados else "")


def _lineas(rut: dict, lineas: list[dict], semana: int, parte: str, atleta: str | None = None,
            por_ejercicio: bool = False):
    """Muestra las líneas de una parte. Con `atleta`, los pesos son casillas que se pueden tocar y cambiar."""
    texto = []

    def volcar():
        if texto:
            st.markdown("\n".join(texto))
            texto.clear()

    for l in lineas:
        if semana < int(l.get("desde") or 0):
            continue
        txt, subio, ajuste = prescripcion_semana(l, semana, rut.get("ajustes"))
        metcon = es_metcon(l["ejercicio"])
        extra = _etiqueta_extra(l, txt, semana, ajuste, subio)
        nota = f" — _{l['nota']}_" if l.get("nota") else ""
        if atleta and tipo_de_linea(parte, l["ejercicio"]) is None:
            volcar()
            cargas = PREFIJO_CARGA.findall(txt)
            pesos = [float(x.replace(",", ".")) for x in NUM_PESO.findall(txt)]
            esquema = NUM_PESO.sub("", txt).replace("  ", " ").strip(" -")
            k = f"w_{atleta}_{semana}_{l['id']}_{txt}"
            if len(pesos) <= 1:
                etiqueta = f"**{l['ejercicio']}**" + (f" · {esquema}" if esquema else "") + extra + nota
                st.number_input(etiqueta, min_value=0.0, step=1.25, format="%.2f",
                                value=pesos[0] if pesos else None, placeholder=t("falta el peso · toca para ponerlo"),
                                key=k, on_change=_cambiar_peso, args=(atleta, semana, l["id"], txt, [k]))
            else:
                st.markdown(f"**{l['ejercicio']}**{extra}{nota}")
                claves = [f"{k}_{i}" for i in range(len(pesos))]
                cols = st.columns(len(pesos))
                for i, p in enumerate(pesos):
                    pref = cargas[i] if i < len(cargas) and cargas[i] else f"Carga {i + 1}"
                    cols[i].number_input(f"{pref} reps" if pref.isdigit() else pref, min_value=0.0, step=1.25,
                                         format="%.2f", value=p, key=claves[i], on_change=_cambiar_peso,
                                         args=(atleta, semana, l["id"], txt, claves))
            if por_ejercicio:
                kc = f"nh_{atleta}_{semana}_{l['id']}_{linea_no_hecha(l, semana)}"
                st.checkbox(t("✗ No lo hice (repite peso la semana que viene)"), value=linea_no_hecha(l, semana),
                            key=kc, on_change=_marcar_linea_cb, args=(atleta, semana, l["id"], kc))
            continue
        solo_bloque = metcon and norm(l["ejercicio"]) in norm(parte)  # «B) WOD» + línea «WOD»
        nombre = "" if solo_bloque else f"**{l['ejercicio']}** · "
        if atleta:
            volcar()
            _linea_texto_editable(atleta, rut, l, txt, semana, metcon, nombre, extra + nota,
                                  tipo_de_linea(parte, l["ejercicio"]) or "wod")
            continue
        if txt:
            linea = f"- {nombre}`{txt}`"
        elif metcon:
            linea = f"- {nombre}:gray[{t('por definir')}]"
        else:
            linea = f"- {nombre}:orange[falta el peso]"
        texto.append(linea + extra + nota)
    volcar()
    if not lineas:
        st.caption("Sin ejercicios.")


def _marcar_linea_cb(atleta: str, semana: int, lid: str, clave: str):
    guardar_rutina(atleta, marcar_linea(_rutina_actual(atleta), lid, semana, bool(st.session_state.get(clave))))


def _guardar_marca(atleta: str, semana: int, dia_id: str, parte: str, clave: str, opciones: dict):
    """Callback del selector de estado de una parte."""
    elegido = st.session_state.get(clave)
    rut = _rutina_actual(atleta)
    if elegido is None:
        nueva = marcar_parte(rut, semana, dia_id, parte, None)
    else:
        estado, destino = opciones[elegido]
        nueva = marcar_parte(rut, semana, dia_id, parte, estado, destino)
    guardar_rutina(atleta, nueva)


def _etiqueta_semana_sig(rut: dict, dia: dict, sem_aqui: int) -> str:
    destino = dia.get("pasa_a")
    if destino and destino != dia["id"]:
        nombre = next((d["nombre"] for d in rut["dias"] if d["id"] == destino), "otro día")
        return f"→ {nombre} (sem. {sem_aqui + 1})"
    return t("→ Semana {n}", n=sem_aqui + 1)


SIMBOLO = {"hecho": ":green[✓]", "no_hecho": ":red[✗]", "pospuesto": ":orange[↷]", "pendiente": ":gray[·]"}


def _historial_txt(rut: dict, dia: dict, parte: str, semana: int) -> str:
    """Semanas anteriores de esta parte: S1 ✓ · S2 ✗ · S3 ↷."""
    previas = historial_parte(rut, dia["id"], parte, semana - 1)
    if not previas:
        return ""
    return f":gray[{t('Historial:')}] " + " ".join(f":gray[S{s}]{SIMBOLO[e]}" for s, e in previas)


def _cabecera_parte(atleta: str, rut: dict, dia: dict, parte: str, semana: int):
    """El nombre de la parte; al tocarlo se puede cambiar la letra y el nombre."""
    k = f"{atleta}_{dia['id']}_{semana}_{parte}"
    with st.popover(f"**{parte}** ✏️"):
        opciones = list(dict.fromkeys([parte] + PARTES))
        elegida = st.selectbox("Parte", opciones, key=f"ps_{k}")
        libre = st.text_input("…o escribe otra", placeholder="C) Gymnastics", key=f"pl_{k}")
        if st.button("Guardar", key=f"pg_{k}", type="primary"):
            nueva = libre.strip() or elegida
            if nueva != parte:
                guardar_rutina(atleta, renombrar_parte(_rutina_actual(atleta), dia["id"], parte, nueva))
                st.session_state["aviso"] = f"Parte cambiada a {nueva}"
            st.rerun()


def _selector_parte(atleta: str, rut: dict, semana: int, dia: dict, parte: str, desde: tuple[int, str] | None = None):
    """✓ Hecho / → día siguiente / → semana que viene, para una parte. `desde` = dónde se muestra si es un pendiente."""
    sem_aqui, dia_aqui = desde or (semana, dia["id"])
    sig = destino_dia_siguiente(rut, sem_aqui, dia_aqui)
    nombre_sig = next(d["nombre"] for d in rut["dias"] if d["id"] == sig[1])
    opciones = {
        t("✓ Hecho"): ("hecho", None),
        t("✗ No hecho"): ("no_hecho", None),
        f"→ {nombre_sig}" + (f" (sem. {sig[0]})" if sig[0] != sem_aqui else ""): ("pospuesto", sig),
        _etiqueta_semana_sig(rut, dia, sem_aqui): ("pospuesto", destino_semana_siguiente(sem_aqui, dia.get("pasa_a") or dia["id"])),
    }
    est = estado_parte(rut, semana, dia["id"], parte)
    actual = None
    for etiqueta, (e, dest) in opciones.items():
        if e == est["estado"] and (dest is None or list(dest) == list(est.get("destino") or [])):
            actual = etiqueta
    marca = est["estado"] + str(est.get("destino") or "")
    clave = f"seg_{atleta}_{semana}_{dia['id']}_{parte}_{sem_aqui}_{dia_aqui}_{marca}"
    st.segmented_control("Estado", list(opciones), default=actual, key=clave, label_visibility="collapsed",
                         on_change=_guardar_marca, args=(atleta, semana, dia["id"], parte, clave, opciones))


def _rutina_actual(atleta: str) -> dict:
    return _completar_partes(cargar_rutinas().get(atleta) or rutinas_iniciales(ATLETAS).get(atleta), atleta)


def _completar_partes(rut: dict | None, atleta: str) -> dict | None:
    """Rutinas guardadas antes de existir las partes: las toma de la rutina inicial o las deduce."""
    if not rut:
        return rut
    rut = migrar(rut, atleta, ATLETAS)
    semilla = {l["id"]: l.get("parte") for d in (rutinas_iniciales(ATLETAS).get(atleta) or {}).get("dias", [])
               for l in d["lineas"]}
    for d in rut["dias"]:
        for l in d["lineas"]:
            if not l.get("parte") and semilla.get(l["id"]):
                l["parte"] = semilla[l["id"]]
        for l, p in zip(d["lineas"], partes_del_dia(d)):
            l.setdefault("parte", p)
    return rut


def _marcar_hechas(atleta: str, semana: int, dia_id: str):
    def f(partes_hechas: list[str]):
        rut = _rutina_actual(atleta)
        for p in partes_hechas:
            rut = marcar_parte(rut, semana, dia_id, p, "hecho")
        guardar_rutina(atleta, rut)
    return f


def tab_rutina(atleta: str, entrenos: list[dict]):
    _BIB_RUN.clear()
    try:
        guardadas = cargar_rutinas()
    except Exception as ex:
        if "rutinas" in str(ex) and ("relation" in str(ex) or "PGRST205" in str(ex) or "does not exist" in str(ex)):
            st.warning("Falta crear la tabla de rutinas en Supabase. Ve a **SQL Editor**, pega esto y pulsa **Run**; "
                       "luego recarga la página.")
            st.code(SQL_RUTINAS, language="sql")
        else:
            st.warning("No se pudo cargar la rutina. Reinicia la app (⋮ → Reboot app) y recarga la página.")
        st.caption(f"Detalle: {ex}")
        return

    rut = _completar_partes(guardadas.get(atleta) or rutinas_iniciales(ATLETAS).get(atleta), atleta)
    if not rut:
        crear_rutina(atleta, guardadas)
        return

    actual = int(rut.get("semana_actual") or 1)
    clave_sem = f"sem_{atleta}"
    if clave_sem not in st.session_state:
        st.session_state[clave_sem] = actual
    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    semana = int(c1.number_input(t("Semana"), min_value=1, step=1, key=clave_sem))
    if semana == actual:
        c2.button(t("Terminé la semana {a} → pasar a la {b}", a=actual, b=actual + 1), key=f"sig_{atleta}",
                  on_click=_cambiar_semana, args=(atleta, rut, actual + 1), use_container_width=True)
    else:
        c2.button(t("Marcar la semana {s} como la actual", s=semana), key=f"act_{atleta}",
                  on_click=_cambiar_semana, args=(atleta, rut, semana), use_container_width=True)
    momento = t("esta semana") if semana == actual else (t("semana pasada") if semana < actual else t("semana que viene"))
    st.caption(t("Semana {s} ({m}). Los pesos tras @ suben lo indicado en «Sube» cada semana (2,5 kg por defecto).",
                 s=semana, m=momento))

    st.caption(t("Toca un peso para cambiarlo: se guarda solo y las semanas siguientes se recalculan. ")
               + t("Los WOD, conditionings y accessories se editan tocándolos. ")
               + t("En las pestañas: ✓ hecho · ◐ a medias · ↷ pasado · ✗ no hecho · • tiene pendientes."))
    with st.expander(t("Opciones al cambiar un peso")):
        st.toggle(t("Mover igual el mismo ejercicio en los otros días"), value=True, key=f"propagar_{atleta}")
        st.toggle(t("Cambiar solo esta semana (excepción)"), value=False, key=f"solo_sem_{atleta}")

    faltan = sin_validar(rut, semana)
    if semana <= actual and faltan:
        st.warning(t("Sin validar en la semana {s}: {f}. Marca cada parte como hecha o pásala a otro día.",
                     s=semana, f="; ".join(faltan)))

    dias = {d["id"]: d for d in rut["dias"]}
    icono = {"hecho": " ✓", "parcial": " ◐", "pospuesto": " ↷", "no_hecho": " ✗", "pendiente": ""}
    etiquetas = []
    for d in rut["dias"]:
        pend = " •" if pendientes_para(rut, semana, d["id"]) else ""
        etiquetas.append(f"{d['nombre']}{icono[resumen_dia(rut, semana, d)]}{pend}")
    for pestana, dia in zip(st.tabs(etiquetas), rut["dias"]):
        with pestana:
            st.markdown(f"#### {dia['nombre']}  {t(CHIP_DIA[resumen_dia(rut, semana, dia)])}")
            grupos = agrupar_por_parte(dia)
            if not grupos:
                st.caption("Sin ejercicios. Añádelos en Editar.")
            for parte, lineas in grupos:
                est = estado_parte(rut, semana, dia["id"], parte)
                n_no = no_hechas_en(lineas, semana) if est["estado"] != "no_hecho" else 0
                aviso_no = f" :red[({n_no} sin hacer)]" if n_no else ""
                _cabecera_parte(atleta, rut, dia, parte, semana)
                estado_txt = f"{_chip_parte(est, semana, dias)}{aviso_no}".strip()
                st.markdown(f"{estado_txt}  {_historial_txt(rut, dia, parte, semana)}".strip())
                _lineas(rut, lineas, semana, parte, atleta, bool(dia.get("por_ejercicio")))
                if tipo_de_linea(parte, "") in ("accessory", "mobility"):
                    _anadir_a_parte(atleta, dia, parte, semana, tipo_de_linea(parte, ""))
                _selector_parte(atleta, rut, semana, dia, parte)
            if grupos:
                with st.expander(t("Registrar resultados")):
                    formulario_entreno(atleta, entrenos, f"rut_{atleta}_{dia['id']}_{semana}",
                                       _inicial_desde_dia(rut, dia, semana), partes=[p for p, _ in grupos],
                                       al_guardar=_marcar_hechas(atleta, semana, dia["id"]))

            for so, did, parte in pendientes_para(rut, semana, dia["id"]):
                origen = dias[did]
                lineas = next((ls for p, ls in agrupar_por_parte(origen) if p == parte), [])
                st.divider()
                st.markdown(f"**:orange[↷ Pendiente · {origen['nombre']} (semana {so}) · {parte}]**")
                _lineas(rut, lineas, so, parte, atleta)
                _selector_parte(atleta, rut, so, origen, parte, desde=(semana, dia["id"]))
                with st.expander("Registrar resultados del pendiente"):
                    formulario_entreno(atleta, entrenos, f"rutp_{atleta}_{did}_{so}_{parte}",
                                       _inicial_desde_dia(rut, origen, so, lineas,
                                                          f"{_titulo_dia(so, origen)} · {parte}"),
                                       partes=[parte], al_guardar=_marcar_hechas(atleta, so, did))

            with st.expander(t("Editar ejercicios")):
                editar_dia(atleta, rut, dia, semana)

    if st.button(t("+ Añadir día"), key=f"add_dia_{atleta}"):
        rut2 = dict(rut, dias=rut["dias"] + [{"id": _nuevo_id(), "nombre": f"Día {len(rut['dias']) + 1}", "lineas": []}])
        guardar_rutina(atleta, rut2)
        st.rerun()


def inventar_rutina_con_ia(atleta: str, dias: int, enfoque: str, con_coach: bool) -> dict:
    ejemplos = []
    for tipo in ("wod", "conditioning", "accessory", "mobility"):
        for g in _bib(tipo):
            if any(v["atleta"] == atleta for v in g["veces"]):
                ejemplos.append(f"[{tipo}] {g['titulo']}: {g['texto'][:300]}")
    if con_coach and _datos_coach():
        muestra = random.sample(_datos_coach()["items"], min(15, len(_datos_coach()["items"])))
        ejemplos += [f"[coach · {i['tipo']}] {i['texto'][:300]}" for i in muestra]
    prompt = (
        f"Diseña una semana de entrenamiento de CrossFit de {dias} días para {atleta}.\n"
        + (f"Lo que ha hecho hasta ahora (copia su estilo, nivel y movimientos):\n" + "\n".join(ejemplos[:40]) + "\n"
           if ejemplos else "No hay historial: haz algo equilibrado para nivel intermedio.\n")
        + (f"Lo que pide: {enfoque}\n" if enfoque else "")
        + ("Escribe los textos en francés.\n" if lang() == "fr" else "")
        + "Cada día tiene partes: A) Fuerza o Halterofilia (con pesos tras @ en kg, p. ej. «5x5 @60»), B) WOD y, si encaja, "
          "C) Conditioning, Accessory o Movilidad.\n"
          'Responde SOLO con JSON: {"dias": [{"nombre": "Día 1", "lineas": [{"parte": "A) Fuerza", "ejercicio": '
          '"Back squat", "prescripcion": "5x5 @60"}, {"parte": "B) WOD", "ejercicio": "WOD", "prescripcion": '
          '"AMRAP 12\': …"}]}]}'
    )
    msg = _cliente_ia().messages.create(model=secreto("ANTHROPIC_MODEL", "claude-sonnet-5-5"), max_tokens=3000,
                                        messages=[{"role": "user", "content": prompt}])
    texto = "".join(getattr(b, "text", "") for b in msg.content)
    m = re.search(r"\{.*\}", texto, re.S)
    return rutina_desde_json(json.loads(m.group(0)) if m else {}, _nuevo_id)


def crear_rutina(atleta: str, guardadas: dict):
    st.info(f"{atleta} aún no tiene rutina." if lang() == "es" else f"{atleta} n'a pas encore de programme.")
    otras = {a: (guardadas.get(a) or rutinas_iniciales(ATLETAS).get(a)) for a in visibles() if a != atleta}
    otras = {a: r for a, r in otras.items() if r}
    opciones = ["Vacía"] + (["Copiar la de otra persona"] if otras else []) + (["✨ Con IA según su estilo"] if ia_disponible() else [])
    modo = st.radio("Cómo crearla", opciones, key=f"cr_modo_{atleta}", horizontal=True)
    if modo == "Copiar la de otra persona":
        origen = st.selectbox("Copiar de", list(otras), key=f"cr_origen_{atleta}")
        st.caption("Se copian los días, los ejercicios y los pesos actuales; empieza en la semana 1 y luego "
                   "ajustas los pesos tocándolos.")
        if st.button("Crear rutina", type="primary", key=f"cr_ok_{atleta}"):
            guardar_rutina(atleta, copiar_rutina(_completar_partes(otras[origen], origen), _nuevo_id))
            st.rerun()
    elif modo == "✨ Con IA según su estilo":
        c1, c2 = st.columns([1, 2])
        dias = c1.number_input("Días por semana", 2, 7, 4, key=f"cr_dias_{atleta}")
        enfoque = c2.text_input("Qué quiere (opcional)", key=f"cr_enf_{atleta}",
                                placeholder="más movilidad, halterofilia, preparar el Open…")
        con_coach = bool(_datos_coach()) and st.checkbox("Inspirarse también en el coach", value=False,
                                                         key=f"cr_coach_{atleta}")
        st.caption("Usa lo que esta persona tenga en las secciones (WODs, Conditioning…), por ejemplo lo importado de "
                   "WhatsApp. Cuanto más haya, más se parecerá a su estilo.")
        if st.button("✨ Crear rutina", type="primary", key=f"cr_ia_{atleta}"):
            with st.spinner("Pensando la semana…"):
                try:
                    rut = inventar_rutina_con_ia(atleta, int(dias), enfoque, con_coach)
                except Exception as ex:
                    st.error(f"La IA no ha podido: {ex}")
                    return
            if not rut["dias"]:
                st.error("La IA no ha devuelto una rutina válida. Prueba otra vez.")
                return
            guardar_rutina(atleta, rut)
            st.session_state["aviso"] = "Rutina creada. Revisa los pesos y ajústalos tocándolos."
            st.rerun()
    elif st.button("Crear rutina", key=f"crear_rut_{atleta}", type="primary"):
        guardar_rutina(atleta, {"semana_actual": 1, "ajustes": {},
                                "dias": [{"id": _nuevo_id(), "nombre": "Día 1", "lineas": []}]})
        st.rerun()


def editar_dia(atleta: str, rut: dict, dia: dict, semana: int):
    col = f"Semana {semana}"
    base = f"{atleta}_{dia['id']}_{semana}"
    df = pd.DataFrame(
        [{"id": l["id"], "Parte": p, "Ejercicio": l["ejercicio"],
          col: prescripcion_semana(l, semana, rut.get("ajustes"))[0],
          "Sube (kg)": float(l.get("sube") or 0), "Nota": l.get("nota", "")}
         for l, p in zip(dia["lineas"], partes_del_dia(dia))],
        columns=["id", "Parte", "Ejercicio", col, "Sube (kg)", "Nota"],
    )
    opciones_parte = list(dict.fromkeys(PARTES + [p for p in df["Parte"] if p]))
    nombre = st.text_input("Nombre del día", dia["nombre"], key=f"nom_{base}")
    por_ej = st.toggle("Poder marcar cada ejercicio de fuerza como no hecho", value=bool(dia.get("por_ejercicio")),
                       key=f"porej_{base}")
    ids_dias = [d["id"] for d in rut["dias"]]
    nombres_dias = {d["id"]: d["nombre"] for d in rut["dias"]}
    actual_pasa = dia.get("pasa_a") if dia.get("pasa_a") in ids_dias else dia["id"]
    pasa_a = st.selectbox("Si no se hace, a la semana siguiente pasa al…", ids_dias, index=ids_dias.index(actual_pasa),
                          format_func=lambda i: nombres_dias[i] + (" (el mismo día)" if i == dia["id"] else ""),
                          key=f"pasa_{base}")
    tabla = st.data_editor(
        df, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"edr_{base}",
        column_order=["Parte", "Ejercicio", col, "Sube (kg)", "Nota"],
        column_config={
            "Parte": st.column_config.SelectboxColumn(options=opciones_parte, default="A) Fuerza", required=True),
            "Ejercicio": st.column_config.TextColumn(width="medium"),
            col: st.column_config.TextColumn(help="Series, reps y peso tras @: 3x3 @50, 3@40 2@45 1@50, 10 @25"),
            "Sube (kg)": st.column_config.NumberColumn(min_value=0.0, step=1.25, default=2.5, format="%.2f",
                                                       help="Kg que sube cada semana. 0 = no sube"),
            "Nota": st.column_config.TextColumn(),
        },
    )
    st.caption("Escribe el peso tras una @ para que suba solo. Para WOD o conditioning deja «Sube» en 0. "
               "La columna Parte agrupa el día en A, B, C…")
    modo = st.radio("Si cambias un peso, aplicarlo a…", ["Esta semana y las siguientes", "Solo esta semana"],
                    horizontal=True, key=f"modo_{base}")
    b1, b2 = st.columns(2)
    if b1.button("Guardar cambios", type="primary", key=f"save_{base}", use_container_width=True):
        filas = [{"id": r.get("id"), "parte": r.get("Parte"), "ejercicio": r.get("Ejercicio"), "presc": r.get(col),
                  "sube": r.get("Sube (kg)"), "nota": r.get("Nota")} for r in tabla.to_dict("records")]
        nueva = aplicar_edicion(rut, dia["id"], filas, semana, modo == "Solo esta semana", _nuevo_id)
        for d in nueva["dias"]:
            if d["id"] == dia["id"]:
                d["nombre"] = nombre.strip() or d["nombre"]
                d["por_ejercicio"] = por_ej
                d["pasa_a"] = None if pasa_a == dia["id"] else pasa_a
        guardar_rutina(atleta, nueva)
        st.session_state["aviso"] = "Rutina guardada"
        st.rerun()

    confirmar = f"conf_borrar_dia_{base}"
    if st.session_state.get(confirmar):
        b2.warning("¿Borrar este día de la rutina?")
        s1, s2 = b2.columns(2)
        if s1.button("Sí, borrar", key=f"si_{base}"):
            guardar_rutina(atleta, dict(rut, dias=[d for d in rut["dias"] if d["id"] != dia["id"]]))
            st.session_state.pop(confirmar, None)
            st.rerun()
        if s2.button("Cancelar", key=f"no_{base}"):
            st.session_state.pop(confirmar, None)
            st.rerun()
    elif b2.button("Borrar día", key=f"del_{base}", use_container_width=True):
        st.session_state[confirmar] = True
        st.rerun()


def tab_historial(atleta: str, entrenos: list[dict]):
    if not entrenos:
        st.info("Aún no hay entrenos. Ve a **Registrar** para guardar el primero.")
        return
    presentes = [k for k in TIPOS if any(w["type"] == k for w in entrenos)]
    filtro = st.multiselect("Filtrar por tipo", presentes, format_func=lambda k: TIPOS[k][0],
                            placeholder="Todos", key=f"filtro_{atleta}")
    lista = [w for w in entrenos if not filtro or w["type"] in filtro]
    prs = ids_con_pr(entrenos)
    st.caption(f"{len(lista)} de {len(entrenos)} entrenos")

    for w in lista:
        with st.container(border=True):
            tiene_foto = bool(w.get("photo_path"))
            cols = st.columns([1, 2]) if tiene_foto else [None, st.container()]
            if tiene_foto:
                src = store().foto(w)
                if src:
                    cols[0].image(src, use_container_width=True)
            cuerpo = cols[1]
            cabecera = f"{etiqueta_tipo(w['type'])} · {fecha_larga(w['date'])}"
            if w.get("duration_sec"):
                cabecera += f" · ⏱ `{fmt_tiempo(w['duration_sec'])}`"
            cuerpo.markdown(cabecera)
            if w.get("title"):
                cuerpo.markdown(f"#### {w['title']}")
            lineas = []
            for e in w.get("entries") or []:
                pr = " :green[**PR**]" if (w["id"], norm(e["name"]) + "|" + e["unit"]) in prs else ""
                lineas.append(f"- {e['name']}: `{fmt_valor(e.get('value'), e['unit'])}`{pr}")
            if lineas:
                cuerpo.markdown("\n".join(lineas))
            if w.get("notes"):
                cuerpo.caption(w["notes"])

            clave = f"borrar_{w['id']}"
            if st.session_state.get("confirmar") == w["id"]:
                cuerpo.warning("¿Borrar este entreno" + (" y su foto" if tiene_foto else "") + "? No se puede deshacer.")
                b1, b2 = cuerpo.columns(2)
                if b1.button("Sí, borrar", key=clave + "_si", type="primary"):
                    store().borrar(w)
                    refrescar()
                    st.session_state.pop("confirmar", None)
                    st.session_state["aviso"] = "Entreno borrado"
                    st.rerun()
                if b2.button("Cancelar", key=clave + "_no"):
                    st.session_state.pop("confirmar", None)
                    st.rerun()
            elif cuerpo.button("Borrar", key=clave):
                st.session_state["confirmar"] = w["id"]
                st.rerun()


COLOR_NIVEL = {"bueno": "green", "malo": "red", "aviso": "orange", "info": "gray"}


def tab_progreso(atleta: str, entrenos: list[dict]):
    if not entrenos:
        st.info("Cuando guardes entrenos con resultados (kg, tiempos, reps…) verás aquí tu progresión.")
        return

    st.subheader("Dónde mejorar")
    for c in consejos(entrenos):
        color = TIPOS[c["tipo"]][2] if c["nivel"] == "tipo" else COLOR_NIVEL[c["nivel"]]
        st.markdown(f":{color}[▌] **{c['titulo']}**  \n{c['detalle']}")

    series = series_ejercicios(entrenos)
    if series:
        st.subheader("Progresión por ejercicio")
        claves = [s["key"] for s in series]
        por_clave = {s["key"]: s for s in series}
        k = st.selectbox("Ejercicio o WOD", claves, key=f"ej_{atleta}",
                         format_func=lambda k: f"{por_clave[k]['name']} ({por_clave[k]['unit']}) · {len(por_clave[k]['pts'])}")
        s = por_clave[k]
        best, ult, prim = mejor_punto(s), s["pts"][-1], s["pts"][0]
        pct = cambio_pct(s)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mejor marca", fmt_valor(best["v"], s["unit"]), f"{best['date']:%d/%m}", delta_color="off")
        m2.metric("Última", fmt_valor(ult["v"], s["unit"]), f"{ult['date']:%d/%m}", delta_color="off")
        m3.metric("Desde el inicio", f"{pct:+.1f}%".replace(".", ",") if pct is not None else "—",
                  f"vs {prim['date']:%d/%m}", delta_color="off")
        m4.metric("Registros", len(s["pts"]))

        xs = [p["date"] for p in s["pts"]]
        ys = [p["v"] for p in s["pts"]]
        txt = [fmt_valor(v, s["unit"]) for v in ys]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color="#1f5fbf", width=2.5),
                                 marker=dict(size=8), text=txt, hovertemplate="%{x|%d/%m/%Y}: %{text}<extra></extra>",
                                 name=s["name"]))
        fig.add_trace(go.Scatter(x=[best["date"]], y=[best["v"]], mode="markers+text",
                                 marker=dict(size=14, color="#2a8c4a"), text=[fmt_valor(best["v"], s["unit"])],
                                 textposition="top center", hoverinfo="skip", name="Mejor marca"))
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
        if s["unit"] == "tiempo":
            eje_tiempo(fig, ys)
            fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("En tiempos, menos es mejor: el eje está invertido para que subir sea mejorar."
                   if s["unit"] in MENOS_ES_MEJOR else "Arriba es mejor. El punto verde es tu mejor marca.")

    st.subheader("Frecuencia semanal")
    lunes, cuentas = sesiones_por_semana(entrenos)
    fig = go.Figure()
    for k, (nombre, color, _) in TIPOS.items():
        if k in cuentas:
            fig.add_trace(go.Bar(x=[f"{l:%d/%m}" for l in lunes], y=cuentas[k], name=nombre, marker_color=color))
    fig.update_layout(barmode="stack", height=280, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=-0.2), yaxis=dict(dtick=1, title="Sesiones"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Sesiones por semana en las últimas 8 semanas (semana que empieza el lunes indicado).")


def tab_grupo(todos: list[dict]):
    if not todos:
        st.info("Cuando alguien guarde entrenos verás aquí la comparación del grupo.")
        return
    hoy = dt.date.today()
    filas = []
    for a in ATLETAS:
        ws = [w for w in todos if w["athlete"] == a]
        tipos30 = [w["type"] for w in ws if (hoy - a_fecha(w["date"])).days <= 30]
        fav = max(set(tipos30), key=tipos30.count) if tipos30 else None
        filas.append({
            "Atleta": a,
            "Sesiones (30 días)": len(tipos30),
            "Media semanal": round(sum(1 for w in ws if 0 <= (hoy - a_fecha(w["date"])).days < 28) / 4, 1),
            "Último entreno": fecha_larga(ws[0]["date"]) if ws else "—",
            "Lo que más hace": TIPOS[fav][0] if fav else "—",
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)

    st.subheader("Sesiones por semana")
    lunes, cuentas = sesiones_por_semana(todos, clave="athlete")
    fig = go.Figure()
    for i, a in enumerate(ATLETAS):
        fig.add_trace(go.Bar(x=[f"{l:%d/%m}" for l in lunes], y=cuentas.get(a, [0] * len(lunes)), name=a,
                             marker_color=COLORES_ATLETA[i % len(COLORES_ATLETA)]))
    fig.update_layout(barmode="group", height=300, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=-0.2), yaxis=dict(dtick=1))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Mismo ejercicio, cara a cara")
    por_atleta = {a: {s["key"]: s for s in series_ejercicios([w for w in todos if w["athlete"] == a])} for a in ATLETAS}
    compartidos: dict[str, list[str]] = {}
    for a, ss in por_atleta.items():
        for k in ss:
            compartidos.setdefault(k, []).append(a)
    comunes = sorted([k for k, quien in compartidos.items() if len(quien) >= 2],
                     key=lambda k: -len(compartidos[k]))
    if not comunes:
        st.caption("Cuando dos o más registréis el mismo ejercicio (escrito igual) podréis compararlo aquí.")
        return
    nombre_de = {k: next(por_atleta[a][k]["name"] for a in compartidos[k]) for k in comunes}
    k = st.selectbox("Ejercicio", comunes, format_func=lambda k: f"{nombre_de[k]} ({k.split('|')[1]})", key="ej_grupo")
    unidad = k.split("|")[1]
    fig = go.Figure()
    marcas = []
    todos_y = []
    for i, a in enumerate(ATLETAS):
        s = por_atleta[a].get(k)
        if not s:
            continue
        ys = [p["v"] for p in s["pts"]]
        todos_y += ys
        fig.add_trace(go.Scatter(x=[p["date"] for p in s["pts"]], y=ys, mode="lines+markers", name=a,
                                 line=dict(color=COLORES_ATLETA[i % len(COLORES_ATLETA)], width=2.5),
                                 text=[fmt_valor(v, unidad) for v in ys],
                                 hovertemplate=a + " · %{x|%d/%m}: %{text}<extra></extra>"))
        b = mejor_punto(s)
        marcas.append({"Atleta": a, "Mejor marca": fmt_valor(b["v"], unidad), "Fecha": f"{b['date']:%d/%m/%Y}",
                       "Registros": len(s["pts"]), "_v": b["v"]})
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2))
    if unidad == "tiempo":
        eje_tiempo(fig, todos_y)
        fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
    marcas.sort(key=lambda m: m["_v"], reverse=unidad not in MENOS_ES_MEJOR)
    st.dataframe(pd.DataFrame(marcas).drop(columns="_v"), hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- WODs
COLOR_CAT = {"Gym": "violet", "Barbell": "red", "Dumbbell": "blue", "Cardio": "green", "🎖️ Hero": "orange",
             "Cadera": "violet", "Hombros": "blue", "Tobillos": "green", "Espalda": "orange", "Isquios": "red"}


def seccion_wods(todos: list[dict]):
    seccion_biblio("wod", todos)


def seccion_biblio(tipo: str, todos: list[dict]):
    try:
        guardadas = cargar_rutinas()
    except Exception as ex:
        st.warning(f"No se pudieron cargar las rutinas: {ex}")
        guardadas = {}
    rutinas = {a: _completar_partes(guardadas.get(a) or rutinas_iniciales(ATLETAS).get(a), a) for a in ATLETAS}
    bib = dict(guardadas.get(CLAVE_BIBLIOTECA) or {})
    clave = CLAVES_BIBLIO[tipo]
    k = f"bib_{tipo}"

    q = st.text_input(t("Buscar por movimiento"), key=f"{k}_q",
                      placeholder="thruster, pull up, wall ball… (separa con comas para buscar varios)")
    if tipo == "mobility":
        cats_tipo = CATEGORIAS_MOVILIDAD
    else:
        cats_tipo = CATEGORIAS_WOD if tipo == "wod" else [c for c in CATEGORIAS_WOD if "Hero" not in c]
    if tipo == "wod":
        cats_tipo = cats_tipo + ["⏱️ EMOM"]
    cat = st.segmented_control(t("Tipo"), cats_tipo, default="Todos", key=f"{k}_cat", format_func=t) or "Todos"
    tramo = (st.segmented_control("Duración", TRAMOS_EMOM, key=f"{k}_tramo")
             if cat == "⏱️ EMOM" else None)
    c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
    quien = [solo()] if solo() else c1.multiselect(t("Quién"), ATLETAS, placeholder=t("Todos"), key=f"{k}_quien")
    solo_h = c2.toggle(t("Solo los hechos"), value=True, key=f"{k}_solo")

    filtrados, por_cat = [], {c: 0 for c in cats_tipo}
    for g in biblioteca(rutinas, ATLETAS, todos, bib, tipo):
        veces = [v for v in g["veces"] if (not quien or v["atleta"] in quien) and (not solo_h or v["estado"] == "hecho")]
        if not veces or (q and not coincide_busqueda(g["titulo"] + "\n" + g["texto"], q)):
            continue
        texto_g = g["titulo"] + "\n" + g["texto"]
        emom = tipo == "wod" and es_emom(texto_g)
        por_cat["Todos"] += 1
        for c in g["categorias"] + (["⏱️ EMOM"] if emom else []):
            if c in por_cat:
                por_cat[c] += 1
        if cat == "⏱️ EMOM":
            if emom and (not tramo or tramo_emom(duracion_emom(texto_g)) == tramo):
                filtrados.append((g, veces))
        elif cat == "Todos" or cat in g["categorias"]:
            filtrados.append((g, veces))
    st.caption(" · ".join(f"{t(c)}: {n}" for c, n in por_cat.items()))
    if tipo == "wod":
        url = ("https://www.google.com/search?q=" + quote(f"site:wodwell.com {q}")) if q else "https://wodwell.com"
        st.link_button("Buscar en Wodwell" + (f": {q}" if q else ""), url)

    if not filtrados:
        st.info(f"No hay {NOMBRE_BIBLIO[tipo]} con estos filtros. Aparecen aquí cuando escribís o elegís lo que toca "
                "en esa parte de la rutina (y la marcáis como hecha) o si los añadís abajo.")
    for g, veces in filtrados:
        with st.container(border=True):
            primera = g["texto"].split("\n")[0]
            titulo = g["titulo"] or (primera[:60] + ("…" if len(primera) > 60 else ""))
            chips = " ".join(f":{COLOR_CAT.get(c, 'gray')}[● {t(c)}]" for c in g["categorias"]) or ":gray[—]"
            st.markdown(f"**{titulo}**  {chips}")
            with st.popover(t("Cambiar tipo")):
                elegidas = st.multiselect("Tipos", [c for c in cats_tipo if c != "Todos"],
                                          default=[c for c in g["categorias"] if c in cats_tipo],
                                          key=f"cat_{tipo}_{g['clave'][:60]}")
                if st.button("Guardar", key=f"catg_{tipo}_{g['clave'][:60]}", type="primary"):
                    corr = dict(bib.get("categorias_manual", {}), **{g["clave"]: elegidas})
                    guardar_rutina(CLAVE_BIBLIOTECA, dict(bib, categorias_manual=corr))
                    st.session_state["aviso"] = "Tipo cambiado"
                    st.rerun()
            if g["texto"] and g["texto"] != titulo:
                st.markdown(g["texto"].replace("\n", "  \n"))
            lineas = []
            for v in veces:
                linea = f"- **{v['atleta'] or '—'}** · {v['cuando']} {SIMBOLO.get(v['estado'], '')}"
                if v["resultado"]:
                    linea += f" · `{v['resultado']}`"
                lineas.append(linea)
            st.markdown("\n".join(lineas))
            if g["ids"]:
                with st.popover("Borrar de la lista"):
                    st.write("¿Seguro? Solo se borra el WOD añadido a mano, no los de las rutinas.")
                    if st.button("Sí, borrar", key=f"del{tipo}_{'_'.join(sorted(g['ids']))}", type="primary"):
                        bib2 = dict(bib, **{clave: [w for w in bib.get(clave, []) if w.get("id") not in g["ids"]]})
                        guardar_rutina(CLAVE_BIBLIOTECA, bib2)
                        st.rerun()

    with st.expander(f"➕ Añadir a {NOMBRE_BIBLIO[tipo]}"):
        with st.form(f"nuevo_{tipo}", clear_on_submit=True):
            nombre = st.text_input("Nombre", placeholder="Fran, Cindy, DT…")
            texto = st.text_area("Qué es", placeholder="21-15-9: thrusters @42,5 + pull ups", height=100)
            c1, c2 = st.columns(2)
            quien_n = c1.multiselect("Quién lo hizo", visibles(), key=f"{k}_nq",
                                     default=[solo()] if solo() else [])
            fecha = c2.date_input("Fecha", dt.date.today(), format="DD/MM/YYYY")
            resultado = st.text_input("Resultado", placeholder="5:41, 18 rondas + 3…")
            if st.form_submit_button("Añadir", type="primary", use_container_width=True):
                if not (nombre.strip() or texto.strip()):
                    st.error("Escribe al menos el nombre o qué es.")
                else:
                    bib2 = dict(bib, **{clave: bib.get(clave, []) + [{
                        "id": uuid.uuid4().hex[:8], "nombre": nombre.strip(), "texto": texto.strip(),
                        "quien": quien_n, "fecha": fecha.isoformat(), "resultado": resultado.strip()}]})
                    guardar_rutina(CLAVE_BIBLIOTECA, bib2)
                    st.session_state["aviso"] = "Añadido a la lista"
                    st.rerun()



    with st.expander(t("📲 Importar de WhatsApp")):
        importar_whatsapp(bib, tipo)

    with st.expander(t("✨ Inventar con IA")):
        res = _ia_panel(tipo, f"sec_{tipo}")
        if res and st.button("Guardar en la lista como idea", key=f"ig_{tipo}"):
            bib2 = dict(bib, **{clave: bib.get(clave, []) + [{
                "id": uuid.uuid4().hex[:8], "nombre": res[0], "texto": res[1], "quien": [],
                "fecha": dt.date.today().isoformat(), "resultado": "", "idea": True}]})
            guardar_rutina(CLAVE_BIBLIOTECA, bib2)
            st.session_state.pop(f"ir_sec_{tipo}", None)
            st.session_state["aviso"] = "Guardado como idea (quita «Solo los hechos» para verlo)"
            st.rerun()

    with st.expander(t("💡 Ideas del repertorio")):
        q2 = st.text_input(t("Buscar en el repertorio"), key=f"{k}_rq", placeholder="thruster, row…")
        heroes = {n for n, _ in HEROES}
        bloques = ([("Clásicos y propuestas", [x for x in REPERTORIO[tipo] if x[0] not in heroes and x not in COMPETICION]),
                    ("🏆 Competición (Open)", COMPETICION), ("🎖️ Hero WODs", HEROES)]
                   if tipo == "wod" else [("", REPERTORIO[tipo])])
        if tipo == "wod" and cat == "🎖️ Hero":
            bloques = [("🎖️ Hero WODs", HEROES)]
        for titulo_b, items in bloques:
            vis = [x for x in items if not q2 or coincide_busqueda(x[0] + "\n" + x[1], q2)]
            if not vis:
                continue
            if titulo_b:
                st.markdown(f"**{titulo_b}**")
            st.markdown("\n".join(f"- **{n}** · {t}" for n, t in vis))


# ---------------------------------------------------------------- importar de WhatsApp
TIPO_ETIQUETA = {"wod": "WOD", "conditioning": "Conditioning", "accessory": "Accessory", "mobility": "Movilidad"}
NADIE = "Nadie (guardar como idea)"


def _leer_chat(archivo) -> str:
    datos = archivo.getvalue()
    if archivo.name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            txts = [n for n in z.namelist() if n.lower().endswith(".txt")]
            if not txts:
                return ""
            datos = z.read(next((n for n in txts if "chat" in n.lower()), txts[0]))
    return datos.decode("utf-8", errors="replace").lstrip("\ufeff")


def importar_whatsapp(bib: dict, tipo_seccion: str):
    n = st.session_state.setdefault("wa_n", 0)
    st.caption("En el iPhone: abre el chat → toca su nombre → Exportar chat → Sin archivos → Guardar en Archivos. "
               "Sube aquí el .zip tal cual (o el .txt).")
    archivos = st.file_uploader("Chats exportados (puedes subir varios a la vez)", type=["zip", "txt"],
                                accept_multiple_files=True, key=f"wa_file_{tipo_seccion}_{n}")
    if not archivos:
        return
    candidatos, total, autores_por_chat, fallidos = [], 0, [], []
    for archivo in archivos:
        try:
            mensajes = parse_whatsapp(_leer_chat(archivo))
        except Exception:
            mensajes = []
        if not mensajes:
            fallidos.append(archivo.name)
            continue
        chat = re.sub(r"(?i)^(whatsapp chat - |chat de whatsapp con )|\.(zip|txt)$", "", archivo.name).strip()
        total += len(mensajes)
        autores_por_chat.append({m["autor"] for m in mensajes})
        candidatos += [dict(c, chat=chat) for c in detectar_entrenos(mensajes)]
    if fallidos:
        st.warning("No reconozco el formato de: " + ", ".join(fallidos))
    # el mismo entreno mandado a varios chats sale una sola vez (el primero)
    unicos: dict[str, dict] = {}
    for c in sorted(candidatos, key=lambda c: c["fecha"]):
        k = norm_busqueda(c["cuerpo"])
        if k in unicos:
            if c["chat"] not in unicos[k]["chat"]:
                unicos[k]["chat"] += ", " + c["chat"]
        else:
            unicos[k] = dict(c)
    candidatos = list(unicos.values())
    st.caption(f"{len(archivos) - len(fallidos)} chats · {total} mensajes leídos · {len(candidatos)} entrenos distintos.")
    if not candidatos:
        st.info("No he encontrado mensajes que parezcan entrenos.")
        return

    # quien sale en todos los chats es casi seguro el dueño del móvil → «Yo»
    comunes = set.intersection(*autores_por_chat) if len(autores_por_chat) > 1 else set()
    st.markdown("**¿Quién es quién?** Cada entreno se marca como hecho por quien lo mandó.")
    mapa = {}
    for autor in sorted({c["autor"] for c in candidatos}):
        opciones = visibles() + [NADIE]
        sugerido = emparejar_autor(autor, visibles()) or (visibles()[0] if autor in comunes else NADIE)
        mapa[autor] = st.selectbox(autor, opciones, index=opciones.index(sugerido), key=f"wa_map_{n}_{autor}")
    autores_sel = st.multiselect("Importar solo los mandados por", sorted(mapa), default=sorted(mapa), key=f"wa_solo_{n}")

    ya = {norm_busqueda(item.get("texto", "")) for clave in CLAVES_BIBLIO.values() for item in bib.get(clave, [])}
    filas = [{"Importar": norm_busqueda(c["cuerpo"]) not in ya, "Fecha": c.get("fecha_entreno", c["fecha"]),
              "Mensaje": c["fecha"], "Autor": c["autor"],
              "Chat": c["chat"], "Tipo": TIPO_ETIQUETA[c["tipo"]], "Nombre": c["nombre"], "Entreno": c["cuerpo"]}
             for c in candidatos if c["autor"] in autores_sel]
    if not filas:
        st.info("Nada que importar con ese filtro.")
        return
    st.markdown("**Revisa la lista:** desmarca lo que no sea un entreno y corrige tipo o nombre si hace falta.")
    tabla = st.data_editor(
        pd.DataFrame(filas), hide_index=True, use_container_width=True, key=f"wa_tabla_{n}",
        disabled=["Mensaje", "Autor", "Chat"],
        column_config={
            "Importar": st.column_config.CheckboxColumn(width="small"),
            "Fecha": st.column_config.DateColumn(format="DD/MM/YYYY", help="Día del entreno (sale de «mañana», «el lunes», «12/10»… si el mensaje lo dice)"),
            "Mensaje": st.column_config.DateColumn(format="DD/MM/YYYY", help="Día en que se mandó el mensaje"),
            "Tipo": st.column_config.SelectboxColumn(options=list(TIPO_ETIQUETA.values()), required=True),
            "Entreno": st.column_config.TextColumn(width="large"),
        },
    )
    elegidas = tabla[tabla["Importar"] == True]  # noqa: E712
    if st.button(f"Importar {len(elegidas)} entrenos", type="primary", disabled=elegidas.empty, key=f"wa_ok_{n}"):
        inverso = {v: k for k, v in TIPO_ETIQUETA.items()}
        nueva = dict(bib)
        for _, f in elegidas.iterrows():
            clave = CLAVES_BIBLIO[inverso[f["Tipo"]]]
            quien = [] if mapa.get(f["Autor"], NADIE) == NADIE else [mapa[f["Autor"]]]
            fecha = f["Fecha"].isoformat() if hasattr(f["Fecha"], "isoformat") else str(f["Fecha"])[:10]
            nueva[clave] = nueva.get(clave, []) + [{
                "id": uuid.uuid4().hex[:8], "nombre": str(f["Nombre"] or "").strip(), "texto": str(f["Entreno"]).strip(),
                "quien": quien, "fecha": fecha, "resultado": "", "idea": not quien, "origen": "whatsapp"}]
        guardar_rutina(CLAVE_BIBLIOTECA, nueva)
        st.session_state["wa_n"] = n + 1
        st.session_state["aviso"] = f"{len(elegidas)} entrenos importados de WhatsApp"
        st.rerun()


# ---------------------------------------------------------------- 🔒 Coach (privado)
CLAVE_COACH = "__coach__"
ACCESO_COACH = ["Yo", "Mi esposa"]  # quién puede usar el material del coach en su rutina
TIPOS_COACH = {"semanas": "📅 Semanas", "emom": "⏱️ EMOMs", "halterofilia": "🏋️ Halterofilia", "fuerza": "💪 Fuerza",
               "wod": "🔥 WOD", "gym": "🤸 Gym", "conditioning": "🫀 Conditioning", "accessory": "🧩 Accessories",
               "mobility": "🧘 Movilidad", "consejo": "💬 Consejos"}
COACH_PARA_LINEA = {"wod": ["wod", "gym"], "conditioning": ["conditioning"], "accessory": ["accessory", "gym", "fuerza"],
                    "mobility": ["mobility"]}


def _datos_coach() -> dict | None:
    try:
        return cargar_rutinas().get(CLAVE_COACH)
    except Exception:
        return None


def coach_abierto() -> bool:
    return bool(st.session_state.get("coach_ok")) and not solo()


def _subir_coach():
    archivo = st.file_uploader("Archivo del coach (coach.json)", type=["json"], key="coach_file")
    if not archivo:
        return
    try:
        data = json.loads(archivo.getvalue().decode("utf-8"))
        assert isinstance(data.get("items"), list)
    except Exception:
        st.error("Ese archivo no es el coach.json que te preparé.")
        return
    st.caption(f"{len(data['items'])} bloques y {len(data.get('semanas', []))} semanas completas.")
    if st.button("Guardar en mi app", type="primary", key="coach_guardar"):
        guardar_rutina(CLAVE_COACH, data)
        st.session_state["aviso"] = "Material del coach guardado"
        st.rerun()


def _fecha_txt(f: str) -> str:
    try:
        return f"{a_fecha(f):%d/%m/%Y}"
    except Exception:
        return str(f)


def seccion_coach():
    pin = secreto("COACH_PIN")
    if not pin:
        st.warning("Para activar esta sección, añade `COACH_PIN = \"…\"` en los Secrets de Streamlit.")
        return
    if not st.session_state.get("coach_ok"):
        intento = st.text_input("PIN del coach", type="password", key="coach_pin_in").strip()
        if intento and intento == str(pin).strip():
            st.session_state.coach_ok = True
            st.rerun()
        elif intento:
            st.error("PIN incorrecto.")
        return
    datos = _datos_coach()
    if not datos or not datos.get("items"):
        st.info("Sube el archivo **coach.json** que te preparé. Se guarda solo en tu base de datos, nunca en GitHub.")
        _subir_coach()
        return
    items, semanas = datos["items"], datos.get("semanas", [])
    conteo = Counter(i["tipo"] for i in items)
    conteo["semanas"], conteo["emom"] = len(semanas), sum(1 for i in items if i.get("emom"))
    vista = st.segmented_control("Tipo", list(TIPOS_COACH), default="emom", key="coach_tipo",
                                 format_func=lambda k: f"{TIPOS_COACH[k]} {conteo.get(k, 0)}",
                                 label_visibility="collapsed") or "emom"
    q = st.text_input(t("Buscar por movimiento"), key="coach_q", placeholder="snatch, MU, bike, thruster…")
    anios = sorted({i["fecha"][:4] for i in items}, reverse=True)
    c1, c2 = st.columns(2)
    anio = c1.selectbox("Año", ["Todos"] + anios, key="coach_anio")

    def pasa(texto: str, fecha: str) -> bool:
        return (anio == "Todos" or fecha.startswith(anio)) and (not q or coincide_busqueda(texto, q))

    if vista == "semanas":
        lista = [x for x in semanas if pasa(x["texto"], x["fecha"])][::-1]
        st.caption(f"{len(lista)} semanas")
        for x in lista[: st.session_state.get("coach_n", 25)]:
            with st.expander(f"Semana enviada el {_fecha_txt(x['fecha'])}"):
                st.markdown(x["texto"].replace("\n", "  \n"))
        _ver_mas(len(lista))
        return

    if vista == "emom":
        lista = [i for i in items if i.get("emom")]
        tramo = c2.segmented_control("Duración", TRAMOS_EMOM + ["?"], key="coach_tramo",
                                     format_func=lambda x: "sin duración" if x == "?" else x)
        quien = st.segmented_control("De", ["Coach", "Diego"], key="coach_autor")
        if tramo:
            lista = [i for i in lista if (tramo_emom(i.get("emom_min")) or "?") == tramo]
        if quien:
            lista = [i for i in lista if i.get("autor", "Coach") == quien]
    else:
        lista = [i for i in items if i["tipo"] == vista]
    lista = [i for i in lista if pasa(i["nombre"] + "\n" + i["texto"], i["fecha"])]

    if vista in ("halterofilia", "fuerza"):
        levs = [x for x, _ in Counter(i["levantamiento"] for i in lista).most_common()]
        lev = c2.selectbox("Levantamiento", ["Todos"] + levs, key="coach_lev")
        if lev != "Todos":
            lista = [i for i in lista if i["levantamiento"] == lev]
            sin_pulls = lambda x: "\n".join(l for l in x.split("\n") if "pull" not in l.lower())  # noqa: E731
            puntos = [(i["fecha"], carga_maxima(sin_pulls(i["texto"]))) for i in lista]
            puntos = sorted((f, v) for f, v in puntos if v)
            if len(puntos) >= 2:
                fig = go.Figure(go.Scatter(x=[f for f, _ in puntos], y=[v for _, v in puntos], mode="markers+lines",
                                           line=dict(color="#d6312b"), hovertemplate="%{x}: %{y} kg<extra></extra>"))
                fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10),
                                  title=f"Progresión {lev}: carga más alta de cada sesión (kg)")
                st.plotly_chart(fig, use_container_width=True)
    elif vista not in ("consejo",):
        cats = sorted({c for i in lista for c in i.get("categorias", [])})
        if cats:
            elegidas = c2.multiselect(t("Tipo"), cats, key=f"coach_cats_{vista}", placeholder=t("Todos"))
            if elegidas:
                lista = [i for i in lista if set(elegidas) <= set(i.get("categorias", []))]

    lista = lista[::-1]
    st.caption(f"{len(lista)} resultados")
    for i in lista[: st.session_state.get("coach_n", 25)]:
        with st.container(border=True):
            extra = []
            if i.get("emom_min"):
                extra.append(f"⏱️ {i['emom_min']}'")
            if i.get("autor") == "Diego":
                extra.append("de Diego")
            chips = " ".join(f":{COLOR_CAT.get(c, 'gray')}[● {c}]" for c in i.get("categorias", []))
            st.markdown(f"**{i['nombre']}**  :gray[{_fecha_txt(i['fecha'])} {i.get('dia', '')}] "
                        f"{' · '.join(extra)}  {chips}")
            st.markdown(i["texto"].replace("\n", "  \n"))
    _ver_mas(len(lista))

    with st.expander("Reemplazar el material del coach"):
        _subir_coach()


def _ver_mas(total: int):
    n = st.session_state.get("coach_n", 25)
    if total > n and st.button(f"Ver más ({total - n} restantes)", key=f"coach_mas_{n}"):
        st.session_state["coach_n"] = n + 25
        st.rerun()


# ---------------------------------------------------------------- main
def _idioma_de_atleta():
    """Al cambiar de persona, pone su idioma (Archchana en francés); luego se puede cambiar arriba."""
    st.session_state["lang"] = IDIOMA_DEFECTO.get(st.session_state.get("atleta"), "es")


def main():
    control_contrasena()
    st.markdown("""<style>
      h1 {letter-spacing:.02em; text-transform:uppercase}
      [data-testid="stMetricValue"] {font-variant-numeric: tabular-nums}
    </style>""", unsafe_allow_html=True)
    cab, idi = st.columns([4, 1], vertical_alignment="bottom")
    cab.title(t("Diario de Entrenos"))
    idi.segmented_control(t("Idioma"), ["es", "fr"], key="lang", default="es", label_visibility="collapsed",
                          format_func=lambda x: {"es": "🇪🇸 ES", "fr": "🇫🇷 FR"}[x])

    if isinstance(store(), LocalStore):
        st.caption("Modo local: los datos se guardan en la carpeta `data/`. Configura Supabase para usarla online.")

    secciones = {"WODs": "wod", "Conditioning": "conditioning", "Accessories": "accessory", "Movilidad": "mobility"}
    opciones_vista = ["Personas"] + list(secciones) + ([] if solo() else ["🔒 Coach"])
    vista = st.segmented_control("Ver", opciones_vista, default="Personas", key="vista",
                                 label_visibility="collapsed", format_func=t) or "Personas"
    if vista == "Personas":
        if solo():
            atleta = solo()
        else:
            atleta = st.segmented_control("Atleta", ATLETAS, default=ATLETAS[0], key="atleta",
                                          label_visibility="collapsed", on_change=_idioma_de_atleta) or ATLETAS[0]
    else:
        atleta = vista
    if vista == "🔒 Coach":
        seccion_coach()
        return

    if aviso := st.session_state.pop("aviso", None):
        st.toast(aviso)

    try:
        todos = cargar_todo()
    except Exception as ex:
        st.error(f"No se pudieron cargar los datos: {ex}")
        st.stop()
    if atleta in secciones:
        seccion_biblio(secciones[atleta], todos)
        return
    mios = [w for w in todos if w["athlete"] == atleta]

    nombres = [t("Rutina"), t("Registrar"), t("Historial"), t("Progreso")] + ([] if solo() else [t("Grupo")])
    pestanas = st.tabs(nombres)
    with pestanas[0]:
        tab_rutina(atleta, mios)
    with pestanas[1]:
        tab_registrar(atleta, mios)
    with pestanas[2]:
        tab_historial(atleta, mios)
    with pestanas[3]:
        tab_progreso(atleta, mios)
    if not solo():
        with pestanas[4]:
            tab_grupo(todos)


main()
