"""Experimento 5 — ¿policy o consenso? ¿Es equivalente que un Core "adopte" RDTS por policy
(deja de spamear pero sigue Core) versus por consenso (se vuelve Knots)?

Parte de la base de sim-2 (Core 78% en 5 mineros: 25/20/15/10/8; Knots 22% disperso) y va
"adoptando" mineros Core uno por uno (del más chico al más grande), en dos modos:

  - policy:   el minero adoptado sigue siendo Core pero NUNCA incluye datos (no_spam_core).
              Sigue aceptando spam y construyendo sobre la cadena spam. Su hashpower NO cambia de bando.
  - consenso: el minero adoptado se vuelve Knots (enforza RDTS, rechaza spam, mina la cadena limpia).
              Su hashpower pasa al bando limpio.

Mismo hashpower adoptado en ambos modos → se compara si son equivalentes.

Uso:  python3 adoption.py --runs 6 --blocks 45
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orchestrator import run_weighted  # noqa: E402
from sim2 import build_step  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "adoption.csv")

KINDS0, WEIGHTS0 = build_step(0)                 # 5 Core (25,20,15,10,8) + 16 Knots (22%)
CORE_IDX = [i for i, k in enumerate(KINDS0) if k == "core"]
ADOPT_ORDER = sorted(CORE_IDX, key=lambda i: WEIGHTS0[i])   # más chico primero: 8,10,15,20,25
TOTAL = sum(WEIGHTS0)
STEPS = list(range(len(CORE_IDX) + 1))            # 0..5 mineros Core adoptando

FIELDS = ["mode", "step", "adopted_hp", "knots_share", "run", "seed",
          "softfork_wins", "fork_depth", "orphan_rate", "secs"]


def config(mode, step):
    adopted = ADOPT_ORDER[:step]
    adopted_hp = round(sum(WEIGHTS0[i] for i in adopted) / TOTAL, 4)
    if mode == "consensus":
        kinds = [("knots" if i in adopted else k) for i, k in enumerate(KINDS0)]
        return kinds, list(WEIGHTS0), None, adopted_hp
    else:  # policy: kinds intactos; adoptados = Core que no spamea
        return list(KINDS0), list(WEIGHTS0), set(adopted), adopted_hp


def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                done.add((r["mode"], int(r["step"]), int(r["run"])))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--blocks", type=int, default=45)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    done = load_done(RESULTS)
    new = not os.path.exists(RESULTS)
    f = open(RESULTS, "a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new:
        w.writeheader(); f.flush()

    plan = [(m, s, r) for m in ("policy", "consensus") for s in STEPS for r in range(a.runs)
            if (m, s, r) not in done]
    print(f"[adoption] {len(plan)} corridas pendientes (modos policy/consensus, "
          f"{len(STEPS)} pasos, runs={a.runs})", flush=True)
    for i, (mode, s, r) in enumerate(plan, 1):
        kinds, weights, no_spam, adopted_hp = config(mode, s)
        seed = 9000 + 1000 * (mode == "consensus") + 30 * s + r
        try:
            m = run_weighted(kinds, weights, f"ad_{mode[0]}{s}_{seed}", blocks=a.blocks,
                             p_spam=1.0, seed=seed, spam_kind="random", no_spam_core=no_spam)
        except Exception as e:
            print(f"  !! {mode} paso {s} run {r} FALLÓ: {type(e).__name__}: {e}", flush=True)
            continue
        w.writerow({"mode": mode, "step": s, "adopted_hp": adopted_hp,
                    "knots_share": m["knots_share"], "run": r, "seed": seed,
                    "softfork_wins": m["softfork_wins"], "fork_depth": m["fork_depth"],
                    "orphan_rate": m["orphan_rate"], "secs": m["secs"]}); f.flush()
        print(f"  [{i}/{len(plan)}] {mode:9s} paso {s} (adoptado {adopted_hp*100:.0f}% hp) "
              f"run {r} -> gana_softfork={m['softfork_wins']} ({m['secs']}s)", flush=True)
    f.close()
    print("[adoption] listo", flush=True)


if __name__ == "__main__":
    main()
