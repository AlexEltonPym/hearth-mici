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

# Mechanics audit: drawing, deck exhaustion, fatigue and the 10-card hand cap.
# Ground truth: 2014 Hearthstone - fatigue damage starts at 1 and escalates by
# 1 per draw from an empty deck; a card drawn into a full hand is destroyed.


# --- fatigue -----------------------------------------------------------------

def test_fatigue_damage_escalates_by_one_per_draw():
  game = GameManager().create_test_game()
  player = game.current_player
  player.deck.clear()
  expected_health = 30
  for expected_hit in [1, 2, 3, 4, 5]:
    game.draw(player, 1)
    expected_health -= expected_hit
    assert player.health == expected_health

def test_fatigue_counter_starts_at_one():
  game = GameManager().create_test_game()
  player = game.current_player
  assert player.fatigue_damage == 1
  player.deck.clear()
  game.draw(player, 1)
  assert player.health == 29
  assert player.fatigue_damage == 2

def test_fatigue_is_tracked_per_player():
  game = GameManager().create_test_game()
  player = game.current_player
  enemy = player.other_player
  player.deck.clear()
  enemy.deck.clear()
  game.draw(player, 3) #1+2+3
  game.draw(enemy, 1)
  assert player.health == 24
  assert enemy.health == 29

def test_fatigue_is_absorbed_by_armor():
  game = GameManager().create_test_game()
  player = game.current_player
  player.deck.clear()
  player.armor = 5
  game.draw(player, 2) #1 then 2
  assert player.armor == 2
  assert player.health == 30

def test_fatigue_can_be_lethal():
  game = GameManager().create_test_game()
  player = game.current_player
  player.deck.clear()
  player.health = 2
  player.fatigue_damage = 5
  with pytest.raises(PlayerDead):
    game.draw(player, 1)
  assert player.health <= 0

def test_drawing_from_an_empty_deck_adds_no_cards():
  game = GameManager().create_test_game()
  player = game.current_player
  player.deck.clear()
  hand_before = len(player.hand)
  game.draw(player, 3)
  assert len(player.hand) == hand_before
  assert len(player.deck) == 0

def test_untap_on_an_empty_deck_causes_fatigue():
  game = GameManager().create_test_game()
  player = game.current_player
  player.deck.clear()
  game.untap()
  assert player.health == 29


# --- normal drawing ----------------------------------------------------------

def test_draw_moves_cards_from_deck_to_hand():
  game = GameManager().create_test_game()
  player = game.current_player
  deck_before = len(player.deck)
  game.draw(player, 3)
  assert len(player.hand) == 3
  assert len(player.deck) == deck_before - 3
  assert len(player.graveyard) == 0

def test_drawn_card_keeps_its_owner():
  game = GameManager().create_test_game()
  player = game.current_player
  game.draw(player, 1)
  drawn = player.hand.get_all()[0]
  assert drawn.owner == player
  assert drawn.parent == player.hand


# --- the 10 card hand cap ----------------------------------------------------

def test_drawing_into_a_full_hand_destroys_the_card():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(10):
    game.game_manager.get_card('Wisp', player.hand)
  assert len(player.hand) == player.hand.max_entries == 10
  deck_before = len(player.deck)
  game.draw(player, 1)
  assert len(player.hand) == 10
  assert len(player.deck) == deck_before - 1
  assert len(player.graveyard) == 1 #burned, not kept in the deck

def test_burned_card_is_the_top_of_the_deck():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(10):
    game.game_manager.get_card('Wisp', player.hand)
  top_of_deck = player.deck.get_all()[-1]
  game.draw(player, 1)
  assert top_of_deck.parent == player.graveyard

def test_a_hand_with_space_is_filled_before_burning_starts():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(9):
    game.game_manager.get_card('Wisp', player.hand)
  game.draw(player, 3)
  assert len(player.hand) == 10
  assert len(player.graveyard) == 2 #one drawn, two burned

def test_drawing_effects_respect_the_hand_cap():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(9):
    game.game_manager.get_card('Wisp', player.hand)
  engineer = game.game_manager.get_card('Novice Engineer', player.hand) #Battlecry: draw a card
  game.perform_action([a for a in game.get_available_actions(player) if a.source == engineer][0])
  assert len(player.hand) == 10 #Engineer left the hand, its draw refilled the slot
  assert len(player.graveyard) == 0


# --- deck bookkeeping --------------------------------------------------------

def test_mulligan_keeps_the_deck_at_full_size():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL])
  game_manager.create_player(Classes.WARRIOR, Deck.generate_random, GreedyAction())
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_random, GreedyAction())
  game = game_manager.create_game()
  for player in [game.player, game.enemy]:
    assert len(player.hand) + len(player.deck) == 30 + (1 if 'The Coin' in player.hand.names() else 0)

def test_fatigue_resets_between_games():
  game = GameManager().create_test_game()
  player = game.current_player
  player.deck.clear()
  game.draw(player, 2)
  assert player.fatigue_damage == 3
  game.reset_game()
  assert game.player.fatigue_damage == 1
  assert game.enemy.fatigue_damage == 1
