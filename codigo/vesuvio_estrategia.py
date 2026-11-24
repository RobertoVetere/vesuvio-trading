"""VESUVIO: estrategia con las palancas adoptadas (ver vesuvio/decisiones.md)."""
import pandas as pd
import trend as TR

def pesos(P, CR, meta=None):
    """meta: None o dict(thr=, boost=) para el meta-etiquetado walk-forward de las entradas largas."""
    full = lambda W: W.reindex(columns=P.tradable).fillna(0.0)
    Wl, T = TR.base_trades(P, CR, N=55, long_only=True, risk=0.01, max_units=3)
    if meta:
        Wl, _ = TR.meta_filter(P, Wl, T, first_year=2019, thr=meta["thr"], boost=meta["boost"], min_train=300)
    W = full(Wl)
    btc = P.C["BTC-USD"]
    alcista = (btc > btc.rolling(200).mean()).reindex(P.cal).fillna(True)
    Wsh = full(TR.base_trades(P, ["BTC-USD", "ETH-USD"], N=55, long_only=False, risk=0.02, cap=0.5)[0]).clip(upper=0)
    m = alcista.astype(float) + (~alcista).astype(float) * 0.5
    return W.mul(m, axis=0) + Wsh.mul((~alcista).astype(float), axis=0), alcista
