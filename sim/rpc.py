"""Cliente JSON-RPC mínimo (stdlib) para hablar con los bitcoind en regtest.

Cada nodo expone su RPC 18443 mapeado a un puerto único del host (18401..).
"""
import json
import time
import urllib.request
import urllib.error

RPC_USER = "bip110"
RPC_PASS = "bip110pass"


class RPCError(Exception):
    def __init__(self, code, message):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class Node:
    def __init__(self, name, host_port, kind):
        self.name = name              # p.ej. "n03"
        self.port = host_port         # puerto RPC en el host
        self.kind = kind              # "core" | "knots"
        self.url = f"http://127.0.0.1:{host_port}/"
        self._id = 0

    def _post(self, path, method, params):
        self._id += 1
        payload = json.dumps({"jsonrpc": "1.0", "id": self._id,
                              "method": method, "params": list(params)}).encode()
        req = urllib.request.Request(self.url.rstrip("/") + path, data=payload)
        req.add_header("Content-Type", "application/json")
        import base64
        tok = base64.b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode()
        req.add_header("Authorization", "Basic " + tok)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = json.loads(e.read().decode())
        if body.get("error"):
            err = body["error"]
            raise RPCError(err["code"], err["message"])
        return body["result"]

    def call(self, method, *params):
        return self._post("", method, params)

    def wallet(self, wallet_name, method, *params):
        return self._post(f"/wallet/{wallet_name}", method, params)

    def wait_ready(self, timeout=60):
        """Espera a que el RPC responda (bitcoind arrancando)."""
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                self.call("getblockchaininfo")
                return True
            except (RPCError, urllib.error.URLError, ConnectionError, OSError) as e:
                last = e
                time.sleep(0.5)
        raise TimeoutError(f"{self.name} RPC no respondió: {last}")

    def __repr__(self):
        return f"<Node {self.name} {self.kind} :{self.port}>"
