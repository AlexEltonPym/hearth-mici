"""Tests for src/determinize.py (opponent-hand determinization)."""
import sys
sys.path.append('../src/')

import numpy as np
from numpy.random import RandomState

from game_manager import GameManager
from enums import CardSets, Classes
from zones import Deck
from strategy import GreedyActionSmart, RandomAction
from utilities import fast_clone
from determinize import determinize_opponent_hand, sample_class_prior_hand

BASIC_MAGE = [
  "Arcane Missiles", "Arcane Missiles", "Murloc Raider", "Murloc Raider",
  "Arcane Explosion", "Arcane Explosion", "Bloodfen Raptor", "Bloodfen Raptor",
  "Novice Engineer", "Novice Engineer", "River Crocolisk", "River Crocolisk",
  "Arcane Intellect", "Arcane Intellect", "Raid Leader", "Raid Leader",
  "Wolfrider", "Wolfrider", "Fireball", "Fireball",
  "Oasis Snapjaw", "Oasis Snapjaw", "Polymorph", "Polymorph",
  "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", "Nightblade", "Nightblade",
  "Boulderfist Ogre", "Boulderfist Ogre"]


def make_game():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), GreedyActionSmart())
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), RandomAction())
  game_manager.create_game()
  return game_manager.game


def opponent_of(game):
  return game.current_player.other_player


def hand_names(player):
  return sorted(card.name for card in player.hand.get_all() if card.collectable)


def test_decklist_mode_preserves_hand_size_and_card_multiset():
  game = make_game()
  opponent = opponent_of(game)
  clone = fast_clone(game)
  clone_opponent = clone.current_player.other_player

  before_hand_size = len([c for c in clone_opponent.hand.get_all() if c.collectable])
  before_pool = sorted(c.name for c in clone_opponent.hand.get_all() if c.collectable) + \
                sorted(c.name for c in clone_opponent.deck.get_all())

  determinize_opponent_hand(clone_opponent, RandomState(7))

  after_hand = [c for c in clone_opponent.hand.get_all() if c.collectable]
  assert len(after_hand) == before_hand_size
  after_pool = sorted(c.name for c in clone_opponent.hand.get_all() if c.collectable) + \
               sorted(c.name for c in clone_opponent.deck.get_all())
  #the combined hand+deck multiset is conserved - nothing invented or lost
  assert sorted(before_pool) == sorted(after_pool)
  #every dealt card belongs to the decklist
  assert all(c.name in BASIC_MAGE for c in after_hand)
  #parents are consistent
  assert all(c.parent is clone_opponent.hand for c in clone_opponent.hand.get_all())
  assert all(c.parent is clone_opponent.deck for c in clone_opponent.deck.get_all())


def test_decklist_mode_leaves_real_state_untouched():
  game = make_game()
  opponent = opponent_of(game)
  before_hand = hand_names(opponent)
  before_deck = [c.name for c in opponent.deck.get_all()]
  rng_before = game.game_manager.random_state.get_state()

  clone = fast_clone(game)
  determinize_opponent_hand(clone.current_player.other_player, RandomState(3))

  assert hand_names(opponent) == before_hand
  assert [c.name for c in opponent.deck.get_all()] == before_deck
  rng_after = game.game_manager.random_state.get_state()
  assert rng_before[0] == rng_after[0] and np.array_equal(rng_before[1], rng_after[1]) \
         and rng_before[2:] == rng_after[2:]


def test_decklist_mode_deterministic_under_fixed_rng():
  game = make_game()
  clone_a = fast_clone(game)
  clone_b = fast_clone(game)
  determinize_opponent_hand(clone_a.current_player.other_player, RandomState(11))
  determinize_opponent_hand(clone_b.current_player.other_player, RandomState(11))
  assert hand_names(clone_a.current_player.other_player) == hand_names(clone_b.current_player.other_player)
  assert [c.name for c in clone_a.current_player.other_player.deck.get_all()] == \
         [c.name for c in clone_b.current_player.other_player.deck.get_all()]


def test_decklist_mode_actually_varies_across_samples():
  #hidden-information sanity: across enough samples the dealt hand should
  #not always equal the true hand (else we'd still be cheating)
  game = make_game()
  true_hand = hand_names(opponent_of(game))
  differing = 0
  for seed in range(10):
    clone = fast_clone(game)
    determinize_opponent_hand(clone.current_player.other_player, RandomState(seed))
    if hand_names(clone.current_player.other_player) != true_hand:
      differing += 1
  assert differing >= 5


def test_class_prior_mode_respects_caps_and_hand_size():
  game = make_game()
  clone = fast_clone(game)
  clone_opponent = clone.current_player.other_player
  before_size = len([c for c in clone_opponent.hand.get_all() if c.collectable])

  priors = {"Fireball": 0.9, "Polymorph": 0.9, "Boulderfist Ogre": 0.8}
  sample_class_prior_hand(clone_opponent, RandomState(5), priors)

  after_hand = [c for c in clone_opponent.hand.get_all() if c.collectable]
  assert len(after_hand) == before_size
  names = [c.name for c in after_hand]
  #2-copy cap (counting publicly played cards too - none this early)
  assert all(names.count(n) <= 2 for n in set(names))
  #fresh cards are correctly owned and parented
  assert all(c.owner is clone_opponent for c in after_hand)
  assert all(c.parent is clone_opponent.hand for c in after_hand)


def test_class_prior_mode_leaves_deck_untouched():
  game = make_game()
  clone = fast_clone(game)
  clone_opponent = clone.current_player.other_player
  before_deck = [c.name for c in clone_opponent.deck.get_all()]
  sample_class_prior_hand(clone_opponent, RandomState(5), {"Fireball": 0.9})
  assert [c.name for c in clone_opponent.deck.get_all()] == before_deck


def test_determinized_clone_plays_a_legal_full_turn():
  game = make_game()
  clone = fast_clone(game)
  #advance the clone to the opponent's turn the way a reply sim would
  clone.end_turn()
  clone.untap()
  replier = clone.current_player
  determinize_opponent_hand(replier, RandomState(2))
  #play the whole reply turn with greedy - must not crash or go illegal
  saved = clone.game_manager.random_state.get_state()
  agent = GreedyActionSmart()
  for _ in range(30):
    try:
      if agent.choose_action(clone):
        break
    except Exception as e:
      from exceptions import PlayerDead
      if isinstance(e, PlayerDead):
        break
      raise
  clone.game_manager.random_state.set_state(saved)
