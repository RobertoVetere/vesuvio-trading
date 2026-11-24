"""VESUVIO palanca 1 — costes. SOLO periodo de diseño (2018-2023); 2024-2026 reservado para la prueba final.
CRIPTO_TREND riesgo 1 %, universo con muertas, Kraken al contado (sin apalancamiento), stop al cierre.
Ejes: comisión (0,40 % tomador / 0,25 % creador) x banda de no-reajuste (25 % / 50 % / solo entradas y salidas)
x piramidar (hasta 3 unidades / 1 unidad).
Uso: python exp_v1_costes.py ../experimentos/v1_costes"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
import universe as U
from exp_cripto_muertas import MUERTAS_OK
U.CRYPTO.extend(MUERTAS_OK)
import panel, trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
FIN_DISENO = "2023-12-31"
P = panel.build(end=FIN_DISENO)
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
CR = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
filas = []
for mu in (3, 1):
    W, _ = TR.base_trades(P, CR, N=55, long_only=True, risk=0.01, max_units=mu)
    W = full(W)
    for com in (0.004, 0.0025):
        for banda in (0.25, 0.5, 10.0):  # 10 = nunca reajusta tamaño: solo entra, sale o invierte
            BT.COST.update(max_gross=1.0, comm_crypto=com, min_trade_eur=50.0, rel_band=banda)
            for ini, fin in (("2018-01-01", FIN_DISENO), ("2018-01-01", "2020-12-31"), ("2022-01-01", FIN_DISENO)):
                r = BT.run(P, W, ini, fin, capital=10_000.0, record_trades=True)
                s = M.stats(r)
                filas.append(dict(unidades=mu, comision=com, banda=banda, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]),
                                  **{c: round(float(v), 4) for c, v in s.items()}))
    print("hecho unidades", mu, flush=True)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
print(tab[["unidades", "comision", "banda", "periodo", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "ops"]].to_string(index=False))
