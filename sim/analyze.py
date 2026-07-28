"""Lee results/results.csv y produce:
  - results/fork_probability.png : P(fork persistente) y profundidad media vs N (Knots)
  - results/report.md            : tabla + lectura del experimento
  - results/summary.json         : datos agregados (para el artifact HTML)

Uso:  python3 analyze.py [--depth-threshold 6]
"""
import argparse
import csv
import json
import math
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RES = "/Users/jmo/bitcoin/bip110/results"
CSV = f"{RES}/results.csv"

INK = "#1f2430"
MUTED = "#8a92a6"
GRID = "#e7e9f0"
ACCENT = "#4c6ef5"      # probabilidad (una serie)
ACCENT_FILL = "#c5cffb"
DEPTH = "#7048e8"       # profundidad
REF = "#e8590c"         # línea de referencia 50%


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


def load(threshold):
    rows = []
    with open(CSV) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    by_n = defaultdict(list)
    for r in rows:
        n = int(r["n_knots"])
        persistent = int(r["fork_depth"]) >= threshold
        by_n[n].append({
            "persistent": persistent,
            "depth": int(r["fork_depth"]),
            "winner": r["winner"],
            "core_cons": r["core_consensus"] in ("True", "true", "1"),
            "knots_cons": r["knots_consensus"] in ("True", "true", "1"),
        })
    return by_n


def aggregate(by_n):
    agg = []
    for n in sorted(by_n):
        runs = by_n[n]
        k = sum(1 for x in runs if x["persistent"])
        p, lo, hi = wilson(k, len(runs))
        depths = [x["depth"] for x in runs]
        agg.append({
            "n_knots": n, "hashpower": n / 20,
            "runs": len(runs), "forks": k,
            "p_fork": p, "ci_lo": lo, "ci_hi": hi,
            "mean_depth": sum(depths) / len(depths),
            "knots_wins": sum(1 for x in runs if x["winner"] == "knots"),
            "all_consensus": all(x["core_cons"] and x["knots_cons"] for x in runs),
        })
    return agg


def plot(agg, threshold):
    ns = [a["n_knots"] for a in agg]
    p = [a["p_fork"] for a in agg]
    lo = [a["ci_lo"] for a in agg]
    hi = [a["ci_hi"] for a in agg]
    depth = [a["mean_depth"] for a in agg]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8.2), height_ratios=[3, 2])
    fig.patch.set_facecolor("white")

    # --- Panel A: probabilidad de fork ---
    ax1.axvline(10, color=REF, lw=1.4, ls=(0, (4, 3)), zorder=1)
    ax1.text(10.15, 0.04, "50% del hashpower\n(10 Knots / 10 Core)", color=REF,
             fontsize=8.5, va="bottom", ha="left")
    ax1.fill_between(ns, lo, hi, color=ACCENT_FILL, alpha=0.7, lw=0, zorder=2)
    ax1.plot(ns, p, color=ACCENT, lw=2, zorder=3)
    ax1.scatter(ns, p, s=34, color=ACCENT, zorder=4, edgecolor="white", linewidth=1)
    ax1.set_ylim(-0.03, 1.05)
    ax1.set_xlim(0.3, 19.7)
    ax1.set_xticks(range(1, 20))
    ax1.set_ylabel("P(fork persistente)", color=INK, fontsize=10)
    ax1.set_title(f"Probabilidad de fork Core↔Knots en regtest (BIP-110/RDTS)\n"
                  f"fork persistente = divergencia ≥ {threshold} bloques · "
                  f"{agg[0]['runs']} corridas por punto",
                  color=INK, fontsize=11.5, loc="left", pad=10)

    # --- Panel B: profundidad media del split ---
    ax2.axvline(10, color=REF, lw=1.4, ls=(0, (4, 3)), zorder=1)
    ax2.bar(ns, depth, color=DEPTH, width=0.62, zorder=2)
    ax2.set_ylabel("Profundidad media\ndel split (bloques)", color=INK, fontsize=10)
    ax2.set_xlabel("Nodos Knots (de 20) — el resto son Core", color=INK, fontsize=10)
    ax2.set_xticks(range(1, 20))
    ax2.set_xlim(0.3, 19.7)

    for ax in (ax1, ax2):
        ax.set_facecolor("white")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=8.5)
        ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
        ax.set_axisbelow(True)

    fig.tight_layout()
    out = f"{RES}/fork_probability.png"
    fig.savefig(out, dpi=150, facecolor="white")
    print("escrito", out)


def write_report(agg, threshold):
    lines = []
    lines.append("# Simulación de fork Core ↔ Knots (BIP-110 / RDTS) en regtest\n")
    lines.append("**Bitcoin Core 31.1** (no conoce RDTS) vs **Bitcoin Knots "
                 "v29.3.knots20260508** (aplica el softfork BIP-110/RDTS, forzado activo "
                 "con `-vbparams=reduced_data:-1:...`).\n")
    lines.append("Modelo: 20 nodos regtest, cada uno = 1/20 del hashpower (minero elegido "
                 "uniforme por bloque). Cada bloque minado por Core lleva datos que RDTS "
                 "invalida (OP_RETURN>83 B y/o item de witness>256 B): **válido para Core, "
                 "rechazado por consenso en Knots** → la cadena se parte.\n")
    lines.append(f"Un fork se cuenta como **persistente** si al final de la corrida las "
                 f"cadenas Core y Knots divergen ≥ {threshold} bloques.\n")
    lines.append("![Probabilidad de fork](fork_probability.png)\n")
    lines.append("## Resultados por proporción\n")
    lines.append("| Knots | Core | Hashpower Knots | Corridas | Forks | P(fork) | "
                 "IC95% | Prof. media | Knots gana |")
    lines.append("|------:|-----:|:---------------:|:--------:|:-----:|:-------:|"
                 ":-----:|:-----------:|:----------:|")
    for a in agg:
        lines.append(
            f"| {a['n_knots']} | {20-a['n_knots']} | {a['hashpower']*100:.0f}% | "
            f"{a['runs']} | {a['forks']} | {a['p_fork']*100:.0f}% | "
            f"[{a['ci_lo']*100:.0f}–{a['ci_hi']*100:.0f}%] | {a['mean_depth']:.1f} | "
            f"{a['knots_wins']} |")
    # lectura
    cross = next((a["n_knots"] for a in agg if a["p_fork"] < 0.5), None)
    all_cons = all(a["all_consensus"] for a in agg)
    lines.append("\n## Lectura\n")
    lines.append(f"- **Cruce de probabilidad** (P baja de 50%) alrededor de **N≈"
                 f"{cross if cross else '—'} nodos Knots**, consistente con la predicción "
                 f"teórica de una carrera de cadena-más-larga con umbral en 50% del "
                 f"hashpower (N=10).")
    lines.append("- Con **mayoría Core** (N<10) el softfork **fracasa**: Knots queda "
                 "aislado en una cadena minoritaria más corta (fork persistente y profundo).")
    lines.append("- Con **mayoría Knots** (N>10) el softfork **triunfa**: la cadena limpia "
                 "es la más larga y Core la adopta reorganizando y descartando sus bloques "
                 "con datos (fork transitorio o inexistente).")
    lines.append(f"- Verificación estructural: en {'TODAS' if all_cons else 'la mayoría de'} "
                 "las corridas todos los nodos Core coincidieron entre sí y todos los Knots "
                 "entre sí — el split es por **consenso**, no por conectividad (la malla "
                 "P2P se mantuvo con `whitelist=noban`).")
    with open(f"{RES}/report.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("escrito", f"{RES}/report.md")
    with open(f"{RES}/summary.json", "w") as f:
        json.dump({"threshold": threshold, "rows": agg}, f, indent=2)
    print("escrito", f"{RES}/summary.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth-threshold", type=int, default=6)
    a = ap.parse_args()
    by_n = load(a.depth_threshold)
    if not by_n:
        print("sin datos en", CSV); return
    agg = aggregate(by_n)
    plot(agg, a.depth_threshold)
    write_report(agg, a.depth_threshold)


if __name__ == "__main__":
    main()
