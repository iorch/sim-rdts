"""sim-2: hashpower heterogéneo y concentrado. Core en pocos mineros grandes (78%),
Knots disperso en muchos chicos (22%). Se van AGREGANDO mineros Knots grandes por paso
para encontrar dónde GANA el softfork (Core reorganiza a la cadena limpia → sin fork).

Config base (paso 0): 21 nodos, 100% hashpower
  Core (78%, 5 nodos):  25 · 20 · 15 · 10 · 8
  Knots (22%, 16 nodos): 3·3 · 2·2·2 · 1×9 · 0.5·0.5
Cada paso añade un minero Knots grande (raw 10,15,20,25,30,35) y renormaliza.

Uso:  python3 sim2.py --runs 12 --blocks 60
"""

import os as _os
_ROOT = _os.environ.get("SIM_RDTS_ROOT") or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, _os.path.join(_ROOT, "sim"))
from orchestrator import run_weighted  # noqa: E402

RESULTS = _os.path.join(_ROOT, "results/sim2.csv")

BASE_CORE = [25, 20, 15, 10, 8]                     # 5 nodos Core = 78%
BASE_KNOTS = [3, 3, 2, 2, 2] + [1] * 9 + [0.5, 0.5]  # 16 nodos Knots = 22%
# mineros Knots grandes añadidos por paso (raw). Se extiende más allá de 35 porque sim-1
# mostró que el cruce es una SUPERMAYORÍA de hashpower, no 50% — hay que llegar a ~85%.
ADD_KNOTS = [10, 15, 20, 25, 30, 35, 45, 60, 85]

FIELDS = ["step", "n_added", "knots_share", "n_nodes", "run", "seed",
          "fork", "fork_depth", "winner", "softfork_wins",
          "core_reorgs", "core_blocks_discarded",
          "core_height", "knots_height", "spam_blocks", "secs"]


def build_step(step):
    """Devuelve (kinds, weights) del paso `step` (0 = base, sin añadir)."""
    added = ADD_KNOTS[:step]
    kinds = ["core"] * len(BASE_CORE) + ["knots"] * (len(BASE_KNOTS) + len(added))
    weights = BASE_CORE + BASE_KNOTS + added
    return kinds, weights


def knots_share(step):
    _, w = build_step(step)
    kinds, _ = build_step(step)
    tot = sum(w)
    return sum(wi for wi, k in zip(w, kinds) if k == "knots") / tot


def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                done.add((int(r["step"]), int(r["run"])))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=12)
    ap.add_argument("--blocks", type=int, default=60)
    ap.add_argument("--pspam", type=float, default=1.0)
    ap.add_argument("--kind", default="random")
    a = ap.parse_args()

    steps = list(range(len(ADD_KNOTS) + 1))  # 0..6
    print("[sim2] plan de pasos:", flush=True)
    for s in steps:
        kinds, w = build_step(s)
        print(f"  paso {s}: {len(kinds)} nodos, knots_share={knots_share(s)*100:4.1f}% "
              f"(añadido raw {ADD_KNOTS[:s]})", flush=True)

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done(RESULTS)
    new = not os.path.exists(RESULTS)
    f = open(RESULTS, "a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new:
        w.writeheader(); f.flush()

    plan = [(s, r) for s in steps for r in range(a.runs) if (s, r) not in done]
    print(f"[sim2] {len(plan)} corridas pendientes (runs={a.runs}, blocks={a.blocks})", flush=True)
    t0 = time.time()
    for i, (s, r) in enumerate(plan, 1):
        kinds, weights = build_step(s)
        seed = 5000 + 100 * s + r
        try:
            m = run_weighted(kinds, weights, f"s2_{s}_{seed}", blocks=a.blocks,
                             p_spam=a.pspam, seed=seed, spam_kind=a.kind)
        except Exception as e:
            print(f"  !! paso {s} run {r} FALLÓ: {type(e).__name__}: {e}", flush=True)
            continue
        row = {"step": s, "n_added": s, "knots_share": round(knots_share(s), 4),
               "n_nodes": m["n_nodes"], "run": r, "seed": seed, "fork": m["fork"],
               "fork_depth": m["fork_depth"], "winner": m["winner"],
               "softfork_wins": m["softfork_wins"],
               "core_reorgs": m["core_reorgs"],
               "core_blocks_discarded": m["core_blocks_discarded"],
               "core_height": m["core_height"],
               "knots_height": m["knots_height"], "spam_blocks": m["spam_blocks"],
               "secs": m["secs"]}
        w.writerow(row); f.flush()
        eta = (time.time() - t0) / i * (len(plan) - i)
        print(f"  [{i}/{len(plan)}] paso {s} (knots {knots_share(s)*100:.0f}%) run {r} -> "
              f"softfork_wins={m['softfork_wins']} fork_depth={m['fork_depth']:2d} "
              f"({m['secs']}s) ETA {eta/60:.0f}m", flush=True)
    f.close()
    print(f"[sim2] listo en {(time.time()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
