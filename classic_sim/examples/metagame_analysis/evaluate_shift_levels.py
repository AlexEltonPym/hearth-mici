"""A/B scorer for metagame-shift predictions: the existing RANKING metrics
(evaluate_shift_prediction.py) plus the LEVELS metrics the ranking metrics
cannot see.

Why levels: the pipeline ranks the shift well (Spearman 0.67-0.89 on movers)
but over-converges - it predicts ~100% adoption for cards whose real adoption
tops out near 79%. Spearman is invariant to that, so a run can look perfect
and still be badly calibrated. Metrics added here:

  levels MAE        mean |predicted - real| adoption share over scored cards
  over-prediction   share of scored cards predicted >=95% where real is <90%
  saturation        share of scored cards predicted at exactly 100%
  mean level gap    mean (predicted - real), signed - is the model high or low

Ranking metrics kept for the guard-rail: a change that fixes levels while
destroying ranking is a failure.

  movers Spearman   Spearman(predicted, real_after) over cards whose REAL
                    adoption moved >=5pp across the shock (same definition as
                    evaluate_rolling.py)
  direction         of those movers, how many the prediction moved the right
                    way from the pre-shock baseline (same definition as
                    evaluate_shift_prediction.py, which quotes Hunter 30/38)

Usage (from classic_sim/examples/metagame_analysis):
  python evaluate_shift_levels.py --era naxx_launch --prefixes shift_ab_baseline shift_ab_collection
  python evaluate_shift_levels.py --era naxx_launch --prefixes shift_ab_baseline --source population
"""
import sys, csv, json, argparse
from pathlib import Path

sys.path.append('../../src')
sys.path.append('../validation')

from scipy.stats import spearmanr

from evaluate_shift_prediction import ERA_WINDOWS, MIN_SHARE, DIRECTION_THRESHOLD, load_real, OUT_DIR
from evolve_metagame_shift import era_class_pool, CLASSES

SATURATION = 0.95
REAL_CEILING = 0.90

LEGENDARY_REPORT = ["Kel'Thuzad", "Loatheb", "Maexxna", "Baron Rivendare", "Feugen", "Stalagg",
                    "Grommash Hellscream", "Ragnaros the Firelord", "Leeroy Jenkins",
                    "Sylvanas Windrunner", "Alexstrasza"]


def load_prediction(prefix, source):
  suffix = "population_adoption" if source == "population" else "predicted_adoption"
  path = OUT_DIR / f"{prefix}_{suffix}.csv"
  shares = {c: {} for c in CLASSES}
  with path.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
  return shares


def score(prediction, baseline, target):
  """Per-class metrics + a pooled row over all three classes."""
  per_class, pooled_abs, pooled_gap, pooled_over, pooled_sat, pooled_n = {}, [], [], 0, 0, 0
  pooled_movers, pooled_hits = 0, 0
  for player_class in CLASSES:
    pool = set(era_class_pool(player_class))
    real, pred, base = target[player_class], prediction[player_class], baseline[player_class]
    cards = [c for c in pool if real.get(c, 0) >= MIN_SHARE or pred.get(c, 0) >= MIN_SHARE
             or base.get(c, 0) >= MIN_SHARE]

    errors = [pred.get(c, 0) - real.get(c, 0) for c in cards]
    over = [c for c in cards if pred.get(c, 0) >= SATURATION and real.get(c, 0) < REAL_CEILING]
    saturated = [c for c in cards if pred.get(c, 0) >= 0.999]

    movers = [c for c in pool if abs(real.get(c, 0) - base.get(c, 0)) >= DIRECTION_THRESHOLD]
    hits = sum(1 for c in movers
               if (real.get(c, 0) - base.get(c, 0)) * (pred.get(c, 0) - base.get(c, 0)) > 0)
    if len(movers) >= 3:
      rho, pvalue = spearmanr([pred.get(c, 0) for c in movers], [real.get(c, 0) for c in movers])
    else:
      rho, pvalue = float("nan"), float("nan")

    per_class[player_class] = {
      "n_scored": len(cards),
      "levels_mae": round(sum(abs(e) for e in errors) / len(cards), 4),
      "mean_gap": round(sum(errors) / len(cards), 4),
      "over_predicted": len(over),
      "over_rate": round(len(over) / len(cards), 4),
      "saturated_at_100": len(saturated),
      "n_movers": len(movers),
      "movers_spearman": round(float(rho), 3),
      "movers_p": round(float(pvalue), 4),
      "direction_hits": hits,
      "direction_rate": round(hits / len(movers), 3) if movers else None,
      "over_predicted_cards": sorted(over, key=lambda c: -(pred.get(c, 0) - real.get(c, 0)))[:8],
    }
    pooled_abs.extend(abs(e) for e in errors)
    pooled_gap.extend(errors)
    pooled_over += len(over)
    pooled_sat += len(saturated)
    pooled_n += len(cards)
    pooled_movers += len(movers)
    pooled_hits += hits

  per_class["POOLED"] = {
    "n_scored": pooled_n,
    "levels_mae": round(sum(pooled_abs) / pooled_n, 4),
    "mean_gap": round(sum(pooled_gap) / pooled_n, 4),
    "over_predicted": pooled_over,
    "over_rate": round(pooled_over / pooled_n, 4),
    "saturated_at_100": pooled_sat,
    "n_movers": pooled_movers,
    "direction_hits": pooled_hits,
    "direction_rate": round(pooled_hits / pooled_movers, 3) if pooled_movers else None,
  }
  return per_class


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--era", choices=list(ERA_WINDOWS), default="naxx_launch")
  parser.add_argument("--prefixes", nargs="+", required=True)
  parser.add_argument("--labels", nargs="+", default=None)
  parser.add_argument("--source", choices=["elites", "population"], default="elites")
  parser.add_argument("--out", default=None)
  args = parser.parse_args()

  labels = args.labels or args.prefixes
  windows = ERA_WINDOWS[args.era]
  baseline = load_real(windows["baseline"])
  target = load_real(windows["target"])

  results = {}
  for label, prefix in zip(labels, args.prefixes):
    try:
      prediction = load_prediction(prefix, args.source)
    except FileNotFoundError:
      print(f"!! {label}: {prefix} prediction missing, skipped")
      continue
    results[label] = score(prediction, baseline, target)

  print(f"\n=== {args.era}: {windows['baseline']} -> {windows['target']} "
        f"(prediction source: {args.source}) ===")
  header = f"{'condition':<22}{'class':<9}{'MAE':>8}{'gap':>8}{'over>=95%':>11}{'sat100':>8}{'rho_mov':>9}{'dir':>10}"
  print(header)
  print("-" * len(header))
  for label, per_class in results.items():
    for player_class in CLASSES + ["POOLED"]:
      row = per_class[player_class]
      rho = row.get("movers_spearman")
      rho_text = f"{rho:+.3f}" if isinstance(rho, float) and rho == rho else "     -"
      direction = f"{row['direction_hits']}/{row['n_movers']}"
      print(f"{label if player_class == CLASSES[0] else '':<22}{player_class:<9}"
            f"{row['levels_mae']:>8.4f}{row['mean_gap']:>+8.4f}"
            f"{row['over_predicted']:>7}/{row['n_scored']:<3}{row['saturated_at_100']:>8}"
            f"{rho_text:>9}{direction:>10}")
    print()

  #the specific thing collection constraints should fix
  print("=== legendary adoption: real vs predicted ===")
  print(f"{'card':<24}{'class':<9}{'real':>8}" + "".join(f"{label[:13]:>15}" for label in labels))
  for card in LEGENDARY_REPORT:
    for player_class in CLASSES:
      pool = set(era_class_pool(player_class))
      if card not in pool:
        continue
      real = target[player_class].get(card, 0.0)
      cells = []
      for label, prefix in zip(labels, args.prefixes):
        if label not in results:
          cells.append("-")
          continue
        try:
          pred = load_prediction(prefix, args.source)[player_class].get(card, 0.0)
        except FileNotFoundError:
          pred = float("nan")
        cells.append(f"{pred:.1%}")
      print(f"{card:<24}{player_class:<9}{real:>8.1%}" + "".join(f"{cell:>15}" for cell in cells))

  out_path = Path(args.out) if args.out else OUT_DIR / f"levels_ab_{args.era}_{args.source}.json"
  with out_path.open("w", encoding="utf-8") as f:
    json.dump({"era": args.era, "windows": windows, "source": args.source,
               "conditions": results}, f, indent=2)
  print(f"\nwrote {out_path}")


if __name__ == "__main__":
  main()
