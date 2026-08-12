"""Evaluate the rolling shock-trajectory predictions against the per-period
ground truth (rolling_periods.py).

For each mode (free, anchored) and period p1-p4:
  - headline Hunter card trajectories, predicted vs real
  - Spearman over cards whose REAL adoption moved >=5pp since the previous
    period (the movers - the part a no-change baseline cannot answer)
  - direction hit-rate on those movers, vs the no-change baseline's 0 by
    construction and vs coin-flip

Usage (from classic_sim/examples/metagame_analysis):
  python evaluate_rolling.py [--modes free anchored]
"""
import csv, argparse, json
from pathlib import Path

from scipy.stats import spearmanr

HERE = Path(__file__).parent
DATA = HERE / "data"
TRUTH_DIR = HERE / ".." / "validation" / "data"

PERIOD_ORDER = ["p0_prenaxx", "p1_naxx_early", "p2_naxx_late",
                "p3_postnerf_early", "p4_postnerf_late"]
CLASSES = ["hunter", "mage", "warrior"]
HEADLINE = ["Starving Buzzard", "Unleash the Hounds", "Webspinner",
            "Sludge Belcher", "Mad Scientist"]
MOVER_THRESHOLD = 0.05


def load_truth(period):
  shares = {}
  with (TRUTH_DIR / f"rolling_adoption_{period}.csv").open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
      shares[row["card"]] = {c: float(row[f"{c}_share"]) for c in CLASSES}
  return shares


def load_prediction(mode, period):
  path = DATA / f"rolling_{mode}_predicted_{period}.csv"
  if not path.exists():
    return None
  shares = {}
  with path.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
      shares[row["card"]] = {c: float(row[f"{c}_share"]) for c in CLASSES}
  return shares


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--modes", nargs="+", default=["free", "anchored"])
  parser.add_argument("--out", default=str(DATA / "rolling_evaluation.json"))
  args = parser.parse_args()

  truth = {p: load_truth(p) for p in PERIOD_ORDER}
  results = {}

  print("=== headline Hunter trajectories (real | per-mode predicted) ===")
  print(f"{'card':<18}" + "".join(f"{p.split('_')[0]:>22}" for p in PERIOD_ORDER[1:]))
  for card in HEADLINE:
    cells = []
    for period in PERIOD_ORDER[1:]:
      real = truth[period].get(card, {}).get("hunter", 0.0)
      preds = []
      for mode in args.modes:
        prediction = load_prediction(mode, period)
        preds.append(f"{prediction.get(card, {}).get('hunter', 0.0):.2f}" if prediction else "-")
      cells.append(f"{real:.2f} | " + "/".join(preds))
    print(f"{card:<18}" + "".join(f"{cell:>22}" for cell in cells))

  for mode in args.modes:
    print(f"\n=== mode: {mode} ===")
    results[mode] = {}
    for prev, period in zip(PERIOD_ORDER, PERIOD_ORDER[1:]):
      prediction = load_prediction(mode, period)
      if prediction is None:
        print(f"{period}: prediction not present yet")
        continue
      per_class = {}
      for player_class in CLASSES:
        movers = []
        for card in set(truth[prev]) | set(truth[period]):
          before = truth[prev].get(card, {}).get(player_class, 0.0)
          after = truth[period].get(card, {}).get(player_class, 0.0)
          if abs(after - before) >= MOVER_THRESHOLD:
            movers.append((card, before, after))
        if len(movers) < 3:
          continue
        predicted = [prediction.get(card, {}).get(player_class, 0.0) for card, _, _ in movers]
        real_after = [after for _, _, after in movers]
        rho, pvalue = spearmanr(predicted, real_after)
        hits = sum(1 for (card, before, after), pred in zip(movers, predicted)
                   if (after - before) * (pred - before) > 0)
        per_class[player_class] = {"n_movers": len(movers), "spearman": round(float(rho), 3),
                                    "p": round(float(pvalue), 4),
                                    "direction_hits": hits,
                                    "direction_rate": round(hits / len(movers), 3)}
        print(f"  {period} {player_class:<8} movers={len(movers):3d} rho={rho:+.3f} "
              f"(p={pvalue:.3f}) direction={hits}/{len(movers)}")
      results[mode][period] = per_class

  with open(args.out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
  print(f"\nwrote {args.out}")


if __name__ == "__main__":
  main()
