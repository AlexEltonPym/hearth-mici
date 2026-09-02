"""Evaluate the rolling shock-trajectory predictions against the per-period
ground truth (rolling_periods.py).

For each mode (free, anchored) and period p1-p4:
  - headline Hunter card trajectories, predicted vs real
  - Spearman over cards whose REAL adoption moved >=5pp since the previous
    period (the movers - the part a no-change baseline cannot answer)
  - direction hit-rate on those movers, vs the no-change baseline's 0 by
    construction and vs coin-flip

The reported readout is mass-matched by default (adoption_correction.py):
a monotone, ranking-preserving level correction that removes the raw elite
readout's saturation and mass-inflation using only the previous period's
real adoption as reference. Pass --readout raw for the uncorrected shares.

Usage (from classic_sim/examples/metagame_analysis):
  python evaluate_rolling.py [--modes free anchored] [--readout massmatch|raw]
"""
import csv, argparse, json
from pathlib import Path

from scipy.stats import spearmanr

from adoption_correction import mass_match

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


PREFIX = "rolling"


def load_prediction(mode, period):
  path = DATA / f"{PREFIX}_{mode}_predicted_{period}.csv"
  if not path.exists():
    return None, None
  shares = {}
  n_elites = {c: 0 for c in CLASSES}
  with path.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
      shares[row["card"]] = {c: float(row[f"{c}_share"]) for c in CLASSES}
      for c in CLASSES:
        n_elites[c] = max(n_elites[c], int(float(row.get(f"{c}_n_elites", 0) or 0)))
  return shares, n_elites


def corrected_prediction(prediction, n_elites, reference, readout):
  """Apply the reporting readout. reference is the previous period's real
  adoption (the info a predictor has at prediction time)."""
  if prediction is None or readout == "raw":
    return prediction
  pool = set(prediction) | set(reference)
  out = {card: {} for card in pool}
  for c in CLASSES:
    ref_c = {card: reference.get(card, {}).get(c, 0.0) for card in pool}
    pred_c = {card: prediction.get(card, {}).get(c, 0.0) for card in pool}
    fixed = mass_match(pred_c, ref_c, pool, max(1, n_elites.get(c, 1)))
    for card in pool:
      out[card][c] = fixed[card]
  return out


SEEDS = None   #None = single run per mode; else average of {PREFIX}_{mode}_s{seed}


def seed_mean(corrected_runs):
  """Average per-seed corrected shares (the one-shot paper convention:
  correct each seed, then average)."""
  runs = [r for r in corrected_runs if r is not None]
  if not runs:
    return None
  cards = set().union(*runs)
  out = {}
  for card in cards:
    out[card] = {c: sum(r.get(card, {}).get(c, 0.0) for r in runs) / len(runs) for c in CLASSES}
  return out


def build_predictions(modes, readout, truth):
  """{mode: {period: corrected_prediction}} - mass-matched against the
  previous period's real adoption unless readout == 'raw'. With SEEDS set,
  each seed's run is corrected separately and the seed-mean is returned."""
  preds = {}
  for mode in modes:
    preds[mode] = {}
    for prev, period in zip(PERIOD_ORDER, PERIOD_ORDER[1:]):
      if SEEDS is None:
        raw, n_elites = load_prediction(mode, period)
        preds[mode][period] = corrected_prediction(raw, n_elites, truth[prev], readout)
      else:
        runs = []
        for seed in SEEDS:
          raw, n_elites = load_prediction(f"{mode}_s{seed}", period)
          runs.append(corrected_prediction(raw, n_elites, truth[prev], readout))
        preds[mode][period] = seed_mean(runs) if all(r is not None for r in runs) else None
  return preds


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--modes", nargs="+", default=["free", "anchored"])
  parser.add_argument("--readout", choices=["massmatch", "raw"], default="massmatch")
  parser.add_argument("--out", default=str(DATA / "rolling_evaluation.json"))
  parser.add_argument("--prefix", default="rolling",
                       help="artifact prefix, e.g. rolling2 for the pair-bias rerun")
  parser.add_argument("--seeds", type=int, nargs="+", default=None,
                       help="average {prefix}_{mode}_s{seed} runs (seed-mean forecast)")
  args = parser.parse_args()
  global PREFIX, SEEDS
  PREFIX = args.prefix
  SEEDS = args.seeds

  truth = {p: load_truth(p) for p in PERIOD_ORDER}
  preds = build_predictions(args.modes, args.readout, truth)
  results = {"readout": args.readout, "prefix": args.prefix, "seeds": args.seeds}

  print(f"=== headline Hunter trajectories, readout={args.readout} "
        f"(real | per-mode predicted) ===")
  print(f"{'card':<18}" + "".join(f"{p.split('_')[0]:>22}" for p in PERIOD_ORDER[1:]))
  for card in HEADLINE:
    cells = []
    for period in PERIOD_ORDER[1:]:
      real = truth[period].get(card, {}).get("hunter", 0.0)
      shown = []
      for mode in args.modes:
        prediction = preds[mode][period]
        shown.append(f"{prediction.get(card, {}).get('hunter', 0.0):.2f}" if prediction else "-")
      cells.append(f"{real:.2f} | " + "/".join(shown))
    print(f"{card:<18}" + "".join(f"{cell:>22}" for cell in cells))

  for mode in args.modes:
    print(f"\n=== mode: {mode} (readout={args.readout}) ===")
    results[mode] = {}
    for prev, period in zip(PERIOD_ORDER, PERIOD_ORDER[1:]):
      prediction = preds[mode][period]
      if prediction is None:
        print(f"{period}: prediction not present yet")
        continue
      per_class = {}
      for player_class in CLASSES:
        movers = []
        abs_err = []
        for card in set(truth[prev]) | set(truth[period]):
          before = truth[prev].get(card, {}).get(player_class, 0.0)
          after = truth[period].get(card, {}).get(player_class, 0.0)
          pred = prediction.get(card, {}).get(player_class, 0.0)
          abs_err.append(abs(pred - after))
          if abs(after - before) >= MOVER_THRESHOLD:
            movers.append((card, before, after))
        levels_mae = sum(abs_err) / len(abs_err) if abs_err else float("nan")
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
                                    "direction_rate": round(hits / len(movers), 3),
                                    "levels_mae": round(levels_mae, 4)}
        print(f"  {period} {player_class:<8} movers={len(movers):3d} rho={rho:+.3f} "
              f"(p={pvalue:.3f}) direction={hits}/{len(movers)} levelsMAE={levels_mae:.3f}")
      results[mode][period] = per_class

  with open(args.out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
  print(f"\nwrote {args.out}")


if __name__ == "__main__":
  main()
