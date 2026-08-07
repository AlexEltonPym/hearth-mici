import sys

# appending the parent directory path
sys.path.append('../')
sys.path.append('../../')

import pytest
from copy import deepcopy

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

# Mechanics audit: the action-generation surface. Every strategy picks from
# game.get_available_actions, so an illegal offer is played and a missing offer
# is invisible - both silently distort every experiment run on the engine.


CASTING_ACTIONS = [Actions.CAST_MINION, Actions.CAST_SPELL, Actions.CAST_WEAPON, Actions.CAST_SECRET]


def action_signature(action):
  return (action.action_type, id(action.source), tuple(id(target) for target in action.targets))

def busy_board(game):
  #a mixed state that exercises most of the generators at once
  player = game.current_player
  enemy = player.other_player
  game.game_manager.get_card('Chillwind Yeti', player.board).attacks_this_turn = 0
  game.game_manager.get_card('Wolfrider', player.board).attacks_this_turn = 0
  game.game_manager.get_card('Argent Squire', enemy.board)
  game.game_manager.get_card('Boulderfist Ogre', enemy.board)
  for name in ['Chillwind Yeti', 'Fireball', 'Fiery War Axe', 'Shattered Sun Cleric', 'Wisp']:
    try:
      game.game_manager.get_card(name, player.hand)
    except KeyError:
      pass
  return player


# --- everything offered is legal --------------------------------------------

def test_no_unaffordable_card_is_ever_offered():
  game = GameManager().create_test_game()
  player = busy_board(game)
  for mana in range(0, 11):
    player.current_mana = mana
    for action in game.get_available_actions(player):
      if action.action_type in CASTING_ACTIONS:
        assert action.source.get_manacost() <= mana
      if action.action_type == Actions.CAST_HERO_POWER:
        assert mana >= 2

def test_offered_cards_always_come_from_the_players_own_hand():
  game = GameManager().create_test_game()
  player = busy_board(game)
  for action in game.get_available_actions(player):
    if action.action_type in CASTING_ACTIONS:
      assert action.source.parent == player.hand
      assert action.source.owner == player

def test_offered_attacks_all_respect_taunt():
  game = GameManager().create_test_game()
  player = busy_board(game)
  taunt = game.game_manager.get_card("Sen'jin Shieldmasta", player.other_player.board)
  for action in game.get_available_actions(player):
    if action.action_type == Actions.ATTACK:
      assert action.targets[0] == taunt

def test_offered_attackers_are_all_able_to_attack():
  game = GameManager().create_test_game()
  player = busy_board(game)
  sick = game.game_manager.get_card('Boulderfist Ogre', player.board) #played this turn
  frozen = game.game_manager.get_card('Core Hound', player.board)
  frozen.attacks_this_turn = 0
  frozen.perm_attributes.append(Attributes.FROZEN)
  attackers = [action.source for action in game.get_available_actions(player) if action.action_type == Actions.ATTACK]
  assert sick not in attackers
  assert frozen not in attackers
  for attacker in attackers:
    assert attacker.get_attack() > 0
    assert not attacker.has_attribute(Attributes.FROZEN)

def test_no_duplicate_identical_actions_are_offered():
  game = GameManager().create_test_game()
  player = busy_board(game)
  signatures = [action_signature(action) for action in game.get_available_actions(player)]
  assert len(signatures) == len(set(signatures))

def test_two_copies_of_a_card_produce_two_distinct_actions():
  #distinct card objects are genuinely distinct choices, not duplicates
  game = GameManager().create_test_game()
  player = game.current_player
  first = game.game_manager.get_card('Chillwind Yeti', player.hand)
  second = game.game_manager.get_card('Chillwind Yeti', player.hand)
  sources = [action.source for action in game.get_available_actions(player) if action.action_type == Actions.CAST_MINION]
  assert first in sources and second in sources

def test_every_offered_action_can_actually_be_performed():
  #a forward model deepcopies the game and plays each offer - none may explode
  game = GameManager().create_test_game()
  busy_board(game)
  for index in range(len(game.get_available_actions(game.current_player))):
    forward = deepcopy(game)
    actions = forward.get_available_actions(forward.current_player)
    try:
      forward.perform_action(actions[index])
    except PlayerDead:
      pass #a lethal action is legal, the game just ends


# --- nothing legal is missing ------------------------------------------------

def test_end_turn_is_always_offered():
  game = GameManager().create_test_game()
  player = game.current_player
  player.current_mana = 0
  player.hand.clear()
  actions = game.get_available_actions(player)
  assert len([action for action in actions if action.action_type == Actions.END_TURN]) == 1

def test_a_minion_with_no_battlecry_targets_is_still_playable():
  game = GameManager().create_test_game()
  player = game.current_player
  cleric = game.game_manager.get_card('Shattered Sun Cleric', player.hand) #targets a friendly minion
  actions = [action for action in game.get_available_actions(player) if action.source == cleric]
  assert len(actions) == 1 and actions[0].targets == []

def test_a_minion_whose_only_target_is_an_enemy_stealth_minion_is_still_playable():
  #FIXED: the stealth filter used to erase every offer for the card, making a
  #perfectly playable minion disappear from the action list entirely
  game = GameManager().create_test_game()
  player = game.current_player
  game.game_manager.get_card('Worgen Infiltrator', player.other_player.board)
  taskmaster = game.game_manager.get_card('Cruel Taskmaster', player.hand) #targeted, any minion
  actions = [action for action in game.get_available_actions(player) if action.source == taskmaster]
  assert len(actions) == 1 and actions[0].targets == []
  game.perform_action(actions[0])
  assert taskmaster.parent == player.board #battlecry simply fizzled

def test_your_own_stealthed_minion_can_be_targeted_by_your_own_spell():
  #FIXED: Stealth reads "can't be targeted by ENEMY spells, Hero Powers or
  #attacks" - the engine was hiding friendly stealthed minions from their owner
  game = GameManager().create_test_game()
  player = game.current_player
  worgen = game.game_manager.get_card('Worgen Infiltrator', player.board)
  charge = game.game_manager.get_card('Charge', player.hand) #friendly minion only
  actions = [action for action in game.get_available_actions(player) if action.source == charge and action.targets == [worgen]]
  assert len(actions) == 1
  game.perform_action(actions[0])
  assert worgen.has_attribute(Attributes.CHARGE)

def test_your_own_stealthed_minion_can_be_targeted_by_your_own_battlecry():
  game = GameManager().create_test_game()
  player = game.current_player
  worgen = game.game_manager.get_card('Worgen Infiltrator', player.board)
  cleric = game.game_manager.get_card('Shattered Sun Cleric', player.hand)
  actions = [action for action in game.get_available_actions(player) if action.source == cleric and action.targets == [worgen]]
  assert len(actions) == 1

def test_an_enemy_stealthed_minion_is_still_hidden_from_spells():
  game = GameManager().create_test_game()
  player = game.current_player
  worgen = game.game_manager.get_card('Worgen Infiltrator', player.other_player.board)
  fireball = game.game_manager.get_card('Fireball', player.hand)
  targets = [action.targets[0] for action in game.get_available_actions(player) if action.source == fireball]
  assert worgen not in targets
  assert player.other_player in targets

def test_hexproof_minions_are_hidden_from_spells_on_both_sides():
  game = GameManager().create_test_game()
  player = game.current_player
  friendly = game.game_manager.get_card('Faerie Dragon', player.board)
  enemy = game.game_manager.get_card('Faerie Dragon', player.other_player.board)
  fireball = game.game_manager.get_card('Fireball', player.hand)
  targets = [action.targets[0] for action in game.get_available_actions(player) if action.source == fireball]
  assert friendly not in targets and enemy not in targets

def test_a_weapon_can_be_played_while_another_weapon_is_equipped():
  #FIXED: get_playable_weapon_actions refused to offer a weapon whenever the
  #hero already had one. Real Hearthstone lets you equip over it (destroying
  #the old weapon), which matters for every weapon-deathrattle card.
  game = GameManager().create_test_game()
  player = game.current_player
  axe = game.game_manager.get_card('Fiery War Axe', player.hand)
  game.perform_action([action for action in game.get_available_actions(player) if action.source == axe][0])
  reaper = game.game_manager.get_card('Arcanite Reaper', player.hand)
  actions = [action for action in game.get_available_actions(player) if action.source == reaper]
  assert len(actions) == 1
  game.perform_action(actions[0])
  assert player.weapon == reaper
  assert axe.parent == player.graveyard

def test_a_random_battlecry_without_replacement_does_not_crash_generation():
  #FIXED: the RANDOMLY branch of the minion/weapon generators referenced an
  #undefined `cast_targets`; only random_replace=True cards dodged the NameError
  game = GameManager().create_test_game()
  player = game.current_player
  bomber = Card(name="Audit Random Battlecry", card_type=CardTypes.MINION, manacost=0, attack=1, health=1,
                effect=DealDamage(value=ConstantInt(1), trigger=Triggers.BATTLECRY, method=Methods.RANDOMLY,
                                  random_count=2, random_replace=False, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))
  bomber.set_owner(player)
  bomber.set_parent(player.hand)
  game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  game.game_manager.get_card('Boulderfist Ogre', player.other_player.board)
  actions = [action for action in game.get_available_actions(player) if action.source == bomber]
  assert len(actions) == 1 and len(actions[0].targets) == 2

def test_hero_power_and_attacks_remain_available_on_a_full_board():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(7):
    game.game_manager.get_card('Wisp', player.board).attacks_this_turn = 0
  game.game_manager.get_card('Chillwind Yeti', player.hand)
  game.game_manager.get_card('Fireball', player.hand)
  actions = game.get_available_actions(player)
  assert len([a for a in actions if a.action_type == Actions.CAST_MINION]) == 0
  assert len([a for a in actions if a.action_type == Actions.CAST_SPELL]) > 0
  assert len([a for a in actions if a.action_type == Actions.ATTACK]) > 0
  assert len([a for a in actions if a.action_type == Actions.CAST_HERO_POWER]) == 1


# --- secrets -----------------------------------------------------------------

def test_a_secret_already_active_is_not_offered_again():
  game = GameManager().create_test_game()
  player = game.current_player
  first = game.game_manager.get_card('Explosive Trap', player.hand)
  second = game.game_manager.get_card('Explosive Trap', player.hand)
  game.perform_action([action for action in game.get_available_actions(player) if action.source == first][0])
  assert len([action for action in game.get_available_actions(player) if action.source == second]) == 0

def test_no_secret_is_offered_once_five_are_active():
  game = GameManager().create_test_game()
  player = game.current_player
  for name in ['Explosive Trap', 'Freezing Trap', 'Misdirection', 'Snake Trap', 'Snipe']:
    secret = game.game_manager.get_card(name, player.hand)
    game.perform_action([action for action in game.get_available_actions(player) if action.source == secret][0])
  assert len(player.secrets_zone) == 5
  extra = game.game_manager.get_card('Counterspell', player.hand)
  assert len([action for action in game.get_available_actions(player) if action.source == extra]) == 0
