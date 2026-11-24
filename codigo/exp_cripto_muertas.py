"""Monedas 'muertas' con datos en la caché (descargadas por exp_cripto.py); las que falten se descargan."""
import data as D
MUERTAS = ["LUNC-USD", "FTT-USD", "EOS-USD", "XEM-USD", "IOTA-USD", "DASH-USD", "NEO-USD", "WAVES-USD", "BSV-USD",
           "ZEC-USD", "XMR-USD", "QTUM-USD", "ICX-USD", "OMG-USD", "LSK-USD", "BTG-USD", "CEL-USD", "BTT-USD"]
MUERTAS_OK = []
for t in MUERTAS:
    p = D.RAW / f"{t}.parquet"
    if not p.exists():
        try:
            df = D.fetch(t)
            if len(df) > 400: df.to_parquet(p)
        except Exception as e:
            print("FALLA", t, e)
    if p.exists(): MUERTAS_OK.append(t)
