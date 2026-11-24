# vesuvio-trading — instrucciones para Claude

Experimento de trading sistemático de Roberto. Claude lo opera cada noche; Roberto aprende leyendo el diario y el dashboard.
**Todo en español. Si algo falla (datos, push, repo), PARA y explícalo. Nunca inventes resultados.**

## Lee esto primero
1. `sistema/manifiesto.json` — mapa completo: qué fichero hace qué, horarios, contratos de datos, fallos conocidos.
2. `estado/ultima_ejecucion.json` — qué pasó en la última ejecución y si quedó algo a medias.
3. `sistema/runbook-nocturno.md` — los pasos exactos de la ejecución nocturna.

## Reparto de trabajo (no lo cambies sin que Roberto lo pida)
- **GitHub Actions** hace lo mecánico: descargar Yahoo y ejecutar `paper.py` (workflow `noche.yml`; desde el entorno de Claude Yahoo devuelve 429), validar ficheros, vigilar que la noche ocurrió.
- **Claude** hace lo que requiere criterio: noticias, `overlay.json`, lanzar `noche.yml` y leer sus resultados, cartera MI_PRACTICA, issues, diario.
- **Vercel** sirve el dashboard (`dashboard/`) con los ficheros de `estado/publico/` y `diario/`.
- **Ejecución con dinero real**: solo la hace el ejecutor (`ejecutor/`, fase 2+), código fijo con límites duros, claves en GitHub Secrets. Claude NUNCA tiene claves ni manda órdenes; solo escribe `estado/ordenes_propuestas.json`.

## Reglas duras
- `overlay.json` solo puede REDUCIR riesgo en PRINCIPAL_CLAUDE (vetar entradas, reducir tamaño, cerrar). Nunca añadir riesgo.
- No reescribas `estado/state.json` a mano: solo lo modifica `paper.py`.
- Si los datos del día no están o están incompletos (ver `datos/meta.json`), no ejecutes `paper.py`: abre/actualiza el issue `fallo` y para.
- Cada ejecución termina escribiendo `estado/ultima_ejecucion.json` (aunque falle, con `ok: false` y el motivo).
- No gastes tokens: no leas CSV enteros si basta con `tail`; no regeneres el dashboard salvo que se pida.
- Commits con mensaje `noche AAAA-MM-DD: …` o `fix: …`.

## Ejecución real (fase 2+): obligatorio
- Stop normal: se evalúa al cierre diario (medido: los stops intradía empeoran por las mechas, ver experimentos/stops).
- Además, toda posición real lleva una **red de seguridad como orden de stop en el exchange a 8x vol** (`red_mult=8`), colocada en el mismo ciclo en que se abre, contra desplomes extremos.
- Si no se puede colocar la red, se cierra la posición y se abre un issue `fallo`.
- Entradas con órdenes limitadas (creador) salvo salidas por stop.

## Issues
- Etiqueta `operacion`: Roberto propone una operación para MI_PRACTICA → simular, responder con feedback (tamaño, stop, encaje con la estrategia, qué habría hecho Claude), cerrar o dejar abierta.
- Etiqueta `pregunta`: contestar en español, nivel principiante, y cerrar.
- Etiqueta `fallo`: la abre la vigilancia de Actions; la tarea de la mañana la resuelve o la explica.
