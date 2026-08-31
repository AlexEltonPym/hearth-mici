"""Score a bias-strength sweep (one evolution run per bias level, one era)
with the adopted pipeline: mass-matched readout + evaluate_shift_levels
metrics. Prints a per-arm comparison table and the headline cards so the
winning bias level can be picked for the paper-grade multi-seed reruns.

Usage (from classic_sim/examples/metagame_analysis):
  python score_bias_sweep.py --era naxx_launch --prefix bt2_b --arms 0 5 10 20
"""
import argparse
import csv
import json

from adoption_correction import mass_match
from evaluate_shift_prediction import ERA_WINDOWS, load_real, OUT_DIR
from evaluate_shift_levels import score
from evolve_metagame_shift import era_class_pool, CLASSES
from score_paper_runs import HEADLINE


def load_run(prefix):
  shares = {c: {} for c in CLASSES}
  n_elites = {c: 0 for c in CLASSES}
  with (OUT_DIR / f"{prefix}_predicted_adoption.csv").open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
        n_elites[player_class] = int(row[f"{player_class.lower()}_n_elites"])
  return shares, n_elites


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--era", choices=list(ERA_WINDOWS), required=True)
  parser.add_argument("--prefix", default="bt2_b")
  parser.add_argument("--arms", type=int, nargs="+", default=[0, 5, 10, 20])
  parser.add_argument("--out", default=None)
  args = parser.parse_args()

  windows = ERA_WINDOWS[args.era]
  baseline, target = load_real(windows["baseline"]), load_real(windows["target"])

  results, fixed_runs = {}, {}
  for arm in args.arms:
    prediction, n_elites = load_run(f"{args.prefix}{arm}")
    fixed = {c: mass_match(prediction[c], baseline[c], era_class_pool(c), n_elites[c])
             for c in CLASSES}
    fixed_runs[arm] = fixed
    results[arm] = score(fixed, baseline, target)

  keys = ["movers_spearman", "direction_rate", "levels_mae", "mean_gap"]
  print(f"=== {args.era}: bias sweep (mass-matched) ===")
  header = "arm      " + "".join(f"{k:>18s}" for k in keys)
  for player_class in CLASSES + ["POOLED"]:
    print(f"\n[{player_class}]")
    print(header)
    for arm in args.arms:
      row = results[arm][player_class]
      cells = "".join(f"{row.get(k):18.3f}" if isinstance(row.get(k), float)
                      else f"{'--':>18s}" for k in keys)
      print(f"bias={arm:<4d}{cells}")

  print(f"\n=== headline cards (baseline -> per-arm corrected | real) ===")
  for player_class, card in HEADLINE[args.era]:
    cells = "  ".join(f"b{arm}={fixed_runs[arm][player_class].get(card, 0.0):5.1%}"
                      for arm in args.arms)
    print(f"{player_class:8s} {card:22s} {baseline[player_class].get(card, 0.0):5.1%} -> "
          f"{cells} | real {target[player_class].get(card, 0.0):5.1%}")

  if args.out:
    with open(args.out, "w", encoding="utf-8") as f:
      json.dump({"era": args.era, "prefix": args.prefix,
                 "per_arm": {str(a): results[a] for a in args.arms}}, f, indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
  main()
