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

# =============================================================================
# Audit slice: common cards 0..19 (0-indexed) from get_common_cards()
#    0 Wisp                 5 Southsea Deckhand    10 Dire Wolf Alpha
#    1 Abusive Sergeant     6 Worgen Infiltrator   11 Faerie Dragon
#    2 Argent Squire        7 Young Dragonhawk     12 Ironbeak Owl
#    3 Leper Gnome          8 Amani Berserker      13 Loot Hoarder
#    4 Shieldbearer         9 Bloodsail Raider     14 Mad Bomber
#                                                   15 Youthful Brewmaster
#                                                   16 Acolyte of Pain
#                                                   17 Earthen Ring Farseer
#                                                   18 Flesheating Ghoul
#                                                   19 Harvest Golem
#
# Ground truth: examples/validation/data/hsreplay_classic/cards.collectible.json,
# entries with "set": "VANILLA" (2014-era text/stats).
# =============================================================================


# --- Wisp (0 mana 1/1, vanilla stats/no minor text) -------------------------

def test_wisp_stats():
  game = GameManager().create_test_game()
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  assert wisp.get_manacost() == 0
  assert wisp.get_attack() == 1
  assert wisp.get_health() == 1
  # VANILLA Wisp has no race (only later reprints gave it Undead)
  assert wisp.creature_type is None


# --- Abusive Sergeant (1 mana 2/1, Battlecry: +2 Attack this turn) ----------

def test_abusive_sergeant_base_stats():
  game = GameManager().create_test_game()
  sergeant = game.game_manager.get_card('Abusive Sergeant', game.current_player.board)
  assert sergeant.get_attack() == 2
  assert sergeant.get_health() == 1

def test_abusive_sergeant_battlecry_temporary_buff():
  game = GameManager().create_test_game()
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  sergeant = game.game_manager.get_card('Abusive Sergeant', game.current_player.hand)
  assert wisp.get_attack() == 1

  buff_action = Action(Actions.CAST_MINION, sergeant, [wisp])
  game.perform_action(buff_action)
  assert wisp.get_attack() == 3  # 1 base + 2 from battlecry

  game.end_turn()
  assert wisp.get_attack() == 1  # "this turn" buff expires


# --- Argent Squire (1 mana 1/1, Divine Shield) -------------------------------

def test_argent_squire_divine_shield_stats():
  game = GameManager().create_test_game()
  squire = game.game_manager.get_card('Argent Squire', game.current_player.board)
  assert squire.get_manacost() == 1
  assert squire.get_attack() == 1
  assert squire.get_health() == 1
  assert squire.has_attribute(Attributes.DIVINE_SHIELD)

def test_argent_squire_silence_removes_divine_shield():
  game = GameManager().create_test_game()
  squire = game.game_manager.get_card('Argent Squire', game.current_player.other_player.board)
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  assert squire.has_attribute(Attributes.DIVINE_SHIELD)

  silence_action = Action(Actions.CAST_MINION, owl, [squire])
  game.perform_action(silence_action)
  assert not squire.has_attribute(Attributes.DIVINE_SHIELD)


# --- Leper Gnome (1 mana 2/1, Deathrattle: deal 2 to enemy hero) ------------

def test_leper_gnome_deathrattle_hits_enemy_hero():
  game = GameManager().create_test_game()
  leper = game.game_manager.get_card('Leper Gnome', game.current_player.board)
  assert leper.get_attack() == 2
  assert leper.get_health() == 1

  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack_action = Action(Actions.ATTACK, leper, [enemy_wisp])
  game.perform_action(attack_action)

  assert leper.parent == leper.owner.graveyard
  assert game.current_player.other_player.get_health() == 28  # 30 - 2 deathrattle


# --- Shieldbearer (1 mana 0/4 Taunt) ----------------------------------------

def test_shieldbearer_taunt_and_no_attack_available():
  game = GameManager().create_test_game()
  shieldbearer = game.game_manager.get_card('Shieldbearer', game.current_player.board)
  assert shieldbearer.get_attack() == 0
  assert shieldbearer.get_health() == 4
  assert shieldbearer.has_attribute(Attributes.TAUNT)

  shieldbearer.attacks_this_turn = 0
  available_actions = game.get_available_actions(game.current_player)
  assert not any(a.action_type == Actions.ATTACK and a.source == shieldbearer for a in available_actions)


# --- Southsea Deckhand (1 mana 2/1 Pirate, Charge while weapon equipped) ----

def test_southsea_deckhand_charge_only_with_weapon():
  game = GameManager().create_test_game()
  deckhand = game.game_manager.get_card('Southsea Deckhand', game.current_player.board)
  assert deckhand.creature_type == CreatureTypes.PIRATE
  assert not deckhand.has_attribute(Attributes.CHARGE)
  assert len(list(filter(lambda a: a.action_type == Actions.ATTACK and a.source == deckhand, game.get_available_actions(game.current_player)))) == 0

  game.game_manager.get_card('Generic Weapon', game.current_player)
  assert deckhand.has_attribute(Attributes.CHARGE)
  assert len(list(filter(lambda a: a.action_type == Actions.ATTACK and a.source == deckhand, game.get_available_actions(game.current_player)))) > 0


# --- Worgen Infiltrator (1 mana 2/1, Stealth) -------------------------------

def test_worgen_infiltrator_stats_and_stealth():
  game = GameManager().create_test_game()
  worgen = game.game_manager.get_card('Worgen Infiltrator', game.current_player.board)
  assert worgen.get_manacost() == 1
  assert worgen.get_attack() == 2
  assert worgen.get_health() == 1
  assert worgen.has_attribute(Attributes.STEALTH)


# --- Young Dragonhawk (1 mana 1/1 Beast, Windfury) --------------------------

def test_young_dragonhawk_windfury():
  game = GameManager().create_test_game()
  dragonhawk = game.game_manager.get_card('Young Dragonhawk', game.current_player.board)
  assert dragonhawk.get_attack() == 1
  assert dragonhawk.get_health() == 1
  assert dragonhawk.has_attribute(Attributes.WINDFURY)

def test_young_dragonhawk_is_beast():
  game = GameManager().create_test_game()
  dragonhawk = game.game_manager.get_card('Young Dragonhawk', game.current_player.board)
  assert dragonhawk.creature_type == CreatureTypes.BEAST


# --- Amani Berserker (2 mana 2/3, Enrage: +3 Attack while damaged) ---------

def test_amani_berserker_enrage_on_damage():
  game = GameManager().create_test_game()
  berserker = game.game_manager.get_card('Amani Berserker', game.current_player.board)
  assert berserker.get_attack() == 2
  game.deal_damage(berserker, 1)
  assert berserker.get_attack() == 5  # 2 base + 3 enrage
  # healing back to full should remove the enrage bonus
  berserker.health = berserker.get_max_health()
  assert berserker.get_attack() == 2

def test_amani_berserker_enrage_removed_by_silence():
  game = GameManager().create_test_game()
  berserker = game.game_manager.get_card('Amani Berserker', game.current_player.other_player.board)
  game.deal_damage(berserker, 1)
  assert berserker.get_attack() == 5

  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  silence_action = Action(Actions.CAST_MINION, owl, [berserker])
  game.perform_action(silence_action)
  assert berserker.get_attack() == 2  # enrage condition silenced away


# --- Bloodsail Raider (2 mana 2/3 Pirate, Battlecry: gain Attack = weapon Attack)

def test_bloodsail_raider_battlecry_no_weapon():
  game = GameManager().create_test_game()
  raider = game.game_manager.get_card('Bloodsail Raider', game.current_player.hand)
  assert game.current_player.weapon is None

  cast_action = Action(Actions.CAST_MINION, raider, [raider])
  game.perform_action(cast_action)
  assert raider.get_attack() == 2  # no weapon -> +0
  assert raider.creature_type == CreatureTypes.PIRATE

def test_bloodsail_raider_battlecry_with_weapon():
  game = GameManager().create_test_game()
  game.game_manager.get_card('Generic Weapon', game.current_player)  # 3 attack weapon
  raider = game.game_manager.get_card('Bloodsail Raider', game.current_player.hand)

  cast_action = Action(Actions.CAST_MINION, raider, [raider])
  game.perform_action(cast_action)
  assert raider.get_attack() == 5  # 2 base + 3 from weapon


# --- Dire Wolf Alpha (2 mana 2/2 Beast, adjacent minions +1 Attack) --------

def test_dire_wolf_alpha_buffs_adjacent_minions():
  game = GameManager().create_test_game()
  # 4 minions so the "not adjacent" wisp doesn't also sit at the far board edge
  # (edge-to-edge wraparound is a separate, known-buggy case - see
  # test_dire_wolf_alpha_board_is_not_circular below).
  wolf = game.game_manager.get_card('Dire Wolf Alpha', game.current_player.board)
  first_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  second_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  game.game_manager.get_card('Wisp', game.current_player.board)

  assert wolf.get_attack() == 2
  assert first_wisp.get_attack() == 2  # adjacent to wolf
  assert second_wisp.get_attack() == 1  # not adjacent to wolf

def test_dire_wolf_alpha_is_beast():
  game = GameManager().create_test_game()
  wolf = game.game_manager.get_card('Dire Wolf Alpha', game.current_player.board)
  assert wolf.creature_type == CreatureTypes.BEAST

def test_dire_wolf_alpha_board_is_not_circular():
  game = GameManager().create_test_game()
  wolf = game.game_manager.get_card('Dire Wolf Alpha', game.current_player.board)          # index 0
  middle_wisp = game.game_manager.get_card('Wisp', game.current_player.board)              # index 1 (adjacent)
  far_wisp = game.game_manager.get_card('Wisp', game.current_player.board)                 # index 2 (far end)

  assert middle_wisp.get_attack() == 2   # correctly adjacent
  assert far_wisp.get_attack() == 1      # NOT adjacent - should not be buffed


# --- Faerie Dragon (2 mana 3/2 Dragon, Elusive/Hexproof) --------------------

def test_faerie_dragon_stats_and_hexproof_blocks_targeted_spell():
  game = GameManager().create_test_game()
  game.player.hand.clear()
  game.enemy.hand.clear()
  game.enemy.current_mana = 10

  faerie = game.game_manager.get_card('Faerie Dragon', game.player.board)
  assert faerie.get_manacost() == 2
  assert faerie.get_attack() == 3
  assert faerie.get_health() == 2
  assert faerie.creature_type == CreatureTypes.DRAGON
  assert faerie.has_attribute(Attributes.HEXPROOF)

  fireball = game.game_manager.get_card('Fireball', game.enemy.hand)
  available_actions = game.get_available_actions(game.enemy)
  fireball_targets = [a.targets[0] for a in available_actions
                       if a.action_type == Actions.CAST_SPELL and a.source == fireball]
  assert faerie not in fireball_targets


# --- Ironbeak Owl (2 mana 2/1 Beast, Battlecry: Silence a minion) ----------

def test_ironbeak_owl_stats():
  game = GameManager().create_test_game()
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.board)
  assert owl.get_manacost() == 2
  assert owl.get_attack() == 2
  assert owl.get_health() == 1
  assert owl.creature_type == CreatureTypes.BEAST

def test_ironbeak_owl_silences_taunt():
  game = GameManager().create_test_game()
  taunter = game.game_manager.get_card('Shieldbearer', game.current_player.other_player.board)
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  assert taunter.has_attribute(Attributes.TAUNT)

  silence_action = Action(Actions.CAST_MINION, owl, [taunter])
  game.perform_action(silence_action)
  assert not taunter.has_attribute(Attributes.TAUNT)


# --- Loot Hoarder (2 mana 2/1, Deathrattle: draw a card) --------------------

def test_loot_hoarder_deathrattle_draws_a_card():
  game = GameManager().create_test_game()
  hoarder = game.game_manager.get_card('Loot Hoarder', game.current_player.board)
  assert hoarder.get_attack() == 2
  assert hoarder.get_health() == 1
  starting_hand_size = len(game.current_player.hand)

  fireblast_action = Action(action_type=Actions.CAST_HERO_POWER, source=game.enemy.hero_power, targets=[hoarder])
  game.perform_action(fireblast_action)
  assert hoarder.parent == hoarder.owner.graveyard
  assert len(game.current_player.hand) == starting_hand_size + 1


# --- Mad Bomber (2 mana 3/2, Battlecry: 3 damage randomly split, excludes self)

def test_mad_bomber_deals_three_damage_total_and_spares_self():
  game = GameManager().create_test_game()
  bomber = game.game_manager.get_card('Mad Bomber', game.current_player.hand)
  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  cast_action = [a for a in game.get_available_actions(game.current_player) if a.source == bomber][0]
  game.perform_action(cast_action)

  wisp_damage = wisp.get_max_health() - wisp.get_health()
  player_damage = game.current_player.get_max_health() - game.current_player.get_health()
  enemy_damage = game.current_player.other_player.get_max_health() - game.current_player.other_player.get_health()
  assert wisp_damage + player_damage + enemy_damage == 3
  # the bomber itself is never a valid random target ("all OTHER characters")
  assert bomber.get_health() == bomber.get_max_health()


# --- Youthful Brewmaster (2 mana 3/2, Battlecry: return friendly minion to hand)

def test_youthful_brewmaster_returns_minion_and_resets_buffs():
  game = GameManager().create_test_game()
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  sergeant = game.game_manager.get_card('Abusive Sergeant', game.current_player.hand)
  game.perform_action(Action(Actions.CAST_MINION, sergeant, [wisp]))
  assert wisp.get_attack() == wisp.attack + 2  # buffed this turn

  brewmaster = game.game_manager.get_card('Youthful Brewmaster', game.current_player.hand)
  game.perform_action(Action(Actions.CAST_MINION, brewmaster, [wisp]))

  assert wisp.parent == game.current_player.hand
  assert wisp not in game.current_player.board
  assert wisp.get_attack() == wisp.original_attack  # temp buff cleared by return-to-hand reset


# --- Acolyte of Pain (3 mana 1/3, whenever damaged draw a card) ------------

def test_acolyte_of_pain_stats_match_vanilla():
  game = GameManager().create_test_game()
  acolyte = game.game_manager.get_card('Acolyte of Pain', game.current_player.board)
  assert acolyte.get_attack() == 1
  assert acolyte.get_health() == 3  # VANILLA (2014) health is 3, not the later-reprint 4

def test_acolyte_of_pain_draws_on_each_damage_instance():
  game = GameManager().create_test_game()
  acolyte = game.game_manager.get_card('Acolyte of Pain', game.current_player.board)
  starting_hand_size = len(game.current_player.hand)
  game.deal_damage(acolyte, 1)
  assert len(game.current_player.hand) == starting_hand_size + 1
  game.deal_damage(acolyte, 1)
  assert len(game.current_player.hand) == starting_hand_size + 2
  game.deal_damage(acolyte, 1)
  assert len(game.current_player.hand) == starting_hand_size + 3
  assert acolyte.parent == acolyte.owner.graveyard


# --- Earthen Ring Farseer (3 mana 3/3, Battlecry: restore 3 health) --------

def test_earthen_ring_farseer_battlecry_heals_target():
  game = GameManager().create_test_game()
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  wisp.health = 1  # simulate damage without killing it (max health defaults higher via test wisp? keep simple)
  game.deal_damage(wisp, 0)  # no-op, just ensure wisp alive
  # use a sturdier minion so we can meaningfully test healing under max health
  golem = game.game_manager.get_card("Shieldbearer", game.current_player.board)
  game.deal_damage(golem, 2)
  assert golem.get_health() == 2

  farseer = game.game_manager.get_card('Earthen Ring Farseer', game.current_player.hand)
  cast_action = Action(Actions.CAST_MINION, farseer, [golem])
  game.perform_action(cast_action)
  assert golem.get_health() == 4  # healed back to full (2 + 3 capped at max 4)


# --- Flesheating Ghoul (3 mana 2/3, whenever a minion dies +1 Attack) ------

def test_flesheating_ghoul_gains_attack_on_any_minion_death():
  game = GameManager().create_test_game()
  ghoul = game.game_manager.get_card('Flesheating Ghoul', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  assert ghoul.get_attack() == 2
  assert ghoul.creature_type is None  # VANILLA Flesheating Ghoul has no race (later reprints gave it Undead)

  game.deal_damage(enemy_wisp, 1)  # kills the enemy wisp
  assert ghoul.get_attack() == 3

  game.deal_damage(friendly_wisp, 1)  # a friendly death should also trigger it
  assert ghoul.get_attack() == 4


# --- Harvest Golem (3 mana 2/3 Mech, Deathrattle: summon a 2/1 Damaged Golem)

def test_harvest_golem_deathrattle_summons_damaged_golem():
  game = GameManager().create_test_game()
  golem = game.game_manager.get_card('Harvest Golem', game.current_player.board)
  assert golem.get_attack() == 2
  assert golem.get_health() == 3
  assert golem.creature_type == CreatureTypes.MECH

  game.deal_damage(golem, 3)
  assert golem.parent == golem.owner.graveyard

  damaged_golems = [c for c in game.current_player.board if c.name == 'Damaged Golem']
  assert len(damaged_golems) == 1
  assert damaged_golems[0].get_attack() == 2
  assert damaged_golems[0].get_health() == 1
