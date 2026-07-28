"""Pase instrumentado corto (modelo uniforme, como sim-1) para medir cuánto tira Core.
Corre unos N representativos con la orquestación ya instrumentada y reporta, por N:
media y mediana de reorgs de Core y de bloques descartados.

Uso:  python3 reorg_probe.py --ns 6,11,16 --runs 6 --blocks 45
"""

import os as _os
_ROOT = _os.environ.get("SIM_RDTS_ROOT") or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import argparse
import csv
import os
import statistics as st
import sys

sys.path.insert(0, _os.path.join(_ROOT, "sim"))
from orchestrator import run_once  # noqa: E402

OUT = _os.path.join(_ROOT, "results/reorg_probe.csv")
FIELDS = ["n_knots", "run", "seed", "fork", "fork_depth", "winner",
          "core_reorgs", "core_blocks_discarded", "spam_blocks", "secs"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", default="6,11,16", help="lista de N (nodos Knots) separada por comas")
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--blocks", type=int, default=45)
    a = ap.parse_args()
    ns = [int(x) for x in a.ns.split(",")]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    f = open(OUT, "w", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    agg = {}
    for n in ns:
        reorgs, discarded = [], []
        for r in range(a.runs):
            seed = 90000 + 100 * n + r
            m = run_once(n, blocks=a.blocks, p_spam=1.0, seed=seed, spam_kind="random")
            w.writerow({k: m.get(k) for k in FIELDS}); f.flush()
            reorgs.append(m["core_reorgs"])
            discarded.append(m["core_blocks_discarded"])
            print(f"  N={n:2d} run={r} reorgs={m['core_reorgs']:2d} "
                  f"descartados={m['core_blocks_discarded']:2d} "
                  f"fork={m['fork']} ({m['secs']}s)", flush=True)
        agg[n] = (reorgs, discarded)
    f.close()

    print("\n=== Cuánto tira Core (Knots share = N/20) ===")
    print(f"{'N':>3} {'hp%':>4} | {'reorgs/corrida':>14} {'med':>5} | "
          f"{'bloq tirados/corrida':>20} {'med':>5} | {'bloq/reorg':>10}")
    for n in ns:
        rr, dd = agg[n]
        tot_r, tot_d = sum(rr), sum(dd)
        per_event = (tot_d / tot_r) if tot_r else 0.0
        print(f"{n:>3} {n*5:>3}% | {st.mean(rr):>14.1f} {st.median(rr):>5.1f} | "
              f"{st.mean(dd):>20.1f} {st.median(dd):>5.1f} | {per_event:>10.1f}")


if __name__ == "__main__":
    main()
