"""VESUVIO palanca 2 — universo. SOLO diseño 2018-2023. Config adoptada en palanca 1 (banda 50 %, creador 0,25 %, 3 unidades).
Universos: U20 (lista actual) / U20+MUERTAS (base) / AMPLIO (+ ~50 que fueron grandes). Liquidez mínima 20M € o 50M €/día.
Uso: python exp_v2_universo.py ../experimentos/v2_universo"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
import universe as U
from exp_cripto_muertas import MUERTAS_OK
from exp_cripto_amplio import EXTRA_OK, FALLIDAS
print("extra con datos:", len(EXTRA_OK), "fallidas:", FALLIDAS, flush=True)
import panel, trend as TR, backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
FIN = "2023-12-31"
BASE20 = list(U.CRYPTO)
universos = {"U20": [], "U20+MUERTAS": MUERTAS_OK, "AMPLIO": MUERTAS_OK + EXTRA_OK}
filas = []
for nombre, extra in universos.items():
    U.CRYPTO[:] = BASE20 + extra
    P = panel.build(end=FIN)
    full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
    CR = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
    dv = P.wide("_dv20", P.tradable) * P.FX
    for liq in (2e7, 5e7):
        P.elig = (P.wide("_nobs", P.tradable) >= 260) & (P.B.astype(float).rolling(4, min_periods=1).max() > 0) & (dv >= liq) & P.sig.notna()
        n_eleg = P.elig[CR].sum(axis=1).loc["2018":FIN]
        W, _ = TR.base_trades(P, CR, N=55, long_only=True, risk=0.01, max_units=3)
        BT.COST.update(max_gross=1.0, comm_crypto=0.0025, min_trade_eur=50.0, rel_band=0.5)
        for ini, fin in (("2018-01-01", FIN), ("2018-01-01", "2020-12-31"), ("2022-01-01", FIN)):
            r = BT.run(P, full(W), ini, fin, capital=10_000.0, record_trades=True)
            s = M.stats(r)
            filas.append(dict(universo=nombre, liquidez_M=int(liq / 1e6), periodo=f"{ini[:4]}-{fin[:4]}", elegibles_mediana=int(n_eleg.median()),
                              ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
        print("hecho", nombre, liq, flush=True)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
print(tab[["universo", "liquidez_M", "periodo", "elegibles_mediana", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "Gross", "ops"]].to_string(index=False))
