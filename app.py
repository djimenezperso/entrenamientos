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
    MENOS_ES_MEJOR, TIPOS, UNIDADES, a_fecha, cambio_pct, consejos, fmt_tiempo, fmt_valor,
    ids_con_pr, mejor_punto, norm, parse_tiempo, parse_valor, series_ejercicios, sesiones_por_semana,
)

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
def tab_registrar(atleta: str, entrenos: list[dict]):
    n = st.session_state.setdefault(f"form_n_{atleta}", 0)
    usados = sorted({e["name"].strip() for w in entrenos for e in (w.get("entries") or []) if e.get("name")}, key=str.lower)

    with st.form(f"nuevo_{atleta}_{n}"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", list(TIPOS), format_func=lambda k: TIPOS[k][0])
        fecha = c2.date_input("Fecha", dt.date.today(), format="DD/MM/YYYY")
        c3, c4 = st.columns([2, 1])
        titulo = c3.text_input("Título", placeholder="Fran, Pierna, 10K suave…")
        duracion = c4.text_input("Duración total", placeholder="h:mm:ss o min")

        st.markdown("**Resultados**")
        tabla = st.data_editor(
            pd.DataFrame({"Ejercicio": [""] * 3, "Resultado": [""] * 3, "Unidad": ["tiempo"] * 3}),
            num_rows="dynamic", hide_index=True, use_container_width=True, key=f"tabla_{atleta}_{n}",
            column_config={
                "Ejercicio": st.column_config.TextColumn(width="medium"),
                "Resultado": st.column_config.TextColumn(help="Tiempo como 4:35 o 1:02:10; el resto, un número"),
                "Unidad": st.column_config.SelectboxColumn(options=UNIDADES, required=True),
            },
        )
        st.caption("Tiempo como 4:35 o 1:02:10. Escribe cada ejercicio siempre igual para seguir su progresión."
                   + (f" Ya usados: {', '.join(usados[:12])}." if usados else ""))
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
    st.session_state[f"form_n_{atleta}"] = n + 1
    st.session_state["aviso"] = "Entreno guardado"
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

    t1, t2, t3, t4 = st.tabs(["Registrar", "Historial", "Progreso", "Grupo"])
    with t1:
        tab_registrar(atleta, mios)
    with t2:
        tab_historial(atleta, mios)
    with t3:
        tab_progreso(atleta, mios)
    with t4:
        tab_grupo(todos)


main()
