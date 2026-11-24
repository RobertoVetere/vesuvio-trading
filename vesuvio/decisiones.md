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

## Palanca 2 — universo (experimentos/v2_universo, v2b_topn) — 2026-11-24
Ensayos: 6 + 3 = 9 (acumulado: 21).
- Universo amplio (~37 operables): mejor en 2018-20 (1,46) pero peor en 2022-23 (0,53, MaxDD -49 %). NO adoptado.
- Liquidez mínima 50M €: peor en todo. Se mantiene 20M €.
- **HALLAZGO:** la base (20 actuales + muertas elegidas a mano) tiene sesgo de selección: ninguna regla implementable alcanza su 0,87 en 2022-23.
- Universo dinámico top-N por liquidez (implementable en real): N=15: 1,03/1,04/0,25 · **N=25: 1,31/1,24/0,58** · N=35: 1,56/1,46/0,48.
**ADOPTADO:** universo dinámico = las 25 criptos más líquidas cada día (≥20M €/día) entre todas las candidatas. **Nueva referencia honesta: Sharpe 1,31 / 1,24 / 0,58, MaxDD -42 %.**
