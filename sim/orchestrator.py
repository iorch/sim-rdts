"""Orquesta UNA corrida: N nodos Knots + (20-N) Core en regtest, malla P2P completa,
mina según un modelo de hashpower (cada nodo = 1/20) e inyecta bloques spam desde Core
(válidos para Core, inválidos por consenso para Knots/RDTS). Mide si la cadena se parte.

Uso directo:  python3 orchestrator.py --knots 5 --blocks 60 --pspam 1.0 --seed 1
"""

import os as _os
_ROOT = _os.environ.get("SIM_RDTS_ROOT") or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import argparse
import concurrent.futures as cf
import random
import subprocess
import sys
import time

sys.path.insert(0, _os.path.join(_ROOT, "sim"))
from rpc import Node, RPCError  # noqa: E402
import spam_txs as S  # noqa: E402

TOTAL = 20
NET = "bip110net"
CONF = _os.path.join(_ROOT, "docker/conf")
IMG_CORE = "bip110-core:31.1"
IMG_KNOTS = "bip110-knots:29.3"
RDTS_ARG = "-vbparams=reduced_data:-1:9223372036854775807"
BASE_PORT = 18401
WALLET = "w"


def sh(*args, check=True):
    return subprocess.run(args, capture_output=True, text=True, check=check).stdout.strip()


def ensure_network():
    out = sh("docker", "network", "ls", "--format", "{{.Name}}")
    if NET not in out.split():
        sh("docker", "network", "create", "--subnet", "172.30.0.0/16", NET)


def container_name(run_id, idx):
    return f"b110_{run_id}_{idx}"


class Network:
    def __init__(self, n_knots, run_id, kinds=None, weights=None):
        # modo simple (sim-1): n_knots -> tipos uniformes, cada nodo peso 1.
        # modo pesado (sim-2): kinds[] y weights[] explícitos (hashpower heterogéneo).
        if kinds is None:
            assert 0 <= n_knots <= TOTAL
            kinds = ["knots"] * n_knots + ["core"] * (TOTAL - n_knots)
        self.kinds = kinds
        self.n = len(kinds)
        self.n_knots = kinds.count("knots")
        self.weights = list(weights) if weights else [1.0] * self.n
        assert len(self.weights) == self.n
        self.run_id = run_id
        self.nodes = []
        self.adaptive = False       # si True, un minero Core deja de incluir datos tras sufrir orfandad
        self.core_gaveup = set()    # índices de nodos Core que ya dejaron de spamear

    def start(self):
        ensure_network()
        self._teardown_silent()
        for idx, kind in enumerate(self.kinds):
            name = container_name(self.run_id, idx)
            cmd = ["docker", "run", "-d", "--name", name, "--network", NET,
                   "-v", f"{CONF}:/conf:ro",
                   "-p", f"{BASE_PORT + idx}:18443",
                   IMG_KNOTS if kind == "knots" else IMG_CORE]
            if kind == "knots":
                cmd.append(RDTS_ARG)
            sh(*cmd)
            self.nodes.append(Node(name, BASE_PORT + idx, kind))
        # esperar RPC en paralelo
        with cf.ThreadPoolExecutor(max_workers=self.n) as ex:
            list(ex.map(lambda n: n.wait_ready(90), self.nodes))
        return self

    def _teardown_silent(self):
        names = [container_name(self.run_id, i) for i in range(self.n)]
        subprocess.run(["docker", "rm", "-f", *names],
                       capture_output=True, text=True, check=False)

    def teardown(self):
        self._teardown_silent()

    # -- topología P2P: malla completa (una dirección por par basta, la conexión es bidireccional)
    def connect_mesh(self):
        for i in range(self.n):
            for j in range(i + 1, self.n):
                peer = f"{container_name(self.run_id, j)}:18444"
                try:
                    self.nodes[i].call("addnode", peer, "add", True)
                except RPCError:
                    self.nodes[i].call("addnode", peer, "add")

    # -- wallets + reparto de fondos para poder construir spam desde cualquier nodo Core
    def bootstrap(self):
        with cf.ThreadPoolExecutor(max_workers=self.n) as ex:
            list(ex.map(lambda n: n.call("createwallet", WALLET), self.nodes))
        self.addr = [n.wallet(WALLET, "getnewaddress") for n in self.nodes]
        miner = self.nodes[0]
        miner.call("generatetoaddress", 101, self.addr[0])
        # repartir 1 BTC a cada otro nodo (para fondos de spam), luego confirmar
        outs = {self.addr[i]: 1.0 for i in range(1, self.n)}
        miner.wallet(WALLET, "sendmany", "", outs)
        miner.call("generatetoaddress", 1, self.addr[0])
        self._settle(3.0)
        # sanidad: todos a la misma altura/tip
        tips = {n.name: n.call("getbestblockhash") for n in self.nodes}
        assert len(set(tips.values())) == 1, f"bootstrap no sincronizó: {tips}"

    def _settle(self, secs):
        time.sleep(secs)

    def mine_round(self, idx, p_spam, rng, spam_kind):
        """El nodo idx mina 1 bloque. Core con probabilidad p_spam mina un bloque con datos,
        salvo que ya se haya 'rendido' (modo adaptativo). Devuelve (tipo, hash_spam, idx)."""
        node = self.nodes[idx]
        spam_ok = (node.kind == "core" and idx not in self.core_gaveup
                   and rng.random() < p_spam)
        if spam_ok:
            try:
                kind, txs = S.build_spam(node, WALLET, spam_kind, rng)
                h = node.call("generateblock", self.addr[idx], txs)["hash"]
                return ("spam", h, idx)
            except (RPCError, StopIteration):
                # sin fondos u otro fallo: cae a bloque limpio
                node.call("generatetoaddress", 1, self.addr[idx])
                return ("clean_fallback", None, idx)
        else:
            node.call("generatetoaddress", 1, self.addr[idx])
            return ("clean", None, idx)

    # -- métricas de fork al final de la corrida
    def measure(self):
        info = []
        for n in self.nodes:
            info.append((n, n.call("getbestblockhash"), n.call("getblockcount")))
        core = [(n, h, c) for (n, h, c) in info if n.kind == "core"]
        knots = [(n, h, c) for (n, h, c) in info if n.kind == "knots"]

        def majority_hash(group):
            hs = [h for (_, h, _) in group]
            return max(set(hs), key=hs.count) if hs else None

        core_hash = majority_hash(core)
        knots_hash = majority_hash(knots)
        core_h = max((c for (_, _, c) in core), default=0)
        knots_h = max((c for (_, _, c) in knots), default=0)
        core_consensus = len({h for (_, h, _) in core}) <= 1
        knots_consensus = len({h for (_, h, _) in knots}) <= 1

        fork = bool(core) and bool(knots) and core_hash != knots_hash
        common_h = self._common_height() if fork else min(core_h, knots_h)
        fork_depth = max(core_h, knots_h) - common_h if fork else 0
        winner = ("core" if core_h > knots_h else "knots" if knots_h > core_h else "tie")
        return {
            "n_knots": self.n_knots, "core_height": core_h, "knots_height": knots_h,
            "common_height": common_h, "fork": fork, "fork_depth": fork_depth,
            "winner": winner, "core_consensus": core_consensus,
            "knots_consensus": knots_consensus,
        }

    def _common_height(self):
        """Mayor altura donde la cadena Core y la Knots comparten hash de bloque."""
        core = next(n for n in self.nodes if n.kind == "core")
        knots = next(n for n in self.nodes if n.kind == "knots")
        h = min(core.call("getblockcount"), knots.call("getblockcount"))
        while h > 0:
            try:
                if core.call("getblockhash", h) == knots.call("getblockhash", h):
                    return h
            except RPCError:
                pass
            h -= 1
        return 0


def _drive(net, blocks, p_spam, seed, spam_kind, keep):
    """Bucle común: arranca red, mina `blocks` rondas (minero ponderado), mide fork."""
    rng = random.Random(seed)
    t0 = time.time()
    try:
        net.start()
        net.connect_mesh()
        net.bootstrap()
        events = {"spam": 0, "clean": 0, "clean_fallback": 0}
        node_ids = range(net.n)
        # instrumentación de reorgs: seguimos la punta de un nodo Core representativo.
        # Cada vez que su punta anterior queda huérfana (confirmations == -1), Core tiró su
        # cadena para adoptar la limpia de Knots. Contamos eventos y bloques descartados.
        rep = next((n for n in net.nodes if n.kind == "core"), None)
        prev_tip = rep.call("getbestblockhash") if rep else None
        core_reorgs = 0
        core_discarded = 0
        spam_hashes = {}            # hash del bloque con datos -> índice del minero Core que lo produjo

        def orphaned(h):
            """True si el bloque h NO está en la cadena activa de Core (quedó huérfano)."""
            try:
                return rep.call("getblockheader", h)["confirmations"] == -1
            except RPCError:
                return False

        for r in range(blocks):
            # modelo de hashpower: minero elegido PONDERADO por su peso (uniforme si todos=1)
            idx = rng.choices(node_ids, weights=net.weights, k=1)[0]
            kind, bhash, midx = net.mine_round(idx, p_spam, rng, spam_kind)
            if kind == "spam":
                spam_hashes[bhash] = midx
            events[kind if kind in events else "clean"] = events.get(
                kind if kind in events else "clean", 0) + 1
            net._settle(0.35)                   # propagación P2P (localhost)
            if rep:
                cur = rep.call("getbestblockhash")
                if cur != prev_tip:
                    try:
                        if rep.call("getblockheader", prev_tip)["confirmations"] == -1:
                            core_reorgs += 1
                            h, d = prev_tip, 0
                            while True:                 # contar bloques huérfanos de esa rama
                                hdr = rep.call("getblockheader", h)
                                if hdr["confirmations"] != -1:
                                    break
                                d += 1
                                h = hdr.get("previousblockhash")
                                if not h:
                                    break
                            core_discarded += d
                    except RPCError:
                        pass
                    prev_tip = cur
                # modo adaptativo: un minero Core cuyo bloque con datos quedó huérfano deja de spamear
                if net.adaptive:
                    for h, mi in spam_hashes.items():
                        if mi not in net.core_gaveup and orphaned(h):
                            net.core_gaveup.add(mi)
        net._settle(3.0)                        # asentamiento final
        tot = sum(net.weights)
        knots_share = sum(w for w, k in zip(net.weights, net.kinds) if k == "knots") / tot
        m = net.measure()
        # probabilidad de orfandad REAL de un bloque con datos = huérfanos / producidos
        spam_produced = len(spam_hashes)
        spam_orphaned = sum(1 for h in spam_hashes if orphaned(h)) if rep else 0
        orphan_rate = (spam_orphaned / spam_produced) if spam_produced else 0.0
        # premio de equilibrio: cuánto (como fracción del premio de bloque) debe pagar el dato
        # para que valga el riesgo de orfandad.  d* = p/(1-p)
        breakeven_fee = (orphan_rate / (1 - orphan_rate)) if orphan_rate < 1 else float("inf")
        # "softfork gana" = convergen (Knots nunca acepta spam, así que converger = cadena limpia)
        m.update({"seed": seed, "blocks": blocks, "p_spam": p_spam,
                  "spam_kind": spam_kind, "spam_blocks": events["spam"],
                  "knots_share": round(knots_share, 4), "n_nodes": net.n,
                  "softfork_wins": (not m["fork"]) or m["fork_depth"] < 6,
                  "core_reorgs": core_reorgs, "core_blocks_discarded": core_discarded,
                  "spam_produced": spam_produced, "spam_orphaned": spam_orphaned,
                  "orphan_rate": round(orphan_rate, 4),
                  "breakeven_fee": (round(breakeven_fee, 4) if breakeven_fee != float("inf") else None),
                  "core_gaveup": len(net.core_gaveup), "adaptive": net.adaptive,
                  "secs": round(time.time() - t0, 1)})
        return m
    finally:
        if not keep:
            net.teardown()


def run_once(n_knots, blocks=60, p_spam=1.0, seed=0, spam_kind="random", keep=False):
    net = Network(n_knots, f"{n_knots:02d}_{seed}")
    return _drive(net, blocks, p_spam, seed, spam_kind, keep)


def run_weighted(kinds, weights, scenario_id, blocks=60, p_spam=1.0, seed=0,
                 spam_kind="random", keep=False, adaptive=False):
    """sim-2: red con hashpower heterogéneo (kinds[] + weights[] explícitos).
    adaptive=True: un minero Core deja de incluir datos tras ver un bloque suyo huérfano."""
    net = Network(0, scenario_id, kinds=kinds, weights=weights)
    net.adaptive = adaptive
    return _drive(net, blocks, p_spam, seed, spam_kind, keep)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--knots", type=int, required=True)
    ap.add_argument("--blocks", type=int, default=60)
    ap.add_argument("--pspam", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--kind", default="random", choices=["random", "op_return", "big_witness"])
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    m = run_once(a.knots, a.blocks, a.pspam, a.seed, a.kind, a.keep)
    import json
    print(json.dumps(m, indent=2))
