# Djimenez Prog · app nueva (web)

Carpeta `web/` del repositorio. Usa los mismos datos de Supabase que la app de Streamlit,
así que puedes usar las dos a la vez.

- `index.html`, `app.js`, `estilo.css`: lo que se ve.
- `api/index.py`: el servidor (Vercel lo ejecuta solo).
- `motor/`: la lógica. `logica.py`, `rutinas_iniciales.py`, `repertorio.py` y `ciclos.py` son
  **copias** de los de la raíz: si cambias uno allí, cópialo también aquí.
- Las claves NO van aquí: van en Vercel → Settings → Environment Variables.

Variables: `SUPABASE_URL`, `SUPABASE_KEY`, `APP_PASSWORD`, `CONTRASENA_ARCHCHANA`,
`CONTRASENA_INVITADOS`, opcionales `APP_ANTIGUA_URL` y `ACCESOS_PERSONALES` (JSON).
