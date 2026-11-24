"""Envoltorio de data.py para Actions: descarga todo y escribe ../estado/publico/datos_meta.json.
Sale con error si falla más del 10 % del universo (sin datos fiables no se decide)."""
import json, sys
from pathlib import Path
import pandas as pd
import data
from universe import CLASSES
bad = data.download_all(force=True)
total = sum(len(v) for v in CLASSES.values())
meta = dict(fecha=str(pd.Timestamp.now(tz="Europe/Madrid").date()), total=total, fallidos=bad)
Path(__file__).parent.parent.joinpath("estado/publico/datos_meta.json").write_text(json.dumps(meta, ensure_ascii=False))
print(meta)
sys.exit(1 if len(bad) > 0.10 * total else 0)
