"""VESUVIO palanca 3 — varias escalas de tendencia. Referencia: ruptura 55 (top-25 dinámico). SOLO diseño 2018-2023.
Variantes: 55 sola / media de 20+55+100 / media de 55+100 / media de 20+55.
Uso: python exp_v3_horizontes.py ../experimentos/v3_horizontes"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
from vesuvio_base import preparar, PERIODOS
import trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
P, CR = preparar()
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
Wn = {n: full(TR.base_trades(P, CR, N=n, long_only=True, risk=0.01, max_units=3)[0]) for n in (20, 55, 100)}
var = {"55": Wn[55], "20+55+100": (Wn[20] + Wn[55] + Wn[100]) / 3, "55+100": (Wn[55] + Wn[100]) / 2, "20+55": (Wn[20] + Wn[55]) / 2}
filas = []
for k, W in var.items():
    for ini, fin in PERIODOS:
        r = BT.run(P, W, ini, fin, capital=10_000.0, record_trades=True)
        s = M.stats(r)
        filas.append(dict(variante=k, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
print(tab[["variante", "periodo", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "Gross", "ops"]].to_string(index=False))
