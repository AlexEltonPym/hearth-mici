"""Marginal-value probe: what is each candidate card WORTH, one card at a time?

The first naxx_launch evolution run showed why whole-deck evolution can't
answer the adoption question at feasible budgets: a single card swap moves a
deck's win rate by ~1pp, far below the early-stopped evaluation noise, so
the population drifts instead of selecting. This probe isolates the single
variable: for each candidate card, swap it into real pre-shock host decks
at a FIXED slot (the same removal slot for every candidate, so differences
between candidates are exactly the added card) and measure the win-rate
delta against a fixed real-deck field at confirm fidelity (fixed games, no
early stopping).

Modes:
  addition (naxx_launch): candidates = the 22 class-legal Naxx cards; hosts
    = real pre-Naxx seed decks. Predicts which new cards are worth playing.
  removal (buzzard_nerf): candidates = the nerfed cards (Buzzard, Leeroy);
    hosts = real Naxx-era decks that RUN the card; the candidate is replaced
    by the host's class staple. Positive removal value in the patched world
    predicts the card gets dropped.

Outputs data/probe_{era}.csv: class, card, mode, mean delta win rate,
per-host deltas, games - plus a comparison against real adoption shifts.

Usage (from classic_sim/examples/metagame_analysis):
  python probe_card_values.py --era naxx_launch --backend ssh --games 60
  python probe_card_values.py --era buzzard_nerf --backend ssh --games 60
"""
import sys, csv, json, argparse
from collections import Counter
from pathlib import Path
from statistics import mean
from random import Random

sys.path.append('../../src')
from enums import CardSets
from card_sets import build_pool

from evolve_metagame_shift import (CLASSES, ERA_SETS, ERAS, LEGENDARY_NAMES, OUT_DIR, SEEDS_DIR,
                                    load_eval_weights, run_matchups_local, run_matchups_ssh)

HOSTS_PER_CLASS = 5
FIELD_PER_CLASS = 3

NAXX_NEUTRALS = ["Zombie Chow", "Undertaker", "Echoing Ooze", "Haunted Creeper", "Mad Scientist",
                 "Nerub'ar Weblord", "Nerubian Egg", "Unstable Ghoul", "Dancing Swords", "Deathlord",
                 "Shade of Naxxramas", "Stoneskin Gargoyle", "Baron Rivendare", "Wailing Soul",
                 "Feugen", "Stalagg", "Loatheb", "Sludge Belcher", "Spectral Knight", "Maexxna",
                 "Kel'Thuzad"]
NAXX_CLASS = {"HUNTER": ["Webspinner"], "MAGE": ["Duplicate"], "WARRIOR": ["Death's Bite"]}
REMOVAL_CANDIDATES = ["Starving Buzzard", "Leeroy Jenkins"]
#neutral, stat-honest substitute when a removal candidate is taken out
REMOVAL_SUBSTITUTE = {"HUNTER": "Chillwind Yeti", "MAGE": "Chillwind Yeti", "WARRIOR": "Chillwind Yeti"}


def load_seeds(era):
  with (SEEDS_DIR / ERAS[era]["seeds"]).open(encoding="utf-8") as f:
    return json.load(f)


def pick_removal_slot(deck, rng):
  """One fixed, non-legendary slot per host - shared by every candidate."""
  candidates = [i for i, card in enumerate(deck) if card not in LEGENDARY_NAMES]
  return rng.choice(candidates)


def build_field(seeds, rng):
  return [{"class": player_class, "deck": list(deck)}
          for player_class in CLASSES
          for deck in rng.sample(seeds[player_class], FIELD_PER_CLASS)]


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--era", choices=list(ERAS), required=True)
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--games", type=int, default=60)
  parser.add_argument("--hosts", type=int, default=HOSTS_PER_CLASS)
  parser.add_argument("--seed", type=int, default=0)
  parser.add_argument("--eval-weights", default=str(OUT_DIR / "self_play_champion.json"))
  args = parser.parse_args()

  rng = Random(args.seed)
  mode = "removal" if args.era == "buzzard_nerf" else "addition"
  eval_weights = load_eval_weights(args.eval_weights) if args.eval_weights else None

  seeds = load_seeds(args.era)
  field = build_field(seeds, rng)

  #per class: hosts + the variant decks per candidate
  plan = {}  #class -> {"hosts": [deck...], "slots": [i...], "candidates": {card: [variant per host]}}
  for player_class in CLASSES:
    if mode == "addition":
      hosts = [list(deck) for deck in rng.sample(seeds[player_class], args.hosts)]
      slots = [pick_removal_slot(deck, rng) for deck in hosts]
      candidates = {}
      for card in NAXX_NEUTRALS + NAXX_CLASS[player_class]:
        variants = []
        for deck, slot in zip(hosts, slots):
          variant = list(deck)
          variant[slot] = card
          variants.append(variant)
        candidates[card] = variants
    else:
      candidates = {}
      hosts, slots = [], []
      for card in REMOVAL_CANDIDATES:
        with_card = [deck for deck in seeds[player_class] if card in deck]
        picked = [list(deck) for deck in rng.sample(with_card, min(args.hosts, len(with_card)))]
        variants = []
        for deck in picked:
          variant = list(deck)
          variant[variant.index(card)] = REMOVAL_SUBSTITUTE[player_class]
          variants.append(variant)
        candidates[card] = variants
        hosts.extend(picked)  #removal baselines are per-candidate hosts
      #in removal mode "hosts" is the concatenation, candidate order fixed
      plan[player_class] = {"hosts": hosts, "candidates": candidates}
      continue
    plan[player_class] = {"hosts": hosts, "candidates": candidates}

  #assemble one flat work list: baselines first, then variants
  work, index = [], []
  for player_class in CLASSES:
    for i, deck in enumerate(plan[player_class]["hosts"]):
      for opponent in field:
        work.append((deck, player_class, opponent["deck"], opponent["class"], args.era,
                     eval_weights, args.games, args.games))
      index.append(("baseline", player_class, i))
    for card, variants in plan[player_class]["candidates"].items():
      for i, deck in enumerate(variants):
        for opponent in field:
          work.append((deck, player_class, opponent["deck"], opponent["class"], args.era,
                       eval_weights, args.games, args.games))
        index.append((card, player_class, i))

  n_field = len(field)
  print(f"era={args.era} mode={mode}: {len(index)} deck evaluations x {n_field} opponents "
        f"x {args.games} games = {len(work) * args.games} games", flush=True)
  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local
  results = run_matchups(work, args.cores)

  win_rates = {}
  for j, key in enumerate(index):
    matchups = results[j * n_field: (j + 1) * n_field]
    win_rates[key] = mean(r[0] for r in matchups)

  rows = []
  for player_class in CLASSES:
    if mode == "addition":
      base = [win_rates[("baseline", player_class, i)] for i in range(len(plan[player_class]["hosts"]))]
      for card in plan[player_class]["candidates"]:
        deltas = [win_rates[(card, player_class, i)] - base[i]
                  for i in range(len(plan[player_class]["candidates"][card]))]
        rows.append({"class": player_class, "card": card, "mode": mode,
                     "mean_delta_wr": round(mean(deltas), 4),
                     "host_deltas": "|".join(f"{d:+.3f}" for d in deltas),
                     "games_per_side": len(deltas) * n_field * args.games})
    else:
      #removal-mode hosts are per-candidate concatenations, in candidate order
      offset = 0
      for card, variants in plan[player_class]["candidates"].items():
        deltas = []
        for i in range(len(variants)):
          baseline_wr = win_rates[("baseline", player_class, offset + i)]
          deltas.append(win_rates[(card, player_class, i)] - baseline_wr)
        offset += len(variants)
        if not deltas:
          continue
        rows.append({"class": player_class, "card": card, "mode": mode,
                     "mean_delta_wr": round(mean(deltas), 4),
                     "host_deltas": "|".join(f"{d:+.3f}" for d in deltas),
                     "games_per_side": len(deltas) * n_field * args.games})

  out_path = OUT_DIR / f"probe_{args.era}.csv"
  with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["class", "card", "mode", "mean_delta_wr", "host_deltas", "games_per_side"])
    writer.writeheader()
    writer.writerows(rows)
  print(f"\nwrote {out_path}\n")

  for player_class in CLASSES:
    class_rows = sorted((r for r in rows if r["class"] == player_class),
                        key=lambda r: -r["mean_delta_wr"])
    print(f"=== {player_class} ===")
    for r in class_rows:
      print(f"  {r['card']:24}{r['mean_delta_wr']:+.3f}")


if __name__ == "__main__":
  main()
