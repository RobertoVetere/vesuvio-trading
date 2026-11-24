"""Cliente mínimo de la API REST de Kraken (contado). Sin dependencias externas."""
import base64, hashlib, hmac, json, time, urllib.parse, urllib.request

API = "https://api.kraken.com"


def firma(ruta, datos, secreto_b64):
    """API-Sign = HMAC-SHA512(secreto, ruta + SHA256(nonce + postdata)), en base64."""
    post = urllib.parse.urlencode(datos)
    msg = ruta.encode() + hashlib.sha256((str(datos["nonce"]) + post).encode()).digest()
    return base64.b64encode(hmac.new(base64.b64decode(secreto_b64), msg, hashlib.sha512).digest()).decode()


class Kraken:
    def __init__(self, clave=None, secreto=None):
        self.clave, self.secreto = clave, secreto

    def _peticion(self, req):
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        if d.get("error"):
            raise RuntimeError(f"Kraken: {d['error']}")
        return d["result"]

    def publico(self, metodo, **params):
        q = ("?" + urllib.parse.urlencode(params)) if params else ""
        return self._peticion(urllib.request.Request(f"{API}/0/public/{metodo}{q}", headers={"User-Agent": "vesuvio"}))

    def privado(self, metodo, **params):
        if not (self.clave and self.secreto):
            raise RuntimeError("Sin claves de Kraken")
        ruta = f"/0/private/{metodo}"
        datos = {"nonce": int(time.time() * 1000), **params}
        h = {"API-Key": self.clave, "API-Sign": firma(ruta, datos, self.secreto), "User-Agent": "vesuvio",
             "Content-Type": "application/x-www-form-urlencoded"}
        return self._peticion(urllib.request.Request(API + ruta, urllib.parse.urlencode(datos).encode(), h))
