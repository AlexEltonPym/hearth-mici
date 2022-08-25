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
  assert len(card_pool) == 3


def test_game():
  seed = random.randrange(1000)
  random.seed(seed)
  print("Seed was:", seed)
  # random.seed(283)
  card_pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  _player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  _enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  game = Game(_player, _enemy)
  # [print(card) for card in game.player.deck.get_all()]
  # assert game.current_player == game.player


  # assert get_utility_card('coin') in game.current_player.other_player.hand


  for i in range(100):
    game.take_turn()
    print(game.current_player)

    if(game.player.card_details['health'] <= 0):
      return 0
    elif(game.enemy.card_details['health'] <= 0):
      return 1


  assert True

def main():
  test_classic_pool()
  print(test_game())

if __name__ == '__main__':
  main()
