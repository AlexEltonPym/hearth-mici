"""Invariants for the 2-of-favouring mutation operator (evolve_metagame_shift
.mutate_deck with pair_bias). Run directly:

  python test_mutation_pairing.py

Checks, over many mutated real seed decks under bias + rarity + collection
combinations:
  - decks stay exactly 30 cards
  - no card exceeds its copy cap (2, or 1 for legendaries)
  - legendaries are NEVER duplicated
  - pair_bias > 1 lowers the mean distinct-card count vs pair_bias == 1
    (i.e. it actually builds 2-ofs), toward the real ~18
"""
import sys, json, random
from collections import Counter
from statistics import mean

sys.path.append('../../src')
sys.path.append('../map_elites')
import evolve_metagame_shift as e

SEEDS = json.load(open('../validation/data/naxx_seeds_naxx_prenerf.json'))


def _mutate_many(pair_bias, generations=40, per_class=40, rarity=False, collection=False):
  random.seed(7)
  decks = []
  for cls in ['HUNTER', 'MAGE', 'WARRIOR']:
    pool = e.era_class_pool(cls)
    rarw = {c: (0.3 if c in e.LEGENDARY_NAMES else 1.0) for c in pool} if rarity else None
    owned = set(pool) if collection else None
    for d0 in SEEDS[cls][:per_class]:
      d = list(d0)
      for _ in range(generations):
        d = e.mutate_deck(d, pool, owned=owned, rarity_weights=rarw, pair_bias=pair_bias)
      decks.append(d)
  return decks


def test_structural_invariants():
  for rarity, collection in [(False, False), (True, False), (True, True)]:
    for d in _mutate_many(4.0, rarity=rarity, collection=collection):
      assert len(d) == 30, f"deck size {len(d)} != 30"
      counts = Counter(d)
      for card, n in counts.items():
        assert n <= e.max_copies(card), f"{card} has {n} copies (cap {e.max_copies(card)})"
        assert not (card in e.LEGENDARY_NAMES and n > 1), f"legendary {card} duplicated"


def test_pair_bias_builds_twoofs():
  base = mean(len(set(d)) for d in _mutate_many(1.0))
  paired = mean(len(set(d)) for d in _mutate_many(4.0))
  real = mean(len(set(d)) for cls in SEEDS for d in SEEDS[cls])
  assert paired < base, f"pair_bias did not reduce distinct count ({paired:.1f} vs {base:.1f})"
  assert paired < base - 2, f"pair_bias effect too small ({base:.1f} -> {paired:.1f})"
  print(f"distinct cards: real={real:.1f}  pair_bias=1 -> {base:.1f}  pair_bias=4 -> {paired:.1f}")


if __name__ == "__main__":
  test_structural_invariants()
  test_pair_bias_builds_twoofs()
  print("all mutation-pairing invariants hold")
