# Diario de Entrenos (Streamlit)

App para guardar entrenos de fuerza, WOD, gym y endurance con foto, tiempos y notas, ver la progresión de cada ejercicio y saber dónde mejorar. Tiene un apartado por persona (Yo, Manu Anel, Salatti y Mi esposa) y una pestaña **Grupo** para compararos.

## Archivos

| Archivo | Qué es |
|---|---|
| `app.py` | La app |
| `logica.py` | Cálculo de tiempos, marcas, progresión y consejos |
| `requirements.txt` | Librerías que instala Streamlit Cloud |
| `schema.sql` | Tabla y bucket de fotos para Supabase |
| `.streamlit/config.toml` | Colores y límite de subida |
| `.streamlit/secrets.toml.example` | Plantilla de claves (no se sube con datos reales) |

Para cambiar los nombres, edita la lista `ATLETAS` al principio de `app.py`.

## 1. Probar en tu ordenador (opcional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Sin claves de Supabase, los datos se guardan en la carpeta `data/`.

## 2. Crear la base de datos en Supabase (gratis)

Streamlit Cloud borra los archivos cada vez que la app se reinicia, así que los entrenos y las fotos se guardan en Supabase.

1. Crea una cuenta y un proyecto en supabase.com.
2. Ve a **SQL Editor**, pega el contenido de `schema.sql` y pulsa **Run**.
3. En **Project Settings → API** copia la **Project URL** y la **service_role key**.

La service_role key solo va en los secrets de Streamlit, que se quedan en el servidor. No la pongas en el código ni en GitHub.

## 3. Subirla a Streamlit Cloud

1. Sube esta carpeta a un repositorio de GitHub (puede ser privado).
2. Entra en share.streamlit.io, pulsa **Create app** y elige el repositorio, la rama y `app.py`.
3. En **Advanced settings → Secrets** pega esto con tus datos:

```toml
APP_PASSWORD = "una-contraseña-para-los-cuatro"

[supabase]
url = "https://TU-PROYECTO.supabase.co"
key = "TU_SERVICE_ROLE_KEY"
```

4. Pulsa **Deploy** y comparte el enlace con Manu, Salatti y tu esposa.

`APP_PASSWORD` es opcional, pero sin ella cualquiera con el enlace puede ver y borrar entrenos.

## Cómo apuntar los resultados

- Tiempos como `4:35` o `1:02:10`. Un número solo en "Duración total" se toma como minutos.
- Peso, reps, km, metros, calorías o rondas como número (`67,5` vale).
- Escribe cada ejercicio siempre igual ("Sentadilla trasera", "Fran") para que la app junte los registros y dibuje la progresión. En la pestaña **Grupo** se comparan los ejercicios que dos o más hayáis escrito igual.
