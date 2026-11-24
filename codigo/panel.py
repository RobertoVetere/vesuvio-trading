"""Construye el panel: calendario diario (incluye fines de semana por cripto), precios, FX a EUR,
features en formato largo y matrices anchas. `end` trunca los datos ANTES de calcular nada (anti-fuga)."""
import numpy as np, pandas as pd
from universe import CLASSES, TRADABLE, asset_class, currency
from features import asset_features
import data as D

TODAY = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)  # velas cripto con fecha < hoy UTC están cerradas
DROP = {"ROG.SW"}


def clean(df, t):
    df = df.copy()
    if t.endswith(".L"):  # Yahoo cotiza LSE en peniques
        for c in ["open", "high", "low", "close"]:
            df[c] = df[c] / 100.0
    if asset_class(t) == "CRYPTO":
        df = df[df.index < TODAY]  # vela del día en curso aún abierta
    df["open"] = df["open"].where(df["open"] > 0)
    df["open"] = df["open"].fillna(df["close"].shift(1)).fillna(df["close"])
    df["high"] = df[["high", "open", "close"]].max(axis=1)
    df["low"] = df[["low", "open", "close"]].min(axis=1)
    return df[df.close > 0]


class Panel:
    pass


def build(end=None, start="2004-01-01"):
    end = pd.Timestamp(end) if end else TODAY
    P = Panel()
    tickers = [t for ts in CLASSES.values() for t in ts if t not in DROP]
    raw = {}
    for t in tickers:
        df = clean(D.load(t), t)
        raw[t] = df[(df.index <= end)]
    P.cal = pd.date_range(start, end, freq="D")
    P.tradable = [t for t in tickers if asset_class(t) != "MACRO"]
    P.macro = [t for t in tickers if asset_class(t) == "MACRO"]
    P.all = tickers
    P.cls = pd.Series({t: asset_class(t) for t in tickers})

    # FX: EUR por unidad de divisa
    eurusd = raw["EURUSD=X"].close.reindex(P.cal).ffill().bfill()
    gbpusd = raw["GBPUSD=X"].close.reindex(P.cal).ffill().bfill()
    usdchf = raw["CHF=X"].close.reindex(P.cal).ffill().bfill()
    fxc = {"EUR": pd.Series(1.0, P.cal), "USD": 1 / eurusd, "GBP": gbpusd / eurusd, "CHF": (1 / eurusd) / usdchf}
    P.fxc = fxc

    O, C, B, FX = {}, {}, {}, {}
    feats = []
    for t in tickers:
        df = raw[t]
        f = asset_features(df, usd_volume=(asset_class(t) == "CRYPTO"))
        f["asset"] = t
        feats.append(f.reset_index())
        if t in P.tradable:
            O[t] = df.open.reindex(P.cal)
            C[t] = df.close.reindex(P.cal)
            B[t] = df.close.reindex(P.cal).notna()
            FX[t] = fxc[currency(t)]
    P.O = pd.DataFrame(O)[P.tradable]
    P.Craw = pd.DataFrame(C)[P.tradable]
    P.C = P.Craw.ffill()
    P.B = pd.DataFrame(B)[P.tradable].fillna(False)
    P.FX = pd.DataFrame(FX)[P.tradable]
    ceur = P.C * P.FX
    P.R = (ceur / ceur.shift(1) - 1).fillna(0.0)  # rentabilidad diaria en EUR (proxy de riesgo)

    L = pd.concat(feats, ignore_index=True)
    L = L[(L.date >= P.cal[0]) & (L.date <= end)]
    L["cls"] = L.asset.map(P.cls)
    L = L.set_index(["date", "asset"]).sort_index()
    P.L = L

    def wide(col, assets, ffill=True, limit=None):
        w = L[col].unstack("asset").reindex(P.cal)
        w = w.reindex(columns=assets)
        return w.ffill(limit=limit) if ffill else w

    P.wide = wide
    P.sig = wide("sig20", P.tradable).ffill()
    # elegibilidad: historia >= 260 sesiones, cotizó en los últimos 4 días, liquidez >= 5M EUR/día
    nobs = wide("_nobs", P.tradable)
    dv = wide("_dv20", P.tradable) * P.FX
    recent = P.B.astype(float).rolling(4, min_periods=1).max() > 0
    liq_min = pd.Series({t: (5e6 if P.cls[t] != "CRYPTO" else 2e7) for t in P.tradable})
    P.elig = (nobs >= 260) & recent & (dv >= liq_min) & P.sig.notna()
    P.end = end
    return P
