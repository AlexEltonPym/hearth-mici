"""build_pool card_patches hook (historical nerf simulation)."""
import sys
from copy import deepcopy

sys.path.append('../')
sys.path.append('../../')

from enums import CardSets
from card_sets import build_pool, SEPT_2014_NERF_PATCHES

SETS = [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER]


def by_name(pool, name):
  return next(card for card in pool if card.name == name)


def test_sept_2014_nerf_patches_apply():
  pool = build_pool(SETS, None, SEPT_2014_NERF_PATCHES)
  buzzard = by_name(pool, "Starving Buzzard")
  assert (buzzard.manacost, buzzard.attack, buzzard.health) == (5, 3, 2)
  leeroy = by_name(pool, "Leeroy Jenkins")
  assert leeroy.manacost == 5
  assert (leeroy.attack, leeroy.health) == (6, 2) #stats untouched by the patch


def test_unpatched_pool_is_not_poisoned_by_patched_build():
  #patched pools are cached under a different key and patch deepcopies - the
  #launch-state pool must stay pristine even after a patched build
  build_pool(SETS, None, SEPT_2014_NERF_PATCHES)
  pool = build_pool(SETS, None)
  buzzard = by_name(pool, "Starving Buzzard")
  assert (buzzard.manacost, buzzard.attack, buzzard.health) == (2, 2, 1)
  assert by_name(pool, "Leeroy Jenkins").manacost == 4


def test_patched_card_survives_reset():
  #original_* fields carry the patch, so Card.reset() between games in a
  #matchup keeps the nerfed values instead of reverting to launch state
  pool = build_pool(SETS, None, SEPT_2014_NERF_PATCHES)
  buzzard = deepcopy(by_name(pool, "Starving Buzzard"))
  buzzard.reset()
  assert (buzzard.manacost, buzzard.attack, buzzard.health) == (5, 3, 2)
