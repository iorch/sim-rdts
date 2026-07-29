"""Experimento 4 — cuándo la TOPOLOGÍA de la red importa.

Knots no retransmite bloques inválidos por RDTS. Si los mineros Core dependen de retransmitirse
sus bloques con datos entre sí, y esa retransmisión pasa por nodos Knots (que la bloquean), la
minería Core se fragmenta. Clave: esto solo muerde cuando el hashpower Core está DISPERSO en
muchos nodos (ninguno supera por sí solo al bando Knots coordinado); un pool grande es inmune
porque extiende su propia cadena sin depender de nadie.

Config: Core 78% DISPERSO en 16 nodos (~4.875% c/u) vs Knots 22% en 4 nodos (bien conectados).
A hashpower FIJO (Core mayoría), se barre core_core_prob = fracción de enlaces Core-Core:
  1.0 = malla completa (Core coordina) ..... 0.0 = Core solo conectado vía Knots (fragmentado).
Se mide si el softfork gana SOLO por efecto de la topología.

Uso:  python3 topology.py --runs 8 --blocks 45
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orchestrator import run_weighted  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "topology.csv")

# Core 78% disperso en 16 nodos; Knots 22% en 4 nodos. Ningún Core (4.875%) supera al Knots total.
KINDS = ["core"] * 16 + ["knots"] * 4
WEIGHTS = [78 / 16] * 16 + [22 / 4] * 4
PROBS = [1.0, 0.75, 0.5, 0.25, 0.1, 0.0]

FIELDS = ["core_core_prob", "run", "seed", "softfork_wins", "fork_depth",
          "orphan_rate", "core_height", "knots_height", "core_reorgs", "secs"]


def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                done.add((float(r["core_core_prob"]), int(r["run"])))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--blocks", type=int, default=45)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done(RESULTS)
    new = not os.path.exists(RESULTS)
    f = open(RESULTS, "a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new:
        w.writeheader(); f.flush()

    plan = [(p, r) for p in PROBS for r in range(a.runs) if (p, r) not in done]
    print(f"[topology] {len(plan)} corridas pendientes "
          f"(Core 78% en 16 nodos, Knots 22% en 4; probs={PROBS})", flush=True)
    for i, (p, r) in enumerate(plan, 1):
        seed = 8000 + int(p * 100) * 10 + r
        try:
            m = run_weighted(KINDS, WEIGHTS, f"topo_{int(p*100)}_{seed}", blocks=a.blocks,
                             p_spam=1.0, seed=seed, spam_kind="random", core_core_prob=p)
        except Exception as e:
            print(f"  !! prob {p} run {r} FALLÓ: {type(e).__name__}: {e}", flush=True)
            continue
        w.writerow({
            "core_core_prob": p, "run": r, "seed": seed,
            "softfork_wins": m["softfork_wins"], "fork_depth": m["fork_depth"],
            "orphan_rate": m["orphan_rate"], "core_height": m["core_height"],
            "knots_height": m["knots_height"], "core_reorgs": m["core_reorgs"],
            "secs": m["secs"]}); f.flush()
        print(f"  [{i}/{len(plan)}] prob={p} run={r} -> gana_softfork={m['softfork_wins']} "
              f"orfandad={m['orphan_rate']:.2f} core_h={m['core_height']} "
              f"knots_h={m['knots_height']} ({m['secs']}s)", flush=True)
    f.close()
    print("[topology] listo", flush=True)


if __name__ == "__main__":
    main()
