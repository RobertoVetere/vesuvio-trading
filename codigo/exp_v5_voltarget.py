"""VESUVIO palanca 5 — objetivo de volatilidad de cartera (usa el capital ocioso). SOLO diseño 2018-2023.
Volatilidad estimada con los pesos de hoy aplicados a los 60 días anteriores (sin mirar el futuro).
Factor = objetivo / vol estimada, limitado a [0,25 ; 3] y a exposición total <= 1 (contado, sin apalancamiento).
Variantes: ref (palancas 1-4) / objetivo 20 % / 30 % / 40 % anual.
Uso: python exp_v5_voltarget.py ../experimentos/v5_voltarget"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
from vesuvio_base import preparar, PERIODOS
from vesuvio_estrategia import pesos
import backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
P, CR = preparar()
W, _ = pesos(P, CR)
R = P.R.reindex(columns=W.columns).fillna(0.0).values
Wv = W.values
vol = np.full(len(W), np.nan)
for i in range(60, len(W)):
    pr = R[i - 59:i + 1] @ Wv[i]
    vol[i] = pr.std() * np.sqrt(365)
vol = pd.Series(vol, W.index)
gross = W.abs().sum(axis=1)
def objetivo(t):
    f = (t / vol).clip(0.25, 3.0).fillna(1.0)
    f = np.minimum(f, (1.0 / gross.replace(0, np.nan)).fillna(3.0))
    return W.mul(f, axis=0)
var = {"ref": W, "vol_20%": objetivo(0.20), "vol_30%": objetivo(0.30), "vol_40%": objetivo(0.40)}
filas = []
for k, w in var.items():
    for ini, fin in PERIODOS:
        r = BT.run(P, w, ini, fin, capital=10_000.0, record_trades=True)
        s = M.stats(r)
        filas.append(dict(variante=k, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
print("vol estimada ref (mediana):", round(float(vol.loc["2018":"2023"].median()), 3))
print(tab[["variante", "periodo", "CAGR", "Vol", "Sharpe", "MaxDD", "CostesAnualPct", "Gross", "ops"]].to_string(index=False))
