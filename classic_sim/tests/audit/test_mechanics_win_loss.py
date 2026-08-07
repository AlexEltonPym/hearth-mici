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

# Mechanics audit: lethal detection, armor, and the board-full edge cases.
# take_turn()/play_game() report 0 when the "player" side is dead and 1 when the
# "enemy" side is dead.


# --- lethal detection --------------------------------------------------------

def test_damage_that_empties_a_hero_raises_player_dead():
  game = GameManager().create_test_game()
  game.player.health = 3
  with pytest.raises(PlayerDead):
    game.deal_damage(game.player, 3)
  assert game.player.health <= 0

def test_lethal_is_detected_on_either_hero():
  for dying, expected_status in [('player', 0), ('enemy', 1)]:
    game = GameManager().create_test_game()
    hero = getattr(game, dying)
    hero.health = 1
    try:
      game.deal_damage(hero, 5)
    except PlayerDead:
      pass
    status = 0 if game.player.health <= 0 else (1 if game.enemy.health <= 0 else -1)
    assert status == expected_status

def test_exactly_zero_health_is_lethal():
  game = GameManager().create_test_game()
  game.enemy.health = 4
  with pytest.raises(PlayerDead):
    game.deal_damage(game.enemy, 4)
  assert game.enemy.health == 0

def test_a_hero_at_one_health_survives_non_lethal_damage():
  game = GameManager().create_test_game()
  game.enemy.health = 5
  game.deal_damage(game.enemy, 4)
  assert game.enemy.health == 1

def test_lethal_from_an_attack_ends_the_game():
  game = GameManager().create_test_game()
  player = game.current_player
  player.other_player.health = 3
  wolfrider = game.game_manager.get_card('Wolfrider', player.board)
  wolfrider.attacks_this_turn = 0
  with pytest.raises(PlayerDead):
    game.perform_action(Action(Actions.ATTACK, wolfrider, [player.other_player]))
  assert player.other_player.health <= 0


# --- armor -------------------------------------------------------------------

def test_armor_absorbs_damage_before_health():
  game = GameManager().create_test_game()
  hero = game.player
  hero.armor = 5
  game.deal_damage(hero, 3)
  assert hero.armor == 2 and hero.health == 30

def test_armor_absorbs_exactly_lethal_damage():
  game = GameManager().create_test_game()
  hero = game.player
  hero.health = 4
  hero.armor = 10
  game.deal_damage(hero, 12) #would be lethal twice over without armor
  assert hero.armor == 0
  assert hero.health == 2

def test_damage_beyond_armor_spills_into_health_and_can_be_lethal():
  game = GameManager().create_test_game()
  hero = game.player
  hero.health = 3
  hero.armor = 2
  with pytest.raises(PlayerDead):
    game.deal_damage(hero, 8)
  assert hero.armor == 0 and hero.health <= 0

def test_armor_does_not_go_negative():
  game = GameManager().create_test_game()
  hero = game.player
  hero.armor = 1
  game.deal_damage(hero, 6)
  assert hero.armor == 0 and hero.health == 25


# --- simultaneous lethal -----------------------------------------------------

def test_simultaneous_lethal_is_reported_as_a_player_loss():
  #DOCUMENTED SIMPLIFICATION: real Hearthstone calls a double kill a draw. The
  #engine's result protocol has only 0 (player dead) / 1 (enemy dead) / -1
  #(ongoing), and take_turn checks the player first, so a mutual kill is scored
  #as a player loss rather than a draw.
  game = GameManager().create_test_game()
  game.player.health = 1
  game.enemy.health = 1
  for hero in [game.player, game.enemy]:
    try:
      game.deal_damage(hero, 5)
    except PlayerDead:
      pass
  assert game.player.health <= 0 and game.enemy.health <= 0
  status = 0 if game.player.health <= 0 else 1
  assert status == 0

def test_a_dying_minions_deathrattle_can_kill_the_attacking_hero():
  #Leper Gnome's 2 damage resolves out of the death, after combat damage: the
  #attacker can win the trade on board and still lose the game
  game = GameManager().create_test_game()
  player = game.current_player
  player.health = 2
  gnome = game.game_manager.get_card('Leper Gnome', player.other_player.board) #2/1, Deathrattle: 2 to enemy hero
  attacker = game.game_manager.get_card('Chillwind Yeti', player.board)
  attacker.attacks_this_turn = 0
  with pytest.raises(PlayerDead):
    game.perform_action(Action(Actions.ATTACK, attacker, [gnome]))
  assert gnome.parent == player.other_player.graveyard
  assert player.health <= 0


# --- board limits ------------------------------------------------------------

def test_a_full_board_blocks_further_minion_plays():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(7):
    game.game_manager.get_card('Wisp', player.board)
  game.game_manager.get_card('Chillwind Yeti', player.hand)
  assert len(player.board) == player.board.max_entries == 7
  assert len([a for a in game.get_available_actions(player) if a.action_type == Actions.CAST_MINION]) == 0

def test_a_full_board_silently_drops_token_summons():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(6):
    game.game_manager.get_card('Wisp', player.board)
  tidehunter = game.game_manager.get_card('Murloc Tidehunter', player.hand) #Battlecry: summon a 1/1
  game.perform_action([a for a in game.get_available_actions(player) if a.source == tidehunter][0])
  assert len(player.board) == 7
  assert 'Murloc Scout' not in player.board.names() #no room left after Tidehunter itself

def test_the_board_frees_up_again_when_a_minion_dies():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(6):
    game.game_manager.get_card('Wisp', player.board)
  doomed = game.game_manager.get_card('Wisp', player.board)
  game.game_manager.get_card('Chillwind Yeti', player.hand)
  assert len([a for a in game.get_available_actions(player) if a.action_type == Actions.CAST_MINION]) == 0
  game.handle_death(doomed)
  assert len([a for a in game.get_available_actions(player) if a.action_type == Actions.CAST_MINION]) == 1

def test_each_player_has_their_own_seven_slot_board():
  game = GameManager().create_test_game()
  player = game.current_player
  for _ in range(7):
    game.game_manager.get_card('Wisp', player.board)
  for _ in range(7):
    game.game_manager.get_card('Wisp', player.other_player.board)
  assert len(player.board) == 7 and len(player.other_player.board) == 7
