"""Analiza results/sim2.csv (hashpower concentrado). Agrega por paso:
P(softfork gana) vs share Knots, y cuánto tira Core (reorgs y bloques descartados,
media y mediana). Escribe results/sim2_summary.json + results/sim2.png + imprime tabla.

Uso:  python3 analyze2.py
"""
import csv
import json
import math
import statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RES = "/Users/jmo/bitcoin/bip110/results"
CSV = f"{RES}/sim2.csv"

INK, MUTED, GRID = "#1f2430", "#8a92a6", "#e7e9f0"
WIN = "#2f9e5f"      # softfork gana (verde)
DISCARD = "#d61f69"  # bloques tirados por Core (magenta)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


def load():
    by = defaultdict(list)
    with open(CSV) as f:
        for r in csv.DictReader(f):
            by[int(r["step"])].append(r)
    rows = []
    for s in sorted(by):
        g = by[s]
        share = float(g[0]["knots_share"])
        wins = sum(1 for r in g if r["softfork_wins"] in ("True", "true", "1"))
        p, lo, hi = wilson(wins, len(g))
        reorgs = [int(r["core_reorgs"]) for r in g]
        disc = [int(r["core_blocks_discarded"]) for r in g]
        depth = [int(r["fork_depth"]) for r in g]
        rows.append({
            "step": s, "knots_share": share, "core_share": round(1 - share, 4),
            "n_nodes": int(g[0]["n_nodes"]), "runs": len(g), "wins": wins,
            "p_win": p, "ci_lo": lo, "ci_hi": hi,
            "reorgs_mean": round(st.mean(reorgs), 2), "reorgs_med": st.median(reorgs),
            "disc_mean": round(st.mean(disc), 2), "disc_med": st.median(disc),
            "depth_mean": round(st.mean(depth), 1),
        })
    return rows


def plot(rows):
    xs = [r["knots_share"] * 100 for r in rows]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), height_ratios=[3, 2])
    fig.patch.set_facecolor("white")

    ax1.axvline(50, color=MUTED, lw=1.2, ls=(0, (4, 3)))
    ax1.fill_between(xs, [r["ci_lo"] for r in rows], [r["ci_hi"] for r in rows],
                     color=WIN, alpha=0.15, lw=0)
    ax1.plot(xs, [r["p_win"] for r in rows], color=WIN, lw=2.2)
    ax1.scatter(xs, [r["p_win"] for r in rows], s=32, color=WIN, zorder=4,
                edgecolor="white", linewidth=1)
    ax1.set_ylim(-0.03, 1.05)
    ax1.set_ylabel("P(el softfork gana)", color=INK)
    ax1.set_title("sim-2 · hashpower concentrado (Core en 5 mineros grandes / Knots disperso)\n"
                  "Core parte de 78%; se agregan mineros Knots grandes",
                  color=INK, fontsize=11.5, loc="left")

    ax2.bar(xs, [r["disc_mean"] for r in rows], width=2.4, color=DISCARD)
    ax2.set_ylabel("Bloques que tira Core\n(media/corrida)", color=INK)
    ax2.set_xlabel("Share de hashpower de Knots (%)", color=INK)
    ax2.axvline(50, color=MUTED, lw=1.2, ls=(0, (4, 3)))

    for ax in (ax1, ax2):
        ax.set_facecolor("white")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(f"{RES}/sim2.png", dpi=150, facecolor="white")
    print("escrito", f"{RES}/sim2.png")


def main():
    rows = load()
    if not rows:
        print("sin datos en", CSV); return
    print(f"\n{'share Knots':>11} {'nodos':>6} {'runs':>5} {'P(gana)':>8} "
          f"{'reorgs μ':>9} {'tira μ':>7} {'tira med':>9} {'prof μ':>7}")
    for r in rows:
        print(f"{r['knots_share']*100:>10.1f}% {r['n_nodes']:>6} {r['runs']:>5} "
              f"{r['p_win']*100:>7.0f}% {r['reorgs_mean']:>9} {r['disc_mean']:>7} "
              f"{r['disc_med']:>9} {r['depth_mean']:>7}")
    with open(f"{RES}/sim2_summary.json", "w") as f:
        json.dump({"rows": rows}, f, indent=2)
    print("escrito", f"{RES}/sim2_summary.json")
    plot(rows)


if __name__ == "__main__":
    main()
