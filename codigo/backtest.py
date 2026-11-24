"""Backtester realista en EUR.
- Pesos objetivo calculados al final del día t (con datos <= t) se ejecutan en la APERTURA siguiente de cada activo.
- Costes: comisiones tipo IBKR, deslizamiento, impuestos de transacciones (ES/FR/IT/UK), préstamo de cortos,
  interés por apalancamiento, riesgo divisa sobre posiciones largas no-EUR.
- Acciones: cortos en acciones enteras; acciones europeas en acciones enteras; EEUU/ETF fraccionales en largos.
"""
import numpy as np, pandas as pd
from universe import currency

COST = dict(
    slip_bps={"US": 2, "ETF": 2, "EU": 5, "CRYPTO_MAJOR": 20, "CRYPTO": 25},
    ftt={".MC": 0.002, ".PA": 0.004, ".MI": 0.001, ".L": 0.005},
    borrow={"US": 0.005, "ETF": 0.005, "EU": 0.01, "CRYPTO_MAJOR": 0.05, "CRYPTO": 0.10},
    margin_rate=0.05, min_trade_eur=300.0, rel_band=0.25, max_gross=1.6,
)


def _vec(P):
    cls = P.cls[P.tradable].values
    major = np.isin(P.tradable, ["BTC-USD", "ETH-USD"])
    key = np.where((cls == "CRYPTO") & major, "CRYPTO_MAJOR", cls)
    slip = np.array([COST["slip_bps"][k] for k in key]) / 1e4
    borrow = np.array([COST["borrow"][k] for k in key])
    ftt = np.array([next((v for s, v in COST["ftt"].items() if t.endswith(s)), 0.0) for t in P.tradable])
    cur = np.array([currency(t) for t in P.tradable])
    eu_min = np.where(cur == "CHF", 10.0, 3.0)
    is_us = np.isin(cls, ["US", "ETF"])
    is_eu = cls == "EU"
    is_cr = cls == "CRYPTO"
    return slip, borrow, ftt, eu_min, is_us, is_eu, is_cr


def run(P, W, start, end, capital=10_000.0, record_trades=False, cost_mult=1.0):
    slip, borrow, ftt, eu_min, is_us, is_eu, is_cr = _vec(P)
    is_stock = is_us | is_eu
    cal = P.cal
    i0, i1 = cal.searchsorted(pd.Timestamp(start)), cal.searchsorted(pd.Timestamp(end), "right")
    O, C, Bm, FX = P.O.values, P.C.values, P.B.values, P.FX.values
    Wv = W.reindex(index=cal, columns=P.tradable).fillna(0.0).values
    N = len(P.tradable)
    u = np.zeros(N)
    nav = capital
    out_nav, out_cost, out_gross, out_net, out_turn, trades = [], [], [], [], [], []
    for i in range(max(i0, 1), i1):
        b = Bm[i]
        o = np.where(b, O[i], C[i - 1])
        pc, c, fx, fxp = C[i - 1], C[i], FX[i], FX[i - 1]
        pc = np.nan_to_num(pc); c = np.nan_to_num(c); o = np.nan_to_num(o)
        # 1) apertura: gap de precio + revalorización divisa de largos
        pnl = np.sum(np.where(b, u * (o - pc) * fxp, 0.0))
        nav_open = nav + pnl
        # 2) operaciones en la apertura (solo activos que cotizan hoy)
        w = Wv[i - 1].copy()
        g = np.abs(w).sum()
        if g > COST["max_gross"]:
            w *= COST["max_gross"] / g
        px = np.where(o > 0, o * fxp, np.nan)
        tgt_units = np.where(b & (px > 0), w * nav_open / np.where(px > 0, px, 1), u)
        # acciones enteras: cortos siempre, Europa siempre
        whole = (is_stock & (tgt_units < 0)) | is_eu
        tgt_units = np.where(whole, np.trunc(tgt_units), tgt_units)
        du = tgt_units - u
        dval = np.abs(du) * np.nan_to_num(px)
        tgt_val = np.abs(tgt_units) * np.nan_to_num(px)
        flip = np.sign(tgt_units) != np.sign(u)
        do = b & (du != 0) & ((dval >= np.maximum(COST["min_trade_eur"], COST["rel_band"] * tgt_val)) | flip
                               | ((tgt_units == 0) & (u != 0)))
        du = np.where(do, du, 0.0)
        notional = np.abs(du) * np.nan_to_num(px)
        loc_notional = np.abs(du) * o
        comm_us = np.clip(0.0035 * np.abs(du), 0.35, 0.01 * loc_notional) * fxp
        comm_eu = np.maximum(eu_min, 0.0005 * loc_notional) * fxp
        comm_cr = 0.001 * notional
        comm = np.where(is_us, comm_us, np.where(is_eu, comm_eu, comm_cr))
        cost = cost_mult * np.where(do, comm + slip * notional + np.where(du > 0, ftt * notional, 0.0), 0.0)
        tc = cost.sum()
        u = u + du
        # 3) intradía hasta el cierre
        pnl2 = np.sum(np.where(b, u * (c - o) * fxp, 0.0)) + np.sum(np.maximum(u, 0) * c * (fx - fxp))
        posv = u * c * fx
        fin = cost_mult * np.sum(np.abs(np.minimum(posv, 0)) * borrow) / 365
        nav_tmp = nav_open + pnl2 - tc
        lev = max(0.0, posv[posv > 0].sum() - nav_tmp - 1.0) * COST["margin_rate"] / 365
        nav = nav_tmp - fin - lev
        out_nav.append(nav); out_cost.append(tc + fin + lev)
        out_gross.append(np.abs(posv).sum() / max(nav, 1e-9)); out_net.append(posv.sum() / max(nav, 1e-9))
        out_turn.append(notional.sum() / max(nav, 1e-9))
        if record_trades and do.any():
            for j in np.where(do)[0]:
                trades.append((cal[i], P.tradable[j], du[j], o[j], cost[j]))
        if nav <= capital * 0.05:
            break
    idx = cal[max(i0, 1):max(i0, 1) + len(out_nav)]
    res = pd.DataFrame({"nav": out_nav, "cost": out_cost, "gross": out_gross, "net": out_net, "turnover": out_turn}, idx)
    res["ret"] = res.nav.pct_change().fillna(res.nav.iloc[0] / capital - 1)
    if record_trades:
        res.attrs["trades"] = pd.DataFrame(trades, columns=["date", "asset", "units", "price", "cost_eur"])
    return res
