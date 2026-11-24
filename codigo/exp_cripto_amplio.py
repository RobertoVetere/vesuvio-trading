"""Candidatas extra para el universo amplio: monedas que fueron grandes en algún momento (Yahoo).
Las que no existan en Yahoo se descartan. El panel decide cuándo era operable cada una (liquidez en ese momento)."""
import data as D
EXTRA = ["MATIC-USD", "POL28321-USD", "ALGO-USD", "VET-USD", "ICP-USD", "APT21794-USD", "ARB11841-USD", "OP-USD",
         "SHIB-USD", "PEPE24478-USD", "INJ-USD", "AAVE-USD", "MKR-USD", "SAND-USD", "MANA-USD", "AXS-USD", "THETA-USD",
         "XTZ-USD", "EGLD-USD", "FTM-USD", "GRT6719-USD", "CRV-USD", "SNX-USD", "COMP5692-USD", "CHZ-USD", "ENJ-USD",
         "BAT-USD", "ZIL-USD", "KSM-USD", "RUNE-USD", "KAS-USD", "SUI20947-USD", "TON11419-USD", "SEI-USD", "TIA22861-USD",
         "IMX10603-USD", "STX4847-USD", "LDO-USD", "RENDER-USD", "HNT-USD", "FLOW-USD", "MINA-USD", "KAVA-USD",
         "1INCH-USD", "YFI-USD", "SUSHI-USD", "CAKE-USD", "WIF-USD", "BONK-USD"]
EXTRA_OK, FALLIDAS = [], []
for t in EXTRA:
    p = D.RAW / f"{t}.parquet"
    if not p.exists():
        try:
            df = D.fetch(t)
            if len(df) > 300: df.to_parquet(p)
        except Exception as e:
            pass
    if p.exists():
        EXTRA_OK.append(t)
    else:
        FALLIDAS.append(t)
