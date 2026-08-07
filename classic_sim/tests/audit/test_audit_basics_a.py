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

# Audit slice: basic cards indices 0..21 (Elven Archer .. Silverback Patriarch)
# Ground truth: examples/validation/data/hsreplay_classic/cards.collectible.json, set == "VANILLA"


# --- Elven Archer (1/1/1, Battlecry: Deal 1 damage) --------------------------

def test_elven_archer_battlecry_deals_1_damage():
  game = GameManager().create_test_game()
  archer = game.game_manager.get_card('Elven Archer', game.current_player.hand)
  assert archer.manacost == 1 and archer.attack == 1 and archer.health == 1
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == archer and a.targets == [game.current_player.other_player]][0]
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 29
  assert archer.parent == archer.owner.board

def test_elven_archer_battlecry_not_boosted_by_spell_damage():
  #minion battlecries are not amplified by Spell Damage, only spells are
  game = GameManager().create_test_game()
  dalaran_mage = game.game_manager.get_card('Dalaran Mage', game.current_player.board) #Spell Damage +1
  assert game.current_player.get_spell_damage() == 1
  archer = game.game_manager.get_card('Elven Archer', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == archer and a.targets == [game.current_player.other_player]][0]
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 29 #still 1 damage, not 2


# --- Goldshire Footman (1/2 Taunt) -------------------------------------------

def test_goldshire_footman_stats_and_taunt():
  game = GameManager().create_test_game()
  footman = game.game_manager.get_card('Goldshire Footman', game.current_player.board)
  assert footman.manacost == 1
  assert footman.get_attack() == 1
  assert footman.get_health() == 2
  assert footman.has_attribute(Attributes.TAUNT)


# --- Grimscale Oracle (1/1 Murloc, "ALL other Murlocs +1 Attack") -----------

def test_grimscale_oracle_buffs_other_murlocs_both_sides():
  game = GameManager().create_test_game()
  oracle = game.game_manager.get_card('Grimscale Oracle', game.current_player.board)
  friendly_murloc = game.game_manager.get_card('Murloc Raider', game.current_player.board)
  enemy_murloc = game.game_manager.get_card('Murloc Raider', game.current_player.other_player.board)
  non_murloc = game.game_manager.get_card('Bloodfen Raptor', game.current_player.board)
  assert oracle.get_attack() == 1 #does not buff itself ("ALL OTHER Murlocs")
  assert friendly_murloc.get_attack() == 3 #2 base + 1
  assert enemy_murloc.get_attack() == 3 #buffs enemy Murlocs too
  assert non_murloc.get_attack() == 3 #unaffected, not a Murloc

def test_grimscale_oracle_aura_removed_on_death():
  game = GameManager().create_test_game()
  oracle = game.game_manager.get_card('Grimscale Oracle', game.current_player.board)
  friendly_murloc = game.game_manager.get_card('Murloc Raider', game.current_player.board)
  assert friendly_murloc.get_attack() == 3
  oracle.change_parent(oracle.owner.graveyard)
  assert friendly_murloc.get_attack() == 2

def test_grimscale_oracle_buffs_live_summoned_murloc_token():
  #the aura is recomputed live from board contents (not summon-event driven),
  #so a token Murloc summoned after the Oracle is on board still gets +1 Attack
  #even though token summons don't fire *_MINION_SUMMONED triggers.
  game = GameManager().create_test_game()
  oracle = game.game_manager.get_card('Grimscale Oracle', game.current_player.board)
  tidehunter = game.game_manager.get_card('Murloc Tidehunter', game.current_player.hand)
  play_tidehunter = [a for a in game.get_available_actions(game.current_player) if a.source == tidehunter][0]
  game.perform_action(play_tidehunter)
  murloc_scout = [c for c in game.current_player.board if c.name == 'Murloc Scout'][0]
  assert murloc_scout.get_attack() == 2 #1 base + 1 from Oracle's live aura


# --- Murloc Raider (2/1 Murloc, vanilla) -------------------------------------

def test_murloc_raider_stats():
  game = GameManager().create_test_game()
  raider = game.game_manager.get_card('Murloc Raider', game.current_player.board)
  assert raider.manacost == 1
  assert raider.get_attack() == 2
  assert raider.get_health() == 1
  assert raider.creature_type == CreatureTypes.MURLOC


# --- Stonetusk Boar (1/1 Beast, Charge) --------------------------------------

def test_stonetusk_boar_charges_immediately():
  game = GameManager().create_test_game()
  boar = game.game_manager.get_card('Stonetusk Boar', game.current_player.board)
  assert boar.has_attribute(Attributes.CHARGE)
  assert boar.creature_type == CreatureTypes.BEAST
  attack = [a for a in game.get_available_actions(game.current_player)
            if a.action_type == Actions.ATTACK and a.source == boar][0]
  game.perform_action(attack)
  assert game.current_player.other_player.get_health() == 29


# --- Voodoo Doctor (2/1, Battlecry: Restore 2 Health) ------------------------

def test_voodoo_doctor_heals_2():
  game = GameManager().create_test_game()
  game.deal_damage(game.current_player.other_player, 5)
  assert game.current_player.other_player.get_health() == 25
  doctor = game.game_manager.get_card('Voodoo Doctor', game.current_player.hand)
  heal = [a for a in game.get_available_actions(game.current_player)
          if a.source == doctor and a.targets == [game.current_player.other_player]][0]
  game.perform_action(heal)
  assert game.current_player.other_player.get_health() == 27


# --- Acidic Swamp Ooze (3/2, Battlecry: Destroy opponent's weapon) ----------

def test_acidic_swamp_ooze_destroys_enemy_weapon():
  game = GameManager().create_test_game()
  ooze = game.game_manager.get_card('Acidic Swamp Ooze', game.current_player.hand)
  enemy_weapon = game.game_manager.get_card('Generic Weapon', game.current_player.other_player)
  assert game.current_player.other_player.weapon
  play_ooze = [a for a in game.get_available_actions(game.current_player) if a.source == ooze][0]
  game.perform_action(play_ooze)
  assert not game.current_player.other_player.weapon
  assert enemy_weapon.parent == enemy_weapon.owner.graveyard
  assert ooze.parent == ooze.owner.board

def test_acidic_swamp_ooze_no_weapon_still_playable():
  #battlecry with no valid weapon target should just fizzle, not block the play
  game = GameManager().create_test_game()
  ooze = game.game_manager.get_card('Acidic Swamp Ooze', game.current_player.hand)
  assert not game.current_player.other_player.weapon
  play_ooze = [a for a in game.get_available_actions(game.current_player) if a.source == ooze][0]
  game.perform_action(play_ooze)
  assert ooze.parent == ooze.owner.board


# --- Bloodfen Raptor (3/2 Beast, vanilla) ------------------------------------

def test_bloodfen_raptor_stats():
  game = GameManager().create_test_game()
  raptor = game.game_manager.get_card('Bloodfen Raptor', game.current_player.board)
  assert raptor.manacost == 2
  assert raptor.get_attack() == 3
  assert raptor.get_health() == 2
  assert raptor.creature_type == CreatureTypes.BEAST


# --- Bluegill Warrior (2/1 Murloc, Charge) -----------------------------------

def test_bluegill_warrior_charges_immediately():
  game = GameManager().create_test_game()
  warrior = game.game_manager.get_card('Bluegill Warrior', game.current_player.board)
  assert warrior.manacost == 2
  assert warrior.get_attack() == 2
  assert warrior.get_health() == 1
  assert warrior.has_attribute(Attributes.CHARGE)
  attack = [a for a in game.get_available_actions(game.current_player)
            if a.action_type == Actions.ATTACK and a.source == warrior][0]
  game.perform_action(attack)
  assert game.current_player.other_player.get_health() == 28


# --- Frostwolf Grunt (2/2 Taunt) ---------------------------------------------

def test_frostwolf_grunt_stats_and_taunt():
  game = GameManager().create_test_game()
  grunt = game.game_manager.get_card('Frostwolf Grunt', game.current_player.board)
  assert grunt.manacost == 2
  assert grunt.get_attack() == 2
  assert grunt.get_health() == 2
  assert grunt.has_attribute(Attributes.TAUNT)

def test_frostwolf_grunt_silence_removes_taunt():
  game = GameManager().create_test_game()
  grunt = game.game_manager.get_card('Frostwolf Grunt', game.current_player.board)
  assert grunt.has_attribute(Attributes.TAUNT)
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  play_owl = [a for a in game.get_available_actions(game.current_player)
              if a.source == owl and a.targets == [grunt]][0]
  game.perform_action(play_owl)
  assert not grunt.has_attribute(Attributes.TAUNT)


# --- Kobold Geomancer (2/2, Spell Damage +1) ---------------------------------

def test_kobold_geomancer_spell_damage():
  game = GameManager().create_test_game()
  geomancer = game.game_manager.get_card('Kobold Geomancer', game.current_player.board)
  assert geomancer.manacost == 2
  assert geomancer.get_attack() == 2
  assert geomancer.get_health() == 2
  assert game.current_player.get_spell_damage() == 1
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast_fireball = [a for a in game.get_available_actions(game.current_player)
                    if a.source == fireball and a.targets == [game.current_player.other_player]][0]
  game.perform_action(cast_fireball)
  assert game.current_player.other_player.get_health() == 23 #6 base + 1 spell damage


# --- Murloc Tidehunter (2/1 Murloc, Battlecry: Summon a 1/1 Murloc Scout) ----

def test_murloc_tidehunter_summons_murloc_scout():
  game = GameManager().create_test_game()
  tidehunter = game.game_manager.get_card('Murloc Tidehunter', game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == tidehunter][0]
  game.perform_action(play)
  assert tidehunter.parent == tidehunter.owner.board
  assert len(game.current_player.board) == 2
  scout = [c for c in game.current_player.board if c.name == 'Murloc Scout'][0]
  assert scout.get_attack() == 1
  assert scout.get_health() == 1
  assert scout.creature_type == CreatureTypes.MURLOC
  assert scout.collectable == False

def test_murloc_tidehunter_no_summon_on_full_board():
  game = GameManager().create_test_game()
  for _ in range(7):
    game.game_manager.get_card('Wisp', game.current_player.board)
  assert len(game.current_player.board) == 7
  tidehunter = game.game_manager.get_card('Murloc Tidehunter', game.current_player.hand)
  #board is full: the minion itself cannot be played
  playable = [a for a in game.get_available_actions(game.current_player) if a.source == tidehunter]
  assert playable == []


# --- Novice Engineer (1/1, Battlecry: Draw a card) ---------------------------

def test_novice_engineer_draws_a_card():
  game = GameManager().create_test_game()
  engineer = game.game_manager.get_card('Novice Engineer', game.current_player.hand)
  assert engineer.manacost == 2
  assert engineer.get_attack() == 1
  assert engineer.get_health() == 1
  assert len(game.current_player.hand) == 1
  play = [a for a in game.get_available_actions(game.current_player) if a.source == engineer][0]
  game.perform_action(play)
  #Engineer left hand, one card was drawn in its place
  assert len(game.current_player.hand) == 1
  assert engineer.parent == engineer.owner.board


# --- River Crocolisk (2/3 Beast, vanilla) ------------------------------------

def test_river_crocolisk_stats():
  game = GameManager().create_test_game()
  crocolisk = game.game_manager.get_card('River Crocolisk', game.current_player.board)
  assert crocolisk.manacost == 2
  assert crocolisk.get_attack() == 2
  assert crocolisk.get_health() == 3
  assert crocolisk.creature_type == CreatureTypes.BEAST


# --- Dalaran Mage (1/4, Spell Damage +1) -------------------------------------

def test_dalaran_mage_stats_and_spell_damage():
  game = GameManager().create_test_game()
  mage = game.game_manager.get_card('Dalaran Mage', game.current_player.board)
  assert mage.manacost == 3
  assert mage.get_attack() == 1
  assert mage.get_health() == 4
  assert game.current_player.get_spell_damage() == 1


# --- Ironforge Rifleman (2/2, Battlecry: Deal 1 damage) ----------------------

def test_ironforge_rifleman_battlecry_deals_1_damage():
  game = GameManager().create_test_game()
  rifleman = game.game_manager.get_card('Ironforge Rifleman', game.current_player.hand)
  assert rifleman.manacost == 3
  assert rifleman.attack == 2 and rifleman.health == 2
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == rifleman and a.targets == [game.current_player.other_player]][0]
  game.perform_action(cast)
  assert game.current_player.other_player.get_health() == 29


# --- Ironfur Grizzly (3/3 Beast, Taunt) --------------------------------------

def test_ironfur_grizzly_stats_and_taunt():
  game = GameManager().create_test_game()
  grizzly = game.game_manager.get_card('Ironfur Grizzly', game.current_player.board)
  assert grizzly.manacost == 3
  assert grizzly.get_attack() == 3
  assert grizzly.get_health() == 3
  assert grizzly.creature_type == CreatureTypes.BEAST
  assert grizzly.has_attribute(Attributes.TAUNT)

def test_ironfur_grizzly_silence_removes_taunt():
  game = GameManager().create_test_game()
  grizzly = game.game_manager.get_card('Ironfur Grizzly', game.current_player.board)
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  play_owl = [a for a in game.get_available_actions(game.current_player)
              if a.source == owl and a.targets == [grizzly]][0]
  game.perform_action(play_owl)
  assert not grizzly.has_attribute(Attributes.TAUNT)
  assert grizzly.get_attack() == 3 #stats unaffected by silence


# --- Magma Rager (5/1, vanilla) ----------------------------------------------

def test_magma_rager_stats():
  game = GameManager().create_test_game()
  rager = game.game_manager.get_card('Magma Rager', game.current_player.board)
  assert rager.manacost == 3
  assert rager.get_attack() == 5
  assert rager.get_health() == 1
  assert rager.creature_type is None


# --- Raid Leader (2/2, "Your other minions have +1 Attack") -----------------

def test_raid_leader_buffs_other_friendly_minions_only():
  game = GameManager().create_test_game()
  leader = game.game_manager.get_card('Raid Leader', game.current_player.board)
  friendly = game.game_manager.get_card('Ironfur Grizzly', game.current_player.board)
  enemy = game.game_manager.get_card('Ironfur Grizzly', game.current_player.other_player.board)
  assert leader.get_attack() == 2 #does not buff itself
  assert friendly.get_attack() == 4 #3 base + 1
  assert enemy.get_attack() == 3 #enemy minions unaffected

def test_raid_leader_aura_removed_on_death():
  game = GameManager().create_test_game()
  leader = game.game_manager.get_card('Raid Leader', game.current_player.board)
  friendly = game.game_manager.get_card('Ironfur Grizzly', game.current_player.board)
  assert friendly.get_attack() == 4
  leader.change_parent(leader.owner.graveyard)
  assert friendly.get_attack() == 3


# --- Razorfen Hunter (2/3, Battlecry: Summon a 1/1 Boar) ---------------------

def test_razorfen_hunter_summons_boar():
  game = GameManager().create_test_game()
  hunter = game.game_manager.get_card('Razorfen Hunter', game.current_player.hand)
  assert hunter.manacost == 3
  assert hunter.attack == 2 and hunter.health == 3
  play = [a for a in game.get_available_actions(game.current_player) if a.source == hunter][0]
  game.perform_action(play)
  boar = [c for c in game.current_player.board if c.name == 'Boar'][0]
  assert boar.get_attack() == 1
  assert boar.get_health() == 1
  assert boar.creature_type == CreatureTypes.BEAST
  assert boar.collectable == False


# --- Shattered Sun Cleric (3/2, Battlecry: Give a friendly minion +1/+1) ----

def test_shattered_sun_cleric_buffs_friendly_minion():
  game = GameManager().create_test_game()
  cleric = game.game_manager.get_card('Shattered Sun Cleric', game.current_player.hand)
  target = game.game_manager.get_card('River Crocolisk', game.current_player.board)
  assert target.get_attack() == 2 and target.get_health() == 3
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == cleric and a.targets == [target]][0]
  game.perform_action(cast)
  assert target.get_attack() == 3
  assert target.get_health() == 4
  assert target.get_max_health() == 4

def test_shattered_sun_cleric_buff_reverted_by_silence():
  #the +1/+1 is applied via perm_attack/perm_health (Durations.PERMANENTLY),
  #which Silence resets to 0, so unlike Hunter's Mark's SetStats this buff is
  #fully undone by Silence.
  game = GameManager().create_test_game()
  cleric = game.game_manager.get_card('Shattered Sun Cleric', game.current_player.hand)
  target = game.game_manager.get_card('River Crocolisk', game.current_player.board)
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == cleric and a.targets == [target]][0]
  game.perform_action(cast)
  assert target.get_attack() == 3
  owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  play_owl = [a for a in game.get_available_actions(game.current_player)
              if a.source == owl and a.targets == [target]][0]
  game.perform_action(play_owl)
  assert target.get_attack() == 2
  assert target.get_health() == 3
  assert target.get_max_health() == 3

def test_shattered_sun_cleric_playable_with_no_friendly_minions():
  #real Hearthstone: Battlecry can be played with no valid target, does nothing
  game = GameManager().create_test_game()
  cleric = game.game_manager.get_card('Shattered Sun Cleric', game.current_player.hand)
  playable = [a for a in game.get_available_actions(game.current_player) if a.source == cleric]
  assert len(playable) == 1
  assert playable[0].targets == []
  game.perform_action(playable[0])
  assert cleric.parent == cleric.owner.board


# --- Silverback Patriarch (1/4 Beast, Taunt) ---------------------------------

def test_silverback_patriarch_stats_and_taunt():
  game = GameManager().create_test_game()
  patriarch = game.game_manager.get_card('Silverback Patriarch', game.current_player.board)
  assert patriarch.manacost == 3
  assert patriarch.get_attack() == 1
  assert patriarch.get_health() == 4
  assert patriarch.creature_type == CreatureTypes.BEAST
  assert patriarch.has_attribute(Attributes.TAUNT)
