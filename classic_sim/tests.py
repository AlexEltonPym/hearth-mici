import random
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

def test_classic_pool():
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])

def test_coin():
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_shieldbearer = get_from_name(card_pool, 'Shieldbearer')
  new_shieldbearer.set_owner(game.current_player)
  new_shieldbearer.set_parent(game.current_player.board)
  new_shieldbearer.attacks_this_turn = 0
  available_actions=game.get_available_actions(game.current_player)
  print(available_actions)
  for action in available_actions:
    assert action.action_type != Actions.ATTACK

def test_southsea_deckhand():
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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
  assert new_bloodsail.attack == 5

def test_direwolf():
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_wolf = get_from_name(card_pool, 'Dire Wolf Alpha')
  new_wolf.set_owner(game.current_player)
  new_wolf.set_parent(game.current_player.board)

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.set_owner(game.current_player)
  new_wisp.set_parent(game.current_player.board)

  assert new_wisp.get_attack(game) == 2
  assert new_wolf.get_attack(game) == 3

def test_loot_hoarder():
  random.seed(0)
  hunter_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  mage_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  _player = Player(Classes.HUNTER, Deck().generate_random(hunter_pool), GreedyAction)
  _enemy = Player(Classes.MAGE, Deck().generate_random(mage_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_hoarder = get_from_name(hunter_pool, 'Loot Hoarder')
  new_hoarder.set_owner(game.current_player)
  new_hoarder.set_parent(game.current_player.board)
  assert len(game.current_player.hand.get_all()) == 4

  fireblast_action = Action(action_type=Actions.CAST_HERO_POWER, source=game.enemy.hero_power, targets=[new_hoarder])
  game.perform_action(fireblast_action)
  assert new_hoarder.parent == new_hoarder.owner.graveyard
  assert len(game.current_player.hand.get_all()) == 5

def test_hexproof():
  random.seed(0)
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

def test_windfury_weapon():
  random.seed(0)
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
  random.seed(0)
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
  random.seed(0)
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

def test_game():
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  for i in range(100):
    game.take_turn()
    if(game.player.health <= 0):
      assert True
      return 0
    elif(game.enemy.health <= 0):
      assert True
      return 1
  assert False

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
  random.seed(0)
  for k in tqdm(range(100)):
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
  test_loot_hoarder()
  # test_simulate()


if __name__ == '__main__':
  main()
