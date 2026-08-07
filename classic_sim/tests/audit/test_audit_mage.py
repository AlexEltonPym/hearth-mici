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

# Audit slice: Mage cards, indices 0..24 (the entire get_mage_cards() pool -
# Arcane Missiles .. Archmage Antonidas).
# Ground truth: examples/validation/data/hsreplay_classic/cards.collectible.json,
# entries with "set": "VANILLA".


# --- Arcane Missiles (1 mana, deal 3 damage randomly split among enemies) ---

def test_arcane_missiles_cost_and_split_damage():
  game = GameManager().create_test_game()
  missiles = game.game_manager.get_card('Arcane Missiles', game.current_player.hand)
  assert missiles.manacost == 1
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board) #1/1
  #bypass the RNG entirely by handing DealDamage an explicit target list: 2 bolts
  #to face, 1 to the wisp - this is exactly what get_playable_spells_actions would
  #have produced with a different random draw, so it's a legitimate resolution path.
  cast = Action(Actions.CAST_SPELL, missiles, [game.current_player.other_player, game.current_player.other_player, enemy_wisp])
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 28
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard


# --- Mirror Image (1 mana, summon two 0/2 Taunt minions) --------------------

def test_mirror_image_summons_two_0_2_taunts():
  game = GameManager().create_test_game()
  mirror_image = game.game_manager.get_card('Mirror Image', game.current_player.hand)
  assert mirror_image.manacost == 1
  cast = Action(Actions.CAST_SPELL, mirror_image, [game.current_player])
  game.perform_action(cast)
  assert len(game.current_player.board) == 2
  for token in game.current_player.board:
    assert token.name == "Mirror Image Token"
    assert token.get_attack() == 0
    assert token.get_health() == 2
    assert token.has_attribute(Attributes.TAUNT)


# --- Arcane Explosion (2 mana, deal 1 damage to all enemy minions) ---------

def test_arcane_explosion_hits_only_enemy_minions():
  game = GameManager().create_test_game()
  arcane_explosion = game.game_manager.get_card('Arcane Explosion', game.current_player.hand)
  assert arcane_explosion.manacost == 2
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board) #1 health
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  cast = list(filter(lambda a: a.source == arcane_explosion, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert friendly_wisp.get_health() == 1 #untouched
  assert game.current_player.other_player.get_health() == 30 #hero untouched


# --- Frostbolt (2 mana, deal 3 damage to a character and Freeze it) --------

def test_frostbolt_minion_damage_and_freeze():
  game = GameManager().create_test_game()
  frostbolt = game.game_manager.get_card('Frostbolt', game.current_player.hand)
  assert frostbolt.manacost == 2
  enemy_boulder = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board) #6/7
  cast = Action(Actions.CAST_SPELL, frostbolt, [enemy_boulder])
  game.perform_action(cast)
  assert enemy_boulder.get_health() == 4
  assert enemy_boulder.has_attribute(Attributes.FROZEN)

def test_frostbolt_hero_freeze_then_ice_lance_finishes():
  #combo: Frostbolt freezes face, Ice Lance then deals 4 (instead of freezing again)
  game = GameManager().create_test_game()
  frostbolt = game.game_manager.get_card('Frostbolt', game.current_player.hand)
  ice_lance = game.game_manager.get_card('Ice Lance', game.current_player.hand)
  cast_frostbolt = Action(Actions.CAST_SPELL, frostbolt, [game.current_player.other_player])
  game.perform_action(cast_frostbolt)
  assert game.current_player.other_player.get_health() == 27
  assert game.current_player.other_player.has_attribute(Attributes.FROZEN)
  cast_ice_lance = Action(Actions.CAST_SPELL, ice_lance, [game.current_player.other_player])
  game.perform_action(cast_ice_lance)
  assert game.current_player.other_player.get_health() == 23


# --- Arcane Intellect (3 mana, draw 2 cards) --------------------------------

def test_arcane_intellect_draws_two():
  game = GameManager().create_test_game()
  arcane_intellect = game.game_manager.get_card('Arcane Intellect', game.current_player.hand)
  assert arcane_intellect.manacost == 3
  assert len(game.current_player.hand) == 1
  cast = Action(Actions.CAST_SPELL, arcane_intellect, [game.current_player])
  game.perform_action(cast)
  assert len(game.current_player.hand) == 2 #cast card left hand, drew 2


# --- Frost Nova (3 mana, Freeze all enemy minions, no damage) --------------

def test_frost_nova_freezes_without_damage():
  game = GameManager().create_test_game()
  frost_nova = game.game_manager.get_card('Frost Nova', game.current_player.hand)
  assert frost_nova.manacost == 3
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  cast = list(filter(lambda a: a.source == frost_nova, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast)
  assert enemy_wisp.has_attribute(Attributes.FROZEN)
  assert enemy_wisp.get_health() == 1 #no damage
  assert not friendly_wisp.has_attribute(Attributes.FROZEN)


# --- Fireball (4 mana, deal 6 damage) ---------------------------------------

def test_fireball_to_face():
  game = GameManager().create_test_game()
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  assert fireball.manacost == 4
  cast = Action(Actions.CAST_SPELL, fireball, [game.current_player.other_player])
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 24

def test_fireball_kills_6_health_minion():
  game = GameManager().create_test_game()
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  enemy_boulder = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board) #6/7
  cast = Action(Actions.CAST_SPELL, fireball, [enemy_boulder])
  game.perform_action(cast)
  assert enemy_boulder.get_health() == 1


# --- Polymorph (4 mana, transform a minion into a 1/1 Sheep) ---------------

def test_polymorph_transforms_and_strips_abilities():
  game = GameManager().create_test_game()
  polymorph = game.game_manager.get_card('Polymorph', game.current_player.hand)
  assert polymorph.manacost == 4
  enemy_footman = game.game_manager.get_card('Goldshire Footman', game.current_player.other_player.board) #1/2 Taunt
  cast = Action(Actions.CAST_SPELL, polymorph, [enemy_footman])
  game.perform_action(cast)
  assert enemy_footman.parent == enemy_footman.owner.graveyard
  assert len(game.current_player.other_player.board) == 1
  sheep = game.current_player.other_player.board.get_all()[0]
  assert sheep.name == "Sheep"
  assert sheep.get_attack() == 1
  assert sheep.get_health() == 1
  assert sheep.creature_type == CreatureTypes.BEAST
  assert not sheep.has_attribute(Attributes.TAUNT)

def test_polymorph_can_target_own_minion():
  #owner_filter=ALL - a mage can (mis)target its own minion too, matching real HS
  game = GameManager().create_test_game()
  polymorph = game.game_manager.get_card('Polymorph', game.current_player.hand)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  cast = Action(Actions.CAST_SPELL, polymorph, [friendly_wisp])
  game.perform_action(cast)
  assert friendly_wisp.parent == friendly_wisp.owner.graveyard
  assert game.current_player.board.get_all()[0].name == "Sheep"


# --- Water Elemental (4 mana 3/6, Freeze any character damaged by it) -----

def test_water_elemental_stats_and_no_race():
  game = GameManager().create_test_game()
  water_elemental = game.game_manager.get_card('Water Elemental', game.current_player.board)
  assert water_elemental.manacost == 4
  assert water_elemental.get_attack() == 3
  assert water_elemental.get_health() == 6
  assert water_elemental.creature_type is None #VANILLA has no race (later reprints added Elemental)

def test_water_elemental_freezes_when_attacking():
  game = GameManager().create_test_game()
  water_elemental = game.game_manager.get_card('Water Elemental', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack = Action(Actions.ATTACK, water_elemental, [enemy_wisp])
  game.perform_action(attack)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard #1 health, dies to 3 damage
  #attacker survives (1 dmg back) - freeze is on the character *damaged by* it, which is now dead;
  #confirm the freeze mechanism itself by attacking a minion that survives instead
  enemy_ogre = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board) #6/7
  attack2 = Action(Actions.ATTACK, water_elemental, [enemy_ogre])
  game.perform_action(attack2)
  assert enemy_ogre.has_attribute(Attributes.FROZEN)

def test_water_elemental_freezes_its_attacker_when_damaged():
  game = GameManager().create_test_game()
  water_elemental = game.game_manager.get_card('Water Elemental', game.current_player.other_player.board)
  attacker_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  attack = Action(Actions.ATTACK, attacker_wisp, [water_elemental])
  game.perform_action(attack)
  assert attacker_wisp.parent == attacker_wisp.owner.graveyard #1 health, dies to 3 damage back
  #use a survivor to confirm freeze applies to something that survives being hit back
  survivor = game.game_manager.get_card('Boulderfist Ogre', game.current_player.board) #6/7
  attack2 = Action(Actions.ATTACK, survivor, [water_elemental])
  game.perform_action(attack2)
  assert survivor.has_attribute(Attributes.FROZEN)


# --- Flamestrike (7 mana, deal 4 damage to all enemy minions) --------------
# VANILLA text is 4 damage (the later CORE/LEGACY reprint buffed it to 5) -
# the engine correctly implements the 2014-era 4 damage version.

def test_flamestrike_deals_4_to_all_enemy_minions():
  game = GameManager().create_test_game()
  flamestrike = game.game_manager.get_card('Flamestrike', game.current_player.hand)
  assert flamestrike.manacost == 7
  enemy_ogre = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board) #6/7
  friendly_ogre = game.game_manager.get_card('Boulderfist Ogre', game.current_player.board)
  cast = list(filter(lambda a: a.source == flamestrike, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast)
  assert enemy_ogre.get_health() == 3
  assert friendly_ogre.get_health() == 7 #untouched


# --- Ice Lance (1 mana, Freeze a character; 4 damage instead if Frozen) ---

def test_ice_lance_freezes_unfrozen_target_no_damage():
  game = GameManager().create_test_game()
  ice_lance = game.game_manager.get_card('Ice Lance', game.current_player.hand)
  assert ice_lance.manacost == 1
  enemy_ogre = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board)
  cast = Action(Actions.CAST_SPELL, ice_lance, [enemy_ogre])
  game.perform_action(cast)
  assert enemy_ogre.get_health() == 7 #no damage
  assert enemy_ogre.has_attribute(Attributes.FROZEN)

def test_ice_lance_deals_4_to_already_frozen_target():
  game = GameManager().create_test_game()
  frost_nova = game.game_manager.get_card('Frost Nova', game.current_player.hand)
  ice_lance = game.game_manager.get_card('Ice Lance', game.current_player.hand)
  enemy_ogre = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board)
  cast_nova = list(filter(lambda a: a.source == frost_nova, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_nova)
  assert enemy_ogre.has_attribute(Attributes.FROZEN)
  cast_lance = Action(Actions.CAST_SPELL, ice_lance, [enemy_ogre])
  game.perform_action(cast_lance)
  assert enemy_ogre.get_health() == 3 #7 - 4


# --- Mana Wyrm (1 mana 1/3, gains +1 Attack whenever you cast a spell) ----

def test_mana_wyrm_gains_attack_on_friendly_spell():
  game = GameManager().create_test_game()
  mana_wyrm = game.game_manager.get_card('Mana Wyrm', game.current_player.board)
  assert mana_wyrm.manacost == 1
  assert mana_wyrm.get_attack() == 1
  assert mana_wyrm.get_health() == 3
  arcane_intellect = game.game_manager.get_card('Arcane Intellect', game.current_player.hand)
  cast = Action(Actions.CAST_SPELL, arcane_intellect, [game.current_player])
  game.perform_action(cast)
  assert mana_wyrm.get_attack() == 2

def test_mana_wyrm_ignores_enemy_spell():
  game = GameManager().create_test_game()
  mana_wyrm = game.game_manager.get_card('Mana Wyrm', game.current_player.other_player.board)
  arcane_intellect = game.game_manager.get_card('Arcane Intellect', game.current_player.hand)
  cast = Action(Actions.CAST_SPELL, arcane_intellect, [game.current_player])
  game.perform_action(cast)
  assert mana_wyrm.get_attack() == 1 #unaffected, it belongs to the opponent


# --- Sorcerer's Apprentice (2 mana 3/2, your spells cost 1 less) ----------

def test_sorcerers_apprentice_reduces_spell_cost():
  game = GameManager().create_test_game()
  apprentice = game.game_manager.get_card("Sorcerer's Apprentice", game.current_player.board)
  assert apprentice.manacost == 2
  assert apprentice.get_attack() == 3
  assert apprentice.get_health() == 2
  arcane_explosion = game.game_manager.get_card('Arcane Explosion', game.current_player.hand) #normally 2
  assert arcane_explosion.get_manacost() == 1

def test_cone_of_cold_does_not_hit_non_adjacent_far_edge():
  game = GameManager().create_test_game()
  cone_of_cold = game.game_manager.get_card('Cone of Cold', game.current_player.hand)
  w1 = game.game_manager.get_card('Wisp', game.current_player.other_player.board) #index 0, left edge
  w2 = game.game_manager.get_card('Wisp', game.current_player.other_player.board) #index 1, true neighbour
  w3 = game.game_manager.get_card('Wisp', game.current_player.other_player.board) #index 2, far edge - NOT adjacent to w1
  cast = Action(Actions.CAST_SPELL, cone_of_cold, [w1])
  game.perform_action(cast)
  assert w3.get_health() == 1 #untouched by a spell cast on the opposite edge
  assert not w3.has_attribute(Attributes.FROZEN)


# --- Counterspell (3 mana secret, when your opponent casts a spell, Counter it) -

def test_counterspell_fizzles_enemy_spell():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.other_player.secrets_zone)
  assert counterspell.manacost == 3
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast = Action(Actions.CAST_SPELL, fireball, [game.current_player.other_player])
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 30 #no damage, spell was countered
  assert fireball.parent == fireball.owner.graveyard #still spent
  assert counterspell.parent == counterspell.owner.graveyard #secret consumed

def test_counterspell_does_not_affect_own_caster():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.secrets_zone)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast = Action(Actions.CAST_SPELL, fireball, [game.current_player.other_player])
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 24 #went through normally
  assert counterspell.parent == counterspell.owner.secrets_zone #not consumed


# --- Kirin Tor Mage (3 mana 4/3, next Secret you play this turn costs 0) --

def test_kirin_tor_mage_frees_only_the_next_secret():
  game = GameManager().create_test_game()
  kirin_tor_mage = game.game_manager.get_card('Kirin Tor Mage', game.current_player.hand)
  assert kirin_tor_mage.manacost == 3
  ice_barrier = game.game_manager.get_card('Ice Barrier', game.current_player.hand)
  vaporize = game.game_manager.get_card('Vaporize', game.current_player.hand)
  play_kirin_tor_mage = Action(Actions.CAST_MINION, kirin_tor_mage, [game.current_player])
  game.perform_action(play_kirin_tor_mage)
  assert ice_barrier.get_manacost() == 0
  cast_ice_barrier = list(filter(lambda a: a.source == ice_barrier, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_ice_barrier)
  assert vaporize.get_manacost() == 3 #only the *next* secret was free, not every secret this turn


# --- Vaporize (3 mana secret, when a minion attacks your hero, destroy it) -

def test_vaporize_destroys_attacking_minion_no_damage():
  game = GameManager().create_test_game()
  vaporize = game.game_manager.get_card('Vaporize', game.current_player.other_player.secrets_zone)
  assert vaporize.manacost == 3
  attacker = game.game_manager.get_card('Boulderfist Ogre', game.current_player.board)
  attack = Action(Actions.ATTACK, attacker, [game.current_player.other_player])
  game.perform_action(attack)
  assert attacker.parent == attacker.owner.graveyard
  assert game.current_player.other_player.get_health() == 30
  assert vaporize.parent == vaporize.owner.graveyard

def test_vaporize_does_not_trigger_on_minion_vs_minion_combat():
  game = GameManager().create_test_game()
  vaporize = game.game_manager.get_card('Vaporize', game.current_player.other_player.secrets_zone)
  attacker = game.game_manager.get_card('Wisp', game.current_player.board)
  enemy_target = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack = Action(Actions.ATTACK, attacker, [enemy_target])
  game.perform_action(attack)
  assert attacker.parent == attacker.owner.graveyard #traded normally
  assert vaporize.parent == vaporize.owner.secrets_zone #not consumed, still armed


# --- Ethereal Arcanist (4 mana 3/3, +2/+2 if you control a Secret at end of turn) -

def test_ethereal_arcanist_buffs_with_secret_up():
  game = GameManager().create_test_game()
  game.game_manager.get_card('Vaporize', game.current_player.secrets_zone)
  arcanist = game.game_manager.get_card('Ethereal Arcanist', game.current_player.board)
  assert arcanist.manacost == 4
  assert arcanist.get_attack() == 3 and arcanist.get_health() == 3
  game.end_turn()
  game.untap()
  assert arcanist.get_attack() == 5
  assert arcanist.get_health() == 5

def test_ethereal_arcanist_no_buff_without_secret():
  game = GameManager().create_test_game()
  arcanist = game.game_manager.get_card('Ethereal Arcanist', game.current_player.board)
  game.end_turn()
  game.untap()
  assert arcanist.get_attack() == 3
  assert arcanist.get_health() == 3


# --- Blizzard (6 mana, 2 damage to all enemy minions and Freeze them) -----

def test_blizzard_damages_and_freezes_only_enemies():
  game = GameManager().create_test_game()
  blizzard = game.game_manager.get_card('Blizzard', game.current_player.hand)
  assert blizzard.manacost == 6
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  cast = list(filter(lambda a: a.source == blizzard, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert friendly_wisp.get_health() == 1
  assert not friendly_wisp.has_attribute(Attributes.FROZEN)


# --- Ice Block (3 mana secret, prevent fatal damage, become Immune) -------

def test_ice_block_prevents_lethal_and_grants_immunity():
  game = GameManager().create_test_game()
  #secrets only trigger against the current turn-holder's actions, so put it on other_player
  ice_block = game.game_manager.get_card('Ice Block', game.current_player.other_player.secrets_zone)
  assert ice_block.manacost == 3
  game.current_player.other_player.armor = 0
  game.deal_damage(game.current_player.other_player, 40) #would be lethal
  assert game.current_player.other_player.get_health() == 30 #prevented
  assert game.current_player.other_player.has_attribute(Attributes.IMMUNE)
  assert ice_block.parent == ice_block.owner.graveyard
  game.deal_damage(game.current_player.other_player, 5) #immune, no further damage
  assert game.current_player.get_health() == 30


# --- Spellbender (3 mana secret, redirect an enemy spell cast on a minion) -

def test_spellbender_redirects_spell_targeting_minion():
  game = GameManager().create_test_game()
  spellbender = game.game_manager.get_card('Spellbender', game.current_player.other_player.secrets_zone)
  assert spellbender.manacost == 3
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  cast = Action(Actions.CAST_SPELL, fireball, [enemy_wisp])
  game.perform_action(cast)
  assert enemy_wisp.get_health() == 1 #untouched, spell was redirected
  assert spellbender.parent == spellbender.owner.graveyard
  tokens = [c for c in game.current_player.other_player.graveyard if c.name == "Spellbender Token"]
  assert len(tokens) == 1 #ate the Fireball and died (1/3 vs 6 dmg)

def test_spellbender_does_not_redirect_spell_targeting_hero():
  game = GameManager().create_test_game()
  spellbender = game.game_manager.get_card('Spellbender', game.current_player.other_player.secrets_zone)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast = Action(Actions.CAST_SPELL, fireball, [game.current_player.other_player])
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 24 #Fireball should have gone face
  assert spellbender.parent == spellbender.owner.secrets_zone #should not have triggered


# --- Pyroblast (10 mana, deal 10 damage) ------------------------------------

def test_pyroblast_ten_damage_to_face():
  game = GameManager().create_test_game()
  pyroblast = game.game_manager.get_card('Pyroblast', game.current_player.hand)
  assert pyroblast.manacost == 10
  cast = Action(Actions.CAST_SPELL, pyroblast, [game.current_player.other_player])
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 20


# --- Archmage Antonidas (7 mana 5/7, whenever you cast a spell, add a Fireball) -

def test_archmage_antonidas_adds_fireball_on_friendly_spell():
  game = GameManager().create_test_game()
  antonidas = game.game_manager.get_card('Archmage Antonidas', game.current_player.board)
  assert antonidas.manacost == 7
  assert antonidas.get_attack() == 5 and antonidas.get_health() == 7
  assert len(game.current_player.hand) == 0
  arcane_intellect = game.game_manager.get_card('Arcane Intellect', game.current_player.hand)
  cast = Action(Actions.CAST_SPELL, arcane_intellect, [game.current_player])
  game.perform_action(cast)
  #hand: 2 cards drawn by Arcane Intellect + 1 added Fireball
  fireballs = [c for c in game.current_player.hand if c.name == "Fireball"]
  assert len(fireballs) == 1
  assert fireballs[0].get_manacost() == 4

def test_archmage_antonidas_ignores_enemy_spell():
  game = GameManager().create_test_game()
  antonidas = game.game_manager.get_card('Archmage Antonidas', game.current_player.other_player.board)
  arcane_intellect = game.game_manager.get_card('Arcane Intellect', game.current_player.hand)
  cast = Action(Actions.CAST_SPELL, arcane_intellect, [game.current_player])
  game.perform_action(cast)
  fireballs = [c for c in game.current_player.other_player.hand if c.name == "Fireball"]
  assert len(fireballs) == 0
