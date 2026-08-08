"""Compare linear / gen4-unseen-net / naxx-finetuned-net probe valuations
against real Naxx-pre-nerf adoption shares, per class.

Usage (from classic_sim/examples/metagame_analysis):
  python compare_finetuned_probe.py
"""
import csv
from pathlib import Path
from statistics import mean

try:
    from scipy.stats import spearmanr
except ImportError:
    spearmanr = None

CLASSES = ["HUNTER", "MAGE", "WARRIOR"]
PROBES = {
    "linear": "data/probe_naxx_launch.csv",
    "gen4_unseen": "data/probe_naxx_launch_neural.csv",
    "finetuned": "data/probe_naxx_launch_neural_finetuned.csv",
}
ADOPTION = "../validation/data/naxx_adoption_naxx_prenerf.csv"

KEY_HUNTER_CARDS = ["Haunted Creeper", "Webspinner"]
KEY_OTHER_CARDS = ["Death's Bite", "Duplicate"]


def load_probe(path):
    rows = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows[(r["class"], r["card"])] = float(r["mean_delta_wr"])
    return rows


def load_adoption(path):
    rows = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows[r["card"]] = {
                "HUNTER": float(r["hunter_share"]),
                "MAGE": float(r["mage_share"]),
                "WARRIOR": float(r["warrior_share"]),
            }
    return rows


def rank_corr(x, y):
    if spearmanr is not None:
        rho, _ = spearmanr(x, y)
        return rho
    # fallback: manual spearman
    def rank(vals):
        idx = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0] * len(vals)
        for r, i in enumerate(idx):
            ranks[i] = r
        return ranks
    rx, ry = rank(x), rank(y)
    n = len(x)
    mx, my = mean(rx), mean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else float("nan")


def main():
    adoption = load_adoption(ADOPTION)
    probes = {name: load_probe(path) for name, path in PROBES.items()}

    print(f"{'probe':<14}" + "".join(f"{c:>10}" for c in CLASSES))
    for name, data in probes.items():
        cors = []
        for cls in CLASSES:
            cards = [c for (k, c) in data if k == cls and c in adoption]
            xs = [data[(cls, c)] for c in cards]
            ys = [adoption[c][cls] for c in cards]
            cors.append(rank_corr(xs, ys))
        print(f"{name:<14}" + "".join(f"{c:>10.3f}" for c in cors))

    print()
    print("Key card deltas (mean_delta_wr) — real Naxx adoption for context:")
    for card in KEY_HUNTER_CARDS:
        real = adoption.get(card, {}).get("HUNTER")
        print(f"  {card:<18} real_hunter_share={real}")
        for name, data in probes.items():
            v = data.get(("HUNTER", card))
            print(f"    {name:<14} {v}")

    for card, cls in [("Death's Bite", "WARRIOR"), ("Duplicate", "MAGE")]:
        real = adoption.get(card, {}).get(cls)
        print(f"  {card:<18} real_{cls.lower()}_share={real}")
        for name, data in probes.items():
            v = data.get((cls, card))
            print(f"    {name:<14} {v}")


if __name__ == "__main__":
    main()
