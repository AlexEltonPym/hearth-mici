"""Score the multi-seed paper rerun (paper_sweep.sh artifacts) with the
adopted pipeline: mass-matched readout, then the ranking + levels metrics of
evaluate_shift_levels.score. Reports per-seed metrics, their mean +- sd, and
the seed-mean prediction scored as one forecast (the paper's headline
numbers). Also prints the headline cards per seed.

Usage (from classic_sim/examples/metagame_analysis):
  python score_paper_runs.py --era buzzard_nerf --seeds 0 1 2
  python score_paper_runs.py --era naxx_launch --seeds 0 1 2 --out data/paper_naxx_launch_scores.json
"""
import csv, json, argparse
from statistics import mean, stdev

from adoption_correction import mass_match
from evaluate_shift_prediction import ERA_WINDOWS, load_real, OUT_DIR
from evaluate_shift_levels import score
from evolve_metagame_shift import era_class_pool, CLASSES

HEADLINE = {
  "buzzard_nerf": [("HUNTER", "Starving Buzzard"), ("HUNTER", "Leeroy Jenkins"),
                    ("HUNTER", "Unleash the Hounds"), ("HUNTER", "Webspinner"),
                    ("WARRIOR", "Leeroy Jenkins")],
  "naxx_launch": [("HUNTER", "Mad Scientist"), ("HUNTER", "Sludge Belcher"),
                   ("HUNTER", "Webspinner"), ("HUNTER", "Unstable Ghoul"),
                   ("MAGE", "Duplicate"), ("WARRIOR", "Death's Bite")],
}


def load_run(prefix):
  """predicted shares + per-class unique-elite counts (Jeffreys n)."""
  shares = {c: {} for c in CLASSES}
  n_elites = {c: 0 for c in CLASSES}
  with (OUT_DIR / f"{prefix}_predicted_adoption.csv").open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
        n_elites[player_class] = int(row[f"{player_class.lower()}_n_elites"])
  return shares, n_elites


def corrected(prediction, n_elites, baseline):
  return {c: mass_match(prediction[c], baseline[c], era_class_pool(c), n_elites[c])
          for c in CLASSES}


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--era", choices=list(ERA_WINDOWS), required=True)
  parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
  parser.add_argument("--prefix", default="paper", help="artifact prefix (default paper_<era>_s<seed>)")
  parser.add_argument("--out", default=None)
  args = parser.parse_args()

  windows = ERA_WINDOWS[args.era]
  baseline, target = load_real(windows["baseline"]), load_real(windows["target"])

  per_seed, corrected_runs = {}, []
  for seed in args.seeds:
    prediction, n_elites = load_run(f"{args.prefix}_{args.era}_s{seed}")
    fixed = corrected(prediction, n_elites, baseline)
    corrected_runs.append(fixed)
    per_seed[seed] = score(fixed, baseline, target)

  #the paper's forecast: average the corrected per-seed shares, score once
  seed_mean = {c: {} for c in CLASSES}
  for player_class in CLASSES:
    cards = set().union(*(run[player_class] for run in corrected_runs))
    for card in cards:
      seed_mean[player_class][card] = mean(run[player_class].get(card, 0.0)
                                            for run in corrected_runs)
  pooled = score(seed_mean, baseline, target)

  report = {"era": args.era, "seeds": args.seeds,
            "per_seed": {str(s): per_seed[s] for s in args.seeds},
            "seed_mean_forecast": pooled}

  print(f"=== {args.era}: per-seed metrics (mass-matched) ===")
  keys = ["movers_spearman", "direction_rate", "levels_mae", "mean_gap"]
  for player_class in CLASSES + ["POOLED"]:
    for key in keys:
      values = [per_seed[s][player_class].get(key) for s in args.seeds]
      if any(v is None or v != v for v in values):
        continue
      sd = stdev(values) if len(values) > 1 else 0.0
      pooled_value = pooled[player_class].get(key)
      print(f"{player_class:8s} {key:16s} seeds={ [round(v, 3) for v in values] } "
            f"mean={mean(values):.3f} sd={sd:.3f} | seed-mean forecast={pooled_value}")

  print(f"\n=== headline cards (baseline -> per-seed corrected -> seed-mean | real) ===")
  for player_class, card in HEADLINE[args.era]:
    values = [run[player_class].get(card, 0.0) for run in corrected_runs]
    print(f"{player_class:8s} {card:22s} {baseline[player_class].get(card, 0.0):5.1%} -> "
          f"{ [f'{v:.1%}' for v in values] } -> {seed_mean[player_class].get(card, 0.0):5.1%} "
          f"| real {target[player_class].get(card, 0.0):5.1%}")

  if args.out:
    with open(args.out, "w", encoding="utf-8") as f:
      json.dump(report, f, indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
  main()
