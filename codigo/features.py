"""Indicadores y features por activo. Todo causal: el valor en t solo usa datos <= t."""
import numpy as np, pandas as pd


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(s, n=14):
    d = s.diff()
    au = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    ad = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / ad.replace(0, np.nan))


def mfi(tp, vol, n=14):
    mf = tp * vol
    d = tp.diff()
    pos = mf.where(d > 0, 0.0).rolling(n).sum()
    neg = mf.where(d < 0, 0.0).rolling(n).sum()
    return 100 - 100 / (1 + pos / neg.replace(0, np.nan))


def volume_index(close, vol, positive=True):
    r = close.pct_change().fillna(0)
    cond = (vol > vol.shift(1)) if positive else (vol < vol.shift(1))
    return (1 + r.where(cond, 0.0)).cumprod()


def konkorde(df, m=15):
    """Konkorde de Blai5 (versión TradingView 'Blai5 Koncorde').
    azul = manos fuertes (NVI), verde = manos débiles (marrón + PVI), marrón = tendencia, media = EMA(marrón)."""
    tp = (df.open + df.high + df.low + df.close) / 4
    pvi = volume_index(df.close, df.volume, True)
    nvi = volume_index(df.close, df.volume, False)
    pvim, nvim = ema(pvi, m), ema(nvi, m)
    oscp = (pvi - pvim) * 100 / (pvim.rolling(90).max() - pvim.rolling(90).min())
    azul = (nvi - nvim) * 100 / (nvim.rolling(90).max() - nvim.rolling(90).min())
    xmf = mfi(tp, df.volume, 14)
    basis = tp.rolling(25).mean()
    dev = 2 * tp.rolling(25).std()
    bollosc = (tp - basis) / (2 * dev) * 100
    xrsi = rsi(tp, 14)
    ll, hh = df.low.rolling(21).min(), df.high.rolling(21).max()
    stoc = (100 * (tp - ll) / (hh - ll)).rolling(3).mean()
    marron = (xrsi + xmf + bollosc + stoc / 3) / 2
    verde = marron + oscp
    media = ema(marron, m)
    out = pd.DataFrame(dict(k_marron=marron, k_verde=verde, k_azul=azul, k_media=media,
                            k_rsi=xrsi, k_mfi=xmf, k_bb=bollosc, k_stoch=stoc))
    return out.replace([np.inf, -np.inf], np.nan)


def asset_features(df, usd_volume=False):
    c, o = df.close, df.open
    dvol = df.volume if usd_volume else c * df.volume
    lc = np.log(c)
    r = lc.diff()
    sig = r.ewm(span=20, adjust=False).std()
    sig60 = r.rolling(60).std()
    f = {"sig20": sig, "sig60": sig60, "volratio": sig / sig60}
    for n in [1, 2, 5, 10, 20, 60, 120, 250]:
        f[f"ret{n}"] = lc.diff(n) / (sig60 * np.sqrt(n))
    f["mom_12_1"] = (lc.shift(21) - lc.shift(252)) / (sig60 * np.sqrt(231))
    for n in [10, 20, 50, 200]:
        f[f"dma{n}"] = (c / c.rolling(n).mean() - 1) / sig
    f["hl_range"] = ((df.high - df.low) / c).rolling(10).mean() / sig
    f["gap"] = (np.log(o) - lc.shift(1)) / sig
    f["intraday"] = (lc - np.log(o)) / sig
    ldv = np.log1p(dvol)
    f["dv_z"] = (ldv - ldv.rolling(60).mean()) / ldv.rolling(60).std()
    f["dv_z5"] = f["dv_z"].rolling(5).mean()
    f["skew60"] = r.rolling(60).skew()
    f["dist_hi250"] = c / c.rolling(250).max() - 1
    f["dist_lo250"] = c / c.rolling(250).min() - 1
    k = konkorde(df)
    for col in k:
        f[col] = k[col]
    f["k_cross"] = k.k_marron - k.k_media
    f["k_cross_chg"] = f["k_cross"].diff()
    f["k_azul_chg"] = k.k_azul.diff(3)
    f["k_verde_chg"] = k.k_verde.diff(3)
    out = pd.DataFrame(f).replace([np.inf, -np.inf], np.nan)
    # auxiliares (no features): z del día para eventos, objetivos futuros (apertura siguiente -> apertura +h)
    out["_z"] = r / sig.shift(1)
    out["_nobs"] = np.arange(len(df)) + 1
    out["_dv20"] = dvol.rolling(20).median()
    for h in (1, 5):
        fwd = o.shift(-1 - h) / o.shift(-1) - 1
        out[f"_fwd{h}"] = fwd
        out[f"_fwdn{h}"] = fwd / (sig * np.sqrt(h))
    return out
