"""S1 - matchup-structure fidelity: simulate real archived decklists against
each other and compare against the real vS Classic Data Reaper matchup matrix.

The 88 real HSReplay decks (data/hsreplay_classic/constructible_decklists.csv,
built by extract_hsreplay_decklists.py) carry no sub-archetype label - the
Wayback capture's archetype_id is a single per-class sentinel (-3/-4/-10),
not a real classification. So this script picks ONE representative deck per
named archetype (Face Hunter, Sunshine Hunter, Burn Mage, Freeze Mage, Aggro
Warrior, Control Warrior - the six vS covers) by scoring each real deck
against a small signature-card set per archetype, then simulates every
constructible pair of those six head-to-head and compares the simulated
win rates against data/vs_classic/matchup_matrix.csv via Spearman rank
correlation on the ordinals (the matrix is banded, not exact percentages -
see extract_vs_matchups.py).

Output: data/s1_simulated_matrix.csv, and a printed comparison table plus
the rank correlation.
"""
import sys, csv, json, argparse
from collections import Counter
from itertools import permutations
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
from game_manager import GameManager
from strategy import GreedyActionSmart, NeuralGreedy
from zones import Deck
from enums import Classes, CardSets

#set from --eval-weights in main(); None -> the default GreedyActionSmart,
#preserving the original S1 baseline behaviour exactly
AGENT_NET_WEIGHTS = None

HERE = Path(__file__).parent
DECKLISTS = HERE / "data" / "hsreplay_classic" / "constructible_decklists.csv"
REAL_MATRIX = HERE / "data" / "vs_classic" / "matchup_matrix.csv"
OUT = HERE / "data" / "s1_simulated_matrix.csv"
GAMES_PER_MATCHUP = 60

#archetype signature cards, picked from established Classic-format archetype
#knowledge. A deck's score is the count of these cards it contains (max 2
#each, since some are 2-ofs); the highest-scoring real deck per archetype
#(above MIN_SCORE) is used as that archetype's representative.
SIGNATURES = {
  "Face Hunter": {"Leper Gnome", "Argent Squire", "Eaglehorn Bow", "Kill Command", "Arcane Shot",
                   "Worgen Infiltrator", "Abusive Sergeant", "Wolfrider", "Unleash the Hounds"},
  "Sunshine Hunter": {"Starving Buzzard", "Houndmaster", "Savannah Highmane", "Timber Wolf",
                       "Scavenging Hyena", "Tundra Rhino", "Animal Companion"},
  "Freeze Mage": {"Ice Block", "Ice Barrier", "Doomsayer", "Acolyte of Pain", "Frost Nova",
                   "Blizzard", "Alexstrasza", "Water Elemental"},
  "Burn Mage": {"Mana Wyrm", "Sorcerer's Apprentice", "Archmage Antonidas", "Mirror Entity",
                "Ice Lance", "Mana Addict"},
  "Aggro Warrior": {"Warsong Commander", "Frothing Berserker", "Charge", "Cruel Taskmaster",
                     "Kor'kron Elite", "Arathi Weaponsmith"},
  "Control Warrior": {"Brawl", "Shield Slam", "Alexstrasza", "Gorehowl", "Armorsmith",
                       "Commanding Shout", "Shield Block", "Fiery War Axe"},
}
MIN_SCORE = 3
ARCHETYPE_CLASS = {"Face Hunter": "HUNTER", "Sunshine Hunter": "HUNTER",
                    "Freeze Mage": "MAGE", "Burn Mage": "MAGE",
                    "Aggro Warrior": "WARRIOR", "Control Warrior": "WARRIOR"}
CLASS_ENUM = {"HUNTER": Classes.HUNTER, "MAGE": Classes.MAGE, "WARRIOR": Classes.WARRIOR}
CARDSET_ENUM = {"HUNTER": CardSets.CLASSIC_HUNTER, "MAGE": CardSets.CLASSIC_MAGE, "WARRIOR": CardSets.CLASSIC_WARRIOR}


def load_decks():
  with DECKLISTS.open(encoding="utf-8") as f:
    return list(csv.DictReader(f))


def pick_representatives(decks):
  reps = {}
  scores = {}
  for archetype, signature in SIGNATURES.items():
    player_class = ARCHETYPE_CLASS[archetype]
    best, best_score = None, 0
    for deck in decks:
      if deck["class"] != player_class:
        continue
      cards = deck["card_list"].split("|")
      score = sum(min(cards.count(card), 2) for card in signature)
      if score > best_score:
        best, best_score = deck, score
    if best and best_score >= MIN_SCORE:
      reps[archetype] = best["card_list"].split("|")
      scores[archetype] = best_score
    else:
      print(f"no clean {archetype} found among real decks (best score {best_score}, need >= {MIN_SCORE})")
  return reps, scores


def make_agent():
  return NeuralGreedy(AGENT_NET_WEIGHTS) if AGENT_NET_WEIGHTS is not None else GreedyActionSmart()


def simulate_matchup(deck_a_list, class_a, deck_b_list, class_b):
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_a]])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_b]])
  game_manager.create_player(CLASS_ENUM[class_a], Deck.generate_from_decklist(deck_a_list), make_agent())
  game_manager.create_enemy(CLASS_ENUM[class_b], Deck.generate_from_decklist(deck_b_list), make_agent())
  result = game_manager.simulate(GAMES_PER_MATCHUP, silent=True, parralel=1, rng=True)
  return result[0] if result else None #mean win rate for the "player" side


def load_real_matrix():
  real = {}
  with REAL_MATRIX.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
      real[(row["hero_deck"], row["opponent_deck"])] = (float(row["winrate_band_pct"]), int(row["ordinal"]))
  return real


def spearman(pairs):
  #pairs: list of (real_ordinal, sim_winrate). No scipy dependency - rank by
  #hand and use the standard rank-correlation formula (ties averaged).
  def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
      j = i
      while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
        j += 1
      avg_rank = (i + j) / 2 + 1
      for k in range(i, j + 1):
        ranks[order[k]] = avg_rank
      i = j + 1
    return ranks

  reals = [p[0] for p in pairs]
  sims = [p[1] for p in pairs]
  rank_r, rank_s = ranks(reals), ranks(sims)
  n = len(pairs)
  d2 = sum((rank_r[i] - rank_s[i]) ** 2 for i in range(n))
  return 1 - (6 * d2) / (n * (n * n - 1)) if n > 1 else float("nan")


def main():
  global AGENT_NET_WEIGHTS, OUT
  parser = argparse.ArgumentParser()
  parser.add_argument("--eval-weights", default=None,
                       help="value-net .npz (neural_eval) piloting both sides; default = GreedyActionSmart")
  parser.add_argument("--out", default=None, help="output CSV override")
  args = parser.parse_args()
  if args.eval_weights:
    from neural_eval import load_weights
    AGENT_NET_WEIGHTS = load_weights(args.eval_weights)
  if args.out:
    OUT = Path(args.out)

  decks = load_decks()
  reps, scores = pick_representatives(decks)
  print("representative decks picked (signature-card score):")
  for archetype, score in scores.items():
    print(f"  {archetype}: score {score}")
  print()

  real_matrix = load_real_matrix()
  rows = []
  comparison = []
  for hero, opponent in permutations(reps.keys(), 2):
    if (hero, opponent) not in real_matrix:
      continue #below vS's reporting threshold, no ground truth to compare
    sim_winrate = simulate_matchup(reps[hero], ARCHETYPE_CLASS[hero], reps[opponent], ARCHETYPE_CLASS[opponent])
    if sim_winrate is None:
      continue
    real_pct, real_ordinal = real_matrix[(hero, opponent)]
    rows.append({"hero": hero, "opponent": opponent, "sim_winrate_pct": round(sim_winrate * 100, 1),
                 "real_winrate_band_pct": real_pct, "real_ordinal": real_ordinal})
    comparison.append((real_ordinal, sim_winrate))
    print(f"[{hero} vs {opponent}] sim={sim_winrate*100:.1f}% real_band={real_pct:.1f}% (ordinal {real_ordinal})")

  with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["hero", "opponent", "sim_winrate_pct", "real_winrate_band_pct", "real_ordinal"])
    writer.writeheader()
    writer.writerows(rows)

  rho = spearman(comparison)
  print(f"\n{len(rows)} matchups compared, {GAMES_PER_MATCHUP} games each")
  print(f"Spearman rank correlation (real ordinal vs simulated win rate): {rho:.3f}")
  print(f"wrote {OUT}")


if __name__ == "__main__":
  main()
