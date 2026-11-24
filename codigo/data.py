"""Descarga de datos diarios OHLCV desde Yahoo (API chart v8) con caché parquet.
Uso: python data.py  -> descarga todo el universo.
"""
import json, time, sys, urllib.request, urllib.error, urllib.parse
from pathlib import Path
import numpy as np, pandas as pd
from universe import CLASSES

RAW = Path(__file__).parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}

def fetch(t, start=946684800):
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(t)}"
           f"?period1={start}&period2={int(time.time())}&interval=1d&events=div%2Csplit&includeAdjustedClose=true")
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                j = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(5 * (k + 1)); continue
            raise
    res = j["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose")
    tz = res["meta"].get("exchangeTimezoneName", "UTC")
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert(tz).normalize().tz_localize(None)
    df = pd.DataFrame({"open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"],
                       "volume": q["volume"], "adjclose": adj if adj else q["close"]}, index=idx, dtype=float)
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close"])
    # Ajuste por dividendos/splits aplicado a OHLC (factor adjclose/close)
    f = (df["adjclose"] / df["close"]).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    for c in ["open", "high", "low"]:
        df[c] = df[c] * f
    df["close_raw"] = df["close"]
    df["close"] = df["adjclose"]
    df["volume"] = df["volume"].fillna(0)
    df.index.name = "date"
    return df.drop(columns="adjclose")

def download_all(force=False):
    import urllib.parse  # noqa
    bad = []
    for cls, ts in CLASSES.items():
        for t in ts:
            p = RAW / f"{t.replace('^','_').replace('=','_')}.parquet"
            if p.exists() and not force: continue
            try:
                df = fetch(t); df.to_parquet(p)
                print(f"{cls:6s} {t:12s} {len(df):5d} {df.index[0].date()} -> {df.index[-1].date()}", flush=True)
            except Exception as e:
                bad.append(t); print("FAIL", t, e, flush=True)
            time.sleep(0.4)
    return bad

def load(t):
    return pd.read_parquet(RAW / f"{t.replace('^','_').replace('=','_')}.parquet")

if __name__ == "__main__":
    import urllib.parse
    print("fallidos:", download_all(force="--force" in sys.argv))
