"""Confirm-phase evaluation + post-hoc feature ablation for a calibrated
weight vector produced by calibrate_greedy_weights.py. Re-evaluates with
more games than the search phase used (full fidelity, fixed count instead
of early-stopped) for a clean, reportable number, distributed the same way
the search phase is (SSH to dwail1/dwail2 by default), and reports:
  - matching loss (default vs calibrated) against the real matrix
  - skill-floor win rate vs RandomAction, per archetype (default vs calibrated)
  - post-hoc ablation: zero each new feature's fitted weight individually,
    holding the rest at their calibrated values, and see how much matching
    loss degrades - a cheap proxy for "does this feature matter", not a full
    re-optimization ablation (see the plan for why that tradeoff was made).
"""
import sys, json, argparse
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../validation')

from calibrate_greedy_weights import (DEFAULT_WEIGHTS, build_matchup_lists,
                                       run_matchups_local, run_matchups_ssh)
from run_s1_matchups import pick_representatives, load_decks, ARCHETYPE_CLASS

NEW_FEATURE_NAMES = ["lethal_margin_mine", "lethal_margin_theirs", "weapon_durability_difference",
                      "fatigue_proximity", "hero_power_available_difference", "unused_mana"]
NEW_FEATURE_START = len(DEFAULT_WEIGHTS) - len(NEW_FEATURE_NAMES)


def matching_work_items(reps, real_pairs, weights, games):
  return [(reps[hero], ARCHETYPE_CLASS[hero], list(weights), reps[opponent], ARCHETYPE_CLASS[opponent], list(weights), games, games)
          for hero, opponent in real_pairs]


def skill_work_items(reps, skill_archetypes, weights, games):
  return [(reps[a], ARCHETYPE_CLASS[a], list(weights), reps[a], ARCHETYPE_CLASS[a], None, games, games)
          for a in skill_archetypes]


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--weights", default="data/calibrated_weights_full.json")
  parser.add_argument("--games", type=int, default=60)
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--backend", choices=["local", "ssh"], default="ssh")
  parser.add_argument("--out", default="data/calibration_confirm.json")
  args = parser.parse_args()

  with open(args.weights, encoding="utf-8") as f:
    calibrated = json.load(f)["weights"]

  decks = load_decks()
  reps, _ = pick_representatives(decks)
  real_pairs, skill_archetypes, real_matrix = build_matchup_lists(reps)
  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local

  #build every piece of work for this whole analysis up front and dispatch it
  #as one batch, so the ssh backend's per-call overhead (dill-serialize,
  #ssh connect, pyenv activate) is paid once, not once per label/ablation.
  labeled_weight_vectors = [("default", DEFAULT_WEIGHTS), ("calibrated", calibrated)]
  for i, name in enumerate(NEW_FEATURE_NAMES):
    ablated = list(calibrated)
    ablated[NEW_FEATURE_START + i] = 0.0
    labeled_weight_vectors.append((f"ablate_{name}", ablated))

  work = []
  spans = {}
  for label, weights in labeled_weight_vectors:
    start = len(work)
    work += matching_work_items(reps, real_pairs, weights, args.games)
    spans[label] = (start, len(work), "matching")
  for label in ("default", "calibrated"): #skill floor only needed for these two
    start = len(work)
    work += skill_work_items(reps, skill_archetypes, dict(labeled_weight_vectors)[label], args.games)
    spans[label + "_skill"] = (start, len(work), "skill")

  print(f"dispatching {len(work)} matchup evaluations ({args.games} games each, backend={args.backend})...")
  results = run_matchups(work, args.cores)

  mse_by_label, skill_by_label, sim_pct_by_label = {}, {}, {}
  for label, weights in labeled_weight_vectors:
    start, end, _ = spans[label]
    sim_pcts = [r * 100 for r in results[start:end]]
    mse_by_label[label] = mean((sim - real_matrix[pair][0]) ** 2 for sim, pair in zip(sim_pcts, real_pairs))
    sim_pct_by_label[label] = dict(zip(real_pairs, sim_pcts))
  for label in ("default", "calibrated"):
    start, end, _ = spans[label + "_skill"]
    skill_by_label[label] = dict(zip(skill_archetypes, results[start:end]))

  print("\nmatching MSE (lower is better match to real win rates):")
  for label, _ in labeled_weight_vectors:
    print(f"  {label}: {mse_by_label[label]:.1f}")

  print("\nskill-floor win rate vs RandomAction (should not drop, default -> calibrated):")
  for archetype in skill_archetypes:
    d, c = skill_by_label["default"][archetype], skill_by_label["calibrated"][archetype]
    flag = "  <-- DROPPED" if c < d else ""
    print(f"  {archetype}: {d:.3f} -> {c:.3f}{flag}")

  print("\nper-matchup (default sim / calibrated sim / real):")
  for hero, opponent in real_pairs:
    d = sim_pct_by_label["default"][(hero, opponent)]
    c = sim_pct_by_label["calibrated"][(hero, opponent)]
    r = real_matrix[(hero, opponent)][0]
    print(f"  {hero} vs {opponent}: {d:.1f}% / {c:.1f}% / {r:.1f}%")

  out = {
    "games_per_matchup": args.games,
    "mse": mse_by_label,
    "skill": skill_by_label,
    "sim_winrate_pct": {label: {f"{h}|{o}": v for (h, o), v in d.items()} for label, d in sim_pct_by_label.items()},
  }
  Path(args.out).parent.mkdir(parents=True, exist_ok=True)
  with open(args.out, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
  print(f"\nwrote {args.out}")


if __name__ == "__main__":
  main()
