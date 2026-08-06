"""Score each leave-one-archetype-out CV fold's fitted weights against ONLY
its held-out archetype's real matchups - the pairs that fold never saw
during fitting. This is the actual generalization test: did calibration
find something that transfers, or did it just memorize the 20 real points?
Compares each fold's held-out MSE against the default weights' MSE on the
exact same held-out pairs.
"""
import sys, json, argparse
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../validation')

from calibrate_greedy_weights import DEFAULT_WEIGHTS, build_matchup_lists, run_matchups_local, run_matchups_ssh
from run_s1_matchups import pick_representatives, load_decks, ARCHETYPE_CLASS

ARCHETYPES = ["Face Hunter", "Sunshine Hunter", "Freeze Mage", "Burn Mage", "Aggro Warrior", "Control Warrior"]


def held_out_pairs(archetype, all_pairs):
  return [(h, o) for h, o in all_pairs if archetype in (h, o)]


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--games", type=int, default=60)
  parser.add_argument("--backend", choices=["local", "ssh"], default="ssh")
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--out", default="data/cv_generalization.json")
  args = parser.parse_args()

  decks = load_decks()
  reps, _ = pick_representatives(decks)
  #build_matchup_lists (not a raw load_real_matrix().keys()) restricts to the
  #20 pairs among our 6 represented archetypes - the full vS matrix has 172
  #matchups across every archetype it covers, most of which we have no
  #representative deck for at all.
  all_pairs, _, real_matrix = build_matchup_lists(reps)
  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local

  fold_weights = {}
  for archetype in ARCHETYPES:
    safe_name = archetype.replace(" ", "_")
    path = Path(f"data/cv_weights_{safe_name}.json")
    with path.open(encoding="utf-8") as f:
      fold_weights[archetype] = json.load(f)["weights"]

  work, spans = [], {}
  for archetype in ARCHETYPES:
    pairs = held_out_pairs(archetype, all_pairs)
    for label, weights in [("default", DEFAULT_WEIGHTS), ("calibrated", fold_weights[archetype])]:
      start = len(work)
      work += [(reps[h], ARCHETYPE_CLASS[h], list(weights), reps[o], ARCHETYPE_CLASS[o], list(weights), args.games, args.games)
               for h, o in pairs]
      spans[(archetype, label)] = (start, len(work), pairs)

  print(f"dispatching {len(work)} held-out matchup evaluations ({args.games} games each)...")
  results = run_matchups(work, args.cores)

  print(f"\n{'archetype':18}{'held-out pairs':>16}{'default MSE':>14}{'calibrated MSE':>17}")
  report = {}
  for archetype in ARCHETYPES:
    row = {}
    for label in ("default", "calibrated"):
      start, end, pairs = spans[(archetype, label)]
      sim_pcts = [r * 100 for r in results[start:end]]
      mse = mean((sim - real_matrix[pair][0]) ** 2 for sim, pair in zip(sim_pcts, pairs))
      row[label] = mse
    report[archetype] = row
    print(f"{archetype:18}{len(spans[(archetype, 'default')][2]):>16}{row['default']:>14.1f}{row['calibrated']:>17.1f}")

  overall_default = mean(r["default"] for r in report.values())
  overall_calibrated = mean(r["calibrated"] for r in report.values())
  print(f"\noverall held-out MSE: default={overall_default:.1f}  calibrated={overall_calibrated:.1f}")

  Path(args.out).parent.mkdir(parents=True, exist_ok=True)
  with open(args.out, "w", encoding="utf-8") as f:
    json.dump({"per_archetype": report, "overall_default_mse": overall_default, "overall_calibrated_mse": overall_calibrated}, f, indent=2)
  print(f"wrote {args.out}")


if __name__ == "__main__":
  main()
