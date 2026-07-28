"""Modelo mejorado (v2) que atiende la crítica:

  1. Mide la probabilidad de orfandad REAL de un bloque con datos (hashes marcados y verificados),
     no un estimador sucio de profundidad de reorganización.
  2. Deriva el INCENTIVO NETO: premio de equilibrio = p_orfandad / (1 - p_orfandad) — cuánto debe
     pagar el dato, como fracción del premio de bloque, para valer el riesgo de orfandad.
  3. Modo 'adaptativo': un minero Core deja de incluir datos tras ver un bloque suyo huérfano
     (la respuesta racional que señalaba la crítica), en vez de suponer que spamea para siempre.

Usa la misma distribución concentrada de sim-2 (build_step).

Uso:  python3 model_v2.py --runs 10 --adaptive-runs 6 --blocks 45
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orchestrator import run_weighted  # noqa: E402
from sim2 import build_step, knots_share, ADD_KNOTS  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "model_v2.csv")
FIELDS = ["mode", "step", "knots_share", "n_nodes", "run", "seed",
          "softfork_wins", "fork_depth", "orphan_rate", "spam_produced", "spam_orphaned",
          "breakeven_fee", "core_gaveup", "core_reorgs", "secs"]


def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                done.add((r["mode"], int(r["step"]), int(r["run"])))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10, help="corridas por paso en modo baseline")
    ap.add_argument("--adaptive-runs", type=int, default=6, help="corridas por paso en modo adaptativo")
    ap.add_argument("--blocks", type=int, default=45)
    a = ap.parse_args()

    steps = list(range(len(ADD_KNOTS) + 1))
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done(RESULTS)
    new = not os.path.exists(RESULTS)
    f = open(RESULTS, "a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new:
        w.writeheader(); f.flush()

    plan = ([("baseline", s, r) for s in steps for r in range(a.runs)]
            + [("adaptive", s, r) for s in steps for r in range(a.adaptive_runs)])
    plan = [(m, s, r) for (m, s, r) in plan if (m, s, r) not in done]
    print(f"[model_v2] {len(plan)} corridas pendientes", flush=True)

    for i, (mode, s, r) in enumerate(plan, 1):
        kinds, weights = build_step(s)
        seed = 7000 + 1000 * (mode == "adaptive") + 50 * s + r
        try:
            m = run_weighted(kinds, weights, f"v2_{mode[0]}{s}_{seed}", blocks=a.blocks,
                             p_spam=1.0, seed=seed, spam_kind="random",
                             adaptive=(mode == "adaptive"))
        except Exception as e:
            print(f"  !! {mode} paso {s} run {r} FALLÓ: {type(e).__name__}: {e}", flush=True)
            continue
        w.writerow({
            "mode": mode, "step": s, "knots_share": round(knots_share(s), 4),
            "n_nodes": m["n_nodes"], "run": r, "seed": seed,
            "softfork_wins": m["softfork_wins"], "fork_depth": m["fork_depth"],
            "orphan_rate": m["orphan_rate"], "spam_produced": m["spam_produced"],
            "spam_orphaned": m["spam_orphaned"], "breakeven_fee": m["breakeven_fee"],
            "core_gaveup": m["core_gaveup"], "core_reorgs": m["core_reorgs"],
            "secs": m["secs"]}); f.flush()
        print(f"  [{i}/{len(plan)}] {mode:8s} paso {s} (knots {knots_share(s)*100:.0f}%) "
              f"run {r} -> orfandad={m['orphan_rate']:.2f} "
              f"gana={m['softfork_wins']} se_rindieron={m['core_gaveup']} ({m['secs']}s)",
              flush=True)
    f.close()
    print("[model_v2] listo", flush=True)


if __name__ == "__main__":
    main()
