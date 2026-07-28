"""Capa económica del modelo v2 — atiende la crítica de Satoshi.

Convierte la probabilidad de orfandad de un bloque con datos en el INCENTIVO NETO:
el premio de equilibrio d* = p/(1-p) es cuánto debe pagar el dato, como fracción del premio de
bloque, para que a un minero Core le convenga incluirlo pese al riesgo de que su bloque quede
huérfano. Derivación:  incluir datos conviene si  (1-p)(S+f+d) > (S+f)  =>  d > (S+f)·p/(1-p).

Compara además el modo baseline (Core spamea siempre) contra el adaptativo (Core deja de
spamear tras sufrir orfandad): en el adaptativo la cadena converge por decisión económica, no
por una guerra de reorganizaciones.

Lee results/model_v2.csv → escribe results/economics_summary.json y una tabla.
"""
import csv
import json
import os
import statistics as st
from collections import defaultdict

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CSV = os.path.join(RES, "model_v2.csv")


def load():
    base = defaultdict(list)
    adap = defaultdict(list)
    with open(CSV) as f:
        for r in csv.DictReader(f):
            (base if r["mode"] == "baseline" else adap)[float(r["knots_share"])].append(r)
    rows = []
    for share in sorted(set(base) | set(adap)):
        b = base.get(share, [])
        a = adap.get(share, [])
        orphan = [float(x["orphan_rate"]) for x in b]
        p = st.mean(orphan) if orphan else 0.0
        breakeven = p / (1 - p) if p < 1 else None      # None = infinito (ningún fee lo justifica)
        rows.append({
            "knots_share": share,
            "orphan_rate": round(p, 3),
            "breakeven_fee": (round(breakeven, 3) if breakeven is not None else None),
            "baseline_converge": round(
                sum(x["softfork_wins"] in ("True", "1") for x in b) / len(b), 3) if b else None,
            "adaptive_converge": round(
                sum(x["softfork_wins"] in ("True", "1") for x in a) / len(a), 3) if a else None,
            "adaptive_gaveup": round(st.mean([int(x["core_gaveup"]) for x in a]), 2) if a else None,
            "n_base": len(b), "n_adap": len(a),
        })
    return rows


def main():
    if not os.path.exists(CSV):
        print("sin datos en", CSV); return
    rows = load()
    print(f"\n{'hashpower':>9} {'orfandad':>9} {'premio equil.':>14} "
          f"{'converge base':>14} {'converge adapt':>15} {'se rindieron':>13}")
    for r in rows:
        be = "∞" if r["breakeven_fee"] is None else f"{r['breakeven_fee']*100:.0f}%"
        cb = "-" if r["baseline_converge"] is None else f"{r['baseline_converge']*100:.0f}%"
        ca = "-" if r["adaptive_converge"] is None else f"{r['adaptive_converge']*100:.0f}%"
        gu = "-" if r["adaptive_gaveup"] is None else f"{r['adaptive_gaveup']:.1f}"
        print(f"{r['knots_share']*100:>8.0f}% {r['orphan_rate']*100:>8.0f}% {be:>14} "
              f"{cb:>14} {ca:>15} {gu:>13}")
    with open(os.path.join(RES, "economics_summary.json"), "w") as f:
        json.dump({"rows": rows}, f, indent=2)
    print("\nescrito", os.path.join(RES, "economics_summary.json"))


if __name__ == "__main__":
    main()
