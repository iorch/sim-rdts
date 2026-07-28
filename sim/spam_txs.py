"""Construye transacciones VÁLIDAS para Bitcoin Core pero INVÁLIDAS para Knots (RDTS/BIP-110).

Cada builder recibe un `rpc.Node` (que debe ser Core, con wallet cargada) y devuelve una
lista de hex de txs firmadas listas para `generateblock` (se incluyen en orden). El bloque
resultante es aceptado por Core y RECHAZADO a nivel de consenso por Knots.

Reglas RDTS ejercitadas:
  - regla 1: salida OP_RETURN > 83 bytes            -> bad-txns-vout-script-toolarge
  - regla 2: item de witness > 256 bytes            -> (script/witness too large)
Reutiliza el functional test framework de Bitcoin Core como librería para serializar scripts.
"""
import os
import sys

# functional test framework (reutilizado como librería, no como runner)
_TF = "/Users/jmo/bitcoin/btc/test/functional"
if _TF not in sys.path:
    sys.path.insert(0, _TF)

from test_framework.script import CScript, OP_DROP, OP_TRUE  # noqa: E402
from test_framework.address import script_to_p2wsh  # noqa: E402
from test_framework.messages import (  # noqa: E402
    CTransaction, CTxIn, CTxOut, COutPoint, CTxInWitness, tx_from_hex,
)

def _fund_and_sign(node, wallet, raw_hex):
    funded = node.wallet(wallet, "fundrawtransaction", raw_hex, {"fee_rate": 5})["hex"]
    signed = node.wallet(wallet, "signrawtransactionwithwallet", funded)
    assert signed.get("complete"), f"firma incompleta: {signed}"
    return signed["hex"]


def build_op_return(node, wallet, data_bytes=100):
    """Regla 1: una tx con OP_RETURN de `data_bytes` (>83) bytes. Autocontenida."""
    data_hex = ("ab" * data_bytes)  # data_bytes bytes de payload
    raw = node.wallet(wallet, "createrawtransaction", [], [{"data": data_hex}])
    return [_fund_and_sign(node, wallet, raw)]


def build_big_witness(node, wallet, blob_bytes=300):
    """Regla 2: item de witness > 256 bytes (estilo inscripción).

    commit: paga a P2WSH(OP_DROP OP_TRUE) (spk de 34 B, limpio).
    reveal: gasta ese output con witness = [<blob>, witnessScript]; el blob (300 B) supera
            el tope RDTS de 256 B pero queda bajo el límite de 520 B de Core -> válido en Core.
    Ambas se devuelven en orden [commit, reveal] para un solo generateblock.
    """
    ws = CScript([OP_DROP, OP_TRUE])
    p2wsh_addr = script_to_p2wsh(ws)
    # commit: salida de 0.001 BTC al P2WSH
    raw = node.wallet(wallet, "createrawtransaction", [], [{p2wsh_addr: 0.001}])
    commit_hex = _fund_and_sign(node, wallet, raw)
    commit = tx_from_hex(commit_hex)
    commit.rehash()
    # localizar el vout que paga al P2WSH
    target_spk = bytes.fromhex(node.wallet(wallet, "getaddressinfo", p2wsh_addr)["scriptPubKey"])
    vout = next(i for i, o in enumerate(commit.vout) if o.scriptPubKey == target_spk)
    # reveal: gasta commit[vout], paga a una dirección propia (menos fee)
    sink = node.wallet(wallet, "getnewaddress")
    sink_spk = bytes.fromhex(node.wallet(wallet, "getaddressinfo", sink)["scriptPubKey"])
    reveal = CTransaction()
    reveal.vin.append(CTxIn(COutPoint(int(commit.hash, 16), vout)))
    reveal.vout.append(CTxOut(90000, sink_spk))  # 0.001 - fee
    reveal.wit.vtxinwit.append(CTxInWitness())
    reveal.wit.vtxinwit[0].scriptWitness.stack = [b"\x5a" * blob_bytes, bytes(ws)]
    reveal.rehash()
    return [commit_hex, reveal.serialize().hex()]


# registro de builders disponibles (nombre -> callable)
BUILDERS = {
    "op_return": build_op_return,
    "big_witness": build_big_witness,
}


def build_spam(node, wallet, kind, rng=None):
    """Devuelve la lista de hex de txs para un bloque spam del tipo dado (o aleatorio)."""
    if kind == "random":
        import random
        kind = (rng or random).choice(list(BUILDERS))
    return kind, BUILDERS[kind](node, wallet)
