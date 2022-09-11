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
  commons = get_classic_common_cards()
  assert len(commons) == 38

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
  assert game.current_player.other_player.health == 30
  use_hero_power = Action(Actions.CAST_HERO_POWER, game.current_player.hero_power, [game.current_player.other_player])
  game.perform_action(use_hero_power)
  assert game.current_player.other_player.health == 28

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
  game.enemy.current_mana = 10

  new_faerie = game.game_manager.get_card('Faerie Dragon', game.player.board)
  new_fireball = game.game_manager.get_card('Fireball', game.enemy.hand)

  available_actions = game.get_available_actions(game.enemy)
  available_actions = list(filter(lambda action: action.action_type==Actions.CAST_SPELL or action.action_type==Actions.CAST_HERO_POWER, available_actions))
  if game.current_player == game.player:
    assert len(available_actions) == 5 #coin, fireblast self and enemy, fireball self and enemy
  else:
    assert len(available_actions) == 4 #no coin

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

  assert new_ghoul.get_attack() == 3
  game.deal_damage(new_wisp, 1)
  assert new_ghoul.get_attack() == 4
  game.deal_damage(enemy_wisp, 1)
  assert new_ghoul.get_attack() == 5
  assert new_ghoul.get_health() == 3
  game.deal_damage(new_ghoul, 3)
  assert new_ghoul.parent == new_ghoul.owner.graveyard
  assert new_ghoul.get_attack() == 5

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

  print(game.current_player.secret_zone)
  assert False


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
    assert len(game.player.deck) == 30
    assert len(game.enemy.deck) == 30
    assert len(game.player.hand) == 0
    assert len(game.enemy.hand) == 0
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
