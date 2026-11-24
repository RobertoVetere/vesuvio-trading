"""Sistema de tendencias (trend following) + meta-etiquetado + piloto automático.
Todo causal: entradas con datos <= t, meta-modelo entrenado solo con operaciones CERRADAS antes de cada año,
selección de variante con resultados de años anteriores. Ejecución en la apertura siguiente (backtest.py)."""
import numpy as np, pandas as pd
LAST_STATE = {}

META_FEATS = ["sig20", "volratio", "ret5", "ret20", "ret60", "mom_12_1", "dv_z", "dv_z5", "k_azul", "k_verde",
              "k_cross", "k_marron", "dist_hi250", "dist_lo250", "skew60", "dma50", "dma200"]


def base_trades(P, assets, N=55, stop_mult=3.0, risk=0.005, max_units=3, add_step=1.0, konk=False, cap=0.25, long_only=False, intraday=False, stops_out=None, red_mult=None):
    """Devuelve pesos objetivo (calendario x activos) y lista de operaciones (para el meta-modelo).
    intraday=True: el stop es una orden en el exchange; salta cuando el mínimo (máximo en cortos) del día lo toca,
    sin esperar al cierre. red_mult: si se da, la orden en el exchange es solo una RED de seguridad a red_mult x vol
    (el stop normal sigue evaluándose al cierre con stop_mult). Si stops_out es un dict, se rellena con la serie de niveles de stop vigentes cada día."""
    W = pd.DataFrame(0.0, index=P.cal, columns=assets)
    trades = []
    az_all = P.L["k_azul"]
    for a in assets:
        loc = P.Craw[a][P.B[a]].dropna()
        if len(loc) < N + 30:
            continue
        el = P.elig[a].reindex(loc.index).fillna(False).values
        c = loc.values
        hh = P.Hi[a].reindex(loc.index).fillna(loc).values; ll = P.Lw[a].reindex(loc.index).fillna(loc).values
        oo = P.O[a].reindex(loc.index).fillna(loc).values
        sv = np.full(len(c), np.nan)  # nivel de stop vigente DURANTE el día i (fijado al cierre de i-1)
        hi = loc.rolling(N).max().shift(1).values
        lo = loc.rolling(N).min().shift(1).values
        atr = loc.diff().abs().ewm(span=20, adjust=False).mean().values * 1.25
        az = az_all.xs(a, level="asset").reindex(loc.index).values if konk else None
        w = np.zeros(len(c))
        pos, units, ext, last_add, ent_i, ent_px = 0, 0, 0.0, 0.0, -1, 0.0
        for i in range(len(c)):
            if np.isnan(atr[i]) or np.isnan(hi[i]):
                continue
            if pos == 0:
                d = 1 if c[i] > hi[i] else (-1 if (c[i] < lo[i] and not long_only) else 0)
                if d and el[i] and (not konk or (az[i] == az[i] and np.sign(az[i]) == d)):
                    pos, units, ext, last_add, ent_i, ent_px = d, 1, c[i], c[i], i, c[i]
            else:
                lvl = sv[i]
                if intraday and lvl == lvl and ((pos > 0 and ll[i] <= lvl) or (pos < 0 and hh[i] >= lvl)):
                    g = 0.25  # misma penalización que backtest.COST['stop_gap_frac']
                    fill = min(oo[i], lvl - g * max(lvl - ll[i], 0)) if pos > 0 else max(oo[i], lvl + g * max(hh[i] - lvl, 0))
                    trades.append((loc.index[ent_i], loc.index[i], a, pos, pos * (fill / ent_px - 1)))
                    pos, units = 0, 0
                    continue
                ext = max(ext, c[i]) if pos > 0 else min(ext, c[i])
                stop_hit = (c[i] < ext - stop_mult * atr[i]) if pos > 0 else (c[i] > ext + stop_mult * atr[i])
                if stop_hit or not el[i]:
                    trades.append((loc.index[ent_i], loc.index[i], a, pos, pos * (c[i] / ent_px - 1)))
                    pos, units = 0, 0
                elif units < max_units and pos * (c[i] - last_add) >= add_step * atr[i]:
                    units += 1; last_add = c[i]
            if pos:
                w[i] = pos * min(units * risk / (stop_mult * atr[i] / c[i]), cap)
                if i + 1 < len(c):
                    m = red_mult if red_mult else stop_mult
                    sv[i + 1] = ext - m * atr[i] if pos > 0 else ext + m * atr[i]
        i = len(c) - 1
        LAST_STATE[a] = dict(fecha=str(loc.index[i].date()), precio=float(c[i]), pos=int(pos), unidades=int(units),
                             max_N=float(hi[i]) if hi[i] == hi[i] else None, min_N=float(lo[i]) if lo[i] == lo[i] else None,
                             stop=(float(ext - stop_mult * atr[i]) if pos > 0 else float(ext + stop_mult * atr[i])) if pos else None,
                             entrada=str(loc.index[ent_i].date()) if pos else None, precio_entrada=float(ent_px) if pos else None)
        if pos:  # operación abierta al final: se registra sin resultado
            trades.append((loc.index[ent_i], pd.NaT, a, pos, np.nan))
        W[a] = pd.Series(w, loc.index).reindex(P.cal).ffill().fillna(0.0)
        if stops_out is not None:
            stops_out[a] = pd.Series(sv, loc.index).reindex(P.cal)
    T = pd.DataFrame(trades, columns=["entry", "exit", "asset", "dir", "ret"])
    return W, T


def meta_filter(P, W, T, first_year=2012, thr=0.40, boost=0.60, min_train=400):
    """Meta-etiquetado walk-forward: P(éxito) de cada entrada; descarta si < thr, x1.5 si > boost."""
    import lightgbm as lgb
    X = P.L.loc[list(zip(T.entry, T.asset)), META_FEATS].reset_index(drop=True)
    X["dir"] = T["dir"].values
    for k in META_FEATS:
        if k.startswith(("ret", "mom", "k_cross", "dma", "skew")):
            X[k + "_d"] = X[k] * X["dir"]
    mac = {}
    for t, f in (("SPY", "dma200"), ("BTC-USD", "dma50"), ("^VIX", "dist_hi250"), ("^TNX", "ret20"), ("DX-Y.NYB", "ret20")):
        s = P.L.xs(t, level="asset")[f].reindex(P.cal).ffill()
        X["m_" + t + f] = s.reindex(T.entry).values
    X["cls_cr"] = (P.cls[T.asset].values == "CRYPTO").astype(float)
    y = (T.ret > 0).astype(float)
    mult = pd.Series(1.0, index=T.index)
    params = dict(objective="binary", learning_rate=0.03, num_leaves=15, min_data_in_leaf=40, feature_fraction=0.7,
                  bagging_fraction=0.8, bagging_freq=1, lambda_l2=2.0, verbose=-1, num_threads=2, seed=3)
    probs = pd.Series(np.nan, index=T.index)
    for Y in range(first_year, P.cal[-1].year + 1):
        cut = pd.Timestamp(f"{Y}-01-01")
        tr = (T.exit < cut) & T.ret.notna()
        te = (T.entry >= cut) & (T.entry < pd.Timestamp(f"{Y+1}-01-01"))
        if tr.sum() < min_train or te.sum() == 0:
            continue
        m = lgb.train(params, lgb.Dataset(X[tr].astype("float32"), y[tr]), num_boost_round=200)
        probs[te] = m.predict(X[te].astype("float32"))
    mult[probs < thr] = 0.0
    mult[probs > boost] = 1.5
    W2 = W.copy()
    for idx, r in T.iterrows():
        if mult[idx] == 1.0:
            continue
        end = r.exit if pd.notna(r.exit) else P.cal[-1]
        # la posición vive desde la entrada hasta la salida (inclusive) en el calendario
        sl = (W2.index >= r.entry) & (W2.index < end + pd.Timedelta(days=1))
        W2.loc[sl, r.asset] = W2.loc[sl, r.asset] * mult[idx]
    return W2, probs


def autopilot(P, variants, R_daily, lookback_years=3, first_year=2014):
    """Cada 1 de enero elige la variante con mejor Sharpe en los `lookback_years` anteriores (solo pasado)."""
    names = list(variants)
    W = pd.DataFrame(0.0, index=P.cal, columns=variants[names[0]].columns)
    picks = {}
    for Y in range(first_year, P.cal[-1].year + 1):
        s, e = pd.Timestamp(f"{Y-lookback_years}-01-01"), pd.Timestamp(f"{Y}-01-01")
        sh = {k: (R_daily[k][(R_daily[k].index >= s) & (R_daily[k].index < e)]) for k in names}
        sh = {k: (v.mean() / v.std() if v.std() > 0 else -9) for k, v in sh.items()}
        best = max(sh, key=sh.get); picks[Y] = best
        sl = (P.cal >= e) & (P.cal < pd.Timestamp(f"{Y+1}-01-01"))
        W.loc[sl] = variants[best].loc[sl].values
    return W, picks
