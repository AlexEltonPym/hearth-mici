"""S3 ground truth: real-world response to the Starving Buzzard nerf (22 Sept 2014).

Builds two monthly time series for 2014 from the Zenodo/HearthPwn deck archive:
  - class share among Mage/Hunter/Warrior decks (the same 3-class normalisation
    the simulator uses, so sim output is directly comparable)
  - Starving Buzzard adoption within Hunter decks (card-level response)

Data (gitignored, ~620MB): data/decks/zenodo_{decks,cards}.csv from
DOI 10.5281/zenodo.10198504. Card and archetype fields carry trailing spaces -
strip before comparing.

Caveat for interpretation: the 2014 ladder ran on Classic + Naxxramas, and Naxx
staples (Undertaker, Haunted Creeper, Sludge Belcher, Loatheb) are outside the
simulator's pool. The card-level Buzzard signal is therefore the cleaner target;
class share is confounded by cards the simulator cannot represent.
"""
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

csv.field_size_limit(10 ** 7)
HERE = Path(__file__).parent
DECKS = HERE / "data" / "decks" / "zenodo_decks.csv"
CARDS = HERE / "data" / "decks" / "zenodo_cards.csv"
OUT = HERE / "data" / "buzzard_nerf_series.csv"

#signature cards used to infer a deck's class (the archive's own archetype
#labels are "Unknown" for essentially all 2014 rows)
CLASS_CARDS = {
  "HUNTER": {"Kill Command", "Animal Companion", "Unleash the Hounds", "Houndmaster",
             "Starving Buzzard", "Eaglehorn Bow", "Explosive Trap", "Freezing Trap",
             "Savannah Highmane", "Hunter's Mark", "Scavenging Hyena", "Tracking",
             "Arcane Shot", "Bestial Wrath", "Flare", "Snake Trap", "Deadly Shot",
             "Multi-Shot", "Misdirection", "Timber Wolf"},
  "MAGE": {"Fireball", "Frostbolt", "Flamestrike", "Polymorph", "Arcane Intellect",
           "Frost Nova", "Blizzard", "Pyroblast", "Mirror Entity", "Counterspell",
           "Ice Block", "Ice Barrier", "Arcane Missiles", "Arcane Explosion",
           "Cone of Cold", "Mana Wyrm", "Sorcerer's Apprentice", "Archmage Antonidas",
           "Water Elemental", "Ethereal Arcanist"},
  "WARRIOR": {"Fiery War Axe", "Execute", "Shield Slam", "Brawl", "Gorehowl",
              "Cruel Taskmaster", "Armorsmith", "Frothing Berserker", "Whirlwind",
              "Grommash Hellscream", "Heroic Strike", "Shield Block", "Battle Rage",
              "Slam", "Arcanite Reaper", "Mortal Strike", "Inner Rage", "Rampage",
              "Commanding Shout", "Charge", "Upgrade!", "Warsong Commander"},
}
MIN_SIGNATURE_HITS = 2
MIN_DECKS_PER_MONTH = 20


def parse_date(value):
  for fmt in ("%d/%m/%Y", "%m/%d/%Y"):
    try:
      return datetime.strptime(value.strip(), fmt)
    except ValueError:
      continue
  return None


def load_2014_ranked_decks():
  decks = {}
  with DECKS.open(encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter=";"):
      date = parse_date(row["Date"])
      if date and date.year == 2014 and row["DeckType"].strip() == "Ranked Deck":
        decks[row["idDeck"]] = date
  return decks


def load_card_lists(deck_ids):
  cards = defaultdict(set)
  with CARDS.open(encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, delimiter=";")
    next(reader)
    for row in reader:
      if len(row) >= 2 and row[0] in deck_ids:
        cards[row[0]].add(row[1].strip())
  return cards


def infer_class(deck_cards):
  hits = {name: len(deck_cards & signature) for name, signature in CLASS_CARDS.items()}
  best = max(hits, key=hits.get)
  return best if hits[best] >= MIN_SIGNATURE_HITS else None


def main():
  decks = load_2014_ranked_decks()
  cards = load_card_lists(set(decks))
  print(f"{len(decks)} ranked 2014 decks, {len(cards)} with card lists")

  months = defaultdict(Counter)
  for deck_id, date in decks.items():
    deck_cards = cards.get(deck_id, set())
    player_class = infer_class(deck_cards)
    if not player_class:
      continue
    month = months[f"{date.year}-{date.month:02d}"]
    month[player_class] += 1
    if player_class == "HUNTER" and "Starving Buzzard" in deck_cards:
      month["buzzard"] += 1

  rows = []
  for month in sorted(months):
    counts = months[month]
    classified = counts["HUNTER"] + counts["MAGE"] + counts["WARRIOR"]
    if classified < MIN_DECKS_PER_MONTH:
      continue
    rows.append({
      "month": month,
      "classified_decks": classified,
      "hunter_share": counts["HUNTER"] / classified,
      "mage_share": counts["MAGE"] / classified,
      "warrior_share": counts["WARRIOR"] / classified,
      "buzzard_share_of_hunter": counts["buzzard"] / counts["HUNTER"] if counts["HUNTER"] else 0.0,
    })

  with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
  print(f"wrote {len(rows)} months to {OUT}\n")

  print(f"{'month':9}{'decks':>7}{'hunter':>9}{'mage':>8}{'warrior':>9}{'buzzard/hunter':>16}")
  for row in rows:
    marker = "  <- nerf" if row["month"] == "2014-09" else ""
    print(f"{row['month']:9}{row['classified_decks']:>7}{row['hunter_share']:>8.1%}"
          f"{row['mage_share']:>8.1%}{row['warrior_share']:>9.1%}"
          f"{row['buzzard_share_of_hunter']:>15.1%}{marker}")

  pre = [r for r in rows if r["month"] < "2014-09"]
  post = [r for r in rows if r["month"] > "2014-09"]
  pre_buzz = sum(r["buzzard_share_of_hunter"] for r in pre) / len(pre)
  post_buzz = sum(r["buzzard_share_of_hunter"] for r in post) / len(post)
  pre_hunter = sum(r["hunter_share"] for r in pre) / len(pre)
  post_hunter = sum(r["hunter_share"] for r in post) / len(post)
  print(f"\nbuzzard in hunter decks: {pre_buzz:.1%} before -> {post_buzz:.1%} after")
  print(f"hunter class share:      {pre_hunter:.1%} before -> {post_hunter:.1%} after")


if __name__ == "__main__":
  main()
