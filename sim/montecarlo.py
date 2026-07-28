"""Barrido Monte Carlo: para cada N (nodos Knots) de 1..19, corre R veces y estima la
probabilidad de fork persistente. Escribe results/results.csv incrementalmente (una fila
por corrida) para poder monitorear el progreso y sobrevivir a interrupciones.

Uso:  python3 montecarlo.py --runs 10 --blocks 45 --pspam 1.0
"""

import os as _os
_ROOT = _os.environ.get("SIM_RDTS_ROOT") or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, _os.path.join(_ROOT, "sim"))
from orchestrator import run_once  # noqa: E402

RESULTS = _os.path.join(_ROOT, "results/results.csv")
FIELDS = ["n_knots", "run", "seed", "fork", "fork_depth", "winner",
          "core_height", "knots_height", "common_height", "spam_blocks",
          "core_consensus", "knots_consensus", "blocks", "p_spam", "spam_kind", "secs"]


def load_done(path):
    """(n_knots, run) ya presentes en el CSV, para poder reanudar."""
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for row in csv.DictReader(f):
                done.add((int(row["n_knots"]), int(row["run"])))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--blocks", type=int, default=45)
    ap.add_argument("--pspam", type=float, default=1.0)
    ap.add_argument("--kind", default="random")
    ap.add_argument("--nmin", type=int, default=1)
    ap.add_argument("--nmax", type=int, default=19)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done(RESULTS)
    new_file = not os.path.exists(RESULTS)
    f = open(RESULTS, "a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new_file:
        w.writeheader(); f.flush()

    plan = [(n, r) for n in range(a.nmin, a.nmax + 1) for r in range(a.runs)
            if (n, r) not in done]
    total = len(plan)
    print(f"[montecarlo] {total} corridas pendientes "
          f"(N={a.nmin}..{a.nmax}, runs={a.runs}, blocks={a.blocks}, pspam={a.pspam})",
          flush=True)
    t0 = time.time()
    for i, (n, r) in enumerate(plan, 1):
        seed = 1000 * n + r
        try:
            m = run_once(n, blocks=a.blocks, p_spam=a.pspam, seed=seed, spam_kind=a.kind)
        except Exception as e:
            print(f"  !! N={n} run={r} FALLÓ: {type(e).__name__}: {e}", flush=True)
            continue
        m["run"] = r
        w.writerow({k: m.get(k) for k in FIELDS}); f.flush()
        el = time.time() - t0
        eta = el / i * (total - i)
        print(f"  [{i}/{total}] N={n:2d} run={r} -> fork={m['fork']} "
              f"depth={m['fork_depth']:2d} winner={m['winner']:5s} "
              f"({m['secs']}s)  ETA {eta/60:.0f}m", flush=True)
    f.close()
    print(f"[montecarlo] listo en {(time.time()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
