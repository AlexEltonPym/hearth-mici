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
# Audit slice: common cards 20..39 (0-indexed) from get_common_cards()
#   20 Jungle Panther        25 Ancient Brewmaster   30 Silvermoon Guardian
#   21 Raging Worgen         26 Cult Master          31 Spellbreaker
#   22 Scarlet Crusader      27 Dark Iron Dwarf       32 Fen Creeper
#   23 Tauren Warrior        28 Dread Corsair         33 Silver Hand Knight
#   24 Thrallmar Farseer     29 Mogu'shan Warden      34 Spiteful Smith
#                                                     35 Stranglethorn Tiger
#                                                     36 Venture Co. Mercenary
#                                                     37 Frost Elemental
#                                                     38 Priestess of Elune
#                                                     39 Windfury Harpy
# =============================================================================


# --- Jungle Panther (3 mana 4/2 Beast, Stealth) -----------------------------

def test_jungle_panther_stats_and_stealth():
  game = GameManager().create_test_game()
  panther = game.game_manager.get_card('Jungle Panther', game.current_player.board)
  assert panther.get_manacost() == 3
  assert panther.get_attack() == 4
  assert panther.get_health() == 2
  assert panther.creature_type == CreatureTypes.BEAST
  assert panther.has_attribute(Attributes.STEALTH)

def test_jungle_panther_stealth_blocks_enemy_targeted_spell_then_lost_on_attack():
  game = GameManager().create_test_game()
  panther = game.game_manager.get_card('Jungle Panther', game.current_player.other_player.board)
  panther.attacks_this_turn = 0
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  # a stealthed enemy minion must not be offered as a targeted-spell target
  fireball_targets = [a.targets[0] for a in game.get_available_actions(game.current_player) if a.source == fireball]
  assert panther not in fireball_targets

  # panther attacks -> loses stealth
  attack_actions = [a for a in game.get_available_actions(game.current_player.other_player) if a.source == panther]
  assert len(attack_actions) == 1
  game.perform_action(attack_actions[0])
  assert not panther.has_attribute(Attributes.STEALTH)


# --- Raging Worgen (3/3/3, Enrage: Windfury + +1 Attack) --------------------

def test_raging_worgen_enrage_grants_windfury_and_attack():
  game = GameManager().create_test_game()
  worgen = game.game_manager.get_card('Raging Worgen', game.current_player.board)
  assert worgen.get_manacost() == 3
  assert worgen.get_attack() == 3
  assert worgen.get_health() == 3
  assert not worgen.has_attribute(Attributes.WINDFURY)
  game.deal_damage(worgen, 1)
  assert worgen.get_attack() == 4
  assert worgen.has_attribute(Attributes.WINDFURY)
  # enrage clears once healed back to full
  worgen.health = worgen.get_max_health()
  assert worgen.get_health() == 3
  assert worgen.get_attack() == 3
  assert not worgen.has_attribute(Attributes.WINDFURY)

def test_raging_worgen_silence_removes_enrage():
  # combo: silence should strip the Enrage condition (engine models enrage as
  # a dynamic Condition cleared by Silence.resolve_action setting condition=None)
  game = GameManager().create_test_game()
  worgen = game.game_manager.get_card('Raging Worgen', game.current_player.board)
  game.deal_damage(worgen, 1)
  assert worgen.get_attack() == 4
  assert worgen.has_attribute(Attributes.WINDFURY)

  spellbreaker = game.game_manager.get_card('Spellbreaker', game.current_player.hand)
  play_spellbreaker = [a for a in game.get_available_actions(game.current_player) if a.source == spellbreaker and a.targets == [worgen]][0]
  game.perform_action(play_spellbreaker)
  assert not worgen.has_attribute(Attributes.WINDFURY)
  assert worgen.get_attack() == 3


# --- Scarlet Crusader (3/1, Divine Shield) ----------------------------------

def test_scarlet_crusader_stats_and_divine_shield():
  game = GameManager().create_test_game()
  scarlet = game.game_manager.get_card('Scarlet Crusader', game.current_player.board)
  assert scarlet.get_manacost() == 3
  assert scarlet.get_attack() == 3
  assert scarlet.get_health() == 1
  assert scarlet.has_attribute(Attributes.DIVINE_SHIELD)
  game.deal_damage(scarlet, 1)
  assert not scarlet.has_attribute(Attributes.DIVINE_SHIELD)
  assert scarlet.get_health() == 1  # shield absorbed the hit entirely


# --- Tauren Warrior (2/3, Taunt, Enrage: +3 Attack) -------------------------

def test_tauren_warrior_taunt_and_enrage():
  game = GameManager().create_test_game()
  tauren = game.game_manager.get_card('Tauren Warrior', game.current_player.board)
  assert tauren.get_manacost() == 3
  assert tauren.get_attack() == 2
  assert tauren.get_health() == 3
  assert tauren.has_attribute(Attributes.TAUNT)
  game.deal_damage(tauren, 1)
  assert tauren.get_attack() == 5
  assert tauren.has_attribute(Attributes.TAUNT)  # enrage doesn't remove taunt

def test_tauren_warrior_silence_removes_taunt_and_enrage():
  game = GameManager().create_test_game()
  tauren = game.game_manager.get_card('Tauren Warrior', game.current_player.other_player.board)
  game.deal_damage(tauren, 1)
  assert tauren.get_attack() == 5
  spellbreaker = game.game_manager.get_card('Spellbreaker', game.current_player.hand)
  play_spellbreaker = [a for a in game.get_available_actions(game.current_player) if a.source == spellbreaker and a.targets == [tauren]][0]
  game.perform_action(play_spellbreaker)
  assert not tauren.has_attribute(Attributes.TAUNT)
  assert tauren.get_attack() == 2  # enrage bonus gone too


# --- Thrallmar Farseer (2/3, Windfury) --------------------------------------

def test_thrallmar_farseer_stats_and_windfury():
  game = GameManager().create_test_game()
  farseer = game.game_manager.get_card('Thrallmar Farseer', game.current_player.board)
  assert farseer.get_manacost() == 3
  assert farseer.get_attack() == 2
  assert farseer.get_health() == 3
  assert farseer.has_attribute(Attributes.WINDFURY)
  farseer.attacks_this_turn = 0
  enemy_wisp1 = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  enemy_wisp2 = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack1 = [a for a in game.get_available_actions(game.current_player) if a.source == farseer and a.targets == [enemy_wisp1]][0]
  game.perform_action(attack1)
  attack2 = [a for a in game.get_available_actions(game.current_player) if a.source == farseer and a.targets == [enemy_wisp2]][0]
  game.perform_action(attack2)
  assert farseer.attacks_this_turn == 2
  assert enemy_wisp1.parent == enemy_wisp1.owner.graveyard
  assert enemy_wisp2.parent == enemy_wisp2.owner.graveyard


# --- Ancient Brewmaster (5/4, Battlecry: return a friendly minion to hand) --

def test_ancient_brewmaster_returns_friendly_minion():
  game = GameManager().create_test_game()
  target = game.game_manager.get_card('Fen Creeper', game.current_player.board)
  target.attacks_this_turn = 0
  brewmaster = game.game_manager.get_card('Ancient Brewmaster', game.current_player.hand)
  assert brewmaster.get_manacost() == 4
  assert brewmaster.get_attack() == 5
  assert brewmaster.get_health() == 4
  play_brewmaster = [a for a in game.get_available_actions(game.current_player) if a.source == brewmaster and a.targets == [target]][0]
  game.perform_action(play_brewmaster)
  assert target in game.current_player.hand.get_all()
  assert target not in game.current_player.board.get_all()

def test_ancient_brewmaster_bounce_does_not_trigger_deathrattle():
  # combo: returning a Harvest Golem to hand is a zone change, not a death,
  # so its SummonToken deathrattle must not fire (no Damaged Golem left behind)
  game = GameManager().create_test_game()
  golem = game.game_manager.get_card('Harvest Golem', game.current_player.board)
  golem.attacks_this_turn = 0
  board_size_before = len(game.current_player.board)
  brewmaster = game.game_manager.get_card('Ancient Brewmaster', game.current_player.hand)
  play_brewmaster = [a for a in game.get_available_actions(game.current_player) if a.source == brewmaster and a.targets == [golem]][0]
  game.perform_action(play_brewmaster)
  assert golem in game.current_player.hand.get_all()
  assert not any(c.name == 'Damaged Golem' for c in game.current_player.board)
  assert len(game.current_player.board) == board_size_before - 1 + 1  # golem left, brewmaster entered


# --- Cult Master (4/2, After a friendly minion dies, draw a card) ----------

def test_cult_master_draws_only_on_friendly_death():
  game = GameManager().create_test_game()
  cult_master = game.game_manager.get_card('Cult Master', game.current_player.board)
  assert cult_master.get_manacost() == 4
  assert cult_master.get_attack() == 4
  assert cult_master.get_health() == 2
  assert len(game.current_player.hand) == 0

  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  game.deal_damage(enemy_wisp, 1)
  assert len(game.current_player.hand) == 0  # enemy death: no draw

  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  game.deal_damage(friendly_wisp, 1)
  assert len(game.current_player.hand) == 1

def test_cult_master_does_not_draw_off_its_own_death():
  # edge case: game.trigger() excludes `triggerer == card` (game.py's
  # `trigger` method), so a dying Cult Master does not draw a card for its
  # own death - matching real Hearthstone, where a minion's own death does
  # not trigger its own "after a friendly minion dies" ability.
  game = GameManager().create_test_game()
  cult_master = game.game_manager.get_card('Cult Master', game.current_player.board)
  assert len(game.current_player.hand) == 0
  game.deal_damage(cult_master, 2)
  assert cult_master.parent == cult_master.owner.graveyard
  assert len(game.current_player.hand) == 0


# --- Dark Iron Dwarf (4/4, Battlecry: give a minion +2 Attack this turn) ---

def test_dark_iron_dwarf_temp_buff_expires_end_of_turn():
  game = GameManager().create_test_game()
  dwarf = game.game_manager.get_card('Dark Iron Dwarf', game.current_player.hand)
  assert dwarf.get_manacost() == 4
  assert dwarf.get_attack() == 4
  assert dwarf.get_health() == 4
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  play_dwarf = [a for a in game.get_available_actions(game.current_player) if a.source == dwarf and a.targets == [wisp]][0]
  game.perform_action(play_dwarf)
  assert wisp.get_attack() == 3
  game.end_turn()
  game.end_turn()
  assert wisp.get_attack() == 1


# --- Dread Corsair (3/3 Pirate Taunt, costs less per weapon Attack) ---------

def test_dread_corsair_cost_reduced_by_weapon_attack():
  game = GameManager().create_test_game()
  corsair = game.game_manager.get_card('Dread Corsair', game.current_player.hand)
  assert corsair.get_manacost() == 4
  assert corsair.get_attack() == 3
  assert corsair.get_health() == 3
  assert corsair.creature_type == CreatureTypes.PIRATE
  weapon = game.game_manager.get_card('Generic Weapon', game.current_player)
  assert weapon.get_attack() == 3
  assert corsair.get_manacost() == 1

def test_dread_corsair_has_taunt():
  game = GameManager().create_test_game()
  corsair = game.game_manager.get_card('Dread Corsair', game.current_player.board)
  assert corsair.has_attribute(Attributes.TAUNT)


# --- Mogu'shan Warden (4 mana 1/7 Taunt) ------------------------------------

def test_mogushan_warden_stats_and_taunt():
  game = GameManager().create_test_game()
  warden = game.game_manager.get_card("Mogu'shan Warden", game.current_player.board)
  assert warden.get_manacost() == 4
  assert warden.get_attack() == 1
  assert warden.get_health() == 7
  assert warden.has_attribute(Attributes.TAUNT)


# --- Silvermoon Guardian (4 mana 3/3, Divine Shield) ------------------------

def test_silvermoon_guardian_stats_and_divine_shield():
  game = GameManager().create_test_game()
  guardian = game.game_manager.get_card('Silvermoon Guardian', game.current_player.board)
  assert guardian.get_manacost() == 4
  assert guardian.get_attack() == 3
  assert guardian.get_health() == 3
  assert guardian.has_attribute(Attributes.DIVINE_SHIELD)


# --- Spellbreaker (4 mana 4/3, Battlecry: Silence a minion) ----------------

def test_spellbreaker_silences_enemy_minion():
  game = GameManager().create_test_game()
  taunt_minion = game.game_manager.get_card('Fen Creeper', game.current_player.other_player.board)
  assert taunt_minion.has_attribute(Attributes.TAUNT)
  spellbreaker = game.game_manager.get_card('Spellbreaker', game.current_player.hand)
  assert spellbreaker.get_manacost() == 4
  assert spellbreaker.get_attack() == 4
  assert spellbreaker.get_health() == 3
  play_spellbreaker = [a for a in game.get_available_actions(game.current_player) if a.source == spellbreaker and a.targets == [taunt_minion]][0]
  game.perform_action(play_spellbreaker)
  assert not taunt_minion.has_attribute(Attributes.TAUNT)

def test_spellbreaker_silence_strips_deathrattle():
  # combo: silencing a Harvest Golem must remove its SummonToken deathrattle
  game = GameManager().create_test_game()
  golem = game.game_manager.get_card('Harvest Golem', game.current_player.other_player.board)
  spellbreaker = game.game_manager.get_card('Spellbreaker', game.current_player.hand)
  play_spellbreaker = [a for a in game.get_available_actions(game.current_player) if a.source == spellbreaker and a.targets == [golem]][0]
  game.perform_action(play_spellbreaker)
  assert golem.effect is None
  game.deal_damage(golem, 5)
  assert golem.parent == golem.owner.graveyard
  assert not any(c.name == 'Damaged Golem' for c in golem.owner.board)


# --- Fen Creeper (5 mana 3/6 Taunt) -----------------------------------------

def test_fen_creeper_stats_and_taunt():
  game = GameManager().create_test_game()
  creeper = game.game_manager.get_card('Fen Creeper', game.current_player.board)
  assert creeper.get_manacost() == 5
  assert creeper.get_attack() == 3
  assert creeper.get_health() == 6
  assert creeper.has_attribute(Attributes.TAUNT)


# --- Silver Hand Knight (5 mana 4/4, Battlecry: Summon a 2/2 Squire) -------

def test_silver_hand_knight_summons_squire():
  game = GameManager().create_test_game()
  knight = game.game_manager.get_card('Silver Hand Knight', game.current_player.hand)
  assert knight.get_manacost() == 5
  assert knight.get_attack() == 4
  assert knight.get_health() == 4
  board_before = len(game.current_player.board)
  play_knight = [a for a in game.get_available_actions(game.current_player) if a.source == knight][0]
  game.perform_action(play_knight)
  squires = [c for c in game.current_player.board if c.name == 'Squire']
  assert len(squires) == 1
  assert squires[0].get_attack() == 2
  assert squires[0].get_health() == 2
  assert len(game.current_player.board) == board_before + 2

def test_silver_hand_knight_squire_triggers_knife_juggler():
  game = GameManager().create_test_game()
  knife_juggler = game.game_manager.get_card('Knife Juggler', game.current_player.board)
  knight = game.game_manager.get_card('Silver Hand Knight', game.current_player.hand)
  enemy = game.current_player.other_player
  enemy_health_before = enemy.get_health()
  play_knight = [a for a in game.get_available_actions(game.current_player) if a.source == knight][0]
  game.perform_action(play_knight)
  # Real Hearthstone: Knife Juggler fires twice here - once for the Knight
  # entering play, once for the Squire token it summons - with the enemy
  # board empty, both 1-damage procs land on the enemy hero (2 total).
  # The engine only fires it once (for the Knight), because SummonToken
  # never raises FRIENDLY_MINION_SUMMONED for the Squire it creates.
  assert enemy_health_before - enemy.get_health() == 2


# --- Spiteful Smith (5 mana 4/6, Enrage: weapon +2 Attack) -----------------

def test_spiteful_smith_enrage_buffs_weapon():
  game = GameManager().create_test_game()
  smith = game.game_manager.get_card('Spiteful Smith', game.current_player.board)
  assert smith.get_manacost() == 5
  assert smith.get_attack() == 4
  assert smith.get_health() == 6
  weapon = game.game_manager.get_card('Generic Weapon', game.current_player)
  assert weapon.get_attack() == 3
  game.deal_damage(smith, 1)
  assert weapon.get_attack() == 5
  game.deal_damage(smith, 10)
  assert smith.parent == smith.owner.graveyard
  assert weapon.get_attack() == 3  # smith dead, aura gone

@pytest.mark.xfail(reason="DATA-MISMATCH: Spiteful Smith is missing creature_type=CreatureTypes.UNDEAD vs VANILLA (race: UNDEAD)", strict=False)
def test_spiteful_smith_is_undead():
  game = GameManager().create_test_game()
  smith = game.game_manager.get_card('Spiteful Smith', game.current_player.board)
  assert smith.creature_type == CreatureTypes.UNDEAD


# --- Stranglethorn Tiger (5 mana 5/5 Beast, Stealth) ------------------------

def test_stranglethorn_tiger_stats_and_stealth():
  game = GameManager().create_test_game()
  tiger = game.game_manager.get_card('Stranglethorn Tiger', game.current_player.board)
  assert tiger.get_manacost() == 5
  assert tiger.get_attack() == 5
  assert tiger.get_health() == 5
  assert tiger.creature_type == CreatureTypes.BEAST
  assert tiger.has_attribute(Attributes.STEALTH)


# --- Venture Co. Mercenary (5 mana 7/6, Your minions cost 3 more) ----------

def test_venture_co_mercenary_raises_only_friendly_cost():
  game = GameManager().create_test_game()
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.hand)
  assert friendly_wisp.get_manacost() == 0
  assert enemy_wisp.get_manacost() == 0

  merc = game.game_manager.get_card('Venture Co. Mercenary', game.current_player.board)
  assert merc.get_attack() == 7
  assert merc.get_health() == 6
  assert friendly_wisp.get_manacost() == 3
  assert enemy_wisp.get_manacost() == 0  # not affected: aura is FRIENDLY-only


# --- Frost Elemental (6 mana 5/5, Battlecry: Freeze a character) -----------

def test_frost_elemental_freezes_minion():
  game = GameManager().create_test_game()
  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  frost = game.game_manager.get_card('Frost Elemental', game.current_player.hand)
  assert frost.get_manacost() == 6
  assert frost.get_attack() == 5
  assert frost.get_health() == 5
  cast_frost = [a for a in game.get_available_actions(game.current_player) if a.source == frost and a.targets[0] == wisp][0]
  game.perform_action(cast_frost)
  assert wisp.has_attribute(Attributes.FROZEN)

def test_frost_elemental_freezes_enemy_hero_and_blocks_weapon_attack():
  # combo: freezing the enemy hero should stop a face-attack with their weapon
  game = GameManager().create_test_game()
  enemy = game.current_player.other_player
  weapon = game.game_manager.get_card('Generic Weapon', enemy)
  frost = game.game_manager.get_card('Frost Elemental', game.current_player.hand)
  cast_frost = [a for a in game.get_available_actions(game.current_player) if a.source == frost and a.targets == [enemy]][0]
  game.perform_action(cast_frost)
  assert enemy.has_attribute(Attributes.FROZEN)
  game.end_turn()
  game.untap()
  hero_attacks = [a for a in game.get_available_actions(game.current_player) if a.action_type == Actions.ATTACK and a.source == game.current_player]
  assert len(hero_attacks) == 0


# --- Priestess of Elune (6 mana 5/4, Battlecry: Restore 4 Health to hero) --

def test_priestess_of_elune_heals_friendly_hero():
  game = GameManager().create_test_game()
  priestess = game.game_manager.get_card('Priestess of Elune', game.current_player.hand)
  assert priestess.get_manacost() == 6
  assert priestess.get_attack() == 5
  assert priestess.get_health() == 4
  game.deal_damage(game.current_player, 3)
  assert game.current_player.get_health() == 27
  cast_priestess = [a for a in game.get_available_actions(game.current_player) if a.source == priestess][0]
  game.perform_action(cast_priestess)
  assert game.current_player.get_health() == 30

def test_priestess_of_elune_heal_does_not_overheal():
  game = GameManager().create_test_game()
  priestess = game.game_manager.get_card('Priestess of Elune', game.current_player.hand)
  game.deal_damage(game.current_player, 1)
  assert game.current_player.get_health() == 29
  cast_priestess = [a for a in game.get_available_actions(game.current_player) if a.source == priestess][0]
  game.perform_action(cast_priestess)
  assert game.current_player.get_health() == 30  # capped at hero max health


# --- Windfury Harpy (6 mana 4/5, Windfury) ----------------------------------

def test_windfury_harpy_stats_and_windfury():
  game = GameManager().create_test_game()
  harpy = game.game_manager.get_card('Windfury Harpy', game.current_player.board)
  assert harpy.get_manacost() == 6
  assert harpy.get_attack() == 4
  assert harpy.get_health() == 5
  assert harpy.has_attribute(Attributes.WINDFURY)
