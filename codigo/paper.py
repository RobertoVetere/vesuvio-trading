"""Paper trading diario. Uso: python paper.py state.json overlay.json outdir
- state.json: estado persistente (objetivos congelados por fecha). Se actualiza en el sitio.
- overlay.json: vetos de Claude del día [{"asset":..,"accion":"veto_entrada|salir","motivo":..}] (puede no existir).
Los objetivos de días pasados NUNCA se recalculan: se guardan una vez y el valor de la cartera se simula sobre ellos."""
import sys, json, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
import panel, trend as TR, backtest as BT, metrics as M

state_p, overlay_p, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
S = json.loads(state_p.read_text())
P = panel.build()
d = (panel.TODAY - pd.Timedelta(days=1))  # último día cripto cerrado = fecha de decisión
d = min(d, P.cal[-1]); ds = str(d.date())
full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
CR20 = [t for t in P.tradable if P.cls[t] == "CRYPTO"]

def principal():
    W, _ = TR.base_trades(P, ["BTC-USD", "ETH-USD"], N=55, long_only=True, risk=0.03, cap=1.0); return full(W)
def cripto20():
    W, _ = TR.base_trades(P, CR20, N=55, long_only=True, risk=0.01); return full(W)
def piloto():
    BT.COST["max_gross"] = 2.0; BT.COST["min_trade_eur"] = 300.0
    a = [t for t in P.tradable if P.cls[t] in ("ETF", "CRYPTO")]; au = a + [t for t in P.tradable if P.cls[t] == "US"]
    V, var = {}, {}
    for N in (20, 55):
        V[f"T{N}"] = TR.base_trades(P, a, N=N); V[f"T{N}_KONK"] = TR.base_trades(P, a, N=N, konk=True)
    var = {k: full(w) for k, (w, t) in V.items()}
    for k in ["T20", "T55", "T55_KONK"]:
        var[k + "_META"] = full(TR.meta_filter(P, *V[k])[0])
    var["T55_META_CONUS"] = full(TR.meta_filter(P, *TR.base_trades(P, au, N=55))[0])
    R = {k: BT.run(P, w, "2010-01-01", ds).ret for k, w in var.items()}
    W, picks = TR.autopilot(P, var, R)
    S.setdefault("piloto_elecciones", {}).update({str(k): v for k, v in picks.items()})
    return W

TR.LAST_STATE.clear()
Wp = principal(); st_principal = {a: TR.LAST_STATE[a] for a in ["BTC-USD", "ETH-USD"]}
TR.LAST_STATE.clear()
W20 = cripto20(); st20 = dict(TR.LAST_STATE)
Wpil = piloto()
# PILOTO_REAL: lo operable por un particular en España (IBKR + Kraken): sin cortos en cripto; ETF de EEUU vía CFD (financiación de largos)
CRM = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
Wreal = Wpil.copy(); Wreal[CRM] = Wreal[CRM].clip(lower=0)
LF_REAL = np.array([0.035 if P.cls[t] == "ETF" else 0.0 for t in P.tradable])
S["estrategias"].setdefault("PILOTO_REAL", {"capital": 10000, "descripcion": "PILOTO ejecutable en España: sin cortos cripto, ETF vía CFD (IBKR) y cripto al contado (Kraken)", "objetivos": {}})
overlay = json.loads(overlay_p.read_text()) if overlay_p.exists() else []
today_targets = {"PRINCIPAL": Wp.loc[d], "CRIPTO20": W20.loc[d], "PILOTO": Wpil.loc[d], "PILOTO_REAL": Wreal.loc[d]}
# Principal + Claude: solo puede reducir (vetar entradas o adelantar salidas), nunca añadir riesgo
wc = Wp.loc[d].copy()
prev = S["estrategias"]["PRINCIPAL_CLAUDE"]["objetivos"]
prev_w = prev[max(prev)] if prev else {}
for o in overlay:
    a = o.get("asset")
    if a in wc.index:
        if o.get("accion") == "veto_entrada" and prev_w.get(a, 0) == 0: wc[a] = 0.0
        if o.get("accion") == "salir": wc[a] = 0.0
# mantener un veto/salida mientras el sistema siga queriendo la misma posición
for a in wc.index:
    if prev and prev_w.get(a, 0) == 0 and wc[a] != 0 and S["estrategias"]["PRINCIPAL"]["objetivos"].get(max(prev), {}).get(a, 0) != 0:
        wc[a] = 0.0
today_targets["PRINCIPAL_CLAUDE"] = wc
for k, w in today_targets.items():
    obj = S["estrategias"][k]["objetivos"]
    if ds >= S["inicio_decisiones"] and ds not in obj:   # congelar: nunca sobreescribir un día ya guardado
        obj[ds] = {a: round(float(v), 6) for a, v in w.items() if abs(v) > 1e-9}
S.setdefault("overlay_log", []).extend([dict(o, fecha=ds) for o in overlay])
S["ultima_decision"] = ds
state_p.write_text(json.dumps(S, ensure_ascii=False))

# ---- simulación sobre objetivos congelados ----
navs, rows, pos_rows, trade_rows = [], [], [], []
end = str(P.cal[-1].date())
for k, cfg in S["estrategias"].items():
    obj = cfg["objetivos"]
    W = pd.DataFrame(0.0, index=P.cal, columns=P.tradable)
    for dd, ww in obj.items():
        for a, v in ww.items():
            if a in W.columns: W.loc[pd.Timestamp(dd), a] = v
    dates = sorted(pd.Timestamp(x) for x in obj)
    if not dates: continue
    W.loc[~W.index.isin(dates)] = np.nan
    W.loc[W.index < dates[0]] = 0.0
    W = W.ffill().fillna(0.0)
    BT.COST["min_trade_eur"] = 10.0 if cfg["capital"] < 2000 else 300.0
    BT.COST["max_gross"] = 2.0
    start = str((dates[0] + pd.Timedelta(days=1)).date())
    if pd.Timestamp(start) > P.cal[-1]:
        nav = pd.Series([cfg["capital"]], index=[dates[0]]); tr = pd.DataFrame()
    else:
        r = BT.run(P, W, start, end, capital=cfg["capital"], record_trades=True, long_fin=LF_REAL if k == "PILOTO_REAL" else None)
        nav = pd.concat([pd.Series([cfg["capital"]], index=[dates[0]]), r.nav]); tr = r.attrs["trades"]
    for dt, v in nav.items(): navs.append(dict(fecha=str(dt.date()), estrategia=k, valor_eur=round(float(v), 2)))
    last_w = obj[max(obj)]
    for a, v in last_w.items():
        pos_rows.append(dict(estrategia=k, activo=a, peso=round(v, 4), valor_eur=round(v * float(nav.iloc[-1]), 2)))
    if len(tr):
        for _, t in tr.iterrows():
            trade_rows.append(dict(estrategia=k, fecha=str(t.date.date()), activo=t.asset, lado="compra" if t.units > 0 else "venta",
                                   unidades=round(float(t.units), 6), precio=round(float(t.price), 4), coste_eur=round(float(t.cost_eur), 3)))
    rows.append(dict(estrategia=k, descripcion=cfg["descripcion"], capital_inicial=cfg["capital"], valor_actual=round(float(nav.iloc[-1]), 2),
                     rentab=round(float(nav.iloc[-1]) / cfg["capital"] - 1, 4), posiciones=len(last_w),
                     exposicion=round(sum(abs(v) for v in last_w.values()), 3)))
opp = []
for a, s in {**st20, **st_principal}.items():
    if s.get("max_N"):
        opp.append(dict(activo=a, precio=round(s["precio"], 4), maximo_55d=round(s["max_N"], 4),
                        distancia_ruptura=round(s["precio"] / s["max_N"] - 1, 4), en_posicion="sí" if s["pos"] else "no",
                        stop=round(s["stop"], 4) if s["stop"] else None, entrada=s["entrada"]))
opp = sorted(opp, key=lambda x: -x["distancia_ruptura"])
pd.DataFrame(navs).to_csv(out / "nav.csv", index=False)
pd.DataFrame(rows).to_csv(out / "resumen.csv", index=False)
pd.DataFrame(pos_rows or [dict(estrategia="", activo="", peso=0, valor_eur=0)]).to_csv(out / "posiciones.csv", index=False)
pd.DataFrame(trade_rows or [dict(estrategia="", fecha="", activo="", lado="", unidades=0, precio=0, coste_eur=0)]).to_csv(out / "operaciones.csv", index=False)
pd.DataFrame(opp).to_csv(out / "oportunidades.csv", index=False)
print(json.dumps(dict(decision=ds, datos_hasta=end, resumen=rows, principal=st_principal, piloto_2026=S.get("piloto_elecciones", {}).get("2026")), ensure_ascii=False, indent=1, default=str))
