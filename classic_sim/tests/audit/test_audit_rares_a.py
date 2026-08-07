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


def act(game, pred):
    """Find the single available action matching pred."""
    return [a for a in game.get_available_actions(game.current_player) if pred(a)][0]


# =====================================================================
# Slice: get_rare_cards() indices 0..17
#   Angry Chicken, Bloodsail Corsair, Lightwarden, Murloc Tidecaller,
#   Secretkeeper, Young Priestess, Ancient Watcher, Crazed Alchemist,
#   Knife Juggler, Mana Addict, Mana Wraith, Master Swordsmith,
#   Pint-Sized Summoner, Sunfury Protector, Wild Pyromancer, Alarm-o-Bot,
#   Arcane Golem, Coldlight Oracle
# =====================================================================


# --- Angry Chicken -----------------------------------------------------

def test_angry_chicken_stats_and_type():
    game = GameManager().create_test_game()
    chicken = game.game_manager.get_card('Angry Chicken', game.current_player.hand)
    assert chicken.get_manacost() == 1
    assert chicken.get_attack() == 1
    assert chicken.get_health() == 1
    assert chicken.creature_type == CreatureTypes.BEAST


def test_angry_chicken_enrage_toggles_off_when_healed_back_to_full():
    # VANILLA text: "Enrage: +5 Attack." Enrage is a live condition, not a
    # one-shot flag: healing back to full should turn it off again.
    game = GameManager().create_test_game()
    chicken = game.game_manager.get_card('Angry Chicken', game.current_player.board)
    defender = game.game_manager.get_card('Defender of Argus', game.current_player.hand)
    play_defender = act(game, lambda a: a.source == defender)
    game.perform_action(play_defender)  # +1/+1 to chicken -> 2/2
    assert chicken.get_attack() == 2
    assert chicken.get_health() == 2

    game.deal_damage(chicken, 1)
    assert chicken.get_health() == 1
    assert chicken.get_attack() == 7  # base 1 + defender buff 1 + enrage 5

    farseer = game.game_manager.get_card('Earthen Ring Farseer', game.current_player.hand)
    heal_chicken = act(game, lambda a: a.source == farseer and a.targets[0] == chicken)
    game.perform_action(heal_chicken)
    assert chicken.get_health() == 2
    assert chicken.get_max_health() == 2
    assert chicken.get_attack() == 2  # enrage should be off again, full health


# --- Bloodsail Corsair ---------------------------------------------------

def test_bloodsail_corsair_stats_and_type():
    game = GameManager().create_test_game()
    corsair = game.game_manager.get_card('Bloodsail Corsair', game.current_player.hand)
    assert corsair.get_manacost() == 1
    assert corsair.get_attack() == 1
    assert corsair.get_health() == 2
    assert corsair.creature_type == CreatureTypes.PIRATE


def test_bloodsail_corsair_battlecry_whiffs_with_no_enemy_weapon():
    # Real card: "Remove 1 Durability from your opponent's weapon." If the
    # opponent has no weapon, the battlecry should simply do nothing rather
    # than making the card unplayable.
    game = GameManager().create_test_game()
    corsair = game.game_manager.get_card('Bloodsail Corsair', game.current_player.hand)
    assert not game.current_player.other_player.weapon
    actions = [a for a in game.get_available_actions(game.current_player) if a.source == corsair]
    assert len(actions) == 1
    assert actions[0].targets == []
    game.perform_action(actions[0])
    assert corsair.parent == corsair.owner.board
    assert not game.current_player.other_player.weapon


def test_bloodsail_corsair_breaks_weapon_at_zero_durability():
    game = GameManager().create_test_game()
    corsair = game.game_manager.get_card('Bloodsail Corsair', game.current_player.hand)
    game.game_manager.get_card('Generic Weapon', game.current_player.other_player)
    assert game.current_player.other_player.weapon.get_health() == 2
    play_corsair = act(game, lambda a: a.source == corsair)
    game.perform_action(play_corsair)
    assert game.current_player.other_player.weapon.get_health() == 1
    game.deal_damage(game.current_player.other_player.weapon, 1)
    assert not game.current_player.other_player.weapon


# --- Lightwarden -----------------------------------------------------------

def test_lightwarden_stats():
    game = GameManager().create_test_game()
    lightwarden = game.game_manager.get_card('Lightwarden', game.current_player.hand)
    assert lightwarden.get_manacost() == 1
    assert lightwarden.get_attack() == 1
    assert lightwarden.get_health() == 2


def test_lightwarden_triggers_on_friendly_minion_heal_not_just_hero():
    # VANILLA text: "Whenever A CHARACTER is healed" (any character, not
    # just the hero).
    game = GameManager().create_test_game()
    lightwarden = game.game_manager.get_card('Lightwarden', game.current_player.board)
    grizzly = game.game_manager.get_card('Ironfur Grizzly', game.current_player.board)
    game.deal_damage(grizzly, 1)
    farseer = game.game_manager.get_card('Earthen Ring Farseer', game.current_player.hand)
    heal_grizzly = act(game, lambda a: a.source == farseer and a.targets[0] == grizzly)
    assert lightwarden.get_attack() == 1
    game.perform_action(heal_grizzly)
    assert lightwarden.get_attack() == 3
    assert grizzly.get_health() == 3


# --- Murloc Tidecaller -----------------------------------------------------

def test_murloc_tidecaller_stats_and_type():
    game = GameManager().create_test_game()
    tidecaller = game.game_manager.get_card('Murloc Tidecaller', game.current_player.hand)
    assert tidecaller.get_manacost() == 1
    assert tidecaller.get_attack() == 1
    assert tidecaller.get_health() == 2
    assert tidecaller.creature_type == CreatureTypes.MURLOC


def test_murloc_tidecaller_triggers_on_token_murloc_summon():
    game = GameManager().create_test_game()
    tidecaller = game.game_manager.get_card('Murloc Tidecaller', game.current_player.board)
    tidehunter = game.game_manager.get_card('Murloc Tidehunter', game.current_player.hand)
    assert tidecaller.get_attack() == 1
    play_tidehunter = act(game, lambda a: a.source == tidehunter)
    game.perform_action(play_tidehunter)
    # Tidehunter's own summon (+1) AND its Murloc Scout token's summon (+1)
    # should both trigger Tidecaller for a total of +2.
    assert tidecaller.get_attack() == 3


# --- Secretkeeper -----------------------------------------------------------

def test_secretkeeper_triggers_on_enemy_secret_too():
    # VANILLA text: "Whenever a Secret is played" - not restricted to
    # friendly secrets.
    game = GameManager().create_test_game()
    secretkeeper = game.game_manager.get_card('Secretkeeper', game.current_player.board)
    enemy_snipe = game.game_manager.get_card('Snipe', game.current_player.other_player.hand)
    assert secretkeeper.get_attack() == 1
    assert secretkeeper.get_health() == 2
    game.end_turn()
    cast_enemy_secret = act(game, lambda a: a.source == enemy_snipe)
    game.perform_action(cast_enemy_secret)
    assert secretkeeper.get_attack() == 2
    assert secretkeeper.get_health() == 3


# --- Young Priestess ---------------------------------------------------

def test_young_priestess_stats():
    game = GameManager().create_test_game()
    yp = game.game_manager.get_card('Young Priestess', game.current_player.hand)
    assert yp.get_manacost() == 1
    assert yp.get_attack() == 2
    assert yp.get_health() == 1


def test_young_priestess_never_buffs_herself():
    # "give ANOTHER random friendly minion +1 Health" - with only herself on
    # board there should be no valid target, and she must not self-buff.
    game = GameManager().create_test_game()
    yp = game.game_manager.get_card('Young Priestess', game.current_player.board)
    game.end_turn()
    game.untap()
    game.end_turn()
    assert yp.get_health() == 1
    assert yp.get_max_health() == 1


# --- Ancient Watcher --------------------------------------------------------

def test_ancient_watcher_stats():
    game = GameManager().create_test_game()
    watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.hand)
    assert watcher.get_manacost() == 2
    assert watcher.get_attack() == 4
    assert watcher.get_health() == 5


def test_ancient_watcher_is_not_taunt():
    # "Can't attack" is not the same as Taunt: enemies must still be able to
    # attack past the Watcher and choose smaller minions.
    game = GameManager().create_test_game()
    watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.other_player.board)
    small = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
    attacker = game.game_manager.get_card('Wisp', game.current_player.board)
    targets = game.get_available_targets(attacker)
    assert watcher in targets
    assert small in targets  # not forced onto the Watcher


# --- Crazed Alchemist --------------------------------------------------

def test_crazed_alchemist_stats():
    game = GameManager().create_test_game()
    alch = game.game_manager.get_card('Crazed Alchemist', game.current_player.hand)
    assert alch.get_manacost() == 2
    assert alch.get_attack() == 2
    assert alch.get_health() == 2


def test_crazed_alchemist_can_target_enemy_minion():
    # Real text: "Swap the Attack and Health of A minion" (any minion,
    # friendly or enemy).
    game = GameManager().create_test_game()
    alch = game.game_manager.get_card('Crazed Alchemist', game.current_player.hand)
    enemy_watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.other_player.board)
    play_alch = act(game, lambda a: a.source == alch and a.targets[0] == enemy_watcher)
    game.perform_action(play_alch)
    assert enemy_watcher.get_attack() == 5
    assert enemy_watcher.get_health() == 4


@pytest.mark.xfail(reason="KNOWN LIMITATION: Silence does not revert SwapStats, so a "
                           "minion swapped by Crazed Alchemist keeps the swapped "
                           "stats instead of returning to its printed values.",
                    strict=False)
def test_crazed_alchemist_swap_reverts_on_silence():
    game = GameManager().create_test_game()
    alch = game.game_manager.get_card('Crazed Alchemist', game.current_player.hand)
    watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.board)
    play_alch = act(game, lambda a: a.source == alch and a.targets[0] == watcher)
    game.perform_action(play_alch)
    assert watcher.get_attack() == 5
    assert watcher.get_health() == 4
    owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
    silence_watcher = act(game, lambda a: a.source == owl and a.targets[0] == watcher)
    game.perform_action(silence_watcher)
    assert watcher.get_attack() == 4
    assert watcher.get_health() == 5


# --- Knife Juggler -----------------------------------------------------

def test_knife_juggler_stats():
    game = GameManager().create_test_game()
    kj = game.game_manager.get_card('Knife Juggler', game.current_player.hand)
    assert kj.get_manacost() == 2
    assert kj.get_attack() == 3
    assert kj.get_health() == 2


def test_knife_juggler_stacks_with_multiple_copies():
    game = GameManager().create_test_game()
    game.game_manager.get_card('Knife Juggler', game.current_player.board)
    game.game_manager.get_card('Knife Juggler', game.current_player.board)
    wisp = game.game_manager.get_card('Wisp', game.current_player.hand)
    before = game.current_player.other_player.get_health()
    play_wisp = act(game, lambda a: a.source == wisp)
    game.perform_action(play_wisp)
    assert game.current_player.other_player.get_health() == before - 2


def test_knife_juggler_triggers_on_token_summon():
    game = GameManager().create_test_game()
    game.game_manager.get_card('Knife Juggler', game.current_player.board)
    tidehunter = game.game_manager.get_card('Murloc Tidehunter', game.current_player.hand)
    before = game.current_player.other_player.get_health()
    play_tidehunter = act(game, lambda a: a.source == tidehunter)
    game.perform_action(play_tidehunter)
    assert game.current_player.other_player.get_health() == before - 2


# --- Mana Addict ---------------------------------------------------------

def test_mana_addict_stats():
    game = GameManager().create_test_game()
    addict = game.game_manager.get_card('Mana Addict', game.current_player.hand)
    assert addict.get_manacost() == 2
    assert addict.get_attack() == 1
    assert addict.get_health() == 3


def test_mana_addict_stacks_within_turn_and_resets_on_end_turn():
    game = GameManager().create_test_game()
    addict = game.game_manager.get_card('Mana Addict', game.current_player.board)
    fireball1 = game.game_manager.get_card('Fireball', game.current_player.hand)
    fireball2 = game.game_manager.get_card('Fireball', game.current_player.hand)
    assert addict.get_attack() == 1
    cast1 = act(game, lambda a: a.source == fireball1 and a.targets[0] == game.current_player.other_player)
    game.perform_action(cast1)
    assert addict.get_attack() == 3
    cast2 = act(game, lambda a: a.source == fireball2 and a.targets[0] == game.current_player.other_player)
    game.perform_action(cast2)
    assert addict.get_attack() == 5
    game.end_turn()
    assert addict.get_attack() == 1


# --- Mana Wraith -----------------------------------------------------------

def test_mana_wraith_stats():
    game = GameManager().create_test_game()
    wraith = game.game_manager.get_card('Mana Wraith', game.current_player.hand)
    assert wraith.get_manacost() == 2
    assert wraith.get_attack() == 2
    assert wraith.get_health() == 2


def test_mana_wraith_taxes_both_players_minions_but_not_spells():
    game = GameManager().create_test_game()
    game.game_manager.get_card('Mana Wraith', game.current_player.board)
    wisp = game.game_manager.get_card('Wisp', game.current_player.hand)
    fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
    enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.hand)
    assert wisp.get_manacost() == 1  # 0 + 1
    assert fireball.get_manacost() == 4  # spells unaffected
    assert enemy_wisp.get_manacost() == 1  # ALL minions, both sides


def test_mana_wraith_aura_stops_on_silence():
    game = GameManager().create_test_game()
    wraith = game.game_manager.get_card('Mana Wraith', game.current_player.board)
    wisp = game.game_manager.get_card('Wisp', game.current_player.hand)
    assert wisp.get_manacost() == 1
    owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
    silence_wraith = act(game, lambda a: a.source == owl and a.targets[0] == wraith)
    game.perform_action(silence_wraith)
    assert wisp.get_manacost() == 0


# --- Master Swordsmith -------------------------------------------------

def test_master_swordsmith_stats():
    game = GameManager().create_test_game()
    ms = game.game_manager.get_card('Master Swordsmith', game.current_player.hand)
    assert ms.get_manacost() == 2
    assert ms.get_attack() == 1
    assert ms.get_health() == 3


def test_master_swordsmith_never_buffs_itself_only_others():
    game = GameManager().create_test_game()
    ms1 = game.game_manager.get_card('Master Swordsmith', game.current_player.board)
    ms2 = game.game_manager.get_card('Master Swordsmith', game.current_player.board)
    assert ms1.get_attack() == 1
    assert ms2.get_attack() == 1
    game.end_turn()
    game.untap()
    # each Swordsmith buffs the OTHER, never itself
    assert ms1.get_attack() == 2
    assert ms2.get_attack() == 2


# --- Pint-Sized Summoner -------------------------------------------------

def test_pint_sized_summoner_stats():
    game = GameManager().create_test_game()
    pint = game.game_manager.get_card('Pint-Sized Summoner', game.current_player.hand)
    assert pint.get_manacost() == 2
    assert pint.get_attack() == 2
    assert pint.get_health() == 2


def test_pint_sized_summoner_only_discounts_first_minion_of_turn():
    game = GameManager().create_test_game()
    game.game_manager.get_card('Pint-Sized Summoner', game.current_player.board)
    wisp1 = game.game_manager.get_card('Wisp', game.current_player.hand)
    wisp2 = game.game_manager.get_card('Wisp', game.current_player.hand)
    watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.hand)
    assert watcher.get_manacost() == 1  # 2 - 1
    play_wisp1 = act(game, lambda a: a.source == wisp1)
    game.perform_action(play_wisp1)
    assert watcher.get_manacost() == 2  # discount used up by wisp1
    assert wisp2.get_manacost() == 0


def test_pint_sized_summoner_discount_cancels_mana_wraith_tax():
    game = GameManager().create_test_game()
    game.game_manager.get_card('Pint-Sized Summoner', game.current_player.board)
    game.game_manager.get_card('Mana Wraith', game.current_player.board)
    wisp1 = game.game_manager.get_card('Wisp', game.current_player.hand)
    wisp2 = game.game_manager.get_card('Wisp', game.current_player.hand)
    assert wisp1.get_manacost() == 0  # 0 + 1 (wraith) - 1 (pint) = 0
    play_wisp1 = act(game, lambda a: a.source == wisp1)
    game.perform_action(play_wisp1)
    assert wisp2.get_manacost() == 1  # discount used, only the wraith tax remains


# --- Sunfury Protector ---------------------------------------------------

def test_sunfury_protector_gives_taunt_to_adjacent_only():
    game = GameManager().create_test_game()
    sunfury = game.game_manager.get_card('Sunfury Protector', game.current_player.hand)
    wisp1 = game.game_manager.get_card('Wisp', game.current_player.board)
    wisp2 = game.game_manager.get_card('Wisp', game.current_player.board)
    play_sunfury = act(game, lambda a: a.source == sunfury)
    game.perform_action(play_sunfury)
    #the new minion joins the right end of the board, so only wisp2 (the
    #previous rightmost minion) is adjacent to it
    assert not wisp1.has_attribute(Attributes.TAUNT)
    assert wisp2.has_attribute(Attributes.TAUNT)
    assert not sunfury.has_attribute(Attributes.TAUNT)


def test_sunfury_protector_stats_match_vanilla():
    game = GameManager().create_test_game()
    sunfury = game.game_manager.get_card('Sunfury Protector', game.current_player.hand)
    assert sunfury.get_manacost() == 2
    assert sunfury.get_attack() == 2
    assert sunfury.get_health() == 3


# --- Wild Pyromancer ---------------------------------------------------

def test_wild_pyromancer_stats():
    game = GameManager().create_test_game()
    pyro = game.game_manager.get_card('Wild Pyromancer', game.current_player.hand)
    assert pyro.get_manacost() == 2
    assert pyro.get_attack() == 3
    assert pyro.get_health() == 2


def test_wild_pyromancer_hits_self_exactly_once_per_spell():
    # Regression guard: Wild Pyromancer must take exactly 1 damage from its
    # own trigger, not 2 (the ALL branch excludes the source and a separate
    # SELF-targeted sub-effect re-adds exactly one hit on the source).
    game = GameManager().create_test_game()
    pyro = game.game_manager.get_card('Wild Pyromancer', game.current_player.board)
    missiles = game.game_manager.get_card('Arcane Missiles', game.current_player.hand)
    cast_missiles = act(game, lambda a: a.source == missiles)
    game.perform_action(cast_missiles)
    assert pyro.parent == pyro.owner.board
    assert pyro.get_health() == 1


def test_wild_pyromancer_aoe_still_fires_deathrattles():
    # 1-health minion killed by the AOE ping should still fire its own
    # deathrattle (Loot Hoarder: draw a card).
    game = GameManager().create_test_game()
    game.game_manager.get_card('Wild Pyromancer', game.current_player.board)
    hoarder = game.game_manager.get_card('Loot Hoarder', game.current_player.board)
    fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
    deck_before = len(game.current_player.deck)
    cast_fireball = act(game, lambda a: a.source == fireball and a.targets[0] == game.current_player.other_player)
    game.perform_action(cast_fireball)
    assert hoarder.parent == hoarder.owner.graveyard
    assert len(game.current_player.deck) == deck_before - 1  # deathrattle drew a card


# --- Alarm-o-Bot -----------------------------------------------------------

def test_alarm_o_bot_stats_and_type():
    game = GameManager().create_test_game()
    alarm = game.game_manager.get_card('Alarm-o-Bot', game.current_player.hand)
    assert alarm.get_manacost() == 3
    assert alarm.get_attack() == 0
    assert alarm.get_health() == 3
    assert alarm.creature_type == CreatureTypes.MECH


def test_alarm_o_bot_swaps_with_a_hand_minion_on_untap():
    game = GameManager().create_test_game()
    alarm = game.game_manager.get_card('Alarm-o-Bot', game.current_player.board)
    watcher = game.game_manager.get_card('Ancient Watcher', game.current_player.hand)
    game.end_turn()
    game.untap()
    assert alarm.parent == alarm.owner.board
    assert watcher.parent == watcher.owner.hand
    game.end_turn()
    game.untap()
    assert alarm.parent == alarm.owner.hand
    assert watcher.parent == watcher.owner.board


def test_alarm_o_bot_does_not_swap_when_hand_has_no_minions():
    game = GameManager().create_test_game()
    alarm = game.game_manager.get_card('Alarm-o-Bot', game.current_player.board)
    game.game_manager.get_card('Fireball', game.current_player.hand)
    game.end_turn()
    game.untap()
    assert alarm.parent == alarm.owner.board  # nothing swappable, stays put


# --- Arcane Golem -----------------------------------------------------

def test_arcane_golem_stats_and_charge():
    game_manager = GameManager()
    game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
    game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
    game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing())
    game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing())
    game = game_manager.create_game()
    game.current_player.current_mana = 3
    arcane_golem = game.game_manager.get_card('Arcane Golem', game.current_player.hand)
    assert arcane_golem.get_manacost() == 3
    assert arcane_golem.get_attack() == 4
    assert arcane_golem.get_health() == 2
    cast_golem = act(game, lambda a: a.source == arcane_golem)
    game.perform_action(cast_golem)
    assert arcane_golem.has_attribute(Attributes.CHARGE)
    assert game.current_player.other_player.max_mana == 1
    assert game.current_player.other_player.current_mana == 1
    # Charge should let it swing the turn it is played
    attack_actions = [a for a in game.get_available_actions(game.current_player)
                       if a.action_type == Actions.ATTACK and a.source == arcane_golem]
    assert len(attack_actions) > 0


def test_arcane_golem_at_ten_mana_does_not_overflow_max_mana():
    # NOTE (simplification): real Hearthstone rule at 10 crystals is that the
    # extra crystal is simply wasted; this engine instead grants an
    # "Excess Mana" spell (draw a card) as a stand-in reward. Documented
    # here as current behaviour, not asserted as strictly correct.
    game_manager = GameManager()
    game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
    game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
    game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing())
    game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing())
    game = game_manager.create_game()
    game.current_player.current_mana = 4
    game.current_player.other_player.max_mana = 10
    game.current_player.other_player.current_mana = 10
    arcane_golem = game.game_manager.get_card('Arcane Golem', game.current_player.hand)
    cast_golem = act(game, lambda a: a.source == arcane_golem)
    game.perform_action(cast_golem)
    assert game.current_player.other_player.max_mana == 10


# --- Coldlight Oracle -----------------------------------------------------

def test_coldlight_oracle_stats_and_type():
    game = GameManager().create_test_game()
    oracle = game.game_manager.get_card('Coldlight Oracle', game.current_player.hand)
    assert oracle.get_manacost() == 3
    assert oracle.get_attack() == 2
    assert oracle.get_health() == 2
    assert oracle.creature_type == CreatureTypes.MURLOC


def test_coldlight_oracle_draws_two_for_each_player():
    game = GameManager().create_test_game()
    assert len(game.current_player.hand) == 0
    assert len(game.current_player.other_player.hand) == 0
    oracle = game.game_manager.get_card('Coldlight Oracle', game.current_player.hand)
    play_oracle = act(game, lambda a: a.source == oracle)
    game.perform_action(play_oracle)
    assert len(game.current_player.hand) == 2
    assert len(game.current_player.other_player.hand) == 2


def test_coldlight_oracle_fatigues_a_player_with_an_empty_deck():
    game = GameManager().create_test_game()
    game.current_player.deck.clear()
    oracle = game.game_manager.get_card('Coldlight Oracle', game.current_player.hand)
    hp_before = game.current_player.get_health()
    play_oracle = act(game, lambda a: a.source == oracle)
    game.perform_action(play_oracle)
    # two failed draws from an empty deck: fatigue for 1, then 2 -> 3 total
    assert game.current_player.get_health() == hp_before - 3
    assert game.current_player.fatigue_damage == 3
