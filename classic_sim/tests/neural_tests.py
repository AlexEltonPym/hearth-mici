"""Tests for neural_eval (feature encoder + numpy value net) and the
NeuralGreedy / MCTS-with-net strategy wiring."""
import sys
sys.path.append('../src/')

import numpy as np
from numpy.random import RandomState

from game_manager import GameManager
from enums import CardSets, Classes
from zones import Deck
from card_sets import build_pool, SEPT_2014_NERF_PATCHES
from strategy import NeuralGreedy, RandomAction, MCTS
from exceptions import TooManyActions
import neural_eval as ne

ALL_SETS = [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_MAGE,
            CardSets.CLASSIC_WARRIOR, CardSets.NAXX_NEUTRAL, CardSets.NAXX_HUNTER,
            CardSets.NAXX_MAGE, CardSets.NAXX_WARRIOR]

BASIC_MAGE = [
  "Arcane Missiles", "Arcane Missiles", "Murloc Raider", "Murloc Raider",
  "Arcane Explosion", "Arcane Explosion", "Bloodfen Raptor", "Bloodfen Raptor",
  "Novice Engineer", "Novice Engineer", "River Crocolisk", "River Crocolisk",
  "Arcane Intellect", "Arcane Intellect", "Raid Leader", "Raid Leader",
  "Wolfrider", "Wolfrider", "Fireball", "Fireball",
  "Oasis Snapjaw", "Oasis Snapjaw", "Polymorph", "Polymorph",
  "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", "Nightblade", "Nightblade",
  "Boulderfist Ogre", "Boulderfist Ogre"]


def full_pool():
  return build_pool(ALL_SETS, RandomState(0))


def test_every_card_encodes_with_correct_dim():
  features = {card.name: ne.card_static_features(card) for card in full_pool()}
  assert len(features) == 245
  assert all(vector.shape == (ne.STATIC_DIM,) for vector in features.values())
  assert all(np.isfinite(vector).all() for vector in features.values())


def test_no_two_cards_encode_identically():
  #ID-free encoding is only useful if it actually separates the pool; a
  #collision means the net literally cannot value those cards differently
  features = {card.name: ne.card_static_features(card) for card in full_pool()}
  by_bytes = {}
  for name, vector in features.items():
    by_bytes.setdefault(vector.tobytes(), []).append(name)
  collisions = [names for names in by_bytes.values() if len(names) > 1]
  assert collisions == []


def test_naxx_cards_encode_sensibly():
  features = {card.name: ne.card_static_features(card) for card in full_pool()}
  undertaker = features["Undertaker"]
  #1-mana 1/2 with an ongoing on-summon trigger and a dynamic filter
  assert undertaker[0] == np.float32(1 / 10.0)  #manacost
  assert undertaker[-1] == 1.0  #has_dynamic_filter (TriggererHasDeathrattle)
  #Death's Bite: weapon with a deathrattle
  deaths_bite = features["Death's Bite"]
  assert deaths_bite[3 + 2] == 1.0  #card_type one-hot: WEAPON is index 2


def test_nerf_patch_changes_encoding():
  plain = build_pool(ALL_SETS, RandomState(0))
  patched = build_pool(ALL_SETS, RandomState(0), card_patches=SEPT_2014_NERF_PATCHES)
  plain_buzzard = next(card for card in plain if card.name == "Starving Buzzard")
  patched_buzzard = next(card for card in patched if card.name == "Starving Buzzard")
  assert not np.array_equal(ne.card_static_features(plain_buzzard),
                            ne.card_static_features(patched_buzzard))


def test_forward_pass_bounded_and_deterministic():
  game = make_game(NeuralGreedy(ne.init_weights(0)), RandomAction())
  weights = ne.init_weights(1)
  value_a = ne.evaluate_state(weights, game)
  value_b = ne.evaluate_state(weights, game)
  assert value_a == value_b
  assert -1.0 <= value_a <= 1.0
  #perspective flip: my value and their value should differ in general
  other = ne.evaluate_state(weights, game, me=game.current_player.other_player)
  assert value_a != other


def make_game(player_strategy, enemy_strategy):
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), player_strategy)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), enemy_strategy)
  game_manager.create_game()
  return game_manager.game


def test_neural_greedy_plays_full_games():
  game = make_game(NeuralGreedy(ne.init_weights(0)), RandomAction())
  completed = 0
  for _ in range(3):
    try:
      result = game.play_game()
      assert result[0] in (0, 1)
      completed += 1
    except (TooManyActions, RecursionError):
      pass
    game.reset_game()
    game.start_game()
  assert completed >= 2


def test_mcts_accepts_net_weights_as_leaf_eval():
  weights = ne.init_weights(0)
  game = make_game(MCTS(iterations=10, guided=True, eval_weights=weights), RandomAction())
  #a few turns is enough to exercise expand/rollout/state_value with the net
  for _ in range(6):
    turn_passed = game.current_player.strategy.choose_action(game)
    if turn_passed:
      game.end_turn()
      game.untap()
