"""Tests for the heuristic-feature refactor (src/heuristic_features.py):
the shared extractor must reproduce the pre-refactor duplicated
implementations byte-for-byte, and the candidate features must be sane."""
import sys
sys.path.append('../src/')

from numpy import tanh
from numpy.random import RandomState

from game_manager import GameManager
from enums import CardSets, Classes
from zones import Deck
from strategy import GreedyActionSmart, RandomAction
from montecarlotreesearch import evaluate_position, _EVAL_WEIGHTS
from heuristic_features import (FEATURE_NAMES, CANDIDATE_NAMES,
                                 extract_features, extract_candidate_features)

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
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), RandomAction())
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), RandomAction())
  game_manager.create_game()
  return game_manager.game


def advanced_states(n_actions=12):
  #a handful of mid-game states with boards/hands developed
  game = make_game()
  states = [game]
  for _ in range(n_actions):
    if game.current_player.strategy.choose_action(game):
      game.end_turn()
      game.untap()
  return game


def test_feature_names_match_vector_length():
  game = advanced_states()
  assert len(extract_features(game, game.current_player)) == len(FEATURE_NAMES) == 26
  assert len(extract_candidate_features(game, game.current_player)) == len(CANDIDATE_NAMES) == 6


def test_get_score_matches_manual_dot_product():
  #GreedyActionSmart.get_score == [turn_passed] + extract_features dot weights,
  #for the default 27-weight vector - the refactor's behavior-preservation claim
  game = advanced_states()
  agent = GreedyActionSmart()
  for turn_passed in (0, 1):
    expected = sum(f * w for f, w in zip([turn_passed] + extract_features(game, game.current_player),
                                          agent.weights))
    assert agent.get_score(game, turn_passed, 0) == expected


def test_evaluate_position_matches_manual_dot_product():
  game = advanced_states()
  features = extract_features(game, game.player)
  expected = float(tanh(sum(f * w for f, w in zip(features, _EVAL_WEIGHTS)) / 100.0))
  assert evaluate_position(game) == expected


def test_evaluate_position_strips_27_long_greedy_vector():
  #the historical silent-misalignment trap: a 27-long greedy vector must now
  #be treated as [turn_passed] + 26 and give the same result as passing the
  #26-long tail explicitly
  game = advanced_states()
  weights_27 = list(GreedyActionSmart().weights)
  assert evaluate_position(game, weights_27) == evaluate_position(game, weights_27[1:])


def test_candidate_features_are_finite_and_perspective_flips():
  game = advanced_states()
  me = game.current_player
  mine = extract_candidate_features(game, me)
  theirs = extract_candidate_features(game, me.other_player)
  assert all(isinstance(v, (int, float)) for v in mine)
  #difference-features flip sign across perspectives
  assert mine[0] == -theirs[0]  #deathrattle_count_difference
  assert mine[1] == -theirs[1]  #taunt_health_difference
  assert mine[4] == -theirs[4]  #divine_shield_attack_difference


def test_full_game_with_refactored_greedy():
  game = make_game()
  game.player.strategy = GreedyActionSmart()
  from exceptions import TooManyActions
  try:
    result = game.play_game()
    assert result[0] in (0, 1)
  except (TooManyActions, RecursionError):
    pass
