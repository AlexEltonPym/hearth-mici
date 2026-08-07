"""S3 ground truth: card-level adoption across the two 2014 metagame shocks.

Builds, from the Zenodo/HearthPwn archive (data/decks/, gitignored), the real
per-class card-inclusion shares for three windows:
  pre_naxx      2014-01-01 .. 2014-07-21  (Basic+Classic ladder only)
  naxx_prenerf  2014-07-22 .. 2014-09-21  (Naxxramas live, pre-nerf)
  post_nerf     2014-09-22 .. 2014-12-07  (Buzzard/Leeroy nerf live, pre-GvG)

These are the prediction targets for the metagame-shift experiments: given
only the decks of one window (plus the pool/patch change), predict the next
window's adoption. Also extracts SEED decklists per window - real ranked
decks that are exactly 30 cards and fully constructible in the simulator's
era pool (class cards + neutrals + Naxx where the window allows) - which the
evolution pipeline uses as its starting population.

Outputs:
  data/naxx_adoption_{window}.csv   card, per-class inclusion share (+ counts)
  data/naxx_seeds_{window}.json     constructible 30-card decklists per class
  data/naxx_adoption_summary.json   deck counts and constructibility rates

Usage (from classic_sim/examples/validation):
  python naxx_adoption_series.py
"""
import sys, csv, json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.append('../../src')

from buzzard_nerf_series import CLASS_CARDS, MIN_SIGNATURE_HITS, parse_date
from hearthpwn_2014_dynamics import legal_pools
from card_sets import get_legendary_cards

csv.field_size_limit(10 ** 7)
HERE = Path(__file__).parent
DECKS = HERE / "data" / "decks" / "zenodo_decks.csv"
CARDS = HERE / "data" / "decks" / "zenodo_cards.csv"
OUT_DIR = HERE / "data"

CLASSES = ["HUNTER", "MAGE", "WARRIOR"]
WINDOWS = {
  "pre_naxx": (datetime(2014, 1, 1), datetime(2014, 7, 22)),
  "naxx_prenerf": (datetime(2014, 7, 22), datetime(2014, 9, 22)),
  "post_nerf": (datetime(2014, 9, 22), datetime(2014, 12, 8)),
}

#HearthPwn's Date is the deck's CREATION date, but the card list (and the Set
#tag) reflect the LAST EDIT - a deck created in June and updated in August
#carries Naxx cards under a pre-Naxx date (measured: 3,725 'Naxx Launch'-
#tagged decks inside the pre-Naxx date window, Webspinner at a nonsense 24.7%
#pre-Naxx adoption). Each window therefore also requires the Set tag to
#belong to the window's patch era. Residual limitation: the Sept 22 nerf got
#no tag of its own (post-nerf edits still show 'Naxx Launch'), so
#naxx_prenerf can still contain post-nerf edits - undetectable, but the
#Buzzard rate there (67.8%, matching pre-Naxx) suggests it is minor.
SET_ALLOWLIST = {
  "pre_naxx": {"Beta Patch 4243", "Beta Patch 4458", "Beta Patch 4482", "Beta Patch 4944",
               "Live Patch 4973", "Live Patch 5170", "Live Patch 5314"},
  "naxx_prenerf": {"Naxx Launch", "Live Patch 5435", "Live Patch 5506"},
  "post_nerf": {"Naxx Launch", "Live Patch 5435", "Live Patch 5506"},
}

#the simulator's Naxxramas set (engine implementation in card_sets.get_naxx_*;
#names hardcoded here so this data script has no dependency on that landing)
NAXX_NEUTRALS = ["Zombie Chow", "Undertaker", "Echoing Ooze", "Haunted Creeper", "Mad Scientist",
                 "Nerub'ar Weblord", "Nerubian Egg", "Unstable Ghoul", "Dancing Swords", "Deathlord",
                 "Shade of Naxxramas", "Stoneskin Gargoyle", "Baron Rivendare", "Wailing Soul",
                 "Feugen", "Stalagg", "Loatheb", "Sludge Belcher", "Spectral Knight", "Maexxna",
                 "Kel'Thuzad"]
NAXX_CLASS = {"HUNTER": ["Webspinner"], "MAGE": ["Duplicate"], "WARRIOR": ["Death's Bite"]}
NAXX_LEGENDARIES = {"Baron Rivendare", "Feugen", "Stalagg", "Loatheb", "Maexxna", "Kel'Thuzad"}


def era_pools(window):
  """Class -> set of legal card names for the window's era."""
  pools = {player_class: set(pool) for player_class, pool in legal_pools().items()}
  if window != "pre_naxx":
    for player_class in CLASSES:
      pools[player_class] |= set(NAXX_NEUTRALS) | set(NAXX_CLASS[player_class])
  return pools


def legendary_names():
  return {card.name for card in get_legendary_cards()} | NAXX_LEGENDARIES


def load_ranked_decks():
  """deck_id -> window label for every 2014 ranked deck whose date AND Set
  tag both belong to the same window's era (see SET_ALLOWLIST)."""
  decks = {}
  with DECKS.open(encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter=";"):
      if row["DeckType"].strip() != "Ranked Deck":
        continue
      date = parse_date(row["Date"])
      if not date:
        continue
      for window, (start, end) in WINDOWS.items():
        if start <= date < end and row["Set"].strip() in SET_ALLOWLIST[window]:
          decks[row["idDeck"]] = window
          break
  return decks


def load_card_counts(deck_ids):
  counts = defaultdict(Counter)
  with CARDS.open(encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, delimiter=";")
    next(reader)
    for row in reader:
      if len(row) >= 2 and row[0] in deck_ids:
        counts[row[0]][row[1].strip()] += 1
  return counts


def infer_class(deck_cards):
  hits = {name: len(set(deck_cards) & signature) for name, signature in CLASS_CARDS.items()}
  best = max(hits, key=hits.get)
  return best if hits[best] >= MIN_SIGNATURE_HITS else None


def constructible(deck_counts, pool, legendaries):
  if sum(deck_counts.values()) != 30:
    return False
  for card, copies in deck_counts.items():
    if card not in pool or copies > (1 if card in legendaries else 2):
      return False
  return True


def main():
  decks = load_ranked_decks()
  cards = load_card_counts(set(decks))
  legendaries = legendary_names()
  print(f"{len(decks)} ranked 2014 decks across {len(WINDOWS)} windows")

  #per window per class: inclusion counter + deck count + constructible seeds
  inclusion = {w: {c: Counter() for c in CLASSES} for w in WINDOWS}
  n_decks = {w: Counter() for w in WINDOWS}
  seeds = {w: {c: [] for c in CLASSES} for w in WINDOWS}
  pools_by_window = {w: era_pools(w) for w in WINDOWS}

  naxx_names = set(NAXX_NEUTRALS) | {c for cs in NAXX_CLASS.values() for c in cs}
  for deck_id, window in decks.items():
    deck_counts = cards.get(deck_id)
    if not deck_counts:
      continue
    #belt and braces on top of the Set filter: a pre-Naxx deck containing any
    #Naxx card is a later edit leaking through - drop it
    if window == "pre_naxx" and naxx_names & set(deck_counts):
      continue
    player_class = infer_class(deck_counts)
    if not player_class:
      continue
    n_decks[window][player_class] += 1
    for card in deck_counts:
      inclusion[window][player_class][card] += 1
    if constructible(deck_counts, pools_by_window[window][player_class], legendaries):
      decklist = sorted([card for card, copies in deck_counts.items() for _ in range(copies)])
      seeds[window][player_class].append(decklist)

  summary = {}
  for window in WINDOWS:
    all_cards = sorted(set().union(*(inclusion[window][c] for c in CLASSES)))
    out_path = OUT_DIR / f"naxx_adoption_{window}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
      writer = csv.writer(f)
      writer.writerow(["card"] + [f"{c.lower()}_share" for c in CLASSES] + [f"{c.lower()}_decks" for c in CLASSES])
      for card in all_cards:
        writer.writerow([card]
                        + [round(inclusion[window][c][card] / n_decks[window][c], 4) if n_decks[window][c] else 0.0 for c in CLASSES]
                        + [inclusion[window][c][card] for c in CLASSES])
    seeds_path = OUT_DIR / f"naxx_seeds_{window}.json"
    with seeds_path.open("w", encoding="utf-8") as f:
      json.dump(seeds[window], f)
    summary[window] = {
      "decks": {c: n_decks[window][c] for c in CLASSES},
      "constructible_seeds": {c: len(seeds[window][c]) for c in CLASSES},
    }
    print(f"[{window}] decks {dict(n_decks[window])} | seeds "
          f"{ {c: len(seeds[window][c]) for c in CLASSES} } | wrote {out_path.name}, {seeds_path.name}")

  with (OUT_DIR / "naxx_adoption_summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
  print("wrote naxx_adoption_summary.json")


if __name__ == "__main__":
  main()
