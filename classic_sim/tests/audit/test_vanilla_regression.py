"""Whole-pool VANILLA regression sweep (audit follow-up).

Walks every collectable card in the classic pool and asserts its manacost /
attack / health against the VANILLA rows of cards.collectible.json - the
2014-era (and 2021 Classic format) card database the validation studies
compare against. This is the guard the full-pool audit recommended: single
data-entry drift (e.g. a post-2014 nerf value leaking in, as happened with
Abusive Sergeant) fails loudly here instead of silently skewing experiments.

Races/creature types are deliberately NOT swept: the modern card DB carries
retro-tagged races (e.g. UNDEAD, added 2022) that did not exist in 2014.
"""
import sys, json
from pathlib import Path

sys.path.append('../')
sys.path.append('../../')

import pytest

from enums import CardSets, CardTypes
from card_sets import build_pool

CARDS_JSON = Path(__file__).parent.parent.parent / "examples" / "validation" / "data" / "hsreplay_classic" / "cards.collectible.json"


def vanilla_rows():
  with CARDS_JSON.open(encoding="utf-8") as f:
    cards = json.load(f)
  return {c["name"]: c for c in cards if c.get("set") == "VANILLA"}


def pool_cards():
  pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER,
                     CardSets.CLASSIC_MAGE, CardSets.CLASSIC_WARRIOR], None)
  return [card for card in pool if card.collectable]


VANILLA = vanilla_rows()
POOL = pool_cards()


@pytest.mark.parametrize("card", POOL, ids=lambda c: c.name)
def test_card_matches_vanilla(card):
  row = VANILLA.get(card.name)
  assert row is not None, f"{card.name} has no VANILLA entry in cards.collectible.json"
  assert card.manacost == row["cost"], f"{card.name} cost: engine {card.manacost}, VANILLA {row['cost']}"
  if card.card_type in (CardTypes.MINION, CardTypes.WEAPON):
    assert card.attack == row.get("attack"), f"{card.name} attack: engine {card.attack}, VANILLA {row.get('attack')}"
    #for weapons the JSON stores durability in 'durability'; minions use 'health'
    real_health = row.get("health", row.get("durability"))
    assert card.health == real_health, f"{card.name} health: engine {card.health}, VANILLA {real_health}"
