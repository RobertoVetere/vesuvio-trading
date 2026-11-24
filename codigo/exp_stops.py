"""Experimento: stops al cierre (sistema actual) vs stops como orden en el exchange (intradía).
Condiciones Kraken al contado: sin apalancamiento, comisión 0,40 %, solo largos, universo con monedas muertas.
Distancia de stop 2/3/4 x volatilidad (3 = sistema actual; 2 y 4 solo como sensibilidad).
Uso: python exp_stops.py ../experimentos/stops"""
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
defs = {"PRINCIPAL": dict(assets=["BTC-USD", "ETH-USD"], risk=0.03, cap=1.0),
        "CRIPTO_TREND_1%": dict(assets=CR, risk=0.01), "CRIPTO_TREND_2%": dict(assets=CR, risk=0.02)}
filas, anual, nstops = [], {}, {}
for nombre, d in defs.items():
    for k in (2.0, 3.0, 4.0):
        for modo in ("cierre", "exchange"):
            so = {} if modo == "exchange" else None
            W, T = TR.base_trades(P, d["assets"], N=55, long_only=True, risk=d["risk"], cap=d.get("cap", 0.25),
                                  stop_mult=k, intraday=(modo == "exchange"), stops_out=so)
            S = pd.DataFrame(so) if so else None
            for ini in ("2018-01-01", "2022-01-01", "2023-01-01"):
                r = BT.run(P, full(W), ini, end, capital=10_000.0, stops=S, record_trades=True)
                s = M.stats(r)
                filas.append(dict(estrategia=nombre, stop_x_vol=k, stop=modo, desde=ini, operaciones=len(r.attrs["trades"]),
                                  **{c: round(float(v), 4) for c, v in s.items()}))
                if ini == "2018-01-01" and k == 3.0:
                    y = r.nav.resample("YE").last(); y = pd.concat([pd.Series([10000.0], [y.index[0] - pd.offsets.YearEnd()]), y]).pct_change().dropna()
                    anual[f"{nombre}|{modo}"] = y.set_axis(y.index.year)
            print("hecho", nombre, k, modo, flush=True)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
pd.DataFrame(anual).round(4).to_csv(out / "por_anio.csv")
print(tab[["estrategia", "stop_x_vol", "stop", "desde", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "operaciones"]].to_string(index=False))
print(pd.DataFrame(anual).round(3).to_string())
