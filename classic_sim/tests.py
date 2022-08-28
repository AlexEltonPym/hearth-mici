import random
from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import build_pool, get_utility_card, get_from_name, get_hero_power
from strategy import GreedyAction


def test_classic_pool():
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])

def test_coin():
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  game.take_turn()
  assert get_utility_card('coin') in game.current_player.hand.get_all()
  cast_coin = game.get_available_actions(game.current_player)[0]
  assert game.current_player.current_mana == 0
  assert cast_coin['source'] in game.current_player.hand.get_all()
  game.perform_action(cast_coin)
  assert cast_coin['source'] not in game.current_player.hand.get_all()
  assert game.current_player.current_mana == 1

def test_abusive_sergeant():
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  new_wisp = get_from_name(card_pool, 'Wisp')
  new_wisp.owner = game.current_player
  new_wisp.parent = game.current_player.board
  game.current_player.board.add(new_wisp)
  assert new_wisp.attack == 1

  new_card = get_from_name(card_pool, 'Abusive sergeant')
  new_card.owner = game.current_player
  new_card.parent = game.current_player.hand
  game.current_player.hand.add(new_card)

  buff_wisp = {'action_type': Actions.CAST_MINION, 'source': new_card, 'target': new_wisp}
  game.perform_action(buff_wisp)
  assert new_wisp.temp_attack == 2
  game.untap()
  assert new_wisp.temp_attack == 0

def test_hunter_hero_power():
  random.seed(0)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  assert game.current_player.hero_power == get_hero_power(Classes.HUNTER)
  assert game.current_player.other_player.health == 30
  use_hero_power = {'action_type': Actions.CAST_HERO_POWER, 'source': game.current_player.hero_power, 'target': game.current_player.other_player}
  game.perform_action(use_hero_power)
  assert game.current_player.other_player.health == 28

def test_game():
  seed = random.randrange(1000)
  random.seed(seed)
  print("Seed was:", seed)
  # random.seed(283)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)

  for i in range(100):
    game.take_turn()
    print(game.current_player.board.get_all())
    if(game.player.health <= 0):
      return 0
    elif(game.enemy.health <= 0):
      return 1


  assert True

def main():
  test_hunter_hero_power()

if __name__ == '__main__':
  main()
