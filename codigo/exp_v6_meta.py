"""VESUVIO palanca 6 — meta-etiquetado LightGBM (walk-forward anual desde 2019; 2018 sin cambios). SOLO diseño 2018-2023.
Variantes: ref / PILOTO (descarta p<0,40, x1,5 si p>0,60) / solo descarta p<0,35 / solo descarta p<0,40.
Uso: python exp_v6_meta.py ../experimentos/v6_meta"""
import sys, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
from vesuvio_base import preparar, PERIODOS
from vesuvio_estrategia import pesos
import backtest as BT, metrics as M
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
P, CR = preparar()
var = {"ref": None, "meta_0.40_x1.5": dict(thr=0.40, boost=0.60), "meta_solo_0.35": dict(thr=0.35, boost=9.9), "meta_solo_0.40": dict(thr=0.40, boost=9.9)}
filas = []
for k, m in var.items():
    W, _ = pesos(P, CR, meta=m)
    for ini, fin in PERIODOS + (("2019-01-01", "2023-12-31"),):
        r = BT.run(P, W, ini, fin, capital=10_000.0, record_trades=True)
        s = M.stats(r)
        filas.append(dict(variante=k, periodo=f"{ini[:4]}-{fin[:4]}", ops=len(r.attrs["trades"]), **{c: round(float(v), 4) for c, v in s.items()}))
    print("hecho", k, flush=True)
tab = pd.DataFrame(filas); tab.to_csv(out / "resumen.csv", index=False)
print(tab[["variante", "periodo", "CAGR", "Sharpe", "MaxDD", "CostesAnualPct", "Gross", "ops"]].to_string(index=False))
