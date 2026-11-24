"""VESUVIO palanca 4 — régimen de mercado (BTC vs su media de 200 días, con datos hasta t). SOLO diseño 2018-2023.
Variantes: ref / largos x0 en bajista / largos x0,5 en bajista / x0 + cortos BTC-ETH en bajista (futuros, coste de
financiación del corto 5 %/año ya en el modelo) / x0,5 + cortos.
Uso: python exp_v4_regimen.py ../experimentos/v4_regimen"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
from vesuvio_base import preparar, PERIODOS
import trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
P, CR = preparar()
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
W = full(TR.base_trades(P, CR, N=55, long_only=True, risk=0.01, max_units=3)[0])
btc = P.C["BTC-USD"]
alcista = (btc > btc.rolling(200).mean()).reindex(P.cal).fillna(True)
Wsh = full(TR.base_trades(P, ["BTC-USD", "ETH-USD"], N=55, long_only=False, risk=0.02, cap=0.5)[0]).clip(upper=0)
Wsh = Wsh.mul((~alcista).astype(float), axis=0)
def escala(f):
    m = alcista.astype(float) + (~alcista).astype(float) * f
    return W.mul(m, axis=0)
var = {"ref": W, "largos_x0_bajista": escala(0.0), "largos_x0.5_bajista": escala(0.5),
       "x0+cortos_BTC_ETH": escala(0.0) + Wsh, "x0.5+cortos_BTC_ETH": escala(0.5) + Wsh}
filas = []
for k, w in var.items():
    for ini, fin in PERIODOS:
        r = BT.run(P, w, ini, fin, capital=10_000.0, record_trades=True)
        s = M.stats(r)
        filas.append(dict(variante=k, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
print("dias bajistas 2018-2023:", round(1 - alcista.loc["2018":"2023"].mean(), 3))
print(tab[["variante", "periodo", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "Gross", "Net", "ops"]].to_string(index=False))
