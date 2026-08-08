"""Predict a real 2014 metagame shock: evolve the PRE-shock real decks under
the POST-shock rules, and measure which cards the evolved population adopts.

The overall challenge (user): "given just the decks months before, predict
the decks post nerf/Naxx". Ground truth is naxx_adoption_series.py's
per-window card-adoption shares; this script produces the simulator's
prediction for comparison against them (and against the no-change baseline:
pre-shock adoption carried forward).

Eras:
  naxx_launch   seeds = real pre-Naxx decks, pool = Classic + Naxxramas
                -> predict the naxx_prenerf window's adoption
  buzzard_nerf  seeds = real Naxx-era decks, pool = Classic + Naxx with the
                real 22 Sept 2014 patch applied (Buzzard 5-mana 3/2,
                Leeroy 5-mana) -> predict the post_nerf window's adoption

Differences from evolve_offarchetype_decks.py (which this derives from):
  - the three class populations evolve in LOCKSTEP in one loop, because the
    gauntlet must span all classes and is refreshed from the archives
  - REFRESHING gauntlet: starts as real pre-shock decks (3/class); every
    REFRESH_EVERY generations, 2 of each class's 3 slots are replaced with
    decks sampled from that class's current archive elites, keeping 1 real
    anchor - the fix for the fixed-gauntlet overfitting the evolved-vs-pool
    confirm phase measured
  - era-aware pools/patches on both the matchup pools and the mutation pool
  - per-generation card-adoption extraction over unique archive elites -
    the final generation's shares are the prediction

Usage (from classic_sim/examples/metagame_analysis):
  python evolve_metagame_shift.py --era naxx_launch --backend local --cores 4 --generations 2 --population 6 --out data/shift_smoke
  python evolve_metagame_shift.py --era naxx_launch --backend ssh --out data/shift_naxx_launch
  python evolve_metagame_shift.py --era buzzard_nerf --backend ssh --out data/shift_buzzard_nerf
"""
import sys, csv, json, argparse, subprocess, ast
from collections import Counter
from pathlib import Path
from statistics import mean
from random import Random, random, randint, choice, choices

sys.path.append('../../src')
sys.path.append('../map_elites')
from game_manager import GameManager
from strategy import GreedyActionSmart, NeuralGreedy
from zones import Deck
from enums import Classes, CardSets
from card_sets import build_pool, get_legendary_cards, SEPT_2014_NERF_PATCHES
from exceptions import TooManyActions

import dill
from scipy.stats import ttest_1samp
from joblib import Parallel, delayed

from map_elites import Archive

HERE = Path(__file__).parent
OUT_DIR = HERE / "data"
SEEDS_DIR = HERE / ".." / "validation" / "data"
CLASSES = ["HUNTER", "MAGE", "WARRIOR"]
CLASS_ENUM = {"HUNTER": Classes.HUNTER, "MAGE": Classes.MAGE, "WARRIOR": Classes.WARRIOR}
ERA_SETS = {
  "HUNTER": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.NAXX_HUNTER],
  "MAGE": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.NAXX_MAGE],
  "WARRIOR": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_WARRIOR, CardSets.NAXX_WARRIOR],
}
ERAS = {
  "naxx_launch": {"seeds": "naxx_seeds_pre_naxx.json", "patches": None},
  "buzzard_nerf": {"seeds": "naxx_seeds_naxx_prenerf.json", "patches": SEPT_2014_NERF_PATCHES},
}

GAUNTLET_PER_CLASS = 3
GAUNTLET_REAL_ANCHORS = 1
REFRESH_EVERY = 3
MIN_GAMES, MAX_GAMES, PVALUE_ALPHA, MIN_STREAK = 4, 12, 0.1, 2

#Naxx legendaries hardcoded (Card carries no rarity field; the classic set's
#legendaries are enumerated by their own getter, Naxx's by this list)
NAXX_LEGENDARY_NAMES = {"Baron Rivendare", "Feugen", "Stalagg", "Loatheb", "Maexxna", "Kel'Thuzad"}
LEGENDARY_NAMES = {card.name for card in get_legendary_cards()} | NAXX_LEGENDARY_NAMES


def max_copies(card_name):
  return 1 if card_name in LEGENDARY_NAMES else 2


def era_class_pool(player_class):
  """Mutation pool: card names legal for this class in the Naxx era (patches
  change stats, never names, so the same pool serves both eras)."""
  return [card.name for card in build_pool(ERA_SETS[player_class], None)]


def mutate_deck(deck, pool, bias=None, bias_strength=10.0):
  """bias: {card: probed_delta_wr} from probe_card_values.py. Models the real
  players' non-neutral exploration: replacement candidates with positive
  probed value are proposed more often (weight 1 + strength*delta/max_delta),
  and slots holding negative-probed cards are replaced more often. Unprobed
  cards keep weight 1 / uniform slot odds."""
  deck = list(deck)
  num_swaps = 0
  for exponent in range(4):
    if random() < 1 / (2 ** exponent):
      num_swaps = exponent
  max_positive = max([d for d in bias.values() if d > 0], default=0) if bias else 0
  for _ in range(num_swaps):
    if bias:
      slot_weights = [1 + bias_strength * max(0.0, -bias.get(card, 0.0)) / max_positive if max_positive else 1
                      for card in deck]
      slot = choices(range(len(deck)), weights=slot_weights)[0]
    else:
      slot = randint(0, len(deck) - 1)
    candidates = [c for c in pool if deck.count(c) < max_copies(c)]
    if not candidates:
      continue
    if bias and max_positive:
      weights = [1 + bias_strength * max(0.0, bias.get(c, 0.0)) / max_positive for c in candidates]
      deck[slot] = choices(candidates, weights=weights)[0]
    else:
      deck[slot] = choice(candidates)
  return deck


def make_fixed_agent(eval_weights):
  #a dict is a value-net weight bundle (neural_eval arrays) -> NeuralGreedy;
  #a list is the linear feature weights -> GreedyActionSmart, as before
  if isinstance(eval_weights, dict):
    return NeuralGreedy(eval_weights)
  return GreedyActionSmart(eval_weights) if eval_weights else GreedyActionSmart()


def load_eval_weights(path):
  """.json -> linear weights list; .npz -> value-net weight dict."""
  if str(path).endswith(".npz"):
    from neural_eval import load_weights
    return load_weights(path)
  with open(path, encoding="utf-8") as f:
    loaded = json.load(f)
  return loaded.get("champion_weights") or loaded["weights"]


def play_matchup_till_stoppage(deck_a, class_a, deck_b, class_b, era, eval_weights,
                                min_games=MIN_GAMES, max_games=MAX_GAMES):
  """Returns (win_rate_for_a, mean_hand_size_a, mean_turns, games_played).
  era selects the card pools AND the historical patch state - it travels in
  the work item so a fresh remote worker rebuilds the right world."""
  patches = ERAS[era]["patches"]
  game_manager = GameManager()
  game_manager.create_player_pool(ERA_SETS[class_a], card_patches=patches)
  game_manager.create_enemy_pool(ERA_SETS[class_b], card_patches=patches)
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
  command = f'cd {dir_} && source ~/.profile && pyenv activate venv && python3 shift_remote_worker.py'
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


def load_seeds(era, population_size, rng):
  """population_size random real pre-shock decks per class (reproducible),
  plus the full per-class seed lists (novelty reference + gauntlet anchors)."""
  with (SEEDS_DIR / ERAS[era]["seeds"]).open(encoding="utf-8") as f:
    all_seeds = json.load(f)
  populations, full = {}, {}
  for player_class in CLASSES:
    class_seeds = all_seeds[player_class]
    full[player_class] = class_seeds
    populations[player_class] = [list(deck) for deck in rng.sample(class_seeds, min(population_size, len(class_seeds)))]
  return populations, full


def initial_gauntlet(full_seeds, rng):
  return [{"class": player_class, "deck": list(deck)}
          for player_class in CLASSES
          for deck in rng.sample(full_seeds[player_class], GAUNTLET_PER_CLASS)]


def refresh_gauntlet(archives, full_seeds, rng):
  """1 real anchor + 2 archive elites per class. Falls back to real decks
  while an archive is still too empty."""
  gauntlet = []
  for player_class in CLASSES:
    entries = [{"class": player_class, "deck": list(deck)}
               for deck in rng.sample(full_seeds[player_class], GAUNTLET_REAL_ANCHORS)]
    elites = archives[player_class].get_elites(unique_only=True)
    wanted = GAUNTLET_PER_CLASS - GAUNTLET_REAL_ANCHORS
    if len(elites) >= wanted:
      picks = rng.sample(elites, wanted)
    else:
      picks = elites
    entries.extend({"class": player_class, "deck": list(e["sample"][1])} for e in picks)
    while len(entries) < GAUNTLET_PER_CLASS:
      entries.append({"class": player_class, "deck": list(rng.choice(full_seeds[player_class]))})
    gauntlet.extend(entries)
  return gauntlet


def novelty(deck, seed_decks):
  deck_counts = Counter(deck)
  best = 30
  for seed in seed_decks:
    shared = sum((deck_counts & Counter(seed)).values())
    best = min(best, 30 - shared)
  return best


def adoption_shares(archive):
  """Card inclusion share over the archive's unique elite decks."""
  elites = archive.get_elites(unique_only=True)
  decks = [e["sample"][1] for e in elites]
  if not decks:
    return {}, 0
  inclusion = Counter()
  for deck in decks:
    for card in set(deck):
      inclusion[card] += 1
  return {card: count / len(decks) for card, count in inclusion.items()}, len(decks)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--era", choices=list(ERAS), required=True)
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=1, help="local backend only")
  parser.add_argument("--generations", type=int, default=15)
  parser.add_argument("--population", type=int, default=20, help="per-class population size / selection count")
  parser.add_argument("--num-buckets", type=int, default=15)
  parser.add_argument("--seed", type=int, default=0, help="rng seed for seed-deck/gauntlet sampling")
  parser.add_argument("--eval-weights", default=str(OUT_DIR / "self_play_champion.json"),
                       help="fixed agent weights piloting both sides. Pass '' for default weights.")
  parser.add_argument("--mutation-bias", default=None,
                       help="probe_card_values.py CSV - biases mutation toward probed-positive cards "
                            "and away from probed-negative slots (per class)")
  parser.add_argument("--bias-strength", type=float, default=10.0)
  parser.add_argument("--fixed-games", type=int, default=None,
                       help="fixed games per matchup (min=max, no early stopping) - reduces selection "
                            "noise at higher cost; default keeps the exploratory 4-12 early stop")
  parser.add_argument("--out", default=None, help="output prefix (default data/shift_<era>)")
  args = parser.parse_args()

  out_prefix = args.out or f"data/shift_{args.era}"
  out_prefix = str(Path(out_prefix).name)
  rng = Random(args.seed)

  eval_weights = load_eval_weights(args.eval_weights) if args.eval_weights else None

  bias_by_class = None
  if args.mutation_bias:
    bias_by_class = {c: {} for c in CLASSES}
    with open(args.mutation_bias, encoding="utf-8") as f:
      for row in csv.DictReader(f):
        bias_by_class[row["class"]][row["card"]] = float(row["mean_delta_wr"])
    print(f"mutation bias loaded: { {c: len(bias_by_class[c]) for c in CLASSES} } probed cards/class")

  populations, full_seeds = load_seeds(args.era, args.population, rng)
  gauntlet = initial_gauntlet(full_seeds, rng)
  pools = {player_class: era_class_pool(player_class) for player_class in CLASSES}
  archives = {player_class: Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35),
                                     num_buckets=args.num_buckets,
                                     archive_name=f"{player_class} {args.era}")
              for player_class in CLASSES}
  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local

  print(f"era={args.era} | seeds/class={ {c: len(full_seeds[c]) for c in CLASSES} } | "
        f"population={args.population}/class | gauntlet={len(gauntlet)} | pool sizes="
        f"{ {c: len(pools[c]) for c in CLASSES} }")

  fitness_path = OUT_DIR / f"{out_prefix}_history.csv"
  adoption_path = OUT_DIR / f"{out_prefix}_adoption_history.csv"
  with fitness_path.open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerow(["generation", "class", "n_elites", "mean_fitness", "best_fitness", "mean_novelty"])
  with adoption_path.open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerow(["generation", "class", "card", "share", "n_unique_elites"])

  for generation in range(args.generations):
    if generation > 0 and generation % REFRESH_EVERY == 0:
      gauntlet = refresh_gauntlet(archives, full_seeds, rng)
      print(f"gen {generation}: gauntlet refreshed ({GAUNTLET_REAL_ANCHORS} real + "
            f"{GAUNTLET_PER_CLASS - GAUNTLET_REAL_ANCHORS} elite per class)", flush=True)

    #mutate all three class populations, evaluate everything in ONE dispatch
    #so the ssh hosts get a single large batch per generation
    for player_class in CLASSES:
      class_bias = bias_by_class[player_class] if bias_by_class else None
      populations[player_class] = [mutate_deck(deck, pools[player_class], class_bias, args.bias_strength)
                                   for deck in populations[player_class]]
    work, spans = [], {}
    for player_class in CLASSES:
      start = len(work)
      for deck in populations[player_class]:
        for opponent in gauntlet:
          if args.fixed_games:
            work.append((deck, player_class, opponent["deck"], opponent["class"], args.era,
                         eval_weights, args.fixed_games, args.fixed_games))
          else:
            work.append((deck, player_class, opponent["deck"], opponent["class"], args.era, eval_weights))
      spans[player_class] = (start, len(work))
    results = run_matchups(work, args.cores)

    n = len(gauntlet)
    for player_class in CLASSES:
      start, end = spans[player_class]
      class_results = results[start:end]
      archive = archives[player_class]
      for i, deck in enumerate(populations[player_class]):
        matchup_results = class_results[i * n: (i + 1) * n]
        fitness = mean(r[0] for r in matchup_results)
        hand_size = mean(r[1] for r in matchup_results)
        turns = mean(r[2] for r in matchup_results)
        archive.add_sample(hand_size, turns, fitness=fitness, sample=([], deck))

      elites = archive.get_elites(args.population, unique_only=True)
      novelties = [novelty(e["sample"][1], full_seeds[player_class]) for e in elites]
      best = max(elites, key=lambda e: e["fitness"])
      print(f"[{player_class}] gen {generation}: elites={len(elites)} "
            f"mean_fitness={mean(e['fitness'] for e in elites):.3f} best_fitness={best['fitness']:.3f} "
            f"mean_novelty={mean(novelties):.1f}/30", flush=True)
      with fitness_path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([generation, player_class, len(elites),
                                 round(mean(e["fitness"] for e in elites), 4),
                                 round(best["fitness"], 4), round(mean(novelties), 2)])

      shares, n_unique = adoption_shares(archive)
      with adoption_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for card, share in sorted(shares.items()):
          writer.writerow([generation, player_class, card, round(share, 4), n_unique])

      populations[player_class] = [choice(elites)["sample"][1] for _ in range(args.population)] \
        if len(elites) < args.population else [e["sample"][1] for e in elites[:args.population]]

      archive.save(save_file=str(OUT_DIR / f"{out_prefix}_{player_class.lower()}_generation{generation}.json"))

  #final-generation adoption = the prediction, in the same shape as the
  #naxx_adoption_{window}.csv ground truth for direct comparison
  prediction_path = OUT_DIR / f"{out_prefix}_predicted_adoption.csv"
  final = {player_class: adoption_shares(archives[player_class]) for player_class in CLASSES}
  all_cards = sorted(set().union(*(final[c][0] for c in CLASSES)))
  with prediction_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["card"] + [f"{c.lower()}_share" for c in CLASSES] + [f"{c.lower()}_n_elites" for c in CLASSES])
    for card in all_cards:
      writer.writerow([card] + [round(final[c][0].get(card, 0.0), 4) for c in CLASSES]
                      + [final[c][1] for c in CLASSES])
  print(f"\nwrote {prediction_path}")


if __name__ == "__main__":
  main()
