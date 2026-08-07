import sys

# appending the parent directory path
sys.path.append('../')
sys.path.append('../../')

import pytest

from card import Card
from zones import Deck
from player import Player
from game import Game
from exceptions import PlayerDead
from enums import *
from card_sets import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
from action import Action

from game_manager import GameManager

# Mechanics audit: hero powers (Steady Shot / Fireblast / Armor Up!)
# Ground truth: 2014 Hearthstone - every basic hero power costs 2 mana and may
# be used once per turn.


def make_game(player_class, enemy_class):
  #create_test_game is hardcoded to WARRIOR vs HUNTER, so build a game directly
  #whenever the mage's Fireblast is the hero power under test
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.TEST_CARDS])
  game_manager.create_player(player_class, Deck.generate_random, GreedyAction())
  game_manager.create_enemy(enemy_class, Deck.generate_random, GreedyAction())
  game = game_manager.create_game()
  game.player.hand.clear()
  game.enemy.hand.clear()
  game.player.current_mana = 10
  game.enemy.current_mana = 10
  game.current_player = game.player
  return game


def hero_power_actions(game, player):
  return [action for action in game.get_available_actions(player) if action.action_type == Actions.CAST_HERO_POWER]


# --- costs -------------------------------------------------------------------

def test_every_hero_power_costs_two_mana():
  for hero_class in [Classes.HUNTER, Classes.MAGE, Classes.WARRIOR]:
    assert get_hero_power(hero_class).manacost == 2

def test_hero_power_deducts_two_mana():
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  game.player.current_mana = 7
  game.perform_action(hero_power_actions(game, game.player)[0])
  assert game.player.current_mana == 5

def test_hero_power_not_offered_below_two_mana():
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  game.player.current_mana = 1
  assert len(hero_power_actions(game, game.player)) == 0
  game.player.current_mana = 2
  assert len(hero_power_actions(game, game.player)) == 1


# --- once per turn -----------------------------------------------------------

def test_hero_power_only_once_per_turn():
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  game.perform_action(hero_power_actions(game, game.player)[0])
  assert game.player.used_hero_power
  assert len(hero_power_actions(game, game.player)) == 0

def test_hero_power_available_again_after_untap():
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  game.perform_action(hero_power_actions(game, game.player)[0])
  game.end_turn() #hands the turn to the enemy
  game.end_turn() #and back
  game.player.max_mana = 9 #untap refills to max_mana, which is still 1 in a fresh game
  game.untap()
  assert not game.player.used_hero_power
  assert len(hero_power_actions(game, game.player)) == 1


# --- Steady Shot (hunter) ----------------------------------------------------

def test_steady_shot_deals_two_to_the_enemy_hero():
  game = make_game(Classes.HUNTER, Classes.WARRIOR)
  game.perform_action(hero_power_actions(game, game.player)[0])
  assert game.enemy.health == 28
  assert game.player.health == 30

def test_steady_shot_can_only_target_the_enemy_hero():
  game = make_game(Classes.HUNTER, Classes.WARRIOR)
  game.game_manager.get_card('Chillwind Yeti', game.enemy.board)
  game.game_manager.get_card('Chillwind Yeti', game.player.board)
  actions = hero_power_actions(game, game.player)
  assert len(actions) == 1
  assert actions[0].targets == [game.enemy]

def test_steady_shot_ignores_enemy_taunt():
  #hero power damage is not an attack, so Taunt never redirects it
  game = make_game(Classes.HUNTER, Classes.WARRIOR)
  game.game_manager.get_card('Goldshire Footman', game.enemy.board)
  game.perform_action(hero_power_actions(game, game.player)[0])
  assert game.enemy.health == 28

def test_steady_shot_is_not_boosted_by_spell_damage():
  game = make_game(Classes.HUNTER, Classes.WARRIOR)
  game.game_manager.get_card('Dalaran Mage', game.player.board) #Spell Damage +1
  game.perform_action(hero_power_actions(game, game.player)[0])
  assert game.enemy.health == 28


# --- Fireblast (mage) --------------------------------------------------------

def test_fireblast_deals_one_damage_to_any_target():
  game = make_game(Classes.MAGE, Classes.WARRIOR)
  yeti = game.game_manager.get_card('Chillwind Yeti', game.enemy.board)
  action = [a for a in hero_power_actions(game, game.player) if a.targets == [yeti]][0]
  game.perform_action(action)
  assert yeti.get_health() == 4

def test_fireblast_can_target_both_heroes_and_both_boards():
  game = make_game(Classes.MAGE, Classes.WARRIOR)
  friendly = game.game_manager.get_card('Chillwind Yeti', game.player.board)
  enemy_minion = game.game_manager.get_card('Chillwind Yeti', game.enemy.board)
  targets = [action.targets[0] for action in hero_power_actions(game, game.player)]
  assert game.player in targets and game.enemy in targets
  assert friendly in targets and enemy_minion in targets

def test_fireblast_cannot_target_an_enemy_stealth_minion():
  game = make_game(Classes.MAGE, Classes.WARRIOR)
  worgen = game.game_manager.get_card('Worgen Infiltrator', game.enemy.board)
  targets = [action.targets[0] for action in hero_power_actions(game, game.player)]
  assert worgen not in targets

def test_fireblast_cannot_target_a_hexproof_minion_on_either_side():
  #Faerie Dragon: "Can't be targeted by spells or Hero Powers" - both sides
  game = make_game(Classes.MAGE, Classes.WARRIOR)
  friendly_dragon = game.game_manager.get_card('Faerie Dragon', game.player.board)
  enemy_dragon = game.game_manager.get_card('Faerie Dragon', game.enemy.board)
  targets = [action.targets[0] for action in hero_power_actions(game, game.player)]
  assert friendly_dragon not in targets and enemy_dragon not in targets

def test_fireblast_kills_a_one_health_minion():
  game = make_game(Classes.MAGE, Classes.WARRIOR)
  wisp = game.game_manager.get_card('Wisp', game.enemy.board)
  action = [a for a in hero_power_actions(game, game.player) if a.targets == [wisp]][0]
  game.perform_action(action)
  assert wisp.parent == game.enemy.graveyard


# --- Armor Up! (warrior) -----------------------------------------------------

def test_armor_up_gives_two_armor_to_its_own_hero():
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  actions = hero_power_actions(game, game.player)
  assert len(actions) == 1 and actions[0].targets == [game.player]
  game.perform_action(actions[0])
  assert game.player.armor == 2
  assert game.enemy.armor == 0

def test_armor_up_stacks_across_turns_without_a_cap():
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  for _ in range(3):
    game.player.used_hero_power = False
    game.player.current_mana = 10
    game.perform_action(hero_power_actions(game, game.player)[0])
  assert game.player.armor == 6

def test_armor_up_does_not_heal_health():
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  game.player.health = 20
  game.perform_action(hero_power_actions(game, game.player)[0])
  assert game.player.health == 20 and game.player.armor == 2


# --- documented simplification ----------------------------------------------

def test_hero_power_affordability_uses_a_hardcoded_cost_of_two():
  #DOCUMENTED SIMPLIFICATION: get_hero_power_actions gates on `current_mana >= 2`
  #rather than hero_power.get_manacost(). No classic/Naxx card changes a hero
  #power's cost, and the aura scan in Card.get_manacost never matches a
  #HERO_POWER card type, so the two are always equal in practice - the literal
  #keeps this hot action-generation path cheap for MCTS rollouts.
  game = make_game(Classes.WARRIOR, Classes.HUNTER)
  game.player.hero_power.manacost = 5
  game.player.current_mana = 2
  assert len(hero_power_actions(game, game.player)) == 1 #offered despite the raised cost
  assert game.player.hero_power.get_manacost() == 5
