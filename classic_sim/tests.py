import random
from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import *
from strategy import GreedyAction
import numpy as np
from action import Action

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
    if card.name == 'The coin':
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

  new_card = get_from_name(card_pool, 'Abusive sergeant')
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

  new_squire = get_from_name(card_pool, 'Argent squire')
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
  
  new_leper = get_from_name(card_pool, 'Leper gnome')
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
  new_shieldbearer.has_attacked = False
  available_actions=game.get_available_actions(game.current_player)
  for action in available_actions:
    assert action.action_type != Actions.ATTACK

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
  wisp.has_attacked = False
  available_actions=game.get_available_actions(game.current_player)
  for action in available_actions:
    assert not (action.action_type == Actions.ATTACK and action.targets[0] == game.current_player.other_player)

def test_damage_all():
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.TEST_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_dam_all = get_from_name(card_pool, 'All dam')
  new_dam_all.set_owner(game.current_player)
  new_dam_all.set_parent(game.current_player.hand)
  
  wisp = get_from_name(card_pool, 'Wisp')
  wisp.set_owner(game.current_player.other_player)
  wisp.set_parent(game.current_player.other_player.board)

  cast_new_dam = game.get_available_actions(game.current_player)[1]
  assert len(cast_new_dam.targets) == 3

  game.perform_action(cast_new_dam)
  assert game.player.health == 27
  assert game.enemy.health == 27
  assert wisp.parent == wisp.owner.graveyard

def test_random_damage_card():
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.RANDOM_CARDS])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  print(game.simulate_game())


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
  random.seed(0)
  hunter_pool = build_pool([CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_NEUTRAL])
  mirror_deck = Deck().generate_random(hunter_pool)
  player = Player(Classes.HUNTER, mirror_deck, GreedyAction)
  enemy = Player(Classes.HUNTER, mirror_deck, GreedyAction)
  games = np.empty(3)
  game = Game(player, enemy)

  for i in range(3):
    games[i] = game.simulate_game()
    game.reset_game()
    
  assert games.mean() < 1 and games.mean() > 0


def main():
  test_random_damage_card()

if __name__ == '__main__':
  main()
