"""Card catalogue for the hearth-rs metagame pipelines: all nine classes,
the full 2014 pool, no dependency on the Python engine's card tables.

Sources (RULES.md authority order: Blizzard data wins):
  1. validation/data/hsjson_2014_cards.json - HearthstoneJSON collectible
     data, sets VANILLA (the 382-card 2014 Classic pool at launch values)
     and NAXX (30): name, cardClass, rarity, set, cost, type.
  2. hearth.card_names() - the engine's own card universe with its
     collectible flag. Used as a cross-check only: every catalogue card
     must be implemented and collectible in the engine, and the engine
     must not carry collectible cards the catalogue lacks. A mismatch is a
     hard error, never silently dropped.

Why: the v2 (three-class) campaign inherited its mutation pool, legendary
list, and class signatures from classic_sim's card_sets, so evolution could
only propose the ~245 cards the Python engine implemented although the
Rust engine plays all 412. This module is the single replacement.

Eras: "pre_naxx" = VANILLA only; "naxx" (Naxx launch and post-nerf alike -
patches change stats, never names) = VANILLA + NAXX.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / ".." / "validation" / "data" / "hsjson_2014_cards.json"

CLASSES = ["DRUID", "HUNTER", "MAGE", "PALADIN", "PRIEST", "ROGUE", "SHAMAN", "WARLOCK", "WARRIOR"]
ERAS = ("pre_naxx", "naxx")
VARIANT_RE = re.compile(r"^(.*) \((?:pre-)?\d{4}-\d{2}-\d{2}\)$")

_cards = None


def _load():
  global _cards
  if _cards is None:
    with DATA.open(encoding="utf-8") as f:
      _cards = {c["name"]: c for c in json.load(f)["cards"]}
    bad = {n: c["cardClass"] for n, c in _cards.items()
           if c["cardClass"] not in CLASSES + ["NEUTRAL"]}
    if bad:
      raise ValueError(f"unexpected classes in catalogue: {bad}")
  return _cards


def verify_against_engine(hearth_module):
  """Hard cross-check against the engine's universe. Call once per process
  before any pipeline run on the hearthrs backend. Engine names ending in
  a dated suffix, e.g. 'Starving Buzzard (2014-09-22)', are the engine's
  own patch variants of a base card and are selected by era, so they are
  accepted when their base name is in the catalogue. The engine lists
  same-named tokens (Mirror Image, Spellbender, ...) as uncollectible
  entries beside the collectible card, so collectibility is any-of."""
  cards = _load()
  engine_collectible, engine_all = set(), set()
  for name, collectible in hearth_module.card_names():
    engine_all.add(name)
    if collectible:
      engine_collectible.add(name)
  missing = sorted(n for n in cards if n not in engine_all)
  uncollectible = sorted(n for n in cards if n in engine_all and n not in engine_collectible)
  extra, bad_variant = [], []
  for n in sorted(engine_collectible - set(cards)):
    m = VARIANT_RE.match(n)
    if m and m.group(1) in cards:
      continue
    (bad_variant if m else extra).append(n)
  if missing or uncollectible or extra or bad_variant:
    raise RuntimeError("catalogue/engine mismatch: "
                       f"missing from engine={missing}, engine says uncollectible={uncollectible}, "
                       f"engine collectible but not in catalogue={extra}, "
                       f"variants of unknown base={bad_variant}")
  return len(cards)


def card(name):
  return _load()[name]


def is_naxx(name):
  return _load()[name]["set"] == "NAXX"


def class_cards(player_class, era="naxx"):
  """Class-exclusive cards (VANILLA class set + the class's Naxx card)."""
  return sorted(n for n, c in _load().items()
                if c["cardClass"] == player_class and (era == "naxx" or c["set"] != "NAXX"))


def neutral_cards(era="naxx"):
  return sorted(n for n, c in _load().items()
                if c["cardClass"] == "NEUTRAL" and (era == "naxx" or c["set"] != "NAXX"))


def legal_pool(player_class, era="naxx"):
  """Every card this class may run in the era: neutrals + its class cards."""
  if era not in ERAS:
    raise ValueError(f"era {era!r} not in {ERAS}")
  return neutral_cards(era) + class_cards(player_class, era)


def legal_pools(era="naxx"):
  return {c: legal_pool(c, era) for c in CLASSES}


def legendaries():
  return {n for n, c in _load().items() if c["rarity"] == "LEGENDARY"}


def max_copies(name):
  return 1 if _load()[name]["rarity"] == "LEGENDARY" else 2


def naxx_neutrals():
  return [n for n in neutral_cards("naxx") if is_naxx(n)]


def naxx_class_cards(player_class):
  return [n for n in class_cards(player_class, "naxx") if is_naxx(n)]


def class_signatures(era="naxx"):
  """class -> set of its class-exclusive cards, for inferring a real deck's
  class from its list (the archive carries no class column)."""
  return {c: set(class_cards(c, era)) for c in CLASSES}


if __name__ == "__main__":
  cards = _load()
  print(f"{len(cards)} cards; legendaries {len(legendaries())}; naxx neutrals {len(naxx_neutrals())}")
  for c in CLASSES:
    print(f"  {c:8s} class cards {len(class_cards(c)):3d} (naxx: {naxx_class_cards(c)})  pool {len(legal_pool(c))}")
  try:
    import hearthrs_backend
    print("engine cross-check ok:", verify_against_engine(hearthrs_backend._load_hearth()))
  except Exception as e:  # noqa: BLE001 - report, this is a diagnostic entry point
    print("engine cross-check FAILED:", e)
