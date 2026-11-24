# Runbook nocturno (Claude, 01:10 Europe/Madrid — la vela cripto del día cierra a las 00:00 UTC)

En orden. Si un paso falla: `estado/ultima_ejecucion.json` con `ok:false`, `paso`, `motivo`; commit; issue `fallo`; PARA. No inventes nada.

1. **Sincroniza**: `git pull`. Lee `estado/ultima_ejecucion.json` y `estado/publico/ejecucion.json`.
2. **Contexto barato**: `estado/publico/oportunidades.csv` (top 10 por `distancia_ruptura`) y `posiciones.csv` de PRINCIPAL/PRINCIPAL_CLAUDE. No leas nav.csv entero.
3. **Noticias**: busca (pocas búsquedas) noticias de BTC/ETH, cripto en general y lo que esté cerca de ruptura. Añade 2-5 filas a `noticias/noticias.csv` (`fecha,tema,lectura,accion`).
4. **Overlay**: `estado/overlay.json` = `[]` o vetos `{"asset","accion":"veto_entrada"|"salir","motivo"}`. Solo reducir riesgo. Un veto necesita un motivo concreto (evento, no "volatilidad").
5. **Push + lanzar**: commit `noche AAAA-MM-DD: overlay y noticias`, push, `gh workflow run noche.yml -R RobertoVetere/vesuvio-trading`.
6. **Esperar**: `gh run list -w noche.yml -L 1 --json status,conclusion,databaseId` cada ~60 s (máx. 40 min). Si `failure` → paso de fallo con el enlace al run.
7. **Resultados**: `git pull`; lee `estado/publico/ejecucion.json`, `resumen.csv`, `operaciones.csv` (solo filas de hoy/ayer) y `estado/ejecutor/ultimo.json` (órdenes del ejecutor, avisos, modo). Inclúyelo en el diario en una sección `## Ejecutor Kraken`; si hay avisos u `ok:false`, explícalos.
8. **MI_PRACTICA**: issues abiertos con etiqueta `operacion` → simula con el precio de cierre de `datos_hasta` (gh api o el último precio en oportunidades si aplica; si no tienes precio fiable, dilo en el issue y no simules). Actualiza `estado/mi_practica.json`, responde con feedback (tamaño, stop, encaje con la estrategia, qué habría hecho Claude), cierra si la operación queda completa.
9. **Preguntas**: issues `pregunta` → responde (principiante) y cierra.
10. **Diario** `diario/<decision>.md` (fecha `decision` de ejecucion.json): `# AAAA-MM-DD` · `## Qué hizo cada estrategia` (PRINCIPAL, PRINCIPAL_CLAUDE, CRIPTO20, PILOTO, MI_PRACTICA: valor, cambio, operaciones y por qué según el sistema) · `## Noticias clave` · `## Mis vetos` · `### Lección del día` (un concepto, no repetido en `diario/lecciones.json`; añádelo). Añade la fecha al principio de `diario/indice.json`.
11. **Cierre**: `estado/ultima_ejecucion.json` = `{"fecha","ok":true,"resumen":"1 línea"}`; commit `noche AAAA-MM-DD: diario`; push; comprueba que entró (`git status -sb`).
