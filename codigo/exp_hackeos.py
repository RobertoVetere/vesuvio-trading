"""Regla de eventos: hackeos (DeFiLlama, api.llama.fi/hacks). SOLO diseño 2018-2023 (2024-26 ya gastado).
Cada hackeo se asigna al token nativo de su cadena. Variantes (4):
 V1 vetar entradas en el token 7 días tras hackeo >= 50M$   V2 >= 100M$, 14 días
 V3 >= 100M$: salir + vetar 7 días                           V4 hackeo >= 200M$: vetar entradas en TODA cripto 7 días
Estrategias: CRIPTO_TREND top-25 dinámico (config palanca 1) y PRINCIPAL (BTC+ETH).
Uso: python exp_hackeos.py ../experimentos/hackeos"""
import sys, json, urllib.request, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
raw = json.load(urllib.request.urlopen(urllib.request.Request("https://api.llama.fi/hacks", headers={"User-Agent": "Mozilla/5.0"}), timeout=60))
print("registros:", len(raw), "| ejemplo:", {k: raw[0].get(k) for k in list(raw[0])[:12]}, flush=True)
H = pd.DataFrame(raw)
H["fecha"] = pd.to_datetime(H["date"], unit="s").dt.normalize()
H["amount"] = pd.to_numeric(H["amount"], errors="coerce").fillna(0)
CADENA = {"Ethereum": "ETH-USD", "Solana": "SOL-USD", "BSC": "BNB-USD", "Binance": "BNB-USD", "Avalanche": "AVAX-USD",
          "Polygon": "POL28321-USD", "Tron": "TRX-USD", "Near": "NEAR-USD", "Cosmos": "ATOM-USD", "Cardano": "ADA-USD",
          "Polkadot": "DOT-USD", "Arbitrum": "ARB11841-USD", "Optimism": "OP-USD", "Sui": "SUI20947-USD", "Aptos": "APT21794-USD",
          "Bitcoin": "BTC-USD", "Fantom": "FTM-USD", "Terra": "LUNC-USD", "Harmony": None, "Ronin": None}
filas = []
for _, h in H.iterrows():
    ch = h.get("chain") or []
    ch = ch if isinstance(ch, list) else [ch]
    for c in ch:
        t = CADENA.get(c)
        if t: filas.append((h.fecha, t, h.amount, h.get("name")))
E = pd.DataFrame(filas, columns=["fecha", "activo", "importe", "nombre"])
E.to_csv(out / "hackeos_asignados.csv", index=False)
print("hackeos asignados a tokens:", len(E), "| >=100M$:", int((E.importe >= 1e8).sum()), flush=True)
from vesuvio_base import preparar, PERIODOS
import trend as TR, backtest as BT, metrics as M
P, CR = preparar()
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
Wct = full(TR.base_trades(P, CR, N=55, long_only=True, risk=0.01, max_units=3)[0])
Wpr = full(TR.base_trades(P, ["BTC-USD", "ETH-USD"], N=55, long_only=True, risk=0.03, cap=1.0)[0])

def aplicar(W, eventos, dias, salir, todos=False):
    W = W.copy()
    for _, e in eventos.iterrows():
        cols = [c for c in W.columns if P.cls.get(c) == "CRYPTO"] if todos else ([e.activo] if e.activo in W.columns else [])
        d0 = e.fecha + pd.Timedelta(days=1)  # se conoce el día del hackeo; actúa al cierre del día siguiente como pronto
        ven = (W.index >= d0) & (W.index < d0 + pd.Timedelta(days=dias))
        for c in cols:
            s = W[c]
            abierta = s.shift(1).fillna(0) != 0
            if salir:
                # cierra la operación abierta en d0 hasta que la estrategia vuelva a 0
                if abierta.loc[d0] if d0 in s.index else False:
                    fin = s.loc[d0:][s.loc[d0:] == 0].index.min()
                    W.loc[d0:(fin if pd.notna(fin) else W.index[-1]), c] = 0.0
            # veto de entradas nuevas en la ventana: anula la operación entera que empiece dentro
            ent = ven & (s != 0) & (s.shift(1).fillna(0) == 0)
            for d in W.index[ent]:
                fin = s.loc[d:][s.loc[d:] == 0].index.min()
                W.loc[d:(fin if pd.notna(fin) else W.index[-1]), c] = 0.0
    return W

var = {"ref": lambda W: W,
       "V1_50M_7d": lambda W: aplicar(W, E[E.importe >= 5e7], 7, False),
       "V2_100M_14d": lambda W: aplicar(W, E[E.importe >= 1e8], 14, False),
       "V3_100M_salir_7d": lambda W: aplicar(W, E[E.importe >= 1e8], 7, True),
       "V4_200M_todo_7d": lambda W: aplicar(W, E[E.importe >= 2e8].drop_duplicates("fecha"), 7, False, todos=True)}
res = []
for est, W0 in (("CRIPTO_TREND", Wct), ("PRINCIPAL", Wpr)):
    for k, f in var.items():
        W = f(W0)
        for ini, fin in PERIODOS:
            r = BT.run(P, W, ini, fin, capital=10_000.0, record_trades=True)
            s = M.stats(r)
            res.append(dict(estrategia=est, variante=k, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
        print("hecho", est, k, flush=True)
tab = pd.DataFrame(res); tab.to_csv(out / "resumen.csv", index=False)
print(tab[["estrategia", "variante", "periodo", "CAGR", "Sharpe", "MaxDD", "ops"]].to_string(index=False))
