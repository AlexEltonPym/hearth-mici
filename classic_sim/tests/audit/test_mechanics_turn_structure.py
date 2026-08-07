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

# Mechanics audit: turn and resource structure (mana crystals, The Coin,
# opening hands, end-of-turn / untap ordering).
# NOTE: game.end_turn() does NOT call game.untap() - a full turn boundary in
# these tests is end_turn() followed by untap().


def make_game():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_player(Classes.WARRIOR, Deck.generate_random, GreedyAction())
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_random, GreedyAction())
  return game_manager.create_game()


# --- mana crystals -----------------------------------------------------------

def test_mana_crystal_grows_by_one_each_untap():
  game = GameManager().create_test_game()
  player = game.current_player
  player.max_mana = 0
  player.current_mana = 0
  for expected in range(1, 6):
    game.untap()
    assert player.max_mana == expected
    assert player.current_mana == expected

def test_mana_crystals_cap_at_ten():
  game = GameManager().create_test_game()
  player = game.current_player
  player.max_mana = 0
  for _ in range(15):
    game.untap()
  assert player.max_mana == 10
  assert player.current_mana == 10

def test_unspent_mana_is_lost_at_the_start_of_the_next_turn():
  game = GameManager().create_test_game()
  player = game.current_player
  player.max_mana = 5
  player.current_mana = 5
  game.game_manager.get_card('Wisp', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.action_type == Actions.CAST_MINION][0])
  assert player.current_mana == 5 #Wisp is free
  player.current_mana = 2 #pretend some mana was spent and some floated
  game.untap()
  assert player.current_mana == 6 #refilled to the new max, the floated 2 did not carry over

def test_spending_mana_reduces_current_but_not_max():
  game = GameManager().create_test_game()
  player = game.current_player
  player.max_mana = 10
  player.current_mana = 10
  yeti = game.game_manager.get_card('Chillwind Yeti', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == yeti][0])
  assert player.current_mana == 6
  assert player.max_mana == 10


# --- opening hands and The Coin ---------------------------------------------

def test_opening_hand_sizes_are_three_and_four_plus_coin():
  game = make_game()
  first = game.current_player
  second = game.current_player.other_player
  assert len(first.hand) == 3
  assert len(second.hand) == 5 #4 cards + The Coin

def test_the_coin_goes_to_the_player_going_second():
  game = make_game()
  assert 'The Coin' in game.current_player.other_player.hand.names()
  assert 'The Coin' not in game.current_player.hand.names()

def test_the_coin_gives_one_temporary_mana():
  game = make_game()
  second = game.current_player.other_player
  coin = [card for card in second.hand if card.name == 'The Coin'][0]
  second.max_mana = 3
  second.current_mana = 3
  game.current_player = second
  game.perform_action(Action(Actions.CAST_SPELL, coin, [second]))
  assert second.current_mana == 4
  assert second.max_mana == 3 #temporary: the crystal itself is not permanent
  game.untap()
  assert second.current_mana == 4 and second.max_mana == 4 #back to the natural curve

def test_the_coin_cannot_take_a_player_past_ten_mana():
  game = make_game()
  second = game.current_player.other_player
  coin = [card for card in second.hand if card.name == 'The Coin'][0]
  second.max_mana = 10
  second.current_mana = 10
  game.current_player = second
  game.perform_action(Action(Actions.CAST_SPELL, coin, [second]))
  assert second.current_mana == 10


# --- end of turn / untap ordering -------------------------------------------

def test_end_turn_hands_control_to_the_other_player():
  game = GameManager().create_test_game()
  starter = game.current_player
  game.end_turn()
  assert game.current_player == starter.other_player

def test_end_of_turn_triggers_fire_before_control_switches():
  #Ragnaros' end-of-turn shot belongs to its controller: it must resolve while
  #that player is still the current player
  game = GameManager().create_test_game()
  player = game.current_player
  game.game_manager.get_card('Ragnaros the Firelord', player.board)
  enemy_health_before = player.other_player.health
  game.end_turn()
  assert player.other_player.health == enemy_health_before - 8
  assert game.current_player == player.other_player

def test_temporary_buffs_expire_at_the_end_of_the_turn_they_were_given():
  game = GameManager().create_test_game()
  player = game.current_player
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  abusive = game.game_manager.get_card('Abusive Sergeant', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == abusive and a.targets == [yeti]][0])
  assert yeti.get_attack() == 6
  game.end_turn()
  assert yeti.get_attack() == 4

def test_temporary_buff_on_an_enemy_minion_also_expires_this_turn():
  game = GameManager().create_test_game()
  player = game.current_player
  enemy_yeti = game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  abusive = game.game_manager.get_card('Abusive Sergeant', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == abusive and a.targets == [enemy_yeti]][0])
  assert enemy_yeti.get_attack() == 6
  game.end_turn()
  assert enemy_yeti.get_attack() == 4

def test_permanent_buffs_survive_the_turn_boundary():
  game = GameManager().create_test_game()
  player = game.current_player
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  cleric = game.game_manager.get_card('Shattered Sun Cleric', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == cleric and a.targets == [yeti]][0])
  assert yeti.get_attack() == 5
  game.end_turn()
  game.end_turn()
  game.untap()
  assert yeti.get_attack() == 5

def test_frozen_thaws_at_the_end_of_its_controllers_turn():
  game = GameManager().create_test_game()
  player = game.current_player
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  yeti.attacks_this_turn = 0 #already on board since last turn
  yeti.perm_attributes.append(Attributes.FROZEN)
  assert len([a for a in game.get_available_actions(player) if a.source == yeti]) == 0
  game.end_turn()
  assert not yeti.has_attribute(Attributes.FROZEN)

def test_frozen_summoning_sick_minion_stays_frozen_through_the_next_turn():
  #a minion that could not have attacked anyway does not burn its thaw
  game = GameManager().create_test_game()
  player = game.current_player
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board) #attacks_this_turn == -1 -> sick
  yeti.perm_attributes.append(Attributes.FROZEN)
  game.end_turn()
  assert yeti.has_attribute(Attributes.FROZEN)

def test_untap_clears_summoning_sickness_and_resets_attack_counters():
  game = GameManager().create_test_game()
  player = game.current_player
  yeti = game.game_manager.get_card('Chillwind Yeti', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.source == yeti][0])
  assert yeti.attacks_this_turn == -1
  game.end_turn()
  game.end_turn()
  game.untap()
  assert yeti.attacks_this_turn == 0
  assert player.attacks_this_turn == 0

def test_untap_draws_exactly_one_card():
  game = GameManager().create_test_game()
  player = game.current_player
  hand_before = len(player.hand)
  deck_before = len(player.deck)
  game.untap()
  assert len(player.hand) == hand_before + 1
  assert len(player.deck) == deck_before - 1

def test_minions_played_this_turn_resets_at_end_of_turn():
  game = GameManager().create_test_game()
  player = game.current_player
  game.game_manager.get_card('Wisp', player.hand)
  game.perform_action([a for a in game.get_available_actions(player) if a.action_type == Actions.CAST_MINION][0])
  assert player.minions_played_this_turn == 1
  game.end_turn()
  assert player.minions_played_this_turn == 0
