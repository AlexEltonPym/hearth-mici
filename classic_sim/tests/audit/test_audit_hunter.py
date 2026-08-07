import sys

# appending the parent directory path
sys.path.append('../')

import pytest

from card import Card
from zones import Deck
from player import Player
from game import Game
from exceptions import PlayerDead
from enums import *
from card_sets import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
from numpy import empty, array
from action import Action
from numpy.random import RandomState

from game_manager import GameManager

# Audit slice: get_hunter_cards() indices 0..24 (all 25 Hunter cards)
#  0 Hunter's Mark        9 Tundra Rhino          18 Eaglehorn Bow
#  1 Arcane Shot         10 Explosive Trap        19 Explosive Shot
#  2 Timber Wolf         11 Freezing Trap         20 Savannah Highmane
#  3 Tracking            12 Scavenging Hyena      21 Bestial Wrath
#  4 Starving Buzzard     13 Snipe                22 Snake Trap
#  5 Animal Companion    14 Deadly Shot           23 Gladiator's Longbow
#  6 Kill Command        15 Unleash the Hounds    24 King Krush
#  7 Houndmaster          16 Flare
#  8 Multi-Shot           17 Misdirection


# ---------------------------------------------------------------------------
# 0. Hunter's Mark
# ---------------------------------------------------------------------------

def test_hunters_mark_sets_health_to_one():
  game = GameManager().create_test_game()
  target = game.game_manager.get_card('River Crocolisk', game.current_player.other_player.board)
  assert target.get_attack() == 2
  assert target.get_health() == 3
  hunters_mark = game.game_manager.get_card("Hunter's Mark", game.current_player.hand)
  assert hunters_mark.get_manacost() == 0  # VANILLA cost is 0 (not the later LEGACY cost of 1)
  cast = list(filter(lambda a: a.source == hunters_mark, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast)
  assert target.get_attack() == 2  # attack unaffected
  assert target.get_health() == 1
  assert target.get_max_health() == 1


def test_explosive_shot_does_not_wrap_around_the_board_edges():
  game = GameManager().create_test_game()
  explosive_shot = game.game_manager.get_card('Explosive Shot', game.current_player.hand)
  giant1 = game.game_manager.get_card('Sea Giant', game.current_player.other_player.board)  # left edge - target this one
  giant2 = game.game_manager.get_card('Sea Giant', game.current_player.other_player.board)
  giant3 = game.game_manager.get_card('Sea Giant', game.current_player.other_player.board)  # right edge, NOT adjacent to giant1
  cast = list(filter(lambda a: a.source == explosive_shot and a.targets[0] == giant1, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast)
  assert giant1.get_health() == 3  # 8 - 5
  assert giant2.get_health() == 6  # 8 - 2, genuinely adjacent
  assert giant3.get_health() == 8  # not adjacent to giant1 on a linear board - should be untouched


# ---------------------------------------------------------------------------
# 20. Savannah Highmane
# ---------------------------------------------------------------------------

def test_savannah_highmane_deathrattle_summons_two_hyenas():
  game = GameManager().create_test_game()
  highmane = game.game_manager.get_card('Savannah Highmane', game.current_player.board)
  assert highmane.get_manacost() == 6
  assert highmane.get_attack() == 6
  assert highmane.get_health() == 5
  game.deal_damage(highmane, 5)
  assert highmane.parent == highmane.owner.graveyard
  assert len(game.current_player.board) == 2
  for hyena in game.current_player.board:
    assert hyena.name == 'Hyena'
    assert hyena.creature_type == CreatureTypes.BEAST
    assert hyena.get_attack() == 2
    assert hyena.get_health() == 2


# ---------------------------------------------------------------------------
# 21. Bestial Wrath
# ---------------------------------------------------------------------------

def test_bestial_wrath_buffs_and_grants_immune_for_the_turn():
  game = GameManager().create_test_game()
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  assert tundra_rhino.get_attack() == 2
  wrath = game.game_manager.get_card('Bestial Wrath', game.current_player.hand)
  assert wrath.get_manacost() == 1
  cast = list(filter(lambda a: a.source == wrath and a.targets[0] == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast)
  assert tundra_rhino.get_attack() == 4
  assert tundra_rhino.has_attribute(Attributes.IMMUNE)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack = list(filter(lambda a: a.source == tundra_rhino and a.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack)
  assert tundra_rhino.get_health() == 5  # took no counter damage, immune
  game.end_turn()
  assert tundra_rhino.get_attack() == 2
  assert not tundra_rhino.has_attribute(Attributes.IMMUNE)


# ---------------------------------------------------------------------------
# 22. Snake Trap
# ---------------------------------------------------------------------------

def test_snake_trap_summons_three_snakes_when_minion_attacked():
  game = GameManager().create_test_game()
  snake_trap = game.game_manager.get_card('Snake Trap', game.current_player.other_player.secrets_zone)
  assert snake_trap.get_manacost() == 2
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack = list(filter(lambda a: a.source == tundra_rhino and a.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack)
  assert snake_trap.parent == snake_trap.owner.graveyard
  snakes = [c for c in game.current_player.other_player.board if c.name == 'Snake']
  assert len(snakes) == 3
  for snake in snakes:
    assert snake.creature_type == CreatureTypes.BEAST
    assert snake.get_attack() == 1
    assert snake.get_health() == 1


# ---------------------------------------------------------------------------
# 23. Gladiator's Longbow
# ---------------------------------------------------------------------------

def test_gladiators_longbow_no_counter_damage_while_attacking():
  game = GameManager().create_test_game()
  bow = game.game_manager.get_card("Gladiator's Longbow", game.current_player)
  assert bow.get_manacost() == 7
  assert bow.get_attack() == 5
  assert bow.get_health() == 2
  assert bow.has_attribute(Attributes.IMMUNE)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack = list(filter(lambda a: a.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack)
  assert game.current_player.get_health() == 30  # hero took no counter damage

def test_gladiators_longbow_hero_still_vulnerable_to_other_damage():
  # engine implements Immune narrowly as "no counter damage from the attacked
  # target during this specific attack" rather than a real Immune status - the
  # hero is still a normal damage target for anything else that same turn.
  game = GameManager().create_test_game()
  game.game_manager.get_card("Gladiator's Longbow", game.current_player)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack = list(filter(lambda a: a.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack)
  game.deal_damage(game.current_player, 10)
  assert game.current_player.get_health() == 20


# ---------------------------------------------------------------------------
# 24. King Krush
# ---------------------------------------------------------------------------

def test_king_krush_stats_and_charge():
  game = GameManager().create_test_game()
  king_krush = game.game_manager.get_card('King Krush', game.current_player.board)
  assert king_krush.get_manacost() == 9
  assert king_krush.get_attack() == 8
  assert king_krush.get_health() == 8
  assert king_krush.creature_type == CreatureTypes.BEAST
  assert king_krush.has_attribute(Attributes.CHARGE)
  attack_actions = list(filter(lambda a: a.source == king_krush and a.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(attack_actions) > 0
