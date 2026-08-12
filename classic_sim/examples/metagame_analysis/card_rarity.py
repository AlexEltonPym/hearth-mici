"""Card name -> rarity, derived from card_sets.py (which carries no rarity
field on the Card object).

Three sources, in order of directness:
  1. NEUTRALS - card_sets.py has one getter per rarity
     (get_basic_cards / get_common_cards / get_rare_cards / get_epic_cards /
     get_legendary_cards), so neutral rarity is exact.
  2. CLASS CARDS - get_hunter_cards / get_mage_cards / get_warrior_cards mix
     rarities but are written in rarity-labelled sections ("#Hunter rare
     cards", ...). The section comments are parsed out of the getter source
     and every quoted name inside a section is intersected with the names the
     getter actually returns, so embedded token cards (Huffer, Whelp, Slime,
     ...) - which are never pool cards - drop out automatically.
  3. NAXXRAMAS - the Naxx getters are grouped by mana cost, not rarity.
     Naxx cards are adventure rewards: they cannot be crafted or disenchanted,
     so a dust prior does not literally apply and the whole set arrives
     together with the wing purchase. We therefore treat every non-legendary
     Naxx card as a common (uniform availability once the wing is bought) and
     the seven wing bosses as legendaries. This is a stated simplification,
     not a claim about the printed rarity gem.

Nothing here mutates card_sets; it only reads it.
"""
import inspect
import re

import card_sets

RARITIES = ("BASIC", "COMMON", "RARE", "EPIC", "LEGENDARY")

#approximate 2014 crafting cost of a non-golden card, in arcane dust
DUST_COST = {"BASIC": 0, "COMMON": 40, "RARE": 100, "EPIC": 400, "LEGENDARY": 1600}

#the seven Curse of Naxxramas boss legendaries. NOTE: evolve_metagame_shift's
#NAXX_LEGENDARY_NAMES omits Thaddius, so max_copies() currently lets a deck run
#two Thaddius; that is a pre-existing bug reported separately, and this map
#deliberately records the true rarity.
NAXX_LEGENDARIES = {"Maexxna", "Loatheb", "Baron Rivendare", "Thaddius",
                    "Feugen", "Stalagg", "Kel'Thuzad"}

_NEUTRAL_GETTERS = {
  "BASIC": card_sets.get_basic_cards,
  "COMMON": card_sets.get_common_cards,
  "RARE": card_sets.get_rare_cards,
  "EPIC": card_sets.get_epic_cards,
  "LEGENDARY": card_sets.get_legendary_cards,
}
_CLASS_GETTERS = (card_sets.get_hunter_cards, card_sets.get_mage_cards, card_sets.get_warrior_cards)
_NAXX_GETTERS = (card_sets.get_naxx_neutral_cards, card_sets.get_naxx_hunter_cards,
                 card_sets.get_naxx_mage_cards, card_sets.get_naxx_warrior_cards)

_SECTION_RE = re.compile(r"^\s*#\s*\w+\s+(basic|common|rare|epic|legendar)", re.IGNORECASE)
_NAME_RE = re.compile(r'name="([^"]+)"')


def _class_card_rarities(getter):
  """Split a class getter's source at its rarity-section comments and assign
  each returned card the rarity of the section its definition sits in."""
  returned = {card.name for card in getter()}
  rarities, section = {}, None
  for line in inspect.getsource(getter).splitlines():
    header = _SECTION_RE.match(line)
    if header:
      word = header.group(1).upper()
      section = "LEGENDARY" if word == "LEGENDAR" else word
      continue
    if section is None:
      continue
    for name in _NAME_RE.findall(line):
      if name in returned and name not in rarities:
        rarities[name] = section
  missing = returned - set(rarities)
  if missing:
    raise RuntimeError(f"{getter.__name__}: no rarity section for {sorted(missing)}")
  return rarities


def build_rarity_map():
  rarity = {}
  for name, getter in _NEUTRAL_GETTERS.items():
    for card in getter():
      rarity.setdefault(card.name, name)
  for getter in _CLASS_GETTERS:
    for card_name, card_rarity in _class_card_rarities(getter).items():
      rarity.setdefault(card_name, card_rarity)
  for getter in _NAXX_GETTERS:
    for card in getter():
      rarity.setdefault(card.name, "LEGENDARY" if card.name in NAXX_LEGENDARIES else "COMMON")
  return rarity


RARITY_BY_NAME = build_rarity_map()

#Curse of Naxxramas cards are ADVENTURE rewards: they cannot be crafted or
#disenchanted, so the dust prior does not apply to them. The whole set arrives
#with the wing purchases, which is an all-or-nothing per-player event rather
#than a per-card one - modelled separately in sample_collections().
NAXX_NAMES = {card.name for getter in _NAXX_GETTERS for card in getter()}


def ownership_prior(exponent=0.25, strength=1.0):
  """Probability that an arbitrary 2014 ladder deckbuilder has a given card
  available, by rarity.

  Base form: p = (40 / dust_cost) ** exponent - i.e. proposal/ownership odds
  fall with crafting cost, softened by the exponent because owning ONE copy of
  a card is far more likely than the raw cost ratio suggests (packs, arena
  rewards, and the fact that a player who wants a specific legendary saves for
  it). exponent=1 is the literal inverse-dust weighting (legendary = 2.5% of a
  common), exponent=0.25 is the default and gives

      basic/common 1.00 | rare 0.80 | epic 0.56 | legendary 0.40

  which brackets the real 2014 numbers: the most-played legendaries in the
  ground-truth window run 45-60% adoption (Grommash 60.5% of Warriors,
  Ragnaros 44.9%) while commons run up to ~85%.

  strength in [0, 1] blends the prior back toward "everyone owns everything"
  (strength=0 disables the constraint entirely).
  """
  prior = {}
  for name in RARITIES:
    dust = DUST_COST[name]
    base = 1.0 if dust <= DUST_COST["COMMON"] else (DUST_COST["COMMON"] / dust) ** exponent
    prior[name] = 1.0 - strength * (1.0 - base)
  return prior


def card_weights(pool, exponent=0.25, strength=1.0):
  """{card name: proposal weight} over a pool, from the same prior."""
  prior = ownership_prior(exponent, strength)
  return {name: prior[RARITY_BY_NAME.get(name, "COMMON")] for name in pool}


if __name__ == "__main__":
  from collections import Counter
  from enums import CardSets
  sets = [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_HUNTER,
          CardSets.CLASSIC_MAGE, CardSets.CLASSIC_WARRIOR, CardSets.NAXX_HUNTER,
          CardSets.NAXX_MAGE, CardSets.NAXX_WARRIOR]
  pool = [card.name for card in card_sets.build_pool(sets, None)]
  uncovered = [name for name in pool if name not in RARITY_BY_NAME]
  print(f"pool={len(pool)} cards, uncovered={uncovered}")
  print(Counter(RARITY_BY_NAME[name] for name in pool if name in RARITY_BY_NAME))
  print("prior:", {k: round(v, 3) for k, v in ownership_prior().items()})
  for name in sorted(pool):
    print(f"  {name:28} {RARITY_BY_NAME.get(name, '???')}")
