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

# Audit slice: rare cards indices 18..35 of get_rare_cards()
# (Coldlight Seer, Demolisher, Emperor Cobra, Imp Master, Injured Blademaster,
#  Mind Control Tech, Questing Adventurer, Ancient Mage, Defender of Argus,
#  Twilight Drake, Violet Teacher, Abomination, Azure Drake, Gadgetzan
#  Auctioneer, Stampeding Kodo, Argent Commander, Sunwalker, Ravenholdt Assassin)
# Ground truth: examples/validation/data/hsreplay_classic/cards.collectible.json, set == "VANILLA"


# --- Coldlight Seer (3/2/3 Murloc, Battlecry: Give ALL other Murlocs +2 Health) ---

def test_coldlight_seer_stats_and_type():
  game = GameManager().create_test_game()
  seer = game.game_manager.get_card('Coldlight Seer', game.current_player.hand)
  assert seer.manacost == 3
  assert seer.attack == 2
  assert seer.health == 3
  assert seer.creature_type == CreatureTypes.MURLOC

def test_coldlight_seer_buffs_all_murlocs_not_self_or_nonmurloc():
  game = GameManager().create_test_game()
  friendly_murloc = game.game_manager.get_card('Murloc Raider', game.current_player.board)
  enemy_murloc = game.game_manager.get_card('Murloc Raider', game.current_player.other_player.board)
  non_murloc = game.game_manager.get_card('Wisp', game.current_player.board)
  seer = game.game_manager.get_card('Coldlight Seer', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == seer][0]
  game.perform_action(cast)
  seer_on_board = [c for c in game.current_player.board if c.name == 'Coldlight Seer'][0]
  assert friendly_murloc.get_health() == 3 #1 base + 2
  assert enemy_murloc.get_health() == 3 #buffs enemy Murlocs too ("ALL other Murlocs")
  assert non_murloc.get_health() == 1 #unaffected, not a Murloc
  assert seer_on_board.get_health() == 3 #does not buff itself ("ALL OTHER Murlocs")


# --- Demolisher (3/1/4 Mech, "At the start of your turn, deal 2 damage to a random enemy") ---

def test_demolisher_stats():
  game = GameManager().create_test_game()
  demolisher = game.game_manager.get_card('Demolisher', game.current_player.board)
  assert demolisher.manacost == 3
  assert demolisher.attack == 1
  assert demolisher.creature_type == CreatureTypes.MECH

def test_demolisher_health_matches_vanilla():
  game = GameManager().create_test_game()
  demolisher = game.game_manager.get_card('Demolisher', game.current_player.board)
  assert demolisher.get_health() == 4

def test_demolisher_deals_2_damage_to_random_enemy_at_start_of_turn():
  game = GameManager().create_test_game()
  demolisher = game.game_manager.get_card('Demolisher', game.current_player.board)
  enemy = game.current_player.other_player
  enemy_minion = game.game_manager.get_card('Ancient Watcher', enemy.board)
  assert enemy_minion.get_health() == 5
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  #target is 'a random enemy' - minion OR hero - so exactly 2 total damage
  #lands somewhere on the enemy side
  minion_damage = 5 - enemy_minion.get_health()
  hero_damage = 30 - enemy.get_health()
  assert minion_damage + hero_damage == 2

def test_demolisher_can_hit_enemy_hero_when_no_enemy_minions():
  game = GameManager().create_test_game()
  demolisher = game.game_manager.get_card('Demolisher', game.current_player.board)
  assert len(game.current_player.other_player.board) == 0
  enemy_hp_before = game.current_player.other_player.get_health()
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert game.current_player.other_player.get_health() < enemy_hp_before


# --- Emperor Cobra (3/2/3 Beast, Poisonous) ----------------------------------

def test_emperor_cobra_stats_and_poisonous():
  game = GameManager().create_test_game()
  cobra = game.game_manager.get_card('Emperor Cobra', game.current_player.hand)
  assert cobra.manacost == 3
  assert cobra.attack == 2
  assert cobra.health == 3
  assert cobra.creature_type == CreatureTypes.BEAST
  assert Attributes.POISONOUS in cobra.attributes

def test_emperor_cobra_poison_destroys_any_minion_it_damages():
  game = GameManager().create_test_game()
  cobra = game.game_manager.get_card('Emperor Cobra', game.current_player.board)
  cobra.attacks_this_turn = 0
  big = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board) #6/7, well above cobra's 2 attack
  attack = [a for a in game.get_available_actions(game.current_player) if a.source == cobra and a.targets[0] == big][0]
  game.perform_action(attack)
  assert big.parent == big.owner.graveyard #destroyed despite only taking 2 of 7 health in damage

def test_emperor_cobra_poison_blocked_by_divine_shield():
  #Divine Shield absorbs the hit entirely - no damage is dealt, so Poisonous never triggers
  game = GameManager().create_test_game()
  cobra = game.game_manager.get_card('Emperor Cobra', game.current_player.board)
  cobra.attacks_this_turn = 0
  shielded = game.game_manager.get_card('Sunwalker', game.current_player.other_player.board)
  attack = [a for a in game.get_available_actions(game.current_player) if a.source == cobra and a.targets[0] == shielded][0]
  game.perform_action(attack)
  assert shielded.parent == shielded.owner.board
  assert not shielded.has_attribute(Attributes.DIVINE_SHIELD)
  assert shielded.get_health() == 5


# --- Imp Master (3/1/5, "End of turn: deal 1 damage to this minion and summon a 1/1 Imp") ---

def test_imp_master_stats():
  game = GameManager().create_test_game()
  imp_master = game.game_manager.get_card('Imp Master', game.current_player.hand)
  assert imp_master.manacost == 3
  assert imp_master.attack == 1
  assert imp_master.health == 5

def test_imp_master_summons_imp_before_self_damage_kills_it():
  #at 1 health, Imp Master should still summon the Imp even though the same
  #trigger's self-damage kills it (both effects fire off the same trigger)
  game = GameManager().create_test_game()
  imp_master = game.game_manager.get_card('Imp Master', game.current_player.board)
  game.deal_damage(imp_master, 4) #down to 1 health
  assert imp_master.get_health() == 1
  game.end_turn()
  assert imp_master.parent == imp_master.owner.graveyard
  assert 'Imp' in [c.name for c in imp_master.owner.board]

@pytest.mark.xfail(reason="KNOWN LIMITATION: SummonToken does not fire *_MINION_SUMMONED triggers, so Imp Master's end-of-turn Imp does not proc Knife Juggler (real Hearthstone: any minion summoned, including tokens from other cards' effects, procs Knife Juggler)", strict=False)
def test_imp_master_imp_summon_triggers_knife_juggler():
  game = GameManager().create_test_game()
  juggler = game.game_manager.get_card('Knife Juggler', game.current_player.board)
  imp_master = game.game_manager.get_card('Imp Master', game.current_player.board)
  enemy_hp_before = game.current_player.other_player.get_health()
  game.end_turn()
  assert game.current_player.other_player.get_health() < enemy_hp_before


# --- Injured Blademaster (3/4/7, Battlecry: Deal 4 damage to HIMSELF) --------

def test_injured_blademaster_stats_and_self_damage_battlecry():
  game = GameManager().create_test_game()
  blademaster = game.game_manager.get_card('Injured Blademaster', game.current_player.hand)
  assert blademaster.manacost == 3
  assert blademaster.attack == 4
  assert blademaster.health == 7
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == blademaster][0]
  game.perform_action(cast)
  bm = [c for c in game.current_player.board if c.name == 'Injured Blademaster'][0]
  assert bm.get_attack() == 4
  assert bm.get_max_health() == 7
  assert bm.get_health() == 3 #7 - 4 self damage


# --- Mind Control Tech (3/3/3, Battlecry not implemented - simplification) ---

def test_mind_control_tech_stats_and_steal_not_implemented():
  #card_sets.py comment: "#not implementing stealing" - deliberate simplification
  game = GameManager().create_test_game()
  mct = game.game_manager.get_card('Mind Control Tech', game.current_player.hand)
  assert mct.manacost == 3
  assert mct.attack == 3
  assert mct.health == 3
  for _ in range(4):
    game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  assert len(game.current_player.other_player.board) == 4 #opponent has 4+ minions, real battlecry would steal one
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == mct][0]
  game.perform_action(cast)
  assert len(game.current_player.other_player.board) == 4 #no minion stolen (simplification)
  assert len(game.current_player.board) == 1 #only Mind Control Tech itself


# --- Questing Adventurer (3/2/2, "Whenever you play a card, gain +1/+1") ----

def test_questing_adventurer_stats():
  game = GameManager().create_test_game()
  qa = game.game_manager.get_card('Questing Adventurer', game.current_player.hand)
  assert qa.manacost == 3
  assert qa.attack == 2
  assert qa.health == 2

def test_questing_adventurer_buffs_on_any_card_played_not_just_minions():
  game = GameManager().create_test_game()
  qa = game.game_manager.get_card('Questing Adventurer', game.current_player.board)
  assert qa.get_attack() == 2 and qa.get_health() == 2
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast_spell = [a for a in game.get_available_actions(game.current_player)
                if a.source == fireball and a.targets[0] == game.current_player.other_player][0]
  game.perform_action(cast_spell)
  assert qa.get_attack() == 3 and qa.get_health() == 3 #buffed by playing a spell
  wisp = game.game_manager.get_card('Wisp', game.current_player.hand)
  play_wisp = [a for a in game.get_available_actions(game.current_player) if a.source == wisp][0]
  game.perform_action(play_wisp)
  assert qa.get_attack() == 4 and qa.get_health() == 4 #buffed by playing a minion too


# --- Ancient Mage (4/2/5, Battlecry: Give adjacent minions Spell Damage +1) --

def test_ancient_mage_stats():
  game = GameManager().create_test_game()
  mage = game.game_manager.get_card('Ancient Mage', game.current_player.hand)
  assert mage.manacost == 4
  assert mage.attack == 2
  assert mage.health == 5

def test_ancient_mage_buffs_the_single_adjacent_minion():
  game = GameManager().create_test_game()
  w1 = game.game_manager.get_card('Wisp', game.current_player.board)
  mage = game.game_manager.get_card('Ancient Mage', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == mage][0]
  game.perform_action(cast)
  assert w1.has_attribute(Attributes.SPELL_DAMAGE)

def test_ancient_mage_adjacency_wrong_with_multiple_minions():
  game = GameManager().create_test_game()
  w1 = game.game_manager.get_card('Wisp', game.current_player.board)
  w2 = game.game_manager.get_card('Wisp', game.current_player.board)
  mage = game.game_manager.get_card('Ancient Mage', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == mage][0]
  game.perform_action(cast)
  assert not w1.has_attribute(Attributes.SPELL_DAMAGE) #w1 is not adjacent to the newly-appended Ancient Mage
  assert w2.has_attribute(Attributes.SPELL_DAMAGE) #w2 (the actual left neighbor) is correctly buffed


# --- Defender of Argus (4/2/3, Battlecry: Give adjacent +1/+1 and Taunt) ----

def test_defender_of_argus_stats():
  game = GameManager().create_test_game()
  argus = game.game_manager.get_card('Defender of Argus', game.current_player.hand)
  assert argus.manacost == 4
  assert argus.attack == 2
  assert argus.health == 3

def test_defender_of_argus_buffs_the_single_adjacent_minion():
  game = GameManager().create_test_game()
  w1 = game.game_manager.get_card('Wisp', game.current_player.board)
  argus = game.game_manager.get_card('Defender of Argus', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == argus][0]
  game.perform_action(cast)
  assert w1.get_attack() == 2 and w1.has_attribute(Attributes.TAUNT)

def test_defender_of_argus_adjacency_wrong_with_multiple_minions():
  game = GameManager().create_test_game()
  w1 = game.game_manager.get_card('Wisp', game.current_player.board)
  w2 = game.game_manager.get_card('Wisp', game.current_player.board)
  w3 = game.game_manager.get_card('Wisp', game.current_player.board)
  argus = game.game_manager.get_card('Defender of Argus', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == argus][0]
  game.perform_action(cast)
  assert not w1.has_attribute(Attributes.TAUNT) #w1 is not adjacent to the newly-appended Defender of Argus
  assert not w2.has_attribute(Attributes.TAUNT) #w2 (middle) is not adjacent either
  assert w3.has_attribute(Attributes.TAUNT) #w3 (the actual left neighbor) is correctly buffed


# --- Twilight Drake (4/4/1 Dragon, Battlecry: +1 Health per card in hand) ---

def test_twilight_drake_stats():
  game = GameManager().create_test_game()
  drake = game.game_manager.get_card('Twilight Drake', game.current_player.hand)
  assert drake.manacost == 4
  assert drake.attack == 4
  assert drake.health == 1
  assert drake.creature_type == CreatureTypes.DRAGON

def test_twilight_drake_battlecry_gains_health_per_card_in_hand():
  game = GameManager().create_test_game()
  game.current_player.hand.clear()
  for _ in range(3):
    game.game_manager.get_card('Wisp', game.current_player.hand)
  drake = game.game_manager.get_card('Twilight Drake', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == drake][0]
  game.perform_action(cast)
  drake_on_board = [c for c in game.current_player.board if c.name == 'Twilight Drake'][0]
  assert drake_on_board.get_attack() == 4
  assert drake_on_board.get_health() == 4 #1 base + 3 cards remaining in hand (Drake itself already left hand)


# --- Violet Teacher (4/3/5, "Whenever you cast a spell, summon a 1/1") -----

def test_violet_teacher_stats():
  game = GameManager().create_test_game()
  teacher = game.game_manager.get_card('Violet Teacher', game.current_player.hand)
  assert teacher.manacost == 4
  assert teacher.attack == 3
  assert teacher.health == 5

def test_violet_teacher_summons_apprentice_on_spell_cast():
  game = GameManager().create_test_game()
  teacher = game.game_manager.get_card('Violet Teacher', game.current_player.board)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == fireball and a.targets[0] == game.current_player.other_player][0]
  assert len(game.current_player.board) == 1
  game.perform_action(cast)
  assert len(game.current_player.board) == 2
  apprentice = [c for c in game.current_player.board if c.name == 'Violet Apprentice'][0]
  assert apprentice.get_attack() == 1 and apprentice.get_health() == 1


# --- Abomination (5/4/4 Taunt, Deathrattle: Deal 2 damage to ALL characters) ---

def test_abomination_stats_and_taunt():
  game = GameManager().create_test_game()
  abom = game.game_manager.get_card('Abomination', game.current_player.hand)
  assert abom.manacost == 5
  assert abom.attack == 4
  assert abom.health == 4
  assert Attributes.TAUNT in abom.attributes

def test_abomination_deathrattle_damages_all_characters():
  game = GameManager().create_test_game()
  abom = game.game_manager.get_card('Abomination', game.current_player.board)
  friendly_other = game.game_manager.get_card('Wisp', game.current_player.board)
  enemy_minion = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  own_hp_before = game.current_player.get_health()
  enemy_hp_before = game.current_player.other_player.get_health()
  game.deal_damage(abom, 100) #kill abomination via real damage path so its deathrattle fires
  assert abom.parent == abom.owner.graveyard
  assert friendly_other.parent == friendly_other.owner.graveyard #1 health, dies to 2 damage
  assert enemy_minion.parent == enemy_minion.owner.graveyard #1 health, dies to 2 damage
  assert game.current_player.get_health() == own_hp_before - 2
  assert game.current_player.other_player.get_health() == enemy_hp_before - 2


# --- Azure Drake (5/4/4 Dragon, Spell Damage +1, Battlecry: Draw a card) ----

def test_azure_drake_stats():
  game = GameManager().create_test_game()
  drake = game.game_manager.get_card('Azure Drake', game.current_player.hand)
  assert drake.manacost == 5
  assert drake.attack == 4
  assert drake.health == 4
  assert drake.creature_type == CreatureTypes.DRAGON
  assert Attributes.SPELL_DAMAGE in drake.attributes

def test_azure_drake_battlecry_draws_card():
  game = GameManager().create_test_game()
  game.current_player.hand.clear()
  drake = game.game_manager.get_card('Azure Drake', game.current_player.hand)
  hand_before = len(game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == drake][0]
  game.perform_action(cast)
  #drake itself leaves hand (-1), battlecry draws a replacement (+1) -> net unchanged
  assert len(game.current_player.hand) == hand_before


# --- Gadgetzan Auctioneer (5/4/4, "Whenever you cast a spell, draw a card") -

def test_gadgetzan_auctioneer_stats():
  game = GameManager().create_test_game()
  auctioneer = game.game_manager.get_card('Gadgetzan Auctioneer', game.current_player.hand)
  assert auctioneer.manacost == 5
  assert auctioneer.attack == 4
  assert auctioneer.health == 4

def test_gadgetzan_auctioneer_draws_on_spell_cast():
  game = GameManager().create_test_game()
  game.current_player.hand.clear()
  game.game_manager.get_card('Gadgetzan Auctioneer', game.current_player.board)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  hand_before = len(game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player)
          if a.source == fireball and a.targets[0] == game.current_player.other_player][0]
  game.perform_action(cast)
  #fireball leaves hand (-1), Auctioneer draws a replacement (+1) -> net unchanged
  assert len(game.current_player.hand) == hand_before


# --- Stampeding Kodo (5/3/5 Beast, Battlecry: Destroy random enemy minion with <=2 attack) ---

def test_stampeding_kodo_stats():
  game = GameManager().create_test_game()
  kodo = game.game_manager.get_card('Stampeding Kodo', game.current_player.hand)
  assert kodo.manacost == 5
  assert kodo.attack == 3
  assert kodo.health == 5
  assert kodo.creature_type == CreatureTypes.BEAST

def test_stampeding_kodo_only_destroys_low_attack_enemy_minion():
  game = GameManager().create_test_game()
  small = game.game_manager.get_card('Wisp', game.current_player.other_player.board) #1 attack, qualifies
  big = game.game_manager.get_card('Boulderfist Ogre', game.current_player.other_player.board) #6 attack, does not qualify
  kodo = game.game_manager.get_card('Stampeding Kodo', game.current_player.hand)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == kodo][0]
  game.perform_action(cast)
  assert small.parent == small.owner.graveyard #only qualifying minion, so RANDOMLY is deterministic
  assert big.parent == big.owner.board


# --- Argent Commander (6/4/2, Charge, Divine Shield) -------------------------

def test_argent_commander_stats_and_keywords():
  game = GameManager().create_test_game()
  argent = game.game_manager.get_card('Argent Commander', game.current_player.hand)
  assert argent.manacost == 6
  assert argent.attack == 4
  assert argent.health == 2
  assert Attributes.CHARGE in argent.attributes
  assert Attributes.DIVINE_SHIELD in argent.attributes


# --- Sunwalker (6/4/5, Taunt, Divine Shield) ---------------------------------

def test_sunwalker_stats_and_keywords():
  game = GameManager().create_test_game()
  sunwalker = game.game_manager.get_card('Sunwalker', game.current_player.hand)
  assert sunwalker.manacost == 6
  assert sunwalker.attack == 4
  assert sunwalker.health == 5
  assert Attributes.TAUNT in sunwalker.attributes
  assert Attributes.DIVINE_SHIELD in sunwalker.attributes


# --- Ravenholdt Assassin (7/7/5, Stealth) ------------------------------------

def test_ravenholdt_assassin_stats_and_stealth():
  game = GameManager().create_test_game()
  raven = game.game_manager.get_card('Ravenholdt Assassin', game.current_player.hand)
  assert raven.manacost == 7
  assert raven.attack == 7
  assert raven.health == 5
  assert Attributes.STEALTH in raven.attributes
