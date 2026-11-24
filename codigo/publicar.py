"""Copia la salida de paper.py (out/) a estado/publico/ para el dashboard y escribe ejecucion.json.
Uso (desde codigo/): python publicar.py out salida.json"""
import json, shutil, sys
from pathlib import Path
import pandas as pd
out, salida = Path(sys.argv[1]), Path(sys.argv[2])
pub = Path(__file__).parent.parent / "estado/publico"
for f in ["nav.csv", "resumen.csv", "posiciones.csv", "operaciones.csv", "oportunidades.csv"]:
    shutil.copy(out / f, pub / f)
shutil.copy(pub.parent.parent / "noticias/noticias.csv", pub / "noticias.csv")
s = json.loads(salida.read_text())
ej = dict(fecha=str(pd.Timestamp.now(tz="Europe/Madrid").date()), ok=True, decision=s["decision"],
          datos_hasta=s["datos_hasta"], piloto_variante=s.get("piloto_2026"), principal=s.get("principal"))
(pub / "ejecucion.json").write_text(json.dumps(ej, ensure_ascii=False, indent=1, default=str))
print(json.dumps(ej, ensure_ascii=False))
