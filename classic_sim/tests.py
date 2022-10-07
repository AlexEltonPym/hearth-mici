from card import Card
from zones import Deck
from player import Player
from game import Game
from enums import *
from card_sets import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
from numpy import empty
from action import Action
from tqdm import tqdm
from numpy.random import RandomState

from game_manager import GameManager

def test_classic_pool():
  basics = get_basic_cards()
  commons = get_common_cards()
  rares = get_rare_cards()
  epics = get_epic_cards()
  mage = get_mage_cards()
  hunter = get_hunter_cards()
  assert len(basics) == 43
  assert len(commons) == 40
  assert len(rares) == 36
  assert len(epics) == 11
  assert len(hunter) == 24
  assert len(mage) == 24

  print(f"{len(basics + commons + rares + epics + mage + hunter)}/202") #172
  assert True

def test_coin():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)
  game = game_manager.create_game()

  coin_card = None
  for card in game.current_player.other_player.hand:
    if card.name == 'The Coin':
      coin_card = card
      break

  cast_coin = Action(Actions.CAST_SPELL, coin_card, [game.current_player.other_player])
  assert game.current_player.other_player.current_mana == 0
  assert cast_coin.source in game.current_player.other_player.hand
  game.perform_action(cast_coin)
  assert cast_coin.source not in game.current_player.other_player.hand
  assert game.current_player.other_player.current_mana == 1

def test_abusive_sergeant():
  game = GameManager().create_test_game()
  new_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  assert new_wisp.attack == 1
  new_sergeant = game.game_manager.get_card('Abusive Sergeant', game.current_player.hand)
  buff_wisp = Action(Actions.CAST_MINION, new_sergeant, [new_wisp])
  game.perform_action(buff_wisp)
  assert new_wisp.temp_attack == 2
  game.end_turn()
  assert new_wisp.temp_attack == 0

def test_hunter_hero_power():
  game = GameManager().create_test_game()

  assert game.current_player.hero_power.name == get_hero_power(Classes.HUNTER).name
  assert game.current_player.other_player.get_health() == 30
  use_hero_power = Action(Actions.CAST_HERO_POWER, game.current_player.hero_power, [game.current_player.other_player])
  game.perform_action(use_hero_power)
  assert game.current_player.other_player.get_health() == 28

def test_elven_archer():
  game = GameManager().create_test_game()
  elven_archer = game.game_manager.get_card('Elven Archer', game.current_player.hand)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  cast_elven_archer_actions = list(filter(lambda action: action.source==elven_archer, game.get_available_actions(game.current_player)))
  assert len(cast_elven_archer_actions) == 4 #self and enemy, both wisps
  kill_enemy_wisp = list(filter(lambda action: action.source==elven_archer and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(kill_enemy_wisp)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert friendly_wisp.get_health() == 1
  assert game.player.get_health() == 30
  assert game.enemy.get_health() == 30

def test_grimscale_oracle():
  game = GameManager().create_test_game()
  murloc_tidecaller = game.game_manager.get_card('Murloc Tidecaller', game.current_player.board)
  assert murloc_tidecaller.get_attack() == 1
  grimscale_oracle = game.game_manager.get_card('Grimscale Oracle', game.current_player.hand)
  play_oracle = list(filter(lambda action: action.source == grimscale_oracle, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_oracle)
  assert murloc_tidecaller.get_attack() == 3
  assert grimscale_oracle.get_attack() == 1
  murloc_raider = game.game_manager.get_card("Murloc Raider", game.current_player.board)
  assert murloc_tidecaller.get_attack() == 3 #setting new card to .board does not trigger minion casts
  assert murloc_raider.get_attack() == 3

def test_stonetusk_boar():
  game = GameManager().create_test_game()
  stonetusk_boar = game.game_manager.get_card('Stonetusk Boar', game.current_player.board)
  assert stonetusk_boar.has_attribute(Attributes.CHARGE)
  attack_with_boar = list(filter(lambda action: action.source == stonetusk_boar, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_boar)
  assert game.current_player.other_player.get_health() == 29
  voodoo_doctor = game.game_manager.get_card('Voodoo Doctor', game.current_player.hand)
  heal_enemy = list(filter(lambda action: action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(heal_enemy)
  assert voodoo_doctor.parent == voodoo_doctor.owner.board
  assert game.current_player.other_player.get_health() == 30

def test_acidic_swamp_ooze():
  game = GameManager().create_test_game()
  acidic_swamp_ooze = game.game_manager.get_card('Acidic Swamp Ooze', game.current_player.hand)
  generic_weapon = game.game_manager.get_card('Generic Weapon', game.current_player.other_player)
  assert game.current_player.other_player.weapon
  play_ooze = list(filter(lambda action: action.source == acidic_swamp_ooze, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_ooze)
  assert not game.current_player.other_player.weapon
  assert generic_weapon.parent == generic_weapon.owner.graveyard

def test_kobold_geomancer():
  game = GameManager().create_test_game()
  kobold_geomancer = game.game_manager.get_card('Kobold Geomancer', game.current_player.board)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast_fireball = list(filter(lambda action: action.source == fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball)
  assert game.current_player.other_player.get_health() == 23

def test_murloc_tidehunter():
  game = GameManager().create_test_game()
  murloc_tidehunter = game.game_manager.get_card('Murloc Tidehunter', game.current_player.hand)
  play_tidehunter = list(filter(lambda action: action.source == murloc_tidehunter, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_tidehunter)
  assert murloc_tidehunter.parent == murloc_tidehunter.owner.board
  assert len(game.current_player.board) == 2

def test_novice_engineer():
  game = GameManager().create_test_game()
  engineer = game.game_manager.get_card('Novice Engineer', game.current_player.hand)
  assert len(game.current_player.hand) == 1
  play_engineer = list(filter(lambda action: action.source == engineer, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_engineer)
  assert len(game.current_player.hand) == 1

def test_raid_leader():
  game = GameManager().create_test_game()
  raid_leader = game.game_manager.get_card('Raid Leader', game.current_player.board)
  ironfur_grizzly = game.game_manager.get_card('Ironfur Grizzly', game.current_player.board)
  assert raid_leader.get_attack() == 2
  assert ironfur_grizzly.get_attack() == 4

def test_shattered_sun_cleric():
  game = GameManager().create_test_game()
  dalaran_mage = game.game_manager.get_card('Dalaran Mage', game.current_player.board)
  assert game.current_player.get_spell_damage() == 1
  assert dalaran_mage.get_attack() == 1
  assert dalaran_mage.get_health() == 4
  assert dalaran_mage.get_max_health() == 4
  shattered_sun_cleric = game.game_manager.get_card('Shattered Sun Cleric', game.current_player.hand)
  buff_mage = list(filter(lambda action: action.source == shattered_sun_cleric, game.get_available_actions(game.current_player)))[0]
  game.perform_action(buff_mage)
  assert dalaran_mage.get_attack() == 2
  assert dalaran_mage.get_health() == 5
  assert dalaran_mage.get_max_health() == 5

def test_darkscale_healer():
  game = GameManager().create_test_game()
  darkscale_healer = game.game_manager.get_card('Darkscale Healer', game.current_player.hand)
  dalaran_mage = game.game_manager.get_card('Dalaran Mage', game.current_player.board)
  assert dalaran_mage.get_attack() == 1
  assert dalaran_mage.get_health() == 4
  assert dalaran_mage.get_max_health() == 4
  game.deal_damage(dalaran_mage, 1)
  game.deal_damage(game.current_player, 10)
  assert dalaran_mage.get_health() == 3
  assert dalaran_mage.get_max_health() == 4
  assert game.current_player.get_health() == 20
  play_healer = list(filter(lambda action: action.source == darkscale_healer, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_healer)
  assert dalaran_mage.get_health() == 4
  assert dalaran_mage.get_max_health() == 4
  assert game.current_player.get_health() == 22


def test_argent_squire():
  game = GameManager().create_test_game()
  new_squire = game.game_manager.get_card('Argent Squire', game.current_player.other_player.board)

  assert Attributes.DIVINE_SHIELD in new_squire.attributes
  
  new_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  assert new_wisp.attack == 1

  attack_squire = Action(Actions.ATTACK, new_wisp, [new_squire])
  game.perform_action(attack_squire)
  assert Attributes.DIVINE_SHIELD not in new_squire.attributes
  assert new_wisp.parent == game.current_player.graveyard
  
  another_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  attack_squire = Action(Actions.ATTACK, another_wisp, [new_squire])
  game.perform_action(attack_squire)
  assert new_squire.parent == game.current_player.other_player.graveyard

def test_leper_gnome():
  game = GameManager().create_test_game()

  new_leper = game.game_manager.get_card('Leper Gnome', game.current_player.board)

  new_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  attack_leper = Action(Actions.ATTACK, new_leper, [new_wisp])
  game.perform_action(attack_leper)
  assert new_leper.parent == new_leper.owner.graveyard
  assert new_wisp.parent == new_wisp.owner.graveyard
  assert game.current_player.other_player.get_health() == 28
  
def test_shieldbearer():
  game = GameManager().create_test_game()

  new_shieldbearer = game.game_manager.get_card('Shieldbearer', game.current_player.board)

  new_shieldbearer.attacks_this_turn = 0
  available_actions=game.get_available_actions(game.current_player)
  for action in available_actions:
    assert action.action_type != Actions.ATTACK

def test_southsea_deckhand():
  game = GameManager().create_test_game()

  new_deckhand = game.game_manager.get_card('Southsea Deckhand', game.current_player.board)

  assert new_deckhand.attacks_this_turn == -1
  assert not new_deckhand.condition.requirement(game, new_deckhand)
  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))) == 0

  new_weapon = game.game_manager.get_card('Generic Weapon', game.current_player)
  assert game.current_player.weapon and game.current_player.weapon == new_weapon
  assert new_deckhand.attacks_this_turn == -1
  assert new_deckhand.condition.requirement(game, new_deckhand)
  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))) == 2 #attack with charge, attack with weapon

def test_silver_hand_knight():
  game = GameManager().create_test_game()
  silver_hand_knight = game.game_manager.get_card('Silver Hand Knight', game.current_player.hand)
  assert silver_hand_knight.parent == silver_hand_knight.owner.hand
  

def test_battlecry_weapon():
  game = GameManager().create_test_game()

  new_weapon = game.game_manager.get_card('Battlecry Weapon', game.current_player.hand)

  cast_weap = list(filter(lambda action: action.action_type == Actions.CAST_WEAPON and action.source==new_weapon, game.get_available_actions(game.current_player)))[0]

  game.perform_action(cast_weap)
  assert game.current_player.weapon == new_weapon
  assert game.current_player.health == 29
  assert game.current_player.other_player.health == 29

  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  hero_attack_options = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(hero_attack_options) == 2
  game.perform_action(hero_attack_options[0])
  assert game.current_player.other_player.health == 26
  assert game.current_player.health == 29
  assert game.current_player.weapon.health == 1
  assert game.current_player.attacks_this_turn == 1
  
  game.current_player.attacks_this_turn = 0
  game.perform_action(hero_attack_options[1])
  assert wisp.parent == wisp.owner.graveyard
  assert game.current_player.health == 28
  assert game.current_player.weapon == None
  assert new_weapon.parent == new_weapon.owner.graveyard
  assert game.current_player.attacks_this_turn == 1

def test_taunt():
  game = GameManager().create_test_game()

  new_shieldbearer = game.game_manager.get_card('Shieldbearer', game.current_player.other_player.board)
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  wisp.attacks_this_turn == 0
  available_actions=game.get_available_actions(game.current_player)
  for action in available_actions:
    assert not (action.action_type == Actions.ATTACK and action.targets[0] == game.current_player.other_player)

def test_stealth():
  game = GameManager().create_test_game()

  new_worgen = game.game_manager.get_card('Worgen Infiltrator', game.current_player.board)
  assert Attributes.STEALTH in new_worgen.attributes

  new_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  new_wisp.attacks_this_turn = 0

  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player.other_player)))) == 1

  new_worgen.attacks_this_turn = 0
  attack_action = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_action)
  assert not Attributes.STEALTH in new_worgen.attributes

  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player.other_player)))) == 2

def test_windfury():
  game = GameManager().create_test_game()

  new_dragonhawk = game.game_manager.get_card('Young Dragonhawk', game.current_player.board)

  assert Attributes.WINDFURY in new_dragonhawk.attributes
  new_dragonhawk.attacks_this_turn = 0

  attack_action = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_action)
  assert new_dragonhawk.attacks_this_turn == 1

  attack_action = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_action)
  assert new_dragonhawk.attacks_this_turn == 2
  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))) == 0

  assert game.current_player.other_player.health == 28

def test_enrage():
  game = GameManager().create_test_game()
  new_berserker = game.game_manager.get_card('Amani Berserker', game.current_player.board)

  assert not new_berserker.condition.requirement(game, new_berserker)
  new_berserker.attacks_this_turn = 0
  new_berserker.health = 2
  assert new_berserker.condition.requirement(game, new_berserker)
  attack_action = Action(action_type=Actions.ATTACK, source=new_berserker, targets=[game.current_player.other_player])
  game.perform_action(attack_action)
  assert game.current_player.other_player.health == 25

def test_bloodsail():
  game = GameManager().create_test_game()

  new_bloodsail = game.game_manager.get_card('Bloodsail Raider', game.current_player.hand)
  new_weapon = game.game_manager.get_card('Generic Weapon', game.current_player.hand)

  cast_weap = list(filter(lambda action: action.action_type == Actions.CAST_WEAPON and action.source == new_weapon, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_weap)
  assert game.current_player.weapon == new_weapon
  cast_bloodsail = list(filter(lambda action: action.source == new_bloodsail, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_bloodsail)
  assert new_bloodsail.parent == new_bloodsail.owner.board
  assert new_bloodsail.get_attack() == 5

def test_frostwolf_warlord():
  game = GameManager().create_test_game()

  frostwolf_warlord = game.game_manager.get_card('Frostwolf Warlord', game.current_player.hand)
  wisp_1 = game.game_manager.get_card('Wisp', game.current_player.board)
  wisp_2 = game.game_manager.get_card('Wisp', game.current_player.board)
  wisp_3 = game.game_manager.get_card('Wisp', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  play_frostwolf = list(filter(lambda action: action.source == frostwolf_warlord, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_frostwolf)
  assert frostwolf_warlord.get_attack() == 7
  assert frostwolf_warlord.get_health() == 7
  assert frostwolf_warlord.get_max_health() == 7

def test_gurubashi_berserker():
  game = GameManager().create_test_game()
  gurubashi_berserker = game.game_manager.get_card('Gurubashi Berserker', game.current_player.board)
  assert gurubashi_berserker.get_attack() == 2
  assert gurubashi_berserker.get_health() == 7
  assert gurubashi_berserker.get_max_health() == 7
  game.deal_damage(gurubashi_berserker, 1)
  assert gurubashi_berserker.get_attack() == 5
  assert gurubashi_berserker.get_health() == 6
  assert gurubashi_berserker.get_max_health() == 7
  game.deal_damage(game.current_player, 1)
  assert gurubashi_berserker.get_attack() == 5
  assert gurubashi_berserker.get_health() == 6
  assert gurubashi_berserker.get_max_health() == 7
  game.deal_damage(gurubashi_berserker, 2)
  assert gurubashi_berserker.get_attack() == 8
  assert gurubashi_berserker.get_health() == 4
  assert gurubashi_berserker.get_max_health() == 7

def test_nightblade():
  game = GameManager().create_test_game()

  nightblade = game.game_manager.get_card('Nightblade',game.current_player.hand)
  assert game.current_player.other_player.get_health() == 30
  play_nightblade = list(filter(lambda action: action.source == nightblade, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_nightblade)
  assert game.current_player.other_player.get_health() == 27

def test_stormpike_commando():
  game = GameManager().create_test_game()
  stormpike_commando = game.game_manager.get_card('Stormpike Commando',game.current_player.hand)
  friendly_wisp = game.game_manager.get_card('Wisp',game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp',game.current_player.other_player.board)
  cast_commando_actions = list(filter(lambda action: action.source == stormpike_commando, game.get_available_actions(game.current_player)))
  assert len(cast_commando_actions) == 4

def test_stormwind_champion():
  game = GameManager().create_test_game()
  stormwind_champion = game.game_manager.get_card('Stormwind Champion',game.current_player.board)
  friendly_wisp = game.game_manager.get_card('Wisp',game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp',game.current_player.other_player.board)

  assert stormwind_champion.get_attack() == 6
  assert stormwind_champion.get_health() == 6
  assert stormwind_champion.get_max_health() == 6
  assert friendly_wisp.get_attack() == 2
  assert friendly_wisp.get_health() == 2
  assert friendly_wisp.get_max_health() == 2 
  assert enemy_wisp.get_attack() == 1
  assert enemy_wisp.get_health() == 1
  assert enemy_wisp.get_max_health() == 1

def test_direwolf():
  game = GameManager().create_test_game()

  new_wolf = game.game_manager.get_card('Dire Wolf Alpha',game.current_player.board)
  first_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  second_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  third_wisp = game.game_manager.get_card('Wisp', game.current_player.board)

  assert first_wisp.get_attack() == 2
  assert second_wisp.get_attack() == 1
  assert third_wisp.get_attack() == 2
  assert new_wolf.get_attack() == 2

  first_wisp.change_parent(first_wisp.owner.graveyard)
  assert first_wisp.get_attack() == 1
  assert second_wisp.get_attack() == 2
  assert third_wisp.get_attack() == 2

  new_wolf.change_parent(new_wolf.owner.graveyard)
  assert second_wisp.get_attack() == 1
  assert third_wisp.get_attack() == 1

def test_loot_hoarder():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)
  game = game_manager.create_game()

  new_hoarder = game.game_manager.get_card('Loot Hoarder', game.current_player.board)
  assert len(game.current_player.hand) == 3

  fireblast_action = Action(action_type=Actions.CAST_HERO_POWER, source=game.enemy.hero_power, targets=[new_hoarder])
  game.perform_action(fireblast_action)
  assert new_hoarder.parent == new_hoarder.owner.graveyard
  assert len(game.current_player.hand) == 4

def test_hexproof():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)
  game = game_manager.create_game()
  game.player.hand.clear()
  game.enemy.hand.clear()
  game.enemy.current_mana = 10

  new_faerie = game.game_manager.get_card('Faerie Dragon', game.player.board)
  new_fireball = game.game_manager.get_card('Fireball', game.enemy.hand)

  available_actions = game.get_available_actions(game.enemy)
  available_actions = list(filter(lambda action: (action.action_type==Actions.CAST_SPELL or action.action_type==Actions.CAST_HERO_POWER) and action.targets[0] == new_faerie, available_actions))
  assert len(available_actions) == 0


def test_mad_bomber():
  game = GameManager().create_test_game()

  new_bomber = game.game_manager.get_card('Mad Bomber', game.current_player.hand)
  new_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  cast_bomber = game.get_available_actions(game.current_player)[0]
  game.perform_action(cast_bomber)

  wisp_damage = new_wisp.get_max_health() - new_wisp.get_health()
  player_damage = game.current_player.get_max_health()-game.current_player.get_health()
  enemy_damage = game.current_player.other_player.get_max_health()-game.current_player.other_player.get_health()
  assert wisp_damage + player_damage + enemy_damage == 3

def test_acolyte_of_pain():
  game = GameManager().create_test_game()
  acolyte_of_pain = game.game_manager.get_card('Acolyte of Pain', game.current_player.board)
  assert len(game.current_player.hand) == 0
  game.deal_damage(acolyte_of_pain, 1)
  assert len(game.current_player.hand) == 1
  game.deal_damage(acolyte_of_pain, 1)
  assert len(game.current_player.hand) == 2
  game.deal_damage(acolyte_of_pain, 1)
  assert len(game.current_player.hand) == 3
  assert acolyte_of_pain.parent == acolyte_of_pain.owner.graveyard

def test_farseer():
  game = GameManager().create_test_game()

  new_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  assert new_wisp.get_health() == 1
  assert new_wisp.get_max_health() == 1
  assert game.current_player.health == 30
  assert game.current_player.max_health == 30
  assert game.current_player.get_max_health() == 30

  defender = game.game_manager.get_card('Defender of Argus', game.current_player.hand)
  cast_defender = list(filter(lambda action: action.source == defender, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_defender)

  assert new_wisp.get_attack() == 2
  assert new_wisp.get_health() == 2 
  assert new_wisp.has_attribute(Attributes.TAUNT)

  new_farseer = game.game_manager.get_card('Earthen Ring Farseer', game.current_player.hand)

  cast_actions = list(filter(lambda action: action.action_type == Actions.CAST_MINION, game.get_available_actions(game.current_player)))
  assert len(cast_actions) == 4 #heal wisp, defender, self and enemy
  game.perform_action(cast_actions[0])
  assert new_wisp.get_health() == 2
  assert new_wisp.get_max_health() == 2

  game.deal_damage(new_wisp, 1)
  assert new_wisp.parent == new_wisp.owner.board
  assert new_wisp.get_health() == 1
  assert new_wisp.get_max_health() == 2
  
  second_farseer = game.game_manager.get_card('Earthen Ring Farseer', game.current_player.hand)

  heal_wisp = list(filter(lambda action: action.source == second_farseer and action.targets[0] == new_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(heal_wisp)
  assert new_wisp.get_health() == 2
  assert new_wisp.get_max_health() == 2

def test_ghoul():
  game = GameManager().create_test_game()

  new_ghoul = game.game_manager.get_card('Flesheating Ghoul', game.current_player.board)
  new_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  assert new_ghoul.get_attack() == 2
  game.deal_damage(new_wisp, 1)
  assert new_ghoul.get_attack() == 3
  game.deal_damage(enemy_wisp, 1)
  assert new_ghoul.get_attack() == 4
  assert new_ghoul.get_health() == 3
  game.deal_damage(new_ghoul, 3)
  assert new_ghoul.parent == new_ghoul.owner.graveyard
  assert new_ghoul.get_attack() == 4

def test_golem():
  game = GameManager().create_test_game()

  new_golem = game.game_manager.get_card('Harvest Golem', game.current_player.board)

  game.deal_damage(new_golem, 3)
  assert new_golem.parent == new_golem.owner.graveyard
  assert len(game.current_player.board) == 1
  assert game.current_player.board.get_all()[0].name == 'Damaged Golem'

def test_ironbeak():
  game = GameManager().create_test_game()

  new_owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  new_hoarder = game.game_manager.get_card('Loot Hoarder', game.current_player.board)
  new_direwolf = game.game_manager.get_card('Dire Wolf Alpha', game.current_player.board)

  assert new_hoarder.get_attack() == 3
  assert new_direwolf.get_attack() == 2

  silence_hoarder = list(filter(lambda action: action.targets[0] == new_hoarder, game.get_available_actions(game.current_player)))[0]
  game.perform_action(silence_hoarder)

  assert new_hoarder.get_attack() == 3
  assert new_direwolf.get_attack() == 2
  assert new_hoarder.effect == None

  game.deal_damage(new_hoarder, 1)
  assert len(game.current_player.hand) == 0

def test_worgen():
  game = GameManager().create_test_game()

  worgen = game.game_manager.get_card('Raging Worgen', game.current_player.board)

  assert not worgen.has_attribute(Attributes.WINDFURY)
  assert worgen.get_attack() == 3
  game.deal_damage(worgen, 1)
  assert worgen.get_max_health() == 3
  assert worgen.get_health() == 2
  assert worgen.get_attack() == 4
  assert worgen.has_attribute(Attributes.WINDFURY)
  assert worgen.attacks_this_turn == -1
  worgen.attacks_this_turn = 0
  attack_actions = list(filter(lambda action: action.source == worgen, game.get_available_actions(game.current_player)))
  game.perform_action(attack_actions[0])
  assert worgen.attacks_this_turn == 1
  attack_actions = list(filter(lambda action: action.source == worgen, game.get_available_actions(game.current_player)))
  game.perform_action(attack_actions[0])
  assert worgen.attacks_this_turn == 2
  assert game.current_player.other_player.get_health() == 22
  attack_actions = list(filter(lambda action: action.source == worgen, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 0

def test_scarlet():
  game = GameManager().create_test_game()

  scarlet = game.game_manager.get_card('Scarlet Crusader', game.current_player.board)
  assert scarlet.has_attribute(Attributes.DIVINE_SHIELD)
  assert scarlet.get_health() == 1
  assert scarlet.get_max_health() == 1
  game.deal_damage(scarlet, 10)
  assert not scarlet.has_attribute(Attributes.DIVINE_SHIELD)
  assert scarlet.get_health() == 1
  assert scarlet.get_max_health() == 1
  game.deal_damage(scarlet, 10)
  assert scarlet.parent == scarlet.owner.graveyard
  assert scarlet.get_health() == -9

def test_tauren_warrior():
  game = GameManager().create_test_game()

  tauren_warrior = game.game_manager.get_card('Tauren Warrior', game.current_player.other_player.board)
  assert tauren_warrior.has_attribute(Attributes.TAUNT)
  assert tauren_warrior.get_attack() == 2
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  wisp.attacks_this_turn = 0

  attack_actions = list(filter(lambda action: action.source == wisp, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 1
  game.perform_action(attack_actions[0])

  assert wisp.parent == wisp.owner.graveyard
  assert tauren_warrior.get_attack() == 5

def test_cult_master():
  game = GameManager().create_test_game()

  cult_master = game.game_manager.get_card('Cult Master', game.current_player.board)
  assert len(game.current_player.hand) == 0
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  game.deal_damage(wisp, 1)
  assert len(game.current_player.hand) == 1

def test_dark_iron_dwarf():
  game = GameManager().create_test_game()

  dark_iron_dwarf = game.game_manager.get_card('Dark Iron Dwarf', game.current_player.hand)
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  cast_dwarf_actions = list(filter(lambda action: action.source == dark_iron_dwarf, game.get_available_actions(game.current_player)))
  assert len(cast_dwarf_actions) == 2
  game.perform_action(cast_dwarf_actions[0])
  assert wisp.get_attack() == 3

def test_dread_corsair():
  game = GameManager().create_test_game()

  dread_corsair = game.game_manager.get_card('Dread Corsair', game.current_player.hand)
  assert dread_corsair.get_manacost() == 4

  new_weapon = game.game_manager.get_card('Generic Weapon', game.current_player)
  assert game.current_player.weapon and game.current_player.weapon.get_attack() == 3
  assert dread_corsair.get_manacost() == 1

def test_venture():
  game = GameManager().create_test_game()

  wisp = game.game_manager.get_card('Wisp', game.current_player.hand)
  assert wisp.get_manacost() == 0

  venture_co_mercenary = game.game_manager.get_card('Venture Co. Mercenary', game.current_player.board)
  assert wisp.get_manacost() == 3

def test_spiteful_smith():
  game = GameManager().create_test_game()

  spiteful_smith = game.game_manager.get_card('Spiteful Smith', game.current_player.board)
  assert spiteful_smith.get_attack() == 4

  generic_weapon = game.game_manager.get_card('Generic Weapon', game.current_player)
  assert generic_weapon.get_attack() == 3

  game.deal_damage(spiteful_smith, 1)
  assert generic_weapon.get_attack() == 5

  game.deal_damage(spiteful_smith, 6)
  assert generic_weapon.get_attack() == 3

def test_angry_chicken():
  game = GameManager().create_test_game()
  chicken = game.game_manager.get_card('Angry Chicken', game.current_player.board)
  defender = game.game_manager.get_card('Defender of Argus', game.current_player.hand)
  assert chicken.get_max_health() == 1
  assert chicken.get_health() == 1
  assert chicken.get_attack() == 1
  cast_defender = list(filter(lambda action: action.source == defender, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_defender)
  assert defender.get_attack() == 2
  assert defender.get_health() == 3
  assert chicken.get_max_health() == 2
  assert chicken.get_health() == 2
  assert chicken.get_attack() == 2
  game.deal_damage(chicken, 1)
  assert chicken.get_max_health() == 2
  assert chicken.get_health() == 1
  assert chicken.get_attack() == 7


def test_bloodsail_corsair():
  game = GameManager().create_test_game()
  bloodsail_corsair = game.game_manager.get_card('Bloodsail Corsair', game.current_player.hand)
  generic_weapon = game.game_manager.get_card('Generic Weapon', game.current_player.other_player)
  assert game.current_player.other_player.weapon
  assert game.current_player.other_player.weapon.get_health() == 2
  play_corsair = list(filter(lambda action: action.source == bloodsail_corsair, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_corsair)
  assert game.current_player.other_player.weapon.get_health() == 1
  assert game.current_player.other_player.weapon.get_max_health() == 2
  game.deal_damage(generic_weapon, 1)
  assert not game.current_player.other_player.weapon

def test_frost_elemental():
  game = GameManager().create_test_game()
  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  frost_elemental = game.game_manager.get_card('Frost Elemental', game.current_player.hand)
  cast_frost_elemental = list(filter(lambda action: action.source == frost_elemental and action.targets[0] == wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_frost_elemental)
  assert wisp.has_attribute(Attributes.FROZEN)
  game.end_turn()
  game.untap()
  assert wisp.has_attribute(Attributes.FROZEN)
  assert wisp.attacks_this_turn == 0
  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))) == 0
  game.end_turn()
  assert not wisp.has_attribute(Attributes.FROZEN)

def test_priestess_of_elune():
  game = GameManager().create_test_game()
  priestess_of_elune = game.game_manager.get_card('Priestess of Elune', game.current_player.hand)
  game.deal_damage(game.current_player, 3)
  assert game.current_player.get_health() == 27
  cast_priestess = list(filter(lambda action: action.source == priestess_of_elune, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_priestess)
  assert game.current_player.get_health() == 30

def test_lightwarden():
  game = GameManager().create_test_game()
  lightwarden = game.game_manager.get_card('Lightwarden', game.current_player.board)
  assert lightwarden.get_attack() == 1
  game.deal_damage(game.current_player, 1)
  assert game.current_player.get_health() == 29

  priestess_of_elune = game.game_manager.get_card('Priestess of Elune', game.current_player.hand)
  cast_priestess = list(filter(lambda action: action.source == priestess_of_elune, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_priestess)
  assert game.current_player.get_health() == 30
  assert lightwarden.get_attack() == 3

  game.deal_damage(game.current_player, 1)
  priestess_of_elune = game.game_manager.get_card('Priestess of Elune', game.current_player.hand)
  game.current_player.current_mana = 10
  cast_priestess = list(filter(lambda action: action.source == priestess_of_elune, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_priestess)
  assert lightwarden.get_attack() == 5


def test_murloc_tidecaller():
  game = GameManager().create_test_game()
  tidecaller = game.game_manager.get_card('Murloc Tidecaller', game.current_player.board)
  triggering_tidecaller = game.game_manager.get_card('Murloc Tidecaller', game.current_player.hand)
  assert tidecaller.get_attack() == 1
  play_tide = list(filter(lambda action: action.source == triggering_tidecaller, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_tide)
  assert tidecaller.get_attack() == 2
  assert triggering_tidecaller.get_attack() == 1
  third_murloc = game.game_manager.get_card('Murloc Tidecaller', game.current_player.hand)
  play_tide = list(filter(lambda action: action.source == third_murloc, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_tide)
  assert tidecaller.get_attack() == 3
  assert triggering_tidecaller.get_attack() == 2
  assert third_murloc.get_attack() == 1

def test_secretkeeper():
  game = GameManager().create_test_game()
  secretkeeper = game.game_manager.get_card('Secretkeeper', game.current_player.board)
  assert secretkeeper.get_attack() == 1
  assert secretkeeper.get_health() == 2
  assert secretkeeper.get_max_health() == 2
  snipe = game.game_manager.get_card('Snipe', game.current_player.hand)
  assert snipe.card_type == CardTypes.SECRET
  secret_actions = list(filter(lambda action: action.action_type == Actions.CAST_SECRET, game.get_available_actions(game.current_player)))
  assert len(secret_actions) == 1
  game.perform_action(secret_actions[0])
  assert len(game.current_player.secrets_zone) == 1
  assert secretkeeper.get_attack() == 2
  assert secretkeeper.get_health() == 3
  assert secretkeeper.get_max_health() == 3
  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.hand)
  play_wisp = list(filter(lambda action: action.source == wisp, game.get_available_actions(game.current_player.other_player)))[0]
  game.perform_action(play_wisp)
  assert wisp.get_health() == -3
  assert wisp.parent == wisp.owner.graveyard
  assert snipe.parent == snipe.owner.graveyard
  assert len(game.current_player.secrets_zone) == 0
  assert secretkeeper.get_attack() == 2
  assert secretkeeper.get_health() == 3
  assert secretkeeper.get_max_health() == 3


def test_young_priestess():
  game = GameManager().create_test_game()
  young_priestess = game.game_manager.get_card("Young Priestess", game.current_player.board)
  assert young_priestess.get_attack() == 2
  assert young_priestess.get_health() == 1
  assert young_priestess.get_max_health() == 1
  game.end_turn()
  assert young_priestess.get_attack() == 2
  assert young_priestess.get_health() == 1
  assert young_priestess.get_max_health() == 1
  game.untap()
  game.end_turn()
  assert young_priestess.get_attack() == 2
  assert young_priestess.get_health() == 1
  assert young_priestess.get_max_health() == 1
  game.untap()
  wisp = game.game_manager.get_card("Wisp", game.current_player.board)
  assert wisp.get_attack() == 1
  assert wisp.get_health() == 1
  assert wisp.get_max_health() == 1
  game.end_turn()
  assert wisp.get_attack() == 1
  assert wisp.get_health() == 2
  assert wisp.get_max_health() == 2
  assert young_priestess.get_attack() == 2
  assert young_priestess.get_health() == 1
  assert young_priestess.get_max_health() == 1
  game.untap()
  game.end_turn()
  game.untap()
  game.end_turn()
  assert wisp.get_attack() == 1
  assert wisp.get_health() == 3
  assert wisp.get_max_health() == 3
  assert young_priestess.get_attack() == 2
  assert young_priestess.get_health() == 1
  assert young_priestess.get_max_health() == 1

def test_ancient_watcher():
  game = GameManager().create_test_game()
  ancient_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.board)
  assert ancient_watcher.attacks_this_turn == -1
  assert ancient_watcher.has_attribute(Attributes.DEFENDER)
  ancient_watcher.attacks_this_turn = 0
  attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 0
  new_owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  play_owl = list(filter(lambda action: action.source == new_owl, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_owl)
  assert not ancient_watcher.has_attribute(Attributes.DEFENDER)
  attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 1

  
def test_crazed_alchemist():
  game = GameManager().create_test_game()
  crazed_alchemist = game.game_manager.get_card("Crazed Alchemist", game.current_player.hand)
  ancient_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.board)
  assert ancient_watcher.has_attribute(Attributes.DEFENDER)
  assert ancient_watcher.get_attack() == 4
  assert ancient_watcher.get_health() == 5
  assert ancient_watcher.get_max_health() == 5
  game.deal_damage(ancient_watcher, 3)
  assert ancient_watcher.get_health() == 2
  assert ancient_watcher.get_max_health() == 5
  play_alch = list(filter(lambda action: action.source == crazed_alchemist, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_alch)
  assert ancient_watcher.get_attack() == 2
  assert ancient_watcher.get_health() == 4
  assert ancient_watcher.get_max_health() == 4
  new_owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  play_owl = list(filter(lambda action: action.source == new_owl and action.targets[0] == ancient_watcher, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_owl)
  assert not ancient_watcher.has_attribute(Attributes.DEFENDER)
  assert ancient_watcher.get_attack() == 2
  assert ancient_watcher.get_health() == 4
  assert ancient_watcher.get_max_health() == 4

def test_knife_juggler():
  game = GameManager().create_test_game()
  knife_juggler = game.game_manager.get_card("Knife Juggler", game.current_player.board)
  wisp = game.game_manager.get_card("Wisp", game.current_player.hand)
  play_wisp = list(filter(lambda action: action.source==wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_wisp)
  assert game.current_player.other_player.get_health() == 29

def test_mana_addict():
  game = GameManager().create_test_game()
  mana_addict = game.game_manager.get_card("Mana Addict", game.current_player.board)
  fireball = game.game_manager.get_card("Fireball", game.current_player.hand)
  play_fireball = list(filter(lambda action: action.source==fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  assert mana_addict.get_attack() == 1
  game.perform_action(play_fireball)
  assert mana_addict.get_attack() == 3
  game.end_turn()
  assert mana_addict.get_attack() == 1

def test_mana_wraith():
  game = GameManager().create_test_game()
  mana_wraith = game.game_manager.get_card("Mana Wraith", game.current_player.board)
  wisp = game.game_manager.get_card("Wisp", game.current_player.hand)
  assert wisp.get_manacost() == 1
  fireball = game.game_manager.get_card("Fireball", game.current_player.hand)
  assert fireball.get_manacost() == 4
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.hand)
  assert enemy_wisp.get_manacost() == 1

def test_master_swordsmith():
  game = GameManager().create_test_game()
  master_swordsmith = game.game_manager.get_card("Master Swordsmith", game.current_player.board)
  assert master_swordsmith.get_attack() == 1
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()

  assert master_swordsmith.get_attack() == 1
  wisp = game.game_manager.get_card("Wisp", game.current_player.board)
  game.end_turn()
  game.untap()
  assert wisp.get_attack() == 2
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert wisp.get_attack() == 3

def test_pint_sized_summoner():
  game = GameManager().create_test_game()
  pint_sized_summoner = game.game_manager.get_card("Pint-Sized Summoner", game.current_player.board)
  assert game.current_player.minions_played_this_turn == 0
  ancient_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.hand)
  assert ancient_watcher.get_manacost() == 1
  play_watcher = list(filter(lambda action: action.source == ancient_watcher, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_watcher)
  angry_chicken = game.game_manager.get_card("Angry Chicken", game.current_player.hand)
  assert angry_chicken.get_manacost() == 1
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert angry_chicken.get_manacost() == 0

def test_sunfury_protector():
  game = GameManager().create_test_game()
  sunfury_protector = game.game_manager.get_card("Sunfury Protector", game.current_player.hand)
  wisp1 = game.game_manager.get_card("Wisp", game.current_player.board)
  wisp2 = game.game_manager.get_card("Wisp", game.current_player.board)

  play_sunfury = list(filter(lambda action: action.source == sunfury_protector, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_sunfury)
  assert len(game.current_player.board) == 3
  assert wisp1.has_attribute(Attributes.TAUNT)
  assert wisp2.has_attribute(Attributes.TAUNT)
  assert not sunfury_protector.has_attribute(Attributes.TAUNT)

def test_wild_pyromancer():
  game = GameManager().create_test_game()
  wild_pyromancer = game.game_manager.get_card("Wild Pyromancer", game.current_player.board)
  ancient_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.board)
  fireball = game.game_manager.get_card("Fireball", game.current_player.hand)
  assert wild_pyromancer.get_health() == 2
  assert ancient_watcher.get_health() == 5
  cast_fireball = list(filter(lambda action: action.source == fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball)
  assert wild_pyromancer.get_health() == 1
  assert ancient_watcher.get_health() == 4
  second_fireball = game.game_manager.get_card("Fireball", game.current_player.hand)
  cast_fireball = list(filter(lambda action: action.source == second_fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball)
  assert wild_pyromancer.get_health() == 0
  assert ancient_watcher.get_health() == 3

def test_alarm_o_bot():
  game = GameManager().create_test_game()
  alarm_o_bot = game.game_manager.get_card("Alarm-o-Bot", game.current_player.board)
  ancient_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.hand)
  game.end_turn()
  game.untap()
  assert alarm_o_bot.parent == alarm_o_bot.owner.board
  assert ancient_watcher.parent == ancient_watcher.owner.hand
  game.end_turn()
  game.untap()
  assert alarm_o_bot.parent == alarm_o_bot.owner.hand
  assert len(game.current_player.board) == 1 #could draw a creature and have that be swapped
  
def test_arcane_golem():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing)
  game = game_manager.create_game()
  game.current_player.current_mana = 3
  assert game.current_player.other_player.max_mana == 0
  assert game.current_player.other_player.current_mana == 0
  arcane_golem = game.game_manager.get_card("Arcane Golem", game.current_player.hand)
  cast_golem = list(filter(lambda action: action.source == arcane_golem, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_golem)
  assert arcane_golem.has_attribute(Attributes.CHARGE)
  assert game.current_player.other_player.max_mana == 1
  assert game.current_player.other_player.current_mana == 1

def test_coldlight_oracle():
  game = GameManager().create_test_game()
  assert len(game.current_player.hand) == 0
  assert len(game.current_player.other_player.hand) == 0
  coldlight_oracle = game.game_manager.get_card("Coldlight Oracle", game.current_player.hand)
  play_oracle = list(filter(lambda action: action.source == coldlight_oracle, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_oracle)
  assert len(game.current_player.hand) == 2
  assert len(game.current_player.other_player.hand) == 2

def test_coldlight_seer():
  game = GameManager().create_test_game()
  coldlight_oracle = game.game_manager.get_card("Coldlight Oracle", game.current_player.board)
  coldlight_seer = game.game_manager.get_card("Coldlight Seer", game.current_player.hand)
  play_seer = list(filter(lambda action: action.source == coldlight_seer, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_seer)
  assert coldlight_oracle.get_health() == 4
  assert coldlight_oracle.get_max_health() == 4
  assert coldlight_seer.get_health() == 3

def test_demolisher():
  game = GameManager().create_test_game()
  ancient_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.other_player.board)
  demolisher = game.game_manager.get_card("Demolisher", game.current_player.board)
  assert ancient_watcher.get_health() == 5
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert ancient_watcher.get_health() == 3

def test_emperor_cobra():
  game = GameManager().create_test_game()
  emperor_cobra = game.game_manager.get_card("Emperor Cobra", game.current_player.board)
  enemy_cobra = game.game_manager.get_card("Emperor Cobra", game.current_player.other_player.board)
  emperor_cobra.attacks_this_turn = 0
  attack_enemy_cobra = list(filter(lambda action: action.source==emperor_cobra and action.targets[0]==enemy_cobra, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_enemy_cobra)
  assert emperor_cobra.get_health() == 1
  assert enemy_cobra.get_health() == 1
  assert emperor_cobra.parent == emperor_cobra.owner.graveyard
  assert enemy_cobra.parent == enemy_cobra.owner.graveyard

def test_imp_master():
  game = GameManager().create_test_game()
  imp_master = game.game_manager.get_card("Imp Master", game.current_player.board)
  assert len(game.current_player.board) == 1
  assert imp_master.get_health() == 5
  assert imp_master.get_max_health() == 5
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert len(game.current_player.board) == 2
  assert imp_master.get_health() == 4
  assert imp_master.get_max_health() == 5
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert len(game.current_player.board) == 3
  assert imp_master.get_health() == 3
  assert imp_master.get_max_health() == 5

def test_injured_blademaster():
  game = GameManager().create_test_game()
  blademaster = game.game_manager.get_card("Injured Blademaster", game.current_player.hand)
  play_blademaster = list(filter(lambda action: action.source==blademaster, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_blademaster)
  assert blademaster.get_health() == 3
  assert blademaster.get_max_health() == 7

def test_questing_adventurer():
  game = GameManager().create_test_game()
  questing_adventurer = game.game_manager.get_card("Questing Adventurer", game.current_player.board)
  wisp = game.game_manager.get_card('Wisp', game.current_player.hand)
  play_wisp = list(filter(lambda action: action.source == wisp, game.get_available_actions(game.current_player)))[0]
  assert questing_adventurer.get_attack() == 2
  assert questing_adventurer.get_health() == 2
  assert questing_adventurer.get_max_health() == 2
  game.perform_action(play_wisp)
  assert questing_adventurer.get_attack() == 3
  assert questing_adventurer.get_health() == 3
  assert questing_adventurer.get_max_health() == 3
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  play_fireball = list(filter(lambda action: action.source == fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_fireball)
  assert questing_adventurer.get_attack() == 4
  assert questing_adventurer.get_health() == 4
  assert questing_adventurer.get_max_health() == 4

def test_ancient_mage():
  game = GameManager().create_test_game()
  ancient_mage = game.game_manager.get_card("Ancient Mage", game.current_player.hand)
  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  second_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  third_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  play_mage = list(filter(lambda action: action.source == ancient_mage, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_mage)
  assert game.current_player.get_spell_damage() == 2

def test_twilight_drake():
  game = GameManager().create_test_game()
  twilight_drake = game.game_manager.get_card("Twilight Drake", game.current_player.hand)
  for i in range(5):
    game.game_manager.get_card("Wisp", game.current_player.hand)
  assert len(game.current_player.hand) == 6
  play_drake = list(filter(lambda action: action.source == twilight_drake, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_drake)
  assert twilight_drake.get_health() == 6
  assert twilight_drake.get_max_health() == 6

def test_violet_teacher():
  game = GameManager().create_test_game()
  violet_teacher = game.game_manager.get_card("Violet Teacher", game.current_player.board)
  assert len(game.current_player.board) == 1
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast_fireball = list(filter(lambda action: action.source == fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball)
  assert len(game.current_player.board) == 2
  
def test_abomination():
  game = GameManager().create_test_game()
  abomination = game.game_manager.get_card("Abomination", game.current_player.board)
  assert abomination.has_attribute(Attributes.TAUNT)
  assert abomination.get_health() == 4
  game.deal_damage(abomination, 4)
  assert game.current_player.get_health() == 28
  assert game.current_player.other_player.get_health() == 28

def test_azure_drake():
  game = GameManager().create_test_game()
  azure_drake = game.game_manager.get_card("Azure Drake", game.current_player.hand)  
  assert len(game.current_player.hand) == 1
  play_drake = list(filter(lambda action: action.source==azure_drake, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_drake)

  assert azure_drake.has_attribute(Attributes.SPELL_DAMAGE)
  assert azure_drake.creature_type == CreatureTypes.DRAGON
  assert game.current_player.get_spell_damage() == 1
  assert len(game.current_player.hand) == 1

def test_gadgetzan_auctioneer():
  game = GameManager().create_test_game()
  auctioneer = game.game_manager.get_card("Gadgetzan Auctioneer", game.current_player.board)  
  assert len(game.current_player.hand) == 0
  fireball1 = game.game_manager.get_card("Fireball", game.current_player.hand)  
  fireball2 = game.game_manager.get_card("Fireball", game.current_player.hand)  
  assert len(game.current_player.hand) == 2
  cast_fireball1 = list(filter(lambda action: action.source == fireball1 and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball1)
  assert len(game.current_player.hand) == 2
  cast_fireball2 = list(filter(lambda action: action.source == fireball2 and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball2)
  assert len(game.current_player.hand) == 2
  enemy_fireball = game.game_manager.get_card("Fireball", game.current_player.other_player.hand)  
  cast_enemy_fireball = list(filter(lambda action: action.source == enemy_fireball and action.targets[0] == game.current_player, game.get_available_actions(game.current_player.other_player)))[0]
  game.perform_action(cast_enemy_fireball)
  assert len(game.current_player.hand) == 2
  assert len(game.current_player.other_player.hand) == 0

def test_stampeding_kodo():
  game = GameManager().create_test_game()
  kodo = game.game_manager.get_card("Stampeding Kodo", game.current_player.hand)
  enemy_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.other_player.board)
  play_kodo = list(filter(lambda action: action.source == kodo, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_kodo)
  assert enemy_watcher.parent == enemy_watcher.owner.board
  second_kodo = game.game_manager.get_card("Stampeding Kodo", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  play_second_kodo = list(filter(lambda action: action.source == second_kodo, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_second_kodo)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard

def test_argent_commander():
  game = GameManager().create_test_game()
  commander = game.game_manager.get_card("Argent Commander", game.current_player.board)
  wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  assert commander.attacks_this_turn == -1
  assert commander.has_attribute(Attributes.DIVINE_SHIELD)
  assert commander.get_health() == 2
  assert commander.get_max_health() == 2
  attack_with_commander = list(filter(lambda action: action.source == commander and action.targets[0] == wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_commander)
  assert commander.attacks_this_turn == 1
  assert not commander.has_attribute(Attributes.DIVINE_SHIELD)
  assert commander.get_health() == 2
  assert commander.get_max_health() == 2

def test_ravenholdt_assassin():
  game = GameManager().create_test_game()
  ravenholdt_assassin = game.game_manager.get_card("Ravenholdt Assassin", game.current_player.other_player.board)
  assert ravenholdt_assassin.has_attribute(Attributes.STEALTH)
  commander = game.game_manager.get_card("Argent Commander", game.current_player.board)
  attack_with_commander_actions = list(filter(lambda action: action.source == commander, game.get_available_actions(game.current_player)))
  assert len(attack_with_commander_actions) == 1
  new_owl = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  silence_actions = list(filter(lambda action: action.source==new_owl, game.get_available_actions(game.current_player)))
  assert len(silence_actions) == 1 #silence your own commander
  game.perform_action(silence_actions[0])
  assert not commander.has_attribute(Attributes.DIVINE_SHIELD)
  assert not commander.has_attribute(Attributes.CHARGE)
  attack_with_commander_actions = list(filter(lambda action: action.source == commander, game.get_available_actions(game.current_player)))
  assert len(attack_with_commander_actions) == 0
  game.end_turn()
  game.untap()
  attack_with_assassin_actions = list(filter(lambda action: action.source == ravenholdt_assassin, game.get_available_actions(game.current_player)))
  assert len(attack_with_assassin_actions) == 3
  attack_commander = list(filter(lambda action: action.targets[0] == commander, attack_with_assassin_actions))[0]
  game.perform_action(attack_commander)
  assert not commander.has_attribute(Attributes.DIVINE_SHIELD)
  assert not ravenholdt_assassin.has_attribute(Attributes.STEALTH)
  assert ravenholdt_assassin.get_health() == 1
  game.end_turn()
  game.untap()
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  game.current_player.current_mana = 4
  cast_fireball_actions = list(filter(lambda action: action.source == fireball, game.get_available_actions(game.current_player)))
  assert len(cast_fireball_actions) == 4

#Epic cards
def test_hungry_crab_no_target():
  game = GameManager().create_test_game()
  hungry_crab = game.game_manager.get_card("Hungry Crab", game.current_player.hand)
  play_crab_no_valid_target = list(filter(lambda action: action.source == hungry_crab, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_crab_no_valid_target)
  assert hungry_crab.get_attack() == 1
  assert hungry_crab.get_health() == 2
  
def test_hungry_crab():
  game = GameManager().create_test_game()
  hungry_crab = game.game_manager.get_card("Hungry Crab", game.current_player.hand)
  murloc = game.game_manager.get_card("Murloc Tidecaller", game.current_player.other_player.board)
  play_crab = list(filter(lambda action: action.source == hungry_crab, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_crab)
  assert hungry_crab.get_attack() == 3
  assert hungry_crab.get_health() == 4
  assert murloc.parent == murloc.owner.graveyard

def test_captains_parrot():
  game = GameManager().create_test_game()
  captains_parrot = game.game_manager.get_card("Captain's Parrot", game.current_player.hand)
  southsea_deckhand = game.game_manager.get_card("Southsea Deckhand", game.current_player.hand)
  southsea_deckhand.change_parent(southsea_deckhand.owner.deck) #when initally setting to deck, has different owners for some reason?

  play_parrot = list(filter(lambda action: action.source == captains_parrot, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_parrot)

  assert len(game.current_player.board) == 1
  assert captains_parrot.parent == captains_parrot.owner.board
  assert len(game.current_player.hand) == 1
  assert game.current_player.hand.get_all()[0].creature_type == CreatureTypes.PIRATE

def test_doomsayer():
  game = GameManager().create_test_game()
  doomsayer = game.game_manager.get_card("Doomsayer", game.current_player.board)
  southsea_deckhand = game.game_manager.get_card("Southsea Deckhand", game.current_player.board)
  wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  game.end_turn()
  assert doomsayer.parent == doomsayer.owner.graveyard
  assert southsea_deckhand.parent == southsea_deckhand.owner.graveyard
  assert wisp.parent == wisp.owner.graveyard

def test_game_hunter():
  game = GameManager().create_test_game()
  venture_co_mercenary = game.game_manager.get_card("Venture Co. Mercenary", game.current_player.other_player.board)
  wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  big_game_hunter = game.game_manager.get_card("Big Game Hunter", game.current_player.hand)
  assert big_game_hunter.get_manacost() == 3
  play_big_game_hunter_actions = list(filter(lambda action: action.source == big_game_hunter, game.get_available_actions(game.current_player)))
  assert len(play_big_game_hunter_actions) == 1
  game.perform_action(play_big_game_hunter_actions[0])
  assert venture_co_mercenary.parent == venture_co_mercenary.owner.graveyard

def test_blood_knight():
  game = GameManager().create_test_game()
  sunwalker = game.game_manager.get_card("Sunwalker", game.current_player.other_player.board)
  argent_commander = game.game_manager.get_card("Argent Commander", game.current_player.other_player.board)
  argent_squire = game.game_manager.get_card("Argent Squire", game.current_player.board)
  blood_knight = game.game_manager.get_card("Blood Knight", game.current_player.hand)
  assert sunwalker.has_attribute(Attributes.DIVINE_SHIELD)
  assert argent_commander.has_attribute(Attributes.DIVINE_SHIELD)
  assert argent_squire.has_attribute(Attributes.DIVINE_SHIELD)
  play_blood_knight = list(filter(lambda action: action.source == blood_knight, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_blood_knight)
  assert blood_knight.get_attack() == 12
  assert blood_knight.get_health() == 12
  assert not sunwalker.has_attribute(Attributes.DIVINE_SHIELD)
  assert not argent_commander.has_attribute(Attributes.DIVINE_SHIELD)
  assert not argent_squire.has_attribute(Attributes.DIVINE_SHIELD)

def test_murloc_warleader():
  game = GameManager().create_test_game()
  murloc_warleader = game.game_manager.get_card("Murloc Warleader", game.current_player.board)
  murloc_tidehunter1 = game.game_manager.get_card("Murloc Tidehunter", game.current_player.other_player.board)
  murloc_tidehunter2 = game.game_manager.get_card("Murloc Tidehunter", game.current_player.board)
  assert murloc_warleader.get_attack() == 3
  assert murloc_warleader.get_health() == 3
  assert murloc_warleader.get_max_health() == 3
  assert murloc_tidehunter1.get_attack() == 4
  assert murloc_tidehunter1.get_health() == 2
  assert murloc_tidehunter1.get_max_health() == 2
  assert murloc_tidehunter2.get_attack() == 4
  assert murloc_tidehunter2.get_health() == 2
  assert murloc_tidehunter2.get_max_health() == 2

def test_southsea_captain():
  game = GameManager().create_test_game()
  southsea_captain = game.game_manager.get_card("Southsea Captain", game.current_player.board)
  southsea_deckhand = game.game_manager.get_card("Southsea Deckhand", game.current_player.board)
  enemy_deckhand = game.game_manager.get_card("Southsea Deckhand", game.current_player.other_player.board)
  assert southsea_captain.creature_type == CreatureTypes.PIRATE
  assert southsea_captain.get_attack() == 3
  assert southsea_captain.get_health() == 3
  assert southsea_captain.get_max_health() == 3
  assert southsea_deckhand.get_attack() == 3
  assert southsea_deckhand.get_health() == 2
  assert southsea_deckhand.get_max_health() == 2
  assert enemy_deckhand.get_attack() == 2
  assert enemy_deckhand.get_health() == 1
  assert enemy_deckhand.get_max_health() == 1

def test_faceless_manipulator():
  game = GameManager().create_test_game()
  argent_commander = game.game_manager.get_card("Argent Commander", game.current_player.board)
  faceless_manipulator = game.game_manager.get_card("Faceless Manipulator", game.current_player.hand)
  play_faceless = list(filter(lambda action: action.source == faceless_manipulator, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_faceless)
  assert faceless_manipulator.has_attribute(Attributes.DIVINE_SHIELD)
  assert faceless_manipulator.has_attribute(Attributes.CHARGE)
  assert faceless_manipulator.get_attack() == 4
  assert faceless_manipulator.get_health() == 2
  assert faceless_manipulator.get_max_health() == 2
  attack_actions = list(filter(lambda action: action.action_type==Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 2
  ironbeak = game.game_manager.get_card('Ironbeak Owl', game.current_player.hand)
  silence_manipulator =  list(filter(lambda action: action.source==ironbeak and action.targets[0]==faceless_manipulator, game.get_available_actions(game.current_player)))[0]
  game.perform_action(silence_manipulator)
  assert not faceless_manipulator.has_attribute(Attributes.DIVINE_SHIELD)
  assert not faceless_manipulator.has_attribute(Attributes.CHARGE)
  assert faceless_manipulator.get_attack() == 4
  assert faceless_manipulator.get_health() == 2
  assert faceless_manipulator.get_max_health() == 2

def test_sea_giant():
  game = GameManager().create_test_game()
  argent_commander = game.game_manager.get_card("Argent Commander", game.current_player.board)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  sea_giant =  game.game_manager.get_card("Sea Giant", game.current_player.hand)
  assert sea_giant.get_manacost() == 8
  wisp = game.game_manager.get_card("Wisp", game.current_player.board)
  assert sea_giant.get_manacost() == 7

def test_sea_giant_empty_board():
  game = GameManager().create_test_game()
  sea_giant =  game.game_manager.get_card("Sea Giant", game.current_player.hand)
  assert sea_giant.get_manacost() == 10

def test_mountain_giant():
  game = GameManager().create_test_game()
  mountain_giant =  game.game_manager.get_card("Mountain Giant", game.current_player.hand)
  assert mountain_giant.get_manacost() == 12
  wisp = game.game_manager.get_card("Wisp", game.current_player.hand)
  assert mountain_giant.get_manacost() == 11
  argent_commander = game.game_manager.get_card("Argent Commander", game.current_player.hand)
  assert mountain_giant.get_manacost() == 10
  for i in range(20):
    game.game_manager.get_card("Wisp", game.current_player.hand)
  assert mountain_giant.get_manacost() == 0
 
def test_molten_giant():
  game = GameManager().create_test_game()
  molten_giant =  game.game_manager.get_card("Molten Giant", game.current_player.hand)
  assert molten_giant.get_manacost() == 20
  game.deal_damage(game.current_player, 5)
  assert molten_giant.get_manacost() == 15
  game.deal_damage(game.current_player, 20)
  assert game.current_player.get_health() == 5
  assert molten_giant.get_manacost() == 0

# Test hunter cards

def test_hunters_mark():
  game = GameManager().create_test_game()
  molten_giant =  game.game_manager.get_card("Molten Giant", game.current_player.other_player.board)
  hunters_mark =  game.game_manager.get_card("Hunter's Mark", game.current_player.hand)
  game.deal_damage(molten_giant, 1)
  assert molten_giant.get_attack() == 8
  assert molten_giant.get_health() == 7
  assert molten_giant.get_max_health() == 8
  play_hunters_mark = list(filter(lambda action: action.source==hunters_mark, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_hunters_mark)
  assert molten_giant.get_attack() == 8
  assert molten_giant.get_health() == 1
  assert molten_giant.get_max_health() == 1

def test_arcane_shot():
  game = GameManager().create_test_game()
  arcane_shot =  game.game_manager.get_card("Arcane Shot", game.current_player.hand)
  watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.other_player.board)
  play_arcane_shot = list(filter(lambda action: action.source==arcane_shot and action.targets[0] == watcher, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_arcane_shot)
  assert watcher.get_health() == 3
  assert watcher.get_max_health() == 5

def test_timber_wolf():
  game = GameManager().create_test_game()
  emperor_cobra = game.game_manager.get_card("Emperor Cobra", game.current_player.board)
  wisp = game.game_manager.get_card("Wisp", game.current_player.board)
  assert emperor_cobra.get_attack() == 2
  assert emperor_cobra.get_health() == 3
  assert wisp.get_attack() == 1
  assert wisp.get_health() == 1
  timber_wolf =  game.game_manager.get_card("Timber Wolf", game.current_player.board)
  assert timber_wolf.get_attack() == 1
  assert timber_wolf.get_health() == 1
  assert emperor_cobra.get_attack() == 3
  assert emperor_cobra.get_health() == 3
  assert wisp.get_attack() == 1
  assert wisp.get_health() == 1


def test_tracking(): #tracking now tutors a beast instead of loot 3
  game = GameManager().create_test_game()
  tracking = game.game_manager.get_card("Tracking", game.current_player.hand)

  captains_parrot = game.game_manager.get_card("Captain's Parrot", game.current_player.hand)
  captains_parrot.change_parent(captains_parrot.owner.deck) #when initally setting to deck, has different owners for some reason?

  play_tracking = list(filter(lambda action: action.source == tracking, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_tracking)

  assert len(game.current_player.hand) == 1
  assert game.current_player.hand.get_all()[0].creature_type == CreatureTypes.BEAST

def test_starving_buzzard():
  game = GameManager().create_test_game()
  starving_buzzard = game.game_manager.get_card("Starving Buzzard", game.current_player.board)
  angry_chicken = game.game_manager.get_card("Angry Chicken", game.current_player.hand)
  play_chicken = list(filter(lambda action: action.source == angry_chicken, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_chicken)
  assert len(game.current_player.hand) == 1
  angry_chicken2 = game.game_manager.get_card("Angry Chicken", game.current_player.hand)
  play_chicken2 = list(filter(lambda action: action.source == angry_chicken2, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_chicken2)
  assert len(game.current_player.hand) == 2
  assert starving_buzzard.creature_type == CreatureTypes.BEAST
  assert starving_buzzard.get_attack() == 2
  assert starving_buzzard.get_health() == 1

def test_animal_companion():
  game = GameManager(RandomState()).create_test_game()
  animal_companion = game.game_manager.get_card("Animal Companion", game.current_player.hand)
  play_companion = list(filter(lambda action: action.source == animal_companion, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_companion)
  if game.current_player.board.get_all()[0].name == "Leokk":
    wisp = game.game_manager.get_card("Wisp", game.current_player.board)
    assert wisp.get_attack() == 2
    assert wisp.get_health() == 1
  else:
    assert game.current_player.board.get_all()[0].name in ["Misha", "Huffer"]


def test_kill_command():
  game = GameManager().create_test_game()
  kill_command = game.game_manager.get_card('Kill Command', game.current_player.hand)
  assert kill_command.effect.value(Action(Actions.CAST_EFFECT, kill_command, [kill_command])) == 3
  river_crok = game.game_manager.get_card('River Crocolisk', game.current_player.board)
  assert kill_command.effect.value(Action(Actions.CAST_EFFECT, kill_command, [kill_command])) == 5
  cast_command = list(filter(lambda action: action.source == kill_command and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_command)
  assert game.current_player.other_player.get_health() == 25

def test_houndmaster():
  game = GameManager().create_test_game()
  houndmaster = game.game_manager.get_card('Houndmaster', game.current_player.hand)
  river_crok = game.game_manager.get_card('River Crocolisk', game.current_player.board)
  assert river_crok.get_attack() == 2
  assert river_crok.get_health() == 3
  play_houndmaster = list(filter(lambda action: action.source == houndmaster and action.targets[0] == river_crok, game.get_available_actions(game.current_player)))
  game.perform_action(play_houndmaster[0])
  assert river_crok.get_attack() == 4
  assert river_crok.get_health() == 5
  assert river_crok.has_attribute(Attributes.TAUNT)

def test_multishot_zero_targets():
  game = GameManager().create_test_game()
  multishot = game.game_manager.get_card('Multi-Shot', game.current_player.hand)
  play_multishot_actions = list(filter(lambda action: action.source == multishot, game.get_available_actions(game.current_player)))
  assert len(play_multishot_actions) == 0

def test_multishot_one_targets():
  game = GameManager().create_test_game()
  mountain_giant = game.game_manager.get_card('Mountain Giant', game.current_player.other_player.board)
  multishot = game.game_manager.get_card('Multi-Shot', game.current_player.hand)
  play_multishot = list(filter(lambda action: action.source == multishot, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_multishot)
  assert mountain_giant.get_health() == 5

def test_multishot():
  game = GameManager().create_test_game()
  mountain_giant = game.game_manager.get_card('Mountain Giant', game.current_player.other_player.board)
  sea_giant = game.game_manager.get_card('Sea Giant', game.current_player.other_player.board)
  multishot = game.game_manager.get_card('Multi-Shot', game.current_player.hand)
  play_multishot = list(filter(lambda action: action.source == multishot, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_multishot)
  assert mountain_giant.get_health() == 5
  assert sea_giant.get_health() == 5


  
def test_tundra_rhino():
  game = GameManager().create_test_game()
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  river_crok = game.game_manager.get_card('River Crocolisk', game.current_player.board)

  assert tundra_rhino.has_attribute(Attributes.CHARGE)
  assert river_crok.has_attribute(Attributes.CHARGE)
  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))) == 2

  
def test_explosive_trap():
  game = GameManager().create_test_game()
  river_crok = game.game_manager.get_card('River Crocolisk', game.current_player.other_player.board)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.other_player.board)
  explosive_trap = game.game_manager.get_card('Explosive Trap', game.current_player.hand)
  play_trap = list(filter(lambda action: action.source == explosive_trap, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_trap)
  assert explosive_trap.parent == explosive_trap.owner.secrets_zone
  enemy_attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player.other_player)))
  assert len(enemy_attack_actions) == 2
  assert game.current_player.other_player.get_health() == 30
  assert game.current_player.get_health() == 30
  assert river_crok.get_health() == 3
  assert tundra_rhino.get_health() == 5
  game.perform_action(enemy_attack_actions[0])
  assert game.current_player.other_player.get_health() == 28
  assert game.current_player.get_health() == 28 #got attacked by a 2-attack minion
  assert river_crok.get_health() == 1
  assert tundra_rhino.get_health() == 3
  assert explosive_trap.parent == explosive_trap.owner.graveyard

def test_freezing_trap():
  game = GameManager().create_test_game()
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.other_player.board)
  freezing_trap = game.game_manager.get_card('Freezing Trap', game.current_player.hand)
  play_trap = list(filter(lambda action: action.source == freezing_trap, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_trap)
  assert freezing_trap.parent == freezing_trap.owner.secrets_zone
  enemy_attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player.other_player)))
  assert len(enemy_attack_actions) == 1
  game.perform_action(enemy_attack_actions[0])
  assert tundra_rhino.parent == tundra_rhino.owner.hand
  assert tundra_rhino.get_manacost() == 7
  assert freezing_trap.parent == freezing_trap.owner.graveyard
  
def test_scavenging_hyena():
  game = GameManager().create_test_game()
  scavenging_hyena = game.game_manager.get_card('Scavenging Hyena', game.current_player.board)
  assert scavenging_hyena.get_attack() == 2
  assert scavenging_hyena.get_health() == 2
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  game.deal_damage(tundra_rhino, 5)
  assert scavenging_hyena.get_attack() == 4
  assert scavenging_hyena.get_health() == 3
  enemy_crok = game.game_manager.get_card('River Crocolisk', game.current_player.other_player.board)
  game.deal_damage(enemy_crok, 5)
  assert scavenging_hyena.get_attack() == 4
  assert scavenging_hyena.get_health() == 3
  friendly_crok = game.game_manager.get_card('River Crocolisk', game.current_player.board)
  game.deal_damage(friendly_crok, 5)
  assert scavenging_hyena.get_attack() == 6
  assert scavenging_hyena.get_health() == 4

def test_deadly_shot():
  game = GameManager().create_test_game()
  deadly_shot = game.game_manager.get_card('Deadly Shot', game.current_player.hand)
  enemy_crok = game.game_manager.get_card('River Crocolisk', game.current_player.other_player.board)

  play_deadly_shot = list(filter(lambda action: action.source == deadly_shot, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_deadly_shot)
  assert enemy_crok.parent == enemy_crok.owner.graveyard

def test_unleash_the_hounds():
  game = GameManager().create_test_game()
  unleash_the_hounds = game.game_manager.get_card('Unleash the Hounds', game.current_player.hand)
  enemy_crok = game.game_manager.get_card('River Crocolisk', game.current_player.other_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  enemy_giant = game.game_manager.get_card('Mountain Giant', game.current_player.other_player.board)
  firendly_wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  play_unleash = list(filter(lambda action: action.source == unleash_the_hounds, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_unleash)
  assert len(game.current_player.board) == 4

def test_flare():
  game = GameManager().create_test_game()
  flare = game.game_manager.get_card('Flare', game.current_player.hand)
  enemy_snipe = game.game_manager.get_card('Snipe', game.current_player.other_player.secrets_zone)
  worgen_infiltrator = game.game_manager.get_card('Worgen Infiltrator', game.current_player.other_player.board)
  assert len(game.current_player.other_player.secrets_zone) == 1
  assert worgen_infiltrator.has_attribute(Attributes.STEALTH)
  play_flare = list(filter(lambda action: action.source == flare, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_flare)
  assert len(game.current_player.other_player.secrets_zone) == 0
  assert not worgen_infiltrator.has_attribute(Attributes.STEALTH)
  assert enemy_snipe.parent == enemy_snipe.owner.graveyard
  assert len(game.current_player.hand) == 1
 
def test_misdirection():
  game = GameManager().create_test_game()
  enemy_misdirection = game.game_manager.get_card('Misdirection', game.current_player.other_player.secrets_zone)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  assert game.current_player.get_health() == 28
  assert enemy_misdirection.parent == enemy_misdirection.owner.graveyard

def test_eaglehorn_bow():
  game = GameManager().create_test_game()
  eaglehorn_bow = game.game_manager.get_card('Eaglehorn Bow', game.current_player)
  assert game.current_player.weapon == eaglehorn_bow
  assert eaglehorn_bow.get_health() == 2
  enemy_misdirection = game.game_manager.get_card('Misdirection', game.current_player.other_player.secrets_zone)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  assert game.current_player.get_health() == 28
  assert enemy_misdirection.parent == enemy_misdirection.owner.graveyard
  assert eaglehorn_bow.get_health() == 3

def test_explosive_shot():
  game = GameManager().create_test_game()
  explosive_shot = game.game_manager.get_card('Explosive Shot', game.current_player.hand)
  enemy_giant1 = game.game_manager.get_card('Sea Giant', game.current_player.other_player.board)
  enemy_giant2 = game.game_manager.get_card('Sea Giant', game.current_player.other_player.board)
  enemy_giant3 = game.game_manager.get_card('Sea Giant', game.current_player.other_player.board)

  cast_explosive_shot = list(filter(lambda action: action.source == explosive_shot and action.targets[0] == enemy_giant1, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_explosive_shot)
  assert enemy_giant1.get_health() == 3
  assert enemy_giant2.get_health() == 6
  assert enemy_giant3.get_health() == 6

def test_savannah_highmane():
  game = GameManager().create_test_game()
  savannah_highmane = game.game_manager.get_card('Savannah Highmane', game.current_player.board)
  game.deal_damage(savannah_highmane, 5)
  assert len(game.current_player.board) == 2
  for hyena in game.current_player.board:
    assert hyena.creature_type == CreatureTypes.BEAST
    assert hyena.get_attack() == 2
    assert hyena.get_health() == 2

def test_beastial_wrath():
  game = GameManager().create_test_game()
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  assert tundra_rhino.get_attack() == 2
  beastial_wrath = game.game_manager.get_card('Beastial Wrath', game.current_player.hand)
  cast_beastial_wrath = list(filter(lambda action: action.source == beastial_wrath, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_beastial_wrath)
  assert tundra_rhino.get_attack() == 4
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  assert game.current_player.other_player.get_health() == 26
  game.end_turn()
  assert tundra_rhino.get_attack() == 2

def test_beastial_wrath_immunity():
  game = GameManager().create_test_game()
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  assert tundra_rhino.get_attack() == 2
  beastial_wrath = game.game_manager.get_card('Beastial Wrath', game.current_player.hand)
  cast_beastial_wrath = list(filter(lambda action: action.source == beastial_wrath, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_beastial_wrath)
  assert tundra_rhino.get_attack() == 4
  assert tundra_rhino.has_attribute(Attributes.IMMUNE)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert tundra_rhino.get_health() == 5
  game.end_turn()
  assert tundra_rhino.get_attack() == 2
  assert not tundra_rhino.has_attribute(Attributes.IMMUNE)

def test_snake_trap():
  game = GameManager().create_test_game()
  snake_trap = game.game_manager.get_card('Snake Trap', game.current_player.other_player.secrets_zone)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  assert snake_trap.parent == snake_trap.owner.graveyard
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert tundra_rhino.get_health() == 4
  assert len(game.current_player.other_player.board) == 3
  for snake in game.current_player.other_player.board:
    assert snake.creature_type == CreatureTypes.BEAST
    assert snake.get_attack() == 1
    assert snake.get_health() == 1

def test_gladiators_longbow():
  game = GameManager().create_test_game()
  gladiators_longbow = game.game_manager.get_card("Gladiator's Longbow", game.current_player)
  assert game.current_player.weapon
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  attack_wisp = list(filter(lambda action: action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_wisp)
  assert gladiators_longbow.get_health() == 1
  assert game.current_player.get_health() == 30
  attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 0
  game.deal_damage(game.current_player, 10)
  assert game.current_player.get_health() == 20

# Mage cards

def test_arcane_missiles():
  game = GameManager(RandomState()).create_test_game()
  arcane_missiles = game.game_manager.get_card("Arcane Missiles", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  cast_missiles = list(filter(lambda action: action.source == arcane_missiles, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_missiles)
  assert enemy_wisp.get_health() == 0 and game.current_player.other_player.get_health() == 28 \
      or enemy_wisp.get_health() == -1 and game.current_player.other_player.get_health() == 29 \
      or enemy_wisp.get_health() == -2 and game.current_player.other_player.get_health() == 30 \
      or game.current_player.other_player.get_health() == 27

def test_mirror_image():
  game = GameManager().create_test_game()
  mirror_image = game.game_manager.get_card("Mirror Image", game.current_player.hand)
  cast_mirror_image = list(filter(lambda action: action.source == mirror_image, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_mirror_image)
  assert len(game.current_player.board) == 2
  for mirror_token in game.current_player.board:
    assert mirror_token.has_attribute(Attributes.TAUNT)
    mirror_token.attacks_this_turn = 0
  attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 0 #cant attack with 0 power
  for mirror_token in game.current_player.board:
    mirror_token.attack = 1
  attack_actions = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(attack_actions) == 2 #can attack with 1 power

def test_arcane_explosion():
  game = GameManager().create_test_game()
  arcane_explosion = game.game_manager.get_card("Arcane Explosion", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_watcher = game.game_manager.get_card("Ancient Watcher", game.current_player.other_player.board)
  assert enemy_wisp.get_health() == 1
  assert enemy_watcher.get_health() == 5
  cast_arcane_explosion = list(filter(lambda action: action.source == arcane_explosion, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_arcane_explosion)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert enemy_watcher.get_health() == 4
  assert game.current_player.other_player.get_health() == 30

def test_frostbolt():
  game = GameManager().create_test_game()
  frostbolt = game.game_manager.get_card("Frostbolt", game.current_player.hand)
  enemy_rhino = game.game_manager.get_card("Tundra Rhino", game.current_player.other_player.board)
  assert enemy_rhino.get_health() == 5
  assert enemy_rhino.has_attribute(Attributes.CHARGE)
  assert not enemy_rhino.has_attribute(Attributes.FROZEN)
  cast_frostbolt = list(filter(lambda action: action.source == frostbolt and action.targets[0] == enemy_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_frostbolt)
  assert enemy_rhino.has_attribute(Attributes.FROZEN)
  assert enemy_rhino.get_health() == 2
  game.end_turn()
  game.untap()
  attack_actions_with_rhino = list(filter(lambda action: action.source == enemy_rhino, game.get_available_actions(game.current_player)))
  assert len(attack_actions_with_rhino) == 0
  assert enemy_rhino.has_attribute(Attributes.FROZEN)
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  attack_actions_with_rhino = list(filter(lambda action: action.source == enemy_rhino, game.get_available_actions(game.current_player)))
  assert len(attack_actions_with_rhino) == 1
  assert not enemy_rhino.has_attribute(Attributes.FROZEN)

def test_arcane_intellect():
  game = GameManager().create_test_game()
  arcane_intellect = game.game_manager.get_card("Arcane Intellect", game.current_player.hand)
  assert len(game.current_player.hand) == 1
  cast_arcane_intellect = list(filter(lambda action: action.source == arcane_intellect, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_arcane_intellect)
  assert len(game.current_player.hand) == 2

def test_arcane_intellect_full_hand():
  game = GameManager().create_test_game()
  arcane_intellect = game.game_manager.get_card("Arcane Intellect", game.current_player.hand)
  assert len(game.current_player.hand) == 1
  for wisp_number in range(9):
    game.game_manager.get_card("Wisp", game.current_player.hand)
  assert len(game.current_player.hand) == 10
  cast_arcane_intellect = list(filter(lambda action: action.source == arcane_intellect, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_arcane_intellect)
  assert len(game.current_player.hand) == 10
  assert len(game.current_player.graveyard) == 2

def test_frost_nova():
  game = GameManager().create_test_game()
  frost_nova = game.game_manager.get_card("Frost Nova", game.current_player.hand)
  for wisp_number in range(4):
    game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  cast_frost_nova = list(filter(lambda action: action.source == frost_nova, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_frost_nova)
  for wisp in game.current_player.other_player.board:
    assert wisp.has_attribute(Attributes.FROZEN)
  game.end_turn()
  game.untap()
  for wisp in game.current_player.other_player.board:
    assert wisp.has_attribute(Attributes.FROZEN)
  game.end_turn()
  game.untap()
  for wisp in game.current_player.other_player.board:
    assert not wisp.has_attribute(Attributes.FROZEN)

def test_polymorph():
  game = GameManager().create_test_game()
  polymorph = game.game_manager.get_card("Polymorph", game.current_player.hand)
  enemy_giant = game.game_manager.get_card("Sea Giant", game.current_player.other_player.board)
  play_polymorph = list(filter(lambda action: action.source == polymorph, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_polymorph)
  assert enemy_giant.parent == enemy_giant.owner.graveyard
  enemy_sheep = game.current_player.other_player.board.get_all()[0]
  assert enemy_sheep.name == "Sheep"
  assert enemy_sheep.get_attack() == 1
  assert enemy_sheep.creature_type == CreatureTypes.BEAST

def test_water_elemental():
  game = GameManager().create_test_game()
  water_elemental = game.game_manager.get_card("Water Elemental", game.current_player.board)
  enemy_giant = game.game_manager.get_card("Sea Giant", game.current_player.other_player.board)
  water_elemental.attacks_this_turn = 0
  attack_with_elemental = list(filter(lambda action: action.source == water_elemental and action.targets[0] == enemy_giant, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_elemental)
  assert enemy_giant.has_attribute(Attributes.FROZEN)
  assert water_elemental.parent == water_elemental.owner.graveyard
  game.end_turn()
  game.untap()
  giant_attack_actions = list(filter(lambda action: action.source == enemy_giant, game.get_available_actions(game.current_player)))
  assert len(giant_attack_actions) == 0
  assert enemy_giant.has_attribute(Attributes.FROZEN)
  game.end_turn()
  game.untap()
  assert not enemy_giant.has_attribute(Attributes.FROZEN)

def test_water_elemental_player():
  game = GameManager().create_test_game()
  water_elemental = game.game_manager.get_card("Water Elemental", game.current_player.board)
  water_elemental.attacks_this_turn = 0
  attack_with_elemental = list(filter(lambda action: action.action_type==Actions.ATTACK and action.source == water_elemental, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_elemental)
  assert game.current_player.other_player.has_attribute(Attributes.FROZEN)
  generic_weapon = game.game_manager.get_card("Generic Weapon", game.current_player.other_player)
  game.end_turn()
  game.untap()
  enemy_weapon_attacks = list(filter(lambda action: action.action_type==Actions.ATTACK and action.source == game.current_player, game.get_available_actions(game.current_player)))
  assert len(enemy_weapon_attacks) == 0
  assert game.current_player.has_attribute(Attributes.FROZEN)
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  enemy_weapon_attacks = list(filter(lambda action: action.action_type==Actions.ATTACK and action.source == game.current_player, game.get_available_actions(game.current_player)))
  assert len(enemy_weapon_attacks) == 2
  assert not game.current_player.has_attribute(Attributes.FROZEN)

def test_flamestrike():
  game = GameManager().create_test_game()
  enemy_water_elemental = game.game_manager.get_card("Water Elemental", game.current_player.other_player.board)
  friendly_wisp = game.game_manager.get_card("Wisp", game.current_player.board)
  flamestrike = game.game_manager.get_card("Flamestrike", game.current_player.hand)
  cast_flamestrike_actions = list(filter(lambda action: action.source == flamestrike, game.get_available_actions(game.current_player)))
  assert len(cast_flamestrike_actions) == 1
  assert enemy_water_elemental.get_health() == 6
  
  game.perform_action(cast_flamestrike_actions[0])
  assert enemy_water_elemental.get_health() == 2
  assert friendly_wisp.parent == friendly_wisp.owner.board
  
def test_ice_lance():
  game = GameManager().create_test_game()
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  ice_lance = game.game_manager.get_card("Ice Lance", game.current_player.hand)
  cast_ice_lance = list(filter(lambda action: action.source == ice_lance and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_ice_lance)
  assert enemy_wisp.has_attribute(Attributes.FROZEN)
  assert enemy_wisp.parent == enemy_wisp.owner.board
  ice_lance2 = game.game_manager.get_card("Ice Lance", game.current_player.hand)
  cast_ice_lance2 = list(filter(lambda action: action.source == ice_lance2 and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_ice_lance2)
  assert enemy_wisp.parent == enemy_wisp.owner.graveyard
  assert enemy_wisp.get_health() == -3 

def test_mana_wyrm():
  game = GameManager().create_test_game()
  mana_wyrm = game.game_manager.get_card("Mana Wyrm", game.current_player.board)
  ice_lance = game.game_manager.get_card("Ice Lance", game.current_player.hand)
  cast_ice_lance = list(filter(lambda action: action.source == ice_lance and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  assert mana_wyrm.get_attack() == 1
  assert mana_wyrm.get_health() == 3
  game.perform_action(cast_ice_lance)
  assert mana_wyrm.get_attack() == 2
  assert mana_wyrm.get_health() == 3
  assert game.current_player.other_player.has_attribute(Attributes.FROZEN)
  assert game.current_player.other_player.get_health() == 30
  ice_lance2 = game.game_manager.get_card("Ice Lance", game.current_player.hand)
  cast_ice_lance2 = list(filter(lambda action: action.source == ice_lance2 and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_ice_lance2)
  assert mana_wyrm.get_attack() == 3
  assert mana_wyrm.get_health() == 3
  assert game.current_player.other_player.has_attribute(Attributes.FROZEN)
  assert game.current_player.other_player.get_health() == 26

def test_sorcerers_apprentice():
  game = GameManager().create_test_game()
  ice_lance = game.game_manager.get_card("Ice Lance", game.current_player.hand)
  assert ice_lance.get_manacost() == 1
  sorcerers_apprentice = game.game_manager.get_card("Sorcerer's Apprentice", game.current_player.board)
  assert ice_lance.get_manacost() == 0
  river_crok = game.game_manager.get_card("River Crocolisk", game.current_player.hand)
  assert river_crok.get_manacost() == 2
  enemy_ice_lance = game.game_manager.get_card("Ice Lance", game.current_player.other_player.hand)
  assert enemy_ice_lance.get_manacost() == 1

def test_ice_barrier():
  game = GameManager().create_test_game()
  ice_barrier = game.game_manager.get_card("Ice Barrier", game.current_player.other_player.secrets_zone)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  assert game.current_player.other_player.armor == 0
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  assert game.current_player.other_player.armor == 6
  assert game.current_player.other_player.get_health() == 30
  assert ice_barrier.parent == ice_barrier.owner.graveyard

def test_multiple_secrets():
  game = GameManager().create_test_game()
  ice_barrier = game.game_manager.get_card("Ice Barrier", game.current_player.other_player.secrets_zone)
  enemy_misdirection = game.game_manager.get_card('Misdirection', game.current_player.other_player.secrets_zone)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]

  assert game.current_player.other_player.armor == 0
  game.perform_action(attack_with_rhino)
  assert game.current_player.other_player.armor == 8
  assert game.current_player.other_player.get_health() == 30
  assert game.current_player.get_health() == 28
  assert enemy_misdirection.parent == enemy_misdirection.owner.graveyard
  assert ice_barrier.parent == ice_barrier.owner.graveyard

def test_mirror_entity():
  game = GameManager().create_test_game()
  mirror_entity = game.game_manager.get_card("Mirror Entity", game.current_player.other_player.secrets_zone)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.hand)
  play_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_rhino)
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  for card in game.current_player.board:
    assert card.name == "Tundra Rhino"
    assert card.collectable
    assert card.owner == game.current_player

  for card in game.current_player.other_player.board:
    assert card.name == "Tundra Rhino"
    assert not card.collectable
    assert card.owner == game.current_player.other_player

def test_cone_of_cold_one_target():
  game = GameManager().create_test_game()
  cone_of_cold = game.game_manager.get_card("Cone of Cold", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  play_cone_of_cold = list(filter(lambda action: action.source == cone_of_cold, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_cone_of_cold)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.has_attribute(Attributes.FROZEN)

def test_cone_of_cold_two_targets():
  game = GameManager().create_test_game()
  cone_of_cold = game.game_manager.get_card("Cone of Cold", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp2 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)

  play_cone_of_cold = list(filter(lambda action: action.source == cone_of_cold and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_cone_of_cold)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.has_attribute(Attributes.FROZEN)
  assert enemy_wisp2.get_health() == 0
  assert enemy_wisp2.has_attribute(Attributes.FROZEN)


def test_cone_of_cold_three_targets():
  game = GameManager().create_test_game()
  cone_of_cold = game.game_manager.get_card("Cone of Cold", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp2 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp3 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)

  play_cone_of_cold = list(filter(lambda action: action.source == cone_of_cold and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_cone_of_cold)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.has_attribute(Attributes.FROZEN)

  assert enemy_wisp2.get_health() == 0
  assert enemy_wisp2.has_attribute(Attributes.FROZEN)

  assert enemy_wisp3.get_health() == 0
  assert enemy_wisp3.has_attribute(Attributes.FROZEN)


def test_cone_of_cold_three_targets_middle():
  game = GameManager().create_test_game()
  cone_of_cold = game.game_manager.get_card("Cone of Cold", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp2 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp3 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)

  play_cone_of_cold = list(filter(lambda action: action.source == cone_of_cold and action.targets[0] == enemy_wisp2, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_cone_of_cold)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.has_attribute(Attributes.FROZEN)

  assert enemy_wisp2.get_health() == 0
  assert enemy_wisp2.has_attribute(Attributes.FROZEN)

  assert enemy_wisp3.get_health() == 0
  assert enemy_wisp3.has_attribute(Attributes.FROZEN)


def test_cone_of_cold_four_targets():
  game = GameManager().create_test_game()
  cone_of_cold = game.game_manager.get_card("Cone of Cold", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp2 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp3 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp4 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)

  play_cone_of_cold = list(filter(lambda action: action.source == cone_of_cold and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_cone_of_cold)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.has_attribute(Attributes.FROZEN)

  assert enemy_wisp2.get_health() == 0  
  assert enemy_wisp2.has_attribute(Attributes.FROZEN)

  assert enemy_wisp3.get_health() == 1  
  assert not enemy_wisp3.has_attribute(Attributes.FROZEN)

  assert enemy_wisp4.get_health() == 0 
  assert enemy_wisp4.has_attribute(Attributes.FROZEN)


def test_cone_of_cold_four_targets_last():
  game = GameManager().create_test_game()
  cone_of_cold = game.game_manager.get_card("Cone of Cold", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp2 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp3 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)
  enemy_wisp4 = game.game_manager.get_card("Wisp", game.current_player.other_player.board)

  play_cone_of_cold = list(filter(lambda action: action.source == cone_of_cold and action.targets[0] == enemy_wisp4, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_cone_of_cold)
  assert enemy_wisp.get_health() == 0
  assert enemy_wisp.has_attribute(Attributes.FROZEN)

  assert enemy_wisp2.get_health() == 1
  assert not enemy_wisp2.has_attribute(Attributes.FROZEN)

  assert enemy_wisp3.get_health() == 0
  assert enemy_wisp3.has_attribute(Attributes.FROZEN)

  assert enemy_wisp4.get_health() == 0
  assert enemy_wisp4.has_attribute(Attributes.FROZEN)

def test_counterspell():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.other_player.secrets_zone)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast_fireball = list(filter(lambda action: action.source == fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball)
  assert fireball.parent == fireball.owner.graveyard
  assert counterspell.parent == counterspell.owner.graveyard
  assert game.current_player.other_player.get_health() == 30

def test_counterspell_friendly():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.secrets_zone)
  fireball = game.game_manager.get_card('Fireball', game.current_player.hand)
  cast_fireball = list(filter(lambda action: action.source == fireball and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_fireball)
  assert fireball.parent == fireball.owner.graveyard
  assert counterspell.parent == counterspell.owner.secrets_zone
  assert game.current_player.other_player.get_health() == 24

def test_counterspell_on_secret():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.other_player.secrets_zone)
  misdirection = game.game_manager.get_card('Misdirection', game.current_player.hand)
  play_misdirection = list(filter(lambda action: action.source == misdirection, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_misdirection)
  assert counterspell.parent == counterspell.owner.graveyard
  assert misdirection.parent == misdirection.owner.graveyard

def test_counterspell_on_flare():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.other_player.secrets_zone)
  flare = game.game_manager.get_card('Flare', game.current_player.hand)
  play_flare = list(filter(lambda action: action.source == flare, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_flare)
  assert counterspell.parent == counterspell.owner.graveyard
  assert flare.parent == flare.owner.graveyard
  assert len(game.current_player.hand) == 0

def test_kirin_tor_mage():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.hand)
  kirin_tor_mage = game.game_manager.get_card('Kirin Tor Mage', game.current_player.hand)
  assert game.current_player.current_mana == 10
  play_kirin_tor_mage = list(filter(lambda action: action.source == kirin_tor_mage, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_kirin_tor_mage)
  assert game.current_player.current_mana == 7
  assert game.current_player.has_attribute(Attributes.FREE_SECRET)
  assert counterspell.get_manacost() == 0
  play_counterspell = list(filter(lambda action: action.source == counterspell, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_counterspell)
  assert game.current_player.current_mana == 7
  misdirection = game.game_manager.get_card('Misdirection', game.current_player.hand)
  assert misdirection.get_manacost() == 2

def test_kirin_tor_mage_end_turn():
  game = GameManager().create_test_game()
  counterspell = game.game_manager.get_card('Counterspell', game.current_player.hand)
  kirin_tor_mage = game.game_manager.get_card('Kirin Tor Mage', game.current_player.hand)
  play_kirin_tor_mage = list(filter(lambda action: action.source == kirin_tor_mage, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_kirin_tor_mage)
  assert game.current_player.current_mana == 7
  assert game.current_player.has_attribute(Attributes.FREE_SECRET)
  assert counterspell.get_manacost() == 0
  game.end_turn()
  game.untap()
  game.end_turn()
  game.untap()
  assert not game.current_player.has_attribute(Attributes.FREE_SECRET)
  assert counterspell.get_manacost() == 3

def test_no_duplicate_secrets():
  game = GameManager().create_test_game()
  counterspell_in_zone = game.game_manager.get_card('Counterspell', game.current_player.secrets_zone)
  counterspell_in_hand = game.game_manager.get_card('Counterspell', game.current_player.hand)
  play_counterspell_in_hand_actions = list(filter(lambda action: action.source == counterspell_in_hand, game.get_available_actions(game.current_player)))
  assert len(play_counterspell_in_hand_actions) == 0

def test_vaporize():
  game = GameManager().create_test_game()
  vaporize = game.game_manager.get_card('Vaporize', game.current_player.other_player.secrets_zone)
  tundra_rhino = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  attack_with_rhino = list(filter(lambda action: action.source == tundra_rhino, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_with_rhino)
  assert vaporize.parent == vaporize.owner.graveyard
  assert tundra_rhino.parent == tundra_rhino.owner.graveyard
  assert game.current_player.other_player.get_health() == 30

def test_etherial_arcanist():
  game = GameManager().create_test_game()
  vaporize = game.game_manager.get_card('Vaporize', game.current_player.secrets_zone)
  etherial_arcanist = game.game_manager.get_card('Etherial Arcanist', game.current_player.board)
  assert etherial_arcanist.get_attack() == 3
  assert etherial_arcanist.get_health() == 3
  game.end_turn()
  game.untap()
  assert etherial_arcanist.get_attack() == 5
  assert etherial_arcanist.get_health() == 5
  game.end_turn()
  game.untap()
  assert etherial_arcanist.get_attack() == 5
  assert etherial_arcanist.get_health() == 5
  game.end_turn()
  game.untap()
  assert etherial_arcanist.get_attack() == 7
  assert etherial_arcanist.get_health() == 7
  vaporize.change_parent(vaporize.owner.graveyard)
  game.end_turn()
  game.untap()
  assert etherial_arcanist.get_attack() == 7
  assert etherial_arcanist.get_health() == 7
  game.end_turn()
  game.untap()
  assert etherial_arcanist.get_attack() == 7
  assert etherial_arcanist.get_health() == 7

def test_blizzard():
  game = GameManager().create_test_game()
  blizzard = game.game_manager.get_card('Blizzard', game.current_player.hand)
  etherial_arcanist = game.game_manager.get_card('Etherial Arcanist', game.current_player.other_player.board)
  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  play_blizzard = list(filter(lambda action: action.source == blizzard, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_blizzard)
  assert etherial_arcanist.get_health() == 1
  assert etherial_arcanist.has_attribute(Attributes.FROZEN)
  assert wisp.get_health() == -1
  assert wisp.parent == wisp.owner.graveyard
  game.end_turn()
  game.untap()
  attack_with_etherial_actions =  list(filter(lambda action: action.source == etherial_arcanist, game.get_available_actions(game.current_player)))
  assert len(attack_with_etherial_actions) == 0
  assert etherial_arcanist.has_attribute(Attributes.FROZEN)

def test_ice_block():
  game = GameManager().create_test_game()
  ice_block = game.game_manager.get_card('Ice Block', game.current_player.other_player.secrets_zone)
  game.current_player.other_player.armor = 5
  game.deal_damage(game.current_player.other_player, 40)
  assert game.current_player.other_player.armor == 5
  assert game.current_player.other_player.get_health() == 30
  assert game.current_player.other_player.has_attribute(Attributes.IMMUNE)
  assert ice_block.parent == ice_block.owner.graveyard
  game.deal_damage(game.current_player.other_player, 1)
  assert game.current_player.other_player.armor == 5
  assert game.current_player.other_player.get_health() == 30
  game.end_turn()
  game.untap()
  assert not game.current_player.has_attribute(Attributes.IMMUNE)

def test_spellbender():
  game = GameManager().create_test_game()
  spellbender = game.game_manager.get_card('Spellbender', game.current_player.other_player.secrets_zone)
  ice_lance = game.game_manager.get_card('Ice Lance', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  freeze_wisp = list(filter(lambda action: action.source == ice_lance and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(freeze_wisp)
  assert not enemy_wisp.has_attribute(Attributes.FROZEN)
  assert len(game.current_player.other_player.board) == 2
  spellbender_token = game.current_player.other_player.board.get_all()[1]
  assert spellbender_token.name == "Spellbender Token"
  assert spellbender_token.has_attribute(Attributes.FROZEN)
  assert spellbender.parent == spellbender.owner.graveyard
  
def test_spellbender_friendly():
  game = GameManager().create_test_game()
  spellbender = game.game_manager.get_card('Spellbender', game.current_player.secrets_zone)
  ice_lance = game.game_manager.get_card('Ice Lance', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  freeze_wisp = list(filter(lambda action: action.source == ice_lance and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(freeze_wisp)
  assert enemy_wisp.has_attribute(Attributes.FROZEN)
  assert len(game.current_player.other_player.board) == 1
  assert len(game.current_player.board) == 0
  assert spellbender.parent == spellbender.owner.secrets_zone
  
def test_spellbender_full_board():
  game = GameManager().create_test_game()
  spellbender = game.game_manager.get_card('Spellbender', game.current_player.other_player.secrets_zone)
  ice_lance = game.game_manager.get_card('Ice Lance', game.current_player.hand)
  enemy_wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  for addition_wisp in range(6):
    game.game_manager.get_card('Wisp', game.current_player.other_player.board)
  assert len(game.current_player.other_player.board) == game.current_player.other_player.board.max_entries
  freeze_wisp = list(filter(lambda action: action.source == ice_lance and action.targets[0] == enemy_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(freeze_wisp)
  assert enemy_wisp.has_attribute(Attributes.FROZEN)
  assert len(game.current_player.other_player.board) == 7
  assert spellbender.parent == spellbender.owner.secrets_zone

def test_pyroblast():
  game = GameManager().create_test_game()
  pyroblast = game.game_manager.get_card('Pyroblast', game.current_player.hand)
  pyroblast_enemy = list(filter(lambda action: action.source == pyroblast and action.targets[0] == game.current_player.other_player, game.get_available_actions(game.current_player)))[0]
  game.perform_action(pyroblast_enemy)
  assert game.current_player.other_player.get_health() == 20

def test_battlecry_reduce_cost():
  game = GameManager().create_test_game()

  battlecry_reduce_cost = game.game_manager.get_card("Battlecry Reduce Cost", game.current_player.hand)
  enemy_wisp = game.game_manager.get_card("Wisp", game.current_player.other_player.hand)
  fireball = game.game_manager.get_card('Fireball', game.current_player.other_player.hand)
  friendly_wisp = game.game_manager.get_card('Wisp', game.current_player.hand)

  assert enemy_wisp.get_manacost() == 0
  assert battlecry_reduce_cost.get_manacost() == 0
  assert fireball.get_manacost() == 4
  assert friendly_wisp.get_manacost() == 0

  play_battlecry = list(filter(lambda action: action.source == battlecry_reduce_cost, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_battlecry)

  assert enemy_wisp.get_manacost() == 1
  assert battlecry_reduce_cost.get_manacost() == 0
  assert fireball.get_manacost() == 5
  assert friendly_wisp.get_manacost() == 0

def test_windfury_weapon():
  game = GameManager().create_test_game()

  new_weapon = game.game_manager.get_card('Windfury Weapon', game.current_player.hand)

  cast_weap = list(filter(lambda action: action.action_type == Actions.CAST_WEAPON and action.source == new_weapon, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_weap)
  assert game.current_player.weapon == new_weapon

  hero_attack_options = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(hero_attack_options) == 1
  game.perform_action(hero_attack_options[0])
  assert game.current_player.other_player.health == 28
  assert game.current_player.health == 30
  assert game.current_player.weapon.health == 1
  assert game.current_player.attacks_this_turn == 1
  
  hero_attack_options = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))

  game.perform_action(hero_attack_options[0])
  assert game.current_player.other_player.health == 26
  assert game.current_player.weapon == None
  assert new_weapon.parent == new_weapon.owner.graveyard
  assert game.current_player.attacks_this_turn == 2

def test_damage_all():
  game = GameManager().create_test_game()

  new_dam_all = game.game_manager.get_card('All Damage', game.current_player.hand)
  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  cast_new_dam = list(filter(lambda action: action.source == new_dam_all, game.get_available_actions(game.current_player)))[0]
  assert len(cast_new_dam.targets) == 3

  game.perform_action(cast_new_dam)
  assert game.player.health == 27
  assert game.enemy.health == 27
  assert wisp.parent == wisp.owner.graveyard

def test_generic_weapon():
  game = GameManager().create_test_game()

  new_weapon = game.game_manager.get_card('Generic Weapon', game.current_player.hand)

  cast_weap = list(filter(lambda action: action.action_type == Actions.CAST_WEAPON and action.source == new_weapon, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_weap)
  assert game.current_player.weapon == new_weapon

  wisp = game.game_manager.get_card('Wisp', game.current_player.other_player.board)

  hero_attack_options = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))
  assert len(hero_attack_options) == 2
  game.perform_action(hero_attack_options[0])
  assert game.current_player.other_player.health == 27
  assert game.current_player.health == 30
  assert game.current_player.weapon.health == 1
  assert game.current_player.attacks_this_turn == 1
  
  game.current_player.attacks_this_turn = 0
  game.perform_action(hero_attack_options[1])
  assert wisp.parent == wisp.owner.graveyard
  assert game.current_player.health == 29
  assert game.current_player.weapon == None
  assert new_weapon.parent == new_weapon.owner.graveyard
  assert game.current_player.attacks_this_turn == 1

def test_return_to_hand():
  game = GameManager().create_test_game()

  wisp = game.game_manager.get_card('Wisp', game.current_player.board)
  sergeant = game.game_manager.get_card('Abusive Sergeant', game.current_player.hand)

  buff_wisp = Action(Actions.CAST_MINION, sergeant, [wisp])
  game.perform_action(buff_wisp)
  assert wisp.temp_attack == 2
  assert wisp.get_attack() == 3

  brewmaster = game.game_manager.get_card('Youthful Brewmaster', game.current_player.hand)

  cast_brewmaster_actions = list(filter(lambda action: action.source == brewmaster, game.get_available_actions(game.current_player)))
  assert len(cast_brewmaster_actions) == 2
  game.perform_action(cast_brewmaster_actions[0])
  assert wisp.parent == wisp.owner.hand
  assert wisp.temp_attack == 0
  assert wisp.get_attack() == 1



def test_fatigue():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing)
  game = game_manager.create_game()

  assert game.current_player.get_health() == 30
  assert len(game.current_player.hand) == 3
  game.draw(game.current_player, 27)
  assert game.current_player.get_health() == 30
  game.draw(game.current_player, 1)
  assert game.current_player.get_health() == 29
  assert game.current_player.fatigue_damage == 2
  game.draw(game.current_player, 2)
  assert game.current_player.get_health() == 24
  assert game.current_player.fatigue_damage == 4
  assert len(game.current_player.hand) == 10

def test_excess_mana():
  game = GameManager().create_test_game()
  game.current_player.max_mana = 10
  gain_perm_mana = game.game_manager.get_card('Gain Perm Mana', game.current_player.hand)
  play_mana = list(filter(lambda action: action.source == gain_perm_mana, game.get_available_actions(game.current_player)))[0]
  game.perform_action(play_mana)
  assert len(game.current_player.hand) == 1
  assert game.current_player.max_mana == 10
  assert game.current_player.current_mana == 10


def test_random_card_game():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing)
  game = game_manager.create_game()

  game_results = empty(10)

  for i in range(10):
    game_results[i] = game.play_game()
    game.reset_game()
  
  assert game_results.mean() <= 1 and game_results.mean() >= 0

def test_big_games():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)
  game = game_manager.create_game()
  game_results = empty(10)

  for i in tqdm(range(10)):
    game_results[i] = game.play_game()
    game.reset_game()
    assert len(game.current_player.deck) + len(game.current_player.hand) == 30
    assert len(game.current_player.other_player.deck) + len(game.current_player.other_player.hand) == 31
    assert len(game.player.graveyard) == 0
    assert len(game.enemy.graveyard) == 0
    assert game.player.attack == 0
    assert game.player.health == 30
    assert game.enemy.attack == 0
    assert game.enemy.health == 30

  assert game_results.mean() < 1 and game_results.mean() > 0

def test_big_simulate():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(10)
  assert result > 0 and result < 1

def test_big_simulate_parralel():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(10, silent=True, parralel=-1)
  assert result > 0 and result < 1

def test_xl_big_random_cards():
  random_state = RandomState(0)
  for k in tqdm(range(100)):
    rand_seed = random_state.randint(0, 1000)
    print(f"seed was {rand_seed}")

    game_manager = GameManager(RandomState(rand_seed))
    game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
    game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
    for j in range(100):
      game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing)
      game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing)
    
      game = game_manager.create_game()

      game_results = empty(100)

      for i in range(100):
        game_result = game.play_game()
        assert game_result == 1 or game_result == 0
        game_results[i] = game_result
        game.reset_game()
      
      assert game_results.mean() < 1 and game_results.mean() > 0

def main():
  test_big_simulate()


if __name__ == '__main__':
  main()
