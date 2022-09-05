from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
import numpy as np
from action import Action
from tqdm import tqdm
from numpy.random import seed, randint

def test_classic_pool():
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])

def test_coin():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.take_turn()

  coin_card = None
  for card in game.current_player.hand.get_all():
    if card.name == 'The Coin':
      coin_card = card
      break

  cast_coin = Action(Actions.CAST_SPELL, coin_card, [game.current_player])

  assert game.current_player.current_mana == 0
  assert cast_coin.source in game.current_player.hand.get_all()
  game.perform_action(cast_coin)
  assert cast_coin.source not in game.current_player.hand.get_all()
  assert game.current_player.current_mana == 1

def test_abusive_sergeant():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player)
  new_wisp.set_parent(game.current_player.board)
  assert new_wisp.attack == 1

  new_card = get_from_name(card_pool, 'Abusive Sergeant')
  new_card.set_owner(game.current_player)
  new_card.set_parent(game.current_player.hand)

  buff_wisp = Action(Actions.CAST_MINION, new_card, [new_wisp])
  game.perform_action(buff_wisp)
  assert new_wisp.temp_attack == 2
  game.end_turn()
  assert new_wisp.temp_attack == 0

def test_hunter_hero_power():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  assert game.current_player.hero_power.name == get_hero_power(Classes.HUNTER).name
  assert game.current_player.other_player.health == 30
  use_hero_power = Action(Actions.CAST_HERO_POWER, game.current_player.hero_power, [game.current_player.other_player])
  game.perform_action(use_hero_power)
  assert game.current_player.other_player.health == 28

def test_argent_squire():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_squire = get_from_name(card_pool, 'Argent Squire')
  new_squire.set_owner(game.current_player.other_player)
  new_squire.set_parent(game.current_player.other_player.board)
  assert Attributes.DIVINE_SHIELD in new_squire.attributes
  
  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player)
  new_wisp.set_parent(game.current_player.board)
  assert new_wisp.attack == 1

  attack_squire = Action(Actions.ATTACK, new_wisp, [new_squire])
  game.perform_action(attack_squire)
  assert Attributes.DIVINE_SHIELD not in new_squire.attributes
  assert new_wisp.parent == game.current_player.graveyard
  
  another_wisp = get_from_name(card_pool, 'Wisp')
  another_wisp.set_owner(game.current_player)
  another_wisp.set_parent(game.current_player.board)
  attack_squire = Action(Actions.ATTACK, another_wisp, [new_squire])
  game.perform_action(attack_squire)
  assert new_squire.parent == game.current_player.other_player.graveyard

def test_leper_gnome():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  
  new_leper = get_from_name(card_pool, 'Leper Gnome')
  new_leper.set_owner(game.current_player)
  new_leper.set_parent(game.current_player.board)

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player.other_player)
  new_wisp.set_parent(game.current_player.other_player.board)

  attack_leper = Action(Actions.ATTACK, new_leper, [new_wisp])
  game.perform_action(attack_leper)
  assert new_leper.parent == new_leper.owner.graveyard
  assert new_wisp.parent == new_wisp.owner.graveyard
  assert game.current_player.other_player.health == 28
  
def test_shieldbearer():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_shieldbearer = get_from_name(card_pool, 'Shieldbearer')
  new_shieldbearer.set_owner(game.current_player)
  new_shieldbearer.set_parent(game.current_player.board)
  new_shieldbearer.attacks_this_turn = 0
  available_actions=game.get_available_actions(game.current_player)
  for action in available_actions:
    assert action.action_type != Actions.ATTACK

def test_southsea_deckhand():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_deckhand = get_from_name(card_pool, 'Southsea Deckhand')
  new_deckhand.set_owner(game.current_player)
  new_deckhand.set_parent(game.current_player.board)

  assert new_deckhand.attacks_this_turn == -1
  assert not new_deckhand.condition.requirement(game, new_deckhand)
  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))) == 0

  new_weapon = get_from_name(card_pool, 'Generic Weapon')
  new_weapon.set_owner(game.current_player)
  new_weapon.set_parent(game.current_player)
  assert new_deckhand.attacks_this_turn == -1
  assert new_deckhand.condition.requirement(game, new_deckhand)
  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))) == 2 #attack with charge, attack with weapon

def test_battlecry_weapon():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.current_player.current_mana = 3
  new_weapon = get_from_name(card_pool, 'Battlecry Weapon')
  new_weapon.set_owner(game.current_player)
  new_weapon.set_parent(game.current_player.hand)

  cast_weap = list(filter(lambda action: action.action_type == Actions.CAST_WEAPON and action.source==new_weapon, game.get_available_actions(game.current_player)))[0]

  game.perform_action(cast_weap)
  assert game.current_player.weapon == new_weapon
  assert game.current_player.health == 29
  assert game.current_player.other_player.health == 29

  wisp = get_from_name(card_pool, 'Wisp')
  wisp.set_owner(game.current_player.other_player)
  wisp.set_parent(game.current_player.other_player.board)

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
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_shieldbearer = get_from_name(card_pool, 'Shieldbearer')
  new_shieldbearer.set_owner(game.current_player.other_player)
  new_shieldbearer.set_parent(game.current_player.other_player.board)

  wisp = get_from_name(card_pool, 'Wisp')
  wisp.set_owner(game.current_player)
  wisp.set_parent(game.current_player.board)
  wisp.attacks_this_turn == 0
  available_actions=game.get_available_actions(game.current_player)
  for action in available_actions:
    assert not (action.action_type == Actions.ATTACK and action.targets[0] == game.current_player.other_player)

def test_stealth():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_worgen = get_from_name(card_pool, 'Worgen Infiltrator')
  new_worgen.set_owner(game.current_player)
  new_worgen.set_parent(game.current_player.board)
  assert Attributes.STEALTH in new_worgen.attributes

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player.other_player)
  new_wisp.set_parent(game.current_player.other_player.board)
  new_wisp.attacks_this_turn = 0

  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player.other_player)))) == 1

  new_worgen.attacks_this_turn = 0
  attack_action = list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player)))[0]
  game.perform_action(attack_action)
  assert not Attributes.STEALTH in new_worgen.attributes

  assert len(list(filter(lambda action: action.action_type == Actions.ATTACK, game.get_available_actions(game.current_player.other_player)))) == 2

def test_windfury():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_dragonhawk = get_from_name(card_pool, 'Young Dragonhawk')
  new_dragonhawk.set_owner(game.current_player)
  new_dragonhawk.set_parent(game.current_player.board)
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
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_berserker = get_from_name(card_pool, 'Amani Berserker')
  new_berserker.set_owner(game.current_player)
  new_berserker.set_parent(game.current_player.board)
  assert not new_berserker.condition.requirement(game, new_berserker)
  new_berserker.attacks_this_turn = 0
  new_berserker.health = 2
  assert new_berserker.condition.requirement(game, new_berserker)
  attack_action = Action(action_type=Actions.ATTACK, source=new_berserker, targets=[game.current_player.other_player])
  game.perform_action(attack_action)
  assert game.current_player.other_player.health == 25

def test_bloodsail():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_bloodsail = get_from_name(card_pool, 'Bloodsail Raider')
  new_bloodsail.set_owner(game.current_player)
  new_bloodsail.set_parent(game.current_player.hand)

  game.current_player.current_mana = 10
  new_weapon = get_from_name(card_pool, 'Generic Weapon')
  new_weapon.set_owner(game.current_player)
  new_weapon.set_parent(game.current_player.hand)

  cast_weap = list(filter(lambda action: action.action_type == Actions.CAST_WEAPON and action.source == new_weapon, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_weap)
  assert game.current_player.weapon == new_weapon

  cast_bloodsail = list(filter(lambda action: action.source == new_bloodsail, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_bloodsail)
  assert new_bloodsail.parent == new_bloodsail.owner.board
  assert new_bloodsail.get_attack() == 5

def test_direwolf():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_wolf = get_from_name(card_pool, 'Dire Wolf Alpha')
  new_wolf.set_owner(game.current_player)
  new_wolf.set_parent(game.current_player.board)

  first_wisp = get_from_name(card_pool, 'Wisp')
  first_wisp.set_owner(game.current_player)
  first_wisp.set_parent(game.current_player.board)

  second_wisp = get_from_name(card_pool, 'Wisp')
  second_wisp.set_owner(game.current_player)
  second_wisp.set_parent(game.current_player.board)
  
  third_wisp = get_from_name(card_pool, 'Wisp')
  third_wisp.set_owner(game.current_player)
  third_wisp.set_parent(game.current_player.board)


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
  seed(0)
  hunter_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  mage_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  _player = Player(Classes.HUNTER, Deck().generate_random(hunter_pool), GreedyAction)
  _enemy = Player(Classes.MAGE, Deck().generate_random(mage_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_hoarder = get_from_name(hunter_pool, 'Loot Hoarder')
  new_hoarder.set_owner(game.current_player)
  new_hoarder.set_parent(game.current_player.board)
  assert len(game.current_player.hand.get_all()) == 3

  fireblast_action = Action(action_type=Actions.CAST_HERO_POWER, source=game.enemy.hero_power, targets=[new_hoarder])
  game.perform_action(fireblast_action)
  assert new_hoarder.parent == new_hoarder.owner.graveyard
  assert len(game.current_player.hand.get_all()) == 4

def test_hexproof():
  seed(0)
  hunter_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  mage_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  _player = Player(Classes.HUNTER, Deck().generate_random(hunter_pool), GreedyAction)
  _enemy = Player(Classes.MAGE, Deck().generate_random(mage_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.player.hand.hand = []
  game.enemy.hand.hand = []

  new_faerie = get_from_name(hunter_pool, 'Faerie Dragon')
  new_faerie.set_owner(game.player)
  new_faerie.set_parent(game.player.board)
  
  new_fireball = get_from_name(mage_pool, 'Fireball')
  new_fireball.set_owner(game.enemy)
  new_fireball.set_parent(game.enemy.hand)

  game.enemy.current_mana = 10

  available_actions = game.get_available_actions(game.enemy)
  available_actions = list(filter(lambda action: action.action_type==Actions.CAST_SPELL or action.action_type==Actions.CAST_HERO_POWER, available_actions))
  assert len(available_actions) == 4 #fireblast self and enemy, fireball self and enemy

def test_mad_bomber():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.current_player.hand.hand = []
  game.current_player.current_mana = 10

  new_bomber = get_from_name(card_pool, 'Mad Bomber')
  new_bomber.set_owner(game.current_player)
  new_bomber.set_parent(game.current_player.hand)

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player.other_player)
  new_wisp.set_parent(game.current_player.other_player.board)

  cast_bomber = game.get_available_actions(game.current_player)[0]
  game.perform_action(cast_bomber)

  assert new_wisp.parent == new_wisp.owner.graveyard 
  assert new_wisp.get_health() == -1 
  assert game.current_player.get_health() == 29 

def test_farseer():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.current_player.hand.hand = []
  game.current_player.current_mana = 10

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player)
  new_wisp.set_parent(game.current_player.board)
  assert new_wisp.get_health() == 1
  assert new_wisp.get_max_health() == 1
  assert game.current_player.health == 30
  assert game.current_player.max_health == 30
  assert game.current_player.get_max_health() == 30

  defender = get_from_name(card_pool, 'Defender of Argus')
  defender.set_owner(game.current_player)
  defender.set_parent(game.current_player.hand)
  cast_defender = list(filter(lambda action: action.source == defender, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_defender)

  assert new_wisp.get_attack() == 2
  assert new_wisp.get_health() == 2 
  assert new_wisp.has_attribute(Attributes.TAUNT)

  new_farseer = get_from_name(card_pool, 'Earthen Ring Farseer')
  new_farseer.set_owner(game.current_player)
  new_farseer.set_parent(game.current_player.hand)

  cast_actions = list(filter(lambda action: action.action_type == Actions.CAST_MINION, game.get_available_actions(game.current_player)))
  assert len(cast_actions) == 4 #heal wisp, defender, self and enemy
  game.perform_action(cast_actions[0])
  assert new_wisp.get_health() == 2
  assert new_wisp.get_max_health() == 2

  game.deal_damage(new_wisp, 1)
  assert new_wisp.parent == new_wisp.owner.board
  assert new_wisp.get_health() == 1
  assert new_wisp.get_max_health() == 2
  
  second_farseer = get_from_name(card_pool, 'Earthen Ring Farseer')
  second_farseer.set_owner(game.current_player)
  second_farseer.set_parent(game.current_player.hand)

  heal_wisp = list(filter(lambda action: action.source == second_farseer and action.targets[0] == new_wisp, game.get_available_actions(game.current_player)))[0]
  game.perform_action(heal_wisp)
  assert new_wisp.get_health() == 2
  assert new_wisp.get_max_health() == 2

def test_ghoul():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.current_player.hand.hand = []
  game.current_player.current_mana = 10

  new_ghoul = get_from_name(card_pool, 'Flesheating Ghoul')
  new_ghoul.set_owner(game.current_player)
  new_ghoul.set_parent(game.current_player.board)

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player)
  new_wisp.set_parent(game.current_player.board)

  enemy_wisp = get_from_name(card_pool, 'Wisp')
  enemy_wisp.set_owner(game.current_player.other_player)
  enemy_wisp.set_parent(game.current_player.other_player.board)

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
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.current_player.hand.hand = []
  game.current_player.current_mana = 10

  new_golem = get_from_name(card_pool, 'Harvest Golem')
  new_golem.set_owner(game.current_player)
  new_golem.set_parent(game.current_player.board)

  game.deal_damage(new_golem, 3)
  assert new_golem.parent == new_golem.owner.graveyard
  assert len(game.current_player.board.get_all()) == 1
  assert game.current_player.board.get_all()[0].name == 'Damaged Golem'


def test_windfury_weapon():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  new_weapon = get_from_name(card_pool, 'Windfury Weapon')
  new_weapon.set_owner(game.current_player)
  new_weapon.set_parent(game.current_player.hand)

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
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_dam_all = get_from_name(card_pool, 'All Damage')
  new_dam_all.set_owner(game.current_player)
  new_dam_all.set_parent(game.current_player.hand)
  
  wisp = get_from_name(card_pool, 'Wisp')
  wisp.set_owner(game.current_player.other_player)
  wisp.set_parent(game.current_player.other_player.board)

  cast_new_dam = list(filter(lambda action: action.source == new_dam_all, game.get_available_actions(game.current_player)))[0]
  assert len(cast_new_dam.targets) == 3

  game.perform_action(cast_new_dam)
  assert game.player.health == 27
  assert game.enemy.health == 27
  assert wisp.parent == wisp.owner.graveyard

def test_generic_weapon():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.current_player.current_mana = 3
  new_weapon = get_from_name(card_pool, 'Generic Weapon')
  new_weapon.set_owner(game.current_player)
  new_weapon.set_parent(game.current_player.hand)

  cast_weap = list(filter(lambda action: action.action_type == Actions.CAST_WEAPON and action.source == new_weapon, game.get_available_actions(game.current_player)))[0]
  game.perform_action(cast_weap)
  assert game.current_player.weapon == new_weapon

  wisp = get_from_name(card_pool, 'Wisp')
  wisp.set_owner(game.current_player.other_player)
  wisp.set_parent(game.current_player.other_player.board)

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
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.current_player.current_mana = 10

  wisp = get_from_name(card_pool, 'Wisp')
  wisp.set_owner(game.current_player)
  wisp.set_parent(game.current_player.board)

  sergeant = get_from_name(card_pool, 'Abusive Sergeant')
  sergeant.set_owner(game.current_player)
  sergeant.set_parent(game.current_player.hand)

  buff_wisp = Action(Actions.CAST_MINION, sergeant, [wisp])
  game.perform_action(buff_wisp)
  assert wisp.temp_attack == 2
  assert wisp.get_attack() == 3

  brewmaster = get_from_name(card_pool, 'Youthful Brewmaster')
  brewmaster.set_owner(game.current_player)
  brewmaster.set_parent(game.current_player.hand)

  cast_brewmaster_actions = list(filter(lambda action: action.source == brewmaster, game.get_available_actions(game.current_player)))
  assert len(cast_brewmaster_actions) == 2
  game.perform_action(cast_brewmaster_actions[0])
  assert wisp.parent == wisp.owner.hand
  assert wisp.temp_attack == 0
  assert wisp.get_attack() == 1

def test_random_card_game():
  card_pool = build_pool([CardSets.RANDOM_CARDS])
  mirror_deck = Deck().generate_random(card_pool)
  _player = Player(Classes.HUNTER, mirror_deck, RandomNoEarlyPassing)
  _enemy = Player(Classes.HUNTER, mirror_deck, RandomNoEarlyPassing)
  game = Game(_player, _enemy)

  game_results = np.empty(10)

  for i in range(10):
    game_results[i] = game.simulate_game()
    game.reset_game()
  
  assert game_results.mean() < 1 and game_results.mean() > 0

def test_fatigue():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  assert game.current_player.get_health() == 30
  assert len(game.current_player.hand.get_all()) == 3
  game.draw(game.current_player, 27)
  assert game.current_player.get_health() == 30
  game.draw(game.current_player, 1)
  assert game.current_player.get_health() == 29
  assert game.current_player.fatigue_damage == 2
  game.draw(game.current_player, 2)
  assert game.current_player.get_health() == 24
  assert game.current_player.fatigue_damage == 4
  assert len(game.current_player.hand.get_all()) == 10

def test_game():
  seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  game.untap()
  turn_passed = False

  while not turn_passed:
    turn_passed = game.current_player.strategy.choose_action(game)
    if game.player.health <= 0:
      assert True
      break
    elif game.enemy.health <= 0:
      assert True
      break
    if turn_passed:
      game.end_turn()

def test_simulate():
  hunter_pool = build_pool([CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_NEUTRAL])
  mirror_deck = Deck().generate_random(hunter_pool)
  player = Player(Classes.HUNTER, mirror_deck, RandomNoEarlyPassing)
  enemy = Player(Classes.HUNTER, mirror_deck, RandomNoEarlyPassing)
  game_results = np.empty(10)
  game = Game(player, enemy)

  for i in range(10):
    game_results[i] = game.simulate_game()
    game.reset_game()
    assert len(game.player.deck.get_all()) == 30
    assert len(game.enemy.deck.get_all()) == 30
    assert len(game.player.hand.get_all()) == 0
    assert len(game.enemy.hand.get_all()) == 0
    assert len(game.player.graveyard.get_all()) == 0
    assert len(game.enemy.graveyard.get_all()) == 0
    assert game.player.attack == 0
    assert game.player.health == 30
    assert game.enemy.attack == 0
    assert game.enemy.health == 30

  assert game_results.mean() < 1 and game_results.mean() > 0

def test_big_random_cards():

  for k in tqdm(range(100)):
    rand_seed = randint(0, 1000)
    print(f"seed was {rand_seed}")
    seed(rand_seed)
    card_pool = build_pool([CardSets.RANDOM_CARDS])
    for j in range(100):
      mirror_deck = Deck().generate_random(card_pool)
      _player = Player(Classes.HUNTER, mirror_deck, RandomNoEarlyPassing)
      _enemy = Player(Classes.HUNTER, mirror_deck, RandomNoEarlyPassing)
      game = Game(_player, _enemy)
      
      game_results = np.empty(100)

      for i in range(100):
        game_result = game.simulate_game()
        assert game_result == 1 or game_result == 0
        game_results[i] = game_result
        game.reset_game()
      
      assert game_results.mean() < 1 and game_results.mean() > 0

def main():
  test_farseer()


if __name__ == '__main__':
  main()
