# VESUVIO — registro de decisiones

Reglas: diseño solo con 2018-01-01 → 2023-12-31. 2024-2026 reservado para UNA prueba final.
Una palanca se adopta solo si mejora el Sharpe en los tres subperiodos (2018-2023, 2018-2020, 2022-2023).
Base de partida: CRIPTO_TREND (ruptura 55, solo largos, riesgo 1 %, hasta 3 unidades), Kraken al contado, comisión 0,40 %, banda 25 %, stop al cierre.

## Palanca 1 — costes (experimentos/v1_costes) — 2026-11-24
Ensayos: 2 (unidades) x 2 (comisión) x 3 (banda) = 12.
| Configuración | Sharpe 18-23 | 18-20 | 22-23 | MaxDD 18-23 | Costes/año |
|---|---|---|---|---|---|
| Base (3 ud, 0,40 %, banda 25 %) | 1,57 | 1,22 | 0,60 | -41 % | 18,3 % |
| Banda 50 % | 1,65 | 1,26 | 0,78 | -30 % | 15,2 % |
| **Banda 50 % + órdenes de creador (0,25 %)** | **1,72** | **1,31** | **0,87** | **-29 %** | **11,8 %** |
| 1 unidad (sin piramidar) | peor en todos | | | | |
| Sin reajustes (solo entrar/salir) | peor en todos | | | | |
**ADOPTADO:** banda de no-reajuste 50 % + entradas con órdenes limitadas (creador). Se mantiene piramidar hasta 3 unidades.
