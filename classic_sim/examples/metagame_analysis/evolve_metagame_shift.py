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
import sys, csv, json, argparse, subprocess, ast, time
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


#Real 2014 constructed decks average 17.5-18.9 DISTINCT cards out of 30 -
#players run a second copy of most non-legendary cards for consistency. A
#swap that draws uniformly from the ~120-card legal pool almost always lands
#on a card the deck does not yet have, so unbiased mutation erodes that
#structure and drifts toward all-singleton decks (measured 19-23 distinct,
#and worse under free-running self-play). PAIR_BIAS up-weights, as a
#replacement candidate, a card already held as a 1-of that can legally become
#a 2-of, pulling the distinct-card count back toward the real range.
#Legendaries have max_copies 1, so they are never eligible to double and stay
#singletons automatically. 1-ofs remain reachable: the bias is a multiplier,
#not a rule, so genuinely-best single copies still win slots.
PAIR_BIAS = 4.0


def mutate_deck(deck, pool, bias=None, bias_strength=10.0, owned=None,
                rarity_weights=None, pair_bias=PAIR_BIAS):
  """bias: {card: probed_delta_wr} from probe_card_values.py. Models the real
  players' non-neutral exploration: replacement candidates with positive
  probed value are proposed more often (weight 1 + strength*delta/max_delta),
  and slots holding negative-probed cards are replaced more often. Unprobed
  cards keep weight 1 / uniform slot odds.

  owned: this deck's owner's collection (set of card names). Only owned cards
  can be proposed - the hard half of the collection constraint.
  rarity_weights: {card: weight in (0,1]} multiplying the proposal odds, so
  rares/epics/legendaries are proposed proportionally less often even when
  owned - the soft half. Both default to off (unconstrained pool).
  pair_bias: multiplier on candidates already held as a 1-of that can become
  a 2-of, so mutation builds the 2-ofs real decks run instead of drifting to
  all singletons. 1.0 disables it (old behaviour)."""
  deck = list(deck)
  num_swaps = 0
  for exponent in range(4):
    if random() < 1 / (2 ** exponent):
      num_swaps = exponent
  max_positive = max([d for d in bias.values() if d > 0], default=0) if bias else 0
  #distinct-card count only DROPS when a swap removes a singleton and adds a
  #copy of a card the deck already holds once. So pairing needs both sides:
  #a slot holding a 1-of (removing it loses a distinct card) and a candidate
  #that is an existing 1-of (adding it costs no distinct card). pair_bias
  #up-weights both. Non-legendary only - legendaries have max_copies 1, so
  #they are never an existing 1-of eligible to double and stay singletons.
  for _ in range(num_swaps):
    slot_weights = [1.0] * len(deck)
    if bias and max_positive:
      slot_weights = [w * (1 + bias_strength * max(0.0, -bias.get(card, 0.0)) / max_positive)
                      for w, card in zip(slot_weights, deck)]
    if pair_bias != 1.0:
      slot_weights = [w * pair_bias if (deck.count(card) == 1 and max_copies(card) == 2) else w
                      for w, card in zip(slot_weights, deck)]
    slot = choices(range(len(deck)), weights=slot_weights)[0]
    #removing this slot's card frees one of its copies, so eligibility is
    #judged against the deck WITHOUT it (lets a 2-of card be re-proposed, and
    #keeps counts honest for the pair test)
    remaining = list(deck)
    del remaining[slot]
    candidates = [c for c in pool if remaining.count(c) < max_copies(c)
                  and (owned is None or c in owned)]
    if not candidates:
      continue
    weights = [1.0] * len(candidates)
    if bias and max_positive:
      weights = [w * (1 + bias_strength * max(0.0, bias.get(c, 0.0)) / max_positive)
                 for w, c in zip(weights, candidates)]
    if rarity_weights:
      weights = [w * rarity_weights.get(c, 1.0) for w, c in zip(weights, candidates)]
    if pair_bias != 1.0:
      weights = [w * pair_bias if (remaining.count(c) == 1 and max_copies(c) == 2) else w
                 for w, c in zip(weights, candidates)]
    deck[slot] = choices(candidates, weights=weights)[0]
  return deck


def sample_collections(pool, seed_decks, prior, rarity_by_name, rng,
                        adventure_names=frozenset(), adventure_ownership=1.0):
  """One collection per population slot: a slot is a PLAYER, and collections
  are persistent - the same slot keeps its collection for the whole run.

  Two gates, because 2014 had two:
    - CRAFTABLE (Classic/Basic) cards: owned independently with probability
      prior[rarity], a soft inverse-dust-cost prior.
    - ADVENTURE (Naxxramas) cards: not craftable at all. The wings deliver the
      whole set, so this is one all-or-nothing draw per player at
      adventure_ownership - which is what bounds every Naxx card's adoption
      below 100% regardless of how strong the simulator thinks it is.
  Plus, unconditionally, every card in the real deck the player started from
  (they demonstrably had those), so genuinely popular real cards are not
  penalised by the prior."""
  #stratified rather than i.i.d.: with a 14-slot population an i.i.d. draw at
  #q=0.7 lands anywhere from 8 to 13 owners, which would be the dominant source
  #of run-to-run variance in exactly the quantity under test
  n_owners = int(round(adventure_ownership * len(seed_decks)))
  adventure_flags = [True] * n_owners + [False] * (len(seed_decks) - n_owners)
  rng.shuffle(adventure_flags)

  collections = []
  for has_adventure, seed_deck in zip(adventure_flags, seed_decks):
    owned = set()
    for name in pool:
      if name in adventure_names:
        if has_adventure:
          owned.add(name)
      elif rng.random() < prior[rarity_by_name.get(name, "COMMON")]:
        owned.add(name)
    owned.update(seed_deck)
    collections.append(owned)
  return collections


def enforce_collection(deck, owned, pool, bias=None, bias_strength=10.0, rarity_weights=None):
  """Netdecking with substitutions: a player who copies someone else's elite
  list still cannot play cards they do not own, so every unowned slot is
  refilled from their own collection. Without this the constraint would not
  bind at all - elite decks are inherited wholesale, so one owner of a card is
  enough to spread it to the entire population."""
  if owned is None:
    return list(deck)
  deck = list(deck)
  max_positive = max([d for d in bias.values() if d > 0], default=0) if bias else 0
  for slot, card in enumerate(deck):
    if card in owned:
      continue
    candidates = [c for c in pool if c in owned and deck.count(c) < max_copies(c)]
    if not candidates:
      continue
    weights = [1 + bias_strength * max(0.0, bias.get(c, 0.0)) / max_positive
               for c in candidates] if max_positive else [1.0] * len(candidates)
    if rarity_weights:
      weights = [w * rarity_weights.get(c, 1.0) for w, c in zip(weights, candidates)]
    deck[slot] = choices(candidates, weights=weights)[0]
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
#None = the original worker with joblib n_jobs=-1 (all cores). An int caps the
#remote pool via shift_remote_worker_capped.py, so several drivers can share
#one host - set by --remote-cores.
REMOTE_CORES = None


#the link to the hosts is a VPN tunnel that occasionally drops for a minute;
#an hours-long evolution should survive that rather than lose every generation
#computed so far. Work is idempotent, so a dropped dispatch is simply re-sent.
DISPATCH_ATTEMPTS = 5
DISPATCH_BACKOFF = 60


def run_host(work_items, host):
  if not work_items:
    return []
  serial_work = dill.dumps(work_items, fmode='wb')
  dir_ = "~/phd/hearth-mici/classic_sim/examples/metagame_analysis/" if host == "laptop" else "~/classic_sim/examples/metagame_analysis/"
  worker = ("shift_remote_worker.py" if REMOTE_CORES is None
            else f"SHIFT_WORKER_JOBS={REMOTE_CORES} python3 shift_remote_worker_capped.py")
  worker = f"python3 {worker}" if REMOTE_CORES is None else worker
  command = f'cd {dir_} && source ~/.profile && pyenv activate venv && {worker}'
  ssh_options = ["-o", "ConnectTimeout=30", "-o", "ConnectionAttempts=3",
                 "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=10"]

  for attempt in range(1, DISPATCH_ATTEMPTS + 1):
    print(f"Starting host {host} with {len(work_items)} work items "
          f"(attempt {attempt}/{DISPATCH_ATTEMPTS})...", flush=True)
    ssh = subprocess.Popen(["ssh"] + ssh_options + [host, command], shell=False,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    result, err = ssh.communicate(input=serial_work)
    if err:
      print(f"{host} error: {err.decode(errors='replace')}")

    for line in result.decode(errors="replace").splitlines():
      if line[:3] == ">>>":
        print(f"Closing host {host}.", flush=True)
        return ast.literal_eval(line[3:])
      else:
        print(f"{host}> {line}")
    print(f"{host} never returned a >>> result line on attempt {attempt}", flush=True)
    if attempt < DISPATCH_ATTEMPTS:
      time.sleep(DISPATCH_BACKOFF * attempt)
  raise RuntimeError(f"{host} never returned a >>> result line in {DISPATCH_ATTEMPTS} attempts")


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


def refresh_gauntlet(archives, full_seeds, rng, real_anchors=GAUNTLET_REAL_ANCHORS):
  """real_anchors real decks + (3 - real_anchors) archive elites per class.
  Falls back to real decks while an archive is still too empty. real_anchors=3
  keeps the field permanently real (rotating, not fixed) - the opt-in test of
  the self-play echo chamber."""
  gauntlet = []
  for player_class in CLASSES:
    entries = [{"class": player_class, "deck": list(deck)}
               for deck in rng.sample(full_seeds[player_class], real_anchors)]
    elites = archives[player_class].get_elites(unique_only=True)
    wanted = GAUNTLET_PER_CLASS - real_anchors
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
  global HOSTS, REMOTE_CORES
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
  parser.add_argument("--pair-bias", type=float, default=PAIR_BIAS,
                       help="up-weight making a held 1-of into a 2-of, so evolved decks "
                            "run the duplicates real decks do instead of drifting to all "
                            "singletons; 1.0 disables (old behaviour)")
  parser.add_argument("--fixed-games", type=int, default=None,
                       help="fixed games per matchup (min=max, no early stopping) - reduces selection "
                            "noise at higher cost; default keeps the exploratory 4-12 early stop")
  parser.add_argument("--out", default=None, help="output prefix (default data/shift_<era>)")
  parser.add_argument("--hosts", default=",".join(HOSTS),
                       help="comma-separated ssh hosts for --backend ssh (default both)")
  parser.add_argument("--remote-cores", type=int, default=None,
                       help="cap the remote joblib pool (default: all cores, unchanged). Use when "
                            "several drivers share one host.")
  parser.add_argument("--real-anchors", type=int, default=GAUNTLET_REAL_ANCHORS,
                       choices=range(0, GAUNTLET_PER_CLASS + 1),
                       help="permanent REAL decks per class in the refreshed gauntlet "
                            f"(default {GAUNTLET_REAL_ANCHORS}); 3 keeps the field entirely real, "
                            "breaking the self-play echo chamber")
  parser.add_argument("--collection", choices=["none", "weight", "own", "both"], default="none",
                       help="collection constraints (default none = every deck may use the whole "
                            "pool). weight: rares/epics/legendaries are PROPOSED less often, in "
                            "proportion to an ownership prior derived from crafting cost. own: each "
                            "population slot is a player with a persistent sampled collection, and "
                            "netdecked lists get unowned cards substituted out. both: both.")
  parser.add_argument("--collection-exponent", type=float, default=0.25,
                       help="ownership prior p = (40/dust)**exponent; 1.0 is literal inverse dust "
                            "cost, 0.25 (default) gives rare .80 / epic .56 / legendary .40")
  parser.add_argument("--collection-strength", type=float, default=1.0,
                       help="blend the prior back toward 'everyone owns everything' (0 = off)")
  parser.add_argument("--adventure-ownership", type=float, default=0.7,
                       help="probability a simulated player has the Naxxramas cards at all. Naxx "
                            "cards are not craftable, so they are gated all-or-nothing per player "
                            "by the wing purchases; 0.7 reflects the five wings still rolling out "
                            "weekly through the first month of the predicted window plus purchase "
                            "friction. Only used with --collection own/both.")
  args = parser.parse_args()

  out_prefix = args.out or f"data/shift_{args.era}"
  out_prefix = str(Path(out_prefix).name)
  rng = Random(args.seed)

  #run_matchups_ssh fans out over this module global, so rebinding it here is
  #what --hosts actually does
  HOSTS = [host.strip() for host in args.hosts.split(",") if host.strip()]
  REMOTE_CORES = args.remote_cores
  print(f"ssh hosts: {HOSTS} (remote cores: {REMOTE_CORES or 'all'})")

  rarity_weights, prior, rarity_by_name, adventure_names = None, None, None, frozenset()
  if args.collection != "none":
    from card_rarity import RARITY_BY_NAME, NAXX_NAMES, ownership_prior, card_weights
    rarity_by_name = RARITY_BY_NAME
    adventure_names = NAXX_NAMES
    prior = ownership_prior(args.collection_exponent, args.collection_strength)
    if args.collection in ("weight", "both"):
      rarity_weights = card_weights(set(RARITY_BY_NAME), args.collection_exponent,
                                     args.collection_strength)
    print(f"collection constraints: mode={args.collection} "
          f"prior={ {k: round(v, 3) for k, v in prior.items()} } "
          f"adventure_ownership={args.adventure_ownership}")

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

  collections = {player_class: None for player_class in CLASSES}
  if args.collection in ("own", "both"):
    collection_rng = Random(args.seed + 9973)
    for player_class in CLASSES:
      collections[player_class] = sample_collections(pools[player_class], populations[player_class],
                                                      prior, rarity_by_name, collection_rng,
                                                      adventure_names, args.adventure_ownership)
    print("collections sampled: "
          + " ".join(f"{c}:{mean(len(o) for o in collections[c]):.0f}/{len(pools[c])} cards owned"
                     for c in CLASSES))

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
      gauntlet = refresh_gauntlet(archives, full_seeds, rng, args.real_anchors)
      print(f"gen {generation}: gauntlet refreshed ({args.real_anchors} real + "
            f"{GAUNTLET_PER_CLASS - args.real_anchors} elite per class)", flush=True)

    #mutate all three class populations, evaluate everything in ONE dispatch
    #so the ssh hosts get a single large batch per generation
    for player_class in CLASSES:
      class_bias = bias_by_class[player_class] if bias_by_class else None
      owners = collections[player_class]
      populations[player_class] = [mutate_deck(deck, pools[player_class], class_bias, args.bias_strength,
                                                owners[i] if owners else None, rarity_weights,
                                                pair_bias=args.pair_bias)
                                   for i, deck in enumerate(populations[player_class])]
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

      inherited = [choice(elites)["sample"][1] for _ in range(args.population)] \
        if len(elites) < args.population else [e["sample"][1] for e in elites[:args.population]]
      owners = collections[player_class]
      populations[player_class] = inherited if not owners else [
        enforce_collection(deck, owners[i], pools[player_class],
                            bias_by_class[player_class] if bias_by_class else None,
                            args.bias_strength, rarity_weights)
        for i, deck in enumerate(inherited)]

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

  #secondary artifact: adoption over the final POPULATION (the decks the
  #simulated players are actually holding) rather than over archive elites
  #(the decks that won). Under collection constraints these differ - the
  #ground truth is a population of submitted decks, not a winners' list.
  population_path = OUT_DIR / f"{out_prefix}_population_adoption.csv"
  pop_shares = {}
  for player_class in CLASSES:
    decks = populations[player_class]
    inclusion = Counter()
    for deck in decks:
      for card in set(deck):
        inclusion[card] += 1
    pop_shares[player_class] = ({card: count / len(decks) for card, count in inclusion.items()},
                                len(decks))
  all_cards = sorted(set().union(*(pop_shares[c][0] for c in CLASSES)))
  with population_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["card"] + [f"{c.lower()}_share" for c in CLASSES] + [f"{c.lower()}_n_elites" for c in CLASSES])
    for card in all_cards:
      writer.writerow([card] + [round(pop_shares[c][0].get(card, 0.0), 4) for c in CLASSES]
                      + [pop_shares[c][1] for c in CLASSES])
  print(f"wrote {population_path}")


if __name__ == "__main__":
  main()
