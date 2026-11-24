"""Experimento: estrategias cripto con condiciones REALES de Kraken al contado.
- Sin apalancamiento (max_gross 1.0), solo largos.
- Comisión 0,40 % (tomador Kraken Pro, volumen bajo) y 0,25 % (creador), + deslizamiento del modelo.
- Universo +MUERTAS (incluye monedas que se hundieron: controla el sesgo de supervivencia).
- Periodos: 2018-hoy, 2022-hoy (sin la manía de 2021), 2023-hoy. Capitales 1.000 € y 10.000 €.
Uso: python exp_kraken.py ../experimentos/kraken"""
import sys, json, warnings; warnings.filterwarnings("ignore")
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
est = {"PRINCIPAL": full(TR.base_trades(P, ["BTC-USD", "ETH-USD"], N=55, long_only=True, risk=0.03, cap=1.0)[0]),
       "CRIPTO_TREND_1%": full(TR.base_trades(P, CR, N=55, long_only=True, risk=0.01)[0]),
       "CRIPTO_TREND_2%": full(TR.base_trades(P, CR, N=55, long_only=True, risk=0.02)[0])}
filas, anual = [], {}
for com in (0.004, 0.0025):
    for cap in (1000.0, 10000.0):
        for nombre, w in est.items():
            BT.COST.update(max_gross=1.0, comm_crypto=com, min_trade_eur=10.0 if cap < 2000 else 50.0)
            for ini in ("2018-01-01", "2022-01-01", "2023-01-01"):
                r = BT.run(P, w, ini, end, capital=cap)
                s = M.stats(r)
                filas.append(dict(estrategia=nombre, comision=com, capital=cap, desde=ini, **{k: round(float(v), 4) for k, v in s.items()}))
                if ini == "2018-01-01" and com == 0.004 and cap == 1000.0:
                    y = r.nav.resample("YE").last(); y = pd.concat([pd.Series([cap], [y.index[0] - pd.offsets.YearEnd()]), y]).pct_change().dropna()
                    anual[nombre] = y.set_axis(y.index.year)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
pd.DataFrame(anual).round(4).to_csv(out / "por_anio.csv")
print(tab[["estrategia", "comision", "capital", "desde", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "Gross"]].to_string(index=False))
print(pd.DataFrame(anual).round(3).to_string())
