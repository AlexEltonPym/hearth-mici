"""Tests the actual hypothesis: does a self-play-trained (pure skill,
zero exposure to the real win-rate target) agent predict real Classic
matchup win rates better than the hand-tuned defaults, or the earlier
win-rate-calibrated weights that turned out to overfit
(examples/validation/README.md)? Same confirm-phase methodology as
analyze_calibration.py - fixed 60-game matchups, matching MSE + skill floor
vs RandomAction - applied to three weight vectors instead of two.

Caveat worth stating plainly: self-play training sampled decks from the
full 88-deck real archive each generation, and the 6 representative
archetype decks used here are members of that same pool - so it's not a
strictly disjoint held-out set the way the leave-one-archetype-out CV's
folds were. What IS disjoint is the real WIN-RATE TARGET itself: nothing
in the training loop ever saw matchup_matrix.csv, so this is still an
honest test of "does skill alone predict real win rates", just not immune
to "got slightly better at piloting these specific decks" as a minor
confound (a much milder issue than fitting directly to the target numbers).
"""
import sys, json, argparse
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../validation')

from calibrate_greedy_weights import DEFAULT_WEIGHTS, build_matchup_lists, run_matchups_local, run_matchups_ssh
from run_s1_matchups import pick_representatives, load_decks, ARCHETYPE_CLASS


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--champion", default="data/self_play_champion.json")
  parser.add_argument("--calibrated", default="data/calibrated_weights_full.json")
  parser.add_argument("--games", type=int, default=60)
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--backend", choices=["local", "ssh"], default="ssh")
  parser.add_argument("--out", default="data/self_play_vs_real.json")
  args = parser.parse_args()

  with open(args.champion, encoding="utf-8") as f:
    champion = json.load(f)["champion_weights"]
  with open(args.calibrated, encoding="utf-8") as f:
    calibrated = json.load(f)["weights"]

  decks = load_decks()
  reps, _ = pick_representatives(decks)
  real_pairs, skill_archetypes, real_matrix = build_matchup_lists(reps)
  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local

  labeled_weight_vectors = [("default", DEFAULT_WEIGHTS), ("win_rate_calibrated", calibrated), ("self_play_champion", champion)]

  work, spans = [], {}
  for label, weights in labeled_weight_vectors:
    start = len(work)
    work += [(reps[h], ARCHETYPE_CLASS[h], list(weights), reps[o], ARCHETYPE_CLASS[o], list(weights), args.games, args.games)
             for h, o in real_pairs]
    spans[label] = (start, len(work))
  for label, weights in labeled_weight_vectors:
    start = len(work)
    work += [(reps[a], ARCHETYPE_CLASS[a], list(weights), reps[a], ARCHETYPE_CLASS[a], None, args.games, args.games)
             for a in skill_archetypes]
    spans[label + "_skill"] = (start, len(work))

  print(f"dispatching {len(work)} matchup evaluations ({args.games} games each)...")
  results = run_matchups(work, args.cores)

  mse_by_label, skill_by_label = {}, {}
  for label, _ in labeled_weight_vectors:
    start, end = spans[label]
    sim_pcts = [r * 100 for r in results[start:end]]
    mse_by_label[label] = mean((sim - real_matrix[pair][0]) ** 2 for sim, pair in zip(sim_pcts, real_pairs))
    start_s, end_s = spans[label + "_skill"]
    skill_by_label[label] = dict(zip(skill_archetypes, results[start_s:end_s]))

  print("\nmatching MSE (lower is better match to real win rates):")
  for label, _ in labeled_weight_vectors:
    print(f"  {label}: {mse_by_label[label]:.1f}")

  print("\nskill vs RandomAction (default -> self_play_champion):")
  for archetype in skill_archetypes:
    d, s = skill_by_label["default"][archetype], skill_by_label["self_play_champion"][archetype]
    print(f"  {archetype}: {d:.3f} -> {s:.3f}")

  out = {"mse": mse_by_label, "skill": skill_by_label, "games_per_matchup": args.games}
  Path(args.out).parent.mkdir(parents=True, exist_ok=True)
  with open(args.out, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
  print(f"\nwrote {args.out}")


if __name__ == "__main__":
  main()
