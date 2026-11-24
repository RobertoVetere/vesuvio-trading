"""Experimento: ¿centrar el sistema en cripto? Con control del sesgo de supervivencia.
Universo BASE = 20 criptos actuales. Universo +MUERTAS = BASE + monedas que fueron top y se hundieron.
Estrategias: PRINCIPAL (BTC+ETH), CRIPTO_TREND (ruptura 55, solo largos, riesgo 1 % y 2 %),
PILOTO_CR (patas cripto de PILOTO_REAL), PILOTO_REAL (completo, referencia).
Uso (desde codigo/): python exp_cripto.py ../experimentos/cripto"""
import sys, json, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
import universe as U, data as D
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
MUERTAS = ["LUNC-USD", "FTT-USD", "EOS-USD", "XEM-USD", "IOTA-USD", "DASH-USD", "NEO-USD", "WAVES-USD", "BSV-USD",
           "ZEC-USD", "XMR-USD", "QTUM-USD", "ICX-USD", "OMG-USD", "LSK-USD", "BTG-USD", "CEL-USD", "BTT-USD"]
ok = []
for t in MUERTAS:
    try:
        df = D.fetch(t)
        if len(df) > 400: df.to_parquet(D.RAW / f"{t}.parquet"); ok.append(t)
        print("ok", t, len(df), df.index[0].date(), df.index[-1].date(), flush=True)
    except Exception as e:
        print("FALLA", t, e, flush=True)
import panel, trend as TR, backtest as BT, metrics as M

def piloto(P):
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
    R = {k: BT.run(P, w, "2010-01-01", str(P.cal[-1].date())).ret for k, w in var.items()}
    W, picks = TR.autopilot(P, var, R)
    cr = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
    W[cr] = W[cr].clip(lower=0)
    return W, picks

filas, anual = [], {}
for uni in ("BASE", "+MUERTAS"):
    if uni == "+MUERTAS":
        U.CRYPTO.extend(ok)
    P = panel.build(); end = str(P.cal[-1].date())
    full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
    CR = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
    etf = np.array([P.cls[t] == "ETF" for t in P.tradable]); lf = np.where(etf, 0.035, 0.0)
    Wpr, _ = TR.base_trades(P, ["BTC-USD", "ETH-USD"], N=55, long_only=True, risk=0.03, cap=1.0)
    W1, _ = TR.base_trades(P, CR, N=55, long_only=True, risk=0.01)
    W2, _ = TR.base_trades(P, CR, N=55, long_only=True, risk=0.02)
    Wpil, picks = piloto(P)
    Wcr = Wpil.copy(); Wcr[[t for t in P.tradable if t not in CR]] = 0.0
    casos = {"PRINCIPAL": (full(Wpr), None), "CRIPTO_TREND_1%": (full(W1), None), "CRIPTO_TREND_2%": (full(W2), None),
             "PILOTO_CR": (Wcr, None), "PILOTO_REAL": (Wpil, lf)}
    for nombre, (w, f) in casos.items():
        BT.COST["max_gross"] = 2.0; BT.COST["min_trade_eur"] = 300.0
        for ini in ("2018-01-01", "2023-01-01"):
            r = BT.run(P, w, ini, end, capital=10_000.0, long_fin=f)
            s = M.stats(r)
            filas.append(dict(universo=uni, estrategia=nombre, desde=ini, **{k: round(float(v), 4) for k, v in s.items()}))
            if ini == "2018-01-01":
                y = r.nav.resample("YE").last(); y = pd.concat([pd.Series([10000.0], [y.index[0] - pd.offsets.YearEnd()]), y]).pct_change().dropna()
                anual[f"{nombre}|{uni}"] = y.set_axis(y.index.year)
    print(uni, "elecciones PILOTO 2018-2026:", {k: v for k, v in picks.items() if k >= 2018}, flush=True)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
pd.DataFrame(anual).round(4).to_csv(out / "por_anio.csv")
json.dump(dict(datos_hasta=end, muertas_incluidas=ok), open(out / "meta.json", "w"), indent=1)
print(tab[["universo", "estrategia", "desde", "CAGR", "Sharpe", "MaxDD", "Gross"]].to_string(index=False))
print(pd.DataFrame(anual).round(3).to_string())
