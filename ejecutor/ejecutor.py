"""Ejecutor de VESUVIO-TRADING en Kraken (contado, solo largos).

Lee los objetivos del día de la estrategia configurada (estado/state.json, escritos por paper.py) y las señales
(estado/publico/ejecucion.json), y los convierte en órdenes respetando ejecutor/limites.json:
- capital máximo, orden máxima, pérdida diaria máxima (activa el interruptor de parada), interruptor manual
  (fichero estado/ejecutor/PARADO);
- compras: orden limitada solo-creador al mejor precio de compra, con STOP CONDICIONAL (red de seguridad a
  red_mult x vol) que Kraken crea en cuanto la compra se ejecuta;
- salidas (objetivo 0): orden a mercado;
- posiciones ya abiertas sin red: se coloca la orden de stop.
modo "prueba": con claves, valida cada orden en Kraken (validate=true) sin enviarla; sin claves, simula una cartera
ficticia (capital_simulado_eur). modo "real": envía. Sale con código 3 si se activa la parada por pérdidas.
Uso (desde la raíz del repo): python ejecutor/ejecutor.py
"""
import json, math, os, sys, time
from pathlib import Path
from kraken import Kraken

RAIZ = Path(__file__).resolve().parent.parent
EST = RAIZ / "estado"
DIR = EST / "ejecutor"
REF_COMPRA, REF_RED = 7777, 8888


def leer(p, defecto=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return defecto


def abajo(x, dec):
    f = 10 ** dec
    return math.floor(x * f) / f


def main():
    DIR.mkdir(parents=True, exist_ok=True)
    L = leer(RAIZ / "ejecutor/limites.json")
    modo, est = L["modo"], L["estrategia"]
    hoy = time.strftime("%Y-%m-%d")
    log = dict(fecha=hoy, modo=modo, estrategia=est, ordenes=[], avisos=[], ok=False)

    def fin(codigo=0):
        log["ok"] = codigo == 0
        (DIR / "ultimo.json").write_text(json.dumps(log, ensure_ascii=False, indent=1))
        with open(DIR / "historial.jsonl", "a") as f:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
        print(json.dumps(log, ensure_ascii=False, indent=1))
        sys.exit(codigo)

    S = leer(EST / "state.json")
    objs = S["estrategias"][est]["objetivos"]
    decision = max(objs) if objs else None
    pesos = objs.get(decision, {}) if decision else {}
    senal = (leer(EST / "publico/ejecucion.json", {}) or {}).get("principal") or {}
    log.update(decision=decision, pesos=pesos)

    k = Kraken(os.environ.get("KRAKEN_KEY") or None, os.environ.get("KRAKEN_SECRET") or None)
    con_claves = bool(k.clave and k.secreto)
    log["con_claves"] = con_claves
    if modo == "real" and not con_claves:
        log["avisos"].append("modo real sin claves: no se hace nada")
        fin(1)

    pares = L["pares"]
    info = k.publico("AssetPairs", pair=",".join(pares.values()))
    tick = k.publico("Ticker", pair=",".join(pares.values()))
    alias = {v["altname"]: (kk, v) for kk, v in info.items()}
    mercado = {}
    for a, p in pares.items():
        kk, v = alias[p]
        t = tick[kk]
        mercado[a] = dict(par=p, base=v["base"], lot=int(v["lot_decimals"]), pdec=int(v["pair_decimals"]),
                          ordermin=float(v.get("ordermin", 0)), costmin=float(v.get("costmin", 0) or 0),
                          bid=float(t["b"][0]), ask=float(t["a"][0]), last=float(t["c"][0]))

    # cartera actual
    if con_claves:
        bal = {kk: float(v) for kk, v in k.privado("Balance").items()}
        eur = bal.get("ZEUR", 0.0)
        tenencia = {a: bal.get(m["base"], 0.0) for a, m in mercado.items()}
        abiertas = k.privado("OpenOrders").get("open", {})
    else:
        sim = leer(DIR / "simulada.json", {"eur": L["capital_simulado_eur"], "tenencia": {}})
        eur, tenencia, abiertas = sim["eur"], {a: sim["tenencia"].get(a, 0.0) for a in mercado}, {}
        log["avisos"].append("sin claves: cartera simulada, órdenes no validadas en Kraken")
    valor = eur + sum(tenencia[a] * mercado[a]["last"] for a in mercado)
    log.update(eur=round(eur, 2), tenencia=tenencia, valor_eur=round(valor, 2))

    # interruptores
    if (DIR / "PARADO").exists():
        log["avisos"].append("PARADO activo: no se opera (borra estado/ejecutor/PARADO para reanudar)")
        fin(0)
    prev = leer(DIR / "ultimo.json", {}) or {}
    if prev.get("valor_eur") and valor < prev["valor_eur"] * (1 - L["perdida_diaria_max_pct"] / 100):
        (DIR / "PARADO").write_text(f"{hoy}: valor {valor:.2f} < {prev['valor_eur']} -{L['perdida_diaria_max_pct']} %\n")
        log["avisos"].append("pérdida diaria máxima superada: PARADO activado")
        fin(3)

    capital = min(valor, L["capital_max_eur"])
    validar = modo != "real"

    def enviar(desc, **params):
        o = dict(desc=desc, **params)
        if con_claves:
            try:
                r = k.privado("AddOrder", **params, **({"validate": "true"} if validar else {}))
                o["respuesta"] = r.get("descr", r)
            except Exception as e:
                o["error"] = str(e)
                log["avisos"].append(f"orden rechazada: {desc}: {e}")
        log["ordenes"].append(o)
        return o

    # cancelar compras sin ejecutar de días anteriores
    if con_claves and not validar:
        for oid, o in abiertas.items():
            if int(o.get("userref") or 0) == REF_COMPRA:
                k.privado("CancelOrder", txid=oid)
                log["avisos"].append(f"cancelada compra pendiente {oid}")

    for a, m in mercado.items():
        w = float(pesos.get(a, 0.0))
        if w < 0:
            log["avisos"].append(f"{a}: peso negativo ignorado (contado, solo largos)")
            w = 0.0
        objetivo_eur = w * capital
        actual_eur = tenencia[a] * m["last"]
        dif_eur = objetivo_eur - actual_eur
        s = senal.get(a, {}) or {}
        red_usd = (s["extremo"] - L["red_mult"] * s["vol_atr"]) if s.get("pos", 0) > 0 and s.get("extremo") and s.get("vol_atr") else None
        red = round(red_usd * m["last"] / s["precio"], m["pdec"]) if red_usd and s.get("precio") else None
        if w == 0 and tenencia[a] * m["last"] >= max(m["costmin"], 5):
            vol = abajo(tenencia[a], m["lot"])
            enviar(f"SALIDA {a}: vender todo", pair=m["par"], type="sell", ordertype="market", volume=f"{vol:.{m['lot']}f}")
            if not con_claves:
                eur += vol * m["bid"]; tenencia[a] -= vol
            continue
        if w > 0 and (actual_eur == 0 or abs(dif_eur) >= 0.5 * objetivo_eur) and dif_eur > 0:
            gasto = min(dif_eur, L["orden_max_eur"], eur * 0.995)
            vol = abajo(gasto / m["bid"], m["lot"])
            if vol < m["ordermin"] or vol * m["bid"] < max(m["costmin"], 10):
                log["avisos"].append(f"{a}: compra de {gasto:.2f} € por debajo del mínimo de Kraken")
            elif red is None:
                log["avisos"].append(f"{a}: sin nivel de red de seguridad: NO se compra")
            else:
                enviar(f"COMPRA {a}: {gasto:.2f} € con red a {red}", pair=m["par"], type="buy", ordertype="limit",
                       price=f"{m['bid']:.{m['pdec']}f}", volume=f"{vol:.{m['lot']}f}", oflags="post", userref=REF_COMPRA,
                       expiretm=f"+{L['caducidad_orden_seg']}", **{"close[ordertype]": "stop-loss", "close[price]": f"{red}"})
                if not con_claves:
                    eur -= vol * m["bid"] * 1.0025; tenencia[a] += vol
        elif w > 0 and dif_eur < 0 and abs(dif_eur) >= 0.5 * objetivo_eur:
            vol = abajo(-dif_eur / m["ask"], m["lot"])
            if vol >= m["ordermin"]:
                enviar(f"REDUCIR {a}", pair=m["par"], type="sell", ordertype="limit", price=f"{m['ask']:.{m['pdec']}f}",
                       volume=f"{vol:.{m['lot']}f}", oflags="post", userref=REF_COMPRA, expiretm=f"+{L['caducidad_orden_seg']}")
        # red de seguridad para lo que ya se tiene
        if tenencia[a] > 0 and red:
            tiene_red = any(int(o.get("userref") or 0) == REF_RED and o["descr"]["pair"] == m["par"] for o in abiertas.values())
            if not tiene_red:
                enviar(f"RED {a} a {red}", pair=m["par"], type="sell", ordertype="stop-loss", price=f"{red}",
                       volume=f"{abajo(tenencia[a], m['lot']):.{m['lot']}f}", userref=REF_RED)
        elif tenencia[a] * m["last"] > 10 and not red:
            log["avisos"].append(f"{a}: posición sin nivel de red calculable: revisar")

    if not con_claves:
        (DIR / "simulada.json").write_text(json.dumps(dict(eur=eur, tenencia=tenencia), indent=1))
    if any("error" in o for o in log["ordenes"]):
        fin(2)
    fin(0)


if __name__ == "__main__":
    main()
