import random
from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import build_pool, get_utility_card
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
    if(game.player.health <= 0):
      return 0
    elif(game.enemy.health <= 0):
      return 1


  assert True

def main():
  test_classic_pool()
  # test_game()
  test_coin()

if __name__ == '__main__':
  main()
