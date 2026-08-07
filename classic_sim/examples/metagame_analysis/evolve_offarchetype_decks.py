"""MAP-Elites deck evolution seeded from the 82 real off-archetype decks
(run_offarchetype_tournament.py) - the "mutate/evolve" follow-up to that
tournament, and the actual mechanism the thesis's metagame-shift prediction
relies on: an agent traversing an archive of decks that are NOT today's
real archetypes.

Design (per user's "power + diversity" choice over "power alone" or
"novelty alone"): reuses the existing map_elites.py Archive machinery -
same phenotype axes (hand size, turns) and same bin-elite-selection loop
shape as examples/metaspace_generation/coevolution.py - rather than
building a new diversity mechanism from scratch. That script co-evolves
BOTH agent weights and decks against a fixed opponent gauntlet; here only
the DECK is evolved (the agent is fixed to the best one this session
validated - self-play champion weights via GreedyActionSmart, not MCTS,
since an evolutionary loop needs many cheap generations x population x
gauntlet evaluations, not a handful of deep-search games) against a fixed
gauntlet of real decks, so fitness is directly "would this deck be
competitive if it showed up in the real field" - real ground truth, not a
self-referential agent-vs-agent signal.

One archive PER CLASS (Hunter/Mage/Warrior) since decks are class-locked -
mixing classes into one phenotype grid wouldn't let cross-class selection
make sense card-pool-wise. Each archive's initial population is that
class's real off-archetype decks (already legal, already-good starting
points - no cold random start needed, unlike coevolution.py's
generate_random_deck). Mutation swaps 0-3 individual card slots per
generation for a same-class pool card not already at its legal copy cap
(2, or 1 for legendaries - see LEGENDARY_NAMES), so evolved decks stay
legal, not just structurally 30 cards.

Fitness = mean win rate vs a fixed 9-deck real gauntlet (3 real decks per
class, the ones with the most real HSReplay total_games, for a reliable
comparison), using the fixed agent on both sides. Novelty (card-overlap
distance to the nearest ORIGINAL seed deck of the same class) is tracked
and reported per generation, but is NOT part of fitness or selection - the
user picked diversity-via-MAP-Elites-bins, not novelty-as-objective.

Usage (from classic_sim/examples/metagame_analysis):
  python evolve_offarchetype_decks.py --backend local --generations 2 --population 4 --out data/evolve_smoke
  python evolve_offarchetype_decks.py --backend ssh --generations 15 --population 20 --out data/evolve_offarchetype
"""
import sys, csv, json, argparse, subprocess, ast
from pathlib import Path
from statistics import mean
from random import random, randint, choice, shuffle

sys.path.append('../../src')
sys.path.append('../validation')
sys.path.append('../map_elites')
from game_manager import GameManager
from strategy import GreedyActionSmart
from zones import Deck
from enums import Classes, CardSets
from card_sets import build_pool, get_legendary_cards
from exceptions import TooManyActions

import dill
from scipy.stats import ttest_1samp
from joblib import Parallel, delayed

from run_offarchetype_tournament import load_offarchetype_decks
from map_elites import Archive

HERE = Path(__file__).parent
OUT_DIR = HERE / "data"
CLASSES = ["HUNTER", "MAGE", "WARRIOR"]
CLASS_ENUM = {"HUNTER": Classes.HUNTER, "MAGE": Classes.MAGE, "WARRIOR": Classes.WARRIOR}
CARDSET_ENUM = {"HUNTER": CardSets.CLASSIC_HUNTER, "MAGE": CardSets.CLASSIC_MAGE, "WARRIOR": CardSets.CLASSIC_WARRIOR}
GAUNTLET_PER_CLASS = 3

MIN_GAMES, MAX_GAMES, PVALUE_ALPHA, MIN_STREAK = 4, 12, 0.1, 2

LEGENDARY_NAMES = {card.name for card in get_legendary_cards()}


def max_copies(card_name):
  return 1 if card_name in LEGENDARY_NAMES else 2


def class_pool(player_class):
  pool = build_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[player_class]], None)
  return [card.name for card in pool]


def mutate_deck(deck, pool):
  """0-3 single-card-slot swaps, geometric-decay count (mostly 0-1, rarely
  more) - same shape as coevolution.py's peturb_agent_and_deck, adapted to
  work on arbitrary (not strictly-paired) real decklists and to respect
  legal copy caps instead of assuming every card is a 2-of."""
  deck = list(deck)
  num_swaps = 0
  for exponent in range(4):
    if random() < 1 / (2 ** exponent):
      num_swaps = exponent
  for _ in range(num_swaps):
    slot = randint(0, len(deck) - 1)
    candidates = [c for c in pool if deck.count(c) < max_copies(c)]
    if not candidates:
      continue
    deck[slot] = choice(candidates)
  return deck


def make_fixed_agent(eval_weights):
  return GreedyActionSmart(eval_weights) if eval_weights else GreedyActionSmart()


def play_matchup_till_stoppage(deck_a, class_a, deck_b, class_b, eval_weights,
                                min_games=MIN_GAMES, max_games=MAX_GAMES):
  """Returns (win_rate_for_a, mean_hand_size_a, mean_turns, games_played).
  Same early-stopping shape as the rest of this session's distributed work -
  min_games/max_games/eval_weights are real parameters, not module globals,
  for the same reason play_matchup_till_stoppage elsewhere in this codebase
  takes them that way (must survive dill-over-stdin into a fresh remote
  worker process)."""
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_a]])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_b]])
  game_manager.create_player(CLASS_ENUM[class_a], Deck.generate_from_decklist(deck_a), make_fixed_agent(eval_weights))
  game_manager.create_enemy(CLASS_ENUM[class_b], Deck.generate_from_decklist(deck_b), make_fixed_agent(eval_weights))
  game_manager.create_game()

  wins, hand_sizes, turn_counts = [], [], []
  streak = 0
  while len(wins) < max_games:
    try:
      result = game_manager.game.play_game()
      wins.append(1 if result[0] == 1 else 0)
      hand_sizes.append(result[2])
      turn_counts.append(result[3])
    except (TooManyActions, RecursionError):
      pass
    game_manager.game.reset_game()
    game_manager.game.start_game()

    if len(wins) >= min_games:
      win_rate = mean(wins)
      if win_rate in (0.0, 1.0):
        pvalue = 0.0
      else:
        pvalue = ttest_1samp(wins, popmean=0.5).pvalue
      streak = streak + 1 if pvalue < PVALUE_ALPHA else 0
      if streak >= MIN_STREAK:
        break

  return (mean(wins) if wins else 0.5, mean(hand_sizes) if hand_sizes else 5.0,
          mean(turn_counts) if turn_counts else 15.0, len(wins))


def _run_one(work_item):
  return play_matchup_till_stoppage(*work_item)


def run_matchups_local(work_items, cores):
  if cores == 1:
    return [_run_one(item) for item in work_items]
  return Parallel(n_jobs=cores)(delayed(_run_one)(item) for item in work_items)


HOSTS = ["dwail1", "dwail2"]


def run_host(work_items, host):
  if not work_items:
    return []
  print(f"Starting host {host} with {len(work_items)} work items...", flush=True)
  serial_work = dill.dumps(work_items, fmode='wb')
  dir_ = "~/phd/hearth-mici/classic_sim/examples/metagame_analysis/" if host == "laptop" else "~/classic_sim/examples/metagame_analysis/"
  command = f'cd {dir_} && source ~/.profile && pyenv activate venv && python3 evolve_remote_worker.py'
  ssh = subprocess.Popen(["ssh", host, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
  result, err = ssh.communicate(input=serial_work)
  if err:
    print(f"{host} error: {err.decode(errors='replace')}")

  for line in result.decode(errors="replace").splitlines():
    if line[:3] == ">>>":
      print(f"Closing host {host}.", flush=True)
      return ast.literal_eval(line[3:])
    else:
      print(f"{host}> {line}")
  raise RuntimeError(f"{host} never returned a >>> result line")


def run_matchups_ssh(work_items, cores):
  n = len(HOSTS)
  chunks = [work_items[i::n] for i in range(n)]
  host_results = Parallel(n_jobs=n, backend="threading")(delayed(run_host)(chunk, host) for chunk, host in zip(chunks, HOSTS))
  results = [None] * len(work_items)
  for host_index, this_host_results in enumerate(host_results):
    for offset, value in enumerate(this_host_results):
      results[host_index + offset * n] = value
  return results


def build_gauntlet():
  """3 real decks per class, the ones with the most real HSReplay
  total_games - a fixed, reliable-ground-truth opponent field every
  evolving deck (of any class) is measured against."""
  pool = load_offarchetype_decks(sort_by_games=True)
  gauntlet = []
  for player_class in CLASSES:
    class_decks = [d for d in pool if d["class"] == player_class][:GAUNTLET_PER_CLASS]
    for d in class_decks:
      gauntlet.append({"class": player_class, "deck": d["card_list"].split("|"), "deck_id": d["deck_id"]})
  return gauntlet


def novelty(deck, seed_decks):
  """Card-overlap distance (30 - shared card count, counting duplicates) to
  the closest ORIGINAL seed deck of the same class - a diagnostic only,
  not part of fitness/selection."""
  from collections import Counter
  deck_counts = Counter(deck)
  best = 30
  for seed in seed_decks:
    seed_counts = Counter(seed)
    shared = sum((deck_counts & seed_counts).values())
    best = min(best, 30 - shared)
  return best


def evaluate_population(population, player_class, gauntlet, eval_weights, cores, run_matchups):
  """population: list of decklists (all same player_class). Returns list of
  (fitness, hand_size, turns) tuples, one per individual, averaged over the
  fixed gauntlet."""
  work = []
  for deck in population:
    for opponent in gauntlet:
      work.append((deck, player_class, opponent["deck"], opponent["class"], eval_weights))
  results = run_matchups(work, cores)

  out = []
  n = len(gauntlet)
  for i in range(len(population)):
    matchup_results = results[i * n: (i + 1) * n]
    win_rates = [r[0] for r in matchup_results]
    hand_sizes = [r[1] for r in matchup_results]
    turns = [r[2] for r in matchup_results]
    out.append((mean(win_rates), mean(hand_sizes), mean(turns)))
  return out


def run_evolution(player_class, seed_decks, gauntlet, eval_weights, generations, population_size,
                   selection_count, num_buckets, cores, run_matchups, out_prefix):
  pool = class_pool(player_class)
  archive = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=num_buckets,
                     archive_name=f"{player_class} off-archetype evolution")

  history = []
  population = list(seed_decks)
  for generation in range(generations):
    population = [mutate_deck(deck, pool) for deck in population]
    stats = evaluate_population(population, player_class, gauntlet, eval_weights, cores, run_matchups)

    for deck, (fitness, hand_size, turns) in zip(population, stats):
      #Archive.get_elites(unique_only=True) keys on tuple(sample[0]+sample[1])
      #(coevolution.py's (agent, deck) convention) - wrap as ([], deck) so the
      #dedup key is the full 30-card deck, not just its first two cards.
      archive.add_sample(hand_size, turns, fitness=fitness, sample=([], deck))

    elites = archive.get_elites(selection_count, unique_only=True)
    novelties = [novelty(elite["sample"][1], seed_decks) for elite in elites]
    best = max(elites, key=lambda e: e["fitness"])
    print(f"[{player_class}] gen {generation}: population={len(elites)} "
          f"mean_fitness={mean(e['fitness'] for e in elites):.3f} best_fitness={best['fitness']:.3f} "
          f"mean_novelty={mean(novelties):.1f}/30", flush=True)
    history.append({"generation": generation, "population": len(elites),
                     "mean_fitness": mean(e["fitness"] for e in elites),
                     "best_fitness": best["fitness"], "mean_novelty": mean(novelties)})

    #next generation's parents: current archive elites (MAP-Elites selection,
    #mirroring coevolution.py's get_elites(max_selection_count, unique_only=True))
    population = [choice(elites)["sample"][1] for _ in range(population_size)] if len(elites) < population_size \
      else [e["sample"][1] for e in elites[:population_size]]

    archive.save(save_file=str(OUT_DIR / f"{out_prefix}_{player_class.lower()}_generation{generation}.json"))

  with open(OUT_DIR / f"{out_prefix}_{player_class.lower()}_history.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["generation", "population", "mean_fitness", "best_fitness", "mean_novelty"])
    writer.writeheader()
    writer.writerows(history)

  return archive, history


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=1, help="local backend only")
  parser.add_argument("--generations", type=int, default=15)
  parser.add_argument("--population", type=int, default=20, help="per-class population size / selection count")
  parser.add_argument("--num-buckets", type=int, default=15)
  parser.add_argument("--eval-weights", default=str(OUT_DIR / "self_play_champion.json"),
                       help="path to a JSON file with a 'champion_weights' or 'weights' key - the fixed agent "
                            "piloting BOTH the evolving decks and the real gauntlet. Pass '' for default weights.")
  parser.add_argument("--out", default="evolve_offarchetype")
  args = parser.parse_args()

  eval_weights = None
  if args.eval_weights:
    with open(args.eval_weights, encoding="utf-8") as f:
      loaded = json.load(f)
    full_weights = loaded.get("champion_weights") or loaded["weights"]
    eval_weights = full_weights  #GreedyActionSmart's own ordering - no drop needed (that's only for evaluate_position/MCTS)

  gauntlet = build_gauntlet()
  print(f"gauntlet: {len(gauntlet)} real decks ({GAUNTLET_PER_CLASS}/class)")

  pool = load_offarchetype_decks(sort_by_games=True)
  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local

  for player_class in CLASSES:
    class_decks = [d["card_list"].split("|") for d in pool if d["class"] == player_class]
    seed_decks = class_decks[:args.population] if len(class_decks) > args.population else class_decks
    print(f"\n=== {player_class}: {len(seed_decks)} seed decks ===")
    run_evolution(player_class, seed_decks, gauntlet, eval_weights, args.generations, args.population,
                  args.population, args.num_buckets, args.cores, run_matchups, args.out)

  print("\ndone")


if __name__ == "__main__":
  main()
