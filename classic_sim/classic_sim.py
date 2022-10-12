from zones import Deck
from enums import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
from game_manager import GameManager
from numpy.random import RandomState

def main():
  results = []
  # results.append(random_hunter_vs_mage())
  results.append(class_cards_hunter_vs_warrior())
  print(results)



  return True

def class_cards_mage_vs_hunter():
  game_manager = GameManager(RandomState())
  game_manager.create_player_pool([CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_HUNTER])
  game_manager.create_player(Classes.MAGE, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(num_games=100, parralel=-1, silent=False)
  return result

def class_cards_hunter_vs_warrior():
  game_manager = GameManager(RandomState())
  game_manager.create_player_pool([CardSets.CLASSIC_HUNTER])
  game_manager.create_enemy_pool([CardSets.CLASSIC_WARRIOR])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.WARRIOR, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(num_games=100, parralel=-1, silent=False)
  return result

def random_hunter_vs_mage():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(num_games=100, parralel=-1)
  return result



if __name__ == '__main__':
  main()
