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

## Palanca 3 — varias escalas (experimentos/v3_horizontes) — 2026-11-24
Ensayos: 3 (acumulado: 24). 20+55+100: 1,23/1,19/0,14 · 55+100: 1,14/1,04/0,20 · 20+55: 1,24/1,23/0,18 (ref. 55: 1,31/1,24/0,58).
**NO adoptado.** Se mantiene ruptura de 55 días.

## Palanca 4 — régimen BTC vs media 200 d (experimentos/v4_regimen) — 2026-11-24
Ensayos: 4 (acumulado: 28). Días bajistas 2018-23: 50 %.
| Variante | 18-23 | 18-20 | 22-23 | MaxDD |
|---|---|---|---|---|
| ref | 1,31 | 1,24 | 0,58 | -42 % |
| largos x0 en bajista | 1,13 | 0,90 | 0,89 | -45 % |
| largos x0,5 | 1,26 | 1,15 | 0,57 | -44 % |
| x0 + cortos BTC/ETH | 1,21 | 1,11 | 1,12 | -46 % |
| **x0,5 + cortos BTC/ETH** | **1,33** | **1,33** | **0,86** | -44 % |
**ADOPTADO:** en bajista (BTC < media 200 d) largos al 50 % + cortos BTC/ETH (ruptura 55, riesgo 2 %, tope 50 %). Requiere futuros de Kraken.

## Palanca 5 — objetivo de volatilidad (experimentos/v5_voltarget) — 2026-11-24
Ensayos: 3 (acumulado: 31). ref 1,33/1,33/0,86 MaxDD -44 % · vol 20 %: 1,16/1,27/0,85 MaxDD -26 % · vol 30 %: 1,20/1,35/0,87 MaxDD -35 % · vol 40 %: 1,26/1,45/0,93 MaxDD -41 %.
**NO adoptado como ventaja** (empeora 2018-23 por recortar en la manía de 2021). **Opción de riesgo para Roberto:** objetivo 20 % casi divide por dos la caída máxima a cambio de ~mitad de rentabilidad.
