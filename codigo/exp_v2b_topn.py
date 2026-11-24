"""VESUVIO palanca 2b — universo dinámico implementable: cada día, las N criptos más líquidas (volumen 20 d en €)
entre todas las candidatas (actuales + muertas + amplio), con liquidez >= 20M €. SOLO diseño 2018-2023.
Uso: python exp_v2b_topn.py ../experimentos/v2b_topn"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
import universe as U
from exp_cripto_muertas import MUERTAS_OK
from exp_cripto_amplio import EXTRA_OK
U.CRYPTO.extend(MUERTAS_OK + EXTRA_OK)
import panel, trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
FIN = "2023-12-31"
P = panel.build(end=FIN)
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
CR = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
dv = (P.wide("_dv20", P.tradable) * P.FX)[CR]
base_elig = P.elig.copy()
filas = []
for N in (15, 25, 35):
    rank = dv.where(base_elig[CR]).rank(axis=1, ascending=False)
    P.elig = base_elig.copy(); P.elig[CR] = base_elig[CR] & (rank <= N)
    W, _ = TR.base_trades(P, CR, N=55, long_only=True, risk=0.01, max_units=3)
    BT.COST.update(max_gross=1.0, comm_crypto=0.0025, min_trade_eur=50.0, rel_band=0.5)
    for ini, fin in (("2018-01-01", FIN), ("2018-01-01", "2020-12-31"), ("2022-01-01", FIN)):
        r = BT.run(P, full(W), ini, fin, capital=10_000.0, record_trades=True)
        s = M.stats(r)
        filas.append(dict(topN=N, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
    print("hecho", N, flush=True)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
print(tab[["topN", "periodo", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "Gross", "ops"]].to_string(index=False))
