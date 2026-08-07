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

# Audit slice: get_warrior_cards() indices 0..24 - the ENTIRE warrior list
# (Execute, Whirlwind, Cleave, Fiery War Axe, Heroic Strike, Charge, Shield Block,
#  Warsong Commander, Kor'kron Elite, Arcanite Reaper, Inner Rage, Battle Rage,
#  Cruel Taskmaster, Rampage, Slam, Arathi Weaponsmith, Upgrade!, Armorsmith,
#  Commanding Shout, Frothing Berserker, Mortal Strike, Shield Slam, Brawl,
#  Gorehowl, Grommash Hellscream)
# Ground truth: examples/validation/data/hsreplay_classic/cards.collectible.json, set == "VANILLA"
#
# Note: tests/card_tests.py already has extensive per-card coverage for this
# slice (test_execute, test_whirlwind, ... test_gorehowl_face,
# test_grommash_hellscream_enrage). Tests here focus on (a) stats/behavior
# sanity per card so the slice is self-contained, and (b) new combo/edge
# cases and mismatches found while auditing against VANILLA text that are
# NOT already covered by card_tests.py.


# --- Execute (1 mana, "Destroy a damaged enemy minion.") --------------------

def test_execute_stats_and_basic_kill():
  game = GameManager().create_test_game()
  execute = game.game_manager.get_card('Execute', game.current_player.hand)
  assert execute.get_manacost() == 1
  enemy_watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.other_player.board)
  game.deal_damage(enemy_watcher, 1)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == execute][0]
  game.perform_action(cast)
  assert enemy_watcher.parent == enemy_watcher.owner.graveyard

def test_execute_cannot_target_friendly_minion():
  game = GameManager().create_test_game()
  execute = game.game_manager.get_card('Execute', game.current_player.hand)
  friendly_watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.board)
  game.deal_damage(friendly_watcher, 1)
  actions = [a for a in game.get_available_actions(game.current_player) if a.source == execute]
  assert len(actions) == 0 #real Execute should offer no legal target here (only enemy minions qualify)


# --- Whirlwind (1 mana, "Deal $1 damage to ALL minions.") -------------------

def test_whirlwind_hits_both_boards():
  game = GameManager().create_test_game()
  whirlwind = game.game_manager.get_card('Whirlwind', game.current_player.hand)
  assert whirlwind.get_manacost() == 1
  friendly = game.game_manager.get_card('Ancient Watcher', game.current_player.board)
  enemy = game.game_manager.get_card('Ancient Watcher', game.current_player.other_player.board)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == whirlwind][0]
  game.perform_action(cast)
  assert friendly.get_health() == 4
  assert enemy.get_health() == 4


# --- Cleave (2 mana, "Deal $2 damage to two random enemy minions.") --------

def test_cleave_cost_and_enemy_only():
  game = GameManager().create_test_game()
  cleave = game.game_manager.get_card('Cleave', game.current_player.hand)
  assert cleave.get_manacost() == 2
  friendly_watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.board)
  enemy_watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.other_player.board)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == cleave][0]
  game.perform_action(cast)
  assert friendly_watcher.get_health() == 5 #never a legal Cleave target, untouched
  assert enemy_watcher.get_health() == 3


# --- Fiery War Axe (2 mana, 3/2 weapon) --------------------------------------

def test_fiery_war_axe_stats_and_two_swings():
  game = GameManager().create_test_game()
  axe = game.game_manager.get_card('Fiery War Axe', game.current_player)
  assert axe.get_manacost() == 2
  assert axe.get_attack() == 3
  assert axe.get_health() == 2 #2 durability
  attack1 = [a for a in game.get_available_actions(game.current_player) if a.source == game.current_player][0]
  game.perform_action(attack1)
  assert axe.get_health() == 1
  assert axe.parent == axe.owner
  game.current_player.attacks_this_turn = 0
  attack2 = [a for a in game.get_available_actions(game.current_player) if a.source == game.current_player][0]
  game.perform_action(attack2)
  assert axe.get_health() == 0
  assert axe.parent == axe.owner.graveyard #broken after 2nd swing


# --- Heroic Strike (2 mana, "+4 Attack this turn") ---------------------------

def test_heroic_strike_cost_and_buff():
  game = GameManager().create_test_game()
  heroic_strike = game.game_manager.get_card('Heroic Strike', game.current_player.hand)
  assert heroic_strike.get_manacost() == 2
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == heroic_strike][0]
  game.perform_action(cast)
  assert game.current_player.get_attack() == 4


# --- Charge (3 mana, "+2 Attack and Charge to a friendly minion") ----------

def test_charge_cost_and_enemy_illegal():
  game = GameManager().create_test_game()
  charge = game.game_manager.get_card('Charge', game.current_player.hand)
  assert charge.get_manacost() == 3
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  actions = [a for a in game.get_available_actions(game.current_player) if a.source == charge and a.targets == [enemy_wisp]]
  assert len(actions) == 0 #Charge only targets friendly minions


# --- Shield Block (3 mana, "Gain 5 Armor. Draw a card.") --------------------

def test_shield_block_cost():
  game = GameManager().create_test_game()
  shield_block = game.game_manager.get_card('Shield Block', game.current_player.hand)
  assert shield_block.get_manacost() == 3


# --- Warsong Commander (3 mana 2/3, charge minions summoned with <=3 attack) -

def test_warsong_commander_stats():
  game = GameManager().create_test_game()
  warsong = game.game_manager.get_card('Warsong Commander', game.current_player.board)
  assert warsong.get_manacost() == 3
  assert warsong.get_attack() == 2
  assert warsong.get_health() == 3

def test_warsong_commander_boundary_four_attack_no_charge():
  #Ancient Watcher is a stand-in 4-attack minion: real Warsong text is
  #"3 or less Attack" so a 4-attack minion must NOT get Charge
  game = GameManager().create_test_game()
  warsong = game.game_manager.get_card('Warsong Commander', game.current_player.board)
  watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == watcher][0]
  game.perform_action(cast)
  assert watcher.get_attack() == 4
  assert not watcher.has_attribute(Attributes.CHARGE)


# --- Kor'kron Elite (4 mana 4/3 Charge) --------------------------------------

def test_korkron_elite_stats():
  game = GameManager().create_test_game()
  korkron = game.game_manager.get_card("Kor'kron Elite", game.current_player.board)
  assert korkron.get_manacost() == 4
  assert korkron.get_attack() == 4
  assert korkron.get_health() == 3
  assert korkron.has_attribute(Attributes.CHARGE)


# --- Arcanite Reaper (5 mana, 5/2 weapon) ------------------------------------

def test_arcanite_reaper_stats():
  game = GameManager().create_test_game()
  reaper = game.game_manager.get_card('Arcanite Reaper', game.current_player)
  assert reaper.get_manacost() == 5
  assert reaper.get_attack() == 5
  assert reaper.get_health() == 2


# --- Inner Rage (0 mana, "Deal 1 damage to a minion and give it +2 Attack") --

def test_inner_rage_cost_and_unrestricted_target():
  game = GameManager().create_test_game()
  inner_rage = game.game_manager.get_card('Inner Rage', game.current_player.hand)
  assert inner_rage.get_manacost() == 0
  friendly_watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.board)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == inner_rage and a.targets == [friendly_watcher]][0]
  game.perform_action(cast)
  assert friendly_watcher.get_health() == 4
  assert friendly_watcher.get_attack() == 6


# --- Battle Rage (2 mana, "Draw a card for each damaged friendly character") -

def test_battle_rage_cost():
  game = GameManager().create_test_game()
  battle_rage = game.game_manager.get_card('Battle Rage', game.current_player.hand)
  assert battle_rage.get_manacost() == 2

def test_battle_rage_hero_damaged_by_one_still_counts():
  game = GameManager().create_test_game()
  battle_rage = game.game_manager.get_card('Battle Rage', game.current_player.hand)
  game.deal_damage(game.current_player, 1)
  assert game.current_player.get_health() == 29
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == battle_rage][0]
  game.perform_action(cast)
  assert len(game.current_player.hand) == 1 #hero is damaged, should draw exactly 1 card


# --- Cruel Taskmaster (2 mana 2/2, Battlecry: 1 dmg + 2 Attack) -------------

def test_cruel_taskmaster_stats():
  game = GameManager().create_test_game()
  cruel = game.game_manager.get_card('Cruel Taskmaster', game.current_player.hand)
  assert cruel.get_manacost() == 2
  assert cruel.attack == 2
  assert cruel.health == 2

def test_cruel_taskmaster_pops_divine_shield_but_still_buffs():
  #combo: damage is absorbed by Divine Shield (no health loss, shield pops)
  #but the "+2 Attack" battlecry clause is independent and still applies
  game = GameManager().create_test_game()
  crusader = game.game_manager.get_card('Scarlet Crusader', game.current_player.board) #3/1 Divine Shield
  assert crusader.has_attribute(Attributes.DIVINE_SHIELD)
  cruel = game.game_manager.get_card('Cruel Taskmaster', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == cruel and a.targets == [crusader]][0]
  game.perform_action(cast)
  assert not crusader.has_attribute(Attributes.DIVINE_SHIELD) #shield popped by the damage
  assert crusader.get_health() == 1 #but no actual health lost
  assert crusader.get_attack() == 5 #3 base + 2 from battlecry


# --- Rampage (2 mana, "Give a damaged minion +3/+3") ------------------------

def test_rampage_cost_and_requires_damaged_target():
  game = GameManager().create_test_game()
  rampage = game.game_manager.get_card('Rampage', game.current_player.hand)
  assert rampage.get_manacost() == 2
  korkron = game.game_manager.get_card("Kor'kron Elite", game.current_player.board)
  actions = [a for a in game.get_available_actions(game.current_player) if a.source == rampage]
  assert len(actions) == 0 #no damaged minions on board yet

def test_rampage_works_on_enemy_minion_too():
  #real Rampage has no friendly/enemy restriction
  game = GameManager().create_test_game()
  rampage = game.game_manager.get_card('Rampage', game.current_player.hand)
  enemy_korkron = game.game_manager.get_card("Kor'kron Elite", game.current_player.other_player.board)
  game.deal_damage(enemy_korkron, 1)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == rampage and a.targets == [enemy_korkron]][0]
  game.perform_action(cast)
  assert enemy_korkron.get_attack() == 7
  assert enemy_korkron.get_health() == 5
  assert enemy_korkron.get_max_health() == 6


# --- Slam (2 mana, "Deal $2 damage to a minion. If it survives, draw.") -----

def test_slam_cost():
  game = GameManager().create_test_game()
  slam = game.game_manager.get_card('Slam', game.current_player.hand)
  assert slam.get_manacost() == 2


# --- Arathi Weaponsmith (4 mana 3/3, Battlecry: Equip a 2/2 weapon) ---------

def test_arathi_weaponsmith_stats():
  game = GameManager().create_test_game()
  smith = game.game_manager.get_card('Arathi Weaponsmith', game.current_player.hand)
  assert smith.get_manacost() == 4
  assert smith.attack == 3
  assert smith.health == 3


# --- Upgrade! (1 mana, weapon +1/+1 or equip 1/3) ---------------------------

def test_upgrade_cost():
  game = GameManager().create_test_game()
  upgrade = game.game_manager.get_card('Upgrade!', game.current_player.hand)
  assert upgrade.get_manacost() == 1


# --- Armorsmith (2 mana 1/4, "friendly minion takes damage -> gain 1 Armor") -

def test_armorsmith_stats():
  game = GameManager().create_test_game()
  armorsmith = game.game_manager.get_card('Armorsmith', game.current_player.board)
  assert armorsmith.get_manacost() == 2
  assert armorsmith.attack == 1
  assert armorsmith.health == 4

def test_armorsmith_removed_by_silence():
  #combo: Silence should strip the triggered ability itself, not just stats
  game = GameManager().create_test_game()
  armorsmith = game.game_manager.get_card('Armorsmith', game.current_player.board)
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  silence = [a for a in game.get_available_actions(game.current_player) if a.source == owl and a.targets == [armorsmith]][0]
  game.perform_action(silence)
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  game.deal_damage(wisp, 1)
  assert game.current_player.armor == 0 #Armorsmith's trigger no longer fires


# --- Commanding Shout (2 mana, "minions can't go below 1 HP this turn, draw")

def test_commanding_shout_cost_and_draw():
  game = GameManager().create_test_game()
  shout = game.game_manager.get_card('Commanding Shout', game.current_player.hand)
  assert shout.get_manacost() == 2
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == shout][0]
  game.perform_action(cast)
  assert len(game.current_player.hand) == 1

def test_commanding_shout_does_not_protect_enemy_minions():
  game = GameManager().create_test_game()
  shout = game.game_manager.get_card('Commanding Shout', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == shout][0]
  game.perform_action(cast)
  game.deal_damage(enemy_wisp, 5)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard #enemy minions still die normally

def test_commanding_shout_expires_end_of_turn():
  game = GameManager().create_test_game()
  shout = game.game_manager.get_card('Commanding Shout', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == shout][0]
  game.perform_action(cast)
  assert game.current_player.has_attribute(Attributes.MINIONS_UNKILLABLE)
  game.end_turn()
  game.untap()
  assert not game.current_player.other_player.has_attribute(Attributes.MINIONS_UNKILLABLE)


# --- Frothing Berserker (3 mana 2/4, "any minion damaged -> +1 Attack") -----

def test_frothing_berserker_stats():
  game = GameManager().create_test_game()
  frothing = game.game_manager.get_card('Frothing Berserker', game.current_player.board)
  assert frothing.get_manacost() == 3
  assert frothing.attack == 2
  assert frothing.health == 4

def test_frothing_berserker_buff_removed_by_silence():
  #combo: Silence must revert the ChangeStats-based combat buff (this is the
  #"already fixed" half of the documented Silence limitation - only
  #SetStats/SwapStats are known-broken, plain ChangeStats should revert fine)
  game = GameManager().create_test_game()
  frothing = game.game_manager.get_card('Frothing Berserker', game.current_player.board)
  whirlwind = game.game_manager.get_card('Whirlwind', game.current_player.hand)
  cast_ww = [a for a in game.get_available_actions(game.current_player) if a.source == whirlwind][0]
  game.perform_action(cast_ww)
  assert frothing.get_attack() == 3 #2 base + 1 from taking whirlwind damage itself
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  silence = [a for a in game.get_available_actions(game.current_player) if a.source == owl and a.targets == [frothing]][0]
  game.perform_action(silence)
  assert frothing.get_attack() == 2 #buff reverted back to base


# --- Mortal Strike (4 mana, 4 dmg or 6 dmg if <=12 health) ------------------

def test_mortal_strike_cost():
  game = GameManager().create_test_game()
  mortal_strike = game.game_manager.get_card('Mortal Strike', game.current_player.hand)
  assert mortal_strike.get_manacost() == 4

def test_mortal_strike_armor_does_not_count_toward_health_threshold():
  #combo: armor absorbs damage before health, so "12 or less Health" must be
  #evaluated on health lost, not on raw damage dealt through armor
  game = GameManager().create_test_game()
  mortal_strike = game.game_manager.get_card('Mortal Strike', game.current_player.hand)
  game.current_player.armor = 10
  game.deal_damage(game.current_player, 20) #10 eaten by armor, 10 to health -> health 20
  assert game.current_player.get_health() == 20
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == mortal_strike and a.targets[0] == game.current_player.other_player][0]
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 26 #base 4 damage, threshold not met

def test_mortal_strike_boundary_exactly_12_health_deals_6():
  game = GameManager().create_test_game()
  mortal_strike = game.game_manager.get_card('Mortal Strike', game.current_player.hand)
  game.deal_damage(game.current_player, 18) #health 30 -> 12, exactly at threshold
  assert game.current_player.get_health() == 12
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == mortal_strike and a.targets[0] == game.current_player.other_player][0]
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 24 #enhanced 6 damage at exactly 12 health


# --- Shield Slam (1 mana, "1 dmg to a minion per Armor you have") -----------

def test_shield_slam_cost_and_zero_armor_still_castable():
  game = GameManager().create_test_game()
  shield_slam = game.game_manager.get_card('Shield Slam', game.current_player.hand)
  assert shield_slam.get_manacost() == 1
  assert game.current_player.armor == 0
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  actions = [a for a in game.get_available_actions(game.current_player) if a.source == shield_slam]
  assert len(actions) == 1 #still targetable with 0 armor, just deals 0 damage
  game.perform_action(actions[0])
  assert enemy_wisp.get_health() == 1


# --- Brawl (5 mana, "Destroy all minions except one (random)") -------------

def test_brawl_cost():
  game = GameManager().create_test_game()
  brawl = game.game_manager.get_card('Brawl', game.current_player.hand)
  assert brawl.get_manacost() == 5


# --- Gorehowl (7 mana, 7/1, "attacking a minion costs Attack not Durability")

def test_gorehowl_stats():
  game = GameManager().create_test_game()
  gorehowl = game.game_manager.get_card('Gorehowl', game.current_player)
  assert gorehowl.get_manacost() == 7
  assert gorehowl.get_attack() == 7
  assert gorehowl.get_health() == 1
  assert gorehowl.has_attribute(Attributes.ATTACK_AS_DURABILITY)


# --- Grommash Hellscream (8 mana 4/9 Charge, "Enrage: +6 Attack") ----------

def test_grommash_stats_and_charge():
  game = GameManager().create_test_game()
  grommash = game.game_manager.get_card('Grommash Hellscream', game.current_player.board)
  assert grommash.get_manacost() == 8
  assert grommash.get_attack() == 4
  assert grommash.get_health() == 9
  assert grommash.has_attribute(Attributes.CHARGE)

def test_grommash_enrage_does_not_stack_across_multiple_hits():
  game = GameManager().create_test_game()
  grommash = game.game_manager.get_card('Grommash Hellscream', game.current_player.board)
  game.deal_damage(grommash, 1)
  assert grommash.get_attack() == 10 #4 base + 6 enrage
  game.deal_damage(grommash, 1) #second, separate hit - still just damaged, not "more" damaged
  assert grommash.get_attack() == 10 #should still be flat +6, not stacking to 16
