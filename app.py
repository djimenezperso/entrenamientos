"""Diario de Entrenos — Streamlit.

Un apartado por persona, con foto, tiempos, notas, progresión y consejos.
Datos en Supabase si hay credenciales en los secrets; si no, en local (SQLite).
"""
from __future__ import annotations

import datetime as dt
import io
import json
import sqlite3
import uuid
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageOps

from logica import (
    MENOS_ES_MEJOR, TIPOS, UNIDADES, a_fecha, aplicar_edicion, cambio_pct, consejos, es_metcon, fmt_num,
    fmt_tiempo, fmt_valor, ids_con_pr, mejor_punto, norm, parse_tiempo, parse_valor, peso_principal,
    prescripcion_semana, series_ejercicios, sesiones_por_semana,
    destino_dia_siguiente, destino_semana_siguiente, estado_dia, marcar_dia, pendientes_para, sin_validar,
)
from rutinas_iniciales import rutinas_iniciales

try:  # fotos HEIC del iPhone
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass

# ===== Cambia aquí los nombres =====
ATLETAS = ["Yo", "Manu Anel", "Salatti", "Mi esposa"]
COLORES_ATLETA = ["#16202b", "#d6312b", "#1f5fbf", "#2a8c4a", "#d9a200", "#7f8994"]
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
    clave = secreto("APP_PASSWORD")
    if not clave or st.session_state.get("dentro"):
        return
    st.title("Diario de Entrenos")
    intento = st.text_input("Contraseña", type="password")
    if intento.strip() == str(clave).strip():  # el móvil a veces añade un espacio al final
        st.session_state.dentro = True
        st.rerun()
    elif intento:
        st.error("Contraseña incorrecta.")
    st.stop()


def eje_tiempo(fig: go.Figure, valores: list[float], eje: str = "yaxis"):
    lo, hi = min(valores), max(valores)
    paso = max(5, round((hi - lo) / 4 / 5) * 5) if hi > lo else 15
    inicio = int(lo // paso * paso)
    ticks = list(range(inicio, int(hi) + paso + 1, paso))
    fig.update_layout(**{eje: dict(tickvals=ticks, ticktext=[fmt_tiempo(t) for t in ticks])})


# ---------------------------------------------------------------- pestañas
def formulario_entreno(atleta: str, entrenos: list[dict], clave: str, inicial: dict | None = None):
    """Formulario de entreno. `inicial` = {tipo, titulo, filas:[{Ejercicio, Resultado, Unidad}]}."""
    inicial = inicial or {}
    n = st.session_state.setdefault(f"form_n_{clave}", 0)
    usados = sorted({e["name"].strip() for w in entrenos for e in (w.get("entries") or []) if e.get("name")}, key=str.lower)
    filas = inicial.get("filas") or [{"Ejercicio": "", "Resultado": "", "Unidad": "tiempo"} for _ in range(3)]
    tipos = list(TIPOS)

    with st.form(f"form_{clave}_{n}"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", tipos, index=tipos.index(inicial.get("tipo", "fuerza")),
                            format_func=lambda k: TIPOS[k][0])
        fecha = c2.date_input("Fecha", dt.date.today(), format="DD/MM/YYYY")
        c3, c4 = st.columns([2, 1])
        titulo = c3.text_input("Título", value=inicial.get("titulo", ""), placeholder="Fran, Pierna, 10K suave…")
        duracion = c4.text_input("Duración total", placeholder="h:mm:ss o min")

        st.markdown("**Resultados**")
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
        notas = st.text_area("Notas", placeholder="Sensaciones, escalado, qué falló…")
        foto = st.file_uploader("Foto", type=["jpg", "jpeg", "png", "webp", "heic", "heif"])
        enviado = st.form_submit_button("Guardar entreno", type="primary", use_container_width=True)

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


def _inicial_desde_dia(rut: dict, dia: dict, semana: int) -> dict:
    filas, fuerza = [], False
    for l in dia["lineas"]:
        txt, _, _ = prescripcion_semana(l, semana, rut.get("ajustes"))
        if es_metcon(l["ejercicio"]):
            filas.append({"Ejercicio": l["ejercicio"], "Resultado": "", "Unidad": "tiempo"})
        else:
            fuerza = True
            p = peso_principal(txt)
            filas.append({"Ejercicio": l["ejercicio"], "Resultado": fmt_num(p) if p is not None else "", "Unidad": "kg"})
    return {"tipo": "fuerza" if fuerza else "wod", "titulo": _titulo_dia(semana, dia), "filas": filas}


def _cambiar_semana(atleta: str, rut: dict, nueva: int):
    rut = dict(rut, semana_actual=nueva)
    guardar_rutina(atleta, rut)
    st.session_state[f"sem_{atleta}"] = nueva


def _chip_estado(est: dict, semana: int, dias: dict) -> str:
    if est["estado"] == "hecho":
        return ":green[✓ hecho]"
    if est["estado"] == "pospuesto":
        s, did = est["destino"]
        nombre = dias.get(did, {}).get("nombre", "otro día")
        return f":orange[↷ pasado a {nombre}" + (f" (semana {s})]" if s != semana else "]")
    return ":gray[○ sin validar]"


def _lineas_dia(rut: dict, dia: dict, semana: int):
    lineas = []
    for l in dia["lineas"]:
        txt, subio, ajuste = prescripcion_semana(l, semana, rut.get("ajustes"))
        if txt:
            linea = f"- **{l['ejercicio']}** · `{txt}`"
        elif es_metcon(l["ejercicio"]):
            linea = f"- **{l['ejercicio']}** · :gray[por definir]"
        else:
            linea = f"- **{l['ejercicio']}** · :orange[falta el peso]"
        if ajuste:
            linea += " :orange[(cambio solo esta semana)]"
        elif subio and semana > int(l.get("base") or 1):
            linea += f" :green[+{fmt_num((semana - int(l['base'])) * float(l['sube']))}]"
        if l.get("nota"):
            linea += f" — _{l['nota']}_"
        lineas.append(linea)
    st.markdown("\n".join(lineas) if lineas else ":gray[Sin ejercicios. Añádelos en Editar.]")


def _marcar(atleta: str, rut: dict, semana: int, dia_id: str, estado, destino=None, aviso: str = ""):
    guardar_rutina(atleta, marcar_dia(rut, semana, dia_id, estado, destino))
    if aviso:
        st.session_state["aviso"] = aviso


def _botones_estado(atleta: str, rut: dict, semana: int, dia: dict, est: dict, k: str,
                    desde: tuple[int, str] | None = None):
    """`desde` = (semana, día) donde se está mostrando, si es un pendiente traído de otro día."""
    if est["estado"] == "hecho":
        if est.get("registrado"):
            st.caption("Validado al registrar el entreno.")
        else:
            st.button("Deshacer", key=f"undo_{k}", on_click=_marcar, args=(atleta, rut, semana, dia["id"], None))
        return
    sem_aqui, dia_aqui = desde or (semana, dia["id"])
    sig = destino_dia_siguiente(rut, sem_aqui, dia_aqui)
    sem_sig = destino_semana_siguiente(sem_aqui, dia["id"])
    nombre_sig = next(d["nombre"] for d in rut["dias"] if d["id"] == sig[1])
    b1, b2, b3 = st.columns(3)
    b1.button("✓ Hecho", key=f"ok_{k}", type="primary", use_container_width=True,
              on_click=_marcar, args=(atleta, rut, semana, dia["id"], "hecho", None, f"{dia['nombre']} validado"))
    b2.button(f"No lo hice → {nombre_sig}" + (f" (sem. {sig[0]})" if sig[0] != sem_aqui else ""),
              key=f"next_{k}", use_container_width=True,
              on_click=_marcar, args=(atleta, rut, semana, dia["id"], "pospuesto", sig, f"Pasado a {nombre_sig}"))
    b3.button(f"No lo hice → semana {sem_sig[0]}", key=f"week_{k}", use_container_width=True,
              on_click=_marcar, args=(atleta, rut, semana, dia["id"], "pospuesto", sem_sig,
                                      f"Pasado a la semana {sem_sig[0]}"))


def tab_rutina(atleta: str, entrenos: list[dict]):
    try:
        guardadas = cargar_rutinas()
    except Exception as ex:
        st.warning("Falta crear la tabla de rutinas en Supabase. Ve a **SQL Editor**, pega esto y pulsa **Run**; "
                   "luego recarga la página.")
        st.code(SQL_RUTINAS, language="sql")
        st.caption(f"Detalle: {ex}")
        return

    rut = guardadas.get(atleta) or rutinas_iniciales(ATLETAS).get(atleta)
    if not rut:
        st.info(f"{atleta} aún no tiene rutina.")
        if st.button("Crear rutina", key=f"crear_rut_{atleta}", type="primary"):
            guardar_rutina(atleta, {"semana_actual": 1, "ajustes": {},
                                    "dias": [{"id": _nuevo_id(), "nombre": "Día 1", "lineas": []}]})
            st.rerun()
        return

    actual = int(rut.get("semana_actual") or 1)
    clave_sem = f"sem_{atleta}"
    if clave_sem not in st.session_state:
        st.session_state[clave_sem] = actual
    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    semana = int(c1.number_input("Semana", min_value=1, step=1, key=clave_sem))
    if semana == actual:
        c2.button(f"Terminé la semana {actual} → pasar a la {actual + 1}", key=f"sig_{atleta}",
                  on_click=_cambiar_semana, args=(atleta, rut, actual + 1), use_container_width=True)
    else:
        c2.button(f"Marcar la semana {semana} como la actual", key=f"act_{atleta}",
                  on_click=_cambiar_semana, args=(atleta, rut, semana), use_container_width=True)
    momento = "esta semana" if semana == actual else ("semana pasada" if semana < actual else "semana que viene")
    st.caption(f"Semana {semana} ({momento}). Los pesos tras @ suben lo indicado en «Sube» cada semana "
               "(2,5 kg por defecto). Cámbialo o haz excepciones en «Editar».")

    registrados = {w.get("title") for w in entrenos}
    faltan = sin_validar(rut, semana, registrados)
    if semana <= actual and faltan:
        st.warning(f"Sin validar en la semana {semana}: {', '.join(faltan)}. "
                   "Márcalos como hechos o pásalos a otro día.")

    nombres = {d["id"]: d for d in rut["dias"]}
    for dia in rut["dias"]:
        with st.container(border=True):
            est = estado_dia(rut, semana, dia["id"], _titulo_dia(semana, dia) in registrados)
            st.markdown(f"#### {dia['nombre']}  {_chip_estado(est, semana, nombres)}")
            _lineas_dia(rut, dia, semana)
            _botones_estado(atleta, rut, semana, dia, est, f"{dia['id']}_{semana}")
            with st.expander("Registrar este día"):
                formulario_entreno(atleta, entrenos, f"rut_{atleta}_{dia['id']}_{semana}",
                                   _inicial_desde_dia(rut, dia, semana))

            for so, did in pendientes_para(rut, semana, dia["id"], registrados):
                origen = nombres[did]
                st.divider()
                st.markdown(f"##### :orange[↷ Pendiente: semana {so} · {origen['nombre']}]")
                _lineas_dia(rut, origen, so)
                est_o = estado_dia(rut, so, did)
                _botones_estado(atleta, rut, so, origen, est_o, f"pend_{did}_{so}_{dia['id']}_{semana}",
                                desde=(semana, dia["id"]))
                with st.expander(f"Registrar {origen['nombre']} (semana {so})"):
                    formulario_entreno(atleta, entrenos, f"rutp_{atleta}_{did}_{so}",
                                       _inicial_desde_dia(rut, origen, so))

            with st.expander("Editar"):
                editar_dia(atleta, rut, dia, semana)

    if st.button("+ Añadir día", key=f"add_dia_{atleta}"):
        rut2 = dict(rut, dias=rut["dias"] + [{"id": _nuevo_id(), "nombre": f"Día {len(rut['dias']) + 1}", "lineas": []}])
        guardar_rutina(atleta, rut2)
        st.rerun()


def editar_dia(atleta: str, rut: dict, dia: dict, semana: int):
    col = f"Semana {semana}"
    base = f"{atleta}_{dia['id']}_{semana}"
    df = pd.DataFrame(
        [{"id": l["id"], "Ejercicio": l["ejercicio"], col: prescripcion_semana(l, semana, rut.get("ajustes"))[0],
          "Sube (kg)": float(l.get("sube") or 0), "Nota": l.get("nota", "")} for l in dia["lineas"]],
        columns=["id", "Ejercicio", col, "Sube (kg)", "Nota"],
    )
    nombre = st.text_input("Nombre del día", dia["nombre"], key=f"nom_{base}")
    tabla = st.data_editor(
        df, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"edr_{base}",
        column_order=["Ejercicio", col, "Sube (kg)", "Nota"],
        column_config={
            "Ejercicio": st.column_config.TextColumn(width="medium"),
            col: st.column_config.TextColumn(help="Series, reps y peso tras @: 3x3 @50, 3@40 2@45 1@50, 10 @25"),
            "Sube (kg)": st.column_config.NumberColumn(min_value=0.0, step=1.25, default=2.5, format="%.2f",
                                                       help="Kg que sube cada semana. 0 = no sube"),
            "Nota": st.column_config.TextColumn(),
        },
    )
    st.caption("Escribe el peso tras una @ para que suba solo. Para WOD o conditioning deja «Sube» en 0.")
    modo = st.radio("Si cambias un peso, aplicarlo a…", ["Esta semana y las siguientes", "Solo esta semana"],
                    horizontal=True, key=f"modo_{base}")
    b1, b2 = st.columns(2)
    if b1.button("Guardar cambios", type="primary", key=f"save_{base}", use_container_width=True):
        filas = [{"id": r.get("id"), "ejercicio": r.get("Ejercicio"), "presc": r.get(col),
                  "sube": r.get("Sube (kg)"), "nota": r.get("Nota")} for r in tabla.to_dict("records")]
        nueva = aplicar_edicion(rut, dia["id"], filas, semana, modo == "Solo esta semana", _nuevo_id)
        for d in nueva["dias"]:
            if d["id"] == dia["id"]:
                d["nombre"] = nombre.strip() or d["nombre"]
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


# ---------------------------------------------------------------- main
def main():
    control_contrasena()
    st.markdown("""<style>
      h1 {letter-spacing:.02em; text-transform:uppercase}
      [data-testid="stMetricValue"] {font-variant-numeric: tabular-nums}
    </style>""", unsafe_allow_html=True)
    st.title("Diario de Entrenos")

    if isinstance(store(), LocalStore):
        st.caption("Modo local: los datos se guardan en la carpeta `data/`. Configura Supabase para usarla online.")

    atleta = st.segmented_control("Atleta", ATLETAS, default=ATLETAS[0], key="atleta", label_visibility="collapsed")
    atleta = atleta or ATLETAS[0]

    if aviso := st.session_state.pop("aviso", None):
        st.toast(aviso)

    try:
        todos = cargar_todo()
    except Exception as ex:
        st.error(f"No se pudieron cargar los datos: {ex}")
        st.stop()
    mios = [w for w in todos if w["athlete"] == atleta]

    t0, t1, t2, t3, t4 = st.tabs(["Rutina", "Registrar", "Historial", "Progreso", "Grupo"])
    with t0:
        tab_rutina(atleta, mios)
    with t1:
        tab_registrar(atleta, mios)
    with t2:
        tab_historial(atleta, mios)
    with t3:
        tab_progreso(atleta, mios)
    with t4:
        tab_grupo(todos)


main()
