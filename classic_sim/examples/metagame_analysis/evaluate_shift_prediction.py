"""Score a metagame-shift prediction against the real post-shock adoption.

Compares evolve_metagame_shift.py's predicted card-adoption shares against
naxx_adoption_series.py's ground truth for the target window, and against
the strongest cheap baseline: NO-CHANGE (the pre-shock window's real
adoption carried forward - real decks are sticky, so this bar is high).

Metrics per class:
  - Spearman(prediction -> real target) vs Spearman(no-change -> real target)
    over cards with real or predicted share >= MIN_SHARE (the zero-mass tail
    of never-played cards would swamp the correlation with ties)
  - top-10 adopted-cards overlap (prediction vs real, baseline vs real)
  - direction hit-rate on cards whose REAL adoption moved >= 5pp between
    windows: did the prediction move the same way? (no-change predicts zero
    movement, so its hit-rate on this set is 0 by construction - reported
    for completeness)
  - headline calls: the cards that defined the real shift

Usage (from classic_sim/examples/metagame_analysis):
  python evaluate_shift_prediction.py --era naxx_launch
  python evaluate_shift_prediction.py --era buzzard_nerf
"""
import sys, csv, json, argparse
from pathlib import Path

sys.path.append('../../src')
sys.path.append('../validation')

from run_s1_matchups import spearman
from evolve_metagame_shift import era_class_pool, CLASSES

HERE = Path(__file__).parent
OUT_DIR = HERE / "data"
GT_DIR = HERE / ".." / "validation" / "data"

ERA_WINDOWS = {
  "naxx_launch": {"baseline": "pre_naxx", "target": "naxx_prenerf"},
  "buzzard_nerf": {"baseline": "naxx_prenerf", "target": "post_nerf"},
}
MIN_SHARE = 0.02
DIRECTION_THRESHOLD = 0.05
HEADLINES = {
  "naxx_launch": {
    "HUNTER": ["Webspinner", "Haunted Creeper", "Mad Scientist", "Undertaker", "Sludge Belcher", "Loatheb", "Kel'Thuzad"],
    "MAGE": ["Mad Scientist", "Duplicate", "Sludge Belcher", "Loatheb", "Undertaker", "Kel'Thuzad"],
    "WARRIOR": ["Death's Bite", "Sludge Belcher", "Loatheb", "Unstable Ghoul", "Kel'Thuzad"],
  },
  "buzzard_nerf": {
    "HUNTER": ["Starving Buzzard", "Leeroy Jenkins", "Unleash the Hounds", "Webspinner", "Houndmaster"],
    "MAGE": ["Mad Scientist", "Duplicate"],
    "WARRIOR": ["Death's Bite", "Sludge Belcher"],
  },
}


def load_real(window):
  path = GT_DIR / f"naxx_adoption_{window}.csv"
  shares = {c: {} for c in CLASSES}
  with path.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
  return shares


def load_prediction(era, prefix):
  path = OUT_DIR / f"{prefix or f'shift_{era}'}_predicted_adoption.csv"
  shares = {c: {} for c in CLASSES}
  with path.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
  return shares


def top_n(shares, pool, n=10):
  return set(sorted((c for c in pool if shares.get(c, 0) > 0), key=lambda c: -shares[c])[:n])


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--era", choices=list(ERA_WINDOWS), required=True)
  parser.add_argument("--prefix", default=None, help="prediction file prefix (default shift_<era>)")
  args = parser.parse_args()

  windows = ERA_WINDOWS[args.era]
  baseline = load_real(windows["baseline"])
  target = load_real(windows["target"])
  prediction = load_prediction(args.era, args.prefix)

  summary = {}
  for player_class in CLASSES:
    pool = set(era_class_pool(player_class))
    cards = [c for c in pool
             if target[player_class].get(c, 0) >= MIN_SHARE
             or prediction[player_class].get(c, 0) >= MIN_SHARE
             or baseline[player_class].get(c, 0) >= MIN_SHARE]

    pred_pairs = [(prediction[player_class].get(c, 0), target[player_class].get(c, 0)) for c in cards]
    base_pairs = [(baseline[player_class].get(c, 0), target[player_class].get(c, 0)) for c in cards]
    rho_pred = spearman(pred_pairs)
    rho_base = spearman(base_pairs)

    top_real = top_n(target[player_class], pool)
    top_pred = top_n(prediction[player_class], pool)
    top_base = top_n(baseline[player_class], pool)

    movers = [c for c in pool
              if abs(target[player_class].get(c, 0) - baseline[player_class].get(c, 0)) >= DIRECTION_THRESHOLD]
    hits = 0
    for c in movers:
      real_delta = target[player_class].get(c, 0) - baseline[player_class].get(c, 0)
      pred_delta = prediction[player_class].get(c, 0) - baseline[player_class].get(c, 0)
      if pred_delta * real_delta > 0:
        hits += 1

    summary[player_class] = {
      "n_cards_scored": len(cards),
      "spearman_prediction": round(rho_pred, 3),
      "spearman_no_change_baseline": round(rho_base, 3),
      "top10_overlap_prediction": len(top_pred & top_real),
      "top10_overlap_baseline": len(top_base & top_real),
      "direction_movers": len(movers),
      "direction_hits": hits,
    }

    print(f"\n=== {player_class} ({len(cards)} cards scored) ===")
    print(f"Spearman vs real {windows['target']}: prediction {rho_pred:.3f} | no-change baseline {rho_base:.3f}")
    print(f"top-10 overlap with real: prediction {len(top_pred & top_real)}/10 | baseline {len(top_base & top_real)}/10")
    print(f"direction hit-rate (real movers >= {DIRECTION_THRESHOLD:.0%}): {hits}/{len(movers)}")
    print(f"{'card':24}{'baseline':>10}{'predicted':>11}{'real':>8}")
    for card in HEADLINES[args.era][player_class]:
      print(f"{card:24}{baseline[player_class].get(card, 0):>9.1%}"
            f"{prediction[player_class].get(card, 0):>11.1%}{target[player_class].get(card, 0):>8.1%}")

  out_path = OUT_DIR / f"{args.prefix or f'shift_{args.era}'}_evaluation.json"
  with out_path.open("w", encoding="utf-8") as f:
    json.dump({"era": args.era, "windows": windows, "per_class": summary}, f, indent=2)
  print(f"\nwrote {out_path}")


if __name__ == "__main__":
  main()
