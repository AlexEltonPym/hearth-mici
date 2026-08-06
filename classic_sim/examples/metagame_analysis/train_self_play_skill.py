"""Train GreedyActionSmart's feature weights via self-play, optimizing purely
for playing strength - no real-world win-rate target anywhere in the loop.
Tests a specific hypothesis: does a higher-skill agent naturally predict real
human matchup win rates better, as a side effect of just being stronger,
rather than by being fit to match them (which calibrate_greedy_weights.py
already showed overfits badly - see examples/validation/README.md)?

Design choices, and why:
- Self-play against a small, growing hall-of-fame, not a fixed opponent.
  A fixed opponent plateaus once beaten reliably (win rate saturates near
  100%, no further gradient). Each generation's best candidate gets promoted
  into the hall-of-fame if it decisively beats the most recent member;
  fitness for the next generation is the average win rate across the last
  HOF_SIZE members, not just the newest, so the optimizer can't win by
  narrowly exploiting one specific opponent's blind spots (a classic
  self-play failure mode) while remaining weak generally.
- Trained on a broad sample of the real 88-deck archive, resampled every
  generation, NOT the 6 representative archetype decks used for the S1
  validation. If training and the final real-matchup evaluation used the
  same decks, a good result could just mean "learned to pilot these 6 decks"
  rather than "got better at Hearthstone" - that would undermine the point
  of the test. Keeping them disjoint makes the final evaluation an honest,
  untouched-by-training check of the hypothesis.
- Mirror matches (same deck both sides) isolate skill from deck quality -
  the only difference between the two sides is the weight vector.

Reuses calibrate_greedy_weights.py's matchup evaluator and SSH distribution
(same infra, different fitness function and no matching/regularization terms
at all - there's nothing to overfit to since the only judge is "did you win").
"""
import sys, csv, json, random, argparse
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../validation')

import cma

from calibrate_greedy_weights import (DEFAULT_WEIGHTS, run_matchups_local, run_matchups_ssh,
                                       play_matchup_till_stoppage)

HERE = Path(__file__).parent
DECKLISTS = HERE.parent / "validation" / "data" / "hsreplay_classic" / "constructible_decklists.csv"

HOF_SIZE = 3 #hall-of-fame members kept; fitness averages win rate across all of them
PROMOTION_GAMES = 30 #fixed-count confirmatory match before promoting a new champion
PROMOTION_THRESHOLD = 0.55
STAGNATION_LIMIT = 10 #stop early if this many generations pass with no promotion


def load_deck_pool():
  with DECKLISTS.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
  return [(row["class"], row["card_list"].split("|")) for row in rows]


def sample_training_decks(deck_pool, n, rng):
  return rng.sample(deck_pool, n)


def evaluate_population(candidates, hall_of_fame, training_decks, cores, run_matchups):
  """Fitness = mean win rate for each candidate across (training_decks x hall_of_fame),
  all mirror matches. Returns list of losses (1 - mean win rate, since CMA-ES minimizes)."""
  work = []
  for weights in candidates:
    for player_class, deck in training_decks:
      for champion in hall_of_fame:
        work.append((deck, player_class, list(weights), deck, player_class, list(champion)))

  results = run_matchups(work, cores)

  losses = []
  idx = 0
  per_candidate = len(training_decks) * len(hall_of_fame)
  for _ in candidates:
    chunk = results[idx: idx + per_candidate]
    idx += per_candidate
    losses.append(1.0 - mean(chunk))
  return losses


def confirm_promotion(candidate_weights, champion_weights, training_decks, cores, run_matchups, rng):
  #a handful of fixed decks (not the whole training sample) is enough for a
  #go/no-go confirmatory check - full precision isn't needed here, the next
  #generation's fitness evaluation will re-test the promoted champion anyway.
  check_decks = rng.sample(training_decks, min(4, len(training_decks)))
  work = [(deck, player_class, list(candidate_weights), deck, player_class, list(champion_weights), PROMOTION_GAMES, PROMOTION_GAMES)
          for player_class, deck in check_decks]
  results = run_matchups(work, cores)
  return mean(results)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--popsize", type=int, default=0)
  parser.add_argument("--max-generations", type=int, default=80)
  parser.add_argument("--sigma0", type=float, default=2.0)
  parser.add_argument("--decks-per-generation", type=int, default=8)
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--seed", type=int, default=0)
  parser.add_argument("--out", default=str(HERE / "data" / "self_play_champion.json"))
  parser.add_argument("--log", default=str(HERE / "data" / "self_play_generations.csv"))
  args = parser.parse_args()

  rng = random.Random(args.seed)
  deck_pool = load_deck_pool()
  print(f"{len(deck_pool)} real decks available for training sampling")

  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local

  hall_of_fame = [DEFAULT_WEIGHTS]
  hof_labels = ["default"]
  es = cma.CMAEvolutionStrategy(list(DEFAULT_WEIGHTS), args.sigma0, {"popsize": args.popsize} if args.popsize else {})

  history = []
  generation = 0
  generations_since_promotion = 0
  while not es.stop() and generation < args.max_generations and generations_since_promotion < STAGNATION_LIMIT:
    training_decks = sample_training_decks(deck_pool, args.decks_per_generation, rng)
    candidates = es.ask()
    losses = evaluate_population(candidates, hall_of_fame, training_decks, args.cores, run_matchups)
    es.tell(candidates, losses)
    generation += 1

    best_index = min(range(len(losses)), key=lambda i: losses[i])
    best_candidate = candidates[best_index]
    best_fitness = 1.0 - losses[best_index]
    print(f"gen {generation}: best_winrate_vs_hof={best_fitness:.3f} mean_winrate_vs_hof={1 - mean(losses):.3f} hof_size={len(hall_of_fame)}", flush=True)

    promoted = False
    winrate_vs_champion = confirm_promotion(best_candidate, hall_of_fame[-1], training_decks, args.cores, run_matchups, rng)
    if winrate_vs_champion > PROMOTION_THRESHOLD:
      hall_of_fame.append(list(best_candidate))
      hof_labels.append(f"gen{generation}")
      if len(hall_of_fame) > HOF_SIZE:
        hall_of_fame.pop(0)
        hof_labels.pop(0)
      promoted = True
      generations_since_promotion = 0
      print(f"  PROMOTED (won {winrate_vs_champion:.1%} of {PROMOTION_GAMES}-ish confirmatory games vs {hof_labels[-2] if len(hof_labels) > 1 else 'default'})", flush=True)
    else:
      generations_since_promotion += 1

    history.append({"generation": generation, "best_winrate_vs_hof": best_fitness,
                     "mean_winrate_vs_hof": 1 - mean(losses), "promoted": promoted,
                     "winrate_vs_champion": winrate_vs_champion, "hof_size": len(hall_of_fame)})

  print(f"\nstopped after {generation} generations ({'stagnation' if generations_since_promotion >= STAGNATION_LIMIT else 'budget/cma-stop'})")
  print(f"final hall of fame: {hof_labels}")

  Path(args.log).parent.mkdir(parents=True, exist_ok=True)
  with open(args.log, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["generation", "best_winrate_vs_hof", "mean_winrate_vs_hof", "promoted", "winrate_vs_champion", "hof_size"])
    writer.writeheader()
    writer.writerows(history)

  with open(args.out, "w", encoding="utf-8") as f:
    json.dump({"champion_weights": hall_of_fame[-1], "hall_of_fame": hall_of_fame, "hof_labels": hof_labels,
               "generations_run": generation, "default_weights": DEFAULT_WEIGHTS}, f, indent=2)
  print(f"wrote {args.out}")


if __name__ == "__main__":
  main()
