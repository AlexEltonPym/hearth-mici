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


# ---------------------------------------------------------------------------
# Audit slice: get_epic_cards() (11) + get_legendary_cards() (16) = 27 cards,
# from src/card_sets.py, checked against the VANILLA entries in
# examples/validation/data/hsreplay_classic/cards.collectible.json.
#
# KNOWN issues (per audit brief, not deep-dived here beyond a single
# documenting test each):
#  (1) token summons don't fire *_MINION_SUMMONED triggers
#  (2) sequential AOE damage can miss same-batch deaths for a dying minion's
#      own trigger
#  (3) Silence doesn't revert SetStats/SwapStats or restore original health
#  (4) Leeroy Jenkins is 5 mana in the engine, VANILLA says 4 - fix planned
#  (5) HEXPROOF is not filtered for battlecry targeting
# ---------------------------------------------------------------------------


# VANILLA ground truth: (cost, attack, health, creature_type) from
# cards.collectible.json. None means no creature type / not a minion stat.
VANILLA_STATS = {
  "Hungry Crab": (1, 1, 2, CreatureTypes.BEAST),
  "Captain's Parrot": (2, 1, 1, CreatureTypes.BEAST),
  "Doomsayer": (2, 0, 7, None),
  "Big Game Hunter": (3, 4, 2, None),
  "Blood Knight": (3, 3, 3, None),
  "Murloc Warleader": (3, 3, 3, CreatureTypes.MURLOC),
  "Southsea Captain": (3, 3, 3, CreatureTypes.PIRATE),
  "Faceless Manipulator": (5, 3, 3, None),
  "Sea Giant": (10, 8, 8, None),
  "Mountain Giant": (12, 8, 8, None),
  "Molten Giant": (20, 8, 8, None),
  "Alexstrasza": (9, 8, 8, CreatureTypes.DRAGON),
  "Ragnaros the Firelord": (8, 8, 8, None),
  "Cairne Bloodhoof": (6, 4, 5, None),
  "Bloodmage Thalnos": (2, 1, 1, None),
  "Leeroy Jenkins": (4, 6, 2, None),  # engine has manacost=5, see known issue (4)
  "Baron Geddon": (7, 7, 5, None),
  "Sylvanas Windrunner": (6, 5, 5, None),
  "Harrison Jones": (5, 5, 4, None),
  "The Black Knight": (6, 4, 5, None),
  "Tinkmaster Overspark": (3, 3, 3, None),
  "Ysera": (9, 4, 12, CreatureTypes.DRAGON),
  "Nat Pagle": (2, 0, 4, None),
  "Nozdormu": (9, 8, 8, CreatureTypes.DRAGON),
  "Lorewalker Cho": (2, 0, 4, None),
  "Elite Tauren Chieftain": (5, 5, 5, None),
  "Millhouse Manastorm": (2, 4, 4, None),
}


def _fresh(game, name, zone):
  return game.game_manager.get_card(name, zone)


def test_epic_and_legendary_pool_sizes():
  epics = get_epic_cards()
  legendaries = get_legendary_cards()
  assert len(epics) == 11
  assert len(legendaries) == 16


@pytest.mark.parametrize("name", list(VANILLA_STATS.keys()))
def test_audit_vanilla_stats(name):
  game = GameManager().create_test_game()
  card = _fresh(game, name, game.current_player.hand)
  cost, attack, health, creature_type = VANILLA_STATS[name]
  if name == "Leeroy Jenkins":
    pytest.xfail(reason="BUG: Leeroy Jenkins costs 5 in the engine, VANILLA is 4 (known issue, fix planned)")
  assert card.get_manacost() == cost
  assert card.original_attack == attack
  assert card.original_health == health
  assert card.creature_type == creature_type


def test_audit_leeroy_jenkins_cost_is_wrong():
  game = GameManager().create_test_game()
  leeroy = _fresh(game, 'Leeroy Jenkins', game.current_player.hand)
  # documents the known cost mismatch explicitly (kept separate from the
  # parametrized stats test so it shows up as its own line in test output)
  assert leeroy.get_manacost() == 4




# ---------------------------------------------------------------------------
# Hungry Crab
# ---------------------------------------------------------------------------

def test_audit_hungry_crab_destroys_murloc_and_buffs_self():
  game = GameManager().create_test_game()
  crab = _fresh(game, 'Hungry Crab', game.current_player.hand)
  murloc = _fresh(game, 'Murloc Raider', game.current_player.other_player.board)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == crab and a.targets == [murloc]][0]
  game.perform_action(play)
  assert murloc.parent == murloc.owner.graveyard
  assert crab.get_attack() == 3
  assert crab.get_health() == 4


def test_audit_hungry_crab_no_murloc_no_buff():
  # combo/edge case: with no valid Murloc target on either board, Hungry Crab
  # can still be played (battlecry fizzles) but must NOT gain +2/+2 - the
  # buff is conditioned on actually destroying something.
  game = GameManager().create_test_game()
  crab = _fresh(game, 'Hungry Crab', game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == crab][0]
  assert play.targets == []
  game.perform_action(play)
  assert crab.parent == crab.owner.board
  assert crab.get_attack() == 1
  assert crab.get_health() == 2


# ---------------------------------------------------------------------------
# Captain's Parrot
# ---------------------------------------------------------------------------

def test_audit_captains_parrot_tutors_a_pirate():
  game = GameManager().create_test_game()
  parrot = _fresh(game, "Captain's Parrot", game.current_player.hand)
  _fresh(game, 'Southsea Deckhand', game.current_player.deck)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == parrot][0]
  game.perform_action(play)
  assert len(game.current_player.hand) == 1
  assert game.current_player.hand.get_all()[0].creature_type == CreatureTypes.PIRATE


def test_audit_captains_parrot_no_pirates_in_deck_still_playable():
  # combo/edge case: with no pirates in the deck, the battlecry fizzles but
  # the minion still gets summoned normally.
  game = GameManager().create_test_game()
  game.current_player.deck.clear()  # remove the randomly-generated deck's own pirates
  parrot = _fresh(game, "Captain's Parrot", game.current_player.hand)
  hand_before = len(game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == parrot][0]
  game.perform_action(play)
  assert parrot.parent == parrot.owner.board
  assert len(game.current_player.hand) == hand_before - 1  # lost parrot, drew nothing


# ---------------------------------------------------------------------------
# Doomsayer - trigger timing bug
# ---------------------------------------------------------------------------

def test_audit_doomsayer_survives_its_own_end_turn():
  # VANILLA: "At the start of your turn, destroy ALL minions." Doomsayer
  # should survive through the rest of the turn it's summoned AND through
  # the opponent's entire next turn - it only wipes the board once its
  # controller's own turn actually starts (untap).
  game = GameManager().create_test_game()
  doomsayer = _fresh(game, 'Doomsayer', game.current_player.board)
  wisp = _fresh(game, 'Wisp', game.current_player.board)
  game.end_turn()  # controller's turn ends, opponent's turn begins
  assert doomsayer.parent == doomsayer.owner.board
  assert wisp.parent == wisp.owner.board




def test_audit_doomsayer_destroys_all_minions_at_start_of_controllers_turn():
  game = GameManager().create_test_game()
  owner = game.current_player
  doomsayer = _fresh(game, 'Doomsayer', owner.board)
  friendly_extra = _fresh(game, 'Wisp', owner.board)
  enemy_wisp = _fresh(game, 'Wisp', owner.other_player.board)
  game.end_turn()  # -> opponent's turn
  game.end_turn()  # -> back to owner's turn
  game.untap()     # start-of-turn processing for owner
  assert doomsayer.parent == doomsayer.owner.graveyard
  assert friendly_extra.parent == friendly_extra.owner.graveyard
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard


# ---------------------------------------------------------------------------
# Big Game Hunter
# ---------------------------------------------------------------------------

def test_audit_big_game_hunter_destroys_7_plus_attack():
  game = GameManager().create_test_game()
  bgh = _fresh(game, 'Big Game Hunter', game.current_player.hand)
  big = _fresh(game, 'Boulderfist Ogre', game.current_player.other_player.board)  # 6/7, below threshold
  big.perm_attack = 1  # bump to 7 attack
  play = [a for a in game.get_available_actions(game.current_player) if a.source == bgh and a.targets == [big]][0]
  game.perform_action(play)
  assert big.parent == big.owner.graveyard


def test_audit_big_game_hunter_cannot_target_6_or_less():
  game = GameManager().create_test_game()
  bgh = _fresh(game, 'Big Game Hunter', game.current_player.hand)
  ogre = _fresh(game, 'Boulderfist Ogre', game.current_player.other_player.board)  # 6 attack
  targeted = [a for a in game.get_available_actions(game.current_player) if a.source == bgh and a.targets == [ogre]]
  assert targeted == []


def test_audit_big_game_hunter_can_target_own_minion():
  # VANILLA: "Destroy a minion with 7 or more Attack" - no owner restriction.
  game = GameManager().create_test_game()
  bgh = _fresh(game, 'Big Game Hunter', game.current_player.hand)
  friendly_big = _fresh(game, 'War Golem', game.current_player.board)  # 7/7
  play = [a for a in game.get_available_actions(game.current_player) if a.source == bgh and a.targets == [friendly_big]]
  assert len(play) == 1
  game.perform_action(play[0])
  assert friendly_big.parent == friendly_big.owner.graveyard


# ---------------------------------------------------------------------------
# Blood Knight
# ---------------------------------------------------------------------------

def test_audit_blood_knight_no_divine_shields_no_buff():
  game = GameManager().create_test_game()
  blood_knight = _fresh(game, 'Blood Knight', game.current_player.hand)
  _fresh(game, 'Wisp', game.current_player.board)
  _fresh(game, 'Wisp', game.current_player.other_player.board)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == blood_knight][0]
  game.perform_action(play)
  assert blood_knight.get_attack() == 3
  assert blood_knight.get_health() == 3


def test_audit_blood_knight_counts_enemy_and_friendly_shields():
  game = GameManager().create_test_game()
  blood_knight = _fresh(game, 'Blood Knight', game.current_player.hand)
  friendly_shield = _fresh(game, 'Argent Squire', game.current_player.board)
  enemy_shield = _fresh(game, 'Argent Squire', game.current_player.other_player.board)
  assert friendly_shield.has_attribute(Attributes.DIVINE_SHIELD)
  assert enemy_shield.has_attribute(Attributes.DIVINE_SHIELD)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == blood_knight][0]
  game.perform_action(play)
  assert not friendly_shield.has_attribute(Attributes.DIVINE_SHIELD)
  assert not enemy_shield.has_attribute(Attributes.DIVINE_SHIELD)
  assert blood_knight.get_attack() == 3 + 2 * 3
  assert blood_knight.get_health() == 3 + 2 * 3


# ---------------------------------------------------------------------------
# Murloc Warleader
# ---------------------------------------------------------------------------

def test_audit_murloc_warleader_buffs_both_sides_but_not_self():
  # VANILLA: "ALL other murlocs have +2/+1" - both friendly AND enemy.
  game = GameManager().create_test_game()
  warleader = _fresh(game, 'Murloc Warleader', game.current_player.board)
  friendly_murloc = _fresh(game, 'Murloc Raider', game.current_player.board)  # 2/1
  enemy_murloc = _fresh(game, 'Murloc Raider', game.current_player.other_player.board)
  assert warleader.get_attack() == 3  # unaffected by its own aura
  assert warleader.get_health() == 3
  assert friendly_murloc.get_attack() == 4
  assert friendly_murloc.get_health() == 2
  assert enemy_murloc.get_attack() == 4
  assert enemy_murloc.get_health() == 2


def test_audit_murloc_warleader_silence_removes_aura_immediately():
  # combo: Silence wipes the aura source's effect, so the aura recomputes to
  # zero on the very next stat read (auras are computed live, not baked in -
  # this is unrelated to known issue (3), which is about SetStats/SwapStats).
  game = GameManager().create_test_game()
  warleader = _fresh(game, 'Murloc Warleader', game.current_player.board)
  murloc = _fresh(game, 'Murloc Raider', game.current_player.board)
  assert murloc.get_attack() == 4
  owl = _fresh(game, 'Ironbeak Owl', game.current_player.hand)
  silence = [a for a in game.get_available_actions(game.current_player) if a.source == owl and a.targets == [warleader]][0]
  game.perform_action(silence)
  assert murloc.get_attack() == 2
  assert murloc.get_health() == 1


# ---------------------------------------------------------------------------
# Southsea Captain
# ---------------------------------------------------------------------------

def test_audit_southsea_captain_friendly_pirates_only():
  game = GameManager().create_test_game()
  captain = _fresh(game, 'Southsea Captain', game.current_player.board)
  friendly_pirate = _fresh(game, 'Southsea Deckhand', game.current_player.board)
  enemy_pirate = _fresh(game, 'Southsea Deckhand', game.current_player.other_player.board)
  assert captain.get_attack() == 3  # aura doesn't buff itself
  assert friendly_pirate.get_attack() == 3
  assert friendly_pirate.get_health() == 2
  assert enemy_pirate.get_attack() == 2  # not buffed - VANILLA text is "Your other Pirates"
  assert enemy_pirate.get_health() == 1


def test_audit_southsea_captain_silence_removes_aura_immediately():
  game = GameManager().create_test_game()
  captain = _fresh(game, 'Southsea Captain', game.current_player.board)
  pirate = _fresh(game, 'Southsea Deckhand', game.current_player.board)
  assert pirate.get_attack() == 3
  owl = _fresh(game, 'Ironbeak Owl', game.current_player.hand)
  silence = [a for a in game.get_available_actions(game.current_player) if a.source == owl and a.targets == [captain]][0]
  game.perform_action(silence)
  assert pirate.get_attack() == 2
  assert pirate.get_health() == 1


# ---------------------------------------------------------------------------
# Faceless Manipulator
# ---------------------------------------------------------------------------

def test_audit_faceless_manipulator_copies_stats_and_attributes():
  game = GameManager().create_test_game()
  target = _fresh(game, 'Argent Commander', game.current_player.other_player.board)  # 4/2 charge, divine shield
  faceless = _fresh(game, 'Faceless Manipulator', game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == faceless and a.targets == [target]][0]
  game.perform_action(play)
  assert faceless.get_attack() == target.original_attack
  assert faceless.get_health() == target.original_health
  assert faceless.has_attribute(Attributes.DIVINE_SHIELD)
  assert faceless.has_attribute(Attributes.CHARGE)


def test_audit_faceless_manipulator_copies_deathrattle_combo():
  # combo: copying Cairne Bloodhoof should also copy its deathrattle, so
  # killing the resulting copy summons a Baine Bloodhoof.
  game = GameManager().create_test_game()
  cairne = _fresh(game, 'Cairne Bloodhoof', game.current_player.other_player.board)
  faceless = _fresh(game, 'Faceless Manipulator', game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == faceless and a.targets == [cairne]][0]
  game.perform_action(play)
  game.handle_death(faceless)
  summoned = [c for c in game.current_player.board if c.name == 'Baine Bloodhoof']
  assert len(summoned) == 1
  assert summoned[0].get_attack() == 4
  assert summoned[0].get_health() == 5


def test_audit_faceless_manipulator_no_target_still_playable():
  # combo/edge case: with no minions anywhere to copy, Faceless can still be
  # played as a vanilla 3/3 (fizzled battlecry), it isn't blocked from hand.
  game = GameManager().create_test_game()
  faceless = _fresh(game, 'Faceless Manipulator', game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == faceless]
  assert len(play) == 1
  assert play[0].targets == []
  game.perform_action(play[0])
  assert faceless.parent == faceless.owner.board
  assert faceless.get_attack() == 3
  assert faceless.get_health() == 3


# ---------------------------------------------------------------------------
# Giants (Sea / Mountain / Molten)
# ---------------------------------------------------------------------------

def test_audit_sea_giant_costs_one_less_per_other_minion_both_sides():
  game = GameManager().create_test_game()
  sea_giant = _fresh(game, 'Sea Giant', game.current_player.hand)
  assert sea_giant.get_manacost() == 10
  _fresh(game, 'Wisp', game.current_player.board)
  assert sea_giant.get_manacost() == 9
  _fresh(game, 'Wisp', game.current_player.other_player.board)
  assert sea_giant.get_manacost() == 8


def test_audit_mountain_giant_costs_one_less_per_other_hand_card():
  game = GameManager().create_test_game()
  mountain_giant = _fresh(game, 'Mountain Giant', game.current_player.hand)
  assert mountain_giant.get_manacost() == 12
  _fresh(game, 'Wisp', game.current_player.hand)
  assert mountain_giant.get_manacost() == 11


def test_audit_molten_giant_costs_one_less_per_damage_taken():
  game = GameManager().create_test_game()
  molten_giant = _fresh(game, 'Molten Giant', game.current_player.hand)
  assert molten_giant.get_manacost() == 20
  game.deal_damage(game.current_player, 5)
  assert molten_giant.get_manacost() == 15


def test_audit_molten_giant_cost_recovers_after_healing():
  # combo/edge case: the aura is recomputed live, so healing the hero should
  # push the cost back up again (Voodoo Doctor heals 2).
  game = GameManager().create_test_game()
  molten_giant = _fresh(game, 'Molten Giant', game.current_player.hand)
  game.deal_damage(game.current_player, 10)
  assert molten_giant.get_manacost() == 10
  voodoo = _fresh(game, 'Voodoo Doctor', game.current_player.hand)
  heal = [a for a in game.get_available_actions(game.current_player) if a.source == voodoo and a.targets == [game.current_player]][0]
  game.perform_action(heal)
  assert molten_giant.get_manacost() == 12  # healed 2, so 2 fewer damage taken -> cost went back up by 2


# ---------------------------------------------------------------------------
# Alexstrasza - max_health cap bug
# ---------------------------------------------------------------------------

def test_audit_alexstrasza_sets_health_to_15():
  game = GameManager().create_test_game()
  alex = _fresh(game, 'Alexstrasza', game.current_player.hand)
  enemy = game.current_player.other_player
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == alex and a.targets == [enemy]][0]
  game.perform_action(cast)
  assert enemy.get_health() == 15


def test_audit_alexstrasza_does_not_reduce_max_health():
  # VANILLA: "Set a hero's remaining Health to 15" only changes CURRENT
  # health - it must not permanently cap max health, so the hero can still
  # be healed back above 15 afterwards.
  game = GameManager().create_test_game()
  alex = _fresh(game, 'Alexstrasza', game.current_player.hand)
  me = game.current_player
  me.health = 10
  cast = [a for a in game.get_available_actions(me) if a.source == alex and a.targets == [me]][0]
  game.perform_action(cast)
  assert me.get_health() == 15
  assert me.get_max_health() == 30




def test_audit_alexstrasza_healing_not_capped():
  # Alexstrasza sets CURRENT hero health to 15 without touching max health -
  # healing afterwards can go past 15 (up to the normal 30 cap).
  game = GameManager().create_test_game()
  alex = _fresh(game, 'Alexstrasza', game.current_player.hand)
  me = game.current_player
  me.health = 10
  cast = [a for a in game.get_available_actions(me) if a.source == alex and a.targets == [me]][0]
  game.perform_action(cast)
  voodoo = _fresh(game, 'Voodoo Doctor', game.current_player.hand)
  heal = [a for a in game.get_available_actions(me) if a.source == voodoo and a.targets == [me]][0]
  game.perform_action(heal)
  assert me.get_health() == 17


# ---------------------------------------------------------------------------
# Ragnaros the Firelord
# ---------------------------------------------------------------------------

def test_audit_ragnaros_cant_attack_and_damages_random_enemy():
  game = GameManager().create_test_game()
  ragnaros = _fresh(game, 'Ragnaros the Firelord', game.current_player.board)
  assert len([a for a in game.get_available_actions(game.current_player) if a.action_type == Actions.ATTACK and a.source == ragnaros]) == 0
  enemy = game.current_player.other_player
  enemy_health = enemy.get_health()
  game.end_turn()
  assert enemy.get_health() == enemy_health - 8


def test_audit_ragnaros_never_damages_own_side():
  game = GameManager().create_test_game()
  ragnaros = _fresh(game, 'Ragnaros the Firelord', game.current_player.board)
  friendly_wisp = _fresh(game, 'Wisp', game.current_player.board)
  me = game.current_player
  my_health_before = me.get_health()
  game.end_turn()
  assert me.get_health() == my_health_before
  assert ragnaros.get_health() == 8
  assert friendly_wisp.get_health() == 1


# ---------------------------------------------------------------------------
# Cairne Bloodhoof
# ---------------------------------------------------------------------------

def test_audit_cairne_deathrattle_summons_baine():
  game = GameManager().create_test_game()
  cairne = _fresh(game, 'Cairne Bloodhoof', game.current_player.board)
  game.handle_death(cairne)
  summoned = [c for c in game.current_player.board if c.name == 'Baine Bloodhoof']
  assert len(summoned) == 1
  assert summoned[0].get_attack() == 4
  assert summoned[0].get_health() == 5
  assert summoned[0].get_manacost() == 4


def test_audit_cairne_deathrattle_fills_its_own_vacated_slot_on_full_board():
  # combo/edge case: handle_death moves Cairne to the graveyard *before*
  # resolving its deathrattle, so even on a full (7/7) board, Baine gets to
  # take the slot Cairne itself just vacated instead of being blocked.
  game = GameManager().create_test_game()
  player = game.current_player
  cairne = _fresh(game, 'Cairne Bloodhoof', player.board)
  for _ in range(player.board.max_entries - 1):
    _fresh(game, 'Wisp', player.board)
  assert len(player.board) == player.board.max_entries
  game.handle_death(cairne)
  assert len(player.board) == player.board.max_entries
  assert any(c.name == 'Baine Bloodhoof' for c in player.board)


# ---------------------------------------------------------------------------
# Bloodmage Thalnos
# ---------------------------------------------------------------------------

def test_audit_bloodmage_thalnos_spell_damage_and_deathrattle_draw():
  game = GameManager().create_test_game()
  thalnos = _fresh(game, 'Bloodmage Thalnos', game.current_player.board)
  assert thalnos.has_attribute(Attributes.SPELL_DAMAGE)
  fireball = _fresh(game, 'Fireball', game.current_player.hand)
  enemy_wisp = _fresh(game, 'Wisp', game.current_player.other_player.board)
  cast = [a for a in game.get_available_actions(game.current_player) if a.source == fireball and a.targets == [enemy_wisp]][0]
  game.perform_action(cast)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard  # 6+1 spell damage overkills a 1-health Wisp

  hand_before = len(game.current_player.hand)
  game.handle_death(thalnos)
  assert len(game.current_player.hand) == hand_before + 1


# ---------------------------------------------------------------------------
# Leeroy Jenkins
# ---------------------------------------------------------------------------

def test_audit_leeroy_charge_and_summons_whelps_for_opponent():
  game = GameManager().create_test_game()
  leeroy = _fresh(game, 'Leeroy Jenkins', game.current_player.hand)
  enemy = game.current_player.other_player
  enemy_board_before = len(enemy.board)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == leeroy][0]
  game.perform_action(play)
  assert leeroy.has_attribute(Attributes.CHARGE)
  assert len(enemy.board) == enemy_board_before + 2
  assert all(c.name == 'Whelp' for c in enemy.board.get_all()[-2:])
  assert len(game.current_player.board) == 0 or leeroy.parent == leeroy.owner.board


# ---------------------------------------------------------------------------
# Baron Geddon
# ---------------------------------------------------------------------------

def test_audit_baron_geddon_hits_all_other_characters_both_sides():
  game = GameManager().create_test_game()
  geddon = _fresh(game, 'Baron Geddon', game.current_player.board)
  me = game.current_player
  friendly_wisp = _fresh(game, 'Wisp', me.board)
  enemy_wisp = _fresh(game, 'Wisp', me.other_player.board)
  my_health_before = me.get_health()
  enemy_health_before = me.other_player.get_health()
  game.end_turn()
  assert geddon.get_health() == 5  # not hit by its own effect
  assert friendly_wisp.parent == friendly_wisp.owner.graveyard
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert me.get_health() == my_health_before - 2  # VANILLA: "ALL other characters" hits its own hero too
  assert me.other_player.get_health() == enemy_health_before - 2


# ---------------------------------------------------------------------------
# Sylvanas Windrunner
# ---------------------------------------------------------------------------

def test_audit_sylvanas_steals_random_enemy_minion_on_death():
  game = GameManager().create_test_game()
  sylvanas = _fresh(game, 'Sylvanas Windrunner', game.current_player.board)
  enemy_wisp = _fresh(game, 'Wisp', game.current_player.other_player.board)
  game.handle_death(sylvanas)
  assert enemy_wisp.owner == game.current_player
  assert enemy_wisp in game.current_player.board.get_all()


def test_audit_sylvanas_steals_into_its_own_vacated_slot_on_full_board():
  # combo/edge case: like Cairne above, Sylvanas is moved to the graveyard
  # before her deathrattle resolves, so a "full" 7/7 board (with Sylvanas as
  # one of the 7) still has room for the stolen minion in her old slot.
  game = GameManager().create_test_game()
  player = game.current_player
  sylvanas = _fresh(game, 'Sylvanas Windrunner', player.board)
  for _ in range(player.board.max_entries - 1):
    _fresh(game, 'Wisp', player.board)
  assert len(player.board) == player.board.max_entries
  enemy_wisp = _fresh(game, 'Wisp', player.other_player.board)
  game.handle_death(sylvanas)
  assert enemy_wisp.owner == player
  assert enemy_wisp in player.board.get_all()


def test_audit_sylvanas_destroys_stolen_minion_if_board_truly_full():
  # the TakeControl full-board branch (destroy instead of steal) only bites
  # when the board is already full with minions OTHER than Sylvanas herself
  # (e.g. she was already off the board / copied elsewhere) - verified
  # directly against TakeControl rather than via a self-deathrattle, since
  # a self-triggered deathrattle always vacates its own slot first.
  game = GameManager().create_test_game()
  player = game.current_player
  # Sylvanas belongs to `player` (owner determines who receives the stolen
  # minion) but is parked in the graveyard rather than the board, so she
  # doesn't consume one of the 7 slots we're about to fill for the test.
  sylvanas = _fresh(game, 'Sylvanas Windrunner', player.graveyard)
  for _ in range(player.board.max_entries):
    _fresh(game, 'Wisp', player.board)
  assert len(player.board) == player.board.max_entries
  enemy_wisp = _fresh(game, 'Wisp', player.other_player.board)
  # directly resolve TakeControl as Sylvanas' deathrattle would, targeting
  # the enemy wisp, on a board that's genuinely full of OTHER minions.
  sylvanas.effect.resolve_action(game, Action(Actions.CAST_EFFECT, sylvanas, [enemy_wisp]))
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert enemy_wisp not in player.board.get_all()


# ---------------------------------------------------------------------------
# Harrison Jones
# ---------------------------------------------------------------------------

def test_audit_harrison_jones_destroys_weapon_and_draws_durability():
  game = GameManager().create_test_game()
  _fresh(game, 'Arcanite Reaper', game.current_player.other_player)  # 5 attack, 2 durability
  harrison = _fresh(game, 'Harrison Jones', game.current_player.hand)
  hand_before = len(game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == harrison][0]
  game.perform_action(play)
  assert not game.current_player.other_player.weapon
  assert len(game.current_player.hand) == hand_before - 1 + 2  # lost Harrison, drew 2 (durability)


def test_audit_harrison_jones_no_weapon_fizzles_but_still_playable():
  game = GameManager().create_test_game()
  harrison = _fresh(game, 'Harrison Jones', game.current_player.hand)
  hand_before = len(game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == harrison]
  assert len(play) == 1
  game.perform_action(play[0])
  assert harrison.parent == harrison.owner.board
  assert len(game.current_player.hand) == hand_before - 1  # only lost Harrison, drew nothing


# ---------------------------------------------------------------------------
# The Black Knight
# ---------------------------------------------------------------------------

def test_audit_black_knight_destroys_enemy_taunt():
  game = GameManager().create_test_game()
  black_knight = _fresh(game, 'The Black Knight', game.current_player.hand)
  enemy_taunt = _fresh(game, 'Goldshire Footman', game.current_player.other_player.board)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == black_knight and a.targets == [enemy_taunt]][0]
  game.perform_action(play)
  assert enemy_taunt.parent == enemy_taunt.owner.graveyard


def test_audit_black_knight_cannot_target_non_taunt_or_friendly_taunt():
  game = GameManager().create_test_game()
  black_knight = _fresh(game, 'The Black Knight', game.current_player.hand)
  enemy_non_taunt = _fresh(game, 'Wisp', game.current_player.other_player.board)
  friendly_taunt = _fresh(game, 'Goldshire Footman', game.current_player.board)
  targeted = [a for a in game.get_available_actions(game.current_player)
              if a.source == black_knight and len(a.targets) > 0]
  assert targeted == []  # neither the non-taunt enemy nor the friendly taunt is a legal target


# ---------------------------------------------------------------------------
# Tinkmaster Overspark
# ---------------------------------------------------------------------------

def test_audit_tinkmaster_transforms_target_into_devilsaur_or_squirrel():
  game = GameManager().create_test_game()
  target = _fresh(game, 'Wisp', game.current_player.other_player.board)
  tinkmaster = _fresh(game, 'Tinkmaster Overspark', game.current_player.hand)
  play = [a for a in game.get_available_actions(game.current_player) if a.source == tinkmaster and a.targets == [target]][0]
  game.perform_action(play)
  transformed = [c for c in game.current_player.other_player.board if c.name in ('Devilsaur', 'Squirrel')]
  assert len(transformed) == 1
  assert target.parent == target.owner.graveyard


def test_audit_tinkmaster_cannot_target_itself():
  game = GameManager().create_test_game()
  tinkmaster = _fresh(game, 'Tinkmaster Overspark', game.current_player.hand)
  targeted_self = [a for a in game.get_available_actions(game.current_player)
                    if a.source == tinkmaster and tinkmaster in a.targets]
  assert targeted_self == []


# ---------------------------------------------------------------------------
# Ysera
# ---------------------------------------------------------------------------

def test_audit_ysera_adds_a_dream_card_at_end_of_turn():
  game = GameManager().create_test_game()
  owner = game.current_player
  _fresh(game, 'Ysera', owner.board)
  hand_before = len(owner.hand)
  game.end_turn()
  assert len(owner.hand) == hand_before + 1
  added = owner.hand.get_all()[0]
  assert added.name in ('Emerald Drake', 'Laughing Sister', 'Dream', 'Ysera Awakens')


# ---------------------------------------------------------------------------
# Nat Pagle
# ---------------------------------------------------------------------------

def test_audit_nat_pagle_uses_start_of_turn_trigger():
  # unlike Doomsayer, Nat Pagle is correctly wired to FRIENDLY_UNTAP for its
  # "at the start of your turn" text.
  game = GameManager().create_test_game()
  _fresh(game, 'Nat Pagle', game.current_player.board)
  hand_before = len(game.current_player.hand)
  game.untap()
  # 50/50 extra draw on top of the normal turn draw - never fewer than +1
  assert len(game.current_player.hand) >= hand_before + 1
  assert len(game.current_player.hand) <= hand_before + 2


# ---------------------------------------------------------------------------
# Nozdormu / Lorewalker Cho / ETC / Millhouse - documented simplifications
# ---------------------------------------------------------------------------

def test_audit_nozdormu_is_vanilla_stats_only():
  # readme.md: real text ("15 seconds per turn") has no meaning in a
  # non-realtime simulator - documented simplification, vanilla body only.
  game = GameManager().create_test_game()
  nozdormu = _fresh(game, 'Nozdormu', game.current_player.hand)
  assert nozdormu.effect is None
  assert nozdormu.creature_type == CreatureTypes.DRAGON


def test_audit_lorewalker_cho_gives_copy_to_the_non_caster():
  game = GameManager().create_test_game()
  cho_owner = game.current_player
  enemy = cho_owner.other_player
  _fresh(game, 'Lorewalker Cho', cho_owner.board)
  missiles = _fresh(game, 'Arcane Missiles', cho_owner.hand)
  cast = [a for a in game.get_available_actions(cho_owner) if a.source == missiles][0]
  game.perform_action(cast)
  assert any(c.name == 'Arcane Missiles' for c in enemy.hand)


def test_audit_elite_tauren_chieftain_is_vanilla_stats_only():
  # readme.md: real hero-power-swap mechanic isn't supported - documented
  # simplification, vanilla 5/5 body only.
  game = GameManager().create_test_game()
  etc = _fresh(game, 'Elite Tauren Chieftain', game.current_player.hand)
  assert etc.effect is None


def test_audit_millhouse_manastorm_is_vanilla_stats_only():
  # readme.md: real "enemy spells cost (0) next turn" needs per-card,
  # auto-reverting cost changes ChangeCost doesn't support - documented
  # simplification, vanilla 4/4 body only.
  game = GameManager().create_test_game()
  millhouse = _fresh(game, 'Millhouse Manastorm', game.current_player.hand)
  assert millhouse.effect is None
