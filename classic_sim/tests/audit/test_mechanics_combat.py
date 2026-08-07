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

# Mechanics audit: attack legality and damage exchange.
# Ground truth: 2014 Hearthstone.


def attack_actions(game, player, source=None):
  return [action for action in game.get_available_actions(player)
          if action.action_type == Actions.ATTACK and (source is None or action.source == source)]

def ready(minion):
  minion.attacks_this_turn = 0 #on board since last turn, no summoning sickness
  return minion


# --- taunt -------------------------------------------------------------------

def test_taunt_is_the_only_legal_attack_target():
  game = GameManager().create_test_game()
  player = game.current_player
  attacker = ready(game.game_manager.get_card('Wolfrider', player.board))
  taunt = game.game_manager.get_card('Goldshire Footman', player.other_player.board)
  game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  targets = [action.targets[0] for action in attack_actions(game, player, attacker)]
  assert targets == [taunt]

def test_taunt_also_constrains_the_hero_attack():
  game = GameManager().create_test_game()
  player = game.current_player
  player.attack = 3
  taunt = game.game_manager.get_card('Goldshire Footman', player.other_player.board)
  targets = [action.targets[0] for action in attack_actions(game, player, player)]
  assert targets == [taunt]

def test_stealthed_taunt_does_not_force_an_attack_and_cannot_be_hit():
  game = GameManager().create_test_game()
  player = game.current_player
  attacker = ready(game.game_manager.get_card('Wolfrider', player.board))
  taunt = game.game_manager.get_card('Goldshire Footman', player.other_player.board)
  taunt.perm_attributes.append(Attributes.STEALTH)
  targets = [action.targets[0] for action in attack_actions(game, player, attacker)]
  assert targets == [player.other_player] #hero only: the stealthed taunt is untouchable

def test_a_stealthed_minion_cannot_be_attacked():
  game = GameManager().create_test_game()
  player = game.current_player
  attacker = ready(game.game_manager.get_card('Wolfrider', player.board))
  worgen = game.game_manager.get_card('Worgen Infiltrator', player.other_player.board)
  targets = [action.targets[0] for action in attack_actions(game, player, attacker)]
  assert worgen not in targets

def test_taunt_stops_constraining_once_it_dies():
  game = GameManager().create_test_game()
  player = game.current_player
  attacker = ready(game.game_manager.get_card('Chillwind Yeti', player.board))
  taunt = game.game_manager.get_card('Goldshire Footman', player.other_player.board) #1/2
  game.perform_action(attack_actions(game, player, attacker)[0])
  assert taunt.parent == player.other_player.graveyard
  second = ready(game.game_manager.get_card('Wolfrider', player.board))
  assert player.other_player in [action.targets[0] for action in attack_actions(game, player, second)]


# --- summoning sickness, charge, windfury ------------------------------------

def test_a_minion_cannot_attack_the_turn_it_is_played():
  game = GameManager().create_test_game()
  player = game.current_player
  yeti = game.game_manager.get_card('Chillwind Yeti', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == yeti][0])
  assert len(attack_actions(game, player, yeti)) == 0

def test_charge_lets_a_minion_attack_the_turn_it_is_played():
  game = GameManager().create_test_game()
  player = game.current_player
  wolfrider = game.game_manager.get_card('Wolfrider', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == wolfrider][0])
  assert len(attack_actions(game, player, wolfrider)) > 0
  game.perform_action(attack_actions(game, player, wolfrider)[0])
  assert player.other_player.health == 27
  assert len(attack_actions(game, player, wolfrider)) == 0 #charge grants one attack, not unlimited

def test_windfury_grants_exactly_two_attacks_per_turn():
  game = GameManager().create_test_game()
  player = game.current_player
  hawk = ready(game.game_manager.get_card('Young Dragonhawk', player.board)) #1/1 Windfury
  assert len(attack_actions(game, player, hawk)) > 0
  game.perform_action(Action(Actions.ATTACK, hawk, [player.other_player]))
  assert len(attack_actions(game, player, hawk)) > 0
  game.perform_action(Action(Actions.ATTACK, hawk, [player.other_player]))
  assert len(attack_actions(game, player, hawk)) == 0
  assert player.other_player.health == 28

def test_windfury_weapon_grants_the_hero_two_swings():
  game = GameManager().create_test_game()
  player = game.current_player
  weapon = game.game_manager.get_card('Windfury Weapon', player.hand) #2/2 Windfury test card
  game.perform_action([a for a in game.get_available_actions(player) if a.source == weapon][0])
  game.perform_action(Action(Actions.ATTACK, player, [player.other_player]))
  assert len(attack_actions(game, player, player)) > 0
  game.perform_action(Action(Actions.ATTACK, player, [player.other_player]))
  assert len(attack_actions(game, player, player)) == 0
  assert player.other_player.health == 26


# --- frozen ------------------------------------------------------------------

def test_a_frozen_minion_cannot_attack():
  game = GameManager().create_test_game()
  player = game.current_player
  yeti = ready(game.game_manager.get_card('Chillwind Yeti', player.board))
  assert len(attack_actions(game, player, yeti)) > 0
  yeti.perm_attributes.append(Attributes.FROZEN)
  assert len(attack_actions(game, player, yeti)) == 0

def test_a_frozen_hero_cannot_attack():
  game = GameManager().create_test_game()
  player = game.current_player
  weapon = game.game_manager.get_card('Fiery War Axe', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == weapon][0])
  assert len(attack_actions(game, player, player)) > 0
  player.perm_attributes.append(Attributes.FROZEN)
  assert len(attack_actions(game, player, player)) == 0

def test_freezing_damage_applies_frozen_to_the_target():
  game = GameManager().create_test_game()
  player = game.current_player
  frost_elemental = game.game_manager.get_card('Frost Elemental', player.hand) #Battlecry: Freeze a character
  target = game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  game.perform_action([a for a in game.get_available_actions(player)
                       if a.source == frost_elemental and a.targets == [target]][0])
  assert target.has_attribute(Attributes.FROZEN)


# --- attributes that forbid attacking ----------------------------------------

def test_defender_minion_cannot_attack():
  game = GameManager().create_test_game()
  player = game.current_player
  watcher = ready(game.game_manager.get_card('Ancient Watcher', player.board))
  assert watcher.has_attribute(Attributes.DEFENDER)
  assert len(attack_actions(game, player, watcher)) == 0

def test_cant_attack_minion_cannot_attack():
  game = GameManager().create_test_game()
  player = game.current_player
  ragnaros = ready(game.game_manager.get_card('Ragnaros the Firelord', player.board))
  assert ragnaros.has_attribute(Attributes.CANT_ATTACK)
  assert len(attack_actions(game, player, ragnaros)) == 0

def test_cant_attack_hero_cannot_attack():
  #FIXED: get_hero_attack_actions checked DEFENDER but not CANT_ATTACK, so a
  #hero carrying the attribute was still offered an attack
  game = GameManager().create_test_game()
  player = game.current_player
  player.attack = 4
  assert len(attack_actions(game, player, player)) > 0
  player.perm_attributes.append(Attributes.CANT_ATTACK)
  assert len(attack_actions(game, player, player)) == 0

def test_a_zero_attack_minion_is_never_offered_an_attack():
  game = GameManager().create_test_game()
  player = game.current_player
  totem = ready(game.game_manager.get_card('Shieldbearer', player.board)) #0/4 Taunt
  assert totem.get_attack() == 0
  assert len(attack_actions(game, player, totem)) == 0

def test_a_hero_with_no_weapon_cannot_attack():
  game = GameManager().create_test_game()
  player = game.current_player
  assert player.get_attack() == 0
  assert len(attack_actions(game, player, player)) == 0


# --- damage exchange ---------------------------------------------------------

def test_minions_trade_damage_in_both_directions():
  game = GameManager().create_test_game()
  player = game.current_player
  attacker = ready(game.game_manager.get_card('Chillwind Yeti', player.board)) #4/5
  defender = game.game_manager.get_card('Boulderfist Ogre', player.other_player.board) #6/7
  game.perform_action(Action(Actions.ATTACK, attacker, [defender]))
  assert defender.get_health() == 3
  assert attacker.parent == player.graveyard #4/5 dies to 6 damage

def test_attacking_a_hero_deals_no_damage_back():
  game = GameManager().create_test_game()
  player = game.current_player
  attacker = ready(game.game_manager.get_card('Chillwind Yeti', player.board))
  game.perform_action(Action(Actions.ATTACK, attacker, [player.other_player]))
  assert player.other_player.health == 26
  assert attacker.get_health() == 5

def test_divine_shield_absorbs_the_hit_and_blocks_poisonous():
  game = GameManager().create_test_game()
  player = game.current_player
  squire = ready(game.game_manager.get_card('Argent Squire', player.board)) #1/1 Divine Shield
  cobra = game.game_manager.get_card('Emperor Cobra', player.other_player.board) #Poisonous
  game.perform_action(Action(Actions.ATTACK, squire, [cobra]))
  assert squire.parent == player.board #survives: the shield ate the damage
  assert not squire.has_attribute(Attributes.DIVINE_SHIELD)
  assert squire.get_health() == 1

def test_poisonous_destroys_any_damaged_minion():
  game = GameManager().create_test_game()
  player = game.current_player
  ogre = ready(game.game_manager.get_card('Boulderfist Ogre', player.board)) #6/7
  cobra = game.game_manager.get_card('Emperor Cobra', player.other_player.board) #2/3 Poisonous
  game.perform_action(Action(Actions.ATTACK, ogre, [cobra]))
  assert ogre.parent == player.graveyard
  assert cobra.parent == player.other_player.graveyard

def test_poisonous_does_not_destroy_a_hero():
  game = GameManager().create_test_game()
  player = game.current_player
  cobra = ready(game.game_manager.get_card('Emperor Cobra', player.board))
  game.perform_action(Action(Actions.ATTACK, cobra, [player.other_player]))
  assert player.other_player.health == 28

def test_attacking_breaks_stealth():
  game = GameManager().create_test_game()
  player = game.current_player
  worgen = ready(game.game_manager.get_card('Worgen Infiltrator', player.board))
  assert worgen.has_attribute(Attributes.STEALTH)
  game.perform_action(Action(Actions.ATTACK, worgen, [player.other_player]))
  assert not worgen.has_attribute(Attributes.STEALTH)

def test_a_weapon_loses_one_durability_per_swing():
  game = GameManager().create_test_game()
  player = game.current_player
  axe = game.game_manager.get_card('Fiery War Axe', player.hand) #3/2
  game.perform_action([a for a in game.get_available_actions(player) if a.source == axe][0])
  game.perform_action(Action(Actions.ATTACK, player, [player.other_player]))
  assert player.weapon.health == 1
  player.attacks_this_turn = 0
  game.perform_action(Action(Actions.ATTACK, player, [player.other_player]))
  assert player.weapon is None
  assert axe.parent == player.graveyard
  assert player.other_player.health == 24
