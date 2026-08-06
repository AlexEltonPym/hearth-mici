"""S1 ground truth: real Classic decklists (Mage/Hunter/Warrior) from HSReplay.

Expands each deck's dbfId-based card list (data/hsreplay_classic/decks_winrate_20210504.json,
Wayback capture 2021-05-04) to full 30-card name lists via the HearthstoneJSON
dbfId->name mapping (cards.collectible.json), and checks each against the
simulator's implemented card pool (card_sets.py) to find which real decks are
now fully constructible - the gap this measured at 5/88 before the Aug 2026
legendaries pass (see readme.md's deck-representability note).

Output: data/hsreplay_classic/constructible_decklists.csv, one row per
constructible deck with its full card list ready for Deck.generate_from_decklist.
"""
import sys, json, csv
from pathlib import Path

sys.path.append('../../src')
from card_sets import (get_basic_cards, get_common_cards, get_rare_cards, get_epic_cards,
                        get_legendary_cards, get_hunter_cards, get_mage_cards, get_warrior_cards)

HERE = Path(__file__).parent
DECKS_JSON = HERE / "data" / "hsreplay_classic" / "decks_winrate_20210504.json"
CARDS_JSON = HERE / "data" / "hsreplay_classic" / "cards.collectible.json"
OUT = HERE / "data" / "hsreplay_classic" / "constructible_decklists.csv"

CLASSES = ["HUNTER", "MAGE", "WARRIOR"]


def implemented_card_names():
  cards = (get_basic_cards() + get_common_cards() + get_rare_cards() + get_epic_cards()
           + get_legendary_cards() + get_hunter_cards() + get_mage_cards() + get_warrior_cards())
  return {card.name for card in cards}


def load_dbf_to_name():
  with CARDS_JSON.open(encoding="utf-8") as f:
    cards = json.load(f)
  return {card["dbfId"]: card["name"] for card in cards}


def expand_decklist(deck_list_json, dbf_to_name):
  pairs = json.loads(deck_list_json)
  names = []
  for dbf_id, count in pairs:
    name = dbf_to_name.get(dbf_id)
    if name is None:
      return None #unknown dbfId (rotated out of the mapping) - treat as unconstructible
    names.extend([name] * count)
  return names


def main():
  with DECKS_JSON.open(encoding="utf-8") as f:
    data = json.load(f)
  dbf_to_name = load_dbf_to_name()
  implemented = implemented_card_names()

  rows = []
  total = 0
  missing_counts = {}
  for player_class in CLASSES:
    for deck in data["series"]["data"][player_class]:
      total += 1
      names = expand_decklist(deck["deck_list"], dbf_to_name)
      if names is None or len(names) != 30:
        continue
      missing = sorted({name for name in names if name not in implemented})
      if missing:
        for name in missing:
          missing_counts[name] = missing_counts.get(name, 0) + 1
        continue
      rows.append({
        "deck_id": deck["deck_id"],
        "class": player_class,
        "win_rate": deck["win_rate"],
        "total_games": deck["total_games"],
        "card_list": "|".join(names),
      })

  with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["deck_id", "class", "win_rate", "total_games", "card_list"])
    writer.writeheader()
    writer.writerows(rows)

  print(f"{len(rows)}/{total} real HSReplay Mage/Hunter/Warrior decks now fully constructible")
  print(f"wrote {len(rows)} decklists to {OUT}\n")

  print("missing cards blocking the remaining decks (deck count blocked, descending):")
  for name, count in sorted(missing_counts.items(), key=lambda item: -item[1]):
    print(f"  {count:>3}  {name}")


if __name__ == "__main__":
  main()
