"""PRUEBA FINAL ÚNICA de VESUVIO congelado: 2024-01-01 → hoy (nunca usado en el diseño).
Comparado con: CRIPTO20 tal como opera hoy (lista fija, 0,40 %, banda 25 %), PRINCIPAL (BTC+ETH) y comprar y mantener BTC.
Incluye Sharpe deflactado del periodo de diseño (34 variantes).
Uso: python exp_final.py ../experimentos/final"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
import universe as U
BASE20 = list(U.CRYPTO)
from vesuvio_base import preparar
from vesuvio_estrategia import pesos
import trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
P, CR = preparar(fin=None)
end = str(P.cal[-1].date())
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
Wv, _ = pesos(P, CR)
# referencias (sin universo dinámico): CRIPTO20 actual, PRINCIPAL, BTC comprar y mantener
import panel
P20 = panel.build(end=None)
W20 = full(TR.base_trades(P20, [t for t in BASE20 if t in P20.tradable], N=55, long_only=True, risk=0.01)[0])
Wpr = full(TR.base_trades(P20, ["BTC-USD", "ETH-USD"], N=55, long_only=True, risk=0.03, cap=1.0)[0])
Wbh = full(pd.DataFrame({"BTC-USD": 1.0}, index=P20.cal))
filas, navs = [], {}
def corre(nombre, Pp, W, cfg, ini, fin):
    BT.COST.update(**cfg)
    r = BT.run(Pp, W, ini, fin, capital=10_000.0, record_trades=True)
    s = M.stats(r)
    filas.append(dict(estrategia=nombre, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
    return r
VES = dict(max_gross=1.0, comm_crypto=0.0025, min_trade_eur=50.0, rel_band=0.5)
C20 = dict(max_gross=1.0, comm_crypto=0.004, min_trade_eur=50.0, rel_band=0.25)
for ini, fin in (("2024-01-01", end), ("2018-01-01", "2023-12-31")):
    navs_p = {}
    navs_p["VESUVIO"] = corre("VESUVIO", P, Wv, VES, ini, fin).nav
    navs_p["CRIPTO20_actual"] = corre("CRIPTO20_actual", P20, W20, C20, ini, fin).nav
    navs_p["PRINCIPAL"] = corre("PRINCIPAL", P20, Wpr, C20, ini, fin).nav
    navs_p["BTC_mantener"] = corre("BTC_mantener", P20, Wbh, C20, ini, fin).nav
    if ini == "2024-01-01": navs = navs_p
BT.COST.update(**VES)
rd = BT.run(P, Wv, "2018-01-01", "2023-12-31", capital=10_000.0).ret
dsr = M.deflated_sharpe(rd, n_trials=34)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
pd.DataFrame(navs).resample("W").last().to_csv(out / "nav_semanal_2024.csv")
an = pd.DataFrame({k: v.resample("YE").last() for k, v in navs.items()})
an = pd.concat([pd.DataFrame({k: [10000.0] for k in navs}, index=[pd.Timestamp("2023-12-31")]), an]).pct_change().dropna()
an.index = an.index.year; an.round(4).to_csv(out / "por_anio_2024.csv")
print("datos hasta", end, "| Sharpe deflactado (prob. de ventaja real, diseño, 34 ensayos):", round(float(dsr), 3))
print(tab[["estrategia", "periodo", "CAGR", "Vol", "Sharpe", "MaxDD", "CostesAnualPct", "Gross", "ops"]].to_string(index=False))
print(an.round(3).to_string())
