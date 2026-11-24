"""Piezas comunes de VESUVIO para experimentos: panel con universo candidato completo y universo dinámico top-N."""
import universe as U
from exp_cripto_muertas import MUERTAS_OK
from exp_cripto_amplio import EXTRA_OK
U.CRYPTO.extend([t for t in MUERTAS_OK + EXTRA_OK if t not in U.CRYPTO])
import panel, backtest as BT

def preparar(fin="2023-12-31", top_n=25):
    """fin=None: hasta hoy (solo para la prueba final)."""
    P = panel.build(end=fin)
    CR = [t for t in P.tradable if P.cls[t] == "CRYPTO"]
    dv = (P.wide("_dv20", P.tradable) * P.FX)[CR]
    rank = dv.where(P.elig[CR]).rank(axis=1, ascending=False)
    P.elig[CR] = P.elig[CR] & (rank <= top_n)
    BT.COST.update(max_gross=1.0, comm_crypto=0.0025, min_trade_eur=50.0, rel_band=0.5)
    return P, CR

PERIODOS = (("2018-01-01", "2023-12-31"), ("2018-01-01", "2020-12-31"), ("2022-01-01", "2023-12-31"))
