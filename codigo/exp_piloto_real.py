"""Experimento: ¿sobrevive PILOTO a las restricciones reales de un particular en España (IBKR)?
Variantes (misma lógica de decisión que paper.py; solo cambian ejecución y costes):
  ORIGINAL        : como en paper.py
  IBKR_CFD        : ETF de EEUU vía CFD (financiación de largos ETF 3,5 %/año neto); resto igual
  IBKR_SIN_CR_CORTO: IBKR_CFD sin cortos en cripto (cripto solo largos)
  IBKR_SIN_CRIPTO : IBKR_CFD sin nada de cripto
Uso (desde codigo/): python exp_piloto_real.py ../experimentos/piloto_real"""
import sys, json, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
import panel, trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
P = panel.build(); end = str(P.cal[-1].date())
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
BT.COST["max_gross"] = 2.0; BT.COST["min_trade_eur"] = 300.0
a = [t for t in P.tradable if P.cls[t] in ("ETF", "CRYPTO")]; au = a + [t for t in P.tradable if P.cls[t] == "US"]
V = {}
for N in (20, 55):
    V[f"T{N}"] = TR.base_trades(P, a, N=N); V[f"T{N}_KONK"] = TR.base_trades(P, a, N=N, konk=True)
var = {k: full(w) for k, (w, t) in V.items()}
for k in ["T20", "T55", "T55_KONK"]:
    var[k + "_META"] = full(TR.meta_filter(P, *V[k])[0])
var["T55_META_CONUS"] = full(TR.meta_filter(P, *TR.base_trades(P, au, N=55))[0])
R = {k: BT.run(P, w, "2010-01-01", end).ret for k, w in var.items()}
W, picks = TR.autopilot(P, var, R)
cr = np.array([P.cls[t] == "CRYPTO" for t in P.tradable]); etf = np.array([P.cls[t] == "ETF" for t in P.tradable])
lf = np.where(etf, 0.035, 0.0)
W_noshort = W.copy(); W_noshort.loc[:, cr] = W_noshort.loc[:, cr].clip(lower=0)
W_nocr = W.copy(); W_nocr.loc[:, cr] = 0.0
casos = {"ORIGINAL": (W, None), "IBKR_CFD": (W, lf), "IBKR_SIN_CR_CORTO": (W_noshort, lf), "IBKR_SIN_CRIPTO": (W_nocr, lf)}
filas, navs = [], {}
for nombre, (w, f) in casos.items():
    for ini in ("2014-01-01", "2023-01-01"):
        r = BT.run(P, w, ini, end, capital=10_000.0, long_fin=f)
        s = M.stats(r); filas.append(dict(variante=nombre, desde=ini, **{k: round(float(v), 4) for k, v in s.items()}))
        if ini == "2014-01-01": navs[nombre] = r.nav
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
pd.DataFrame(navs).resample("W").last().to_csv(out / "nav_semanal.csv")
anual = pd.DataFrame({k: v.resample("YE").last().pct_change() for k, v in navs.items()}); anual.index = anual.index.year
anual.round(4).to_csv(out / "por_anio.csv")
json.dump(dict(datos_hasta=end, elecciones=picks), open(out / "meta.json", "w"), default=str, indent=1)
print(tab[["variante", "desde", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "Gross"]].to_string(index=False))
print(anual.round(3).to_string())
