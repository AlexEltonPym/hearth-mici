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
from action import Action

from game_manager import GameManager


# ---------------------------------------------------------------------------
# Slice: basic cards 22..42 (Wolfrider .. War Golem)
# Ground truth: examples/validation/data/hsreplay_classic/cards.collectible.json, "set": "VANILLA"
# ---------------------------------------------------------------------------


def cast_action_for(game, source):
  """Find the (unique, no-target-choice-needed) available action that plays `source`."""
  actions = list(filter(lambda action: action.source == source, game.get_available_actions(game.current_player)))
  assert len(actions) >= 1, f"No playable action found for {source.name}"
  return actions[0]


# ---- Wolfrider (3 mana 3/1 Charge) ----------------------------------------

def test_wolfrider_stats():
  game = GameManager().create_test_game()
  wolfrider = game.game_manager.get_card('Wolfrider', game.current_player.board)
  assert wolfrider.manacost == 3
  assert wolfrider.get_attack() == 3
  assert wolfrider.get_health() == 1
  assert wolfrider.has_attribute(Attributes.CHARGE)

def test_wolfrider_can_attack_same_turn_charge():
  game = GameManager().create_test_game()
  wolfrider = game.game_manager.get_card('Wolfrider', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  play_wolfrider = cast_action_for(game, wolfrider)
  game.perform_action(play_wolfrider)
  attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK and action.source == wolfrider,
                                game.get_available_actions(game.current_player)))
  assert len(attack_actions) > 0


# ---- Chillwind Yeti (4 mana 4/5 vanilla) -----------------------------------

def test_chillwind_yeti_stats():
  game = GameManager().create_test_game()
  yeti = game.game_manager.get_card('Chillwind Yeti', game.current_player.board)
  assert yeti.manacost == 4
  assert yeti.get_attack() == 4
  assert yeti.get_health() == 5
  assert yeti.effect is None
  assert yeti.attributes == []


# ---- Dragonling Mechanic (4 mana 2/4, Battlecry: summon 2/1 Mechanical Dragonling) ----

def test_dragonling_mechanic_stats():
  game = GameManager().create_test_game()
  mechanic = game.game_manager.get_card('Dragonling Mechanic', game.current_player.board)
  assert mechanic.manacost == 4
  assert mechanic.get_attack() == 2
  assert mechanic.get_health() == 4

def test_dragonling_mechanic_battlecry_summons_token():
  game = GameManager().create_test_game()
  mechanic = game.game_manager.get_card('Dragonling Mechanic', game.current_player.hand)
  assert len(game.current_player.board) == 0
  play_mechanic = cast_action_for(game, mechanic)
  game.perform_action(play_mechanic)
  assert len(game.current_player.board) == 2
  token = [c for c in game.current_player.board if c.name == 'Mechanical Dragonling'][0]
  assert token.get_attack() == 2
  assert token.get_health() == 1
  assert token.creature_type == CreatureTypes.MECH
  assert token.collectable == False

def test_dragonling_mechanic_token_procs_knife_juggler():
  game = GameManager().create_test_game()
  juggler = game.game_manager.get_card('Knife Juggler', game.current_player.board)
  mechanic = game.game_manager.get_card('Dragonling Mechanic', game.current_player.hand)
  assert game.current_player.other_player.get_health() == 30
  play_mechanic = cast_action_for(game, mechanic)
  game.perform_action(play_mechanic)
  # Real Hearthstone: Knife Juggler procs once for the Dragonling Mechanic itself
  # entering play, and once more for the Mechanical Dragonling token -> 2 damage total.
  assert game.current_player.other_player.get_health() == 28


# ---- Gnomish Inventor (4 mana 2/4, Battlecry: Draw a card) -----------------

def test_gnomish_inventor_stats():
  game = GameManager().create_test_game()
  inventor = game.game_manager.get_card('Gnomish Inventor', game.current_player.board)
  assert inventor.manacost == 4
  assert inventor.get_attack() == 2
  assert inventor.get_health() == 4

def test_gnomish_inventor_battlecry_draws_card():
  game = GameManager().create_test_game()
  inventor = game.game_manager.get_card('Gnomish Inventor', game.current_player.hand)
  hand_size_before = len(game.current_player.hand)
  play_inventor = cast_action_for(game, inventor)
  game.perform_action(play_inventor)
  # -1 for the inventor leaving hand to the board, +1 for the drawn card
  assert len(game.current_player.hand) == hand_size_before


# ---- Oasis Snapjaw (4 mana 2/7 Beast, vanilla) -----------------------------

def test_oasis_snapjaw_stats():
  game = GameManager().create_test_game()
  snapjaw = game.game_manager.get_card('Oasis Snapjaw', game.current_player.board)
  assert snapjaw.manacost == 4
  assert snapjaw.get_attack() == 2
  assert snapjaw.get_health() == 7
  assert snapjaw.creature_type == CreatureTypes.BEAST
  assert snapjaw.effect is None


# ---- Ogre Magi (4 mana 4/4, Spell Damage +1) -------------------------------

def test_ogre_magi_stats_and_attribute():
  game = GameManager().create_test_game()
  ogre = game.game_manager.get_card('Ogre Magi', game.current_player.board)
  assert ogre.manacost == 4
  assert ogre.get_attack() == 4
  assert ogre.get_health() == 4
  assert ogre.has_attribute(Attributes.SPELL_DAMAGE)

def test_ogre_magi_boosts_fireball_damage():
  game = GameManager().create_test_game()
  game.game_manager.get_card('Ogre Magi', game.current_player.board)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  target_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  cast_fireball = Action(Actions.CAST_SPELL, fireball, [target_wisp])
  game.perform_action(cast_fireball)
  # Fireball base damage is 6, +1 from Ogre Magi's Spell Damage
  assert target_wisp.get_health() == 1 - 7


# ---- Sen'jin Shieldmasta (4 mana 3/5 Taunt) --------------------------------

def test_senjin_shieldmasta_stats_and_taunt():
  game = GameManager().create_test_game()
  senjin = game.game_manager.get_card("Sen'jin Shieldmasta", game.current_player.other_player.board)
  assert senjin.manacost == 4
  assert senjin.get_attack() == 3
  assert senjin.get_health() == 5
  assert senjin.has_attribute(Attributes.TAUNT)

def test_senjin_shieldmasta_forces_attacks():
  game = GameManager().create_test_game()
  senjin = game.game_manager.get_card("Sen'jin Shieldmasta", game.current_player.other_player.board)
  other_enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  targets = game.get_available_targets(friendly_wisp)
  assert targets == [senjin]


# ---- Stormwind Knight (4 mana 2/5 Charge) ----------------------------------

def test_stormwind_knight_stats():
  game = GameManager().create_test_game()
  knight = game.game_manager.get_card('Stormwind Knight', game.current_player.board)
  assert knight.manacost == 4
  assert knight.get_attack() == 2
  assert knight.get_health() == 5
  assert knight.has_attribute(Attributes.CHARGE)


# ---- Booty Bay Bodyguard (5 mana 5/4 Taunt) --------------------------------

def test_booty_bay_bodyguard_stats_and_taunt():
  game = GameManager().create_test_game()
  bodyguard = game.game_manager.get_card('Booty Bay Bodyguard', game.current_player.board)
  assert bodyguard.manacost == 5
  assert bodyguard.get_attack() == 5
  assert bodyguard.get_health() == 4
  assert bodyguard.has_attribute(Attributes.TAUNT)


# ---- Darkscale Healer (5 mana 4/5, Battlecry: restore 2 to all friendly) ---

def test_darkscale_healer_stats():
  game = GameManager().create_test_game()
  healer = game.game_manager.get_card('Darkscale Healer', game.current_player.board)
  assert healer.manacost == 5
  assert healer.get_attack() == 4
  assert healer.get_health() == 5

def test_darkscale_healer_heals_friendly_minions_and_hero_not_enemy():
  game = GameManager().create_test_game()
  healer = game.game_manager.get_card('Darkscale Healer', game.current_player.hand)
  friendly_snapjaw = game.game_manager.get_card('Oasis Snapjaw', game.current_player.board)  # 2/7
  enemy_snapjaw = game.game_manager.get_card('Oasis Snapjaw', game.current_player.other_player.board)  # 2/7
  game.deal_damage(friendly_snapjaw, 2)
  game.deal_damage(enemy_snapjaw, 2)
  game.deal_damage(game.current_player, 5)
  assert friendly_snapjaw.get_health() == 5
  assert game.current_player.get_health() == 25
  play_healer = cast_action_for(game, healer)
  game.perform_action(play_healer)
  # friendly minion healed by 2, within its max health
  assert friendly_snapjaw.get_health() == 7
  # enemy minion untouched
  assert enemy_snapjaw.get_health() == 5
  # friendly hero healed by 2
  assert game.current_player.get_health() == 27

def test_darkscale_healer_does_not_overheal_past_max():
  game = GameManager().create_test_game()
  healer = game.game_manager.get_card('Darkscale Healer', game.current_player.hand)
  yeti = game.game_manager.get_card('Chillwind Yeti', game.current_player.board)
  game.deal_damage(yeti, 1)
  assert yeti.get_health() == 4
  play_healer = cast_action_for(game, healer)
  game.perform_action(play_healer)
  # 4 + 2 healing would be 6, but max health is 5
  assert yeti.get_health() == 5
  assert yeti.get_max_health() == 5


# ---- Frostwolf Warlord (5 mana 4/4, Battlecry: +1/+1 per other friendly minion) ----

def test_frostwolf_warlord_stats():
  game = GameManager().create_test_game()
  warlord = game.game_manager.get_card('Frostwolf Warlord', game.current_player.board)
  assert warlord.manacost == 5
  assert warlord.get_attack() == 4
  assert warlord.get_health() == 4

def test_frostwolf_warlord_no_other_minions_no_buff():
  game = GameManager().create_test_game()
  warlord = game.game_manager.get_card('Frostwolf Warlord', game.current_player.hand)
  play_warlord = cast_action_for(game, warlord)
  game.perform_action(play_warlord)
  assert warlord.get_attack() == 4
  assert warlord.get_health() == 4

def test_frostwolf_warlord_only_counts_friendly_others():
  game = GameManager().create_test_game()
  warlord = game.game_manager.get_card('Frostwolf Warlord', game.current_player.hand)
  game.game_manager.get_card('Wisp', game.current_player.board)
  game.game_manager.get_card('Wisp', game.current_player.board)
  game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  play_warlord = cast_action_for(game, warlord)
  game.perform_action(play_warlord)
  # +1/+1 for each of the 2 other FRIENDLY minions only, enemy minions don't count
  assert warlord.get_attack() == 6
  assert warlord.get_health() == 6


# ---- Gurubashi Berserker (5 mana 2/7, gains +3 attack whenever it takes damage) ----

def test_gurubashi_berserker_stats():
  game = GameManager().create_test_game()
  berserker = game.game_manager.get_card('Gurubashi Berserker', game.current_player.board)
  assert berserker.manacost == 5
  assert berserker.get_attack() == 2
  assert berserker.get_health() == 7

def test_gurubashi_berserker_healing_does_not_trigger_gain():
  game = GameManager().create_test_game()
  berserker = game.game_manager.get_card('Gurubashi Berserker', game.current_player.board)
  game.deal_damage(berserker, 2)
  assert berserker.get_attack() == 5
  assert berserker.get_health() == 5
  healer = game.game_manager.get_card('Darkscale Healer', game.current_player.hand)
  play_healer = cast_action_for(game, healer)
  game.perform_action(play_healer)
  assert berserker.get_health() == 7  # healed back to full
  assert berserker.get_attack() == 5  # healing must not proc another +3


# ---- Nightblade (5 mana 4/4, Battlecry: deal 3 to the enemy hero) ---------

def test_nightblade_stats():
  game = GameManager().create_test_game()
  nightblade = game.game_manager.get_card('Nightblade', game.current_player.board)
  assert nightblade.manacost == 5
  assert nightblade.get_attack() == 4
  assert nightblade.get_health() == 4

def test_nightblade_battlecry_not_boosted_by_spell_damage():
  game = GameManager().create_test_game()
  game.game_manager.get_card('Archmage', game.current_player.board)  # Spell Damage +1
  nightblade = game.game_manager.get_card('Nightblade', game.current_player.hand)
  assert game.current_player.other_player.get_health() == 30
  play_nightblade = cast_action_for(game, nightblade)
  game.perform_action(play_nightblade)
  # battlecry damage from a minion is not a spell, so Spell Damage must not apply
  assert game.current_player.other_player.get_health() == 27


# ---- Stormpike Commando (5 mana 4/2, Battlecry: deal 2 damage) -------------

def test_stormpike_commando_stats():
  game = GameManager().create_test_game()
  commando = game.game_manager.get_card('Stormpike Commando', game.current_player.board)
  assert commando.manacost == 5
  assert commando.get_attack() == 4
  assert commando.get_health() == 2

def test_stormpike_commando_deals_two_targeted_damage():
  game = GameManager().create_test_game()
  commando = game.game_manager.get_card('Stormpike Commando', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  cast_commando = Action(Actions.CAST_MINION, commando, [enemy_wisp])
  game.perform_action(cast_commando)
  assert enemy_wisp.get_health() == 1 - 2

def test_stormpike_commando_not_boosted_by_spell_damage():
  game = GameManager().create_test_game()
  game.game_manager.get_card('Ogre Magi', game.current_player.board)  # Spell Damage +1
  commando = game.game_manager.get_card('Stormpike Commando', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  cast_commando = Action(Actions.CAST_MINION, commando, [enemy_wisp])
  game.perform_action(cast_commando)
  # battlecry damage is not a spell, so it stays at 2 regardless of Spell Damage
  assert enemy_wisp.get_health() == 1 - 2


# ---- Archmage (6 mana 4/7, Spell Damage +1) --------------------------------

def test_archmage_stats_and_attribute():
  game = GameManager().create_test_game()
  archmage = game.game_manager.get_card('Archmage', game.current_player.board)
  assert archmage.manacost == 6
  assert archmage.get_attack() == 4
  assert archmage.get_health() == 7
  assert archmage.has_attribute(Attributes.SPELL_DAMAGE)

def test_archmage_and_ogre_magi_spell_damage_stack():
  game = GameManager().create_test_game()
  game.game_manager.get_card('Archmage', game.current_player.board)
  game.game_manager.get_card('Ogre Magi', game.current_player.board)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  target_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  cast_fireball = Action(Actions.CAST_SPELL, fireball, [target_wisp])
  game.perform_action(cast_fireball)
  # 6 base + 1 (Archmage) + 1 (Ogre Magi) = 8
  assert target_wisp.get_health() == 1 - 8


# ---- Boulderfist Ogre (6 mana 6/7 vanilla) ---------------------------------

def test_boulderfist_ogre_stats():
  game = GameManager().create_test_game()
  ogre = game.game_manager.get_card('Boulderfist Ogre', game.current_player.board)
  assert ogre.manacost == 6
  assert ogre.get_attack() == 6
  assert ogre.get_health() == 7
  assert ogre.effect is None


# ---- Lord of the Arena (6 mana 6/5 Taunt) ----------------------------------

def test_lord_of_the_arena_stats_and_taunt():
  game = GameManager().create_test_game()
  lord = game.game_manager.get_card('Lord of the Arena', game.current_player.board)
  assert lord.manacost == 6
  assert lord.get_attack() == 6
  assert lord.get_health() == 5
  assert lord.has_attribute(Attributes.TAUNT)


# ---- Reckless Rocketeer (6 mana 5/2 Charge) --------------------------------

def test_reckless_rocketeer_stats_and_charge():
  game = GameManager().create_test_game()
  rocketeer = game.game_manager.get_card('Reckless Rocketeer', game.current_player.board)
  assert rocketeer.manacost == 6
  assert rocketeer.get_attack() == 5
  assert rocketeer.get_health() == 2
  assert rocketeer.has_attribute(Attributes.CHARGE)


# ---- Core Hound (7 mana 9/5 Beast, vanilla) --------------------------------

def test_core_hound_stats():
  game = GameManager().create_test_game()
  hound = game.game_manager.get_card('Core Hound', game.current_player.board)
  assert hound.manacost == 7
  assert hound.get_attack() == 9
  assert hound.get_health() == 5
  assert hound.creature_type == CreatureTypes.BEAST
  assert hound.effect is None


# ---- Stormwind Champion (7 mana 6/6, Your other minions have +1/+1) -------

def test_stormwind_champion_stats():
  game = GameManager().create_test_game()
  champion = game.game_manager.get_card('Stormwind Champion', game.current_player.board)
  assert champion.manacost == 7
  assert champion.get_attack() == 6
  assert champion.get_health() == 6

def test_stormwind_champion_buffs_others_not_itself():
  game = GameManager().create_test_game()
  champion = game.game_manager.get_card('Stormwind Champion', game.current_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  # doesn't buff itself
  assert champion.get_attack() == 6
  assert champion.get_health() == 6
  # buffs friendly minions
  assert friendly_wisp.get_attack() == 2
  assert friendly_wisp.get_health() == 2
  # does not buff enemy minions
  assert enemy_wisp.get_attack() == 1
  assert enemy_wisp.get_health() == 1

def test_stormwind_champion_two_champions_stack_but_dont_buff_selves():
  game = GameManager().create_test_game()
  champion_1 = game.game_manager.get_card('Stormwind Champion', game.current_player.board)
  champion_2 = game.game_manager.get_card('Stormwind Champion', game.current_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  # each champion buffs the OTHER champion by +1/+1, so each is 7/7, not 8/8
  assert champion_1.get_attack() == 7
  assert champion_1.get_health() == 7
  assert champion_2.get_attack() == 7
  assert champion_2.get_health() == 7
  # the wisp gets +1/+1 from each champion
  assert friendly_wisp.get_attack() == 3
  assert friendly_wisp.get_health() == 3

def test_stormwind_champion_aura_removed_on_death():
  game = GameManager().create_test_game()
  champion = game.game_manager.get_card('Stormwind Champion', game.current_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  assert friendly_wisp.get_attack() == 2
  assert friendly_wisp.get_health() == 2
  game.deal_damage(champion, champion.get_health())
  assert champion in game.current_player.graveyard
  # the aura buff should vanish along with its source
  assert friendly_wisp.get_attack() == 1
  assert friendly_wisp.get_health() == 1


# ---- War Golem (7 mana 7/7 vanilla) ----------------------------------------

def test_war_golem_stats():
  game = GameManager().create_test_game()
  golem = game.game_manager.get_card('War Golem', game.current_player.board)
  assert golem.manacost == 7
  assert golem.get_attack() == 7
  assert golem.get_health() == 7
  assert golem.effect is None
  assert golem.attributes == []
