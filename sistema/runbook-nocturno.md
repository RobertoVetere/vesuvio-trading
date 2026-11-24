# Runbook nocturno (Claude, 22:15 Europe/Madrid)

Sigue los pasos en orden. Si un paso falla: escribe `estado/ultima_ejecucion.json` con `ok: false`, `paso` y `motivo`, haz commit, abre/actualiza un issue `fallo` y PARA. No inventes nada.

1. **Sincroniza**: `git pull`. Lee `estado/ultima_ejecucion.json`.
2. **Comprueba datos**: `datos/meta.json` debe tener `fecha` = último día hábil y `fallidos` vacío o < 10 %. Si no → fallo.
3. **Noticias**: busca noticias relevantes de los activos en posición y en oportunidades (las 10 más cercanas a ruptura). Añádelas a `noticias/noticias.csv` sin duplicar.
4. **Overlay**: escribe `estado/overlay.json` (solo reducir riesgo en PRINCIPAL_CLAUDE). Cada veto con `activo`, `accion` (vetar_entrada | reducir | cerrar) y `motivo` en una frase.
5. **Simulación**: `python3 codigo/paper.py estado/state.json estado/overlay.json out` y después el adaptador a `estado/publico/`.
6. **MI_PRACTICA**: procesa issues abiertos con etiqueta `operacion`; actualiza `estado/mi_practica.json`; responde en cada issue.
7. **Preguntas**: contesta issues con etiqueta `pregunta` y ciérralos.
8. **Diario**: `diario/AAAA-MM-DD.md` con: qué hizo cada estrategia y por qué · noticias clave · vetos · MI_PRACTICA · **Lección del día** (un concepto para principiante, que no esté en `diario/lecciones.json`; añádelo allí). Actualiza `diario/indice.json`.
9. **Cierre**: `estado/ultima_ejecucion.json` con `ok: true`, fecha y resumen de 1 línea. Commit `noche AAAA-MM-DD: …` y push. Verifica que el push entró.
