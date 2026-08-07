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

# Curse of Naxxramas (2014). Undertaker is deliberately the PRE-nerf +1/+1
# version - the Jan 2015 nerf to +1/+0 is what modern card databases carry.


NAXX_SETS = [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR,
             CardSets.TEST_CARDS, CardSets.NAXX_NEUTRAL, CardSets.NAXX_HUNTER, CardSets.NAXX_MAGE, CardSets.NAXX_WARRIOR]


def naxx_game(player_class=Classes.WARRIOR, enemy_class=Classes.MAGE):
  game_manager = GameManager()
  game_manager.create_player_pool(NAXX_SETS)
  game_manager.create_enemy_pool(NAXX_SETS)
  game_manager.create_player(player_class, Deck.generate_random, GreedyAction())
  game_manager.create_enemy(enemy_class, Deck.generate_random, GreedyAction())
  game = game_manager.create_game()
  game.player.hand.clear()
  game.enemy.hand.clear()
  game.player.current_mana = 10
  game.enemy.current_mana = 10
  game.current_player = game.player
  return game

def play(game, card, target=None):
  actions = [action for action in game.get_available_actions(card.owner)
             if action.source == card and (target is None or action.targets == [target])]
  game.perform_action(actions[0])
  return actions[0]


# --- set composition ---------------------------------------------------------

def test_naxx_pool_sizes():
  assert len(get_naxx_neutral_cards()) == 21
  assert len(get_naxx_hunter_cards()) == 1
  assert len(get_naxx_mage_cards()) == 1
  assert len(get_naxx_warrior_cards()) == 1

def test_naxx_cards_do_not_leak_into_the_classic_pool():
  classic = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR], None)
  naxx_names = [card.name for card in get_naxx_neutral_cards() + get_naxx_hunter_cards() + get_naxx_mage_cards() + get_naxx_warrior_cards()]
  assert len(classic) == 221
  assert [card.name for card in classic if card.name in naxx_names] == []

def test_naxx_sets_are_added_by_name():
  pool = build_pool([CardSets.NAXX_NEUTRAL, CardSets.NAXX_WARRIOR], None)
  assert len(pool) == 22
  assert "Death's Bite" in [card.name for card in pool]
  assert 'Webspinner' not in [card.name for card in pool]


# --- Zombie Chow (1/2/3, Deathrattle: restore 5 Health to the ENEMY hero) ----

def test_zombie_chow_stats():
  game = naxx_game()
  chow = game.game_manager.get_card('Zombie Chow', game.current_player.hand)
  assert (chow.get_manacost(), chow.get_attack(), chow.get_health()) == (1, 2, 3)

def test_zombie_chow_deathrattle_heals_the_enemy_hero():
  game = naxx_game()
  player = game.current_player
  player.other_player.health = 20
  player.health = 20
  chow = game.game_manager.get_card('Zombie Chow', player.board)
  game.handle_death(chow)
  assert player.other_player.health == 25
  assert player.health == 20 #never its own hero

def test_zombie_chow_healing_is_capped_at_full_health():
  game = naxx_game()
  player = game.current_player
  player.other_player.health = 28
  chow = game.game_manager.get_card('Zombie Chow', player.board)
  game.handle_death(chow)
  assert player.other_player.health == 30


# --- Undertaker (1/1/2, deathrattle summons give +1/+1) ---------------------

def test_undertaker_stats():
  game = naxx_game()
  undertaker = game.game_manager.get_card('Undertaker', game.current_player.hand)
  assert (undertaker.get_manacost(), undertaker.get_attack(), undertaker.get_health()) == (1, 1, 2)

def test_undertaker_grows_when_a_deathrattle_minion_is_played():
  game = naxx_game()
  player = game.current_player
  undertaker = game.game_manager.get_card('Undertaker', player.board)
  play(game, game.game_manager.get_card('Haunted Creeper', player.hand))
  assert (undertaker.get_attack(), undertaker.get_health()) == (2, 3)

def test_undertaker_ignores_minions_without_a_deathrattle():
  game = naxx_game()
  player = game.current_player
  undertaker = game.game_manager.get_card('Undertaker', player.board)
  play(game, game.game_manager.get_card('Chillwind Yeti', player.hand))
  play(game, game.game_manager.get_card('Novice Engineer', player.hand)) #battlecry, not deathrattle
  assert (undertaker.get_attack(), undertaker.get_health()) == (1, 2)

def test_undertaker_ignores_tokens_without_a_deathrattle():
  game = naxx_game()
  player = game.current_player
  undertaker = game.game_manager.get_card('Undertaker', player.board)
  creeper = game.game_manager.get_card('Haunted Creeper', player.board)
  game.handle_death(creeper) #summons two Spectral Spiders, neither has a deathrattle
  assert player.board.names().count('Spectral Spider') == 2
  assert (undertaker.get_attack(), undertaker.get_health()) == (1, 2)

def test_undertaker_grows_from_a_summoned_deathrattle_token():
  #Mirror Entity summons (not plays) a copy of the enemy's Haunted Creeper
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  enemy = player.other_player
  undertaker = game.game_manager.get_card('Undertaker', player.board)
  play(game, game.game_manager.get_card('Mirror Entity', player.hand))
  game.current_player = enemy #secrets only fire on the opponent's turn
  play(game, game.game_manager.get_card('Haunted Creeper', enemy.hand))
  assert 'Haunted Creeper' in player.board.names()
  assert (undertaker.get_attack(), undertaker.get_health()) == (2, 3)

def test_undertaker_buff_is_permanent():
  game = naxx_game()
  player = game.current_player
  undertaker = game.game_manager.get_card('Undertaker', player.board)
  play(game, game.game_manager.get_card('Haunted Creeper', player.hand))
  game.end_turn()
  game.end_turn()
  game.untap()
  assert (undertaker.get_attack(), undertaker.get_health()) == (2, 3)


# --- Echoing Ooze (2/1/2, Battlecry: summon a copy) -------------------------

def test_echoing_ooze_stats():
  game = naxx_game()
  ooze = game.game_manager.get_card('Echoing Ooze', game.current_player.hand)
  assert (ooze.get_manacost(), ooze.get_attack(), ooze.get_health()) == (2, 1, 2)

def test_echoing_ooze_summons_a_copy_of_itself():
  #SIMPLIFICATION: the real Ooze copies itself at the END of the turn, so buffs
  #played on it in between are copied as well. Without delayed-summon machinery
  #the copy arrives immediately, always with printed stats.
  game = naxx_game()
  player = game.current_player
  ooze = game.game_manager.get_card('Echoing Ooze', player.hand)
  play(game, ooze)
  assert player.board.names() == ['Echoing Ooze', 'Echoing Ooze']
  copy = [minion for minion in player.board if minion != ooze][0]
  assert (copy.get_attack(), copy.get_health()) == (1, 2)
  assert not copy.collectable

def test_echoing_ooze_copy_does_not_summon_further_copies():
  game = naxx_game()
  player = game.current_player
  play(game, game.game_manager.get_card('Echoing Ooze', player.hand))
  assert len(player.board) == 2 #no runaway chain


# --- Haunted Creeper (2/1/2 Beast, Deathrattle: two 1/1 Spectral Spiders) ---

def test_haunted_creeper_stats_and_type():
  game = naxx_game()
  creeper = game.game_manager.get_card('Haunted Creeper', game.current_player.hand)
  assert (creeper.get_manacost(), creeper.get_attack(), creeper.get_health()) == (2, 1, 2)
  assert creeper.creature_type == CreatureTypes.BEAST

def test_haunted_creeper_summons_two_spectral_spiders():
  game = naxx_game()
  player = game.current_player
  creeper = game.game_manager.get_card('Haunted Creeper', player.board)
  game.handle_death(creeper)
  spiders = [minion for minion in player.board if minion.name == 'Spectral Spider']
  assert len(spiders) == 2
  assert all((spider.get_attack(), spider.get_health()) == (1, 1) for spider in spiders)

def test_haunted_creeper_only_fills_the_space_it_has():
  game = naxx_game()
  player = game.current_player
  for _ in range(6):
    game.game_manager.get_card('Wisp', player.board)
  creeper = game.game_manager.get_card('Haunted Creeper', player.board)
  game.handle_death(creeper)
  assert len(player.board) == 7
  assert player.board.names().count('Spectral Spider') == 1


# --- Mad Scientist (2/2/2, Deathrattle: a Secret from your deck into play) --

def test_mad_scientist_stats():
  game = naxx_game()
  scientist = game.game_manager.get_card('Mad Scientist', game.current_player.hand)
  assert (scientist.get_manacost(), scientist.get_attack(), scientist.get_health()) == (2, 2, 2)

def test_mad_scientist_puts_a_secret_from_the_deck_into_play():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  player.deck.clear()
  game.game_manager.get_card('Counterspell', player.deck)
  scientist = game.game_manager.get_card('Mad Scientist', player.board)
  game.handle_death(scientist)
  assert player.secrets_zone.names() == ['Counterspell']
  assert len(player.deck) == 0
  assert len(player.hand) == 0 #into play, not into hand

def test_mad_scientist_does_nothing_without_a_secret_in_the_deck():
  game = naxx_game()
  player = game.current_player
  player.deck.clear()
  game.game_manager.get_card('Chillwind Yeti', player.deck)
  scientist = game.game_manager.get_card('Mad Scientist', player.board)
  game.handle_death(scientist)
  assert len(player.secrets_zone) == 0
  assert len(player.deck) == 1

def test_mad_scientist_never_duplicates_an_active_secret():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  play(game, game.game_manager.get_card('Counterspell', player.hand))
  player.deck.clear()
  game.game_manager.get_card('Counterspell', player.deck)
  scientist = game.game_manager.get_card('Mad Scientist', player.board)
  game.handle_death(scientist)
  assert player.secrets_zone.names() == ['Counterspell']
  assert len(player.deck) == 1 #the duplicate stays in the deck

def test_mad_scientist_respects_the_five_secret_cap():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  for name in ['Explosive Trap', 'Freezing Trap', 'Misdirection', 'Snake Trap', 'Snipe']:
    play(game, game.game_manager.get_card(name, player.hand))
  assert len(player.secrets_zone) == 5
  player.deck.clear()
  game.game_manager.get_card('Counterspell', player.deck)
  scientist = game.game_manager.get_card('Mad Scientist', player.board)
  game.handle_death(scientist)
  assert len(player.secrets_zone) == 5
  assert len(player.deck) == 1


# --- Nerub'ar Weblord (2/1/4, Battlecry minions cost 2 more) ----------------

def test_nerubar_weblord_stats():
  game = naxx_game()
  weblord = game.game_manager.get_card("Nerub'ar Weblord", game.current_player.hand)
  assert (weblord.get_manacost(), weblord.get_attack(), weblord.get_health()) == (2, 1, 4)

def test_nerubar_weblord_taxes_battlecry_minions_on_both_sides():
  game = naxx_game()
  player = game.current_player
  friendly_battlecry = game.game_manager.get_card('Novice Engineer', player.hand)
  enemy_battlecry = game.game_manager.get_card('Novice Engineer', player.other_player.hand)
  assert friendly_battlecry.get_manacost() == 2
  game.game_manager.get_card("Nerub'ar Weblord", player.board)
  assert friendly_battlecry.get_manacost() == 4
  assert enemy_battlecry.get_manacost() == 4

def test_nerubar_weblord_leaves_other_cards_alone():
  game = naxx_game()
  player = game.current_player
  vanilla = game.game_manager.get_card('Chillwind Yeti', player.hand)
  spell = game.game_manager.get_card('Fireball', player.hand)
  weapon = game.game_manager.get_card('Fiery War Axe', player.hand)
  deathrattle = game.game_manager.get_card('Haunted Creeper', player.hand)
  game.game_manager.get_card("Nerub'ar Weblord", player.board)
  assert vanilla.get_manacost() == 4
  assert spell.get_manacost() == 4
  assert weapon.get_manacost() == 2
  assert deathrattle.get_manacost() == 2

def test_nerubar_weblord_tax_ends_when_it_leaves_the_board():
  game = naxx_game()
  player = game.current_player
  engineer = game.game_manager.get_card('Novice Engineer', player.hand)
  weblord = game.game_manager.get_card("Nerub'ar Weblord", player.board)
  assert engineer.get_manacost() == 4
  game.handle_death(weblord)
  assert engineer.get_manacost() == 2


# --- Nerubian Egg (2/0/2, Deathrattle: summon a 4/4 Nerubian) ---------------

def test_nerubian_egg_stats():
  game = naxx_game()
  egg = game.game_manager.get_card('Nerubian Egg', game.current_player.hand)
  assert (egg.get_manacost(), egg.get_attack(), egg.get_health()) == (2, 0, 2)

def test_nerubian_egg_hatches_a_four_four():
  game = naxx_game()
  player = game.current_player
  egg = game.game_manager.get_card('Nerubian Egg', player.board)
  game.handle_death(egg)
  nerubian = [minion for minion in player.board if minion.name == 'Nerubian'][0]
  assert (nerubian.get_attack(), nerubian.get_health()) == (4, 4)


# --- Unstable Ghoul (2/1/3 Taunt, Deathrattle: 1 damage to ALL minions) -----

def test_unstable_ghoul_stats_and_taunt():
  game = naxx_game()
  ghoul = game.game_manager.get_card('Unstable Ghoul', game.current_player.hand)
  assert (ghoul.get_manacost(), ghoul.get_attack(), ghoul.get_health()) == (2, 1, 3)
  assert ghoul.has_attribute(Attributes.TAUNT)

def test_unstable_ghoul_damages_every_minion_on_death():
  game = naxx_game()
  player = game.current_player
  friendly = game.game_manager.get_card('Chillwind Yeti', player.board)
  enemy = game.game_manager.get_card('Boulderfist Ogre', player.other_player.board)
  ghoul = game.game_manager.get_card('Unstable Ghoul', player.board)
  game.handle_death(ghoul)
  assert friendly.get_health() == 4
  assert enemy.get_health() == 6
  assert player.other_player.health == 30 #minions only, never heroes

def test_unstable_ghoul_sweeps_one_health_minions():
  game = naxx_game()
  player = game.current_player
  wisps = [game.game_manager.get_card('Wisp', player.other_player.board) for _ in range(3)]
  ghoul = game.game_manager.get_card('Unstable Ghoul', player.board)
  game.handle_death(ghoul)
  assert len(player.other_player.board) == 0
  assert all(wisp.parent == player.other_player.graveyard for wisp in wisps)


# --- Dancing Swords (3/4/4, Deathrattle: your OPPONENT draws a card) --------

def test_dancing_swords_stats():
  game = naxx_game()
  swords = game.game_manager.get_card('Dancing Swords', game.current_player.hand)
  assert (swords.get_manacost(), swords.get_attack(), swords.get_health()) == (3, 4, 4)

def test_dancing_swords_gives_the_opponent_the_card():
  game = naxx_game()
  player = game.current_player
  enemy_hand_before = len(player.other_player.hand)
  swords = game.game_manager.get_card('Dancing Swords', player.board)
  game.handle_death(swords)
  assert len(player.other_player.hand) == enemy_hand_before + 1
  assert len(player.hand) == 0


# --- Deathlord (3/2/8 Taunt, Deathrattle: opponent puts a minion into play) --

def test_deathlord_stats_and_taunt():
  game = naxx_game()
  deathlord = game.game_manager.get_card('Deathlord', game.current_player.hand)
  assert (deathlord.get_manacost(), deathlord.get_attack(), deathlord.get_health()) == (3, 2, 8)
  assert deathlord.has_attribute(Attributes.TAUNT)

def test_deathlord_pulls_a_minion_from_the_opponents_deck():
  game = naxx_game()
  player = game.current_player
  enemy = player.other_player
  enemy.deck.clear()
  game.game_manager.get_card('Chillwind Yeti', enemy.deck)
  deathlord = game.game_manager.get_card('Deathlord', player.board)
  game.handle_death(deathlord)
  assert enemy.board.names() == ['Chillwind Yeti']
  assert len(enemy.deck) == 0
  assert len(player.board) == 0 #the minion belongs to the opponent

def test_deathlord_only_pulls_minions():
  game = naxx_game()
  player = game.current_player
  enemy = player.other_player
  enemy.deck.clear()
  game.game_manager.get_card('Fireball', enemy.deck)
  deathlord = game.game_manager.get_card('Deathlord', player.board)
  game.handle_death(deathlord)
  assert len(enemy.board) == 0
  assert enemy.deck.names() == ['Fireball']

def test_deathlord_does_nothing_when_the_opponents_board_is_full():
  game = naxx_game()
  player = game.current_player
  enemy = player.other_player
  for _ in range(7):
    game.game_manager.get_card('Wisp', enemy.board)
  enemy.deck.clear()
  game.game_manager.get_card('Chillwind Yeti', enemy.deck)
  deathlord = game.game_manager.get_card('Deathlord', player.board)
  game.handle_death(deathlord)
  assert len(enemy.board) == 7
  assert len(enemy.deck) == 1

def test_deathlord_summon_is_a_real_summon():
  #the pulled minion triggers the opponent's summon watchers
  game = naxx_game()
  player = game.current_player
  enemy = player.other_player
  enemy_undertaker = game.game_manager.get_card('Undertaker', enemy.board)
  enemy.deck.clear()
  game.game_manager.get_card('Haunted Creeper', enemy.deck)
  deathlord = game.game_manager.get_card('Deathlord', player.board)
  game.handle_death(deathlord)
  assert (enemy_undertaker.get_attack(), enemy_undertaker.get_health()) == (2, 3)


# --- Shade of Naxxramas (3/2/2 Stealth, +1/+1 at the start of your turn) ----

def test_shade_of_naxxramas_stats_and_stealth():
  game = naxx_game()
  shade = game.game_manager.get_card('Shade of Naxxramas', game.current_player.hand)
  assert (shade.get_manacost(), shade.get_attack(), shade.get_health()) == (3, 2, 2)
  assert shade.has_attribute(Attributes.STEALTH)

def test_shade_of_naxxramas_grows_every_one_of_your_turns():
  game = naxx_game()
  player = game.current_player
  shade = game.game_manager.get_card('Shade of Naxxramas', player.board)
  game.end_turn()
  game.untap() #the enemy's turn
  assert (shade.get_attack(), shade.get_health()) == (2, 2)
  game.end_turn()
  game.untap() #back to the shade's owner
  assert (shade.get_attack(), shade.get_health()) == (3, 3)
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert (shade.get_attack(), shade.get_health()) == (4, 4)

def test_shade_of_naxxramas_keeps_its_stealth_while_growing():
  game = naxx_game()
  player = game.current_player
  shade = game.game_manager.get_card('Shade of Naxxramas', player.board)
  game.end_turn()
  game.end_turn()
  game.untap()
  assert shade.has_attribute(Attributes.STEALTH)


# --- Stoneskin Gargoyle (3/1/4, restore to full at the start of your turn) --

def test_stoneskin_gargoyle_stats():
  game = naxx_game()
  gargoyle = game.game_manager.get_card('Stoneskin Gargoyle', game.current_player.hand)
  assert (gargoyle.get_manacost(), gargoyle.get_attack(), gargoyle.get_health()) == (3, 1, 4)

def test_stoneskin_gargoyle_heals_itself_to_full():
  game = naxx_game()
  player = game.current_player
  gargoyle = game.game_manager.get_card('Stoneskin Gargoyle', player.board)
  game.deal_damage(gargoyle, 3)
  assert gargoyle.get_health() == 1
  game.end_turn()
  game.end_turn()
  game.untap()
  assert gargoyle.get_health() == 4

def test_stoneskin_gargoyle_does_not_heal_on_the_enemy_turn():
  game = naxx_game()
  player = game.current_player
  gargoyle = game.game_manager.get_card('Stoneskin Gargoyle', player.board)
  game.deal_damage(gargoyle, 3)
  game.end_turn()
  game.untap() #the enemy's untap
  assert gargoyle.get_health() == 1

def test_stoneskin_gargoyle_never_exceeds_its_maximum_health():
  game = naxx_game()
  player = game.current_player
  gargoyle = game.game_manager.get_card('Stoneskin Gargoyle', player.board)
  game.end_turn()
  game.end_turn()
  game.untap()
  assert gargoyle.get_health() == 4


# --- Baron Rivendare (4/1/7, your deathrattles trigger twice) ---------------

def test_baron_rivendare_stats():
  game = naxx_game()
  baron = game.game_manager.get_card('Baron Rivendare', game.current_player.hand)
  assert (baron.get_manacost(), baron.get_attack(), baron.get_health()) == (4, 1, 7)

def test_baron_rivendare_doubles_a_friendly_deathrattle():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card('Baron Rivendare', player.board)
  creeper = game.game_manager.get_card('Haunted Creeper', player.board)
  game.handle_death(creeper)
  assert player.board.names().count('Spectral Spider') == 4

def test_baron_rivendare_does_not_double_enemy_deathrattles():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card('Baron Rivendare', player.board)
  enemy_creeper = game.game_manager.get_card('Haunted Creeper', player.other_player.board)
  game.handle_death(enemy_creeper)
  assert player.other_player.board.names().count('Spectral Spider') == 2

def test_a_silenced_baron_rivendare_stops_doubling():
  game = naxx_game()
  player = game.current_player
  baron = game.game_manager.get_card('Baron Rivendare', player.board)
  wailing_soul = game.game_manager.get_card('Wailing Soul', player.hand)
  play(game, wailing_soul) #silences the Baron
  creeper = game.game_manager.get_card('Haunted Creeper', player.board)
  game.handle_death(creeper)
  assert baron.effect is None
  assert player.board.names().count('Spectral Spider') == 2

def test_baron_rivendare_does_not_double_once_he_has_left_the_board():
  game = naxx_game()
  player = game.current_player
  baron = game.game_manager.get_card('Baron Rivendare', player.board)
  game.handle_death(baron)
  creeper = game.game_manager.get_card('Haunted Creeper', player.board)
  game.handle_death(creeper)
  assert player.board.names().count('Spectral Spider') == 2


# --- Wailing Soul (4/3/5, Battlecry: Silence your OTHER minions) ------------

def test_wailing_soul_stats():
  game = naxx_game()
  soul = game.game_manager.get_card('Wailing Soul', game.current_player.hand)
  assert (soul.get_manacost(), soul.get_attack(), soul.get_health()) == (4, 3, 5)

def test_wailing_soul_silences_your_other_minions_only():
  game = naxx_game()
  player = game.current_player
  friendly = game.game_manager.get_card('Argent Squire', player.board)
  enemy = game.game_manager.get_card('Argent Squire', player.other_player.board)
  soul = game.game_manager.get_card('Wailing Soul', player.hand)
  play(game, soul)
  assert not friendly.has_attribute(Attributes.DIVINE_SHIELD)
  assert enemy.has_attribute(Attributes.DIVINE_SHIELD)

def test_wailing_soul_does_not_silence_itself():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card('Wisp', player.board)
  soul = game.game_manager.get_card('Wailing Soul', player.hand)
  play(game, soul)
  assert soul.effect is not None #it keeps its own (already spent) battlecry

def test_wailing_soul_is_playable_with_an_empty_board():
  game = naxx_game()
  player = game.current_player
  soul = game.game_manager.get_card('Wailing Soul', player.hand)
  play(game, soul)
  assert soul.parent == player.board


# --- Feugen and Stalagg (5 mana legendaries, Thaddius when both die) --------

def test_feugen_and_stalagg_stats():
  game = naxx_game()
  player = game.current_player
  feugen = game.game_manager.get_card('Feugen', player.hand)
  stalagg = game.game_manager.get_card('Stalagg', player.hand)
  assert (feugen.get_manacost(), feugen.get_attack(), feugen.get_health()) == (5, 4, 7)
  assert (stalagg.get_manacost(), stalagg.get_attack(), stalagg.get_health()) == (5, 7, 4)

def test_one_twin_alone_summons_nothing():
  game = naxx_game()
  player = game.current_player
  feugen = game.game_manager.get_card('Feugen', player.board)
  game.handle_death(feugen)
  assert len(player.board) == 0

def test_the_second_twin_to_die_summons_thaddius():
  game = naxx_game()
  player = game.current_player
  feugen = game.game_manager.get_card('Feugen', player.board)
  stalagg = game.game_manager.get_card('Stalagg', player.board)
  game.handle_death(feugen)
  game.handle_death(stalagg)
  assert player.board.names() == ['Thaddius']
  thaddius = player.board.get_all()[0]
  assert (thaddius.get_attack(), thaddius.get_health()) == (11, 11)

def test_thaddius_arrives_in_either_death_order():
  game = naxx_game()
  player = game.current_player
  feugen = game.game_manager.get_card('Feugen', player.board)
  stalagg = game.game_manager.get_card('Stalagg', player.board)
  game.handle_death(stalagg)
  game.handle_death(feugen)
  assert player.board.names() == ['Thaddius']

def test_a_twin_that_died_on_the_other_side_does_not_count():
  game = naxx_game()
  player = game.current_player
  enemy_stalagg = game.game_manager.get_card('Stalagg', player.other_player.board)
  game.handle_death(enemy_stalagg)
  feugen = game.game_manager.get_card('Feugen', player.board)
  game.handle_death(feugen)
  assert len(player.board) == 0

def test_the_twins_remember_deaths_from_earlier_turns():
  game = naxx_game()
  player = game.current_player
  feugen = game.game_manager.get_card('Feugen', player.board)
  game.handle_death(feugen)
  game.end_turn()
  game.end_turn()
  game.untap()
  stalagg = game.game_manager.get_card('Stalagg', player.board)
  game.handle_death(stalagg)
  assert 'Thaddius' in player.board.names()


# --- Loatheb (5/5/5, Battlecry: enemy spells cost 5 more next turn) --------

def test_loatheb_stats():
  game = naxx_game()
  loatheb = game.game_manager.get_card('Loatheb', game.current_player.hand)
  assert (loatheb.get_manacost(), loatheb.get_attack(), loatheb.get_health()) == (5, 5, 5)

def test_loatheb_taxes_the_enemys_spells():
  game = naxx_game()
  player = game.current_player
  enemy_fireball = game.game_manager.get_card('Fireball', player.other_player.hand)
  own_fireball = game.game_manager.get_card('Fireball', player.hand)
  play(game, game.game_manager.get_card('Loatheb', player.hand))
  assert enemy_fireball.get_manacost() == 9
  assert own_fireball.get_manacost() == 4 #only the opponent pays

def test_loatheb_tax_survives_the_whole_enemy_turn():
  game = naxx_game()
  player = game.current_player
  enemy_fireball = game.game_manager.get_card('Fireball', player.other_player.hand)
  play(game, game.game_manager.get_card('Loatheb', player.hand))
  game.end_turn()
  game.untap() #the taxed turn starts
  assert enemy_fireball.get_manacost() == 9
  game.end_turn()
  game.untap() #Loatheb's controller starts their turn: the tax expires
  assert enemy_fireball.get_manacost() == 4

def test_loatheb_also_taxes_secrets():
  game = naxx_game(enemy_class=Classes.MAGE)
  player = game.current_player
  enemy_secret = game.game_manager.get_card('Counterspell', player.other_player.hand)
  play(game, game.game_manager.get_card('Loatheb', player.hand))
  assert enemy_secret.get_manacost() == 8

def test_loatheb_leaves_enemy_minions_and_weapons_alone():
  game = naxx_game()
  player = game.current_player
  enemy_minion = game.game_manager.get_card('Chillwind Yeti', player.other_player.hand)
  enemy_weapon = game.game_manager.get_card('Fiery War Axe', player.other_player.hand)
  play(game, game.game_manager.get_card('Loatheb', player.hand))
  assert enemy_minion.get_manacost() == 4
  assert enemy_weapon.get_manacost() == 2


# --- Sludge Belcher (5/3/5 Taunt, Deathrattle: a 1/2 Slime with Taunt) -----

def test_sludge_belcher_stats_and_taunt():
  game = naxx_game()
  belcher = game.game_manager.get_card('Sludge Belcher', game.current_player.hand)
  assert (belcher.get_manacost(), belcher.get_attack(), belcher.get_health()) == (5, 3, 5)
  assert belcher.has_attribute(Attributes.TAUNT)

def test_sludge_belcher_leaves_a_taunting_slime():
  game = naxx_game()
  player = game.current_player
  belcher = game.game_manager.get_card('Sludge Belcher', player.board)
  game.handle_death(belcher)
  slime = [minion for minion in player.board if minion.name == 'Slime'][0]
  assert (slime.get_attack(), slime.get_health()) == (1, 2)
  assert slime.has_attribute(Attributes.TAUNT)


# --- Spectral Knight (5/4/6, can't be targeted by spells or Hero Powers) ---

def test_spectral_knight_stats_and_hexproof():
  game = naxx_game()
  knight = game.game_manager.get_card('Spectral Knight', game.current_player.hand)
  assert (knight.get_manacost(), knight.get_attack(), knight.get_health()) == (5, 4, 6)
  assert knight.has_attribute(Attributes.HEXPROOF)

def test_spectral_knight_cannot_be_hit_by_spells_or_hero_powers():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  knight = game.game_manager.get_card('Spectral Knight', player.other_player.board)
  game.game_manager.get_card('Fireball', player.hand)
  actions = game.get_available_actions(player)
  spell_targets = [action.targets[0] for action in actions if action.action_type == Actions.CAST_SPELL]
  hero_power_targets = [action.targets[0] for action in actions if action.action_type == Actions.CAST_HERO_POWER]
  assert knight not in spell_targets
  assert knight not in hero_power_targets

def test_spectral_knight_can_still_be_attacked_and_hit_by_aoe():
  game = naxx_game()
  player = game.current_player
  knight = game.game_manager.get_card('Spectral Knight', player.other_player.board)
  attacker = game.game_manager.get_card('Chillwind Yeti', player.board)
  attacker.attacks_this_turn = 0
  attack = [action for action in game.get_available_actions(player)
            if action.action_type == Actions.ATTACK and action.targets == [knight]]
  assert len(attack) == 1
  game.perform_action(attack[0])
  assert knight.get_health() == 2
  ghoul = game.game_manager.get_card('Unstable Ghoul', player.board)
  game.handle_death(ghoul)
  assert knight.get_health() == 1


# --- Maexxna (6/2/8 Beast, Poisonous) --------------------------------------

def test_maexxna_stats_and_keywords():
  game = naxx_game()
  maexxna = game.game_manager.get_card('Maexxna', game.current_player.hand)
  assert (maexxna.get_manacost(), maexxna.get_attack(), maexxna.get_health()) == (6, 2, 8)
  assert maexxna.creature_type == CreatureTypes.BEAST
  assert maexxna.has_attribute(Attributes.POISONOUS)

def test_maexxna_destroys_whatever_she_damages():
  game = naxx_game()
  player = game.current_player
  maexxna = game.game_manager.get_card('Maexxna', player.board)
  maexxna.attacks_this_turn = 0
  ogre = game.game_manager.get_card('Boulderfist Ogre', player.other_player.board)
  game.perform_action(Action(Actions.ATTACK, maexxna, [ogre]))
  assert ogre.parent == player.other_player.graveyard
  assert maexxna.parent == player.board


# --- Kel'Thuzad (8/6/8, resummon this turn's friendly dead each turn) ------

def test_kel_thuzad_stats():
  game = naxx_game()
  kel_thuzad = game.game_manager.get_card("Kel'Thuzad", game.current_player.hand)
  assert (kel_thuzad.get_manacost(), kel_thuzad.get_attack(), kel_thuzad.get_health()) == (8, 6, 8)

def test_kel_thuzad_resummons_friendly_minions_that_died_this_turn():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card("Kel'Thuzad", player.board)
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  game.handle_death(yeti)
  assert 'Chillwind Yeti' not in player.board.names()
  game.end_turn()
  assert player.board.names().count('Chillwind Yeti') == 1

def test_kel_thuzad_resummons_at_the_end_of_the_enemy_turn_too():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card("Kel'Thuzad", player.board)
  game.end_turn() #now the enemy's turn
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  game.handle_death(yeti)
  game.end_turn()
  assert player.board.names().count('Chillwind Yeti') == 1

def test_kel_thuzad_ignores_enemy_minions():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card("Kel'Thuzad", player.board)
  enemy_yeti = game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  game.handle_death(enemy_yeti)
  game.end_turn()
  assert len(player.other_player.board) == 0
  assert player.board.names() == ["Kel'Thuzad"]

def test_kel_thuzad_resummons_pristine_copies():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card("Kel'Thuzad", player.board)
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  yeti.perm_attack = 5 #a buff it picked up in play
  game.deal_damage(yeti, 2)
  game.handle_death(yeti)
  game.end_turn()
  resummoned = [minion for minion in player.board if minion.name == 'Chillwind Yeti'][0]
  assert (resummoned.get_attack(), resummoned.get_health()) == (4, 5)
  assert resummoned.attacks_this_turn == -1 #summoning sick, like any new summon

def test_a_dead_kel_thuzad_resummons_nothing():
  game = naxx_game()
  player = game.current_player
  kel_thuzad = game.game_manager.get_card("Kel'Thuzad", player.board)
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  game.handle_death(yeti)
  game.handle_death(kel_thuzad)
  game.end_turn()
  assert len(player.board) == 0

def test_kel_thuzad_only_resummons_this_turns_dead():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card("Kel'Thuzad", player.board)
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  game.handle_death(yeti)
  game.end_turn()
  assert player.board.names().count('Chillwind Yeti') == 1
  game.end_turn() #nothing new died
  assert player.board.names().count('Chillwind Yeti') == 1

def test_kel_thuzad_stops_at_a_full_board():
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card("Kel'Thuzad", player.board)
  for _ in range(3):
    game.handle_death(game.game_manager.get_card('Wisp', player.board))
  for _ in range(6):
    game.game_manager.get_card('Bloodfen Raptor', player.board)
  assert len(player.board) == 7
  game.end_turn()
  assert len(player.board) == 7


# --- Webspinner (hunter, 1/1/1 Beast, Deathrattle: a random Beast card) ----

def test_webspinner_stats_and_type():
  game = naxx_game()
  webspinner = game.game_manager.get_card('Webspinner', game.current_player.hand)
  assert (webspinner.get_manacost(), webspinner.get_attack(), webspinner.get_health()) == (1, 1, 1)
  assert webspinner.creature_type == CreatureTypes.BEAST

def test_webspinner_adds_a_random_beast_to_your_hand():
  game = naxx_game()
  player = game.current_player
  webspinner = game.game_manager.get_card('Webspinner', player.board)
  game.handle_death(webspinner)
  assert len(player.hand) == 1
  assert player.hand.get_all()[0].creature_type == CreatureTypes.BEAST
  assert len(player.other_player.hand) == 0


# --- Duplicate (mage, 3 mana Secret: 2 copies of a dead friendly minion) --

def test_duplicate_is_a_three_mana_secret():
  game = naxx_game(player_class=Classes.MAGE)
  duplicate = game.game_manager.get_card('Duplicate', game.current_player.hand)
  assert duplicate.get_manacost() == 3
  assert duplicate.card_type == CardTypes.SECRET

def test_duplicate_puts_two_copies_into_your_hand():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  play(game, game.game_manager.get_card('Duplicate', player.hand))
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  game.current_player = player.other_player #secrets only fire on the opponent's turn
  game.handle_death(yeti)
  assert player.hand.names() == ['Chillwind Yeti', 'Chillwind Yeti']
  assert len(player.secrets_zone) == 0 #the secret is spent

def test_duplicate_copies_are_pristine():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  play(game, game.game_manager.get_card('Duplicate', player.hand))
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  yeti.perm_attack = 4
  game.deal_damage(yeti, 1)
  game.current_player = player.other_player
  game.handle_death(yeti)
  copies = player.hand.get_all()
  assert all((copy.get_attack(), copy.get_health()) == (4, 5) for copy in copies)

def test_duplicate_does_not_fire_on_its_owners_turn():
  #real secrets never trigger during their owner's own turn
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  play(game, game.game_manager.get_card('Duplicate', player.hand))
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  game.handle_death(yeti)
  assert len(player.hand) == 0
  assert player.secrets_zone.names() == ['Duplicate']

def test_duplicate_ignores_enemy_minion_deaths():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  play(game, game.game_manager.get_card('Duplicate', player.hand))
  enemy_yeti = game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  game.current_player = player.other_player
  game.handle_death(enemy_yeti)
  assert len(player.hand) == 0
  assert player.secrets_zone.names() == ['Duplicate']

def test_duplicate_stops_at_a_full_hand():
  game = naxx_game(player_class=Classes.MAGE)
  player = game.current_player
  play(game, game.game_manager.get_card('Duplicate', player.hand))
  for _ in range(9):
    game.game_manager.get_card('Wisp', player.hand)
  yeti = game.game_manager.get_card('Chillwind Yeti', player.board)
  game.current_player = player.other_player
  game.handle_death(yeti)
  assert len(player.hand) == 10
  assert player.hand.names().count('Chillwind Yeti') == 1


# --- Death's Bite (warrior, 4 mana 4/2, Deathrattle: 1 damage to all) -----

def test_deaths_bite_stats():
  game = naxx_game()
  weapon = game.game_manager.get_card("Death's Bite", game.current_player.hand)
  assert weapon.get_manacost() == 4
  assert weapon.card_type == CardTypes.WEAPON
  assert (weapon.get_attack(), weapon.get_health()) == (4, 2)

def test_deaths_bite_deathrattle_fires_when_it_runs_out_of_durability():
  game = naxx_game()
  player = game.current_player
  friendly = game.game_manager.get_card('Chillwind Yeti', player.board)
  enemy = game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  play(game, game.game_manager.get_card("Death's Bite", player.hand))
  for _ in range(2):
    player.attacks_this_turn = 0
    game.perform_action(Action(Actions.ATTACK, player, [player.other_player]))
  assert player.weapon is None
  assert friendly.get_health() == 4 and enemy.get_health() == 4

def test_deaths_bite_deathrattle_fires_when_the_weapon_is_destroyed():
  game = naxx_game()
  player = game.current_player
  enemy = player.other_player
  wisp = game.game_manager.get_card('Wisp', enemy.board)
  play(game, game.game_manager.get_card("Death's Bite", player.hand))
  game.current_player = enemy
  ooze = game.game_manager.get_card('Acidic Swamp Ooze', enemy.hand) #Battlecry: destroy your opponent's weapon
  play(game, ooze)
  assert player.weapon is None
  assert wisp.parent == enemy.graveyard #the 1 damage swept the board

def test_deaths_bite_deathrattle_fires_when_it_is_replaced():
  game = naxx_game()
  player = game.current_player
  wisp = game.game_manager.get_card('Wisp', player.board)
  deaths_bite = game.game_manager.get_card("Death's Bite", player.hand)
  play(game, deaths_bite)
  play(game, game.game_manager.get_card('Fiery War Axe', player.hand))
  assert player.weapon.name == 'Fiery War Axe'
  assert deaths_bite.parent == player.graveyard
  assert wisp.parent == player.graveyard

def test_deaths_bite_is_not_doubled_by_baron_rivendare():
  #Baron doubles the deathrattles of your MINIONS - a weapon is not a minion
  game = naxx_game()
  player = game.current_player
  game.game_manager.get_card('Baron Rivendare', player.board)
  yeti = game.game_manager.get_card('Chillwind Yeti', player.other_player.board)
  play(game, game.game_manager.get_card("Death's Bite", player.hand))
  for _ in range(2):
    player.attacks_this_turn = 0
    game.perform_action(Action(Actions.ATTACK, player, [player.other_player]))
  assert yeti.get_health() == 4 #1 damage, not 2

def test_a_destroyed_weapon_is_not_a_minion_death():
  #FIXED: weapon destruction used to fire the minion-death trigger family
  game = naxx_game()
  player = game.current_player
  cult_master = game.game_manager.get_card('Cult Master', player.board) #draw when a friendly minion dies
  play(game, game.game_manager.get_card("Death's Bite", player.hand))
  axe = game.game_manager.get_card('Fiery War Axe', player.hand)
  assert len(player.hand) == 1
  play(game, axe) #destroys Death's Bite, whose deathrattle damages the board
  assert len(player.hand) == 0 #the weapon death drew Cult Master nothing
  assert cult_master.parent == player.board and cult_master.get_health() == 1
