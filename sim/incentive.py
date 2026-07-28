"""Frecuencia de REEMPLAZO de la cadena de Core por la de Knots, en tiempo real.

Cada reorg de Core (core_reorgs) = un evento donde su cadena (con datos) es reemplazada por
la limpia de Knots -> Core pierde esos bloques. Mapeo a tiempo real: 1 bloque de red ≈ 10 min
=> 144 bloques/día. Las corridas usaron BLOCKS bloques cada una.

Reporta, por share de hashpower Knots:
  - reorgs/día (media)            = mean(core_reorgs) * 144 / BLOCKS
  - P(≥1 reemplazo por día)       ≈ 1 - exp(-reorgs/día)   (modelo Poisson)
El umbral de interés: reorgs/día ≥ 1  =>  incentivo diario para señalar RDTS.
"""

import os as _os
_ROOT = _os.environ.get("SIM_RDTS_ROOT") or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import csv
import math
import statistics as st
from collections import defaultdict

RES = _os.path.join(_ROOT, "results")
BLOCKS = 45
PER_DAY = 144  # bloques/día a 10 min


def rows_from(path, share_key, is_uniform=False):
    out = defaultdict(list)
    try:
        data = list(csv.DictReader(open(path)))
    except FileNotFoundError:
        return out
    for r in data:
        if is_uniform:
            share = int(r["n_knots"]) / 20
        else:
            share = float(r["knots_share"])
        out[round(share, 4)].append(int(r["core_reorgs"]))
    return out


def report(title, groups):
    print(f"\n=== {title} ===")
    print(f"{'share Knots':>11} {'n':>3} {'reorgs/corrida':>14} {'reorgs/DÍA':>10} "
          f"{'P(≥1/día)':>10}  incentivo")
    for share in sorted(groups):
        rr = groups[share]
        m = st.mean(rr)
        per_day = m * PER_DAY / BLOCKS
        p_ge1 = 1 - math.exp(-per_day)
        flag = "◀ ≥1/día" if per_day >= 1 else ""
        print(f"{share*100:>10.1f}% {len(rr):>3} {m:>14.2f} {per_day:>10.2f} "
              f"{p_ge1*100:>9.0f}%  {flag}")


def main():
    # sim-2 (hashpower concentrado)
    g2 = rows_from(f"{RES}/sim2.csv", "knots_share")
    report("sim-2 · hashpower concentrado (Core en pocos mineros grandes)", g2)
    # sim-1 uniforme (probe)
    gp = rows_from(f"{RES}/reorg_probe.csv", None, is_uniform=True)
    if gp:
        report("modelo uniforme (reorg_probe)", gp)

    # umbral de incentivo en sim-2
    thr = None
    for share in sorted(g2):
        per_day = st.mean(g2[share]) * PER_DAY / BLOCKS
        if per_day >= 1 and thr is None:
            thr = share
    print(f"\nUmbral de incentivo (≥1 reemplazo/día) en sim-2: "
          f"~{thr*100:.0f}% de hashpower Knots" if thr else "\nsin umbral alcanzado")
    print(f"Umbral de VICTORIA del softfork (sim-1/2): ~55-57% de hashpower.")
    print("Nota: p_spam=1.0 (cada bloque de Core lleva datos) => cota SUPERIOR de la frecuencia.")


if __name__ == "__main__":
    main()
