"""Experimento: stop al cierre (actual) + RED de seguridad en el exchange contra desplomes (5/6/8 x vol).
Condiciones Kraken al contado (sin apalancamiento, 0,40 %), universo con monedas muertas.
Uso: python exp_red.py ../experimentos/red"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
import universe as U
from exp_cripto_muertas import MUERTAS_OK
U.CRYPTO.extend(MUERTAS_OK)
import panel, trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
P = panel.build(); end = str(P.cal[-1].date())
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
CR = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
BT.COST.update(max_gross=1.0, comm_crypto=0.004, min_trade_eur=50.0)
defs = {"PRINCIPAL": dict(assets=["BTC-USD", "ETH-USD"], risk=0.03, cap=1.0), "CRIPTO_TREND_1%": dict(assets=CR, risk=0.01, cap=0.25)}
filas, anual, peores = [], {}, {}
for nombre, d in defs.items():
    for red in (None, 5.0, 6.0, 8.0):
        so = {} if red else None
        W, T = TR.base_trades(P, d["assets"], N=55, long_only=True, risk=d["risk"], cap=d["cap"], stop_mult=3.0,
                              intraday=bool(red), stops_out=so, red_mult=red)
        S = pd.DataFrame(so) if so else None
        modo = f"red_{red:.0f}x" if red else "solo_cierre"
        for ini in ("2018-01-01", "2022-01-01", "2023-01-01"):
            r = BT.run(P, full(W), ini, end, capital=10_000.0, stops=S, record_trades=True)
            s = M.stats(r)
            filas.append(dict(estrategia=nombre, modo=modo, desde=ini, operaciones=len(r.attrs["trades"]), peor_dia=round(float(r.ret.min()), 4),
                              **{c: round(float(v), 4) for c, v in s.items()}))
            if ini == "2018-01-01":
                y = r.nav.resample("YE").last(); y = pd.concat([pd.Series([10000.0], [y.index[0] - pd.offsets.YearEnd()]), y]).pct_change().dropna()
                anual[f"{nombre}|{modo}"] = y.set_axis(y.index.year)
        # peor operación individual (protección contra desplomes)
        peores[f"{nombre}|{modo}"] = round(float(T.ret.min()), 3)
        print("hecho", nombre, modo, flush=True)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
pd.DataFrame(anual).round(4).to_csv(out / "por_anio.csv")
print(tab[["estrategia", "modo", "desde", "CAGR", "Sharpe", "MaxDD", "peor_dia", "CostesAnualPct", "operaciones"]].to_string(index=False))
print("peor operación individual:", peores)
print(pd.DataFrame(anual).round(3).to_string())
