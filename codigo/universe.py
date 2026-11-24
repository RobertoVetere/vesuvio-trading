"""Universo de activos. Clase -> lista de tickers Yahoo."""

US = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","V","UNH","XOM","JNJ","PG","MA",
      "HD","CVX","MRK","ABBV","LLY","PEP","KO","AVGO","COST","WMT","BAC","PFE","TMO","CSCO","MCD",
      "ADBE","CRM","NFLX","AMD","INTC","ORCL","DIS","NKE","CAT","BA","GS","MS","WFC","C","GE","HON",
      "UPS","LMT","RTX","DE","COP","SLB","OXY","F","GM","DAL","UAL","CCL","MAR","NEE","DUK","T","VZ",
      "PLD","AMT","FCX","NEM","MU","QCOM","TXN"]

EU = ["SAN.MC","BBVA.MC","ITX.MC","IBE.MC","TEF.MC","REP.MC","CABK.MC","AENA.MC","FER.MC","AMS.MC",
      "IAG.MC","ACS.MC","GRF.MC","MAP.MC","NTGY.MC","ENG.MC","ELE.MC","CLNX.MC","ASML.AS","SAP.DE",
      "SIE.DE","ALV.DE","MC.PA","OR.PA","TTE.PA","SAN.PA","AIR.PA","BNP.PA","RMS.PA","NESN.SW",
      "NOVN.SW","ROG.SW","SHEL.L","AZN.L","HSBA.L","BP.L","RIO.L","ENEL.MI","ISP.MI","UCG.MI"]

ETF = ["SPY","QQQ","IWM","DIA","EFA","EEM","VGK","EWJ","FXI","EWZ","XLK","XLF","XLE","XLV","XLI",
       "XLY","XLP","XLU","XLB","XLRE","XLC","SMH","KRE","XBI","ITB","JETS","TLT","IEF","SHY","HYG",
       "LQD","GLD","SLV","USO","UNG","DBA","UUP","FXE"]

CRYPTO = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD","LINK-USD",
          "DOT-USD","LTC-USD","BCH-USD","TRX-USD","ATOM-USD","XLM-USD","UNI7083-USD","NEAR-USD",
          "ETC-USD","FIL-USD","HBAR-USD"]

# Solo información (no operables): macro / régimen
MACRO = ["^VIX","^GSPC","^IBEX","^STOXX50E","^TNX","^IRX","EURUSD=X","GBPUSD=X","CHF=X","DX-Y.NYB",
         "GC=F","CL=F","HG=F","BZ=F"]

CLASSES = {"US": US, "EU": EU, "ETF": ETF, "CRYPTO": CRYPTO, "MACRO": MACRO}
TRADABLE = {k: v for k, v in CLASSES.items() if k != "MACRO"}

def asset_class(t):
    for k, v in CLASSES.items():
        if t in v:
            return k
    raise KeyError(t)

def currency(t):
    if t.endswith((".MC",".AS",".DE",".PA",".MI")): return "EUR"
    if t.endswith(".SW"): return "CHF"
    if t.endswith(".L"): return "GBP"   # Yahoo cotiza en peniques (GBp)
    return "USD"
